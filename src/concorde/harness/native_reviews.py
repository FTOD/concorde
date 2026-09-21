"""Finite scope preparation and aggregate admission; native workflow owns reviewer order."""

from __future__ import annotations
import json
import sys
from dataclasses import replace
from pathlib import Path
from shlex import join

from ..spec.repository import SpecError, digest
from ..spec.typed_data import canonical, typed
from ..review.review import (
    scope_members,
    inputs,
    accept_review_result,
    aggregate_scope,
    _failed_review,
)
from .context import ContextSnapshot
from .host import OperationHost
from .invocation import Invocation
from .native_evidence import _record, NativeChildEvidence, verify_native_children
from .native_runtime import admit_native_runtime


def prepare_scope(run, payload):
    from .native_context import execute, _write, candidate_input_digest

    mode = "spec" if run.operation == "concorde-spec-review" else "code"
    components, identity, members = scope_members(run, mode, initialize=True)
    if run.host.mode == "describe-policy":
        return {
            "state": "described",
            "accepted": False,
            "scope": [t["target_id"] for t in members],
            "output": run.response(
                "described",
                "Fresh native reviewers; prompt-level read-only file policy; no reviewer ran.",
            ),
        }
    if not members:
        raise SpecError(
            "review scope contains no executable reviewer", "unsupported_target"
        )
    slots = []
    for task in members:
        envelope = {
            **payload["invocation"],
            "input": typed(
                run.operation + "-request",
                {k: v for k, v in task.items() if v is not None},
            ),
        }
        value = execute(
            run.host.package_root,
            "prepare-review-item",
            {**payload, "invocation": envelope},
        )
        if value.get("state") != "prepared":
            raise SpecError(
                "review preparation refused: " + canonical(value), "invalid_context"
            )
        slots.append(
            {k: value[k] for k in ("descriptor", "digest", "ticket", "call", "binding")}
        )
    root = _record(Path(slots[0]["descriptor"]))
    scope = {
        "operation": run.operation,
        "mode": mode,
        "parent_task": run.task,
        "configuration": run.configuration,
        "components": components,
        "scope_identity": identity,
        "members": members,
        "slots": slots,
        "candidate_digest": candidate_input_digest(run.repository.root),
        "parent_spec": run.repository.spec_context(run.target.id).value,
    }
    _write(Path(root["directory"]) / "review-scope.json", scope)
    return {
        **slots[0],
        "state": "prepared",
        "accepted": False,
        "workflow_kind": "review",
        "output": run.response(
            "described", "Native review scope prepared, not reviewed."
        ),
    }


def _root_run(package, base, scope):
    return Invocation(
        scope["operation"],
        scope["configuration"],
        scope["parent_task"],
        OperationHost(Path(base["project_root"]), package),
    )


def _current(run, scope, *, check_members=False):
    from .native_context import candidate_input_digest

    from .configuration import load_configuration

    if load_configuration(run.repository.root) != scope["configuration"]:
        raise SpecError("review configuration changed", "configuration_mismatch")
    components, identity, members = scope_members(run, scope["mode"])
    if (
        components != scope["components"]
        or identity != scope["scope_identity"]
        or members != scope["members"]
        or run.repository.spec_context(run.target.id).value != scope["parent_spec"]
        or candidate_input_digest(run.repository.root) != scope["candidate_digest"]
    ):
        raise SpecError("native aggregate review scope changed", "stale_context")
    if check_members:
        from .context import recheck_context

        for task, entry in zip(scope["members"], scope["slots"], strict=True):
            slot = _record(Path(entry["descriptor"]))
            if digest(slot) != entry["digest"]:
                raise SpecError("review descriptor changed", "stale_context")
            child = Invocation(
                scope["operation"],
                scope["configuration"],
                task,
                replace(run.host, coordinated=True),
            )
            recheck_context(
                child.repository, ContextSnapshot(canonical(slot["snapshot"]))
            )
            if inputs(child, scope["mode"])[0] != slot["review_input"]:
                raise SpecError(
                    "review member changed before aggregate acceptance", "stale_context"
                )


def _failure(run, scope, error):
    outputs = []
    for task in scope["members"]:
        child = Invocation(
            scope["operation"],
            scope["configuration"],
            task,
            replace(run.host, coordinated=True),
        )
        info, _ = inputs(child, scope["mode"])
        outputs.append(_failed_review(child, info, None, error)["data"])
    return aggregate_scope(
        run, scope["mode"], scope["components"], scope["scope_identity"], outputs
    )


