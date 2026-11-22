# 3Dworld

Single image → understood, segmented, completed and lifted into an editable 3D scene that can steer generative video models. See [`PLAN.md`](PLAN.md) for the product and technical plan (Turkish).

> **License:** testing and evaluation only, commercial use prohibited — see [`LICENSE`](LICENSE). Third-party components and their licenses are tracked in [`LICENSES.md`](LICENSES.md).

## Status: Phase 0 done, Phase 1 started

| Part | Path | State |
|---|---|---|
| Scene schema: coordinate convention, intrinsics, scene graph, review state machine | `crates/scene-schema` | ✅ tested |
| Geometry core: point map → edge-aware mesh → GLB / PLY | `crates/geom-core` | ✅ tested, ~8× faster than a NumPy reference |
| Python bindings (`import geom_core`) | `crates/geom-py` | ✅ tested |
| Image → MoGe-2 → textured depth mesh | `workers/geometry/image_to_mesh.py` | ✅ runs on CPU (~20 s/image) and GPU |
| Click-to-select objects (SAM 2.1): one encode per image, ~30-60 ms per click on CPU; part/whole candidates, +/- refinement clicks | `workers/segment/propose.py` | ✅ |
| Background filling (LaMa) | `workers/complete/inpaint.py` | ✅ |
| Layered 2.5D scene: object layers + filled background, depth re-fit without seams, multi-mesh GLB | `workers/pipeline/layered_scene.py`, `workers/common/depth_ops.py` | ✅ runs on CPU (~45 s/image) |
| Weight allowlist | `weights/allowlist.txt`, `workers/common/weights.py` | ✅ |
| License gates | `deny.toml`, `scripts/check_blacklist.py`, CI | ✅ |

## Development

Rust:

```bash
cargo test
cargo run --release -p geom-core --example bench
cargo deny check licenses bans sources
```

Python bindings (inside a virtualenv):

```bash
pip install maturin numpy pytest
(cd crates/geom-py && maturin develop --release)
pytest -q crates/geom-py/tests
```

Image to mesh with MoGe-2 (needs PyTorch and MoGe installed **without** its optional CUDA extras; see LICENSES.md for what must not be installed):

```bash
python -m workers.geometry.image_to_mesh photo.jpg out/photo
```

Layered scene from clicked objects (pixel coordinates of the resized image; `X,Y,-` / `X,Y,+` refine the previous object):

```bash
python -m workers.pipeline.layered_scene photo.jpg out/photo --click 230,430 --click 460,400
```

Output is in the glTF convention (+Y up, camera looks along −Z, meters); the original camera sits at the origin. `out/photo/camera.json` holds its intrinsics.
