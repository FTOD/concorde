#!/usr/bin/env python3
"""Check out Concorde's vendored external references (git submodules) without their media.

A Module may declare third-party documentation or source as an ``includes`` of kind ``external``,
vendored under ``reference/`` as a git submodule pinned to a fixed revision. A plain
``git submodule update --init`` would download the upstream repositories' media as well. This script performs the checkout the
Framework expects instead: a partial clone (``--filter=blob:none``) whose sparse-checkout
patterns, recorded in ``.gitmodules`` under ``submodule.<name>.concorde-sparse``, exclude media by
suffix, checked out at exactly the commit the superproject records.

    python3 scripts/development/init-references.py            # every submodule in .gitmodules
    python3 scripts/development/init-references.py --check    # report without cloning

Run it once in a fresh clone (after ``python3 scripts/concorde.py build``); with no submodule in
``.gitmodules`` it does nothing.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def git(
    *arguments: str, cwd: Path = ROOT, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *arguments), cwd=cwd, text=True, capture_output=True, check=check
    )


def submodules() -> list[dict[str, str]]:
    if not (ROOT / ".gitmodules").is_file():
        return []
    entries: dict[str, dict[str, str]] = {}
    listing = git("config", "-f", ".gitmodules", "--list").stdout
    for line in listing.splitlines():
        key, _, value = line.partition("=")
        if not key.startswith("submodule."):
            continue
        name, field = key[len("submodule.") :].rsplit(".", 1)
        entries.setdefault(name, {"name": name})[field] = value
    return [entry for entry in entries.values() if "path" in entry and "url" in entry]


def recorded_commit(path: str) -> str | None:
    listing = git("ls-files", "--stage", "--", path, check=False).stdout.split()
    return listing[1] if len(listing) >= 4 and listing[0] == "160000" else None


def checked_out(path: str) -> bool:
    directory = ROOT / path
    return directory.is_dir() and (directory / ".git").exists()


def initialize(entry: dict[str, str]) -> None:
    path, url = entry["path"], entry["url"]
    commit = recorded_commit(path)
    if commit is None:
        raise SystemExit(f"{path} is not a submodule of this checkout")
    # A linked worktree has a .git *file*. Git resolves a worktree-local
    # administrative path, keeping this checkout's submodules independent.
    module_dir = Path(
        git(
            "rev-parse", "--path-format=absolute", "--git-path", f"modules/{path}"
        ).stdout.strip()
    )
    if module_dir.exists():
        raise SystemExit(
            f"{module_dir} already exists; remove it or finish the checkout by hand"
        )
    module_dir.parent.mkdir(parents=True, exist_ok=True)
    git("submodule", "init", "--", path)
    git(
        "clone",
        "--quiet",
        "--filter=blob:none",
        "--no-checkout",
        "--separate-git-dir",
        str(module_dir),
        url,
        str(ROOT / path),
    )
    patterns = entry.get("concorde-sparse")
    if patterns:
        git(
            "sparse-checkout",
            "set",
            "--no-cone",
            *shlex.split(patterns),
            cwd=ROOT / path,
        )
    fetch = git(
        "fetch",
        "--quiet",
        "--depth",
        "1",
        "origin",
        commit,
        cwd=ROOT / path,
        check=False,
    )
    if fetch.returncode:
        raise SystemExit(f"cannot fetch {commit} for {path}: {fetch.stderr.strip()}")
    git("checkout", "--quiet", "--detach", commit, cwd=ROOT / path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report the state of every reference without cloning",
    )
    arguments = parser.parse_args(argv)
    entries = submodules()
    if not entries:
        print("no submodules declared in .gitmodules")
        return 0
    missing = 0
    for entry in entries:
        path = entry["path"]
        present = checked_out(path)
        state = "checked out" if present else "missing"
        if not present and not arguments.check:
            initialize(entry)
            state = "initialized"
        if state == "missing":
            missing += 1
        print(f"{path}: {state} @ {recorded_commit(path) or '?'}")
    return 1 if arguments.check and missing else 0


if __name__ == "__main__":
    sys.exit(main())