def workflow_service(package, action, path, expected):
    from .native_context import execute, _write
    from .native_planning import descriptor

    base = descriptor(
        path, expected, allow_invalid=action in {"workflow-result", "workflow-stop"}
    )
    directory = Path(base["directory"])
    scope = _record(directory / "review-scope.json")
    if action == "workflow-stop":
        (directory / "workflow-stopped").touch(exist_ok=True)
        return {"state": "cancelled", "accepted": False}
    binding = _record(directory / "workflow-binding.json")
    status = _record(Path(binding["asyncDir"]) / "status.json")
    if (
        status.get("runId") != binding["runId"]
        or status.get("sessionId") != base["native_session_id"]
    ):
        raise SpecError("foreign native review workflow", "incompatible_handoff")
    receipt = directory / "workflow-result.json"
    run = _root_run(package, base, scope)
    if action == "workflow-result":
        if not receipt.exists() and status.get("state") in {"failed", "stopped"}:
            try:
                _current(run, scope)
                output = _failure(
                    run,
                    scope,
                    SpecError(
                        "native scope failed or did not cover every reviewer",
                        "execution_failed",
                    ),
                )
                _write(
                    receipt, {"state": "failed", "accepted": False, "output": output}
                )
            except SpecError as error:
                return {
                    "state": "stale",
                    "accepted": False,
                    "error": str(error),
                    "native_state": status.get("state"),
                }
        return {
            **(
                _record(receipt)
                if receipt.exists()
                else {"state": "running", "accepted": False}
            ),
            "native_state": status.get("state"),
            "native_error": status.get("error"),
            "run_id": binding["runId"],
        }
    if (directory / "workflow-stopped").exists():
        raise SpecError("native review cancelled", "execution_cancelled")
    _current(run, scope)
    slots = []
    expected_children = []
    for index, entry in enumerate(scope["slots"]):
        slot = descriptor(entry["descriptor"], entry["digest"])
        slots.append(slot)
        if action == "workflow-check":
            checked = execute(
                package, "check", {}, entry["descriptor"], entry["digest"]
            )
            if checked.get("state") != "prepared":
                raise SpecError("review preflight stale", "stale_context")
        else:
            proposal = _record(Path(slot["directory"]) / "proposal.json")
            expected_children.append(
                NativeChildEvidence(
                    "review-" + str(index),
                    slot["agent"],
                    slot["ticket"],
                    digest(proposal),
                    entry["call"]["gate"]["command"],
                    slot["ticket"],
                )
            )
    if action == "workflow-check":
        return {"state": "ready"}
    if action != "workflow-finalize":
        raise SpecError("unknown review Host action", "invalid_input")
    verify_native_children(
        Path(binding["asyncDir"]),
        run_id=binding["runId"],
        session_id=base["native_session_id"],
        ticket=base["ticket"],
        children=tuple(expected_children),
        runtime=admit_native_runtime(Path(base["runtime"]["package_root"])),
    )
    admitted = []
    for index, (entry, slot) in enumerate(zip(scope["slots"], slots, strict=True)):
        key = "review-" + str(index)
        emissions = [
            v
            for v in status["workflow"]["emits"]
            if v.get("kind") == "concorde.child-terminal" and v.get("key") == key
        ]
        if len(emissions) != 1:
            raise SpecError("missing reviewer coverage", "invalid_completion")
        event = emissions[0]
        preflight = _record(Path(slot["directory"]) / "preflight.json")
        value = execute(
            package,
            "admit-review",
            {
                "details": {
                    "mode": "single",
                    "runId": event["runId"],
                    "results": [event["result"]],
                },
                "isError": False,
                "tool_call_id": binding["runId"] + "/" + key,
                "session_id": slot["session_id"],
                "launch_contract_digest": preflight["launchContractDigest"],
                "gate_command": entry["call"]["gate"]["command"],
            },
            entry["descriptor"],
            entry["digest"],
        )
        if value.get("state") != "admitted":
            raise SpecError(
                "review proposal was not independently admitted", "invalid_completion"
            )
        admitted.append(value)
    # No review persistence drives model progression. Recheck all members after their
    # individual admissions, so an earlier member cannot go stale while others are checked.
    _current(run, scope, check_members=True)
    _write(directory / "aggregate-terminal.json", {"state": "finalizing"})
    outputs = []
    for task, slot, value in zip(scope["members"], slots, admitted, strict=True):
        child = Invocation(
            scope["operation"],
            scope["configuration"],
            task,
            replace(run.host, coordinated=True),
        )
        snapshot = ContextSnapshot(canonical(slot["snapshot"]))
        child.last_context = snapshot.id
        outputs.append(
            accept_review_result(
                child,
                snapshot,
                slot["review_input"],
                value["proposal"]["result"]["data"],
            )["data"]
        )
    output = aggregate_scope(
        run, scope["mode"], scope["components"], scope["scope_identity"], outputs
    )
    from .status_store import write_run

    write_run(
        run.repository.root,
        f".concorde/runs/{run.host.invocation_id}/native-reviews.json",
        canonical(
            {"scope": scope, "binding": binding, "admitted": admitted, "output": output}
        ).encode(),
    )
    _write(receipt, {"state": "accepted", "accepted": True, "output": output})
    return {
        "state": "finished",
        "accepted": True,
        "outcome": output["data"]["outcome"],
        "reviewers": len(outputs),
    }
