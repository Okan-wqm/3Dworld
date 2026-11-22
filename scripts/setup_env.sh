#!/usr/bin/env bash
# Reproducible Python environment for 3Dworld (every session starts from a fresh
# container: run this first).
#
#   scripts/setup_env.sh            model-free stack: build geom_core, lint, run tests
#   scripts/setup_env.sh --models   + PyTorch (CPU), MoGe, SAM 2 for the workers
#   scripts/setup_env.sh --models --gpu   same, with the CUDA build of PyTorch
#
# The virtualenv goes to $VENV (default: .venv). MoGe and sam2 are cloned at pinned
# commits into .deps/ and installed with --no-deps, so the forbidden or unneeded extras
# their own requirements would pull in are never installed (see LICENSES.md).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${VENV:-$ROOT/.venv}"
PYTHON="${PYTHON:-python3}"
MODELS=0
TORCH_INDEX="https://download.pytorch.org/whl/cpu"

for arg in "$@"; do
  case "$arg" in
    --models) MODELS=1 ;;
    --gpu) TORCH_INDEX="https://download.pytorch.org/whl/cu128" ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

MOGE_URL=https://github.com/microsoft/MoGe.git
MOGE_SHA=74fbce054ebed49800de42d0ad0e83495065719a
SAM2_URL=https://github.com/facebookresearch/sam2.git
SAM2_SHA=2b90b9f5ceec907a1c18123530e92e794ad901a4

clone_at() {  # url sha dir
  if [ "$(git -C "$3" rev-parse HEAD 2>/dev/null || true)" != "$2" ]; then
    rm -rf "$3"
    git init -q "$3"
    git -C "$3" fetch -q --depth 1 "$1" "$2"
    git -C "$3" checkout -q FETCH_HEAD
  fi
}

"$PYTHON" -m venv "$VENV"
# shellcheck disable=SC1091
. "$VENV/bin/activate"
PIP=(python -m pip install -q -c "$ROOT/requirements/constraints.txt")

"${PIP[@]}" -r "$ROOT/requirements/base.txt"

if [ "$MODELS" = 1 ]; then
  "${PIP[@]}" --index-url "$TORCH_INDEX" torch==2.15.0 torchvision==0.29.2
  "${PIP[@]}" -r "$ROOT/requirements/models.txt"
  clone_at "$MOGE_URL" "$MOGE_SHA" "$ROOT/.deps/MoGe"
  clone_at "$SAM2_URL" "$SAM2_SHA" "$ROOT/.deps/sam2"
  "${PIP[@]}" --no-deps -e "$ROOT/.deps/MoGe"
  SAM2_BUILD_CUDA=0 "${PIP[@]}" --no-deps --no-build-isolation -e "$ROOT/.deps/sam2"
fi

maturin develop --release -q -m "$ROOT/crates/geom-py/Cargo.toml"
echo "Environment ready: . $VENV/bin/activate"
