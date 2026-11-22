"""Post-model stage of the layered scene: masks + geometry -> meshes, GLB, scene.json.

Model-free and deterministic, so it is unit-tested in CI without PyTorch. The model
stage (`layered_scene.py`) produces its inputs.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any

import numpy as np
from PIL import Image
from scipy import ndimage

import geom_core
from workers.common import scene_json
from workers.common.images import png_bytes

PALETTE = [  # Okabe-Ito, color-blind safe
    (230, 159, 0), (86, 180, 233), (0, 158, 115), (240, 228, 66),
    (0, 114, 178), (213, 94, 0), (204, 121, 167), (153, 153, 153),
]  # fmt: skip

# Object meshes cut at depth jumps above 4 %; the background (nothing behind it) is
# allowed to stretch over steps up to 25 % rather than show holes.
OBJECT_MAX_DEPTH_RATIO = 0.04
BACKGROUND_MAX_DEPTH_RATIO = 0.25


@dataclass
class Layer:
    """One selected object."""

    id: str
    mask: np.ndarray  # (H, W) bool
    score: float  # segmentation quality in [0, 1]


@dataclass
class LayeredScene:
    glb: bytes
    scene: dict[str, Any]  # scene.json content
    intrinsics: dict[str, Any]  # pixel intrinsics of the original camera
    overlay: np.ndarray  # RGB preview of the selected masks


def fill_mask(layers: list[Layer], shape: tuple[int, int]) -> np.ndarray:
    """Region to fill behind the objects: their union, slightly dilated so object edge
    pixels do not leak into the background texture."""
    union = np.zeros(shape, bool)
    for layer in layers:
        union |= layer.mask
    if not union.any():
        return union
    dilated: np.ndarray = ndimage.binary_dilation(union, iterations=max(4, int(0.012 * max(shape))))
    return dilated


def overlay(image: np.ndarray, masks: list[np.ndarray]) -> np.ndarray:
    out = image.astype(np.float32)
    for i, m in enumerate(masks):
        color = np.array(PALETTE[i % len(PALETTE)], np.float32)
        out[m] = 0.45 * out[m] + 0.55 * color
        edge = m & ~ndimage.binary_erosion(m, iterations=2)
        out[edge] = color
    return out.clip(0, 255).astype(np.uint8)


def build_layers(
    rgb: np.ndarray,
    points: np.ndarray,
    intrinsics_norm: np.ndarray,
    layers: list[Layer],
    background: np.ndarray,
    background_points: np.ndarray,
) -> LayeredScene:
    """Meshes every layer and the filled background into one GLB plus scene.json.

    rgb / background: (H, W, 3) uint8 photo and filled background.
    points / background_points: (H, W, 3) float32 OpenCV-convention geometry, NaN where
    invalid. intrinsics_norm: normalized 3x3 camera matrix.
    """
    h, w = rgb.shape[:2]
    bg_mesh = geom_core.grid_mesh(
        np.ascontiguousarray(background_points), max_depth_ratio=BACKGROUND_MAX_DEPTH_RATIO
    )
    parts = [("background", bg_mesh, png_bytes(background), "image/png")]
    photo_png = png_bytes(rgb)
    objects = []
    for layer in layers:
        # Erode by a pixel: boundary pixels mix object and background depth.
        mesh_mask = ndimage.binary_erosion(layer.mask, iterations=1)
        mesh = geom_core.grid_mesh(
            points, mask=np.ascontiguousarray(mesh_mask), max_depth_ratio=OBJECT_MAX_DEPTH_RATIO
        )
        parts.append((layer.id, mesh, photo_png, "image/png"))
        objects.append(scene_json.proposed_object(layer.id, layer.score, f"masks/{layer.id}.png"))

    intrinsics = scene_json.intrinsics_from_normalized(intrinsics_norm, w, h)
    scene = scene_json.build_scene(
        intrinsics,
        objects,
        source_uri="source.png",
        background_image_uri="background.png",
        background_asset_uri="scene.glb",
    )
    return LayeredScene(
        glb=geom_core.write_glb_scene(parts),
        scene=scene,
        intrinsics=intrinsics,
        overlay=overlay(rgb, [layer.mask for layer in layers]),
    )


def write_outputs(
    out_dir: pathlib.Path,
    result: LayeredScene,
    layers: list[Layer],
    rgb: np.ndarray,
    background: np.ndarray,
) -> None:
    (out_dir / "masks").mkdir(parents=True, exist_ok=True)
    for layer in layers:
        Image.fromarray((layer.mask * 255).astype(np.uint8)).save(out_dir / "masks" / f"{layer.id}.png")
    (out_dir / "scene.glb").write_bytes(result.glb)
    (out_dir / "scene.json").write_text(json.dumps(result.scene, indent=2))
    (out_dir / "camera.json").write_text(json.dumps(result.intrinsics, indent=2))
    Image.fromarray(rgb).save(out_dir / "source.png")
    Image.fromarray(background).save(out_dir / "background.png")
    Image.fromarray(result.overlay).save(out_dir / "overlay.png")
