"""Bounded Issue workflow Host steps and exclusive invocation-owned slot transport."""

from __future__ import annotations

import dataclasses
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from ..issues.graph import MAX_DECISIONS
from ..issues.solve import IssueSolve
from ..spec.repository import SpecError, digest
from ..spec.typed_data import canonical, typed
from .execution_error import response_failure, safe_text, workflow_feedback
from .host import OperationHost
from .invocation import Invocation
from .native_evidence import NativeChildEvidence, _record, verify_native_children
from .native_runtime import admit_native_runtime

SLOT = re.compile(r"^(d-[0-5]|v-[0-5]-[0-3]-[0-9]+)$")


def _save(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(canonical(value))
    os.replace(temporary, path)


def _root(path, expected):
    root = _record(Path(path))
    if digest(Path(path).read_bytes()) != expected:
        raise SpecError("Issue root descriptor changed", "stale_context")
    return root


def _ensure_running(root):
    if (Path(root["directory"]) / "stopped").exists():
        raise SpecError("Issue workflow stopped", "execution_cancelled")


def _run(package, root):
    from .configuration import load_configuration

    if (
        str(package) != root["package_root"]
        or load_configuration(Path(root["project_root"])) != root["configuration"]
    ):
        raise SpecError("Issue runtime/configuration changed", "configuration_mismatch")
    return Invocation(
        "concorde-issues",
        root["configuration"],
        root["task"],
        OperationHost(Path(root["project_root"]), package),
    )


def prepare_root(run, payload):
    from .native_context import _write, native_output_schema

    if run.host.mode == "describe-policy":
        return {
            "state": "described",
            "accepted": False,
            "output": run.response(
                "described",
                "Native bounded Issue decisions/reviews and journaled Host disposition; no child ran.",
            ),
        }
    domain = IssueSolve(run)
    route = domain.prepare({})
    if route["route"] == "finish":
        return {
            "state": "not-run",
            "accepted": True,
            "output": domain.finish({})["output"],
        }
    runtime = admit_native_runtime(Path(payload["native_root"]))
    directory = Path(tempfile.mkdtemp(prefix="concorde-native-issue-"))
    ticket = str(uuid.uuid4())
    root = {
        "schema_version": 1,
        "operation": "concorde-issues",
        "directory": str(directory),
        "ticket": ticket,
        "package_root": str(run.host.package_root),
        "python": sys.executable,
        "node": payload["native_node"],
        "project_root": str(run.repository.root),
        "configuration": run.configuration,
        "task": run.task,
        "envelope": payload["invocation"],
        "session_id": payload["session_id"],
        "native_session_id": payload.get("native_session_id", payload["session_id"]),
        "runtime": dataclasses.asdict(runtime),
        "stageSchema": native_output_schema("concorde-agent-stage-result"),
        "reviewSchema": native_output_schema("concorde-review-stage-result"),
    }
    path = directory / "descriptor.json"
    _write(path, root)
    checksum = digest(root)
    _save(
        directory / "issue-session.json",
        {
            "domain": domain.dump(),
            "iteration": 0,
            "phase": "next",
            "inventory": [],
            "groups": [],
        },
    )
    argv = [
        sys.executable,
        str(run.host.package_root / "scripts/run-operation.py"),
        "--native-context",
    ]
    return {
        "state": "prepared",
        "accepted": False,
        "workflow_kind": "issue",
        "descriptor": str(path),
        "digest": checksum,
        "ticket": ticket,
        "binding": {
            "argv": argv,
            "root": str(run.repository.root),
            "descriptor": str(path),
            "digest": checksum,
        },
        "output": run.response(
            "described", "Native Issue workflow prepared; no decision accepted."
        ),
    }


def slot_binding(root, key):
    if not SLOT.fullmatch(key):
        raise SpecError("invalid Issue slot index", "invalid_input")
    return _record(Path(root["directory"]) / "bindings" / f"{key}.json")


def stage_slot(package, path, checksum, key):
    from .native_context import execute

    root = _root(path, checksum)
    if (Path(root["directory"]) / "stopped").exists():
        raise SpecError("Issue workflow stopped", "execution_cancelled")
    entry = slot_binding(root, key)
    if entry["root_digest"] != checksum or entry["key"] != key:
        raise SpecError("foreign Issue slot binding", "incompatible_handoff")
    return execute(package, "stage", {}, entry["descriptor"], entry["digest"])


def _prepare_slot(package, root, path, checksum, key, operation, task, selection=None):
    from .native_context import _write, execute

    _ensure_running(root)
    directory = Path(root["directory"])
    (directory / "bindings").mkdir(exist_ok=True)
    if (directory / "bindings" / f"{key}.json").exists():
        raise SpecError("Issue slot is already issued", "invalid_completion")
    clean = {k: v for k, v in task.items() if v is not None and not k.startswith("_")}
    code = (
        "import {issueCall,issueLayout} from "
        + json.dumps((package / "pi/issue-call.mjs").as_uri())
        + ";console.log(JSON.stringify(issueCall(issueLayout("
        + canonical(root)
        + ","
        + json.dumps(str(path))
        + ","
        + json.dumps(checksum)
        + "),"
        + json.dumps(key)
        + ")))"
    )
    call = json.loads(
        subprocess.check_output(
            [root["node"], "--input-type=module", "-e", code], text=True
        )
    )
    gate = call["gate"]["command"]
    envelope = {
        **root["envelope"],
        "operation_id": operation,
        "input": typed(operation + "-request", clean),
    }
    payload = {
        "invocation": envelope,
        "native_root": root["runtime"]["package_root"],
        "session_id": root["session_id"],
        "native_session_id": root["native_session_id"],
        "native_call": call,
        "slot_directory": str(directory / "slots" / key),
        "slot_ticket": root["ticket"] + ":" + key,
        "gate_command": gate,
    }
    if selection:
        payload["issue_selection"] = selection
    value = execute(
        package, "prepare-issue-item" if selection else "prepare-review-item", payload
    )
    if value.get("state") != "prepared":
        raise response_failure(
            "Issue slot preparation refused", value, layer="issues", attempt=key
        )
    entry = {k: value[k] for k in ("descriptor", "digest", "ticket", "call")}
    entry.update(root_digest=checksum, key=key)
    _write(directory / "bindings" / f"{key}.json", entry)
    return entry


def _correlated(package, root, state, status, binding, key):
    from .native_context import execute

    _ensure_running(root)
    entry = slot_binding(root, key)
    slot = _record(Path(entry["descriptor"]))
    events = [
        x
        for x in status["workflow"]["emits"]
        if x.get("kind") == "concorde.child-terminal" and x.get("key") == key
    ]
    if len(events) != 1:
        raise SpecError("Issue native child evidence missing", "stale_evidence")
    event = events[0]
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
            "session_id": root["session_id"],
            "launch_contract_digest": preflight["launchContractDigest"],
            "gate_command": entry["call"]["gate"]["command"],
        },
        entry["descriptor"],
        entry["digest"],
    )
    if value.get("state") != "admitted":
        raise response_failure(
            "Issue proposal was not admitted",
            value,
            layer="issues",
            attempt=slot["ticket"],
        )
    return value


