# 3Dworld

Single image → understood, segmented, completed and lifted into an editable 3D scene that can steer generative video models. See [`PLAN.md`](PLAN.md) for the product and technical plan (Turkish) and [`CLAUDE.md`](CLAUDE.md) for the rules every coding session follows.

> **License:** testing and evaluation only, commercial use prohibited — see [`LICENSE`](LICENSE). Third-party components and their licenses are tracked in [`LICENSES.md`](LICENSES.md).

## Quick start

Prerequisites: Linux, git, `make`, Python ≥ 3.12, Rust via rustup (the version in `rust-toolchain.toml` is installed automatically), and for `make licenses` [cargo-deny](https://github.com/EmbarkStudios/cargo-deny). A GPU is optional.

```bash
make setup
```

```bash
make ci
```

`make setup` creates `.venv` with pinned versions (`requirements/`) and builds the `geom_core` Python bindings. `make ci` runs exactly what CI runs: lint (rustfmt, clippy, ruff, mypy), Rust and Python tests, the schema contract check and the license gates.

To run the models (PyTorch CPU build, MoGe-2, SAM 2.1, LaMa):

```bash
make setup-models
```

Add `GPU=1` for the CUDA build of PyTorch. Model weights are downloaded from Hugging Face on first use, at the revisions pinned in `weights/revisions.txt`, into the Hugging Face cache (`HF_HOME`, default `~/.cache/huggingface`); they are never committed.

## Running

Layered scene from clicked objects. Click coordinates are pixels of the resized image (longest side 768); `X,Y,+` / `X,Y,-` refine the previous object:

```bash
.venv/bin/python -m workers.pipeline.layered_scene photo.jpg out/photo --click 230,430 --click 460,400
```

Single textured depth mesh of the whole image:

```bash
.venv/bin/python -m workers.geometry.image_to_mesh photo.jpg out/photo
```

Outputs use the glTF convention (+Y up, camera looks along −Z, meters) with the original camera at the origin; `camera.json` holds its intrinsics.

## Status: Phase 0 done, Phase 1 started

| Part | Path |
|---|---|
| Scene schema: coordinate convention, intrinsics, scene graph, review state machine; JSON Schema in `schema/` | `crates/scene-schema` |
| Geometry core: point map → edge-aware mesh → GLB / PLY | `crates/geom-core` |
| Python bindings (`import geom_core`, typed via `geom_core.pyi`) | `crates/geom-py` |
| Image → MoGe-2 → textured depth mesh | `workers/geometry/image_to_mesh.py` |
| Click-to-select objects (SAM 2.1), optional automatic suggestions | `workers/segment/propose.py` |
| Background filling (LaMa) | `workers/complete/inpaint.py` |
| Layered 2.5D scene: model stage + pure, tested post-model stage | `workers/pipeline/layered_scene.py`, `workers/pipeline/layers.py` |
| Shared model-free helpers: scene.json builder, clicks, image loading, depth fitting, weights | `workers/common/` |
| License gates: cargo-deny, forbidden-package check, weights allowlist + pinned revisions | `deny.toml`, `scripts/check_blacklist.py`, `weights/` |

Not built yet (planned in PLAN.md): the HTTP API, the web editor, the WASM build, video encoding, GPU scheduling, full 3D objects.

## Measured performance

Measured in a 4-vCPU cloud container without GPU, weights already cached, `01_HouseIndoor.jpg` from the MoGe examples resized to 768×512, four clicked objects:

| Stage | Time |
|---|---|
| Load MoGe-2 / SAM 2.1 small / LaMa | 5.1 s / 0.6 s / 0.5 s |
| MoGe-2 inference (photo) | 14.3 s |
| SAM image encoding, then per click | 2.3 s, then ~56 ms |
| LaMa background filling | 3.2 s |
| MoGe-2 inference (filled background) | 14.8 s |
| Meshing + GLB (Rust) | 0.3 s |
| **Total** | **≈ 41 s** |

The first run in a fresh container is slower (weight download). Meshing a 1920×1080 frame alone (`cargo run --release -p geom-core --example bench`): ≈ 0.35 s for 4.1 M triangles on the same machine. Outputs are deterministic: repeated runs, and runs in a freshly built environment, produce byte-identical files.
