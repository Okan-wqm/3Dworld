"""Pure NumPy/SciPy depth operations used by the workers (no model dependencies, so they
are unit-tested in CI without PyTorch)."""

from __future__ import annotations

import warnings
from typing import NamedTuple

import numpy as np
from scipy import ndimage

# Re-estimated background depth more than this far off the photo's scale is reported
# (not rejected): it usually means the filled background looks unlike the photo.
SUSPICIOUS_SCALE = (0.2, 5.0)
MIN_KNOWN_PIXELS = 100


def _check_shapes(**arrays: np.ndarray) -> None:
    """Raises `ValueError` naming the arrays if their image dimensions differ."""
    shapes = {name: a.shape[:2] for name, a in arrays.items()}
    if len(set(shapes.values())) != 1:
        raise ValueError(f"image dimensions differ: {shapes}")


class BackgroundFit(NamedTuple):
    points: np.ndarray  # (H, W, 3) float32
    scale: float  # applied to the re-estimated geometry
    fallback: bool  # True: too few reference pixels, the estimate was used unscaled


def occluding_fraction(mask: np.ndarray, depth: np.ndarray, gap_px: int, jump: float) -> float:
    """Fraction of the mask's boundary where the mask is clearly in front of what lies
    just outside it.

    A free-standing object (sofa, horse) occludes its surroundings along most of its
    outline. A wall, floor or rug does not: it meets neighboring surfaces at creases, and
    whatever stands on it is *closer*. Image borders are ignored. Returns 0.0 when the
    outline has fewer than 20 usable pixels.
    """
    _check_shapes(mask=mask, depth=depth)
    inside_edge = mask & ~ndimage.binary_erosion(mask, iterations=1)
    inside_edge[[0, -1], :] = False
    inside_edge[:, [0, -1]] = False
    ys, xs = np.nonzero(inside_edge)
    if ys.size < 20:
        return 0.0
    # Depth just inside vs. the farthest depth a few pixels outside, per boundary pixel.
    z_in = ndimage.median_filter(np.where(mask, depth, np.nan), size=3)[ys, xs]
    outside = np.where(mask, -np.inf, np.nan_to_num(depth, nan=-np.inf))
    z_out = ndimage.maximum_filter(outside, size=2 * gap_px + 1)[ys, xs]
    ok = np.isfinite(z_in) & np.isfinite(z_out)
    if ok.sum() < 20:
        return 0.0
    return float(np.mean(z_out[ok] > z_in[ok] * (1 + jump)))


def fit_background_depth(
    new_points: np.ndarray, ref_points: np.ndarray, filled: np.ndarray
) -> BackgroundFit:
    """Brings the re-estimated background geometry into the photo's geometry.

    MoGe's metric scale changes when objects are removed (they were scale cues), so the
    new estimate is first scaled to match the photo outside the filled region. The
    remaining per-pixel difference (in log depth) is then spread smoothly into the
    filled region, so the background is exactly the photo's geometry outside it and
    joins it without a seam.

    Problems are reported, never hidden: too few reference pixels sets `fallback` and
    warns; a suspicious scale warns.
    """
    _check_shapes(new_points=new_points, ref_points=ref_points, filled=filled)
    z_new, z_ref = new_points[..., 2], ref_points[..., 2]
    known = ~filled & np.isfinite(z_new) & np.isfinite(z_ref) & (z_new > 0) & (z_ref > 0)
    if known.sum() < MIN_KNOWN_PIXELS:
        warnings.warn(
            f"background fit: only {int(known.sum())} reference pixels; using the "
            "re-estimated depth unscaled",
            stacklevel=2,
        )
        out = np.where(filled[..., None], new_points, ref_points).astype(np.float32)
        return BackgroundFit(out, 1.0, True)
    scale = float(np.median(z_ref[known] / z_new[known]))
    if not SUSPICIOUS_SCALE[0] <= scale <= SUSPICIOUS_SCALE[1]:
        warnings.warn(f"background fit: unusual depth scale {scale:.3g}", stacklevel=2)
    resid = np.where(known, np.log(np.where(known, z_ref, 1.0) / (scale * np.where(known, z_new, 1.0))), 0.0)
    # Normalized convolution: smooth fill of the residual from known pixels.
    sigma = 0.05 * max(filled.shape)
    num = ndimage.gaussian_filter(resid, sigma)
    den = ndimage.gaussian_filter(known.astype(np.float64), sigma)
    resid_fill = np.where(known, resid, num / np.maximum(den, 1e-6))
    corrected = new_points * (scale * np.exp(resid_fill))[..., None]
    out = np.where(filled[..., None], corrected, ref_points)
    return BackgroundFit(out.astype(np.float32), scale, False)
