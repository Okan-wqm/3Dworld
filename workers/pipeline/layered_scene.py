"""Phase 1 core: single image -> layered 2.5D scene ("Paralaks Sahne").

    python -m workers.pipeline.layered_scene IMAGE OUT_DIR --click X,Y [--click X,Y ...]
    python -m workers.pipeline.layered_scene IMAGE OUT_DIR --auto

Objects are picked by clicking them (one `--click` per object; `X,Y,-` adds a negative
refinement click to the previous object, `X,Y,+` a positive one), or suggested
automatically with `--auto`. Click k always produces object `obj-k`.

Steps (PLAN.md §2):
  [3]  MoGe-2: metric point map + camera
  [2]  SAM 2.1: one mask per clicked object (or automatic suggestions)
  [5]  LaMa: fill the background behind the objects
  [5b] MoGe-2 again on the filled background, fitted to the original depth
  [7]  geom-core: one depth mesh per object + one for the background (layers.py)

Writes OUT_DIR/scene.glb (nodes "background", "obj-01", ...), scene.json, camera.json,
source.png, background.png, masks/obj-XX.png and overlay.png.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import time
import warnings

import numpy as np
import torch

from workers.common.clicks import Click, ClickError, check_bounds, object_id, parse_clicks
from workers.common.depth_ops import fit_background_depth
from workers.common.images import load_image
from workers.complete.inpaint import inpaint, load_lama
from workers.geometry.image_to_mesh import estimate_geometry, load_moge
from workers.pipeline.layers import Layer, build_layers, fill_mask, write_outputs
from workers.segment.propose import ClickSession, load_sam, propose_objects

# Click selections smaller than this (e.g. a click on an object that an earlier click
# already took) are dropped with a warning instead of becoming sliver objects.
MIN_OBJECT_PIXELS = 64


class Models:
    """Models loaded once per process, with their load time recorded separately from
    inference time."""

    def __init__(self, device: str, sam_size: str, timings: dict[str, float]):
        self.device, self.sam_size, self._timings = device, sam_size, timings
        self._sam = self._lama = None

    def _timed(self, name: str, load):
        t = time.perf_counter()
        model = load()
        self._timings[f"load_{name}"] = self._timings.get(f"load_{name}", 0.0) + time.perf_counter() - t
        return model

    def warm_moge(self) -> None:
        self._timed("moge", lambda: load_moge(self.device))

    @property
    def sam(self):
        if self._sam is None:
            self._sam = self._timed("sam", lambda: load_sam(self.sam_size, self.device))
        return self._sam

    @property
    def lama(self):
        if self._lama is None:
            self._lama = self._timed("lama", lambda: load_lama(self.device))
        return self._lama


def select_by_clicks(session: ClickSession, objects: list[list[Click]]) -> list[Layer]:
    layers, taken = [], None
    for index, clicks in enumerate(objects, 1):
        mask, score = session.select(clicks)
        if taken is None:
            taken = np.zeros_like(mask)
        mask &= ~taken  # first click wins where two objects overlap
        taken |= mask
        oid = object_id(index)
        if mask.sum() < MIN_OBJECT_PIXELS:
            warnings.warn(f"{oid}: only {int(mask.sum())} pixels left (already selected?); dropped", stacklevel=2)
            continue
        layers.append(Layer(oid, mask, score))
    return layers


def build_layered_scene(rgb: np.ndarray, models: Models, clicks: list[list[Click]] | None, timings: dict):
    """Runs the model stage, then the pure post-model stage (`layers.build_layers`).
    Returns (result, layers, background, background_scale)."""
    models.warm_moge()
    t = time.perf_counter()
    geo = estimate_geometry(rgb, models.device)
    timings["moge"] = time.perf_counter() - t

    sam = models.sam
    t = time.perf_counter()
    if clicks is None:
        proposals = propose_objects(sam, rgb, geo.points[..., 2])
        layers = [Layer(object_id(i), p.mask, p.score) for i, p in enumerate(proposals, 1)]
    else:
        session = ClickSession(sam, rgb)
        timings["sam_encode"] = time.perf_counter() - t
        t_clicks = time.perf_counter()
        layers = select_by_clicks(session, clicks)
        timings["sam_per_click_ms"] = 1000 * (time.perf_counter() - t_clicks) / max(1, len(clicks))
    timings["sam"] = time.perf_counter() - t

    filled = fill_mask(layers, rgb.shape[:2])
    scale = 1.0
    if filled.any():
        lama = models.lama
        t = time.perf_counter()
        background = inpaint(lama, rgb, filled, models.device)
        timings["lama"] = time.perf_counter() - t
        t = time.perf_counter()
        # Same camera as the photo: without a fixed FOV MoGe re-guesses it for the
        # edited image and the background no longer lines up.
        bg_geo = estimate_geometry(background, models.device, geo.fov_x_deg)
        fit = fit_background_depth(bg_geo.points, geo.points, filled)
        background_points, scale = fit.points, fit.scale
        timings["moge_bg"] = time.perf_counter() - t
    else:
        background, background_points = rgb, geo.points

    t = time.perf_counter()
    result = build_layers(rgb, geo.points, geo.intrinsics_norm, layers, background, background_points)
    timings["mesh_glb"] = time.perf_counter() - t
    return result, layers, background, scale


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("image", type=pathlib.Path)
    ap.add_argument("out_dir", type=pathlib.Path)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--max-side", type=int, default=768,
                    help="resize longest side to this (smaller than image_to_mesh's 1024: "
                         "three models run per image)")  # fmt: skip
    ap.add_argument("--sam", choices=["large", "small"], default=None,
                    help="default: large on GPU, small on CPU")  # fmt: skip
    ap.add_argument("--click", action="append", default=[], metavar="X,Y[,+|-]",
                    help="select an object at pixel X,Y of the resized image")  # fmt: skip
    ap.add_argument("--auto", action="store_true", help="suggest objects automatically")
    args = ap.parse_args()
    if not args.click and not args.auto:
        ap.error("pick objects with --click X,Y (repeatable) or use --auto")
    try:
        clicks = None if args.auto else parse_clicks(args.click)
        rgb = load_image(args.image, args.max_side)
        if clicks is not None:
            check_bounds(clicks, rgb.shape[1], rgb.shape[0])
    except ClickError as e:
        ap.error(str(e))
    except (OSError, ValueError) as e:
        sys.exit(f"error: {e}")

    timings: dict[str, float] = {}
    sam_size = args.sam or ("large" if args.device.startswith("cuda") else "small")
    models = Models(args.device, sam_size, timings)
    result, layers, background, scale = build_layered_scene(rgb, models, clicks, timings)
    write_outputs(args.out_dir, result, layers, rgb, background)

    h, w = rgb.shape[:2]
    print(f"{args.image.name}: {w}x{h}, {len(layers)} objects, bg depth scale {scale:.3f}, "
          f"GLB {len(result.glb) / 1e6:.1f} MB")  # fmt: skip
    print("  " + ", ".join(f"{k} {v:.1f}" + ("" if k.endswith("_ms") else "s") for k, v in timings.items()))


if __name__ == "__main__":
    main()
