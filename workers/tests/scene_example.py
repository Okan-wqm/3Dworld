"""The example scene committed as `schema/fixtures/scene.example.json`.

Regenerate after an intended format change:
    python -m workers.tests.scene_example

Numbers are exactly representable in f32 so the Rust round-trip test can compare
values exactly.
"""

from __future__ import annotations

import json
import pathlib

from workers.common import scene_json

FIXTURE = pathlib.Path(__file__).resolve().parents[2] / "schema" / "fixtures" / "scene.example.json"


def example_scene() -> dict:
    intrinsics = scene_json.intrinsics_from_normalized(
        [[0.5, 0.0, 0.5], [0.0, 0.75, 0.5], [0.0, 0.0, 1.0]], width=768, height=512
    )
    objects = [
        scene_json.proposed_object("obj-01", 0.75, "masks/obj-01.png", label="horse"),
        scene_json.proposed_object("obj-02", 0.5, "masks/obj-02.png"),
    ]
    return scene_json.build_scene(
        intrinsics,
        objects,
        source_uri="source.png",
        background_image_uri="background.png",
        background_asset_uri="scene.glb",
    )


def render(scene: dict) -> str:
    return json.dumps(scene, indent=2) + "\n"


if __name__ == "__main__":
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(render(example_scene()))
    print(f"wrote {FIXTURE}")
