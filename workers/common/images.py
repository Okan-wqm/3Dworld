"""Image loading shared by all workers (model-free, unit-tested)."""

from __future__ import annotations

import io
import pathlib

import numpy as np
from PIL import Image, ImageOps

MIN_SIDE = 32


def load_image(path: str | pathlib.Path, max_side: int) -> np.ndarray:
    """Loads an image as RGB uint8 (H, W, 3), upright and resized so its longest side
    is at most `max_side`.

    - EXIF orientation is applied, so phone photos are processed the way browsers show
      them (clicks made in the editor hit the right pixels).
    - Palette, grayscale and RGBA images are converted to RGB.
    - Images smaller than `MIN_SIDE` pixels on a side are rejected with `ValueError`.
    """
    with Image.open(path) as raw:
        img = ImageOps.exif_transpose(raw).convert("RGB")
    img.thumbnail((max_side, max_side))
    if min(img.size) < MIN_SIDE:
        raise ValueError(
            f"{path}: image is {img.size[0]}x{img.size[1]}; need at least {MIN_SIDE} px per side"
        )
    return np.asarray(img).copy()


def png_bytes(rgb: np.ndarray) -> bytes:
    """Encodes an RGB uint8 array as PNG."""
    buf = io.BytesIO()
    Image.fromarray(rgb).save(buf, format="PNG")
    return buf.getvalue()
