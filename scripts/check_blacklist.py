#!/usr/bin/env python3
"""Fails if any forbidden third-party package appears in the repository's dependency files.

Usage: check_blacklist.py [ROOT]   (default: the repository root)

The list mirrors the "Yasak" (forbidden) section of LICENSES.md. It catches packages
that a license scanner may miss, e.g. CUDA extensions cloned by install scripts or
packages whose PyPI metadata understates their license.
"""

from __future__ import annotations

import pathlib
import re
import sys

FORBIDDEN = {
    "nvdiffrast": "NVIDIA Source Code License (non-commercial)",
    "nvdiffrec": "NVIDIA Source Code License (non-commercial)",
    "diffoctreerast": "Inria-derived license (non-commercial)",
    "diff-gaussian-rasterization": "Inria Gaussian-Splatting License (non-commercial)",
    "diff_gaussian_rasterization": "Inria Gaussian-Splatting License (non-commercial)",
    "mip-splatting": "Inria Gaussian-Splatting License (non-commercial)",
    "pymeshfix": "GPL-3.0",
    "python-igraph": "GPL-2.0",
    "igraph": "GPL-2.0",
    "plyfile": "GPL-3.0",
    "ultralytics": "AGPL-3.0",
    "imageio-ffmpeg": "bundles a GPL FFmpeg binary",
    "rmbg": "briaai RMBG weights are CC BY-NC",
}

# Files that declare or install dependencies.
DEP_FILES = (
    "requirements*.txt",
    "requirements/*.txt",
    "constraints*.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "environment*.yml",
    "Dockerfile*",
    "*.sh",
    "package.json",
    "Cargo.toml",
    "Makefile",
    "*.yml",
    "*.yaml",
)

SKIP_DIRS = {".git", "target", "node_modules", ".venv", "venv"}


def dependency_files(root: pathlib.Path):
    for pattern in DEP_FILES:
        for path in root.rglob(pattern):
            if not SKIP_DIRS.intersection(path.parts):
                yield path


def main(argv: list[str]) -> int:
    root = (
        pathlib.Path(argv[1]).resolve() if len(argv) > 1 else pathlib.Path(__file__).resolve().parent.parent
    )
    pattern = re.compile(
        r"(?<![\w-])(" + "|".join(re.escape(n) for n in FORBIDDEN) + r")(?![\w-])",
        re.IGNORECASE,
    )
    problems = []
    for path in sorted(set(dependency_files(root))):
        for lineno, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            for match in pattern.finditer(line):
                name = match.group(1).lower()
                problems.append(
                    f"{path.relative_to(root)}:{lineno}: '{name}' is forbidden ({FORBIDDEN[name]})"
                )
    if problems:
        print("Forbidden third-party packages found (see LICENSES.md):")
        print("\n".join(problems))
        return 1
    print("No forbidden packages found.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
