# Rules for coding sessions in 3Dworld

This project is built by LLM coding sessions, each starting in a fresh container. These are the rules the repository already enforces or relies on; checks are named so you can run them.

## Start and finish

- Start: `make setup` (or `make setup-models` when you run models; `GPU=1` for CUDA). Use `.venv/bin/python`.
- Finish: `make ci` must pass. It is exactly what CI runs: lint (rustfmt, clippy `-D warnings`, ruff, mypy strict on model-free modules), Rust and Python tests, the schema contract, the license gates.
- After changing Rust code used from Python, or the type stub `crates/geom-py/geom_core.pyi` (it is installed with the bindings): `make bindings`. Keep the stub in sync with the `#[pyfunction]`s.
- CI uses only the model-free environment (`make setup`). Code checked by mypy or imported by default tests must not need the model stack at import time; check with a `make setup` environment before pushing.
- The Rust toolchain version lives only in `rust-toolchain.toml`; Python versions only in `requirements/` (exact pins, transitive pins in `constraints.txt`).

## Licenses (hard rule)

- Every third-party package, model or service must be ✅ in `LICENSES.md` before it is used. Allowed: MIT, Apache-2.0, BSD, ISC, Zlib, HPND, MPL-2.0; named exceptions are listed there. Forbidden: non-commercial, research-only, AGPL, embedded GPL, revenue/user-threshold or region-restricted licenses.
- Never install the forbidden packages listed in `LICENSES.md` (e.g. nvdiffrast, nvdiffrec, diffoctreerast, diff-gaussian-rasterization, pymeshfix, igraph, plyfile, ultralytics, imageio-ffmpeg, RMBG weights). `scripts/check_blacklist.py` fails the build if one appears in a dependency file, script, Makefile or workflow.
- MoGe and sam2 are installed from pinned commits with `--no-deps` by `scripts/setup_env.sh`; never install them with their own dependencies.
- Model weights are loaded only through `workers.common.weights.fetch(model_id, filename)`: the id must be in `weights/allowlist.txt` (✅ in LICENSES.md) and have a pinned revision in `weights/revisions.txt`. `workers/tests/test_licenses.py` checks code, allowlist and LICENSES.md against each other.
- Weights and generated outputs (`*.glb`, `*.ply`, `out/`) never go into git.
- The project's own license (`LICENSE`) is evaluation-only, no commercial use.

## Conventions the code depends on

- Coordinates: `scene.json` and all written files use glTF (+X right, +Y up, camera looks along −Z, meters; the original camera is the world origin). Model outputs are OpenCV (+Y down, +Z forward). Convert only with `scene_schema::coords` (Rust) or `geom_core.opencv_to_gltf` / `geom_core.grid_mesh` (Python), never by hand.
- Pixel centers are at `(col + 0.5, row + 0.5)`; intrinsics are in pixels (`scene_schema::Intrinsics`), MoGe's normalized intrinsics are converted by `scene_json.intrinsics_from_normalized`.
- `scene.json` is the cross-language contract. Rust (`crates/scene-schema`) defines it and exports `schema/scene.schema.json`; Python builds it only through `workers/common/scene_json.py`; the committed fixture `schema/fixtures/scene.example.json` is deserialized by a Rust test. Unknown fields are rejected on both sides. After changing the schema or the builder, run `make schema` and commit the regenerated files.
- Object review state follows `scene_schema::status`: stages advance one at a time; user edits mark downstream outputs stale and never trigger regeneration on their own.
- Click `k` on the command line produces object `obj-k`.

## Tests

- Model-free code (`workers/common/`, `workers/pipeline/layers.py`) is unit-tested and type-checked; CI runs without model weights.
- Tests that need weights are marked `models` and skipped by default (`pytest -m models` to run them).
- Changes to the layered-scene pipeline that are meant to be behavior-preserving must give byte-identical outputs (`sha256sum`) to a run before the change, same clicks, same device.
