"""image_to_mesh fails before writing anything when there is no valid depth. The model is
replaced by a stub, so this needs PyTorch installed but no weights."""

import sys

import numpy as np
import pytest
from PIL import Image

pytest.importorskip("torch")

from workers.geometry import image_to_mesh  # noqa: E402


def test_no_valid_depth_writes_nothing(tmp_path, monkeypatch):
    img = tmp_path / "in.png"
    Image.new("RGB", (64, 48), (90, 90, 90)).save(img)
    out = tmp_path / "out"

    def no_depth(rgb, device, fov_x=None):
        h, w = rgb.shape[:2]
        return image_to_mesh.Geometry(np.full((h, w, 3), np.nan, np.float32), np.eye(3, dtype=np.float32))

    monkeypatch.setattr(image_to_mesh, "load_moge", lambda device: None)
    monkeypatch.setattr(image_to_mesh, "estimate_geometry", no_depth)
    monkeypatch.setattr(sys, "argv", ["image_to_mesh", str(img), str(out), "--device", "cpu"])
    with pytest.raises(SystemExit, match="no valid depth"):
        image_to_mesh.main()
    assert not out.exists()
