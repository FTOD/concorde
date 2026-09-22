"""Selected causal evidence from real native probes to the tester's issued report directory.

Only model events are scripted. No native transcript, proposal body, auth or environment is
exported. This driver deliberately exits nonzero when the product caller reports refusal; a
passing probe assertion must not turn the command carrying that refusal into success.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from concorde.harness.execution_error import (
    exception_feedback,
    response_failure,
)
from concorde.harness.native_runtime import admit_native_runtime


def nodes(feedback):
    yield feedback
    for cause in feedback["causes"]:
        yield from nodes(cause)


def native_refusal(source: Path, native: Path, sdk: Path, case: str):
    workflow = case == "workflow"
    scenario = {
        "direct": "business-invalid",
        "schema": "malformed",
        "workflow": "empty-plan",
        "optional": "business-invalid",
        "cancel": "cancel",
    }[case]
    completed = subprocess.run(
        [
            "node",
            str(
                source
                / "tests/concorde/harness"
                / (
                    "native_planning_probe.mjs"
                    if workflow
                    else "native_context_probe.mjs"
                )
            ),
            str(native),
            str(sdk),
            str(source),
            scenario,
        ],
        capture_output=True,
        text=True,
        timeout=100,
        check=True,
    )
    summary = json.loads(completed.stdout.splitlines()[-1])
    root = Path(summary["root"])
    if workflow:
        response = json.loads((root / "plan-result.json").read_text())
    else:
        final = json.loads((root / "final.json").read_text())
        assert final["isError"]
        response = final["details"]["concorde_context"]
    assert not response["accepted"]
    return response_failure(
        "Selected product caller refused completion",
        response,
        layer="integration-driver",
    ), summary


def selected_references(feedback, scratch: Path):
    """Select only known sanitized causal records, never automatically archive native paths."""
    selected, unretained = {}, set()
    for node in nodes(feedback):
        for ref in node["diagnostics"]["references"]:
            # Native status/metadata and display paths are not themselves sanitized records.
            if not isinstance(ref, str):
                continue
            file = Path(ref)
            if not (
                file.name == "failure.json"
                or file.name.startswith(("host-failure-", "submission-error-"))
            ):
                unretained.add(ref)
                continue
            resolved = file.resolve(strict=True)
            assert resolved.is_relative_to(scratch)
            assert not any(p.is_symlink() for p in (file, *file.parents))
            raw = file.read_bytes()
            assert len(raw) <= 2 * 1024 * 1024
            detail = json.loads(raw)
            assert detail["schema_version"] == 1 and detail["diagnostics"]["redacted"]
            # The exact error selected by the caller is already sanitized by production.
            selected[ref] = {
                "source": ref,
                "source_digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
                "source_bytes": len(raw),
                "feedback": detail,
            }
    return list(selected.values()), sorted(unretained)


def main():
    source, native, sdk = map(Path, sys.argv[1:4])
    case = sys.argv[4]
    scratch = Path(os.environ["CONCORDE_CHECK_TMPDIR"])
    binding = admit_native_runtime(native)
    observed = {}

    def service(_context):
        cause, summary = native_refusal(source, native, sdk, case)
        observed.update(summary)
        raise cause

    try:
        if case == "optional":
            from concorde.harness.operation_node import OperationNode
            from tests.concorde.harness.test_operation_node import _stage_context

            OperationNode("planner").graph(service).invoke(_stage_context()["data"])
        else:
            service(None)
    except Exception as error:
        feedback = exception_feedback(error)
    else:
        raise AssertionError("fixture unexpectedly completed")
    # Setup/observer failures must not masquerade as the intended native execution.
    assert observed["realModelCalls"] == 0
    assert observed["scriptedCalls"] == (2 if case == "workflow" else 1)
    selected, unretained = selected_references(feedback, scratch)
    report = {
        "schema_version": 1,
        "case": case,
        "scratch": str(scratch),
        "native_source_digest": binding.source_digest,
        "scripted_calls": observed["scriptedCalls"],
        "real_model_calls": observed["realModelCalls"],
        "accepted": False,
        "failure": feedback,
        "selected_diagnostics": selected,
        "unretained_native_references": unretained,
        "semantic_complete": all(n["diagnostics"]["complete"] for n in nodes(feedback)),
    }
    raw = (json.dumps(report, indent=2) + "\n").encode()
    assert len(raw) < 2 * 1024 * 1024, "selected evidence exceeds explicit report bound"
    report_path = Path(os.environ["CONCORDE_CHECK_REPORT_DIR"]) / "causal.json"
    report_path.write_bytes(raw)
    report_path.chmod(0o600)
    print(json.dumps({"case": case, "report": "causal.json", "realModelCalls": 0}))
    print(
        "Selected product failure; retrieve causal.json via Host manifest",
        file=sys.stderr,
    )
    return 17


if __name__ == "__main__":
    raise SystemExit(main())
