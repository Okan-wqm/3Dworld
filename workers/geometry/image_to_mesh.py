"""M0: single image -> MoGe-2 geometry -> textured depth mesh (GLB) + camera.

Usage:
    python -m workers.geometry.image_to_mesh IMAGE OUT_DIR [--device cpu|cuda] [--stride N]

Writes to OUT_DIR:
    scene.glb       textured mesh of the whole image, glTF convention, meters
    points.ply      colored point cloud (debug)
    camera.json     intrinsics of the original camera (scene-schema `Intrinsics`)
"""

from __future__ import annotations

import argparse
import functools
import json
import pathlib
import sys
import time
from dataclasses import dataclass

import numpy as np
import torch

import geom_core
from workers.common import scene_json
from workers.common.images import load_image, png_bytes
from workers.common.weights import fetch

MODEL_ID = "Ruicheng/moge-2-vitl"


@dataclass
class Geometry:
    """MoGe-2 output for one image, OpenCV camera convention."""

    points: np.ndarray  # (H, W, 3) float32 meters; NaN where invalid
    intrinsics_norm: np.ndarray  # (3, 3) normalized (fx, cx per width; fy, cy per height)

    @property
    def valid(self) -> np.ndarray:
        return np.isfinite(self.points).all(-1)

    @property
    def fov_x_deg(self) -> float:
        return float(np.degrees(2 * np.arctan(0.5 / self.intrinsics_norm[0, 0])))

    def pixel_intrinsics(self) -> dict:
        h, w = self.points.shape[:2]
        return scene_json.intrinsics_from_normalized(self.intrinsics_norm, w, h)


@functools.cache
def load_moge(device: str):
    """MoGe-2 at its pinned revision; loaded once per process and device."""
    from moge.model.v2 import MoGeModel

    return MoGeModel.from_pretrained(fetch(MODEL_ID, "model.pt")).to(device).eval()


def estimate_geometry(image: np.ndarray, device: str, fov_x: float | None = None) -> Geometry:
    """Runs MoGe-2 on an RGB uint8 image. Pass `fov_x` (degrees) to reuse a known camera,
    e.g. when re-estimating an edited version of the same photo."""
    model = load_moge(device)
    tensor = torch.from_numpy(image).permute(2, 0, 1).float().div(255).to(device)
    with torch.inference_mode():
        # Half precision only helps (and only works) on GPU.
        out = model.infer(tensor, fov_x=fov_x, use_fp16=device.startswith("cuda"))
    points = np.ascontiguousarray(out["points"].cpu().numpy(), dtype=np.float32)
    valid = out["mask"].cpu().numpy().astype(bool) & np.isfinite(points).all(-1)
    points[~valid] = np.nan
    return Geometry(points, out["intrinsics"].cpu().numpy())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("image", type=pathlib.Path)
    ap.add_argument("out_dir", type=pathlib.Path)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--stride", type=int, default=1, help="mesh every n-th pixel")
    ap.add_argument("--max-side", type=int, default=1024, help="resize longest side to this")
    args = ap.parse_args()

    try:
        rgb = load_image(args.image, args.max_side)
    except (OSError, ValueError) as e:
        sys.exit(f"error: {e}")
    h, w = rgb.shape[:2]

    t0 = time.perf_counter()
    load_moge(args.device)
    t1 = time.perf_counter()
    geo = estimate_geometry(rgb, args.device)
    t2 = time.perf_counter()

    # Fail before writing anything: an image with no valid depth has nothing to mesh.
    valid = geo.valid
    if not valid.any():
        sys.exit(f"error: {args.image}: MoGe-2 found no valid depth; nothing written")

    points = geo.points
    intrinsics = geo.pixel_intrinsics()
    mesh = geom_core.grid_mesh(points, max_depth_ratio=0.04, stride=args.stride)
    glb = mesh.to_glb(png_bytes(rgb), "image/png")
    flat = points.reshape(-1, 3)
    keep = valid.reshape(-1)
    ply = geom_core.write_ply_points(
        geom_core.opencv_to_gltf(np.ascontiguousarray(flat[keep])),
        np.ascontiguousarray(rgb.reshape(-1, 3)[keep]),
    )
    t3 = time.perf_counter()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "scene.glb").write_bytes(glb)
    (args.out_dir / "points.ply").write_bytes(ply)
    (args.out_dir / "camera.json").write_text(json.dumps(intrinsics, indent=2))

    depth = points[..., 2][valid]
    print(
        f"{args.image.name}: {w}x{h}, MoGe-2 on {args.device}: load {t1 - t0:.1f}s, "
        f"inference {t2 - t1:.1f}s, mesh+GLB {1000 * (t3 - t2):.0f} ms\n"
        f"  {mesh}, FOV-x {geo.fov_x_deg:.1f}°, depth {depth.min():.2f}-{depth.max():.2f} m, "
        f"GLB {len(glb) / 1e6:.1f} MB -> {args.out_dir}"
    )


if __name__ == "__main__":
    main()
