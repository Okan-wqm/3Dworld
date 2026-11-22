//! Scene graph types shared by the Rust API, the Python GPU workers and the web editor.
//!
//! This crate is the single source of truth for:
//! - the coordinate convention of `scene.json` ([`coords`]),
//! - camera intrinsics ([`camera`]),
//! - the scene graph itself ([`scene`]),
//! - the per-object review state machine and invalidation rules ([`status`]).
//!
//! The JSON Schema exported by the `export-schema` binary (`schema/scene.schema.json`)
//! is the contract for other languages. Drift is caught by tests, not by code
//! generation: the Python builder (`workers/common/scene_json.py`) is validated against
//! the schema, and its committed output (`schema/fixtures/scene.example.json`) must
//! deserialize here (see `tests/fixture.rs`). Unknown fields are rejected on both sides.

pub mod camera;
pub mod coords;
pub mod scene;
pub mod status;

pub use camera::Intrinsics;
pub use scene::{
    AssetRef, Background, Camera, Label, LabelSource, SCHEMA_VERSION, Scene, SceneObject, Transform,
};
pub use status::{Change, ObjectStatus, Stage, StatusError};

/// JSON Schema of [`Scene`], used to generate TypeScript and Pydantic types.
pub fn scene_json_schema() -> serde_json::Value {
    serde_json::to_value(schemars::schema_for!(Scene)).expect("schema serializes")
}
