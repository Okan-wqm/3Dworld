"""Phase 1 core: single image -> layered 2.5D scene ("Paralaks Sahne").

    python -m workers.pipeline.layered_scene IMAGE OUT_DIR --click X,Y [--click X,Y ...]
    python -m workers.pipeline.layered_scene IMAGE OUT_DIR --auto

Objects are picked by clicking them (one `--click` per object; `X,Y,-` adds a negative
refinement click to the previous object, `X,Y,+` a positive one), or suggested
automatically with `--auto`.

Steps (PLAN.md §2):
  [3]  MoGe-2: metric point map + camera
  [2]  SAM 2.1: one mask per clicked object (or automatic suggestions)
  [5]  LaMa: fill the background behind the objects
  [5b] MoGe-2 again on the filled background, scaled to match the original depth
  [7]  geom-core: one depth mesh per object + one for the background

Writes OUT_DIR/scene.glb (nodes "background", "obj-01", ...), scene.json
(scene-schema v1), camera.json, background.png, masks/obj-XX.png and overlay.png.
"""

from __future__ import annotations

import argparse
import io
import json
import pathlib
import time

import numpy as np
import torch
from PIL import Image
from scipy import ndimage

import geom_core
from workers.common.depth_ops import fit_background_depth
from workers.complete.inpaint import inpaint, load_lama
from workers.geometry.image_to_mesh import estimate_geometry
from workers.segment.propose import ClickSession, Proposal, load_sam, propose_objects

PALETTE = [  # Okabe-Ito, color-blind safe
    (230, 159, 0), (86, 180, 233), (0, 158, 115), (240, 228, 66),
    (0, 114, 178), (213, 94, 0), (204, 121, 167), (153, 153, 153),
]


