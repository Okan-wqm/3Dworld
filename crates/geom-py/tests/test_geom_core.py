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


# --- Input hardening: wrong input raises ValueError, never PanicException, and memory
# layout never changes the result.


def test_fortran_order_gives_same_mesh_as_c_order():
    depth = np.linspace(1.0, 2.0, 4 * 5, dtype=np.float32).reshape(4, 5)
    pts_c = geom_core.points_from_depth(depth, 3.0, 3.0, 2.5, 2.0)
    pts_f = geom_core.points_from_depth(np.asfortranarray(depth), 3.0, 3.0, 2.5, 2.0)
    assert np.array_equal(pts_c, pts_f)
    mask = np.zeros((4, 5), bool)
    mask[:, :3] = True
    a = geom_core.grid_mesh(pts_c, mask=mask)
    b = geom_core.grid_mesh(np.asfortranarray(pts_c), mask=np.asfortranarray(mask))
    assert np.array_equal(a.positions, b.positions)
    assert np.array_equal(a.indices, b.indices)


def test_strided_view_is_read_logically():
    pts = flat_points(8, 10)
    view = pts[::2, ::2]
    assert geom_core.grid_mesh(view).positions.shape == (20, 3)


@pytest.mark.parametrize("shape,stride", [((0, 0, 3), 1), ((0, 5, 3), 2), ((5, 0, 3), 2), ((1, 1, 3), 1)])
def test_degenerate_sizes_return_empty_mesh(shape, stride):
    m = geom_core.grid_mesh(np.ones(shape, np.float32), stride=stride)
    assert m.triangle_count == 0


def test_bad_inputs_raise_value_error():
    pts = flat_points()
    cases = [
        lambda: geom_core.opencv_to_gltf(np.ones((4, 2), np.float32)),
        lambda: geom_core.write_ply_points(np.ones((4, 2), np.float32)),
        lambda: geom_core.points_from_depth(np.ones((2, 2), np.float32), 0.0, 1.0, 1.0, 1.0),
        lambda: geom_core.points_from_depth(np.ones((2, 2), np.float32), np.nan, 1.0, 1.0, 1.0),
        lambda: geom_core.grid_mesh(pts, max_depth_ratio=float("nan")),
        lambda: geom_core.grid_mesh(pts, max_depth_ratio=-1.0),
        lambda: geom_core.grid_mesh(pts, stride=0),
        lambda: geom_core.grid_mesh(pts).to_glb(b"", "image/png"),
        lambda: geom_core.grid_mesh(pts).to_glb(b"not a png", "image/png"),
        lambda: geom_core.write_glb_scene([("x", geom_core.grid_mesh(pts), b"\xff\xd8\xff", "image/png")]),
    ]
    for i, case in enumerate(cases):
        with pytest.raises(ValueError):
            case()
