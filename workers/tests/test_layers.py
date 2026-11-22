"""Model-free test of the post-model stage: synthetic geometry and masks in, GLB and
scene.json out. Runs in CI without PyTorch."""

import json
import pathlib
import struct

import jsonschema
import numpy as np

from workers.pipeline.layers import Layer, build_layers, fill_mask, write_outputs

SCHEMA = json.loads(
    (pathlib.Path(__file__).resolve().parents[2] / "schema" / "scene.schema.json").read_text()
)
H, W, F = 48, 64, 60.0
K_NORM = np.array([[F / W, 0, 0.5], [0, F / H, 0.5], [0, 0, 1]], np.float32)


def scene_points():
    """A wall at 4 m with a box at 2 m in front of it (OpenCV convention)."""
    z = np.full((H, W), 4.0, np.float32)
    box = np.zeros((H, W), bool)
    box[12:36, 16:40] = True
    z[box] = 2.0
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32) + 0.5
    pts = np.stack([(xs - W / 2) / F * z, (ys - H / 2) / F * z, z], -1)
    return pts.astype(np.float32), box


def glb_parts(glb: bytes):
    json_len = struct.unpack_from("<I", glb, 12)[0]
    doc = json.loads(glb[20 : 20 + json_len])
    bin_chunk = glb[20 + json_len + 8 :]
    return doc, bin_chunk


def node_positions(glb: bytes, name: str) -> np.ndarray:
    doc, binary = glb_parts(glb)
    node = next(n for n in doc["nodes"] if n["name"] == name)
    acc = doc["accessors"][doc["meshes"][node["mesh"]]["primitives"][0]["attributes"]["POSITION"]]
    view = doc["bufferViews"][acc["bufferView"]]
    return np.frombuffer(binary, np.float32, acc["count"] * 3, view["byteOffset"]).reshape(-1, 3)


def build():
    pts, box = scene_points()
    rgb = np.full((H, W, 3), 128, np.uint8)
    layers = [Layer("obj-01", box, 0.9)]
    bg_points = pts.copy()
    bg_points[box] = pts[~box][0]  # stand-in for the filled background
    return build_layers(rgb, pts, K_NORM, layers, rgb, bg_points), layers, box, rgb


def test_scene_json_matches_schema_and_ids():
    result, layers, _, _ = build()
    jsonschema.validate(result.scene, SCHEMA)
    assert [o["id"] for o in result.scene["objects"]] == ["obj-01"]
    assert result.intrinsics == {"fx": F, "fy": F, "cx": W / 2, "cy": H / 2, "width": W, "height": H}


def test_glb_nodes_are_background_then_object_ids():
    result, _, _, _ = build()
    doc, _ = glb_parts(result.glb)
    assert [n["name"] for n in doc["nodes"]] == ["background", "obj-01"]


def test_object_vertices_reproject_onto_their_mask():
    result, _, box, _ = build()
    v = node_positions(result.glb, "obj-01")
    assert len(v) > 0
    x, y, z = v[:, 0], -v[:, 1], -v[:, 2]  # glTF -> OpenCV
    u = F * x / z + W / 2
    w = F * y / z + H / 2
    # Vertices sit at pixel centers: they reproject within 0.5 px of a masked pixel.
    cols, rows = np.floor(u).astype(int), np.floor(w).astype(int)
    assert np.all(np.abs(u - (cols + 0.5)) < 1e-3) and np.all(np.abs(w - (rows + 0.5)) < 1e-3)
    assert box[rows, cols].all()


def test_fill_mask_covers_objects_with_margin():
    _, box = scene_points()
    filled = fill_mask([Layer("obj-01", box, 1.0)], (H, W))
    assert filled[box].all() and filled.sum() > box.sum()
    assert not fill_mask([], (H, W)).any()


def test_write_outputs(tmp_path):
    result, layers, _, rgb = build()
    write_outputs(tmp_path, result, layers, rgb, rgb)
    names = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file())
    assert names == [
        "background.png", "camera.json", "masks/obj-01.png", "overlay.png",
        "scene.glb", "scene.json", "source.png",
    ]  # fmt: skip
    jsonschema.validate(json.loads((tmp_path / "scene.json").read_text()), SCHEMA)
