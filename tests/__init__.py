"""Repository test package.

Importing this package puts the runtime sources on ``sys.path`` once, so any test module can run
on its own (``python -m pytest tests/concorde/spec/test_checks.py``, or
``python -m unittest tests.concorde.spec.test_checks``) without relying on the collection
order that previously imported a module doing this insertion first.
"""

import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parent.parent / "src"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
