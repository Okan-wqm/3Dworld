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
import io
import json
import pathlib
import time

import numpy as np
import torch
from PIL import Image

import geom_core
from workers.common.weights import require_allowed

MODEL_ID = "Ruicheng/moge-2-vitl"


def estimate_geometry(image: np.ndarray, device: str) -> dict:
    """Runs MoGe-2. Returns OpenCV-convention points (H, W, 3), validity mask (H, W) and
    normalized intrinsics (3, 3)."""
    from moge.model.v2 import MoGeModel

    model = MoGeModel.from_pretrained(require_allowed(MODEL_ID)).to(device).eval()
    tensor = torch.from_numpy(image).permute(2, 0, 1).float().div(255).to(device)
    with torch.inference_mode():
        # Half precision only helps (and only works) on GPU.
        out = model.infer(tensor, use_fp16=device.startswith("cuda"))
    return {k: v.cpu().numpy() for k, v in out.items() if isinstance(v, torch.Tensor)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("image", type=pathlib.Path)
    ap.add_argument("out_dir", type=pathlib.Path)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--stride", type=int, default=1, help="mesh every n-th pixel")
    ap.add_argument("--max-side", type=int, default=1024, help="resize longest side to this")
    args = ap.parse_args()

    img = Image.open(args.image).convert("RGB")
    img.thumbnail((args.max_side, args.max_side))
    rgb = np.asarray(img)
    h, w = rgb.shape[:2]

    t0 = time.perf_counter()
    geo = estimate_geometry(rgb, args.device)
    t1 = time.perf_counter()

    points = np.ascontiguousarray(geo["points"], dtype=np.float32)
    valid = geo["mask"].astype(bool) & np.isfinite(points).all(-1)
    points[~valid] = np.nan
    k = geo["intrinsics"]
    intrinsics = {
        "fx": float(k[0, 0] * w),
        "fy": float(k[1, 1] * h),
        "cx": float(k[0, 2] * w),
        "cy": float(k[1, 2] * h),
        "width": w,
        "height": h,
    }

    mesh = geom_core.grid_mesh(points, max_depth_ratio=0.04, stride=args.stride)
    png = io.BytesIO()
    img.save(png, format="PNG")
    glb = mesh.to_glb(png.getvalue(), "image/png")

    flat = points.reshape(-1, 3)
    keep = np.isfinite(flat).all(1)
    ply = geom_core.write_ply_points(
        geom_core.opencv_to_gltf(np.ascontiguousarray(flat[keep])),
        np.ascontiguousarray(rgb.reshape(-1, 3)[keep]),
    )
    t2 = time.perf_counter()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "scene.glb").write_bytes(glb)
    (args.out_dir / "points.ply").write_bytes(ply)
    (args.out_dir / "camera.json").write_text(json.dumps(intrinsics, indent=2))

    fov_x = 2 * np.degrees(np.arctan(0.5 * w / intrinsics["fx"]))
    depth = points[..., 2][valid]
    print(
        f"{args.image.name}: {w}x{h}, MoGe-2 on {args.device} {t1 - t0:.1f}s, "
        f"mesh+GLB {1000 * (t2 - t1):.0f} ms\n"
        f"  {mesh}, FOV-x {fov_x:.1f}°, depth {depth.min():.2f}-{depth.max():.2f} m, "
        f"GLB {len(glb) / 1e6:.1f} MB -> {args.out_dir}"
    )


if __name__ == "__main__":
    main()
