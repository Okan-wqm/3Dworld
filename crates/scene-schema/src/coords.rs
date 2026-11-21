//! Coordinate conventions.
//!
//! **`scene.json` uses the glTF / three.js convention:** right-handed, `+X` right,
//! `+Y` up, the camera looks along `-Z`, units are meters.
//!
//! **Model outputs (MoGe, OpenCV) use the OpenCV camera convention:** `+X` right,
//! `+Y` down, `+Z` forward (into the scene).
//!
//! Converting between the two is a rotation of 180° around the X axis, i.e. flipping
//! the sign of Y and Z. This is the *only* place where that conversion is defined;
//! every other crate and worker must call these functions instead of flipping axes
//! by hand.

use glam::{Mat3, Quat, Vec3};

/// Rotation that maps OpenCV camera coordinates to glTF camera coordinates.
pub const OPENCV_TO_GLTF: Mat3 = Mat3::from_cols(
    Vec3::new(1.0, 0.0, 0.0),
    Vec3::new(0.0, -1.0, 0.0),
    Vec3::new(0.0, 0.0, -1.0),
);

/// Converts a point or direction from OpenCV camera space to glTF camera space.
#[inline]
pub fn opencv_to_gltf(p: Vec3) -> Vec3 {
    Vec3::new(p.x, -p.y, -p.z)
}

/// Converts a point or direction from glTF camera space to OpenCV camera space.
/// The conversion is its own inverse.
#[inline]
pub fn gltf_to_opencv(p: Vec3) -> Vec3 {
    opencv_to_gltf(p)
}

/// Converts a rotation expressed in OpenCV camera space to glTF camera space
/// (change of basis `C * R * C^-1`).
pub fn opencv_rotation_to_gltf(r: Quat) -> Quat {
    let c = Quat::from_mat3(&OPENCV_TO_GLTF);
    (c * r * c.inverse()).normalize()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn point_in_front_of_opencv_camera_is_at_negative_z_in_gltf() {
        // 2 m in front of the camera, slightly right and *below* the optical axis.
        let p_cv = Vec3::new(0.5, 0.25, 2.0);
        let p_gl = opencv_to_gltf(p_cv);
        assert_eq!(p_gl, Vec3::new(0.5, -0.25, -2.0));
    }

    #[test]
    fn conversion_is_an_involution() {
        let p = Vec3::new(1.0, 2.0, 3.0);
        assert_eq!(gltf_to_opencv(opencv_to_gltf(p)), p);
    }

    #[test]
    fn matrix_matches_function() {
        let p = Vec3::new(-0.3, 1.7, 4.2);
        assert!((OPENCV_TO_GLTF * p - opencv_to_gltf(p)).length() < 1e-6);
    }

    #[test]
    fn rotation_change_of_basis() {
        // A yaw (rotation around the OpenCV Y axis, which points down) must become a
        // rotation around glTF -Y.
        let r_cv = Quat::from_rotation_y(0.3);
        let r_gl = opencv_rotation_to_gltf(r_cv);
        let v = Vec3::new(0.0, 0.0, 1.0);
        let expected = opencv_to_gltf(r_cv * v);
        assert!((r_gl * opencv_to_gltf(v) - expected).length() < 1e-6);
    }
}
