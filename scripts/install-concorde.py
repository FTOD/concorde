#!/usr/bin/env python3
"""Install Concorde into a project: ``python3 scripts/install-concorde.py <project>``."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from concorde.distribution.install import main  # noqa: E402

sys.exit(main(sys.argv[1:]))
