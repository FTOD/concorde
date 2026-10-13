#!/usr/bin/env python3
"""Portable entry point that resolves the Concorde runtime relative to itself.

In a source checkout prepared with ``uv sync``, the checkout's own ``.venv`` holds Concorde's Python
dependencies, so the command runs again on that interpreter; an installed copy has no ``.venv``
and already runs on Concorde's own environment.

``build --check`` writes no file, so for it Python writes no bytecode cache either, on this
interpreter and on the one the command runs again on.
"""

import os
import sys
from pathlib import Path


def _writes_nothing(words: list[str]) -> bool:
    """Whether the command is ``build --check``, after any global ``--project-root``."""
    while words and words[0].startswith("--project-root"):
        words = words[2:] if words[0] == "--project-root" else words[1:]
    return words[:1] == ["build"] and "--check" in words[1:]


if _writes_nothing(sys.argv[1:]):
    sys.dont_write_bytecode = True
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_PYTHON = PACKAGE_ROOT / ".venv/bin/python"
if CHECKOUT_PYTHON.is_file() and os.path.realpath(sys.prefix) != os.path.realpath(
    PACKAGE_ROOT / ".venv"
):
    os.execv(
        CHECKOUT_PYTHON,
        [str(CHECKOUT_PYTHON), *(["-B"] if sys.dont_write_bytecode else []), *sys.argv],
    )
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from concorde.distribution.cli import main

raise SystemExit(main())
