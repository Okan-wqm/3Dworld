"""Model weights: the single download path (see LICENSES.md, "Süreç" step 4).

Weights downloaded at runtime are invisible to package license scanners, so every
worker gets its files through `fetch()`, which
- refuses model ids that are not in `weights/allowlist.txt` (license-checked), and
- downloads exactly the revision pinned in `weights/revisions.txt` (reproducible).

`HF_HUB_OFFLINE` is not forced: there is no weight mirror yet, and a fresh session must
be able to download. Set it yourself once weights are cached.
"""

from __future__ import annotations

import pathlib

_WEIGHTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "weights"
ALLOWLIST = _WEIGHTS_DIR / "allowlist.txt"
REVISIONS = _WEIGHTS_DIR / "revisions.txt"


class ForbiddenWeightsError(RuntimeError):
    pass


def _entries(path: pathlib.Path) -> list[list[str]]:
    lines = (ln.strip() for ln in path.read_text().splitlines())
    return [ln.split() for ln in lines if ln and not ln.startswith("#")]


def allowed_ids() -> set[str]:
    return {fields[0] for fields in _entries(ALLOWLIST)}


def pinned_revisions() -> dict[str, str]:
    return {fields[0]: fields[1] for fields in _entries(REVISIONS)}


def require_allowed(model_id: str) -> str:
    """Returns `model_id` if it is on the allowlist, raises otherwise."""
    if model_id not in allowed_ids():
        raise ForbiddenWeightsError(
            f"'{model_id}' is not in weights/allowlist.txt. Check its license and add it "
            "to LICENSES.md and the allowlist before using it."
        )
    return model_id


def fetch(model_id: str, filename: str) -> str:
    """Local path of `filename` from the allowlisted model at its pinned revision."""
    from huggingface_hub import hf_hub_download

    require_allowed(model_id)
    revision = pinned_revisions().get(model_id)
    if revision is None:
        raise ForbiddenWeightsError(
            f"'{model_id}' has no pinned revision in weights/revisions.txt."
        )
    return hf_hub_download(model_id, filename, revision=revision)
