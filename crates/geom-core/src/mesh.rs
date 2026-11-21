//! Triangle meshes built from point maps ("depth meshes", the 2.5D layers of PLAN.md).

use glam::{Vec2, Vec3};
use scene_schema::coords::opencv_to_gltf;

use crate::pointmap::PointMap;
use crate::{GeomError, check_len};

/// Indexed triangle mesh in the **glTF convention**, with texture coordinates that map
/// onto the source image (glTF UV origin is the top-left corner of the image).
#[derive(Debug, Clone, Default, PartialEq)]
pub struct Mesh {
    pub positions: Vec<Vec3>,
    pub uvs: Vec<Vec2>,
    /// Counter-clockwise triangles (front faces point toward the original camera).
    pub indices: Vec<u32>,
}

impl Mesh {
    pub fn triangle_count(&self) -> usize {
        self.indices.len() / 3
    }

    /// Axis-aligned bounds `(min, max)`; `None` for an empty mesh.
    pub fn bounds(&self) -> Option<(Vec3, Vec3)> {
        let first = *self.positions.first()?;
        Some(
            self.positions
                .iter()
                .fold((first, first), |(lo, hi), &p| (lo.min(p), hi.max(p))),
        )
    }
}

#[derive(Debug, Clone, Copy)]
pub struct GridMeshOptions<'a> {
    /// Only pixels where the mask is `true` become vertices. Row-major, same size as the
    /// point map. `None` keeps every valid pixel.
    pub mask: Option<&'a [bool]>,
    /// A triangle is dropped when `max_depth / min_depth - 1` of its corners exceeds this.
    /// Cuts the mesh at depth discontinuities (object edges) instead of stretching
    /// triangles across them. `0.04` = 4 % relative jump.
    pub max_depth_ratio: f32,
    /// Take every `stride`-th pixel in both directions (1 = full resolution).
    pub stride: u32,
}

impl Default for GridMeshOptions<'_> {
    fn default() -> Self {
        Self {
            mask: None,
            max_depth_ratio: 0.04,
            stride: 1,
        }
    }
}

const NO_VERTEX: u32 = u32::MAX;

/// Triangulates the pixel grid of a point map.
///
/// Every sampled, valid (and masked) pixel becomes a vertex; each grid cell yields up to
/// two triangles, skipping triangles that touch an invalid pixel or span a depth
/// discontinuity.
pub fn grid_mesh(pm: &PointMap, opts: &GridMeshOptions) -> Result<Mesh, GeomError> {
    if opts.stride == 0 {
        return Err(GeomError::ZeroStride);
    }
    if let Some(mask) = opts.mask {
        check_len(pm.width, pm.height, mask.len())?;
    }
    let s = opts.stride;
    let cols = (pm.width - 1) / s + 1;
    let rows = (pm.height - 1) / s + 1;

    // 1. Assign compact vertex indices to sampled, valid, masked pixels.
    let mut vertex_of = vec![NO_VERTEX; (cols * rows) as usize];
    let mut positions = Vec::new();
    let mut uvs = Vec::new();
    let (w, h) = (pm.width as f32, pm.height as f32);
    for gr in 0..rows {
        for gc in 0..cols {
            let (col, row) = (gc * s, gr * s);
            let idx = (row * pm.width + col) as usize;
            let p = pm.points[idx];
            let masked = opts.mask.is_none_or(|m| m[idx]);
            if masked && PointMap::is_valid(p) {
                vertex_of[(gr * cols + gc) as usize] = positions.len() as u32;
                positions.push(opencv_to_gltf(p));
                uvs.push(Vec2::new((col as f32 + 0.5) / w, (row as f32 + 0.5) / h));
            }
        }
    }
    if positions.len() >= NO_VERTEX as usize {
        return Err(GeomError::TooManyVertices(positions.len()));
    }

    // 2. Emit triangles, one grid row of cells at a time.
    let depth = |v: u32| -positions[v as usize].z; // glTF -Z is OpenCV +Z
    let max_ratio = 1.0 + opts.max_depth_ratio;
    let keep = |a: u32, b: u32, c: u32| {
        if a == NO_VERTEX || b == NO_VERTEX || c == NO_VERTEX {
            return false;
        }
        let (za, zb, zc) = (depth(a), depth(b), depth(c));
        za.max(zb).max(zc) <= za.min(zb).min(zc) * max_ratio
    };
    let row_triangles = |gr: u32| {
        let mut out = Vec::new();
        for gc in 0..cols.saturating_sub(1) {
            let v = |r: u32, c: u32| vertex_of[(r * cols + c) as usize];
            // a b
            // c d   (image layout; row grows downward)
            let (a, b) = (v(gr, gc), v(gr, gc + 1));
            let (c, d) = (v(gr + 1, gc), v(gr + 1, gc + 1));
            // Counter-clockwise as seen from the camera in glTF space.
            if keep(a, c, b) {
                out.extend([a, c, b]);
            }
            if keep(b, c, d) {
                out.extend([b, c, d]);
            }
        }
        out
    };
    let cell_rows = 0..rows.saturating_sub(1);
    #[cfg(feature = "parallel")]
    let indices: Vec<u32> = {
        use rayon::prelude::*;
        cell_rows
            .into_par_iter()
            .map(row_triangles)
            .collect::<Vec<_>>()
            .concat()
    };
    #[cfg(not(feature = "parallel"))]
    let indices: Vec<u32> = cell_rows.flat_map(row_triangles).collect();

    let mut mesh = Mesh {
        positions,
        uvs,
        indices,
    };
    drop_unused_vertices(&mut mesh);
    Ok(mesh)
}

