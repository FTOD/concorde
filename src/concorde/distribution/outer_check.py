"""Tester command bridge: OS read-only governing tree, disposable external fixtures only."""

from __future__ import annotations

import json
import os
import signal
import sys
from pathlib import Path

from ..harness.check_executor import execute_check


def main() -> int:
    def cancel(_signal, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, cancel)
    if os.environ.get("CONCORDE_SESSION_SELECTION"):
        from ..harness.entry import runtime_selection

        runtime_selection(Path(__file__).resolve().parents[3])
    request = json.load(sys.stdin)
    if set(request) != {"command", "timeout"} or not isinstance(
        request["command"], str
    ):
        raise ValueError("invalid tester command")
    result = execute_check(
        Path.cwd(),
        ["/bin/bash", "-c", request["command"]],
        timeout=request["timeout"],
        environment=dict(os.environ),
        private_tmp=True,
    )
    # Diagnostics returned to the tester are not telemetry.
    print(
        json.dumps(
            {
                "returncode": result.returncode,
                "timed_out": result.timed_out,
                "stdout": result.stdout[-20000:].decode("utf-8", "replace"),
                "stderr": result.stderr[-20000:].decode("utf-8", "replace"),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
