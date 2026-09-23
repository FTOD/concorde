"""The native driver: preparation, the result gate and workflow services of every Agent call.

Every native action is one finite Host command; only JSON and owned scratch cross a model run, and
no Python stack waits for Pi. The driver holds the shared path (admission re-entry, capsule
assembly through Task context, the result gate's actions, native evidence, coverage, the terminal
reservation and archiving) and reaches providers only through hook entry points: an Agent hook
named by an Agent definition's ``hook`` and a workflow hook named by a capability declaration's
entry point. It imports no provider. Scratch is cooperative same-user storage, not an isolation
boundary.
"""

from __future__ import annotations

import dataclasses
import importlib
import json
import os
import shlex
import shutil
import sys
import tempfile
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Protocol

from ..spec.repository import SpecError, SpecRepository, digest, read_file
from ..spec.typed_data import canonical, data_schema, decode, type_version, typed
from .capsule import assemble_capsule, delivered_documents, verify_capsule
from .change_worktree import read_change, workspace_context
from .checks import check_command
from .context import ContextSnapshot, recheck_context, resolve_context
from .entry import invocation_failure, validate_invocation
from .execution_error import (
    ExecutionFailure,
    OperationExecutionError,
    exception_feedback,
    failure,
    native_feedback,
    response_failure,
    safe_text,
    workflow_feedback,
)
from .host import AdmittedRequest, OperationHost
from .invocation import Invocation, bind
from .model_selection import worker_selection
from .native_evidence import (
    NativeChildEvidence,
    _record,
    verify_native_children,
    verify_native_single,
)
from .native_result import MAX_PROPOSAL_BYTES, control_value
from .native_runtime import admit_native_runtime
from .worker_profile import (
    AgentDefinition,
    agent_definition,
    bind_agent,
    load_instructions,
    validate_agent_result,
)

PREPARE = "prepare"
PREPARE_SLOT = "prepare-slot"
RESULT_TYPES = ("concorde-agent-stage-result", "concorde-review-stage-result")
# The actions that re-admit the stored invocation of one call and take its command lock.
CALL_ACTIONS = frozenset(
    {
        "check",
        "submit",
        "invalidate",
        "observe-error",
        "report",
        "checks",
        "stage",
        "accept",
        "admit",
    }
)


# --- hook interfaces ------------------------------------------------------------------------


@dataclass(frozen=True)
class StagePlan:
    """What an Agent hook contributes to one call."""

    stage_inputs: tuple[dict, ...] = ()
    review_input: dict | None = None
    instructions: str | None = None
    stop: dict | None = None
    stop_accepted: bool = False
    bind_admitted_snapshot: bool = False


class AgentHook(Protocol):
    def prepare(
        self, run: Invocation, admitted: tuple[dict, ...] | None
    ) -> StagePlan: ...

    def recheck(self, run: Invocation, descriptor: dict) -> None: ...

    def validate(
        self, run: Invocation, snapshot: ContextSnapshot, plan: StagePlan, data: dict
    ) -> None: ...

    def accept(
        self, run: Invocation, snapshot: ContextSnapshot, plan: StagePlan, data: dict
    ) -> dict: ...


@dataclass(frozen=True)
class WorkflowPlan:
    """What a workflow hook contributes to one Workflow."""

    script: str
    host: str
    steps: tuple[str, ...]
    expansion: dict
    helpers: tuple[str, ...] = ()
    stop: dict | None = None
    stop_accepted: bool = False


def stop_plan(response: dict, *, accepted: bool = False) -> WorkflowPlan:
    """A workflow plan that ends preparation with ``response``; no Workflow runs."""
    return WorkflowPlan("", "", (), {}, stop=response, stop_accepted=accepted)


class WorkflowDriver(Protocol):
    def issue_slot(
        self, key: str, agent: str, task: dict, *, stage_inputs: tuple[dict, ...] = ()
    ) -> dict: ...

    def check(self, key: str) -> None: ...

    def coverage(self, keys: Sequence[str]) -> None: ...

    def admit(self, key: str) -> dict: ...

    def accept(self, key: str) -> dict: ...

    def receipt(self, value: dict) -> None: ...

    def stopped(self) -> bool: ...


class WorkflowHook(Protocol):
    def prepare(self, run: Invocation, driver: WorkflowDriver) -> WorkflowPlan: ...

    def step(self, run: Invocation, driver: WorkflowDriver, name: str) -> dict: ...

    def on_failure(
        self, run: Invocation, driver: WorkflowDriver, native_state: str
    ) -> dict | None: ...


AGENT_HOOK_METHODS = ("prepare", "recheck", "validate", "accept")
WORKFLOW_HOOK_METHODS = ("prepare", "step", "on_failure")


def resolve_hook(reference: str, methods: tuple[str, ...]):
    """The hook a ``module:attribute`` entry point names, or ``invalid_agent_binding``."""
    module_name, separator, attribute = reference.partition(":")
    try:
        if not separator or not module_name or not attribute:
            raise ValueError("not module:attribute")
        value = getattr(importlib.import_module(module_name), attribute)
    except (ImportError, AttributeError, ValueError) as error:
        raise SpecError(
            f"hook {reference!r} does not resolve: {error}", "invalid_agent_binding"
        ) from error
    if not all(callable(getattr(value, name, None)) for name in methods):
        raise SpecError(
            f"hook {reference!r} lacks the methods {', '.join(methods)}",
            "invalid_agent_binding",
        )
    return value


# --- shared helpers -------------------------------------------------------------------------


def native_output_schema(result_type: str, ticket: str | None = None) -> dict:
    """The self-contained proposal schema: ``invocation_id`` and the embedded result type."""
    if result_type not in RESULT_TYPES:
        raise ValueError("unsupported native result type")
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
                    "data": data_schema(result_type),
                },
                "required": ["type_id", "schema_version", "data"],
                "additionalProperties": False,
            },
        },
        "required": ["invocation_id", "result"],
        "additionalProperties": False,
    }


