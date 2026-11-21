"""Model weight allowlist (see LICENSES.md, "Süreç" step 4).

Weights downloaded at runtime are invisible to package license scanners, so every
worker resolves model ids through `require_allowed()` before loading anything.
"""

from __future__ import annotations

import pathlib

_ALLOWLIST = pathlib.Path(__file__).resolve().parents[2] / "weights" / "allowlist.txt"


class ForbiddenWeightsError(RuntimeError):
    pass


def allowed_ids() -> set[str]:
    lines = _ALLOWLIST.read_text().splitlines()
    return {ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith("#")}


def require_allowed(model_id: str) -> str:
    """Returns `model_id` if it is on the allowlist, raises otherwise."""
    if model_id not in allowed_ids():
        raise ForbiddenWeightsError(
            f"'{model_id}' is not in weights/allowlist.txt. Check its license and add it "
            "to LICENSES.md and the allowlist before using it."
        )
    return model_id
