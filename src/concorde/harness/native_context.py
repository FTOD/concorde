"""Finite native context-assessor preparation, staging and result admission.

Each command terminates. Only JSON and owned scratch cross the model interval;
no Python stack, Graph or worker executor waits for Pi. Scratch is cooperative
same-user storage, not an isolation boundary or an alternative lifecycle ledger.
"""

from __future__ import annotations

import dataclasses
import json
import os
import shlex
import sys
import tempfile
import uuid
from pathlib import Path
from types import SimpleNamespace

from ..distribution.build import load_model_instructions
from ..issues.references import validate_references
from ..issues.reporting import reporter_for_invocation
from ..spec.repository import SpecError, digest, read_file
from ..spec.typed_data import DATA_SCHEMAS, canonical, decode, typed
from ..spec.wire_shapes import type_version
from ..spec.issue_shapes import REPORT
from .admission import run_operation
from .change_worktree import read_change
from .context import (
    context_documents,
    materialize_documents,
    resolve_context,
    recheck_context,
)
from .entry import runtime_selection, validate_invocation, invocation_failure
from .host import OperationHost
from .invocation import validate_stage_identity
from .model_selection import worker_selection
from .native_evidence import _record, verify_native_single
from .native_result import MAX_PROPOSAL_BYTES, control_value
from .native_runtime import admit_native_runtime
from .worker_profile import worker_profile, validate_worker_output

OPERATION = "concorde-context-solve"
AGENT = "concorde-context-assessor"


def assessment_context(run):
    prompt = load_model_instructions(run.host.package_root, "context_assessor")
    prompt = dataclasses.replace(
        prompt,
        body=(
            run.host.package_root / "generated/native/context-assessor.md"
        ).read_text(),
    )
    agent = worker_profile("context_assessor")
    snapshot = resolve_context(
        run.repository,
        run.target.id,
        phase="context-solve",
        task=run.task["task"],
        focus_id=run.task.get("focus_id"),
        constraints=tuple(run.task.get("constraints", [])),
        instructions=prompt.body,
        agent=agent,
    )
    run.last_context = snapshot.id
    return prompt, agent, snapshot


def _response(run, value):
    return run.response(
        "completed" if value["outcome"] == "sufficient" else value["outcome"],
        value["answer"],
        blockers=value["blockers"],
    )


def _write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())


def _reporter(run, descriptor, snapshot):
    invocation = SimpleNamespace(
        context_json=canonical(
            typed(
                "concorde-agent-stage-context",
                {
                    "snapshot": typed("concorde-context-snapshot", snapshot.value),
                    "change_id": run.change_id,
                    "expected_artifacts": [],
                },
            )
        ),
        invocation_id=descriptor["ticket"],
        agent="context_assessor",
        operation=OPERATION,
        stage="context-solve",
    )
    reporter = reporter_for_invocation(
        run.repository.root,
        invocation,
        target_id=run.target.id,
        change_id=run.change_id,
    )
    receipts = Path(descriptor["directory"]) / "reports.json"
    if receipts.exists():
        reporter.receipts.extend(decode(receipts.read_text()))
    return reporter


def _proposal(run, descriptor, snapshot):
    directory = Path(descriptor["directory"])
    if (directory / "invalid").exists():
        raise SpecError("native proposal slot is invalidated", "invalid_completion")
    value = _record(directory / "proposal.json")
    if (
        set(value) != {"invocation_id", "result"}
        or value["invocation_id"] != descriptor["ticket"]
    ):
        raise SpecError("foreign native proposal", "incompatible_handoff")
    raw = read_file(directory, "proposal.json")
    if len(raw) > MAX_PROPOSAL_BYTES or raw != canonical(value).encode():
        raise SpecError(
            "native proposal bytes changed or exceed their bound", "stale_evidence"
        )
    validate_worker_output(worker_profile("context_assessor"), value["result"])
    data = value["result"]["data"]
    validate_stage_identity(data, snapshot.id)
    reporter = _reporter(run, descriptor, snapshot)
    validate_references(
        run.repository.root, data["blockers"], admitted=reporter.receipts
    )
    return value


