//! Python bindings for `geom-core`, imported as `geom_core`.
//!
//! Arrays are exchanged as NumPy arrays. Heavy work runs with the GIL released so
//! worker threads are not blocked.

use geom_core::{GridMeshOptions, Mesh, PointMap, Texture};
use glam::Vec3;
use numpy::ndarray::Array2;
use numpy::{IntoPyArray, PyArray2, PyReadonlyArray2, PyReadonlyArray3, PyUntypedArrayMethods};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use scene_schema::Intrinsics;

fn value_err(e: impl std::fmt::Display) -> PyErr {
    PyValueError::new_err(e.to_string())
}

fn to_vec3(flat: &[f32]) -> Vec<Vec3> {
    let (triples, _) = flat.as_chunks::<3>();
    triples.iter().map(|&c| Vec3::from_array(c)).collect()
}

fn vec3_array<'py>(py: Python<'py>, v: &[Vec3]) -> Bound<'py, PyArray2<f32>> {
    let flat: Vec<f32> = v.iter().flat_map(|p| p.to_array()).collect();
    Array2::from_shape_vec((v.len(), 3), flat)
        .expect("shape matches")
        .into_pyarray(py)
}

/// Triangle mesh in the glTF convention (+Y up, camera looks along -Z, meters).
#[pyclass(name = "Mesh", module = "geom_core", frozen)]
struct PyMesh {
    inner: Mesh,
}

#[pymethods]
impl PyMesh {
    /// Vertex positions, shape (N, 3), float32.
    #[getter]
    fn positions<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray2<f32>> {
        vec3_array(py, &self.inner.positions)
    }

    /// Texture coordinates into the source image, shape (N, 2), float32.
    #[getter]
    fn uvs<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray2<f32>> {
        let flat: Vec<f32> = self.inner.uvs.iter().flat_map(|p| p.to_array()).collect();
        Array2::from_shape_vec((self.inner.uvs.len(), 2), flat)
            .expect("shape matches")
            .into_pyarray(py)
    }

    /// Triangle indices, shape (T, 3), uint32, counter-clockwise.
    #[getter]
    fn indices<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray2<u32>> {
        Array2::from_shape_vec((self.inner.triangle_count(), 3), self.inner.indices.clone())
            .expect("shape matches")
            .into_pyarray(py)
    }

    #[getter]
    fn triangle_count(&self) -> usize {
        self.inner.triangle_count()
    }

    /// Serializes to GLB bytes. `texture` is encoded PNG or JPEG bytes of the source image.
    #[pyo3(signature = (texture=None, mime_type="image/png"))]
    fn to_glb<'py>(
        &self,
        py: Python<'py>,
        texture: Option<&[u8]>,
        mime_type: &str,
    ) -> PyResult<Bound<'py, PyBytes>> {
        let tex = texture.map(|bytes| Texture { bytes, mime_type });
        let glb = py
            .detach(|| geom_core::write_glb(&self.inner, tex))
            .map_err(value_err)?;
        Ok(PyBytes::new(py, &glb))
    }

    fn __repr__(&self) -> String {
        format!(
            "Mesh(vertices={}, triangles={})",
            self.inner.positions.len(),
            self.inner.triangle_count()
        )
    }
}

/// Builds an edge-aware mesh from a per-pixel point map.
///
/// points: (H, W, 3) float32 in the OpenCV camera convention (e.g. MoGe-2 output).
///   Invalid pixels must be NaN or have z <= 0.
/// mask: optional (H, W) bool; only masked pixels become vertices.
/// max_depth_ratio: triangles whose corner depths differ by more than this relative
///   amount are dropped (cuts at object edges).
/// stride: sample every n-th pixel.
#[pyfunction]
#[pyo3(signature = (points, mask=None, max_depth_ratio=0.04, stride=1))]
fn grid_mesh(
    py: Python<'_>,
    points: PyReadonlyArray3<'_, f32>,
    mask: Option<PyReadonlyArray2<'_, bool>>,
    max_depth_ratio: f32,
    stride: u32,
) -> PyResult<PyMesh> {
    let shape = points.shape();
    if shape[2] != 3 {
        return Err(value_err("points must have shape (H, W, 3)"));
    }
    let (h, w) = (shape[0] as u32, shape[1] as u32);
    let flat = points
        .as_slice()
        .map_err(|_| value_err("points must be C-contiguous"))?;
    let mask_slice = match &mask {
        Some(m) => {
            if m.shape() != [h as usize, w as usize] {
                return Err(value_err("mask must have shape (H, W)"));
            }
            Some(
                m.as_slice()
                    .map_err(|_| value_err("mask must be C-contiguous"))?,
            )
        }
        None => None,
    };
    let mesh = py
        .detach(|| {
            let pm = PointMap::new(w, h, to_vec3(flat))?;
            geom_core::grid_mesh(
                &pm,
                &GridMeshOptions {
                    mask: mask_slice,
                    max_depth_ratio,
                    stride,
                },
            )
        })
        .map_err(value_err)?;
    Ok(PyMesh { inner: mesh })
}

