//! CPU geometry core of 3Dworld.
//!
//! Turns the per-pixel geometry predicted by a depth model (MoGe-2) into meshes and
//! writes them as GLB or PLY. Used from Python GPU workers (via `geom-py`), from the
//! browser (via `geom-wasm`) and from Rust services.
//!
//! Inputs are in the OpenCV camera convention (what models output); outputs written to
//! files are in the glTF convention used by `scene.json`. See [`scene_schema::coords`].

pub mod glb;
pub mod mesh;
pub mod ply;
pub mod pointmap;

pub use glb::{GlbPart, Texture, write_glb, write_glb_scene};
pub use mesh::{GridMeshOptions, Mesh, grid_mesh};
pub use ply::write_ply_points;
pub use pointmap::PointMap;

#[derive(Debug, thiserror::Error, PartialEq)]
pub enum GeomError {
    #[error("expected {expected} values for a {width}x{height} image, got {got}")]
    SizeMismatch {
        width: u32,
        height: u32,
        expected: usize,
        got: usize,
    },
    #[error("stride must be at least 1")]
    ZeroStride,
    #[error("mesh has {0} vertices; GLB indices are limited to u32")]
    TooManyVertices(usize),
}

pub(crate) fn check_len(width: u32, height: u32, got: usize) -> Result<(), GeomError> {
    let expected = width as usize * height as usize;
    if got != expected {
        return Err(GeomError::SizeMismatch {
            width,
            height,
            expected,
            got,
        });
    }
    Ok(())
}
