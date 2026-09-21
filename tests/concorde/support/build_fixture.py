"""Shared helper for tests that exercise the real build or the real graph.

Any test that needs a working built package as a *prerequisite* (worktree
creation, a Studio graph bound to a temporary root) should build the package root into its own
temporary directory first, rather than depending on the actual checkout being pre-built. Tests
that exercise ``build``/``check_build``/``write_build`` themselves are not this helper's concern;
they call those functions directly.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .paths import REPOSITORY_ROOT


def build_package_copy(root: Path):
    """Copy ``prompts/`` and ``operations/`` into ``root`` and build them there.

    Requires ``concorde.distribution.build`` to already be importable (callers insert
    ``RUNTIME_ROOT`` onto ``sys.path`` before importing this helper, as usual). Returns the
    ``BuildResult``.
    """

    from concorde.distribution.build import write_build

    shutil.copytree(REPOSITORY_ROOT / "prompts", root / "prompts", dirs_exist_ok=True)
    shutil.copytree(REPOSITORY_ROOT / "protocol", root / "protocol", dirs_exist_ok=True)
    shutil.copytree(
        REPOSITORY_ROOT / "operations", root / "operations", dirs_exist_ok=True
    )
    shutil.copytree(
        REPOSITORY_ROOT / "src/concorde/spec",
        root / "src/concorde/spec",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    return write_build(root)


def refresh_projection_goldens() -> tuple[str, ...]:
    """Explicitly refresh test expectations from this checkout's pure build renderer.

    Run with ``PYTHONPATH=src .venv/bin/python -m tests.concorde.support.build_fixture``.
    No ambient installation or generated/session copy supplies fixture bytes. The fixture
    inventory is exact: retired projections are removed, never retained as supported assets.
    """
    from concorde.distribution.build import (
        LEGACY_OPERATION_NAMES,
        PRIVATE_PI_SESSION_SHIM,
        build,
    )

    golden = REPOSITORY_ROOT / "tests/concorde/fixtures/build/golden"
    expected = {}
    for output in build(REPOSITORY_ROOT).outputs:
        relative = None
        if output.path.startswith(("generated/agents/", "generated/native/")):
            relative = output.path.removeprefix("generated/")
        if output.path == PRIVATE_PI_SESSION_SHIM:
            relative = "pi/concorde-session.ts"
        if relative is not None:
            expected[relative] = output.content
    retired = {
        f"{client}/{name}/SKILL.md"
        for client in ("claude", "codex")
        for name in LEGACY_OPERATION_NAMES
    }
    for path in golden.rglob("*"):
        relative = path.relative_to(golden).as_posix()
        if path.is_file() and relative not in expected and relative not in retired:
            raise ValueError(f"unknown golden fixture: {path}")
        if path.is_symlink():
            raise ValueError(f"unsafe golden fixture: {path}")
    for path in golden.rglob("*"):
        if path.is_file() and path.relative_to(golden).as_posix() not in expected:
            path.unlink()
    for path in sorted(golden.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    for relative, content in sorted(expected.items()):
        path = golden / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return tuple(sorted(expected))


if __name__ == "__main__":
    for relative in refresh_projection_goldens():
        print(relative)
