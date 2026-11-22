import numpy as np

from workers.common.depth_ops import fit_background_depth, occluding_fraction


def scene_with_box(h=80, w=100, wall=4.0, box=2.0):
    depth = np.full((h, w), wall, np.float32)
    mask = np.zeros((h, w), bool)
    mask[20:60, 30:70] = True
    depth[mask] = box
    return depth, mask


def test_free_standing_object_occludes_its_outline():
    depth, mask = scene_with_box()
    assert occluding_fraction(mask, depth, gap_px=2, jump=0.03) > 0.9


def test_flat_surface_region_does_not_occlude():
    depth, mask = scene_with_box(box=4.0)  # same depth as the wall: a poster, a rug
    assert occluding_fraction(mask, depth, gap_px=2, jump=0.03) == 0.0


def test_surface_with_object_in_front_does_not_occlude():
    # The "wall" region surrounds a closer box: outside the wall mask things are closer.
    depth, box = scene_with_box()
    wall = ~box
    wall[:, :5] = False  # keep the mask off the image border on one side
    assert occluding_fraction(wall, depth, gap_px=2, jump=0.03) < 0.1


def points_from_depth(z):
    h, w = z.shape
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    f = 50.0
    return np.stack([(xs - w / 2) / f * z, (ys - h / 2) / f * z, z], -1).astype(np.float32)


def test_background_fit_rescales_and_joins_without_seam():
    h, w = 60, 80
    ref_z = np.full((h, w), 3.0, np.float32)
    filled = np.zeros((h, w), bool)
    filled[20:40, 30:50] = True
    ref = points_from_depth(ref_z)
    ref[filled] = np.nan  # the photo has the object there, not the background
    # Re-estimate has the wrong metric scale (objects removed) and a slight tilt.
    new_z = 1.0 + 0.002 * np.arange(w, dtype=np.float32)[None, :].repeat(h, 0)
    new = points_from_depth(new_z)

    out, scale = fit_background_depth(new, ref, filled)
    assert 2.4 < scale < 3.0
    # Outside the filled region the photo's geometry is kept exactly.
    assert np.allclose(out[~filled], ref[~filled], equal_nan=True)
    # Inside, depth is close to the surrounding wall: no step at the seam.
    assert np.all(np.abs(out[filled][:, 2] - 3.0) < 0.15)
