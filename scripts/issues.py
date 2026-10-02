#!/usr/bin/env python3
"""The Issues bookkeeping command, ``concorde issues``, run directly from a checkout."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from concorde.issues.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
