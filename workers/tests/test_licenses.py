"""The license gate must hold by itself: these tests fail when code, the allowlist and
LICENSES.md disagree."""

import pathlib
import re
import subprocess
import sys

import pytest

from workers.common import weights

ROOT = pathlib.Path(__file__).resolve().parents[2]
LICENSES = (ROOT / "LICENSES.md").read_text()


def approved_models_section() -> str:
    start = LICENSES.index("## ✅ Onaylı modeller")
    end = LICENSES.index("\n## ", start + 1)
    return LICENSES[start:end]


def test_every_allowlisted_model_is_approved_in_licenses_md():
    section = approved_models_section()
    missing = [m for m in sorted(weights.allowed_ids()) if f"`{m}`" not in section]
    assert not missing, f"allowlisted but not ✅ in LICENSES.md: {missing}"


def test_every_pinned_revision_is_allowlisted_and_well_formed():
    for model_id, rev in weights.pinned_revisions().items():
        assert model_id in weights.allowed_ids(), model_id
        assert re.fullmatch(r"[0-9a-f]{40}", rev), f"{model_id}: {rev}"


def model_ids_in_code() -> set[str]:
    """Hugging Face-style ids ("owner/name") written as string literals in worker code."""
    found = set()
    for path in (ROOT / "workers").rglob("*.py"):
        if "tests" in path.parts:
            continue
        for lit in re.findall(r"""["']([A-Za-z0-9][\w.-]*/[\w.-]+)["']""", path.read_text()):
            if not lit.startswith(("image/", "masks/", "configs/")):
                found.add(lit)
    return found


def test_every_model_in_code_is_allowlisted_and_pinned():
    ids = model_ids_in_code()
    assert ids, "expected at least one model id in workers/"
    assert ids <= weights.allowed_ids(), ids - weights.allowed_ids()
    assert ids <= set(weights.pinned_revisions()), ids - set(weights.pinned_revisions())


def test_unknown_model_is_refused():
    with pytest.raises(weights.ForbiddenWeightsError):
        weights.require_allowed("briaai/RMBG-2.0")
    with pytest.raises(weights.ForbiddenWeightsError):
        weights.fetch("briaai/RMBG-2.0", "model.pth")


def run_blacklist(root: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_blacklist.py"), str(root)],
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    "relpath,line",
    [
        ("requirements/models.txt", "plyfile==1.0"),
        (".github/workflows/ci.yml", "      - run: pip install nvdiffrast"),
        ("scripts/setup.sh", "pip install igraph"),
    ],
)
def test_blacklist_catches_forbidden_packages(tmp_path, relpath, line):
    target = tmp_path / relpath
    target.parent.mkdir(parents=True)
    target.write_text(line + "\n")
    result = run_blacklist(tmp_path)
    assert result.returncode == 1, result.stdout


def test_blacklist_passes_clean_tree_and_ignores_comments(tmp_path):
    (tmp_path / "requirements.txt").write_text("numpy==2.0\n# plyfile is forbidden\n")
    assert run_blacklist(tmp_path).returncode == 0


def test_repository_itself_is_clean():
    assert run_blacklist(ROOT).returncode == 0