def candidate_input_digest(root) -> str:
    """The digest of the change status, apart from its run list and revision."""
    value = read_change(root)
    return digest(
        {k: v for k, v in value.items() if k not in {"runs", "revision"}}
        if value
        else None
    )


def quote(value: str) -> str:
    """POSIX single-quote one argument, exactly as the workflow registrar does."""
    return "'" + value.replace("'", "'\\''") + "'"


def command_text(argv: Sequence[str]) -> str:
    return " ".join(quote(item) for item in argv)


def _write(path: Path, value) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())


def _save(path: Path, value) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(canonical(value))
    os.replace(temporary, path)


def _remember_failure(directory, feedback, name="failure.json"):
    # The first failure stays causal even when a later gate merely sees an invalid slot.
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


def _descriptor(path, expected) -> dict:
    value = _record(Path(path))
    if digest(Path(path).read_bytes()) != expected:
        raise SpecError("native descriptor changed", "stale_context")
    if Path(value["directory"]) / "descriptor.json" != Path(path):
        raise SpecError("foreign native descriptor", "incompatible_handoff")
    return value


def _response(run, value):
    return run.response(
        "completed" if value["outcome"] == "sufficient" else value["outcome"],
        value["answer"],
        blockers=value["blockers"],
    )


def stage_response(run, data: dict) -> dict:
    """The result envelope of an Agent stage result that records nothing further."""
    return _response(run, data)


def launcher_argv(package_root: Path) -> list[str]:
    return [
        sys.executable,
        str(package_root / "scripts/run-operation.py"),
        "--native-context",
    ]


# --- one Agent call -------------------------------------------------------------------------


