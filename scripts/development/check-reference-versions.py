#!/usr/bin/env python3
"""Deterministic check: the vendored LangGraph source is the version Concorde runs.

Concorde's Modules reference ``reference/langgraph`` (the langchain-ai/langgraph repository) as
external reference material for agents. That reference is only honest when it is checked out at
the exact release the runtime installs, so this check compares the vendored package's declared
version with the installed distribution and with the locked requirement.
"""
from __future__ import annotations

import importlib.metadata
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENDORED_PYPROJECT = ROOT / "reference/langgraph/libs/langgraph/pyproject.toml"
LOCK = ROOT / "uv.lock"


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
    return 0


if __name__ == "__main__":
    sys.exit(main())
