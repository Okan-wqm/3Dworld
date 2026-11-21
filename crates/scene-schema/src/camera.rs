//! Pinhole camera intrinsics.
//!
//! Pixel convention: pixel `(col, row)` covers `[col, col+1) x [row, row+1)` and its
//! center is at `(col + 0.5, row + 0.5)`. Intrinsics are expressed in pixels of an
//! image of size `width x height`, in the OpenCV camera convention (see [`crate::coords`]).

use glam::{Vec2, Vec3};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize, JsonSchema)]
pub struct Intrinsics {
    /// Focal length along X, in pixels.
    pub fx: f32,
    /// Focal length along Y, in pixels.
    pub fy: f32,
    /// Principal point X, in pixels.
    pub cx: f32,
    /// Principal point Y, in pixels.
    pub cy: f32,
    /// Image width in pixels.
    pub width: u32,
    /// Image height in pixels.
    pub height: u32,
}

impl Intrinsics {
    /// Square pixels, principal point at the image center, given horizontal field of view.
    pub fn from_fov_x(fov_x_radians: f32, width: u32, height: u32) -> Self {
        let fx = 0.5 * width as f32 / (0.5 * fov_x_radians).tan();
        Self {
            fx,
            fy: fx,
            cx: 0.5 * width as f32,
            cy: 0.5 * height as f32,
            width,
            height,
        }
    }

    /// Builds intrinsics from normalized values (as returned by MoGe: `fx`, `cx` in
    /// units of image width, `fy`, `cy` in units of image height).
    pub fn from_normalized(fx: f32, fy: f32, cx: f32, cy: f32, width: u32, height: u32) -> Self {
        Self {
            fx: fx * width as f32,
            fy: fy * height as f32,
            cx: cx * width as f32,
            cy: cy * height as f32,
            width,
            height,
        }
    }

    pub fn fov_x(&self) -> f32 {
        2.0 * (0.5 * self.width as f32 / self.fx).atan()
    }

    pub fn fov_y(&self) -> f32 {
        2.0 * (0.5 * self.height as f32 / self.fy).atan()
    }

    /// Back-projects a pixel position (in pixels, not pixel index) at depth `z` (meters,
    /// along the optical axis) to an OpenCV camera-space point.
    #[inline]
    pub fn unproject(&self, pixel: Vec2, z: f32) -> Vec3 {
        Vec3::new(
            (pixel.x - self.cx) / self.fx * z,
            (pixel.y - self.cy) / self.fy * z,
            z,
        )
    }

    /// Projects an OpenCV camera-space point to pixel coordinates. Returns `None` for
    /// points at or behind the camera.
    #[inline]
    pub fn project(&self, p: Vec3) -> Option<Vec2> {
        if p.z <= 0.0 {
            return None;
        }
        Some(Vec2::new(
            self.fx * p.x / p.z + self.cx,
            self.fy * p.y / p.z + self.cy,
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fov_roundtrip() {
        let k = Intrinsics::from_fov_x(60f32.to_radians(), 1920, 1080);
        assert!((k.fov_x() - 60f32.to_radians()).abs() < 1e-5);
    }

    #[test]
    fn project_unproject_roundtrip() {
        let k = Intrinsics::from_fov_x(55f32.to_radians(), 640, 480);
        let px = Vec2::new(100.5, 300.5);
        let p = k.unproject(px, 3.2);
        let back = k.project(p).unwrap();
        assert!((back - px).length() < 1e-3);
    }

    #[test]
    fn behind_camera_does_not_project() {
        let k = Intrinsics::from_fov_x(1.0, 10, 10);
        assert!(k.project(Vec3::new(0.0, 0.0, -1.0)).is_none());
    }
}
