//! Per-pixel 3D points.

use glam::{Vec2, Vec3};
use scene_schema::Intrinsics;

use crate::{GeomError, check_len};

/// One 3D point per pixel, row-major, in the **OpenCV camera convention** (meters).
/// Invalid pixels (sky, no prediction) are stored as NaN.
#[derive(Debug, Clone, PartialEq)]
pub struct PointMap {
    pub width: u32,
    pub height: u32,
    pub points: Vec<Vec3>,
}

impl PointMap {
    /// Wraps an existing point map (e.g. MoGe-2's `points` output).
    pub fn new(width: u32, height: u32, points: Vec<Vec3>) -> Result<Self, GeomError> {
        check_len(width, height, points.len())?;
        Ok(Self {
            width,
            height,
            points,
        })
    }

    /// Back-projects a depth map (meters along the optical axis). Non-finite or
    /// non-positive depths become invalid points.
    pub fn from_depth(depth: &[f32], intrinsics: &Intrinsics) -> Result<Self, GeomError> {
        let (w, h) = (intrinsics.width, intrinsics.height);
        check_len(w, h, depth.len())?;
        let k = intrinsics;
        if !(k.fx.is_finite() && k.fx > 0.0 && k.fy.is_finite() && k.fy > 0.0) {
            return Err(GeomError::InvalidIntrinsics(format!(
                "focal lengths must be finite and positive, got fx={} fy={}",
                k.fx, k.fy
            )));
        }
        if !(k.cx.is_finite() && k.cy.is_finite()) {
            return Err(GeomError::InvalidIntrinsics(format!(
                "principal point must be finite, got cx={} cy={}",
                k.cx, k.cy
            )));
        }
        let points = depth
            .iter()
            .enumerate()
            .map(|(i, &z)| {
                if z.is_finite() && z > 0.0 {
                    let col = (i % w as usize) as f32 + 0.5;
                    let row = (i / w as usize) as f32 + 0.5;
                    intrinsics.unproject(Vec2::new(col, row), z)
                } else {
                    Vec3::NAN
                }
            })
            .collect();
        Ok(Self {
            width: w,
            height: h,
            points,
        })
    }

    #[inline]
    pub fn get(&self, col: u32, row: u32) -> Vec3 {
        self.points[(row * self.width + col) as usize]
    }

    #[inline]
    pub fn is_valid(p: Vec3) -> bool {
        p.is_finite() && p.z > 0.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn invalid_depth_becomes_nan() {
        let k = Intrinsics::from_fov_x(1.0, 2, 1);
        let pm = PointMap::from_depth(&[1.0, f32::NAN], &k).unwrap();
        assert!(PointMap::is_valid(pm.get(0, 0)));
        assert!(!PointMap::is_valid(pm.get(1, 0)));
    }

    #[test]
    fn size_is_checked() {
        let k = Intrinsics::from_fov_x(1.0, 4, 4);
        assert!(matches!(
            PointMap::from_depth(&[1.0; 3], &k),
            Err(GeomError::SizeMismatch { .. })
        ));
    }

    #[test]
    fn bad_intrinsics_are_rejected() {
        for (fx, cx) in [
            (0.0, 1.0),
            (-1.0, 1.0),
            (f32::NAN, 1.0),
            (1.0, f32::INFINITY),
        ] {
            let k = Intrinsics {
                fx,
                fy: 1.0,
                cx,
                cy: 1.0,
                width: 2,
                height: 2,
            };
            assert!(matches!(
                PointMap::from_depth(&[1.0; 4], &k),
                Err(GeomError::InvalidIntrinsics(_))
            ));
        }
    }

    #[test]
    fn center_pixel_lies_on_optical_axis() {
        let k = Intrinsics::from_fov_x(1.0, 3, 3);
        let pm = PointMap::from_depth(&[2.0; 9], &k).unwrap();
        let c = pm.get(1, 1);
        assert!(c.x.abs() < 1e-6 && c.y.abs() < 1e-6 && (c.z - 2.0).abs() < 1e-6);
    }
}