class _Call:
    """Preparation and the result gate of one Agent call, inside a re-admitted request."""

    def __init__(
        self,
        package_root: Path,
        action: str,
        payload: dict,
        result: dict,
        internal: dict,
    ):
        self.package_root = package_root
        self.action = action
        # ``payload`` is the step's JSON input; ``internal`` what the Host itself supplies.
        self.payload = payload
        self.result = result
        self.internal = internal

    # Admission's dispatch hands every native route to one of these two entries.
    def agent_call(self, request: AdmittedRequest, agent: str) -> dict:
        return self._run(bind(request), self.internal.get("agent") or agent)

    def workflow(self, request: AdmittedRequest, entry: str) -> dict:
        if self.action == PREPARE:
            return _prepare_workflow(self, bind(request), entry)
        return self._run(bind(request), self.internal.get("agent"))

    def _run(self, run: Invocation, agent: str | None) -> dict:
        if self.action in {PREPARE, PREPARE_SLOT}:
            return self._prepare(run, agent)
        return self._step(run)

    # -- preparation ---------------------------------------------------------------------

    def _prepare(self, run: Invocation, agent: str | None) -> dict:
        if agent is None:
            raise SpecError("no Agent named for this native call", "invalid_input")
        definition = agent_definition(agent)
        hook = resolve_hook(definition.hook, AGENT_HOOK_METHODS)
        admitted = self.internal.get("admitted")
        plan = hook.prepare(run, None if admitted is None else tuple(admitted))
        if plan.stop is not None:
            self.result.update(
                state="described" if run.host.mode == "describe-policy" else "not-run",
                accepted=plan.stop_accepted,
            )
            return plan.stop
        binding = bind_agent(run.host.package_root, definition.name)
        snapshot = resolve_context(
            run.repository,
            run.target.id,
            agent=binding,
            task=run.task["task"],
            focus_id=run.task.get("focus_id"),
            constraints=tuple(run.task.get("constraints", [])),
            stage_inputs=plan.stage_inputs,
            require_inputs=run.host.mode == "execute",
        )
        run.last_context = snapshot.id
        if run.host.mode == "describe-policy":
            return self._describe(run, definition, snapshot)
        native_root = self.payload.get("native_root")
        if not isinstance(native_root, str) or not native_root:
            raise SpecError(
                "Select CONCORDE_NATIVE_SUBAGENTS_ROOT before native execution",
                "missing_runtime",
            )
        runtime = admit_native_runtime(Path(native_root))
        slot = self.internal.get("slot_directory")
        directory = (
            Path(slot)
            if slot
            else Path(tempfile.mkdtemp(prefix="concorde-native-context-"))
        )
        directory.mkdir(parents=True, exist_ok=True)
        capsule = directory / "context"
        delivered = assemble_capsule(
            run.repository, snapshot, capsule, review=plan.review_input
        )
        ticket = self.internal.get("slot_ticket") if slot else str(uuid.uuid4())
        body = (
            plan.instructions
            if plan.instructions is not None
            else load_instructions(run.host.package_root, binding)
        )
        external = "concorde-" + definition.name.replace("_", "-")
        descriptor = {
            "schema_version": 1,
            "kind": "call",
            "operation": run.operation,
            "phase": definition.phase,
            "agent": definition.name,
            "external": external,
            "hook": definition.hook,
            "ticket": ticket,
            "directory": str(directory),
            "package_root": str(self.package_root.resolve()),
            "python": sys.executable,
            "project_root": str(run.repository.root),
            "envelope": self.payload["invocation"],
            "configuration": run.configuration,
            "snapshot": snapshot.value,
            "stage_inputs": list(plan.stage_inputs),
            "review_input": plan.review_input,
            "instructions_digest": digest(body.encode()),
            "bind_admitted_snapshot": plan.bind_admitted_snapshot,
            "result_type": definition.result,
            "delivered": delivered,
            "registry_digest": digest(run.repository.registry_bytes),
            "change_digest": candidate_input_digest(run.repository.root),
            "runtime": dataclasses.asdict(runtime),
            "session_id": self.payload["session_id"],
            "native_session_id": self.payload.get(
                "native_session_id", self.payload["session_id"]
            ),
            "gate_command": self.internal.get("gate_command"),
            "workflow": self.internal.get("workflow"),
        }
        filename = directory / "descriptor.json"
        argv = launcher_argv(self.package_root)
        child_extension = directory / "capture.ts"
        child_extension.write_text(
            "import { readFileSync } from 'node:fs';\n"
            + "import { nativeContextChild } from "
            + json.dumps(
                str(self.package_root / "pi/extensions/concorde-native-child.ts")
            )
            + ";\n"
            + "export default nativeContextChild({..."
            + json.dumps(
                {
                    "argv": argv,
                    "descriptor": str(filename),
                    "root": str(run.repository.root),
                    "reportSchema": _report_schema(),
                    "checks": "run_checks" in definition.tools,
                    "checksTimeoutMs": 10000
                    + 1000
                    * sum(
                        check_command(run.repository.checks[key])[1]
                        for key in run.target.checks
                    ),
                }
            )
            + ", digest: readFileSync("
            + json.dumps(str(directory / "descriptor.digest"))
            + ", 'utf8')});\n"
        )
        chosen = worker_selection(run.configuration, definition.name)
        fields = {
            "name": external,
            "description": "Prepared native "
            + definition.name
            + "; use only its issued invocation.",
            "tools": [*definition.tools, "report_issue"],
            "extensions": [str(child_extension)],
            "allowNestedSubagents": False,
            "maxSubagentDepth": 1,
            "acceptanceRole": "writer"
            if definition.writes_implementation
            else "read-only",
            "inheritProjectContext": False,
            "inheritGlobalContext": False,
            "inheritSkills": False,
            "defaultContext": "fresh",
            "async": False,
            "timeoutMs": (chosen.timeout_seconds or definition.timeout_seconds) * 1000,
            "systemPromptMode": "replace",
            **({"model": chosen.model} if chosen.model else {}),
            **({"thinking": chosen.thinking} if chosen.thinking else {}),
        }
        agent_file = capsule / (".pi/agents/" + external + ".md")
        agent_file.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            key
            + ": "
            + (", ".join(value) if isinstance(value, list) else json.dumps(value))
            for key, value in fields.items()
        ]
        agent_file.write_text("---\n" + "\n".join(lines) + "\n---\n" + body)
        settings = capsule / ".pi/settings.json"
        settings.write_text(
            canonical({"subagents": {"projectRootResolution": "nearest"}})
        )
        descriptor["assets"] = {
            str(path.relative_to(directory)): digest(path.read_bytes())
            for path in (agent_file, child_extension, settings)
        }
        call = {
            "agent": external,
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
            "outputSchema": native_output_schema(definition.result, ticket),
        }
        provided = self.internal.get("native_call")
        if provided is not None:
            if (
                provided.get("agent") != external
                or provided.get("cwd") != str(capsule)
                or provided.get("gate", {}).get("command")
                != self.internal.get("gate_command")
            ):
                raise SpecError(
                    "foreign native slot call layout", "incompatible_handoff"
                )
            call = dict(provided)
        descriptor["launch"] = {k: v for k, v in call.items() if k != "gate"}
        _write(filename, descriptor)
        identity = digest(descriptor)
        (directory / "descriptor.digest").write_text(identity)
        command = descriptor["gate_command"] or shlex.join(
            [*argv, "stage", str(filename), identity]
        )
        call["gate"] = {"command": command}
        self.result.update(
            state="prepared",
            accepted=False,
            descriptor=str(filename),
            digest=identity,
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
            f"Prepared native {definition.name}; model not run and result not accepted.",
        )

    def _describe(self, run, definition: AgentDefinition, snapshot) -> dict:
        from ..spec.boundaries import scope_roots

        self.result.update(
            state="described",
            accepted=False,
            policy={
                "enforcement": "prompt-level",
                "agent": definition.name,
                "read": [
                    "context.json",
                    *delivered_documents(run.repository, snapshot.value),
                    *(
                        [
                            record["path"]
                            for record in snapshot.value["external_references"]
                        ]
                        if "references" in definition.reads
                        else []
                    ),
                ],
                "write": list(
                    scope_roots(run.repository.implementation_scope(run.target))
                )
                if definition.writes_implementation
                else [],
                "tools": list(definition.tools),
                "delegation": False,
            },
        )
        return run.response(
            "described",
            f"Native {definition.name} intended read policy; no child was launched.",
        )

    # -- the result gate ---------------------------------------------------------------------

    def _step(self, run: Invocation) -> dict:
        descriptor = self.internal["descriptor"]
        action = self.action
        directory = Path(descriptor["directory"])
        if (
            action not in {"invalidate", "observe-error"}
            and (directory / "invalid").exists()
        ):
            raise _slot_failure(directory)
        if (directory / "terminal.json").exists():
            raise SpecError(
                "native invocation is already terminal; prepare a fresh request",
                "invalid_completion",
            )
        definition = agent_definition(descriptor["agent"])
        hook = resolve_hook(descriptor["hook"], AGENT_HOOK_METHODS)
        if definition.hook != descriptor["hook"]:
            raise SpecError("the Agent's hook changed", "stale_context")
        plan = hook.prepare(run, tuple(descriptor["stage_inputs"]))
        if (
            plan.stop is not None
            or canonical(list(plan.stage_inputs))
            != canonical(descriptor["stage_inputs"])
            or canonical(plan.review_input) != canonical(descriptor["review_input"])
        ):
            raise SpecError("the hook's stage plan changed", "stale_context")
        snapshot = ContextSnapshot(canonical(descriptor["snapshot"]))
        if not plan.bind_admitted_snapshot:
            current = resolve_context(
                run.repository,
                run.target.id,
                agent=bind_agent(run.host.package_root, definition.name),
                task=run.task["task"],
                focus_id=run.task.get("focus_id"),
                constraints=tuple(run.task.get("constraints", [])),
                stage_inputs=plan.stage_inputs,
            )
            changed = sorted(
                key
                for key in current.value.keys() | descriptor["snapshot"].keys()
                if key != "context_id"
                and current.value.get(key) != descriptor["snapshot"].get(key)
            )
            if changed:
                raise SpecError(
                    "native call inputs changed: " + ", ".join(changed),
                    "stale_context",
                )
        run.last_context = snapshot.id
        if (
            run.configuration != descriptor["configuration"]
            or digest(run.repository.registry_bytes) != descriptor["registry_digest"]
            or candidate_input_digest(run.repository.root)
            != descriptor["change_digest"]
        ):
            raise SpecError("native call inputs changed", "stale_context")
        for name, expected in descriptor["assets"].items():
            if digest(read_file(directory, name)) != expected:
                raise SpecError(
                    "native Agent or capture asset changed", "stale_context"
                )
        recheck_context(run.repository, snapshot)
        verify_capsule(
            run.repository, snapshot, directory / "context", descriptor["delivered"]
        )
        hook.recheck(run, descriptor)
        if action in {"accept", "admit"}:
            _refuse_failed_run(self.payload, descriptor, directory)
        if action == "observe-error":
            # Observation is not acceptance and does not invalidate a correctable rejection.
            observed = self.payload.get("feedback", {})
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
            self.result.update(state="observed", accepted=False)
        elif action == "invalidate":
            if self.payload.get("reason"):
                _remember_failure(
                    directory,
                    failure(
                        self.payload["reason"],
                        layer="proposal",
                        category="capture-failure",
                        attempt=descriptor["ticket"],
                    ),
                )
            (directory / "invalid").touch(exist_ok=True)
            self.result.update(state="invalidated", accepted=False)
        elif action == "report":
            reporter = _reporter(run, descriptor, snapshot, definition)
            self.result.update(reporter(self.payload))
            (directory / "reports.json").write_text(canonical(reporter.receipts))
        elif action == "checks":
            if "run_checks" not in definition.tools:
                raise SpecError(
                    "this Agent has no configured check service", "permission_denied"
                )
            from .checks import check_service

            self.result.update(
                check_service(run.repository, run.target, descriptor["ticket"])()
            )
        elif action == "check":
            self.result.update(state="prepared", accepted=False)
        elif action == "submit":
            try:
                if len(canonical(self.payload).encode()) > MAX_PROPOSAL_BYTES:
                    raise SpecError(
                        "native proposal exceeds 1 MiB", "invalid_completion"
                    )
                _write(directory / "proposal.json", self.payload)
                _proposal(run, descriptor, snapshot, definition, hook, plan)
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
            self.result.update(state="proposed", accepted=False)
        elif action in {"stage", "accept", "admit"}:
            proposal = _proposal(run, descriptor, snapshot, definition, hook, plan)
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
                self.result.update(control)
            else:
                return self._accept(run, descriptor, snapshot, hook, plan, proposal)
        else:
            raise SpecError("unknown native action", "invalid_input")
        return run.response(
            "described", "Native proposal transport; not accepted completion."
        )

    def _accept(self, run, descriptor, snapshot, hook, plan, proposal) -> dict:
        directory = Path(descriptor["directory"])
        runtime = admit_native_runtime(Path(descriptor["runtime"]["package_root"]))
        if dataclasses.asdict(runtime) != descriptor["runtime"]:
            raise SpecError("native producer changed", "stale_evidence")
        metadata = verify_native_single(
            self.payload,
            agent=descriptor["external"],
            session_id=descriptor["session_id"],
            ticket=descriptor["ticket"],
            proposal_digest=digest(proposal),
            gate_command=self.payload["gate_command"],
            runtime=runtime,
        )
        expected_gate = descriptor["gate_command"] or shlex.join(
            [
                *launcher_argv(self.package_root),
                "stage",
                str(directory / "descriptor.json"),
                self.internal["descriptor_digest"],
            ]
        )
        if self.payload["gate_command"] != expected_gate:
            raise SpecError("foreign native gate", "incompatible_handoff")
        if self.action == "admit":
            self.result.update(
                state="admitted", accepted=False, proposal=proposal, native=metadata
            )
            return run.response(
                "described", "Proposal independently admitted; not accepted."
            )
        # The exclusive terminal reservation makes a repeated or concurrent accept fail.
        _write(directory / "terminal.json", {"state": "finalizing", "accepted": False})
        data = proposal["result"]["data"]
        output = hook.accept(run, snapshot, plan, data)
        from .status_store import write_run

        write_run(
            run.host.archive_root,
            f".concorde/runs/{run.host.invocation_id}/native-context.json",
            canonical(
                {
                    "descriptor": descriptor,
                    "proposal": proposal,
                    "native": metadata,
                    "correlation": self.payload,
                    "accepted": True,
                }
            ).encode(),
        )
        self.result.update(state="accepted", accepted=True, outcome=data["outcome"])
        (directory / "terminal.json").write_text(
            canonical(
                {
                    "state": "accepted",
                    "outcome": data["outcome"],
                    "output": output,
                    "change_digest": candidate_input_digest(run.repository.root),
                    "workspace": workspace_context(
                        run.repository.root,
                        target_id=run.target.id,
                        task=run.task["task"],
                    ),
                }
            )
        )
        return output


