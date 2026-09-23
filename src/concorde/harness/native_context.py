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
from ..spec.boundaries import scope_roots
from ..spec.issue_shapes import REPORT
from ..spec.repository import SpecError, digest, read_file
from ..spec.typed_data import DATA_SCHEMAS, canonical, decode, typed
from ..spec.wire_shapes import type_version
from .admission import run_operation
from .change_worktree import read_change, workspace_context
from .context import (
    ContextSnapshot,
    context_documents,
    materialize_documents,
    materialize_references,
    recheck_context,
    resolve_context,
)
from .entry import invocation_failure, runtime_selection, validate_invocation
from .execution_error import (
    ExecutionFailure,
    exception_feedback,
    failure,
    native_feedback,
)
from .host import OperationHost
from .invocation import validate_stage_identity
from .model_selection import worker_selection
from .native_evidence import _record, verify_native_single
from .native_result import MAX_PROPOSAL_BYTES, control_value
from .native_runtime import admit_native_runtime
from .worker_profile import validate_worker_output, worker_profile

OPERATION = "concorde-context-solve"
AGENT = "concorde-context-assessor"


def native_output_schema(result_type: str, ticket: str | None = None) -> dict:
    """Self-contained native proposal schema shared by direct and Issue workflow slots.

    The two native result payload schemas are reference-free. Embed the payload itself,
    not json_schema's separately rooted TypedValue document underneath ``result``.
    The producer may then safely wrap this entire document underneath ``value``.
    """
    if result_type not in {
        "concorde-agent-stage-result",
        "concorde-review-stage-result",
    }:
        raise ValueError("unsupported native result type")
    from copy import deepcopy

    return {
        "type": "object",
        "properties": {
            "invocation_id": {"const": ticket}
            if ticket is not None
            else {"type": "string"},
            "result": {
                "type": "object",
                "properties": {
                    "type_id": {"const": result_type},
                    "schema_version": {"const": type_version(result_type)},
                    "data": deepcopy(DATA_SCHEMAS[result_type]),
                },
                "required": ["type_id", "schema_version", "data"],
                "additionalProperties": False,
            },
        },
        "required": ["invocation_id", "result"],
        "additionalProperties": False,
    }


def candidate_input_digest(root):
    value = read_change(root)
    return digest(
        {k: v for k, v in value.items() if k not in {"runs", "revision"}}
        if value
        else None
    )


def assessment_context(run, phase="context-solve", inputs=()):
    role = {
        "context-solve": "context_assessor",
        "plan": "planner",
        "tasks": "task_author",
        "implementation": "programmer",
        "issue-solve": "issue_solver",
        "spec-review": "spec_reviewer",
        "code-review": "code_reviewer",
    }[phase]
    prompt = load_model_instructions(run.host.package_root, role)
    prompt = dataclasses.replace(
        prompt,
        body=(
            run.host.package_root
            / ("generated/native/" + role.replace("_", "-") + ".md")
        ).read_text(),
    )
    agent = worker_profile(role)
    snapshot = resolve_context(
        run.repository,
        run.target.id,
        phase=phase,
        task=run.task["task"],
        focus_id=run.task.get("focus_id"),
        constraints=tuple(run.task.get("constraints", [])),
        instructions=prompt.body,
        agent=agent,
        stage_inputs=inputs,
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
                "concorde-review-stage-context"
                if descriptor["phase"].endswith("-review")
                else "concorde-agent-stage-context",
                {
                    "snapshot": typed("concorde-context-snapshot", snapshot.value),
                    **(
                        {
                            "review": typed(
                                "concorde-review-input", descriptor["review_input"]
                            )
                        }
                        if descriptor["phase"].endswith("-review")
                        else {"change_id": run.change_id, "expected_artifacts": []}
                    ),
                },
            )
        ),
        invocation_id=descriptor["ticket"],
        agent=descriptor["role"],
        operation=descriptor["worker_operation"],
        stage=descriptor["phase"],
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


def _remember_failure(directory, feedback, name="failure.json"):
    # First failure remains causal even when a later gate merely sees an invalid slot.
    path = directory / name
    if not path.exists():
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(canonical(feedback))
            stream.flush()
            os.fsync(stream.fileno())


