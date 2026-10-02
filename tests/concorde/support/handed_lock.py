"""Hand a lock the test holds to the code it calls in this same process.

A process handed a lock adopts the descriptor its environment's ``CONCORDE_INHERITED_LOCKS`` names
(Tracing's "Handing a lock on"). ``handed`` gives the code run in its block a duplicate of the
descriptor the test holds the lock with, named there, as a task merge hands its merge lock to the
``concorde issues`` it starts; the code adopts it once, without waiting, and closes it as it lets
the lock go, while the test's own descriptor keeps holding it.
"""

from __future__ import annotations

import contextlib
import json
import os
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from concorde.kernel.tracing import locks


@contextmanager
def handed(path: Path, descriptor: int):
    """Run the block as a process handed the lock ``path`` that ``descriptor`` holds."""
    copy = os.dup(descriptor)
    with (
        patch.dict(os.environ, {locks.INHERITED: json.dumps({str(path): copy})}),
        patch.object(locks, "_inherited", None),
    ):
        try:
            yield
        finally:
            # Adopted, the copy was closed as the lock was let go; never adopted, close it here.
            left = locks._inherited
            if left is None or left.get(os.path.realpath(path)) == copy:
                with contextlib.suppress(OSError):
                    os.close(copy)