/// Back-projects a depth map (H, W) in meters to an (H, W, 3) OpenCV point map.
/// Intrinsics are in pixels.
#[pyfunction]
fn points_from_depth<'py>(
    py: Python<'py>,
    depth: PyReadonlyArray2<'py, f32>,
    fx: f32,
    fy: f32,
    cx: f32,
    cy: f32,
) -> PyResult<Bound<'py, PyAny>> {
    let shape = depth.shape();
    let (h, w) = (shape[0] as u32, shape[1] as u32);
    let flat = depth
        .as_slice()
        .map_err(|_| value_err("depth must be C-contiguous"))?;
    let k = Intrinsics {
        fx,
        fy,
        cx,
        cy,
        width: w,
        height: h,
    };
    let pm = py
        .detach(|| PointMap::from_depth(flat, &k))
        .map_err(value_err)?;
    let flat: Vec<f32> = pm.points.iter().flat_map(|p| p.to_array()).collect();
    let arr = numpy::ndarray::Array3::from_shape_vec((h as usize, w as usize, 3), flat)
        .expect("shape matches");
    Ok(arr.into_pyarray(py).into_any())
}

/// Encodes points (N, 3) float32 and optional colors (N, 3) uint8 as binary PLY bytes.
#[pyfunction]
#[pyo3(signature = (points, colors=None))]
fn write_ply_points<'py>(
    py: Python<'py>,
    points: PyReadonlyArray2<'py, f32>,
    colors: Option<PyReadonlyArray2<'py, u8>>,
) -> PyResult<Bound<'py, PyBytes>> {
    if points.shape()[1] != 3 {
        return Err(value_err("points must have shape (N, 3)"));
    }
    let pts = to_vec3(
        points
            .as_slice()
            .map_err(|_| value_err("points must be C-contiguous"))?,
    );
    let cols: Option<Vec<[u8; 3]>> = match &colors {
        Some(c) => {
            if c.shape() != [pts.len(), 3] {
                return Err(value_err("colors must have shape (N, 3)"));
            }
            let s = c
                .as_slice()
                .map_err(|_| value_err("colors must be C-contiguous"))?;
            Some(s.as_chunks::<3>().0.to_vec())
        }
        None => None,
    };
    let ply = py.detach(|| geom_core::write_ply_points(&pts, cols.as_deref()));
    Ok(PyBytes::new(py, &ply))
}

/// Converts (N, 3) points from the OpenCV to the glTF convention (flips Y and Z).
#[pyfunction]
fn opencv_to_gltf<'py>(
    py: Python<'py>,
    points: PyReadonlyArray2<'py, f32>,
) -> PyResult<Bound<'py, PyArray2<f32>>> {
    let pts = to_vec3(
        points
            .as_slice()
            .map_err(|_| value_err("points must be C-contiguous"))?,
    );
    let out: Vec<Vec3> = pts
        .into_iter()
        .map(scene_schema::coords::opencv_to_gltf)
        .collect();
    Ok(vec3_array(py, &out))
}

/// `(name, mesh, texture bytes, mime type)` as passed from Python.
type PyGlbPart<'py> = (String, PyRef<'py, PyMesh>, Option<Vec<u8>>, String);

/// Writes several named meshes into one GLB.
///
/// parts: list of `(name, mesh, texture_bytes_or_None, mime_type)` tuples, e.g.
///   `[("background", bg_mesh, bg_png, "image/png"), ("obj-1", m1, png, "image/png")]`.
#[pyfunction]
fn write_glb_scene<'py>(
    py: Python<'py>,
    parts: Vec<PyGlbPart<'py>>,
) -> PyResult<Bound<'py, PyBytes>> {
    let glb_parts: Vec<geom_core::GlbPart<'_>> = parts
        .iter()
        .map(|(name, mesh, tex, mime)| geom_core::GlbPart {
            name,
            mesh: &mesh.inner,
            texture: tex.as_deref().map(|bytes| Texture {
                bytes,
                mime_type: mime,
            }),
        })
        .collect();
    let glb = geom_core::write_glb_scene(&glb_parts).map_err(value_err)?;
    Ok(PyBytes::new(py, &glb))
}

#[pymodule]
#[pyo3(name = "geom_core")]
fn geom_core_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyMesh>()?;
    m.add_function(wrap_pyfunction!(write_glb_scene, m)?)?;
    m.add_function(wrap_pyfunction!(grid_mesh, m)?)?;
    m.add_function(wrap_pyfunction!(points_from_depth, m)?)?;
    m.add_function(wrap_pyfunction!(write_ply_points, m)?)?;
    m.add_function(wrap_pyfunction!(opencv_to_gltf, m)?)?;
    Ok(())
}
