#!/usr/bin/env python3
"""Deterministic check: the vendored LangGraph and pi-subagents sources are the versions Concorde runs.

Concorde's Modules reference ``reference/langgraph`` (the langchain-ai/langgraph repository) and
``reference/pi-subagents`` as external reference material for agents. A reference is only honest
when it is checked out at the exact release the runtime installs, so this check compares the
vendored LangGraph package's declared version with the installed distribution and the locked
requirement, and the vendored pi-subagents version with the pin in ``pi/package.json``. The Pi
reference is not compared: Pi is the developer's own installation.
"""
from __future__ import annotations

import importlib.metadata
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENDORED_PYPROJECT = ROOT / "reference/langgraph/libs/langgraph/pyproject.toml"
LOCK = ROOT / "uv.lock"
VENDORED_SUBAGENTS = ROOT / "reference/pi-subagents/package.json"
PI_PACKAGE = ROOT / "pi/package.json"


def vendored_version() -> str:
    if not VENDORED_PYPROJECT.is_file():
        raise SystemExit(f"missing {VENDORED_PYPROJECT.relative_to(ROOT)}; run scripts/development/init-references.py")
    match = re.search(r'^version\s*=\s*"([^"]+)"', VENDORED_PYPROJECT.read_text(encoding="utf-8"), re.M)
    if match is None:
        raise SystemExit("vendored langgraph pyproject.toml declares no version")
    return match.group(1)


def locked_version() -> str | None:
    text = LOCK.read_text(encoding="utf-8") if LOCK.is_file() else ""
    match = re.search(r'^name = "langgraph"\nversion = "([^"]+)"', text, re.M)
    return match.group(1) if match else None


def main() -> int:
    vendored = vendored_version()
    installed = importlib.metadata.version("langgraph")
    locked = locked_version()
    print(f"vendored={vendored} installed={installed} locked={locked}")
    if vendored != installed or (locked is not None and locked != vendored):
        print("reference/langgraph is not checked out at the installed LangGraph version; "
              "update the submodule commit (git -C reference/langgraph fetch --depth 1 origin <tag> && "
              "git -C reference/langgraph checkout <tag>) and commit the new gitlink", file=sys.stderr)
        return 1
    if not VENDORED_SUBAGENTS.is_file():
        raise SystemExit(f"missing {VENDORED_SUBAGENTS.relative_to(ROOT)}; run scripts/development/init-references.py")
    subagents = json.loads(VENDORED_SUBAGENTS.read_text(encoding="utf-8"))["version"]
    pinned = json.loads(PI_PACKAGE.read_text(encoding="utf-8"))["dependencies"]["pi-subagents"]
    print(f"pi-subagents vendored={subagents} pinned={pinned}")
    if subagents != pinned:
        print("reference/pi-subagents is not checked out at the version pi/package.json pins; "
              "check out the matching v<version> tag and commit the new gitlink", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
