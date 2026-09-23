"""A stand-in for ``scripts/run-operation.py`` that exercises the Pi session extension's tool.

Like the real launcher it takes one public Operation name as its argument, reads one invocation
envelope from stdin and prints one result envelope, with diagnostics on stderr and exit code 3
for a result that is not succeeded or described. The scenario is chosen by FAKE_LAUNCHER_SCENARIO:

- ``echo`` (default): succeed and return the received envelope inside ``output``;
- ``blocked``: return a blocked result with one error and exit 3;
- ``hang``: wait; on SIGTERM print a cancelled result and exit 3, as the real launcher does;
- ``stubborn``: wait and ignore SIGTERM, so only killing the process group ends the run;
- ``large``: succeed with an output well above the extension's 48 KiB return limit.
"""
import json
import os
import signal
import sys
import time


def result(operation: str, envelope: dict, **changes) -> dict:
    value = {
        "type_id": "concorde-operation-result",
        "schema_version": 3,
        "operation_id": operation,
        "invocation_id": "fake-invocation",
        "mode": envelope.get("mode"),
        "status": "succeeded",
        "workspace": None,
        "output": {"echo": envelope},
        "errors": [],
    }
    value.update(changes)
    return value


def main() -> int:
    operation = sys.argv[1] if len(sys.argv) > 1 else None
    scenario = os.environ.get("FAKE_LAUNCHER_SCENARIO", "echo")
    envelope = json.loads(sys.stdin.read() or "{}")
    if scenario in {"hang", "stubborn"}:
        def cancelled(signum, frame):
            print(json.dumps(result(operation, envelope, status="failed", output=None,
                                    errors=[{"code": "execution_cancelled", "field": "",
                                             "message": "operation cancelled by the host"}])))
            sys.stdout.flush()
            raise SystemExit(3)
        signal.signal(signal.SIGTERM, cancelled if scenario == "hang" else signal.SIG_IGN)
        time.sleep(60)
        return 0
    if scenario == "blocked":
        print(json.dumps(result(operation, envelope, status="blocked", output=None,
                                errors=[{"code": "invalid_input", "field": "/task",
                                         "message": "task is required"}])))
        return 3
    if scenario == "large":
        print(json.dumps(result(operation, envelope, output={"filler": "x" * (64 * 1024)})))
        return 0
    print(json.dumps(result(operation, envelope)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