def _slot_failure(directory, *, missing=False):
    paths = (
        [directory / "failure.json"] if (directory / "failure.json").exists() else []
    )
    paths.extend(sorted(directory.glob("submission-error-*.json")))
    return ExecutionFailure(
        failure(
            "native child submitted no captured result"
            if missing
            else "native invocation is invalidated; fresh admission required",
            code="invalid_completion",
            layer="native-slot",
            category="no-submission" if missing and not paths else "host-refusal",
            causes=[_record(path) for path in paths],
            references=[str(path) for path in paths],
        )
    )


def _proposal(run, descriptor, snapshot):
    directory = Path(descriptor["directory"])
    if (directory / "invalid").exists():
        raise _slot_failure(directory)
    if not (directory / "proposal.json").exists():
        raise _slot_failure(directory, missing=True)
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
    validate_worker_output(worker_profile(descriptor["role"]), value["result"])
    data = value["result"]["data"]
    if descriptor["phase"].endswith("-review"):
        from ..review.review import _validate

        _validate(run, snapshot, descriptor["review_input"], data)
    else:
        validate_stage_identity(data, snapshot.id)
    reporter = _reporter(run, descriptor, snapshot)
    validate_references(
        run.repository.root,
        data.get("blockers", data.get("issues", [])),
        admitted=[*reporter.receipts, *reporter.admitted_receipts],
    )
    if data.get("outcome") in {"completed", "sufficient"}:
        if descriptor["phase"] == "plan" and not data["plan"].strip():
            raise SpecError("planning produced no usable plan", "invalid_completion")
        if descriptor["phase"] == "implementation":
            from ..implementation.implement import (
                prepare_implementation,
                validate_implementation,
            )

            validate_implementation(
                run,
                data,
                prepare_implementation(
                    run, admitted_inputs=descriptor["snapshot"]["stage_inputs"]
                )[1],
            )
        if descriptor["phase"] == "tasks":
            from ..planning.tasks import prepare_tasks, validate_tasks

            validate_tasks(run, data, prepare_tasks(run)[2])
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
    if action not in {
        "prepare",
        "prepare-planner",
        "prepare-review-item",
        "prepare-issue-item",
    }:
        descriptor = _record(Path(descriptor_path))
        if digest(Path(descriptor_path).read_bytes()) != expected_digest:
            raise SpecError("native descriptor changed", "stale_context")
        if Path(descriptor["directory"]) / "descriptor.json" != Path(descriptor_path):
            raise SpecError("foreign native descriptor", "incompatible_handoff")
        if str(package_root.resolve()) != descriptor["package_root"]:
            raise SpecError("native runtime selection changed", "workspace_mismatch")
        os.chdir(descriptor["project_root"])
        envelope = descriptor["envelope"]
    else:
        envelope = payload["invocation"]
    operation = envelope["operation_id"]
    if operation not in {
        OPERATION,
        "concorde-plan",
        "concorde-tasks",
        "concorde-implement",
        "concorde-spec-review",
        "concorde-code-review",
        "concorde-issues",
    }:
        raise SpecError("not a native read-only planning entry", "unknown_operation")
    validate_invocation(envelope, operation)
    selection = runtime_selection(package_root)
    result = {}

    def service(run):
        nonlocal descriptor
        if operation == "concorde-issues" and action == "prepare":
            from .native_issues import prepare_root

            prepared = prepare_root(run, payload)
            result.update(
                {key: value for key, value in prepared.items() if key != "output"}
            )
            return prepared["output"]
        if (
            operation in {"concorde-spec-review", "concorde-code-review"}
            and action == "prepare"
        ):
            from .native_reviews import prepare_scope

            prepared = prepare_scope(run, payload)
            result.update(
                {key: value for key, value in prepared.items() if key != "output"}
            )
            return prepared["output"]
        phase = (
            descriptor["phase"]
            if descriptor
            else (
                "plan"
                if action == "prepare-planner"
                else "tasks"
                if operation == "concorde-tasks"
                else "implementation"
                if operation == "concorde-implement"
                else operation.removeprefix("concorde-")
                if operation.endswith("-review")
                else "issue-solve"
                if operation == "concorde-issues"
                else "context-solve"
            )
        )
        from ..planning.tasks import prepare_tasks
        from ..review.review import require_spec_review
        from .change_worktree import progress

        inputs = (
            tuple([payload["issue_selection"]])
            if phase == "issue-solve" and not descriptor
            else tuple(descriptor["snapshot"]["stage_inputs"])
            if phase == "issue-solve"
            else ()
        )
        implementation = None
        if phase == "implementation":
            from ..implementation.implement import (
                persist_implementation,
                prepare_implementation,
            )

            implementation = prepare_implementation(
                run,
                admitted_inputs=descriptor["snapshot"]["stage_inputs"]
                if descriptor
                else None,
            )
            work, local, revisions, inputs, stopped = implementation
            if stopped:
                result.update(state="not-run", accepted=False)
                return stopped
            if not local and action == "prepare" and run.host.mode == "execute":
                result.update(state="not-run", accepted=True)
                return persist_implementation(
                    run,
                    {
                        "tasks": [],
                        "answer": "Separately completed components are current; checks/reviews remain separate.",
                    },
                    work,
                    local,
                    revisions,
                )
        if operation not in {OPERATION, "concorde-issues"} and not phase.endswith(
            "-review"
        ):
            require_spec_review(run)
            if phase == "tasks":
                inputs = prepare_tasks(run)[1]
            if phase in {"tasks", "implementation"}:
                reviews = [
                    v for v in inputs if v["type_id"] == "concorde-review-result"
                ]
                if reviews and not any(
                    value["type_id"] == "concorde-issue-context" for value in inputs
                ):
                    from ..issues.references import observation_context

                    inputs = (
                        *inputs,
                        observation_context(
                            run.repository.root, reviews[0]["data"]["issues"]
                        ),
                    )
            if (
                action
                in {
                    "prepare",
                    "prepare-planner",
                    "prepare-review-item",
                    "prepare-issue-item",
                }
                and run.host.mode == "execute"
                and not run.host.coordinated
            ):
                progress(
                    run.repository.root,
                    phase=phase if phase in {"tasks", "implementation"} else "plan",
                    status="active",
                    invalidate=True,
                )
        prompt, agent, snapshot = assessment_context(run, phase, inputs)
        info = None
        if phase.endswith("-review"):
            from ..review.review import inputs as review_inputs

            info, prompt = review_inputs(run, phase.split("-")[0])
            prompt = dataclasses.replace(
                prompt,
                body=(
                    run.host.package_root
                    / ("generated/native/" + agent.name.replace("_", "-") + ".md")
                ).read_text(),
            )
            snapshot = resolve_context(
                run.repository,
                run.target.id,
                phase=phase,
                task=run.task["task"],
                focus_id=run.task.get("focus_id"),
                constraints=tuple(run.task.get("constraints", [])),
                instructions=prompt.body,
                agent=agent,
            )
            run.last_context = snapshot.id
        if descriptor and phase == "implementation":
            snapshot = ContextSnapshot(canonical(descriptor["snapshot"]))
            run.last_context = snapshot.id
        if action in {
            "prepare",
            "prepare-planner",
            "prepare-review-item",
            "prepare-issue-item",
        }:
            if run.host.mode == "describe-policy":
                result.update(
                    state="described",
                    accepted=False,
                    policy={
                        "enforcement": "prompt-level",
                        "role": agent.name,
                        "read": [
                            "context.json",
                            *context_documents(run.repository, snapshot.value),
                            *(
                                [
                                    record["path"]
                                    for record in snapshot.value["external_references"]
                                ]
                                if "references" in agent.contract.effects.reads
                                else []
                            ),
                        ],
                        "write": list(
                            scope_roots(run.repository.implementation_scope(run.target))
                        )
                        if phase == "implementation"
                        else [],
                        "tools": list(agent.tools),
                        "delegation": False,
                    },
                )
                return run.response(
                    "described",
                    f"Native {agent.name} intended read policy; no child was launched.",
                )
            blocked = (
                run.assessment_dependencies(snapshot)
                if phase == "context-solve"
                else None
            )
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
            if operation not in {OPERATION, "concorde-issues"} and not phase.endswith(
                "-review"
            ):
                pending = run.pending_gaps(phase, snapshot)
                if pending:
                    result.update(state="not-run", accepted=False)
                    return run.response(
                        "spec_incomplete",
                        "Repair the recorded necessary contracts before resuming this step.",
                        blockers=pending,
                    )
            runtime = admit_native_runtime(Path(payload["native_root"]))
            directory = (
                Path(payload["slot_directory"])
                if payload.get("slot_directory")
                and action in {"prepare-issue-item", "prepare-review-item"}
                else Path(tempfile.mkdtemp(prefix="concorde-native-context-"))
            )
            if not directory.exists():
                directory.mkdir(parents=True)
            capsule = directory / "context"
            capsule.mkdir()
            materialize_documents(
                capsule, context_documents(run.repository, snapshot.value)
            )
            if "references" in agent.contract.effects.reads:
                materialize_references(
                    run.repository, capsule, snapshot.value["external_references"]
                )
            if phase == "code-review":
                materialize_documents(
                    capsule,
                    {
                        item["path"]: read_file(run.repository.root, item["path"])
                        for item in snapshot.value["implementation_artifacts"]
                    },
                )
            index = snapshot.serialized + "\n"
            if info is not None:
                index = (
                    canonical(
                        {
                            "snapshot": typed(
                                "concorde-context-snapshot", snapshot.value
                            ),
                            "review": typed("concorde-review-input", info),
                        }
                    )
                    + "\n"
                )
            if phase == "implementation":
                index = (
                    canonical(
                        {
                            **snapshot.value,
                            "native_workspace": str(run.repository.root),
                            "intended_write_paths": [
                                str(run.repository.root / p)
                                for p in scope_roots(
                                    run.repository.implementation_scope(run.target)
                                )
                            ],
                            "file_scope_enforcement": "prompt-level",
                            "network_and_credentials": "model policy, not OS confinement",
                        }
                    )
                    + "\n"
                )
            (capsule / "context.json").write_text(index)
            ticket = (
                payload.get("slot_ticket")
                if payload.get("slot_directory")
                else str(uuid.uuid4())
            )
            descriptor = {
                "schema_version": 1,
                "gate_command": payload.get("gate_command"),
                "operation": operation,
                "worker_operation": "concorde-context-solve"
                if phase == "context-solve"
                else operation,
                "phase": phase,
                "role": agent.name,
                "agent": "concorde-" + agent.name.replace("_", "-"),
                "native_session_id": payload.get(
                    "native_session_id", payload["session_id"]
                ),
                "ticket": ticket,
                "directory": str(directory),
                "package_root": str(package_root.resolve()),
                "python": sys.executable,
                "project_root": str(run.repository.root),
                "envelope": envelope,
                "configuration": run.configuration,
                "snapshot": snapshot.value,
                "index": index,
                "review_input": info,
                "result_type": "concorde-review-stage-result"
                if info is not None
                else "concorde-agent-stage-result",
                "delivered": {
                    str(p.relative_to(capsule)): digest(p.read_bytes())
                    for p in capsule.rglob("*")
                    if p.is_file()
                },
                "prompt_digest": prompt.binding.digest,
                "registry_digest": digest(run.repository.registry_bytes),
                "change_digest": candidate_input_digest(run.repository.root),
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
                        "checks": "run_checks" in agent.tools,
                        "checksTimeoutMs": 10000
                        + 1000
                        * sum(
                            run.repository.checks[key]["timeout_seconds"]
                            for key in run.target.checks
                        ),
                    }
                )
                + ", digest: readFileSync("
                + json.dumps(str(directory / "descriptor.digest"))
                + ", 'utf8')});\n"
            )
            chosen = worker_selection(run.configuration, agent.name)
            definition = {
                "description": "Prepared native "
                + agent.name
                + "; use only its issued invocation.",
                "systemPrompt": prompt.body,
                "tools": [
                    *[t for t in agent.tools if phase != "code-review" or t != "bash"],
                    "report_issue",
                ],
                "extensions": [str(child_extension)],
                "allowNestedSubagents": False,
                "maxSubagentDepth": 1,
                "acceptanceRole": "writer"
                if phase == "implementation"
                else "read-only",
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
            agent_file = capsule / (".pi/agents/" + descriptor["agent"] + ".md")
            agent_file.parent.mkdir(parents=True)
            fields = {"name": descriptor["agent"], **definition}
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
            schema = native_output_schema(descriptor["result_type"], ticket)
            call = {
                "agent": descriptor["agent"],
                "task": "Assess context.json for invocation_id " + ticket,
                "cwd": str(capsule),
                "agentScope": "project",
                "context": "fresh",
                "async": False,
                "mission": False,
                "artifacts": True,
                "artifactDir": "session",
                "intercomBridge": {"mode": "off"},
                "agentContract": {"version": 1},
                "outputSchema": schema,
            }
            if payload.get("slot_directory") and payload.get("native_call"):
                call = dict(payload["native_call"])
                if call["agent"] != descriptor["agent"] or call["cwd"] != str(capsule):
                    raise SpecError(
                        "foreign native Issue call layout", "incompatible_handoff"
                    )
            descriptor["launch"] = {k: v for k, v in call.items() if k != "gate"}
            _write(filename, descriptor)
            identity = digest(descriptor)
            (directory / "descriptor.digest").write_text(identity)
            command = descriptor.get("gate_command") or shlex.join(
                [*argv, "stage", str(filename), identity]
            )
            call["gate"] = {"command": command}
            result.update(
                state="prepared",
                accepted=False,
                descriptor=str(filename),
                digest=identity,
                definition=definition,
                call=call,
                ticket=ticket,
                binding={
                    "argv": argv,
                    "root": str(run.repository.root),
                    "descriptor": str(filename),
                    "digest": identity,
                },
            )
            return run.response(
                "described",
                "Prepared native assessment; model not run and result not accepted.",
            )
        assert descriptor is not None
        directory = Path(descriptor["directory"])
        if (
            action not in {"invalidate", "observe-error"}
            and (directory / "invalid").exists()
        ):
            raise _slot_failure(directory)
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
            or candidate_input_digest(run.repository.root)
            != descriptor["change_digest"]
        ):
            raise SpecError("native assessment inputs changed", "stale_context")
        for name, expected in descriptor["assets"].items():
            if digest(read_file(directory, name)) != expected:
                raise SpecError(
                    "native Agent or capture asset changed", "stale_context"
                )
        if info is not None and info != descriptor["review_input"]:
            raise SpecError("review input identity changed", "stale_context")
        recheck_context(
            run.repository, snapshot, check_implementation=phase != "implementation"
        )
        capsule = directory / "context"
        if (capsule / "context.json").read_text() != descriptor.get(
            "index", snapshot.serialized + "\n"
        ):
            raise SpecError("native context index changed", "stale_context")
        for name, expected in descriptor.get("delivered", {}).items():
            if digest(read_file(capsule, name)) != expected:
                raise SpecError("delivered native inputs changed", "stale_context")
        for name, raw in context_documents(run.repository, snapshot.value).items():
            if read_file(capsule, name) != raw:
                raise SpecError("native context document changed", "stale_context")
        if phase == "issue-solve":
            from ..issues.store import read_issue

            selected = descriptor["snapshot"]["stage_inputs"][0]["data"]
            if (
                read_issue(run.repository.root, selected["issue_id"])[1]
                != selected["revision"]
            ):
                raise SpecError("Issue changed during native decision", "stale_issue")
        if action in {"accept", "admit-review"}:
            rows = payload.get("details", {}).get("results", [])
            if len(rows) == 1 and (
                rows[0].get("interrupted")
                or rows[0].get("stopped")
                or rows[0].get("exitCode") != 0
            ):
                from .worker_executor import OperationExecutionError

                error = OperationExecutionError(
                    "native worker did not complete",
                    outcome="limit_exhausted"
                    if rows[0].get("timedOut")
                    else "cancelled"
                    if rows[0].get("interrupted") or rows[0].get("stopped")
                    else "failed",
                )
                error.feedback = native_feedback(rows[0], attempt=descriptor["ticket"])
                error.feedback["causes"].extend(
                    _slot_failure(directory).feedback["causes"]
                )
                raise error
        if action == "observe-error":
            # Observation is not acceptance and does not invalidate a correctable SDK rejection.
            observed = payload.get("feedback", {})
            feedback = failure(
                observed.get(
                    "message", "Native structured submission failed before capture"
                ),
                layer="structured-output",
                category=observed.get("category", "unknown"),
                attempt=observed.get("attempt") or descriptor["ticket"],
                diagnostics=observed.get("diagnostics", {}).get("text"),
            )
            _remember_failure(
                directory,
                feedback,
                "submission-error-" + digest(feedback)[7:] + ".json",
            )
            result.update(state="observed", accepted=False)
        elif action == "invalidate":
            if payload.get("reason"):
                _remember_failure(
                    directory,
                    failure(
                        payload["reason"],
                        layer="proposal",
                        category="capture-failure",
                        attempt=descriptor["ticket"],
                    ),
                )
            (directory / "invalid").touch(exist_ok=True)
            result.update(state="invalidated", accepted=False)
        elif action == "report":
            reporter = _reporter(run, descriptor, snapshot)
            result.update(reporter(payload))
            (directory / "reports.json").write_text(canonical(reporter.receipts))
        elif action == "checks":
            if "run_checks" not in agent.tools:
                raise SpecError(
                    "this role has no configured check service", "permission_denied"
                )
            from .checks import check_service

            result.update(
                check_service(run.repository, run.target, descriptor["ticket"])()
            )
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
            except BaseException as error:
                try:
                    _remember_failure(
                        directory,
                        exception_feedback(
                            error, layer="host-submit", attempt=descriptor["ticket"]
                        ),
                    )
                except (OSError, ValueError) as observation_error:
                    error.feedback = failure(
                        "Native submission failed and its diagnostic could not be retained",
                        layer="host-submit",
                        attempt=descriptor["ticket"],
                        causes=[
                            exception_feedback(error),
                            exception_feedback(
                                observation_error, layer="failure-observation"
                            ),
                        ],
                    )
                    error.feedback["diagnostics"]["complete"] = False
                (directory / "invalid").touch(exist_ok=True)
                raise
            result.update(state="proposed", accepted=False)
        elif action in {"stage", "accept", "admit-review"}:
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
                    agent=descriptor["agent"],
                    session_id=descriptor["session_id"],
                    ticket=descriptor["ticket"],
                    proposal_digest=digest(proposal),
                    gate_command=payload["gate_command"],
                    runtime=runtime,
                )
                expected_gate = descriptor.get("gate_command") or shlex.join(
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
                if action == "admit-review":
                    result.update(
                        state="admitted",
                        accepted=False,
                        proposal=proposal,
                        native=metadata,
                    )
                    return run.response(
                        "described",
                        "Review proposal independently admitted for aggregate acceptance.",
                    )
                # Exclusive receipt reservation prevents repeated effects after uncertain failure.
                _write(
                    directory / "terminal.json",
                    {"state": "finalizing", "accepted": False},
                )
                data = proposal["result"]["data"]
                run.completed.append(descriptor["worker_operation"])
                output = _response(run, data)
                if data["outcome"] in {"completed", "sufficient"}:
                    if phase == "plan":
                        from ..planning.plan import persist_plan_result

                        run.completed.insert(0, "concorde-context-solve")
                        output = persist_plan_result(run, data)
                    elif phase == "implementation":
                        from ..implementation.implement import persist_implementation

                        state, local, revisions, _, _ = implementation
                        output = persist_implementation(
                            run, data, state, local, revisions
                        )
                    elif phase == "tasks":
                        from ..planning.tasks import persist_tasks

                        state, _, _, repair, scope = prepare_tasks(run)
                        output = persist_tasks(run, data, state, repair, scope)
                    else:
                        run.record_gaps(phase, [])
                elif data["blockers"]:
                    run.record_gaps(phase, data["blockers"])
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
                result.update(state="accepted", accepted=True, outcome=data["outcome"])
                (directory / "terminal.json").write_text(
                    canonical(
                        {
                            "state": "accepted",
                            "outcome": data["outcome"],
                            "output": output,
                            "change_digest": candidate_input_digest(
                                run.repository.root
                            ),
                            "workspace": workspace_context(
                                run.repository.root,
                                target_id=run.target.id,
                                task=run.task["task"],
                            ),
                        }
                    )
                )
                return output
        else:
            raise SpecError("unknown native context action", "invalid_input")
        return run.response(
            "described", "Native proposal transport; not accepted completion."
        )

    def relay(host, op, invocation, candidate):
        from .native_planning import relay_prepare

        relayed = relay_prepare(host, invocation, candidate, payload)
        result.update({k: v for k, v in relayed.items() if k != "result"})
        return relayed["result"], ""

    host = OperationHost(
        Path.cwd(),
        package_root,
        mode=envelope["mode"],
        native_assessment=service,
        native_transport=action != "accept",
        relay=relay,
        session_provenance=selection,
    )
    envelope_result = run_operation(
        operation, envelope["configuration"], envelope["input"], host_context=host
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
    if action == "prepare-planner":
        prior = _record(Path(descriptor_path))
        terminal = _record(Path(prior["directory"]) / "terminal.json")
        if (
            digest(Path(descriptor_path).read_bytes()) != expected_digest
            or prior["operation"] != "concorde-plan"
            or prior["phase"] != "context-solve"
            or terminal.get("outcome") != "sufficient"
        ):
            raise SpecError(
                "planner requires accepted sufficient assessment", "invalid_completion"
            )
        os.chdir(prior["project_root"])
        from ..spec.repository import SpecRepository
        from .context import ContextSnapshot

        # Assessment may resolve a recorded prerequisite. Recheck the assessed
        # contracts against its Host-recorded post-acceptance lifecycle, not the
        # pre-effect lifecycle that the assessor originally received.
        continuation = dict(prior["snapshot"])
        continuation["workspace"] = terminal["workspace"]
        continuation.pop("context_id")
        continuation["context_id"] = digest(continuation)
        repository = SpecRepository(Path.cwd(), package_root)
        recheck_context(repository, ContextSnapshot(canonical(continuation)))
        from .configuration import load_configuration

        if (
            load_configuration(Path.cwd()) != prior["configuration"]
            or digest(repository.registry_bytes) != prior["registry_digest"]
            or load_model_instructions(package_root, "context_assessor").binding.digest
            != prior["prompt_digest"]
        ):
            raise SpecError("assessed inputs changed before planning", "stale_context")
        if candidate_input_digest(Path.cwd()) != terminal["change_digest"]:
            raise SpecError(
                "candidate changed after assessment acceptance", "stale_context"
            )
        return _execute(
            package_root,
            action,
            {
                "invocation": prior["envelope"],
                "native_root": prior["runtime"]["package_root"],
                "session_id": prior["session_id"],
                "native_session_id": prior["native_session_id"],
            },
        )
    if action in {"prepare", "prepare-review-item", "prepare-issue-item"}:
        return _execute(package_root, action, payload)
    # One finite command at a time per owned slot. This is not a model scheduler.
    import fcntl

    descriptor = _record(Path(descriptor_path))
    if digest(Path(descriptor_path).read_bytes()) != expected_digest:
        raise SpecError("native descriptor changed", "stale_context")
    with (Path(descriptor["directory"]) / "command.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _execute(package_root, action, payload, descriptor_path, expected_digest)


def main(package_root, args):
    operation = None
    try:
        raw = sys.stdin.buffer.read(MAX_PROPOSAL_BYTES + 1)
        if len(raw) > MAX_PROPOSAL_BYTES:
            raise SpecError("native input exceeds 1 MiB", "invalid_input")
        payload = decode(raw.decode()) if raw else {}
        action = args[0]
        operation = (
            payload.get("invocation", {}).get("operation_id")
            if action in {"prepare", "prepare-review-item", "prepare-issue-item"}
            else _record(Path(args[1])).get("operation")
        )
        if action == "issue-gate":
            from .native_issues import stage_slot

            value = stage_slot(package_root, *args[1:])
        elif action.startswith("workflow-"):
            if operation == "concorde-issues":
                from .native_issues import workflow_service
            elif operation in {"concorde-spec-review", "concorde-code-review"}:
                from .native_reviews import workflow_service
            else:
                from .native_planning import workflow_service
            value = workflow_service(package_root, action, *args[1:])
        else:
            value = execute(package_root, action, payload, *args[1:])
        if action in {"stage", "issue-gate"} and value.get("state") == "staged":
            value.pop("result")
        print(canonical(value))
        return 3 if value.get("state") == "rejected" else 0
    except Exception as error:
        print(
            canonical(
                {
                    "state": "rejected",
                    "accepted": False,
                    "result": invocation_failure(operation, error),
                }
            )
        )
        return 3
