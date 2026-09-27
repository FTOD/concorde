#!/usr/bin/env python3
"""Portable entry point that resolves the Concorde runtime relative to itself.

In a source checkout prepared with ``uv sync``, the checkout's own ``.venv`` holds Concorde's Python
dependencies, so the command runs again on that interpreter; an installed copy has no ``.venv``
and already runs on Concorde's own environment.
"""

import os
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_PYTHON = PACKAGE_ROOT / ".venv/bin/python"
if CHECKOUT_PYTHON.is_file() and os.path.realpath(sys.prefix) != os.path.realpath(
    PACKAGE_ROOT / ".venv"
):
    os.execv(CHECKOUT_PYTHON, [str(CHECKOUT_PYTHON), *sys.argv])
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from concorde.distribution.cli import main

raise SystemExit(main())