def _report_schema():
    from ..issues.shapes import REPORT

    return REPORT


def _refuse_failed_run(payload, descriptor, directory) -> None:
    rows = payload.get("details", {}).get("results", [])
    if len(rows) == 1 and (
        rows[0].get("interrupted")
        or rows[0].get("stopped")
        or rows[0].get("exitCode") != 0
    ):
        error = OperationExecutionError(
            "native Agent run did not complete",
            outcome="limit_exhausted"
            if rows[0].get("timedOut")
            else "cancelled"
            if rows[0].get("interrupted") or rows[0].get("stopped")
            else "failed",
        )
        error.feedback = native_feedback(rows[0], attempt=descriptor["ticket"])
        error.feedback["causes"].extend(_slot_failure(directory).feedback["causes"])
        raise error


def _reporter(run, descriptor, snapshot, definition: AgentDefinition):
    from ..issues.reporting import reporter_for_invocation

    review = definition.context == "concorde-review-stage-context"
    invocation = SimpleNamespace(
        context_json=canonical(
            typed(
                definition.context,
                {
                    "snapshot": typed("concorde-context-snapshot", snapshot.value),
                    **(
                        {
                            "review": typed(
                                "concorde-review-input", descriptor["review_input"]
                            )
                        }
                        if review
                        else {"change_id": run.change_id, "expected_artifacts": []}
                    ),
                },
            )
        ),
        invocation_id=descriptor["ticket"],
        agent=definition.name,
        operation=descriptor["operation"],
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


def _proposal(run, descriptor, snapshot, definition, hook, plan):
    from ..issues.references import validate_references

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
    validate_agent_result(definition, value["result"])
    data = value["result"]["data"]
    reporter = _reporter(run, descriptor, snapshot, definition)
    validate_references(
        run.repository.root,
        data.get("blockers", data.get("issues", [])),
        admitted=[*reporter.receipts, *reporter.admitted_receipts],
    )
    hook.validate(run, snapshot, plan, data)
    return value


# --- one Workflow ---------------------------------------------------------------------------


class _Workflow:
    """The Workflow driver a workflow hook receives: slots, coverage, admission, receipts."""

    def __init__(self, package_root: Path, descriptor: dict, context: dict):
        self.package_root = package_root
        self.descriptor = descriptor
        self.directory = Path(descriptor["directory"])
        self.ticket = descriptor["ticket"]
        self.context = context

    # Facts a hook may read.
    @property
    def node(self) -> str:
        return self.descriptor["node"] or "node"

    @property
    def slot_gate(self) -> str:
        """The gate command prefix of a slot; a slot's gate is this plus its key."""
        return command_text(
            [
                *launcher_argv(self.package_root),
                "slot-gate",
                str(self.directory / "descriptor.json"),
                self.descriptor["digest"],
            ]
        )

    def _binding(self, key: str) -> dict:
        path = self.directory / "bindings" / f"{key}.json"
        if "/" in key or not path.is_file():
            raise SpecError(f"no issued slot {key!r}", "invalid_completion")
        return _record(path)

    def slot(self, key: str) -> dict | None:
        """The descriptor of an issued slot, or None."""
        path = self.directory / "bindings" / f"{key}.json"
        if not path.is_file():
            return None
        return _record(Path(_record(path)["descriptor"]))

    def terminal(self, key: str) -> dict:
        """The terminal record of an accepted slot."""
        slot = self.slot(key)
        if slot is None:
            raise SpecError(f"no issued slot {key!r}", "invalid_completion")
        return _record(Path(slot["directory"]) / "terminal.json")

    def issue_slot(
        self,
        key: str,
        agent: str,
        task: dict,
        *,
        stage_inputs: tuple[dict, ...] = (),
        operation: str | None = None,
        call: dict | None = None,
    ) -> dict:
        if self.stopped():
            raise SpecError("the Workflow was stopped", "execution_cancelled")
        if self.descriptor["runtime"] is None:
            raise SpecError(
                "Select CONCORDE_NATIVE_SUBAGENTS_ROOT before native execution",
                "missing_runtime",
            )
        bindings = self.directory / "bindings"
        bindings.mkdir(exist_ok=True)
        if (bindings / f"{key}.json").exists():
            raise SpecError("slot is already issued", "invalid_completion")
        operation = operation or self.descriptor["operation"]
        clean = {
            k: v for k, v in task.items() if v is not None and not k.startswith("_")
        }
        envelope = {
            **self.descriptor["envelope"],
            "operation_id": operation,
            "input": typed(operation + "-request", clean),
        }
        payload = {
            "invocation": envelope,
            "native_root": self.descriptor["runtime"]["package_root"],
            "session_id": self.descriptor["session_id"],
            "native_session_id": self.descriptor["native_session_id"],
        }
        internal = {
            "agent": agent,
            "admitted": list(stage_inputs) if stage_inputs else None,
            "slot_directory": str(self.directory / "slots" / key),
            "slot_ticket": self.ticket + ":" + key,
            "workflow": {"directory": str(self.directory), "key": key},
        }
        if call is not None:
            internal.update(native_call=call, gate_command=call["gate"]["command"])
        value = _admit(
            self.package_root,
            PREPARE_SLOT,
            payload,
            envelope,
            self.context,
            relay=False,
            internal=internal,
        )
        if value.get("state") != "prepared":
            raise response_failure(
                "slot preparation refused", value, layer="workflow", attempt=key
            )
        entry = {k: value[k] for k in ("descriptor", "digest", "ticket", "call")}
        entry.update(key=key, agent=agent)
        _write(bindings / f"{key}.json", entry)
        return value["call"]

    def _command(self, key: str, action: str, payload: dict) -> dict:
        entry = self._binding(key)
        return execute(
            self.package_root,
            action,
            payload,
            entry["descriptor"],
            entry["digest"],
            **self.context,
        )

    def check(self, key: str) -> None:
        value = self._command(key, "check", {})
        if value.get("state") != "prepared":
            raise response_failure(
                "slot is no longer current", value, layer="workflow", attempt=key
            )

    def _native(self) -> tuple[dict, dict]:
        binding = _record(self.directory / "workflow-binding.json")
        status = _record(Path(binding["asyncDir"]) / "status.json")
        if (
            status.get("runId") != binding["runId"]
            or status.get("sessionId") != self.descriptor["native_session_id"]
        ):
            raise SpecError("foreign native workflow", "incompatible_handoff")
        return binding, status

    def coverage(self, keys: Sequence[str]) -> None:
        binding, _ = self._native()
        children = []
        for key in keys:
            entry = self._binding(key)
            slot = _record(Path(entry["descriptor"]))
            proposal = _record(Path(slot["directory"]) / "proposal.json")
            children.append(
                NativeChildEvidence(
                    key,
                    slot["external"],
                    slot["ticket"],
                    digest(proposal),
                    entry["call"]["gate"]["command"],
                    slot["ticket"],
                )
            )
        verify_native_children(
            Path(binding["asyncDir"]),
            run_id=binding["runId"],
            session_id=self.descriptor["native_session_id"],
            ticket=self.ticket,
            children=tuple(children),
            runtime=admit_native_runtime(
                Path(self.descriptor["runtime"]["package_root"])
            ),
        )

    def _correlation(self, key: str) -> dict:
        binding, status = self._native()
        entry = self._binding(key)
        slot = _record(Path(entry["descriptor"]))
        emissions = [
            item
            for item in status.get("workflow", {}).get("emits", [])
            if item.get("kind") == "concorde.child-terminal" and item.get("key") == key
        ]
        if len(emissions) != 1:
            raise SpecError(f"missing native child for slot {key}", "stale_evidence")
        emission = emissions[0]
        preflight = _record(Path(slot["directory"]) / "preflight.json")
        return {
            "details": {
                "mode": "single",
                "runId": emission["runId"],
                "results": [emission["result"]],
            },
            "isError": False,
            "tool_call_id": binding["runId"] + "/" + key,
            "session_id": slot["session_id"],
            "launch_contract_digest": preflight["launchContractDigest"],
            "gate_command": entry["call"]["gate"]["command"],
        }

    def admit(self, key: str) -> dict:
        value = self._command(key, "admit", self._correlation(key))
        if value.get("state") != "admitted":
            raise response_failure(
                "slot proposal was not independently admitted",
                value,
                layer="workflow",
                attempt=key,
            )
        return value

    def accept(self, key: str) -> dict:
        value = self._command(key, "accept", self._correlation(key))
        if not value.get("accepted"):
            raise response_failure(
                "slot proposal was not accepted", value, layer="workflow", attempt=key
            )
        return value

    def receipt(self, value: dict) -> None:
        _write(self.directory / "workflow-result.json", value)

    def reserve(self, name: str) -> None:
        """Reserve a provider's own exclusive record; a second reservation fails."""
        try:
            _write(self.directory / f"{name}.json", {"state": "finalizing"})
        except FileExistsError as error:
            raise SpecError(
                f"{name} is already reserved", "invalid_completion"
            ) from error

    def stopped(self) -> bool:
        return (self.directory / "workflow-stopped").exists()

    def state(self, name: str, default=None):
        """A provider's own JSON record in the Workflow directory."""
        path = self.directory / f"{name}.json"
        return _record(path) if path.exists() else default

    def save(self, name: str, value) -> None:
        _save(self.directory / f"{name}.json", value)


def _prepare_workflow(call: _Call, run: Invocation, entry: str) -> dict:
    hook = resolve_hook(entry, WORKFLOW_HOOK_METHODS)
    payload = call.payload
    ticket = str(uuid.uuid4())
    execute_mode = run.host.mode == "execute"
    # A policy preview creates nothing; its hook stops before issuing any slot.
    directory = (
        Path(tempfile.mkdtemp(prefix="concorde-native-workflow-"))
        if execute_mode
        else Path(tempfile.gettempdir()) / f"concorde-native-workflow-preview-{ticket}"
    )
    base = {
        "schema_version": 1,
        "kind": "workflow",
        "operation": run.operation,
        "hook": entry,
        "directory": str(directory),
        "ticket": ticket,
        "package_root": str(call.package_root.resolve()),
        "python": sys.executable,
        "node": payload.get("native_node"),
        "project_root": str(run.repository.root),
        "configuration": run.configuration,
        "task": run.task,
        "envelope": payload["invocation"],
        "session_id": payload.get("session_id"),
        "native_session_id": payload.get(
            "native_session_id", payload.get("session_id")
        ),
        "runtime": None,
        "digest": None,
    }
    native_root = payload.get("native_root")
    if execute_mode and isinstance(native_root, str) and native_root:
        base["runtime"] = dataclasses.asdict(admit_native_runtime(Path(native_root)))
    driver = _Workflow(call.package_root, base, _context(call))
    try:
        plan = hook.prepare(run, driver)
    except BaseException:
        if execute_mode and not (directory / "bindings").exists():
            shutil.rmtree(directory, ignore_errors=True)
        raise
    if plan.stop is not None:
        if execute_mode and not (directory / "bindings").exists():
            shutil.rmtree(directory, ignore_errors=True)
        call.result.update(
            state="described" if not execute_mode else "not-run",
            accepted=plan.stop_accepted,
        )
        return plan.stop
    if not execute_mode:
        raise SpecError("a Workflow runs only in execute mode", "invalid_input")
    if base["runtime"] is None:
        raise SpecError(
            "Select CONCORDE_NATIVE_SUBAGENTS_ROOT before native execution",
            "missing_runtime",
        )
    descriptor = {
        **{k: v for k, v in base.items() if k != "digest"},
        "script": plan.script,
        "host": plan.host,
        "steps": list(plan.steps),
        "helpers": list(plan.helpers),
        "name": "concorde." + run.operation.removeprefix("concorde-") + "." + ticket,
    }
    path = directory / "descriptor.json"
    _write(path, descriptor)
    identity = digest(descriptor)
    (directory / "descriptor.digest").write_text(identity)
    driver.descriptor = {**descriptor, "digest": identity}
    commands = {
        step: [
            descriptor["node"] or "node",
            str(call.package_root / plan.host),
            step,
            str(path),
            identity,
        ]
        for step in plan.steps
    }
    expansion = {
        **plan.expansion,
        "ticket": ticket,
        "commands": {step: command_text(argv) for step, argv in commands.items()},
        "slot_gate": driver.slot_gate,
    }
    call.result.update(
        state="prepared",
        accepted=False,
        descriptor=str(path),
        digest=identity,
        ticket=ticket,
        binding={
            "argv": launcher_argv(call.package_root),
            "root": str(run.repository.root),
            "descriptor": str(path),
            "digest": identity,
        },
        workflow={
            "name": descriptor["name"],
            "script": plan.script,
            "host": plan.host,
            "steps": list(plan.steps),
            "helpers": list(plan.helpers),
            "commands": commands,
            "expansion": expansion,
        },
    )
    return run.response(
        "described", "Native Workflow prepared; no Agent ran and nothing is accepted."
    )


def _context(call) -> dict:
    return call.internal["context"]


def _workflow_run(package_root: Path, descriptor: dict, context: dict) -> Invocation:
    from .configuration import load_configuration

    root = Path(descriptor["project_root"])
    if (
        str(package_root.resolve()) != descriptor["package_root"]
        or load_configuration(root) != descriptor["configuration"]
    ):
        raise SpecError(
            "Workflow runtime or configuration changed", "configuration_mismatch"
        )
    return Invocation(
        descriptor["operation"],
        descriptor["configuration"],
        descriptor["task"],
        OperationHost(
            root,
            package_root,
            services=context["services"],
            session_provenance=context["provenance"],
        ),
    )


def _workflow_descriptor(path, expected) -> dict:
    value = _descriptor(path, expected)
    if value.get("kind") != "workflow":
        raise SpecError("not a Workflow descriptor", "incompatible_handoff")
    return {**value, "digest": expected}


def workflow_step(package_root: Path, name: str, path, expected, context) -> dict:
    """``workflow-<name>``: the workflow hook's answer to one of its declared steps."""
    import fcntl

    descriptor = _workflow_descriptor(path, expected)
    directory = Path(descriptor["directory"])
    with (directory / "host.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        driver = _Workflow(package_root, descriptor, context)
        if driver.stopped() or (directory / "invalid").exists():
            raise SpecError("the Workflow was stopped", "execution_cancelled")
        if name not in descriptor["steps"]:
            raise SpecError(f"unknown Workflow step {name!r}", "invalid_input")
        if (directory / "workflow-result.json").exists():
            raise SpecError("the Workflow already finished", "invalid_completion")
        _, status = driver._native()
        if status.get("state") != "running":
            raise SpecError("the Workflow is not running", "execution_cancelled")
        os.chdir(descriptor["project_root"])
        run = _workflow_run(package_root, descriptor, context)
        hook = resolve_hook(descriptor["hook"], WORKFLOW_HOOK_METHODS)
        return hook.step(run, driver, name)


def workflow_result(package_root: Path, path, expected, context) -> dict:
    """``workflow-result``: the Workflow's receipt, or its running or failed native state."""
    descriptor = _workflow_descriptor(path, expected)
    directory = Path(descriptor["directory"])
    driver = _Workflow(package_root, descriptor, context)
    binding, status = driver._native()
    receipt = directory / "workflow-result.json"
    native = {
        "native_state": status.get("state"),
        "native_error": safe_text(status["error"]) if status.get("error") else None,
        "run_id": binding["runId"],
    }
    if status.get("state") in {"failed", "stopped"} and not receipt.exists():
        marker = directory / "failure-observed"
        try:
            marker.touch(exist_ok=False)
        except FileExistsError:
            pass
        else:
            try:
                os.chdir(descriptor["project_root"])
                run = _workflow_run(package_root, descriptor, context)
                hook = resolve_hook(descriptor["hook"], WORKFLOW_HOOK_METHODS)
                value = hook.on_failure(run, driver, status.get("state"))
                if value is not None:
                    driver.receipt(value)
            except SpecError as error:
                return {
                    "state": "stale",
                    "accepted": False,
                    "error": str(error),
                    "failure": workflow_feedback(descriptor, status, binding),
                    **native,
                }
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
        **native,
        "failure": workflow_feedback(descriptor, status, binding)
        if status.get("state") not in {"running", "complete"}
        or status.get("error")
        or (status.get("state") != "running" and not receipt.exists())
        else None,
    }


def workflow_stop(path, expected) -> dict:
    """``workflow-stop``: every later step of the Workflow fails."""
    descriptor = _workflow_descriptor(path, expected)
    (Path(descriptor["directory"]) / "workflow-stopped").touch(exist_ok=True)
    return {"state": "cancelled", "accepted": False}


def workflow_invalidate(path, expected, context) -> dict:
    """``invalidate`` of a Workflow that never launched: its issued slots are invalidated too."""
    descriptor = _workflow_descriptor(path, expected)
    directory = Path(descriptor["directory"])
    (directory / "workflow-stopped").touch(exist_ok=True)
    (directory / "invalid").touch(exist_ok=True)
    for entry in sorted((directory / "bindings").glob("*.json")):
        slot = _record(entry)
        (Path(slot["descriptor"]).parent / "invalid").touch(exist_ok=True)
    return {"state": "invalidated", "accepted": False}


def slot_gate(package_root: Path, path, expected, key, context) -> dict:
    """``slot-gate``: the staging gate of one Workflow slot, named by its key."""
    descriptor = _workflow_descriptor(path, expected)
    driver = _Workflow(package_root, descriptor, context)
    if driver.stopped():
        raise SpecError("the Workflow was stopped", "execution_cancelled")
    return driver._command(key, "stage", {})


# --- entry ----------------------------------------------------------------------------------


def _relay(payload: dict, result: dict):
    def relay(host, op, invocation, candidate):
        relayed = relay_prepare(host, invocation, candidate, payload)
        result.update({k: v for k, v in relayed.items() if k != "result"})
        return relayed["result"], ""

    return relay


def _no_relay(host, op, invocation, candidate):
    raise SpecError("a native step never relays", "workspace_mismatch")


def relay_prepare(host, invocation, candidate, payload):
    """Run the native preparation in the relayed candidate, with the candidate's own launcher."""
    import subprocess

    from .relay import relay_launcher

    # An explicit private selection may bind candidate code to disposable Git data; an ordinary
    # installed run enters the verified candidate-local runtime instead.
    argv = (
        [sys.executable, str(host.package_root / "scripts/run-operation.py")]
        if host.session_provenance
        else relay_launcher(
            host,
            candidate,
            bootstrap=bool(host.relay_target.get("bootstrap_installation")),
        )
    )
    public = {k: v for k, v in payload.items() if not k.startswith("_")}
    process = subprocess.run(
        [*argv, "--native-context", PREPARE],
        input=canonical({**public, "invocation": invocation}),
        text=True,
        capture_output=True,
        cwd=candidate,
        timeout=120,
    )
    try:
        value = json.loads(process.stdout)
    except ValueError as error:
        raise ExecutionFailure(
            failure(
                "candidate native preparation returned no envelope",
                code="relay_failed",
                layer="native-relay",
                category="transport",
                attempt=host.invocation_id,
                causes=[exception_feedback(error)],
                diagnostics=canonical(
                    {
                        "exit_code": process.returncode,
                        "stdout": process.stdout,
                        "stderr": process.stderr,
                    }
                ),
            )
        ) from error
    if process.returncode != 0 and value.get("state") != "rejected":
        raise ExecutionFailure(
            failure(
                "native preparation exited unsuccessfully",
                code="relay_failed",
                layer="native-relay",
                category="native-exit",
                diagnostics=canonical(
                    {"exit_code": process.returncode, "stderr": process.stderr}
                ),
            )
        )
    return value


def _admit(
    package_root, action, payload, envelope, context, *, relay, internal=None
) -> dict:
    from .admission import run_operation

    operation = envelope["operation_id"]
    validate_invocation(envelope, operation)
    services = context["services"]
    declaration = services.catalog.get(operation) if services else None
    if declaration is None or not declaration.get("model_backed"):
        raise SpecError("not a native capability", "unknown_operation")
    result: dict = {}
    call = _Call(
        package_root, action, payload, result, {**(internal or {}), "context": context}
    )
    host = OperationHost(
        Path.cwd(),
        package_root,
        mode=envelope["mode"],
        native_driver=call,
        native_transport=action != "accept",
        relay=_relay(payload, result) if relay else _no_relay,
        services=services,
        session_provenance=context["provenance"],
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
    *,
    services=None,
    provenance=None,
):
    """One native action; ``services`` and ``provenance`` are what the launcher hands admission.

    An action started by another action of the same native command inherits what the launcher
    handed that command.
    """
    services = services or _LAUNCHED.get("services")
    if services is None:
        raise SpecError(
            "a native action needs the services the launcher hands admission",
            "invalid_input",
        )
    if provenance is None:
        provenance = _LAUNCHED.get("provenance")
    context = {"services": services, "provenance": provenance}
    if action == PREPARE:
        return _admit(
            package_root, action, payload, payload["invocation"], context, relay=True
        )
    if action not in CALL_ACTIONS:
        raise SpecError("unknown native action", "invalid_input")
    import fcntl

    descriptor = _descriptor(descriptor_path, expected_digest)
    if descriptor.get("kind") == "workflow":
        if action != "invalidate":
            raise SpecError("not an Agent call descriptor", "incompatible_handoff")
        return workflow_invalidate(descriptor_path, expected_digest, context)
    if str(package_root.resolve()) != descriptor["package_root"]:
        raise SpecError("native runtime selection changed", "workspace_mismatch")
    # One finite command at a time per call; never held across a model run.
    with (Path(descriptor["directory"]) / "command.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        os.chdir(descriptor["project_root"])
        return _admit(
            package_root,
            action,
            payload,
            descriptor["envelope"],
            context,
            relay=False,
            internal={
                "descriptor": descriptor,
                "descriptor_digest": expected_digest,
                "agent": descriptor["agent"],
            },
        )


# What the launcher handed the running ``--native-context`` command.
_LAUNCHED: dict = {}


def main(package_root, args, *, services, select_session):
    """The ``--native-context`` entry; the launcher supplies admission's services and selection."""
    operation = None
    try:
        _LAUNCHED.update(services=services, provenance=select_session())
        context = {
            "services": services,
            "provenance": _LAUNCHED["provenance"],
        }
        raw = sys.stdin.buffer.read(MAX_PROPOSAL_BYTES + 1)
        if len(raw) > MAX_PROPOSAL_BYTES:
            raise SpecError("native input exceeds 1 MiB", "invalid_input")
        payload = decode(raw.decode()) if raw else {}
        action = args[0]
        operation = (
            payload.get("invocation", {}).get("operation_id")
            if action == PREPARE
            else _record(Path(args[1])).get("operation")
        )
        if action == "slot-gate":
            value = slot_gate(package_root, *args[1:4], context)
        elif action == "workflow-result":
            value = workflow_result(package_root, *args[1:3], context)
        elif action == "workflow-stop":
            value = workflow_stop(*args[1:3])
        elif action.startswith("workflow-"):
            value = workflow_step(
                package_root, action.removeprefix("workflow-"), *args[1:3], context
            )
        else:
            value = execute(package_root, action, payload, *args[1:3])
        if action in {"stage", "slot-gate"} and value.get("state") == "staged":
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


def open_repository(descriptor: dict, package_root: Path) -> SpecRepository:
    """The Spec repository of a descriptor's project."""
    return SpecRepository(Path(descriptor["project_root"]), package_root)