def _execute(
    package_root: Path,
    action: str,
    payload: dict,
    descriptor_path=None,
    expected_digest=None,
):
    """Selected finite Host service. Model values cannot choose paths or actions."""
    descriptor = None
    if action != "prepare":
        descriptor = _record(Path(descriptor_path))
        if digest(descriptor) != expected_digest:
            raise SpecError("native descriptor changed", "stale_context")
        if Path(descriptor["directory"]) / "descriptor.json" != Path(descriptor_path):
            raise SpecError("foreign native descriptor", "incompatible_handoff")
        if str(package_root.resolve()) != descriptor["package_root"]:
            raise SpecError("native runtime selection changed", "workspace_mismatch")
        os.chdir(descriptor["project_root"])
        envelope = descriptor["envelope"]
    else:
        envelope = payload["invocation"]
    validate_invocation(envelope, OPERATION)
    selection = runtime_selection(package_root)
    result = {}

    def service(run):
        nonlocal descriptor
        prompt, agent, snapshot = assessment_context(run)
        if action == "prepare":
            if run.host.mode == "describe-policy":
                result.update(
                    state="described",
                    accepted=False,
                    policy={
                        "enforcement": "prompt-level",
                        "read": [
                            "context.json",
                            *context_documents(run.repository, snapshot.value),
                        ],
                        "write": [],
                        "tools": list(agent.tools),
                        "delegation": False,
                    },
                )
                return run.response(
                    "described",
                    "Native context-assessor read policy; no child was launched.",
                )
            blocked = run.assessment_dependencies(snapshot)
            if blocked is not None:
                result.update(state="not-run", accepted=False)
                return _response(run, blocked)
            if (
                not isinstance(payload.get("native_root"), str)
                or not payload["native_root"]
            ):
                raise SpecError(
                    "Select CONCORDE_NATIVE_SUBAGENTS_ROOT before native execution",
                    "missing_runtime",
                )
            runtime = admit_native_runtime(Path(payload["native_root"]))
            directory = Path(tempfile.mkdtemp(prefix="concorde-native-context-"))
            capsule = directory / "context"
            capsule.mkdir()
            materialize_documents(
                capsule, context_documents(run.repository, snapshot.value)
            )
            (capsule / "context.json").write_text(snapshot.serialized + "\n")
            ticket = str(uuid.uuid4())
            descriptor = {
                "schema_version": 1,
                "ticket": ticket,
                "directory": str(directory),
                "package_root": str(package_root.resolve()),
                "project_root": str(run.repository.root),
                "envelope": envelope,
                "configuration": run.configuration,
                "snapshot": snapshot.value,
                "prompt_digest": prompt.binding.digest,
                "registry_digest": digest(run.repository.registry_bytes),
                "change_digest": digest(read_change(run.repository.root)),
                "runtime": dataclasses.asdict(runtime),
                "session_id": payload["session_id"],
            }
            filename = directory / "descriptor.json"
            argv = [
                sys.executable,
                str(package_root / "scripts/run-operation.py"),
                "--native-context",
            ]
            child_extension = directory / "capture.ts"
            child_extension.write_text(
                "import { readFileSync } from 'node:fs';\n"
                + "import { nativeContextChild } from "
                + json.dumps(
                    str(package_root / "pi/extensions/concorde-native-child.ts")
                )
                + ";\n"
                + "export default nativeContextChild({..."
                + json.dumps(
                    {
                        "argv": argv,
                        "descriptor": str(filename),
                        "root": str(run.repository.root),
                        "reportSchema": REPORT,
                    }
                )
                + ", digest: readFileSync("
                + json.dumps(str(directory / "descriptor.digest"))
                + ", 'utf8')});\n"
            )
            chosen = worker_selection(run.configuration, "context_assessor")
            definition = {
                "description": "Assess one prepared Module's complete Spec context. Prepare with concorde-context-solve first.",
                "systemPrompt": prompt.body,
                "tools": [*agent.tools, "report_issue"],
                "extensions": [str(child_extension)],
                "allowNestedSubagents": False,
                "maxSubagentDepth": 1,
                "acceptanceRole": "read-only",
                "inheritProjectContext": False,
                "inheritGlobalContext": False,
                "inheritSkills": False,
                "defaultContext": "fresh",
                "async": False,
                "timeoutMs": (chosen.timeout_seconds or agent.timeout_seconds) * 1000,
                "systemPromptMode": "replace",
                **({"model": chosen.model} if chosen.model else {}),
                **({"thinking": chosen.thinking} if chosen.thinking else {}),
            }
            agent_file = capsule / ".pi/agents/concorde-context-assessor.md"
            agent_file.parent.mkdir(parents=True)
            fields = {"name": AGENT, **definition}
            body = fields.pop("systemPrompt")
            lines = []
            for key, value in fields.items():
                if isinstance(value, list):
                    lines.append(key + ": " + ", ".join(value))
                else:
                    lines.append(key + ": " + json.dumps(value))
            agent_file.write_text("---\n" + "\n".join(lines) + "\n---\n" + body)
            settings = capsule / ".pi/settings.json"
            settings.write_text(
                canonical({"subagents": {"projectRootResolution": "nearest"}})
            )
            descriptor["assets"] = {
                str(path.relative_to(directory)): digest(path.read_bytes())
                for path in (agent_file, child_extension, settings)
            }
            schema = {
                "type": "object",
                "properties": {
                    "invocation_id": {"const": ticket},
                    "result": {
                        "type": "object",
                        "properties": {
                            "type_id": {"const": "concorde-agent-stage-result"},
                            "schema_version": {
                                "const": type_version("concorde-agent-stage-result")
                            },
                            "data": DATA_SCHEMAS["concorde-agent-stage-result"],
                        },
                        "required": ["type_id", "schema_version", "data"],
                        "additionalProperties": False,
                    },
                },
                "required": ["invocation_id", "result"],
                "additionalProperties": False,
            }
            call = {
                "agent": AGENT,
                "task": "Assess context.json for invocation_id " + ticket,
                "cwd": str(capsule),
                "agentScope": "project",
                "context": "fresh",
                "async": False,
                "artifacts": True,
                "artifactDir": "session",
                "intercomBridge": {"mode": "off"},
                "agentContract": {"version": 1},
                "outputSchema": schema,
            }
            descriptor["launch"] = call.copy()
            _write(filename, descriptor)
            identity = digest(descriptor)
            (directory / "descriptor.digest").write_text(identity)
            command = shlex.join([*argv, "stage", str(filename), identity])
            call["gate"] = {"command": command}
            result.update(
                state="prepared",
                accepted=False,
                descriptor=str(filename),
                digest=identity,
                definition=definition,
                call=call,
                ticket=ticket,
            )
            return run.response(
                "described",
                "Prepared native assessment; model not run and result not accepted.",
            )
        assert descriptor is not None
        directory = Path(descriptor["directory"])
        if action != "invalidate" and (directory / "invalid").exists():
            raise SpecError("native invocation is invalidated", "invalid_completion")
        if (directory / "terminal.json").exists():
            raise SpecError(
                "native invocation is already terminal; prepare a fresh assessment",
                "invalid_completion",
            )
        if (
            snapshot.value != descriptor["snapshot"]
            or run.configuration != descriptor["configuration"]
            or prompt.binding.digest != descriptor["prompt_digest"]
            or digest(run.repository.registry_bytes) != descriptor["registry_digest"]
            or digest(read_change(run.repository.root)) != descriptor["change_digest"]
        ):
            raise SpecError("native assessment inputs changed", "stale_context")
        for name, expected in descriptor["assets"].items():
            if digest(read_file(directory, name)) != expected:
                raise SpecError(
                    "native Agent or capture asset changed", "stale_context"
                )
        recheck_context(run.repository, snapshot)
        capsule = directory / "context"
        if (capsule / "context.json").read_text() != snapshot.serialized + "\n":
            raise SpecError("native context index changed", "stale_context")
        for name, raw in context_documents(run.repository, snapshot.value).items():
            if read_file(capsule, name) != raw:
                raise SpecError("native context document changed", "stale_context")
        if action == "invalidate":
            (directory / "invalid").touch(exist_ok=True)
            result.update(state="invalidated", accepted=False)
        elif action == "report":
            reporter = _reporter(run, descriptor, snapshot)
            result.update(reporter(payload))
            (directory / "reports.json").write_text(canonical(reporter.receipts))
        elif action == "check":
            result.update(state="prepared", accepted=False)
        elif action == "submit":
            try:
                if len(canonical(payload).encode()) > MAX_PROPOSAL_BYTES:
                    raise SpecError(
                        "native proposal exceeds 1 MiB", "invalid_completion"
                    )
                _write(directory / "proposal.json", payload)
                _proposal(run, descriptor, snapshot)
            except BaseException:
                (directory / "invalid").touch(exist_ok=True)
                raise
            result.update(state="proposed", accepted=False)
        elif action in {"stage", "accept"}:
            proposal = _proposal(run, descriptor, snapshot)
            control = control_value(
                {
                    "schema_version": 1,
                    "ticket": descriptor["ticket"],
                    "invocation_id": descriptor["ticket"],
                    "proposal_digest": digest(proposal),
                    "state": "staged",
                    "accepted": False,
                }
            )
            if action == "stage":
                result.update(control)
            else:
                runtime = admit_native_runtime(
                    Path(descriptor["runtime"]["package_root"])
                )
                if dataclasses.asdict(runtime) != descriptor["runtime"]:
                    raise SpecError("native producer changed", "stale_evidence")
                metadata = verify_native_single(
                    payload,
                    agent=AGENT,
                    session_id=descriptor["session_id"],
                    ticket=descriptor["ticket"],
                    proposal_digest=digest(proposal),
                    gate_command=payload["gate_command"],
                    runtime=runtime,
                )
                expected_gate = shlex.join(
                    [
                        sys.executable,
                        str(package_root / "scripts/run-operation.py"),
                        "--native-context",
                        "stage",
                        str(descriptor_path),
                        expected_digest,
                    ]
                )
                if payload["gate_command"] != expected_gate:
                    raise SpecError("foreign native gate", "incompatible_handoff")
                # Exclusive receipt reservation prevents repeated effects after uncertain failure.
                _write(
                    directory / "terminal.json",
                    {"state": "finalizing", "accepted": False},
                )
                data = proposal["result"]["data"]
                run.completed.append(OPERATION)
                if data["blockers"] or data["outcome"] == "sufficient":
                    run.record_gaps("context-solve", data["blockers"])
                from .status_store import write_run

                evidence = {
                    "descriptor": descriptor,
                    "proposal": proposal,
                    "native": metadata,
                    "correlation": payload,
                    "accepted": True,
                }
                write_run(
                    run.host.archive_root,
                    f".concorde/runs/{run.host.invocation_id}/native-context.json",
                    canonical(evidence).encode(),
                )
                result.update(state="accepted", accepted=True)
                output = _response(run, data)
                (directory / "terminal.json").write_text(
                    canonical({"state": "accepted", "output": output})
                )
                return output
        else:
            raise SpecError("unknown native context action", "invalid_input")
        return run.response(
            "described", "Native proposal transport; not accepted completion."
        )

    host = OperationHost(
        Path.cwd(),
        package_root,
        mode=envelope["mode"],
        native_assessment=service,
        session_provenance=selection,
    )
    envelope_result = run_operation(
        OPERATION, envelope["configuration"], envelope["input"], host_context=host
    )
    if envelope_result["errors"]:
        return {"state": "rejected", "accepted": False, "result": envelope_result}
    return {**result, "result": envelope_result}


