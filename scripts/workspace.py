#!/usr/bin/env python3
"""Compatibility filename for the typed context Operation; no positional task arguments."""
import sys
from pathlib import Path
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))
from concorde.capabilities.operation_service import operation_main
if __name__ == "__main__":
    raise SystemExit(operation_main("concorde-context", PACKAGE_ROOT))
