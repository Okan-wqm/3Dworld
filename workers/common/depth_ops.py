"""Pure NumPy/SciPy depth operations used by the workers (no model dependencies, so they
are unit-tested in CI without PyTorch)."""

from __future__ import annotations

import numpy as np
from scipy import ndimage


def occluding_fraction(mask: np.ndarray, depth: np.ndarray, gap_px: int, jump: float) -> float:
    """Fraction of the mask's boundary where the mask is clearly in front of what lies
    just outside it.

    A free-standing object (sofa, horse) occludes its surroundings along most of its
    outline. A wall, floor or rug does not: it meets neighboring surfaces at creases, and
    whatever stands on it is *closer*. Image borders are ignored.
    """
    h, w = mask.shape
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
) -> tuple[np.ndarray, float]:
    """Brings the re-estimated background geometry into the photo's geometry.

    MoGe's metric scale changes when objects are removed (they were scale cues), so the
    new estimate is first scaled to match the photo outside the filled region. The
    remaining per-pixel difference (in log depth) is then spread smoothly into the
    filled region, so the background is exactly the photo's geometry outside it and
    joins it without a seam.
    """
    z_new, z_ref = new_points[..., 2], ref_points[..., 2]
    known = ~filled & np.isfinite(z_new) & np.isfinite(z_ref) & (z_new > 0) & (z_ref > 0)
    if known.sum() < 100:
        return np.where(filled[..., None], new_points, ref_points).astype(np.float32), 1.0
    scale = float(np.median(z_ref[known] / z_new[known]))
    resid = np.where(known, np.log(np.where(known, z_ref, 1.0) / (scale * np.where(known, z_new, 1.0))), 0.0)
    # Normalized convolution: smooth fill of the residual from known pixels.
    sigma = 0.05 * max(filled.shape)
    num = ndimage.gaussian_filter(resid, sigma)
    den = ndimage.gaussian_filter(known.astype(np.float64), sigma)
    resid_fill = np.where(known, resid, num / np.maximum(den, 1e-6))
    corrected = new_points * (scale * np.exp(resid_fill))[..., None]
    out = np.where(filled[..., None], corrected, ref_points)
    return out.astype(np.float32), scale
