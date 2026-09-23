#!/usr/bin/env python3
"""Bootstrap the supported Distribution installer from this exact package."""

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
# The declaration packages ``agents`` and ``operations`` live at the package root.
sys.path.insert(0, str(PACKAGE_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from concorde.distribution.installation import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
