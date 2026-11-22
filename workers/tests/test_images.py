import numpy as np
import pytest
from PIL import Image

from workers.common.images import load_image, png_bytes


def save_with_orientation(path, img: Image.Image, orientation: int):
    exif = Image.Exif()
    exif[0x0112] = orientation  # Orientation tag
    img.save(path, exif=exif)


def test_exif_rotation_is_applied(tmp_path):
    # Stored landscape 80x40 with a red left half; orientation 6 = rotate 90° CW to view.
    raw = np.zeros((40, 80, 3), np.uint8)
    raw[:, :40] = (255, 0, 0)
    path = tmp_path / "phone.jpg"
    save_with_orientation(path, Image.fromarray(raw), 6)
    rgb = load_image(path, max_side=200)
    assert rgb.shape == (80, 40, 3)  # displayed upright: portrait
    # After a 90° clockwise turn the stored left half ends up on top.
    assert rgb[:40, :, 0].mean() > 200 and rgb[40:, :, 0].mean() < 50


@pytest.mark.parametrize("mode", ["RGBA", "P", "L", "LA", "I;16"])
def test_modes_become_rgb(tmp_path, mode):
    img = Image.new("RGB", (64, 48), (10, 200, 30)).convert(mode)
    path = tmp_path / f"img_{mode.replace(';', '')}.png"
    img.save(path)
    rgb = load_image(path, max_side=100)
    assert rgb.shape == (48, 64, 3) and rgb.dtype == np.uint8


def test_resize_keeps_aspect(tmp_path):
    path = tmp_path / "big.png"
    Image.new("RGB", (400, 200)).save(path)
    assert load_image(path, max_side=100).shape == (50, 100, 3)


def test_tiny_images_are_rejected(tmp_path):
    path = tmp_path / "tiny.png"
    Image.new("RGB", (8, 8)).save(path)
    with pytest.raises(ValueError):
        load_image(path, max_side=100)


def test_png_bytes_roundtrip():
    rgb = np.random.default_rng(0).integers(0, 255, (5, 7, 3), dtype=np.uint8)
    import io

    assert np.array_equal(np.asarray(Image.open(io.BytesIO(png_bytes(rgb)))), rgb)
