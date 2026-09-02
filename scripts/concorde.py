#!/usr/bin/env python3
"""Portable entry point that resolves the Concorde runtime relative to itself."""

from pathlib import Path
import sys

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from concorde.cli import main  # noqa: E402

raise SystemExit(main())