/// Removes vertices that no triangle references (isolated pixels, cut edges).
fn drop_unused_vertices(mesh: &mut Mesh) {
    let mut remap = vec![NO_VERTEX; mesh.positions.len()];
    for &i in &mesh.indices {
        remap[i as usize] = 0;
    }
    let mut next = 0u32;
    let mut positions = Vec::with_capacity(mesh.positions.len());
    let mut uvs = Vec::with_capacity(mesh.uvs.len());
    for (old, slot) in remap.iter_mut().enumerate() {
        if *slot != NO_VERTEX {
            *slot = next;
            next += 1;
            positions.push(mesh.positions[old]);
            uvs.push(mesh.uvs[old]);
        }
    }
    for i in &mut mesh.indices {
        *i = remap[*i as usize];
    }
    mesh.positions = positions;
    mesh.uvs = uvs;
}

#[cfg(test)]
mod tests {
    use super::*;
    use scene_schema::Intrinsics;

    fn flat(w: u32, h: u32, z: f32) -> PointMap {
        let k = Intrinsics::from_fov_x(1.0, w, h);
        PointMap::from_depth(&vec![z; (w * h) as usize], &k).unwrap()
    }

    #[test]
    fn full_plane_has_two_triangles_per_cell() {
        let m = grid_mesh(&flat(4, 3, 2.0), &GridMeshOptions::default()).unwrap();
        assert_eq!(m.positions.len(), 12);
        assert_eq!(m.triangle_count(), 3 * 2 * 2);
    }

    #[test]
    fn plane_ends_up_in_front_of_camera_in_gltf() {
        let m = grid_mesh(&flat(4, 3, 2.0), &GridMeshOptions::default()).unwrap();
        assert!(m.positions.iter().all(|p| (p.z + 2.0).abs() < 1e-5));
    }

    #[test]
    fn front_faces_point_toward_camera() {
        let m = grid_mesh(&flat(4, 3, 2.0), &GridMeshOptions::default()).unwrap();
        for t in m.indices.chunks(3) {
            let [a, b, c] = [0, 1, 2].map(|i| m.positions[t[i] as usize]);
            let normal = (b - a).cross(c - a);
            // Camera at origin looking along -Z: a front face's normal points to +Z.
            assert!(normal.z > 0.0, "triangle {t:?} faces away");
        }
    }

    #[test]
    fn depth_step_is_not_bridged() {
        // Left half at 1 m, right half at 3 m: no triangle may connect them.
        let (w, h) = (6, 4);
        let k = Intrinsics::from_fov_x(1.0, w, h);
        let depth: Vec<f32> = (0..w * h)
            .map(|i| if i % w < 3 { 1.0 } else { 3.0 })
            .collect();
        let pm = PointMap::from_depth(&depth, &k).unwrap();
        let m = grid_mesh(&pm, &GridMeshOptions::default()).unwrap();
        // Each 3-wide half has 2x3 cells -> 12 triangles; the seam column is dropped.
        assert_eq!(m.triangle_count(), 24);
        for t in m.indices.chunks(3) {
            let zs: Vec<f32> = t.iter().map(|&i| -m.positions[i as usize].z).collect();
            assert!(zs.iter().all(|&z| (z - zs[0]).abs() < 1e-5));
        }
    }

    #[test]
    fn mask_restricts_vertices() {
        let pm = flat(4, 4, 1.0);
        let mask: Vec<bool> = (0..16).map(|i| i % 4 < 2).collect(); // left two columns
        let opts = GridMeshOptions {
            mask: Some(&mask),
            ..Default::default()
        };
        let m = grid_mesh(&pm, &opts).unwrap();
        assert_eq!(m.positions.len(), 8);
        assert_eq!(m.triangle_count(), 6);
    }

    #[test]
    fn invalid_pixels_and_orphans_are_removed() {
        let k = Intrinsics::from_fov_x(1.0, 3, 3);
        let mut depth = vec![1.0; 9];
        depth[4] = f32::NAN; // center pixel invalid
        let pm = PointMap::from_depth(&depth, &k).unwrap();
        let m = grid_mesh(&pm, &GridMeshOptions::default()).unwrap();
        // Only the top-left and bottom-right corner triangles avoid the center pixel.
        assert_eq!(m.triangle_count(), 2);
        // 8 valid pixels, but the top-right and bottom-left corners are orphans.
        assert_eq!(m.positions.len(), 6);
        assert!(m.indices.iter().all(|&i| (i as usize) < m.positions.len()));
    }

    #[test]
    fn stride_downsamples() {
        let m = grid_mesh(
            &flat(9, 9, 1.0),
            &GridMeshOptions {
                stride: 4,
                ..Default::default()
            },
        )
        .unwrap();
        assert_eq!(m.positions.len(), 9);
        assert_eq!(m.triangle_count(), 8);
    }

    #[test]
    fn uvs_are_pixel_centers() {
        let m = grid_mesh(&flat(2, 2, 1.0), &GridMeshOptions::default()).unwrap();
        assert!(m.uvs.contains(&Vec2::new(0.25, 0.25)));
        assert!(m.uvs.contains(&Vec2::new(0.75, 0.75)));
    }

    #[test]
    fn zero_stride_is_rejected() {
        let opts = GridMeshOptions {
            stride: 0,
            ..Default::default()
        };
        assert_eq!(
            grid_mesh(&flat(2, 2, 1.0), &opts),
            Err(GeomError::ZeroStride)
        );
    }
}
