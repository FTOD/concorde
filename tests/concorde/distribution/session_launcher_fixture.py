"""A stand-in launcher for the Pi session tool: capability runs and native preparation steps.

Like ``scripts/run-operation.py`` it takes one capability name, reads one capability request from
standard input and prints one result envelope; with ``--native-context <step>`` it answers the
native preparation and workflow steps the session extension sends. Every invocation appends
``{"argv", "stdin"}`` as one JSON line to ``SESSION_LAUNCHER_LOG``. ``SESSION_LAUNCHER_SCENARIO``
selects the run outcome:

- ``echo`` (default): a succeeded envelope whose ``output`` echoes the request;
- ``blocked``: a blocked envelope, exit 3;
- ``failed-zero``: a failed envelope, exit 0;
- ``nonzero``: a succeeded envelope, exit 5;
- ``garbage``: text that is not JSON, exit 0.

``SESSION_LAUNCHER_DIR`` is a scratch directory for the prepared workflow's descriptor and
package files.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[3]
WORKFLOW_RESULT = {
    "state": "accepted",
    "accepted": True,
    "native_state": "completed",
    "result": {"status": "succeeded", "reconciled_by": "fixture-host"},
}


def envelope(operation: str, request: dict, status: str = "succeeded") -> dict:
    return {
        "type_id": "concorde-operation-result",
        "schema_version": 3,
        "operation_id": operation,
        "invocation_id": "fixture-invocation",
        "mode": request.get("mode"),
        "status": status,
        "workspace": None,
        "output": {"echo": request} if status == "succeeded" else None,
        "errors": []
        if status == "succeeded"
        else [
            {"code": "invalid_input", "field": "/task", "message": "task is required"}
        ],
    }


def prepared_workflow(value: dict) -> dict:
    directory = Path(os.environ["SESSION_LAUNCHER_DIR"])
    package = directory / "package"
    (package / "pi").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(
        REPOSITORY / "pi/execution-error.mjs", package / "pi/execution-error.mjs"
    )
    (package / "workflow.js").write_text(
        "const plan = __CONCORDE_WORKFLOW__;\n", encoding="utf-8"
    )
    descriptor = directory / "descriptor.json"
    operation = value["invocation"]["operation_id"]
    descriptor.write_text(
        json.dumps(
            {
                "operation": operation,
                "package_root": str(package),
                "runtime": {"package_root": str(REPOSITORY / "pi")},
                "directory": str(directory),
                "project_root": str(Path.cwd()),
            }
        ),
        encoding="utf-8",
    )
    return {
        "state": "prepared",
        "accepted": False,
        "ticket": "fixture-ticket",
        "descriptor": str(descriptor),
        "workflow": {
            "name": "concorde-fixture-workflow",
            "script": "workflow.js",
            "helpers": [],
            "commands": {"host-step": ["true"]},
            "expansion": {"steps": 1},
        },
        "binding": {
            "argv": [sys.executable, str(Path(__file__).resolve()), "--native-context"],
            "descriptor": str(descriptor),
            "digest": "fixture-digest",
            "root": str(Path.cwd()),
        },
    }


def native(step: str, value: dict) -> dict:
    if step == "prepare":
        invocation = value["invocation"]
        if os.environ.get("SESSION_LAUNCHER_NATIVE") == "workflow":
            return prepared_workflow(value)
        return {
            "state": "prepared",
            "accepted": False,
            "descriptor": "fixture-descriptor",
            "digest": "fixture-digest",
            "call": {
                "agent": "concorde-context-assessor",
                "task": f"prepared for {invocation['operation_id']}",
                "context": "fresh",
            },
        }
    if step == "workflow-result":
        return WORKFLOW_RESULT
    return {"state": step}


def main() -> int:
    raw = sys.stdin.read()
    log = os.environ.get("SESSION_LAUNCHER_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as stream:
            stream.write(json.dumps({"argv": sys.argv[1:], "stdin": raw}) + "\n")
    value = json.loads(raw or "{}")
    if sys.argv[1:2] == ["--native-context"]:
        print(json.dumps(native(sys.argv[2], value)))
        return 0
    operation = sys.argv[1]
    scenario = os.environ.get("SESSION_LAUNCHER_SCENARIO", "echo")
    if scenario == "blocked":
        print(json.dumps(envelope(operation, value, "blocked")))
        return 3
    if scenario == "failed-zero":
        print(json.dumps(envelope(operation, value, "failed")))
        return 0
    if scenario == "nonzero":
        print(json.dumps(envelope(operation, value)))
        return 5
    if scenario == "garbage":
        print("launcher crashed before printing an envelope")
        return 0
    print(json.dumps(envelope(operation, value)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
