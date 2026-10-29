#!/usr/bin/env python3
"""Run the source checkout's type check, including in a fresh delivery worktree."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCSITE = ROOT / "docsite"


def main() -> int:
    # All preparation happens in an external temporary copy. Configured checks see the actual
    # project read-only, including its ignored caches and generated documentation directories.
    with tempfile.TemporaryDirectory(prefix="concorde-docsite-types-") as directory:
        docsite = Path(directory) / "docsite"
        shutil.copytree(
            DOCSITE,
            docsite,
            ignore=shutil.ignore_patterns(
                "node_modules",
                ".generated",
                ".docusaurus",
                "build",
                "coverage",
                "*.tsbuildinfo",
            ),
        )
        return check_copy(docsite)


# npm ci in a fresh copy leaves out an optional package now and then, such as esbuild's platform
# package, when its download fails: an install is used only once it holds every package it needs.
INSTALL_ATTEMPTS = 3


def node_platform() -> dict[str, str]:
    """This machine's values of the package fields ``os``, ``cpu`` and ``libc``, as Node names
    them."""
    words = subprocess.run(
        [
            "node",
            "-p",
            (
                "[process.platform, process.arch,"
                " process.report.getReport().header.glibcVersionRuntime ? 'glibc' : 'musl']"
                ".join(' ')"
            ),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return dict(zip(("os", "cpu", "libc"), words, strict=True))


def admits(value: str, allowed: str | list[str] | None) -> bool:
    """Whether a package field such as ``os`` admits ``value``, as npm reads it: any listed
    value admits it, and a listed ``!value`` refuses it."""
    if allowed is None:
        return True
    allowed = [allowed] if isinstance(allowed, str) else allowed
    if value in [entry[1:] for entry in allowed if entry.startswith("!")]:
        return False
    positive = [entry for entry in allowed if not entry.startswith("!")]
    return not positive or "any" in positive or value in positive


def lacking(docsite: Path, lock: dict, platform: dict[str, str]) -> list[str]:
    """The packages of the lockfile that the install under ``docsite`` lacks or holds at another
    version: every package for this platform that is not optional, and every optional one made
    for this platform. An optional package for every platform is needed only by a package left
    out, so npm may leave it out too. A package that only optional peer dependencies reach (both
    ``peer`` and ``optional``) is installed by npm 10 and left out by npm 11: it may be missing,
    but one that is present holds its locked version."""
    missing = []
    for path, entry in lock.get("packages", {}).items():
        if not path or not all(
            admits(platform[field], entry.get(field)) for field in platform
        ):
            continue
        if entry.get("optional") and not any(field in entry for field in platform):
            continue
        try:
            version = json.loads((docsite / path / "package.json").read_text())[
                "version"
            ]
        except FileNotFoundError:
            if not (entry.get("peer") and entry.get("optional")):
                missing.append(path)
            continue
        except (OSError, ValueError, KeyError, TypeError):
            missing.append(path)
            continue
        if not entry.get("link") and version != entry.get("version"):
            missing.append(path)
    return missing


def check_copy(docsite: Path) -> int:
    lock = json.loads((DOCSITE / "package-lock.json").read_text())
    platform = node_platform()
    installed = DOCSITE / "node_modules"
    # The checkout's own install serves when it holds what the lockfile asks for.
    if (installed / "typescript/bin/tsc").is_file() and not lacking(
        DOCSITE, lock, platform
    ):
        (docsite / "node_modules").symlink_to(installed, target_is_directory=True)
    else:
        for attempt in range(1, INSTALL_ATTEMPTS + 1):
            subprocess.run(
                ["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
                cwd=docsite,
                check=True,
            )
            missing = lacking(docsite, lock, platform)
            if not missing:
                break
            print(
                f"npm ci (attempt {attempt} of {INSTALL_ATTEMPTS}) left out "
                + ", ".join(missing),
                file=sys.stderr,
            )
        else:
            return 1
    compiler = docsite / "node_modules/typescript/bin/tsc"
    # TypeScript imports the sidebar, not published pages or rendered diagram HTML.
    # Derive the real sidebar in a fresh checkout without requiring publication first.
    prepare = (
        "const {mkdirSync,writeFileSync}=require('node:fs');"
        "const {loadScopedRegistry}=require('./plugins/scoped-content/model.ts');"
        "const {scopedSidebar}=require('./plugins/scoped-content/materialize.ts');"
        "const sidebar=scopedSidebar(loadScopedRegistry(process.argv[1]));"
        "mkdirSync('.generated',{recursive:true});"
        "writeFileSync('.generated/specs-sidebar.json',JSON.stringify(sidebar,null,2)+'\\n');"
    )
    subprocess.run(
        ["node", "--import", "tsx", "-e", prepare, str(ROOT)], cwd=docsite, check=True
    )
    return subprocess.run(
        [
            "node",
            str(compiler),
            "--noEmit",
            "--project",
            str(docsite / "tsconfig.json"),
        ],
        cwd=docsite,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