def _coverage(root, state, status, binding):
    children = []
    for key in state["inventory"]:
        entry = slot_binding(root, key)
        slot = _record(Path(entry["descriptor"]))
        proposal = _record(Path(slot["directory"]) / "proposal.json")
        children.append(
            NativeChildEvidence(
                key,
                slot["agent"],
                slot["ticket"],
                digest(proposal),
                entry["call"]["gate"]["command"],
                slot["ticket"],
            )
        )
    verify_native_children(
        Path(binding["asyncDir"]),
        run_id=binding["runId"],
        session_id=root["native_session_id"],
        ticket=root["ticket"],
        children=tuple(children),
        runtime=admit_native_runtime(Path(root["runtime"]["package_root"])),
    )


def workflow_service(package, action, path, checksum):
    import fcntl

    root = _root(path, checksum)
    directory = Path(root["directory"])
    if action == "workflow-stop":
        (directory / "stopped").touch(exist_ok=True)
        return {"state": "cancelled", "accepted": False}
    if action == "workflow-result":
        binding = _record(directory / "workflow-binding.json")
        status = _record(Path(binding["asyncDir"]) / "status.json")
        if (
            status.get("runId") != binding["runId"]
            or status.get("sessionId") != root["native_session_id"]
        ):
            raise SpecError("foreign Issue workflow", "incompatible_handoff")
        receipt = directory / "workflow-result.json"
        return {
            **(
                _record(receipt)
                if receipt.exists()
                else {
                    "state": "running"
                    if status.get("state") == "running"
                    else "failed",
                    "accepted": False,
                }
            ),
            "native_state": status.get("state"),
            "native_error": safe_text(status["error"]) if status.get("error") else None,
            "failure": workflow_feedback(root, status, binding)
            if status.get("state") not in {"running", "complete"}
            or status.get("error")
            or (status.get("state") != "running" and not receipt.exists())
            else None,
            "run_id": binding["runId"],
        }
    with (directory / "host.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _step(package, action, Path(path), checksum, root, directory)


def _step(package, action, path, checksum, root, directory):
    state = _record(directory / "issue-session.json")
    receipt = directory / "workflow-result.json"
    binding = _record(directory / "workflow-binding.json")
    status = _record(Path(binding["asyncDir"]) / "status.json")
    if (
        status.get("runId") != binding["runId"]
        or status.get("sessionId") != root["native_session_id"]
    ):
        raise SpecError("foreign Issue workflow", "incompatible_handoff")
    if (directory / "stopped").exists() or status.get("state") != "running":
        raise SpecError("Issue workflow is not running", "execution_cancelled")
    match = re.fullmatch(r"workflow-issue-(next|decision|verified)-([0-5])", action)
    if not match:
        raise SpecError("unknown Issue Host step", "invalid_input")
    step, index = match[1], int(match[2])
    if index != state["iteration"] or step != state["phase"]:
        raise SpecError("duplicate/stale Issue workflow step", "invalid_completion")
    run = _run(package, root)
    domain = IssueSolve(run, state["domain"])
    domain.assert_current()
    route = "decide"
    counts = [0, 0, 0, 0]
    if step == "next":
        prepared = domain.prepare_decision()
        if "selection" not in prepared:
            route = "finished"
            output = domain.finish({})["output"]
        else:
            task = {
                **root["envelope"]["input"]["data"],
                "target_id": run.target.id,
                "task": run.task["task"],
                "change_id": run.change_id,
                "expected_revision": domain.solution["revision"],
            }
            key = f"d-{index}"
            _prepare_slot(
                package,
                root,
                path,
                checksum,
                key,
                "concorde-issues",
                task,
                prepared["selection"],
            )
            state["inventory"].append(key)
            state["phase"] = "decision"
    elif step == "decision":
        _coverage(root, state, status, binding)
        value = _correlated(package, root, state, status, binding, f"d-{index}")
        _ensure_running(root)
        decision = domain.accept_decision(value["proposal"]["result"]["data"])
        route = decision["route"]
        if route == "close":
            _ensure_running(root)
            domain.close({})
            output = domain.ready({})["output"]
            route = "finished"
        elif route == "finish":
            output = domain.finish({})["output"]
            route = "finished"
        elif route == "verify":
            from ..review.review import scope_members

            requests = domain.verification_requests()
            state["verification_before"] = domain.current_inputs()
            state["groups"] = []
            for group, (mode, task) in enumerate(requests):
                # Fixed group indices preserve spec/code and Issue-specific/ordinary identity.
                group_index = group if len(requests) == 4 else group * 2
                child = Invocation(
                    "concorde-" + mode + "-review",
                    run.configuration,
                    task,
                    dataclasses.replace(run.host, coordinated=True),
                )
                components, identity, members = scope_members(
                    child, mode, initialize=True
                )
                entries = []
                keys = []
                for member, selected in enumerate(members):
                    key = f"v-{index}-{group_index}-{member}"
                    entries.append(
                        _prepare_slot(
                            package,
                            root,
                            path,
                            checksum,
                            key,
                            child.operation,
                            selected,
                        )
                    )
                    keys.append(key)
                    state["inventory"].append(key)
                from .native_context import candidate_input_digest

                scope = {
                    "operation": child.operation,
                    "mode": mode,
                    "parent_task": child.task,
                    "configuration": run.configuration,
                    "components": components,
                    "scope_identity": identity,
                    "members": members,
                    "slots": entries,
                    "candidate_digest": candidate_input_digest(run.repository.root),
                    "parent_spec": child.repository.spec_context(child.target.id).value,
                }
                state["groups"].append({"scope": scope, "keys": keys})
                counts[group_index] = len(keys)
            state["phase"] = "verified"
    else:
        _coverage(root, state, status, binding)
        from .native_reviews import _current, commit_scope

        admitted = []
        for group in state["groups"]:
            scope = group["scope"]
            child = Invocation(
                scope["operation"],
                run.configuration,
                scope["parent_task"],
                dataclasses.replace(run.host, coordinated=True),
            )
            _current(child, scope, check_members=True)
            values = [
                _correlated(package, root, state, status, binding, key)
                for key in group["keys"]
            ]
            admitted.append((child, scope, values))
        # Recheck all inputs before publishing any scope. Python loops aggregate data only.
        for child, scope, values in admitted:
            _current(child, scope, check_members=True)
        outputs = []
        for child, scope, values in admitted:
            _ensure_running(root)
            outputs.append(commit_scope(child, scope, values))
        result = domain.accept_verification(outputs, state["verification_before"])
        if result["route"] == "finish":
            output = domain.finish({})["output"]
            route = "finished"
        else:
            state["iteration"] += 1
            state["phase"] = "next"
            route = "decide"
            if state["iteration"] >= MAX_DECISIONS:
                domain.stop(
                    "conflicting",
                    "Issue solving reached its bounded decision limit; progress is retained.",
                    "limit-exhausted",
                )
                output = domain.finish({})["output"]
                route = "finished"
    state["domain"] = domain.dump()
    if route == "finished":
        _save(receipt, {"state": "accepted", "accepted": True, "output": output})
        state["phase"] = "finished"
        from .status_store import write_run

        write_run(
            run.repository.root,
            f".concorde/runs/{run.host.invocation_id}/native-issue.json",
            canonical(
                {"root": root, "state": state, "binding": binding, "output": output}
            ).encode(),
        )
    _save(directory / "issue-session.json", state)
    return {
        "schema_version": 1,
        "ticket": root["ticket"],
        "iteration": index,
        "route": route,
        "groups": counts,
    }
