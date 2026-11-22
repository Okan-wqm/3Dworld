"""Object proposals with SAM 2.1 (Meta, Apache-2.0).

Two entry points used by the review flow (PLAN.md §1.1, screen 2):
- `ClickSession`: the main interaction, as in the product we are modeling: the user
  clicks an object and gets its mask immediately; more clicks refine it;
- `propose_objects`: optional automatic suggestions for a whole image, filtered to whole
  objects that stand out in depth from their surroundings (walls and floors stay
  background). Slower (tens of seconds on CPU), so it is off by default.

Labels come from the scene-understanding step (VLM), not from here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from huggingface_hub import hf_hub_download
from workers.common.depth_ops import occluding_fraction
from workers.common.weights import require_allowed

# (Hugging Face repo, checkpoint file, sam2 config name)
MODELS = {
    "large": ("facebook/sam2.1-hiera-large", "sam2.1_hiera_large.pt", "configs/sam2.1/sam2.1_hiera_l.yaml"),
    "small": ("facebook/sam2.1-hiera-small", "sam2.1_hiera_small.pt", "configs/sam2.1/sam2.1_hiera_s.yaml"),
}


@dataclass
class Proposal:
    mask: np.ndarray  # (H, W) bool
    score: float  # SAM predicted IoU
    area_frac: float
    occluding: float  # fraction of its outline where it is in front of its surroundings
    bbox: tuple[int, int, int, int]  # x, y, w, h


def load_sam(size: str = "large", device: str = "cpu"):
    from sam2.build_sam import build_sam2

    repo, ckpt, cfg = MODELS[size]
    path = hf_hub_download(require_allowed(repo), ckpt)
    return build_sam2(cfg, path, device=device)


def propose_objects(
    sam,
    image: np.ndarray,
    depth: np.ndarray,
    *,
    points_per_side: int = 24,
    min_area: float = 0.002,
    max_area: float = 0.35,
    min_occluding: float = 0.35,
    max_objects: int = 20,
) -> list[Proposal]:
    """Automatic object proposals.

    image: (H, W, 3) uint8. depth: (H, W) meters, NaN where invalid.
    Keeps masks that occlude their surroundings along a good part of their outline
    (objects, not walls/floors), and whole objects rather than their parts: candidates are visited from large to
    small and a candidate mostly covered by an already kept object is dropped.
    """
    from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator

    gen = SAM2AutomaticMaskGenerator(
        sam,
        points_per_side=points_per_side,
        pred_iou_thresh=0.8,
        stability_score_thresh=0.9,
        min_mask_region_area=int(min_area * image.shape[0] * image.shape[1]),
    )
    with torch.inference_mode():
        raw = gen.generate(image)

    h, w = depth.shape
    gap_px = max(2, int(0.006 * max(h, w)))
    candidates = []
    for r in raw:
        m = r["segmentation"].astype(bool)
        frac = m.mean()
        if not (min_area <= frac <= max_area):
            continue
        occluding = occluding_fraction(m, depth, gap_px, jump=0.03)
        if occluding < min_occluding:
            continue
        candidates.append(
            Proposal(m, float(r["predicted_iou"]), float(frac), occluding, tuple(int(v) for v in r["bbox"]))
        )

    kept: list[Proposal] = []
    covered = np.zeros((h, w), bool)
    for p in sorted(candidates, key=lambda p: p.area_frac, reverse=True):
        if (p.mask & covered).sum() > 0.3 * p.mask.sum():
            continue
        p.mask = p.mask & ~covered
        kept.append(p)
        covered |= p.mask
        if len(kept) == max_objects:
            break
    return kept


class ClickSession:
    """Interactive selection, the main way objects are picked (PLAN.md §1.1, screen 2).

    The image encoder runs once in the constructor (the slow part, ~1-5 s on CPU);
    every click after that only runs SAM's light mask decoder (tens of milliseconds),
    so the user gets a mask back right away.

    Clicks are `(x, y, positive)` in pixels. The first positive click selects an object;
    further clicks refine it: positive adds a missed part, negative removes a wrong one.
    """

    def __init__(self, sam, image: np.ndarray):
        from sam2.sam2_image_predictor import SAM2ImagePredictor

        self._pred = SAM2ImagePredictor(sam)
        with torch.inference_mode():
            self._pred.set_image(image)

    def candidates(self, clicks: list[tuple[float, float, bool]]) -> list[tuple[np.ndarray, float]]:
        """All masks SAM offers for the clicks, from smallest (part) to largest (whole).

        One click is ambiguous (cushion, chair, or chair with cushion?), so SAM returns
        three nested candidates; the UI lets the user switch between them. With several
        clicks the intent is clear and there is a single candidate.
        """
        if not clicks or not clicks[0][2]:
            raise ValueError("the first click must be positive")
        coords = np.array([[x, y] for x, y, _ in clicks], np.float32)
        labels = np.array([1 if pos else 0 for _, _, pos in clicks])
        with torch.inference_mode():
            masks, scores, _ = self._pred.predict(
                point_coords=coords, point_labels=labels, multimask_output=len(clicks) == 1
            )
        out = [(m.astype(bool), float(s)) for m, s in zip(masks, scores)]
        return sorted(out, key=lambda c: c[0].sum())

    def select(
        self, clicks: list[tuple[float, float, bool]], score_margin: float = 0.1
    ) -> tuple[np.ndarray, float]:
        """Default choice: the *whole* object, i.e. the largest candidate whose quality
        score is within `score_margin` of the best. Picking by score alone tends to
        return a part (a cushion instead of the sofa)."""
        cands = self.candidates(clicks)
        best = max(s for _, s in cands)
        return [c for c in cands if c[1] >= best - score_margin][-1]
