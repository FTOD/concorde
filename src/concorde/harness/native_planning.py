"""Finite planning workflow services. Native JavaScript alone orders model children."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from ..spec.repository import SpecError, digest
from ..spec.typed_data import canonical
from .native_evidence import _record, NativeChildEvidence, verify_native_children
from .native_runtime import admit_native_runtime


def relay_prepare(host, invocation, candidate, payload):
    from .relay import relay_launcher

    # Explicit private selection may bind candidate code to disposable Git data.
    # Ordinary installed execution instead enters the verified candidate-local runtime.
    argv = (
        [sys.executable, str(host.package_root / "scripts/run-operation.py")]
        if host.session_provenance
        else relay_launcher(
            host,
            candidate,
            bootstrap=bool(host.relay_target.get("bootstrap_installation")),
        )
    )
    process = subprocess.run(
        [*argv, "--native-context", "prepare"],
        input=canonical({**payload, "invocation": invocation}),
        text=True,
        capture_output=True,
        cwd=candidate,
        timeout=120,
    )
    try:
        value = json.loads(process.stdout)
    except ValueError as error:
        raise SpecError(
            "candidate native preparation returned no envelope", "relay_failed"
        ) from error
    return value


def descriptor(path, expected, *, allow_invalid=False):
    value = _record(Path(path))
    if digest(value) != expected:
        raise SpecError("planning descriptor changed", "stale_context")
    if not allow_invalid and (Path(value["directory"]) / "invalid").exists():
        raise SpecError("planning workflow was invalidated", "invalid_completion")
    return value


def workflow_service(package, action, path, expected):
    from .native_context import execute, _write

    base = descriptor(
        path, expected, allow_invalid=action in {"workflow-result", "workflow-stop"}
    )
    directory = Path(base["directory"])
    if action == "workflow-stop":
        (directory / "workflow-stopped").touch(exist_ok=True)
        return {"state": "cancelled", "accepted": False}
    if action != "workflow-result" and (directory / "workflow-stopped").exists():
        raise SpecError("native planning was cancelled", "execution_cancelled")
    binding = _record(directory / "workflow-binding.json")
    status = _record(Path(binding["asyncDir"]) / "status.json")
    if (
        status.get("runId") != binding["runId"]
        or status.get("sessionId") != base["native_session_id"]
    ):
        raise SpecError("foreign native planning workflow", "incompatible_handoff")
    receipt = directory / "workflow-result.json"
    if action == "workflow-result":
        if status.get("state") in {"failed", "stopped"} and not receipt.exists():
            # Record terminal failure only while this invocation still owns the same
            # semantic candidate inputs; an old status poll cannot invalidate newer work.
            from .change_worktree import repository_lock, progress
            from .native_context import candidate_input_digest

            latest = base
            if (directory / "planner.json").exists():
                prepared = _record(directory / "planner.json")
                latest = _record(Path(prepared["descriptor"]))
            root = Path(latest["project_root"])
            with repository_lock(root):
                if candidate_input_digest(root) == latest["change_digest"]:
                    progress(
                        root,
                        status="blocked",
                        outcome="execution_cancelled"
                        if status.get("state") == "stopped"
                        else "execution_failed",
                    )
        value = (
            _record(receipt)
            if receipt.exists()
            else {
                "state": "running" if status.get("state") == "running" else "failed",
                "accepted": False,
            }
        )
        return {
            **value,
            "native_state": status.get("state"),
            "native_error": status.get("error"),
            "run_id": binding["runId"],
        }
    slots = [("assessor", base, str(path), expected)]
    if action == "workflow-finalize":
        planner = _record(directory / "planner.json")
        slot = descriptor(planner["descriptor"], planner["digest"])
        slots.append(("planner", slot, planner["descriptor"], planner["digest"]))
    expected_children = []
    for key, slot, file, checksum in slots:
        proposal = _record(Path(slot["directory"]) / "proposal.json")
        from shlex import join

        gate = join(
            [
                sys.executable,
                str(package / "scripts/run-operation.py"),
                "--native-context",
                "stage",
                file,
                checksum,
            ]
        )
        expected_children.append(
            NativeChildEvidence(
                key,
                slot["agent"],
                slot["ticket"],
                digest(proposal),
                gate,
                slot["ticket"],
            )
        )
    verify_native_children(
        Path(binding["asyncDir"]),
        run_id=binding["runId"],
        session_id=base["native_session_id"],
        ticket=base["ticket"],
        children=tuple(expected_children),
        runtime=admit_native_runtime(Path(base["runtime"]["package_root"])),
    )
    key, slot, file, checksum = slots[-1]
    emissions = [
        v
        for v in status["workflow"]["emits"]
        if v.get("kind") == "concorde.child-terminal" and v.get("key") == key
    ]
    if len(emissions) != 1:
        raise SpecError("missing native planning child", "stale_evidence")
    emission = emissions[0]
    preflight = _record(Path(slot["directory"]) / "preflight.json")
    value = execute(
        package,
        "accept",
        {
            "details": {
                "mode": "single",
                "runId": emission["runId"],
                "results": [emission["result"]],
            },
            "isError": False,
            "tool_call_id": binding["runId"] + "/" + key,
            "session_id": slot["session_id"],
            "launch_contract_digest": preflight["launchContractDigest"],
            "gate_command": expected_children[-1].gate_command,
        },
        file,
        checksum,
    )
    if not value.get("accepted"):
        raise SpecError(
            "native planning result was rejected: " + canonical(value),
            "invalid_completion",
        )
    if action == "workflow-advance" and value.get("outcome") == "sufficient":
        next_value = execute(package, "prepare-planner", {}, str(path), expected)
        if next_value.get("state") != "prepared":
            _write(receipt, next_value)
            return {"state": "stopped", "accepted": False}
        _write(directory / "planner.json", next_value)
        return next_value
    _write(receipt, value)
    return {
        "state": "finished",
        "accepted": value["accepted"],
        "outcome": value.get("outcome"),
    }
