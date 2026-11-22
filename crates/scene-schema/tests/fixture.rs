//! Contract test: the scene written by the Python builder must deserialize here, carry
//! the current schema version, and survive a round trip unchanged.

use scene_schema::{SCHEMA_VERSION, Scene, Stage};

const FIXTURE: &str = include_str!("../../../schema/fixtures/scene.example.json");

#[test]
fn python_fixture_deserializes() {
    let scene: Scene = serde_json::from_str(FIXTURE).expect("fixture matches the Rust types");
    assert_eq!(scene.schema_version, SCHEMA_VERSION);
    assert_eq!(scene.objects.len(), 2);
    assert_eq!(scene.objects[0].label.text, "horse");
    assert_eq!(scene.objects[0].status.stage, Stage::Proposed);
}

/// JSON does not distinguish `0` from `0.0`; compare all numbers as f64.
fn numbers_as_f64(v: serde_json::Value) -> serde_json::Value {
    use serde_json::Value;
    match v {
        Value::Number(n) => serde_json::json!(n.as_f64().expect("finite number")),
        Value::Array(a) => Value::Array(a.into_iter().map(numbers_as_f64).collect()),
        Value::Object(o) => {
            Value::Object(o.into_iter().map(|(k, v)| (k, numbers_as_f64(v))).collect())
        }
        other => other,
    }
}

#[test]
fn python_fixture_round_trips_without_loss() {
    let original: serde_json::Value = serde_json::from_str(FIXTURE).unwrap();
    let scene: Scene = serde_json::from_value(original.clone()).unwrap();
    assert_eq!(
        numbers_as_f64(serde_json::to_value(&scene).unwrap()),
        numbers_as_f64(original)
    );
}

#[test]
fn unknown_fields_are_rejected() {
    let mut v: serde_json::Value = serde_json::from_str(FIXTURE).unwrap();
    v["objects"][0]["extra"] = serde_json::json!(1);
    assert!(serde_json::from_value::<Scene>(v).is_err());
}