def png_bytes(rgb: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(rgb).save(buf, format="PNG")
    return buf.getvalue()


def geometry(image: np.ndarray, device: str, fov_x: float | None = None):
    geo = estimate_geometry(image, device, fov_x)
    points = np.ascontiguousarray(geo["points"], dtype=np.float32)
    valid = geo["mask"].astype(bool) & np.isfinite(points).all(-1)
    points[~valid] = np.nan
    return points, geo["intrinsics"]


def parse_clicks(specs: list[str]) -> list[list[tuple[float, float, bool]]]:
    """`X,Y` starts a new object; `X,Y,+` / `X,Y,-` refine the previous one."""
    objects: list[list[tuple[float, float, bool]]] = []
    for spec in specs:
        x, y, *sign = spec.split(",")
        if sign and objects:
            objects[-1].append((float(x), float(y), sign[0] != "-"))
        else:
            objects.append([(float(x), float(y), True)])
    return objects


def select_by_clicks(sam, rgb: np.ndarray, objects, timings: dict) -> list[Proposal]:
    t = time.perf_counter()
    session = ClickSession(sam, rgb)
    timings["sam_encode"] = time.perf_counter() - t
    proposals, taken = [], np.zeros(rgb.shape[:2], bool)
    t = time.perf_counter()
    for clicks in objects:
        mask, score = session.select(clicks)
        mask &= ~taken  # first click wins where two objects overlap
        taken |= mask
        ys, xs = np.nonzero(mask)
        bbox = (int(xs.min()), int(ys.min()), int(np.ptp(xs)) + 1, int(np.ptp(ys)) + 1) if xs.size else (0, 0, 0, 0)
        proposals.append(Proposal(mask, score, float(mask.mean()), 1.0, bbox))
    timings["sam_per_click_ms"] = 1000 * (time.perf_counter() - t) / max(1, len(objects))
    return [p for p in proposals if p.mask.any()]


def overlay(image: np.ndarray, masks: list[np.ndarray]) -> np.ndarray:
    out = image.astype(np.float32)
    for i, m in enumerate(masks):
        color = np.array(PALETTE[i % len(PALETTE)], np.float32)
        out[m] = 0.45 * out[m] + 0.55 * color
        edge = m & ~ndimage.binary_erosion(m, iterations=2)
        out[edge] = color
    return out.clip(0, 255).astype(np.uint8)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("image", type=pathlib.Path)
    ap.add_argument("out_dir", type=pathlib.Path)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--max-side", type=int, default=768)
    ap.add_argument("--sam", choices=["large", "small"], default=None,
                    help="default: large on GPU, small on CPU")
    ap.add_argument("--click", action="append", default=[], metavar="X,Y[,+|-]",
                    help="select an object at pixel X,Y of the resized image")
    ap.add_argument("--auto", action="store_true", help="suggest objects automatically")
    args = ap.parse_args()
    if not args.click and not args.auto:
        ap.error("pick objects with --click X,Y (repeatable) or use --auto")
    sam_size = args.sam or ("large" if args.device.startswith("cuda") else "small")
    out = args.out_dir
    (out / "masks").mkdir(parents=True, exist_ok=True)
    timings = {}

    img = Image.open(args.image).convert("RGB")
    img.thumbnail((args.max_side, args.max_side))
    rgb = np.asarray(img).copy()
    h, w = rgb.shape[:2]

    t = time.perf_counter()
    points, k = geometry(rgb, args.device)
    depth = points[..., 2]
    timings["moge"] = time.perf_counter() - t

    t = time.perf_counter()
    sam = load_sam(sam_size, args.device)
    if args.auto:
        proposals = propose_objects(sam, rgb, depth)
    else:
        proposals = select_by_clicks(sam, rgb, parse_clicks(args.click), timings)
    del sam
    timings["sam"] = time.perf_counter() - t

    # Fill a slightly dilated union so that edge pixels of objects do not leak into the
    # background texture.
    t = time.perf_counter()
    union = np.zeros((h, w), bool)
    for p in proposals:
        union |= p.mask
    fill_mask = ndimage.binary_dilation(union, iterations=max(4, int(0.012 * max(h, w))))
    background = inpaint(load_lama(args.device), rgb, fill_mask, args.device) if union.any() else rgb
    timings["lama"] = time.perf_counter() - t

    t = time.perf_counter()
    if union.any():
        # Same camera as the photo: without a fixed FOV MoGe re-guesses it for the edited
        # image and the background no longer lines up.
        fov_x = float(np.degrees(2 * np.arctan(0.5 / k[0, 0])))
        bg_points, _ = geometry(background, args.device, fov_x)
        bg_points, s = fit_background_depth(bg_points, points, fill_mask)
    else:
        bg_points, s = points, 1.0
    timings["moge_bg"] = time.perf_counter() - t

    t = time.perf_counter()
    # The background is the last layer: nothing lies behind it, so stretching a triangle
    # over a depth step looks better than leaving a hole. Objects keep the strict cut.
    bg_mesh = geom_core.grid_mesh(np.ascontiguousarray(bg_points), max_depth_ratio=0.25)
    parts = [("background", bg_mesh, png_bytes(background))]
    photo_png = png_bytes(rgb)
    objects = []
    for i, p in enumerate(proposals, 1):
        oid = f"obj-{i:02d}"
        # Erode by a pixel: boundary pixels mix object and background depth.
        mesh_mask = ndimage.binary_erosion(p.mask, iterations=1)
        mesh = geom_core.grid_mesh(points, mask=np.ascontiguousarray(mesh_mask))
        parts.append((oid, mesh, photo_png))
        Image.fromarray((p.mask * 255).astype(np.uint8)).save(out / "masks" / f"{oid}.png")
        objects.append({
            "id": oid,
            "label": {"text": "object", "source": "model", "confidence": round(p.score, 3)},
            "mask": {"uri": f"masks/{oid}.png", "sha256": None},
            "completion": None,
            "asset": None,
            "transform": {"translation": [0, 0, 0], "rotation": [0, 0, 0, 1], "scale": [1, 1, 1]},
            "transform_edited_by_user": False,
            "status": {"stage": "proposed", "stale_from": None, "failure": None},
        })
    glb = geom_core.write_glb_scene([(n, m, tex, "image/png") for n, m, tex in parts])
    timings["mesh_glb"] = time.perf_counter() - t

    intrinsics = {"fx": float(k[0, 0] * w), "fy": float(k[1, 1] * h),
                  "cx": float(k[0, 2] * w), "cy": float(k[1, 2] * h), "width": w, "height": h}
    scene = {
        "schema_version": 1,
        "source_image": {"uri": "source.png", "sha256": None},
        "camera": {"intrinsics": intrinsics,
                   "pose": {"translation": [0, 0, 0], "rotation": [0, 0, 0, 1], "scale": [1, 1, 1]}},
        "objects": objects,
        "background": {"inpainted_image": {"uri": "background.png", "sha256": None},
                       "asset": {"uri": "scene.glb", "sha256": None}, "stale": False},
    }
    (out / "scene.glb").write_bytes(glb)
    (out / "scene.json").write_text(json.dumps(scene, indent=2))
    (out / "camera.json").write_text(json.dumps(intrinsics, indent=2))
    Image.fromarray(rgb).save(out / "source.png")
    Image.fromarray(background).save(out / "background.png")
    Image.fromarray(overlay(rgb, [p.mask for p in proposals])).save(out / "overlay.png")

    print(f"{args.image.name}: {w}x{h}, {len(proposals)} objects, bg depth scale {s:.3f}, "
          f"GLB {len(glb) / 1e6:.1f} MB")
    print("  " + ", ".join(f"{k} {v:.1f}" + ("" if k.endswith("_ms") else "s") for k, v in timings.items()))


if __name__ == "__main__":
    main()
