import json
import pathlib

import jsonschema
import pytest

from workers.common import scene_json
from workers.tests.scene_example import FIXTURE, example_scene, render

SCHEMA = json.loads(
    (pathlib.Path(__file__).resolve().parents[2] / "schema" / "scene.schema.json").read_text()
)


def test_builder_output_matches_rust_schema():
    jsonschema.validate(example_scene(), SCHEMA)


def test_committed_fixture_is_current():
    # The Rust test deserializes this file; if the builder changes, regenerate it with
    # `python -m workers.tests.scene_example` so both sides keep testing the same thing.
    assert FIXTURE.read_text() == render(example_scene())


def test_version_comes_from_rust():
    import geom_core

    assert example_scene()["schema_version"] == geom_core.SCHEMA_VERSION


def test_unknown_field_is_rejected_by_schema():
    scene = example_scene()
    scene["objects"][0]["extra"] = 1
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(scene, SCHEMA)


def test_intrinsics_follow_rust_from_normalized():
    k = scene_json.intrinsics_from_normalized([[0.5, 0, 0.25], [0, 0.75, 0.5], [0, 0, 1]], 800, 600)
    assert k == {"fx": 400.0, "fy": 450.0, "cx": 200.0, "cy": 300.0, "width": 800, "height": 600}
