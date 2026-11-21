"""Tests for the `geom_core` Python module (built with `maturin develop`)."""

import numpy as np
import pytest

import geom_core


def flat_points(h=4, w=5, z=2.0):
    depth = np.full((h, w), z, np.float32)
    return geom_core.points_from_depth(depth, 3.0, 3.0, w / 2, h / 2)


def test_plane_mesh_shapes():
    m = geom_core.grid_mesh(flat_points())
    assert m.positions.shape == (20, 3)
    assert m.uvs.shape == (20, 2)
    assert m.indices.shape == (4 * 3 * 2, 3)
    assert m.indices.dtype == np.uint32
    # glTF convention: in front of the camera means negative Z.
    assert np.allclose(m.positions[:, 2], -2.0)


def test_mask_and_nan_handling():
    pts = flat_points()
    pts[0, 0] = np.nan
    mask = np.zeros((4, 5), bool)
    mask[:, :3] = True
    m = geom_core.grid_mesh(pts, mask=mask)
    assert m.triangle_count == 2 * 3 * 2 - 1


def test_glb_header():
    glb = geom_core.grid_mesh(flat_points()).to_glb()
    assert glb[:4] == b"glTF"
    assert int.from_bytes(glb[8:12], "little") == len(glb)


def test_shape_errors():
    with pytest.raises(ValueError):
        geom_core.grid_mesh(np.zeros((4, 5, 2), np.float32))
    with pytest.raises(ValueError):
        geom_core.grid_mesh(flat_points(), mask=np.ones((3, 3), bool))


def test_ply_and_axis_flip():
    pts = np.array([[1.0, 2.0, 3.0]], np.float32)
    assert np.allclose(geom_core.opencv_to_gltf(pts), [[1.0, -2.0, -3.0]])
    ply = geom_core.write_ply_points(pts, np.array([[1, 2, 3]], np.uint8))
    assert b"element vertex 1" in ply
