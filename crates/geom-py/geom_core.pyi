# Type stub for the Rust extension module `geom_core` (crates/geom-py/src/lib.rs).
# Keep in sync with the #[pyfunction]s there; mypy checks callers against it.

from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

SCHEMA_VERSION: int

class Mesh:
    @property
    def positions(self) -> npt.NDArray[np.float32]: ...
    @property
    def uvs(self) -> npt.NDArray[np.float32]: ...
    @property
    def indices(self) -> npt.NDArray[np.uint32]: ...
    @property
    def triangle_count(self) -> int: ...
    def to_glb(self, texture: bytes | None = None, mime_type: str = "image/png") -> bytes: ...

def grid_mesh(
    points: npt.NDArray[np.float32],
    mask: npt.NDArray[np.bool_] | None = None,
    max_depth_ratio: float = 0.04,
    stride: int = 1,
) -> Mesh: ...
def points_from_depth(
    depth: npt.NDArray[np.float32], fx: float, fy: float, cx: float, cy: float
) -> npt.NDArray[np.float32]: ...
def write_ply_points(
    points: npt.NDArray[np.float32], colors: npt.NDArray[np.uint8] | None = None
) -> bytes: ...
def opencv_to_gltf(points: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]: ...
def write_glb_scene(parts: Sequence[tuple[str, Mesh, bytes | None, str]]) -> bytes: ...