def execute(
    package_root: Path,
    action: str,
    payload: dict,
    descriptor_path=None,
    expected_digest=None,
):
    if action == "prepare":
        return _execute(package_root, action, payload)
    # One finite command at a time per owned slot. This is not a model scheduler.
    import fcntl

    descriptor = _record(Path(descriptor_path))
    if digest(descriptor) != expected_digest:
        raise SpecError("native descriptor changed", "stale_context")
    with (Path(descriptor["directory"]) / "command.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _execute(package_root, action, payload, descriptor_path, expected_digest)


def main(package_root, args):
    try:
        raw = sys.stdin.buffer.read(MAX_PROPOSAL_BYTES + 1)
        if len(raw) > MAX_PROPOSAL_BYTES:
            raise SpecError("native input exceeds 1 MiB", "invalid_input")
        payload = decode(raw.decode()) if raw else {}
        action = args[0]
        value = execute(package_root, action, payload, *args[1:])
        if action == "stage" and value.get("state") == "staged":
            value.pop("result")
        print(canonical(value))
        return 3 if value.get("state") == "rejected" else 0
    except Exception as error:
        print(
            canonical(
                {
                    "state": "rejected",
                    "accepted": False,
                    "result": invocation_failure(OPERATION, error),
                }
            )
        )
        return 3
