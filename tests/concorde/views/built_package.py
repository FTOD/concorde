"""The Concorde package the scaffold tests install from.

Installing a project's defaults needs a built package. A configured check runs on a clean
checkout, read-only, where nothing is built. So when this checkout has no fresh build, the tests
build a copy of its package in a scratch directory, once per process, and install from there.
"""

from __future__ import annotations

import atexit
import functools
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from concorde.distribution.build import BuildError, verify_fresh
from tests.concorde.support.paths import REPOSITORY_ROOT

# What the build reads: the package roots and the files at the root it records as sources.
_DIRECTORIES = ("prompts", "src", "protocol", "specs", "scripts", "docs", "docsite")
_FILES = (
    "concorde.json",
    "pyproject.toml",
    "README.md",
    "LICENSE",
    "CLAUDE.md",
    ".concorde/config.json",
    ".concorde/specs.json",
)
_DISPOSABLE = shutil.ignore_patterns(
    "node_modules", "__pycache__", ".generated", ".docusaurus", "coverage", "*.pyc"
)


@functools.cache
def built_package() -> Path:
    """This checkout when its build is fresh, otherwise a freshly built copy in scratch."""
    try:
        verify_fresh(REPOSITORY_ROOT)
        return REPOSITORY_ROOT
    except BuildError:
        pass
    scratch = Path(tempfile.mkdtemp(prefix="concorde-views-package-"))
    atexit.register(shutil.rmtree, scratch, True)
    for name in _DIRECTORIES:
        source = REPOSITORY_ROOT / name
        if source.is_dir():

            def ignore(directory, names, source=source):
                # Only generated output directly under a copied root is left out.
                top = {"build"} if Path(directory) == source else set()
                return _DISPOSABLE(directory, names) | (top & set(names))

            shutil.copytree(source, scratch / name, ignore=ignore)
    for name in _FILES:
        if (REPOSITORY_ROOT / name).is_file():
            (scratch / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPOSITORY_ROOT / name, scratch / name)
    built = subprocess.run(
        [sys.executable, "scripts/concorde.py", "build"],
        cwd=scratch,
        capture_output=True,
        text=True,
    )
    if built.returncode:
        raise RuntimeError(
            f"building a scratch copy of the package at {scratch} failed:\n"
            + built.stdout
            + built.stderr
        )
    return scratch
