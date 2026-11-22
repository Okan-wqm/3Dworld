"""Builds `scene.json` documents (scene-schema, see `schema/scene.schema.json`).

This is the only place Python creates scene.json content. Tests validate its output
against the JSON Schema exported from Rust, and its committed example
(`schema/fixtures/scene.example.json`) must deserialize in Rust, so a field renamed on
one side fails CI. The version number comes from the Rust crate via `geom_core`.
"""

from __future__ import annotations

from typing import Any

import geom_core

SCHEMA_VERSION: int = geom_core.SCHEMA_VERSION

Json = dict[str, Any]


def asset_ref(uri: str, sha256: str | None = None) -> Json:
    return {"uri": uri, "sha256": sha256}


def identity_transform() -> Json:
    return {"translation": [0, 0, 0], "rotation": [0, 0, 0, 1], "scale": [1, 1, 1]}


def intrinsics_from_normalized(k: Any, width: int, height: int) -> Json:
    """Pixel intrinsics from a normalized 3x3 matrix (MoGe: fx, cx in units of width;
    fy, cy in units of height). Same convention as Rust `Intrinsics::from_normalized`."""
    return {
        "fx": float(k[0][0] * width),
        "fy": float(k[1][1] * height),
        "cx": float(k[0][2] * width),
        "cy": float(k[1][2] * height),
        "width": int(width),
        "height": int(height),
    }


def proposed_object(object_id: str, confidence: float, mask_uri: str, label: str = "object") -> Json:
    """A freshly proposed object: label from the model, nothing generated yet."""
    return {
        "id": object_id,
        "label": {"text": label, "source": "model", "confidence": round(confidence, 3)},
        "mask": asset_ref(mask_uri),
        "completion": None,
        "asset": None,
        "transform": identity_transform(),
        "transform_edited_by_user": False,
        "status": {"stage": "proposed", "stale_from": None, "failure": None},
    }


def build_scene(
    intrinsics: Json,
    objects: list[Json],
    *,
    source_uri: str,
    background_image_uri: str | None,
    background_asset_uri: str | None,
) -> Json:
    """A complete scene seen from the original camera (identity pose)."""
    background = None
    if background_image_uri is not None or background_asset_uri is not None:
        background = {
            "inpainted_image": asset_ref(background_image_uri) if background_image_uri else None,
            "asset": asset_ref(background_asset_uri) if background_asset_uri else None,
            "stale": False,
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "source_image": asset_ref(source_uri),
        "camera": {"intrinsics": intrinsics, "pose": identity_transform()},
        "objects": objects,
        "background": background,
    }
