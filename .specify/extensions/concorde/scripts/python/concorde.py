#!/usr/bin/env python3
"""Portable entry point that resolves the bundled runtime relative to itself."""

from pathlib import Path
import sys

EXTENSION_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(EXTENSION_ROOT / "runtime"))

from concorde.cli import main  # noqa: E402

raise SystemExit(main())
