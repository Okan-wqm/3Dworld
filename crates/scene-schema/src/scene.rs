//! The scene graph stored as `scene.json`.
//!
//! All positions and transforms are in the glTF convention, in meters (see
//! [`crate::coords`]). The world frame is the camera frame of the *original* photo:
//! the original camera sits at the origin looking along `-Z`.

use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

use crate::camera::Intrinsics;
use crate::status::ObjectStatus;

/// Bumped on every breaking change of the format.
pub const SCHEMA_VERSION: u32 = 1;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Scene {
    pub schema_version: u32,
    /// The uploaded photo.
    pub source_image: AssetRef,
    /// The original camera that took the photo.
    pub camera: Camera,
    pub objects: Vec<SceneObject>,
    pub background: Option<Background>,
}

impl Scene {
    pub fn new(source_image: AssetRef, intrinsics: Intrinsics) -> Self {
        Self {
            schema_version: SCHEMA_VERSION,
            source_image,
            camera: Camera {
                intrinsics,
                pose: Transform::IDENTITY,
            },
            objects: Vec::new(),
            background: None,
        }
    }

    pub fn object(&self, id: &str) -> Option<&SceneObject> {
        self.objects.iter().find(|o| o.id == id)
    }

    pub fn object_mut(&mut self, id: &str) -> Option<&mut SceneObject> {
        self.objects.iter_mut().find(|o| o.id == id)
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Camera {
    pub intrinsics: Intrinsics,
    /// Camera-to-world transform. Identity for the original camera.
    pub pose: Transform,
}

/// Translation, rotation (unit quaternion `[x, y, z, w]`) and non-uniform scale, applied
/// in glTF order: scale, then rotate, then translate.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Transform {
    pub translation: [f32; 3],
    pub rotation: [f32; 4],
    pub scale: [f32; 3],
}

impl Transform {
    pub const IDENTITY: Self = Self {
        translation: [0.0; 3],
        rotation: [0.0, 0.0, 0.0, 1.0],
        scale: [1.0; 3],
    };

    pub fn to_mat4(&self) -> glam::Mat4 {
        glam::Mat4::from_scale_rotation_translation(
            glam::Vec3::from(self.scale),
            glam::Quat::from_array(self.rotation),
            glam::Vec3::from(self.translation),
        )
    }
}

impl Default for Transform {
    fn default() -> Self {
        Self::IDENTITY
    }
}

/// Reference to a file in asset storage. `sha256` makes assets content-addressed so the
/// same output is never generated twice.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct AssetRef {
    pub uri: String,
    pub sha256: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Label {
    pub text: String,
    pub source: LabelSource,
    /// Model confidence in `[0, 1]`; `None` for labels typed by the user.
    pub confidence: Option<f32>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum LabelSource {
    Model,
    User,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct SceneObject {
    pub id: String,
    pub label: Label,
    /// Binary mask in the source image.
    pub mask: Option<AssetRef>,
    /// Approved amodal completion (RGBA, background removed).
    pub completion: Option<AssetRef>,
    /// Generated 3D asset (GLB).
    pub asset: Option<AssetRef>,
    /// Object-to-world transform.
    pub transform: Transform,
    /// True once the user has moved, rotated or scaled the object by hand. Such
    /// transforms are kept when the asset is regenerated.
    pub transform_edited_by_user: bool,
    pub status: ObjectStatus,
}

impl SceneObject {
    pub fn proposed(id: impl Into<String>, label: impl Into<String>, confidence: f32) -> Self {
        Self {
            id: id.into(),
            label: Label {
                text: label.into(),
                source: LabelSource::Model,
                confidence: Some(confidence),
            },
            mask: None,
            completion: None,
            asset: None,
            transform: Transform::IDENTITY,
            transform_edited_by_user: false,
            status: ObjectStatus::default(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Background {
    /// Background with objects removed and holes filled.
    pub inpainted_image: Option<AssetRef>,
    /// Background geometry (GLB).
    pub asset: Option<AssetRef>,
    pub stale: bool,
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample() -> Scene {
        let mut s = Scene::new(
            AssetRef {
                uri: "assets/barn.jpg".into(),
                sha256: None,
            },
            Intrinsics::from_fov_x(1.0, 1280, 720),
        );
        s.objects
            .push(SceneObject::proposed("obj-1", "horse", 0.93));
        s
    }

    #[test]
    fn json_roundtrip() {
        let s = sample();
        let json = serde_json::to_string_pretty(&s).unwrap();
        let back: Scene = serde_json::from_str(&json).unwrap();
        assert_eq!(s, back);
    }

    #[test]
    fn schema_mentions_core_types() {
        let schema = crate::scene_json_schema().to_string();
        for name in ["SceneObject", "Intrinsics", "Stage", "Transform"] {
            assert!(schema.contains(name), "schema misses {name}");
        }
    }

    #[test]
    fn identity_transform_is_identity_matrix() {
        assert_eq!(Transform::IDENTITY.to_mat4(), glam::Mat4::IDENTITY);
    }
}
