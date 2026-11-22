"""Background filling with LaMa (Apache-2.0).

Weights: TorchScript export of big-lama (`JosephCatrambone/big-lama-torchscript`,
Apache-2.0, port of advimman/lama). Needs only PyTorch.
"""

from __future__ import annotations

import numpy as np
import torch
from huggingface_hub import hf_hub_download

from workers.common.weights import require_allowed

MODEL = ("JosephCatrambone/big-lama-torchscript", "lama.pt")


def load_lama(device: str = "cpu"):
    path = hf_hub_download(require_allowed(MODEL[0]), MODEL[1])
    return torch.jit.load(path, map_location=device).eval()


def inpaint(lama, image: np.ndarray, mask: np.ndarray, device: str = "cpu") -> np.ndarray:
    """Fills `mask` (H, W bool) in `image` (H, W, 3 uint8). Returns uint8 (H, W, 3).

    Pixels outside the mask are copied back from the input unchanged.
    """
    h, w = mask.shape
    # LaMa needs sides divisible by 8.
    ph, pw = (-h) % 8, (-w) % 8
    img = np.pad(image, ((0, ph), (0, pw), (0, 0)), mode="reflect")
    msk = np.pad(mask, ((0, ph), (0, pw)), mode="constant")
    img_t = torch.from_numpy(img).permute(2, 0, 1)[None].float().div(255).to(device)
    msk_t = torch.from_numpy(msk)[None, None].float().to(device)
    with torch.inference_mode():
        out = lama(img_t, msk_t)
    out = (out[0].permute(1, 2, 0).clamp(0, 1).mul(255).round().byte().cpu().numpy())[:h, :w]
    result = image.copy()
    result[mask] = out[mask]
    return result
