#!/usr/bin/env python3
"""List configured model candidates, from any directory (no Git required)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from concorde.harness.available_models import main

if __name__ == "__main__":
    raise SystemExit(main())
