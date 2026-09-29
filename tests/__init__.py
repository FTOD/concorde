"""Repository test package.

Importing this package puts the runtime sources on ``sys.path`` once, so any test module can run
on its own (``python -m pytest tests/concorde/spec/test_checks.py``, or
``python -m unittest tests.concorde.spec.test_checks``) without relying on the collection
order that previously imported a module doing this insertion first.

It also points the model map at the tests' own, so that no test, nor any process a test starts,
resolves a worker's model through the developer's map; a test of the map names its own.
"""

import os
import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parent.parent / "src"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
MODEL_MAP = Path(__file__).resolve().parent / "concorde/support/models.json"
os.environ["CONCORDE_MODEL_MAP"] = str(MODEL_MAP)
