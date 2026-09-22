"""Tester command bridge: OS read-only execution with Host-owned durable evidence."""

from __future__ import annotations

import json
import math
import os
import signal
import sys
from pathlib import Path
from threading import Event

from ..harness.check_evidence import CheckEvidence, report_names
from ..harness.check_executor import execute_check


def main() -> int:
    cancel_event = Event()

    def cancel(_signal, _frame):
        # Poll cancellation at the execution boundary, never interrupt cleanup/export.
        cancel_event.set()

    signal.signal(signal.SIGTERM, cancel)
    signal.signal(signal.SIGINT, cancel)
    selection = None
    if os.environ.get("CONCORDE_SESSION_SELECTION"):
        from ..harness.entry import runtime_selection

        selection = runtime_selection(Path(__file__).resolve().parents[3])
    request = json.load(sys.stdin)
    if (
        not isinstance(request, dict)
        or not {"command", "timeout"}
        <= set(request)
        <= {"command", "timeout", "reports"}
        or not isinstance(request["command"], str)
        or len(request["command"]) > 32768
        or type(request["timeout"]) not in (int, float)
        or not math.isfinite(request["timeout"])
        or not 0 < request["timeout"] <= 3600
    ):
        raise ValueError("invalid tester command")
    names = report_names(request.get("reports", []))
    evidence = CheckEvidence(
        Path.cwd(),
        names,
        command=request["command"],
        timeout=request["timeout"],
        selection=selection,
        tool_call_id=os.environ.get("CONCORDE_TEST_TOOL_CALL_ID"),
    )

    result = None
    failure = None
    try:
        print(
            json.dumps(
                {"tester_check_ready": True, "execution_id": evidence.execution_id}
            ),
            flush=True,
        )
        result = execute_check(
            Path.cwd(),
            ["/bin/bash", "-c", request["command"]],
            timeout=request["timeout"],
            environment=dict(os.environ),
            private_tmp=True,
            evidence=evidence.collect,
            cancel_event=cancel_event,
        )
    except (Exception, KeyboardInterrupt) as error:
        failure = error
    if not evidence.collected:
        evidence.collect(None, result, failure)
    source = result if result is not None else failure
    response = {
        "returncode": result.returncode if result is not None else None,
        "timed_out": result.timed_out if result is not None else False,
        "cancelled": isinstance(failure, KeyboardInterrupt),
        "cancellation_requested": cancel_event.is_set(),
        "error": str(failure) if failure is not None else None,
        "evidence": evidence.summary(),
    }
    for name in ("stdout", "stderr"):
        data = getattr(source, name, b"")
        total = getattr(source, name + "_bytes", None)
        total = len(data) if total is None else total
        response[name] = data[-20000:].decode("utf-8", "replace")
        response[name + "_bytes"] = total
        response[name + "_truncated"] = total > 20000
    # Diagnostics are not telemetry. Command failure never destroys export references.
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
