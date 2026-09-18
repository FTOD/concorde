"""Trusted execution of every public Concorde operation under Profile 15.

Agents consume frozen Spec snapshots. Deterministic checks execute separately and their raw
output never becomes a non-implementation agent input. Each stage starts a fresh process.
"""

from __future__ import annotations

import copy
import importlib
import json
import os
import sys
import tempfile
import uuid
from contextlib import suppress
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from ..distribution.build import BuildError, load_model_instructions, verify_fresh
from ..harness.change_worktree import (
    STATE_PATH,
    WORK_PATH,
    bind_owner,
    blocker_scope,
    create_worktree,
    ensure_change,
    graph_state,
    progress,
    read_change,
    record_transition,
    refresh_registry,
    resume_owner,
    save_change,
    save_target_state,
    snapshot_tree,
    target_state,
    work_path,
    workspace_context,
    workspace_identity,
)
from ..harness.check_executor import CHECK_POLICY, CheckSandboxError, execute_check
from ..harness.context import (
    DiscoveryContext,
    context_documents,
    materialize_documents,
    materialize_references,
    recheck_context,
    recheck_discovery_context,
    recheck_topology_author_context,
    reference_grants,
    resolve_context,
    resolve_discovery_context,
    resolve_topology_author_context,
)
from ..harness.model_selection import worker_selection
from ..harness.permissions import PermissionPolicyError, PolicyBinding, compile_policy
from ..harness.usage import read_usage, record_usage, summarize_usage
from ..harness.worker_executor import (
    OperationExecutionError,
    WorkerOutcome,
    build_worker_invocation,
    worker_instructions,
)
from ..harness.worker_profile import (
    ContractError,
    binding_json,
    external_worker_name,
    worker_profile,
)
from ..spec.changes import apply_files, file_change
from ..spec.contracts import (
    DETERMINISTIC_OPERATIONS,
    DISCOVERY_NODES,
    DISCOVERY_OPERATIONS,
    MAIN_OPERATION,
    MODEL_STAGES,
    TOPOLOGY_AUTHOR_NODE,
    load_operation_inventory,
)
from ..spec.repository import SpecError, SpecRepository, digest, read_file
from ..spec.typed_data import (
    OPERATION_CONTRACTS,
    TypedDataError,
    artifact,
    canonical,
    checked_path,
    decode,
    typed,
    validate_typed,
    verify_artifacts,
)
from ..spec.validation import (
    document_context_findings,
    module_dependency_findings,
    validate_repository,
)
from .configuration import load_configuration


@dataclass(frozen=True)
class OperationHost:
    project_root: Path
    package_root: Path
    mode: str = "execute"
    executor: Any = None
    allow_primary_worktree: bool = False
    outer_sandbox: str | None = None
    routed_target: str | None = None
    configuration_snapshot: str = ""
    session_root: Path | None = None
    coordinated: bool = False
    track_gaps: bool = False
    defer_ready: bool = False
    defer_component_checks: bool = False
    finalize_components: bool = False
    issue_intent: str | None = None
    depth: int = 0
    invocation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # The top-level operation invocation's identity, inherited by every nested invocation so one
    # Graph run keeps one usage record under .concorde/runs/<root_invocation_id>/.
    root_invocation_id: str | None = None
    descriptions: list[dict] = field(default_factory=list)
    evidence: list[Any] = field(default_factory=list)
    lifecycle: dict = field(default_factory=dict)
    observer: Any = None

    def observe(self, event: str, **details) -> None:
        # Observability must never turn a completed mutation into a retryable failure.
        if self.observer is not None:
            with suppress(Exception):
                self.observer(event, **details)

    def __post_init__(self):
        if self.project_root.is_symlink() or self.package_root.is_symlink():
            raise SpecError("host roots cannot be symlinks", "workspace_mismatch")
        object.__setattr__(self, "project_root", self.project_root.resolve())
        object.__setattr__(self, "package_root", self.package_root.resolve())
        object.__setattr__(
            self, "session_root", (self.session_root or self.project_root).resolve()
        )


def _operation_key(operation: str) -> str:
    return operation[len("concorde-") :].replace("-", "_")


def _protocol_documents(
    value: dict, granted: dict[str, bytes]
) -> list[tuple[str, bytes]]:
    """The Protocol files a context index lists, in its order, with their verified bytes."""
    return [(record["path"], granted[record["path"]]) for record in value["protocol"]]


def _worker_invocation(
    configuration: dict,
    *,
    operation: str,
    stage: str,
    prompt,
    workspace: Path,
    context_value: dict,
    receipt: dict,
    policy,
    protocol: list[tuple[str, bytes]],
):
    """Bind one worker launch: its frozen context, policy, binding, instructions and model selection."""
    agent = worker_profile(prompt.binding.agent)
    resolve_child_operation(operation, external_worker_name(agent.name))
    return build_worker_invocation(
        operation=operation,
        stage=stage,
        agent=agent.name,
        invocation_id=str(uuid.uuid4()),
        workspace=str(workspace),
        context_json=canonical(context_value),
        receipt_json=canonical(receipt),
        policy=policy,
        binding_json=binding_json(prompt.binding),
        instructions=worker_instructions(prompt.body, protocol),
        selection=worker_selection(configuration, agent.name),
        child_selections=tuple(
            (child.name, worker_selection(configuration, agent.name, child.name))
            for child in agent.children
        ),
    )


def _worker_description(prompt, invocation, policy, **labels) -> dict:
    """The describe-policy record of one worker launch: its grant, profile and model selection."""
    agent = worker_profile(prompt.binding.agent)
    return {
        **labels,
        "read_paths": list(policy.read_paths),
        "write_paths": list(policy.write_paths),
        "network": False,
        "fresh_session": True,
        "policy_digest": policy.digest,
        "agent": external_worker_name(agent.name),
        "agent_binding_digest": prompt.binding.digest,
        "profile_digest": prompt.binding.profile_digest,
        "instructions_digest": prompt.binding.instructions_digest,
        "workspace": agent.workspace,
        "tools": list(agent.tools),
        "children": [child.name for child in agent.children],
        "model": invocation.selection.model,
        "thinking": invocation.selection.thinking,
        "timeout_seconds": invocation.selection.timeout_seconds
        or prompt.binding.timeout_seconds,
    }


def _run_worker(
    host,
    invocation,
    prompt,
    *,
    operation: str,
    stage: str,
    target_id: str | None,
    result_type: str,
    change_id: str | None = None,
    checks=None,
) -> tuple[WorkerOutcome, dict]:
    """Run a bound worker with report-only issue authority; retain reports even on failure."""
    from ..harness.worker_executor import WorkerExecutor
    from ..issues.reporting import reporter_for_invocation

    executor = host.executor or WorkerExecutor(host.package_root)
    reporter = reporter_for_invocation(
        host.project_root, invocation, target_id=target_id, change_id=change_id
    )
    try:
        outcome = executor(invocation, checks=checks, report_issue=reporter)
    finally:
        # Already accepted observations survive invalid completion, cancellation and time limits.
        for receipt in reporter.receipts:
            host.observe(
                "issue_reported",
                **receipt,
                launch_invocation_id=invocation.invocation_id,
            )
    if (
        not isinstance(outcome, WorkerOutcome)
        or outcome.invocation_digest != invocation.digest
        or outcome.binding_digest != prompt.binding.digest
    ):
        raise SpecError(
            "worker outcome is not bound to this invocation", "invalid_completion"
        )
    record_usage(
        host,
        operation=operation,
        stage=stage,
        target_id=target_id,
        agent=external_worker_name(invocation.agent),
        invocation=invocation,
        result=outcome,
        change_id=change_id,
    )
    data = validate_typed(outcome.value, result_type)["data"]
    from ..issues.references import validate_references

    validate_references(
        host.project_root,
        data.get("blockers", data.get("issues", [])),
        admitted=[*reporter.receipts, *reporter.admitted_receipts],
    )
    return outcome, data


def _check_service(repository: SpecRepository, target, invocation_id: str):
    """The host's run_checks answer: every configured check's status and the tail of its log."""

    def run_checks() -> dict:
        current = SpecRepository(repository.root, repository.package_root)
        results = _check(current, current.select(target.id), invocation_id)
        for item in results:
            log = checked_path(
                current.root, f".concorde/runs/{invocation_id}/{item['check_id']}.log"
            )
            item["output_tail"] = (
                log.read_bytes()[-20000:].decode("utf-8", "replace")
                if log.is_file()
                else ""
            )
        return {"checks": results}

    return run_checks


def resolve_child_operation(parent_operation: str, child_operation: str):
    """Return the child operation module for one in-process nested dispatch, or refuse it.

    A parent may always invoke itself (recursive fan-out across component targets, as
    ``review_scope`` and ``implement_scope`` do, is not operation composition and needs no
    declared edge). Any other child must appear in the parent operation module's declared
    ``USES``, or this raises ``SpecError(..., "undeclared_operation")``. Pure name resolution
    with no side effect beyond importing the two modules; kept separate from ``invoke_operation``
    so the declared composition graph can be checked exhaustively without executing anything.
    """

    inventory = load_operation_inventory()
    parent_key, child_key = (
        _operation_key(parent_operation),
        _operation_key(child_operation),
    )
    for key, external in ((parent_key, parent_operation), (child_key, child_operation)):
        if key not in inventory.OPERATIONS or inventory.external_name(key) != external:
            raise SpecError(f"unknown operation: {external}", "unknown_operation")
    if parent_key != child_key:
        try:
            parent_module = importlib.import_module(
                f"{inventory.__name__}.{parent_key}"
            )
        except ImportError as error:
            raise SpecError(
                f"unknown parent operation: {parent_operation}", "unknown_operation"
            ) from error
        if child_key not in parent_module.USES:
            raise SpecError(
                f"{parent_operation} has no declared composition edge to {child_operation}",
                "undeclared_operation",
            )
    try:
        return importlib.import_module(f"{inventory.__name__}.{child_key}")
    except ImportError as error:
        raise SpecError(
            f"unknown operation: {child_operation}", "unknown_operation"
        ) from error


def invoke_operation(
    parent_operation: str,
    child_operation: str,
    configuration: dict,
    payload: dict,
    host: OperationHost,
) -> dict:
    """Adapt existing host-wire composition to an Operation's State-based ``run``.

    Development, Issue solving and recursive per-component review use this transport adapter.
    Model nodes use their own admitted State via OperationNode; both paths check the same USES
    relation. A wire adapter is not a second kind of executable identity.
    """

    child_module = resolve_child_operation(parent_operation, child_operation)
    return _run_host_node(
        child_module.run, host, configuration, payload, child_operation
    )


def _run_host_node(runner, host, configuration, payload, operation):
    """The wire boundary adapts to State; trusted execution context never enters State."""
    from langgraph.runtime import Runtime

    from ..harness.operation_state import OperationRuntimeContext

    validate_typed(payload, f"{operation}-request")
    return runner(
        payload["data"],
        Runtime(
            context=OperationRuntimeContext(host=host, configuration=configuration)
        ),
    )["result"]


def _worktree(
    host: OperationHost, mutation: bool, task: dict
) -> tuple[OperationHost, dict | None]:
    if task.get("change_id") is not None:
        state = read_change(host.project_root, required=True)
        if task["change_id"] != state["change_id"]:
            raise SpecError(
                "change ID does not own this worktree", "incompatible_handoff"
            )
    if host.mode == "describe-policy":
        return host, None
    primary, current = workspace_identity(host.project_root)
    if (
        current is not None
        and primary is not None
        and current["path"] != primary["path"]
    ):
        state = ensure_change(
            host.project_root,
            task=task if mutation else None,
            change_id=task.get("change_id"),
        )
        refresh_registry(host.project_root)
        return host, {
            key: state[key]
            for key in (
                "path",
                "branch",
                "base_commit",
                "change_id",
                "primary_worktree",
            )
        }
    if mutation and not host.allow_primary_worktree:
        if task.get("_issue_recovery"):
            raise SpecError(
                "pending Issue disposition must recover in its owning worktree; do not create another candidate",
                "workspace_mismatch",
            )
        if primary is None:
            raise SpecError(
                "mutations require a committed Git worktree", "workspace_mismatch"
            )
        # Preparing a worktree is a handoff, never permission to continue the
        # originating agent conversation against a different checkout.
        return host, {
            **create_worktree(host.project_root, task, package_root=host.package_root),
            "handoff": True,
        }
    if mutation:
        ensure_change(
            host.project_root,
            task=task,
            change_id=task.get("change_id"),
            allow_primary=True,
        )
    if current is not None:
        refresh_registry(host.project_root)
    return host, None


def _issues_revision(root: Path) -> str:
    from ..issues.store import list_issues

    return digest([(item["id"], item["revision"]) for item in list_issues(root)])


def _implementation_digest(repository: SpecRepository, target) -> str:
    """Digest the declared listing entries and the bytes of every file they currently bind."""
    return digest(
        {
            "listed": list(target.files),
            "files": [
                (path, digest(read_file(repository.root, path)))
                for path in repository.implementation_files(target)
            ],
        }
    )


def _implementation_users(repository: SpecRepository, target) -> tuple:
    """Every Module whose entries cover one of these entries or bound files, with no context union."""
    affected = {
        target.id,
        *(module.id for module in repository.covering_modules(target)),
    }
    return tuple(
        module for module in repository.targets.values() if module.id in affected
    )


def _unconfirmed_files(repository: SpecRepository, target) -> list[str]:
    """Listed entries that neither exist nor are explicitly declared pending by their entity."""
    entities = repository.entity_files(target)
    return sorted(
        entry
        for entry in repository.missing_entries(target)
        if entry not in entities or entry not in entities[entry].pending
    )


def _component_intent(tasks: list[dict]) -> str:
    return "\n\n".join(
        task["description"] + "\nAcceptance: " + task["acceptance"] for task in tasks
    )


def _impact_revisions(repository: SpecRepository, targets) -> list[dict]:
    return [
        {
            "target_id": target.id,
            "spec_digest": _target_revision(repository, target),
            "implementation_digest": _implementation_digest(repository, target),
        }
        for target in targets
    ]


def _target_revision(repository: SpecRepository, target) -> str:
    return digest(
        {
            "target": asdict(target),
            "protocol": repository.config["protocol"],
            "spec_resolution": repository.spec_context(target.id).value,
        }
    )


def _check_revision(repository: SpecRepository, target) -> str:
    inputs = []
    for check_id in target.checks:
        check = repository.checks[check_id]
        inputs.append((check_id, check))
        for relative in check.get("inputs", []):
            path = checked_path(repository.root, relative)
            members = (
                sorted(
                    p.relative_to(repository.root).as_posix()
                    for p in path.rglob("*")
                    if p.is_file()
                    and "__pycache__" not in p.parts
                    and p.suffix not in {".pyc", ".pyo"}
                )
                if path.is_dir()
                else [relative]
            )
            if path.is_dir() and any(p.is_symlink() for p in path.rglob("*")):
                raise SpecError("check input cannot contain symlinks", "unsafe_path")
            inputs.extend(
                (member, digest(read_file(repository.root, member)))
                for member in members
            )
    return digest(
        {
            "implementation": _implementation_digest(repository, target),
            "check_inputs": inputs,
            "execution_policy": CHECK_POLICY,
        }
    )


def _check(repository: SpecRepository, target, invocation_id: str) -> list[dict]:
    """Only the host executes configured argv. Never send stdout/stderr to a Spec-only agent."""
    before = _check_revision(repository, target)
    results = []
    for check_id in target.checks:
        configured = repository.checks[check_id]
        argv = list(configured["argv"])
        if argv[0] == "{python}":
            argv[0] = sys.executable
        failure = None
        status, code = "failed", -1
        try:
            result = execute_check(
                repository.root,
                argv,
                timeout=configured["timeout_seconds"],
                environment={
                    **os.environ,
                    "PYTHONPATH": str(repository.package_root / "src"),
                },
            )
            log = result.stdout + b"\n" + result.stderr
            status = (
                "timeout"
                if result.timed_out
                else ("passed" if result.returncode == 0 else "failed")
            )
            code = result.returncode
        except CheckSandboxError as error:
            log = error.stdout + b"\n" + error.stderr + b"\n" + str(error).encode()
            failure = error
        path = f".concorde/runs/{invocation_id}/{check_id}.log"
        # Logs are host/implementation evidence, absent from non-implementation context manifests.
        destination = checked_path(repository.root, path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(log)
        if failure is not None:
            raise SpecError(
                f"configured check {check_id} requires an enforceable read-only sandbox; "
                f"see host log {path}",
                "check_sandbox_unavailable",
            ) from failure
        results.append(
            {
                "check_id": check_id,
                "target_id": target.id,
                "status": status,
                "exit_code": code,
                "source_digest": before,
                "log_digest": digest(log),
            }
        )
    if _check_revision(repository, target) != before:
        raise SpecError(
            "configured validation changed the implementation it measured",
            "stale_evidence",
        )
    return results


class MainInvocation:
    """Global Module discovery followed by fresh target workers."""

    def __init__(
        self, operation: str, configuration: dict, task: dict, host: OperationHost
    ):
        self.operation, self.configuration, self.task, self.host = (
            operation,
            configuration,
            task,
            host,
        )
        if operation not in DISCOVERY_OPERATIONS:
            raise SpecError(
                "operation does not support main discovery", "unknown_operation"
            )
        self.action = (
            task.get("action", "route") if operation == MAIN_OPERATION else "route"
        )
        self.repository = SpecRepository(host.project_root, host.package_root)
        self.entry = self.repository.select(self.repository.entry_target)
        if self.entry.kind != "module":
            raise SpecError(
                "the project entry target must be a Module for main discovery",
                "invalid_entry_target",
            )
        if task.get("focus_id") and not task.get("target_id"):
            raise SpecError("a focus hint requires a target hint", "invalid_focus")
        if task.get("target_id"):
            self.repository.select(task["target_id"], task.get("focus_id"))
        self.discovered = [self.entry.id]
        self.last_context: str | None = None
        self.last_snapshot: DiscoveryContext | None = None
        self.completed: list[str] = []

    def main_response(
        self,
        outcome: str,
        answer: str = "",
        *,
        routes=(),
        topology_proposal=None,
        application=None,
        files=(),
        blockers=(),
    ) -> dict:
        if self.last_context is None or self.last_snapshot is None:
            raise SpecError(
                "main response has no discovery context", "invalid_completion"
            )
        return typed(
            "concorde-main-response",
            {
                "action": self.action,
                "entry_target": self.entry.id,
                "context_id": self.last_context,
                "outcome": outcome,
                "answer": answer,
                "discovered_targets": list(self.discovered),
                "routes": list(routes),
                "topology_proposal": topology_proposal,
                "application": application,
                "files": list(files),
                "blockers": list(blockers),
                "completed_operations": list(self.completed),
                "workspace": self.last_snapshot.value["workspace"],
            },
        )

    def operation_response(
        self, outcome: str, answer: str = "", *, blockers=()
    ) -> dict:
        if self.last_context is None:
            raise SpecError(
                "main response has no discovery context", "invalid_completion"
            )
        return typed(
            OPERATION_CONTRACTS[self.operation][1],
            {
                "target_id": self.entry.id,
                "focus_id": None,
                "change_id": self.task.get("change_id"),
                "context_id": self.last_context,
                "outcome": outcome,
                "answer": answer,
                "artifacts": [],
                "blockers": list(blockers),
                "checks": [],
                "completed_operations": list(self.completed),
                **({"reviews": []} if self.operation == "concorde-review" else {}),
            },
        )

    def stage(self, phase: str, occurrence: int) -> dict:
        role = DISCOVERY_NODES[self.action]
        prompt = load_model_instructions(self.host.package_root, role)
        agent = worker_profile(prompt.binding.agent)
        snapshot = resolve_discovery_context(
            self.repository,
            tuple(self.discovered),
            operation=self.operation,
            phase=phase,
            task=self.task["task"],
            action=self.action,
            target_hint=self.task.get("target_id"),
            focus_hint=self.task.get("focus_id"),
            constraints=tuple(self.task.get("constraints", [])),
            instructions=prompt.body,
            agent=agent,
        )
        self.last_context = snapshot.id
        self.last_snapshot = snapshot
        before_registry = self.repository.registry_bytes
        with tempfile.TemporaryDirectory(prefix="concorde-discovery-") as directory:
            capsule = Path(directory)
            project_workspace = agent.workspace == "project"
            project = self.host.project_root if project_workspace else capsule
            context_file = capsule / "context.json"
            # The index is written beside byte-identical copies of every document it lists; the
            # worker opens them on demand instead of receiving their bodies in its input.
            granted = context_documents(self.repository, snapshot.value)
            if self.host.mode != "describe-policy":
                context_file.write_text(snapshot.serialized + "\n")
                if not project_workspace:
                    materialize_documents(capsule, granted)
            roles = {prompt.effects.reads[0]: ("context.json", *sorted(granted))}
            try:
                policy = compile_policy(
                    prompt.effects,
                    PolicyBinding(
                        self.operation, phase, occurrence, role, role, write_roles=()
                    ),
                    roles,
                )
            except PermissionPolicyError as error:
                raise SpecError(str(error), "permission_denied") from error
            receipt = {
                "schema_version": 16,
                "entry_target": self.entry.id,
                "phase": phase,
                "context_id": snapshot.id,
                "source_digest": snapshot.id,
                "registry_digest": digest(before_registry),
                "discovered_targets": list(self.discovered),
                "role_paths": {key: list(value) for key, value in roles.items()},
            }
            value = typed(
                "concorde-main-stage-context",
                {
                    "snapshot": typed("concorde-discovery-context", snapshot.value),
                },
            )
            invocation = _worker_invocation(
                self.configuration,
                operation=self.operation,
                stage=phase,
                prompt=prompt,
                workspace=project,
                context_value=value,
                receipt=receipt,
                policy=policy,
                protocol=_protocol_documents(snapshot.value, granted),
            )
            self.host.descriptions.append(
                _worker_description(
                    prompt,
                    invocation,
                    policy,
                    operation=self.operation,
                    phase=phase,
                    context_id=snapshot.id,
                    project_root=str(project),
                    discovered_targets=list(self.discovered),
                )
            )
            if self.host.mode == "describe-policy":
                return {
                    "context_id": snapshot.id,
                    "outcome": "described",
                    "answer": "",
                    "expand_targets": [],
                    "routes": [],
                    "blockers": [],
                }
            from ..harness.operation_node import OperationNode

            result = None

            def launch_worker(context):
                nonlocal result
                result, data = _run_worker(
                    self.host,
                    invocation,
                    prompt,
                    operation=self.operation,
                    stage=phase,
                    target_id=self.entry.id,
                    result_type="concorde-main-stage-result",
                )
                return data

            data = OperationNode(agent.name).invoke(value, launch_worker)
            self._validate_result(snapshot, phase, data)
            if (
                read_file(self.repository.root, self.repository.registry_path)
                != before_registry
            ):
                raise SpecError(
                    "registry changed during main discovery", "stale_context"
                )
            recheck_discovery_context(self.repository, snapshot)
            if load_configuration(self.repository.root) != self.configuration:
                raise SpecError(
                    "configuration changed during main discovery",
                    "configuration_mismatch",
                )
            if context_file.read_text() != snapshot.serialized + "\n":
                raise SpecError("frozen discovery capsule changed", "stale_context")
            self.host.evidence.append(result)
            return data

    def _validate_result(
        self, snapshot: DiscoveryContext, phase: str, data: dict
    ) -> None:
        if data["context_id"] != snapshot.id:
            raise SpecError(
                "main returned a different discovery context identity",
                "incompatible_handoff",
            )
        outcome = data["outcome"]
        expansions, routes, blockers = (
            data["expand_targets"],
            data["routes"],
            data["blockers"],
        )
        topology = data["topology_design"]
        if phase == "route":
            if outcome == "completed":
                if (
                    self.operation != MAIN_OPERATION
                    or self.action != "ask"
                    or expansions
                    or routes
                    or blockers
                    or topology is not None
                    or not data["answer"].strip()
                ):
                    raise SpecError(
                        "direct main answers require only an answer from admitted Spec context or workspace metadata",
                        "invalid_completion",
                    )
            elif outcome == "expand":
                if not expansions or routes or blockers or topology is not None:
                    raise SpecError(
                        "expand requires only nonempty Module targets",
                        "invalid_completion",
                    )
            elif outcome == "routed":
                if (
                    self.action == "ask"
                    or expansions
                    or not routes
                    or blockers
                    or topology is not None
                ):
                    raise SpecError(
                        "routed requires only nonempty worker routes",
                        "invalid_completion",
                    )
            elif outcome == "topology_proposed":
                if (
                    self.action != "design-topology"
                    or expansions
                    or routes
                    or blockers
                    or topology is None
                ):
                    raise SpecError(
                        "topology design has inconsistent fields", "invalid_completion"
                    )
            elif outcome in {"spec_incomplete", "unsupported", "conflicting", "failed"}:
                if (
                    expansions
                    or routes
                    or topology is not None
                    or (outcome == "spec_incomplete" and not blockers)
                ):
                    raise SpecError(
                        "blocked main routing has inconsistent fields",
                        "invalid_completion",
                    )
            else:
                raise SpecError(
                    "route phase returned an unsupported outcome", "invalid_completion"
                )
        else:
            raise SpecError("main returned an unsupported phase", "invalid_completion")
        # _run_worker has admitted every referenced observation against this exact discovery.
        if blockers and outcome in {
            "completed",
            "routed",
            "expand",
            "topology_proposed",
        }:
            raise SpecError(
                "successful discovery cannot retain task blockers", "invalid_completion"
            )

    def discover_routes(self) -> tuple[list[dict], dict | None]:
        from .discovery_graph import build_discovery_graph

        state = build_discovery_graph(self.discovery_nodes().__getitem__).invoke(
            {"occurrence": 0},
            {"recursion_limit": 2 * (len(self.repository.targets) + 1) + 3},
        )
        return state["routes"], state["decision"]

    def discovery_nodes(self):
        routable_targets = sum(
            target.kind == "module" for target in self.repository.targets.values()
        )

        def decide(state):
            occurrence = state.get("occurrence", 0)
            if occurrence > routable_targets:
                raise SpecError("main discovery step limit exceeded", "context_limit")
            decision = self.stage("route", occurrence)
            route = (
                "finish"
                if self.host.mode == "describe-policy"
                else {"expand": "expand_context", "routed": "bind_routes"}.get(
                    decision["outcome"], "finish"
                )
            )
            return {"occurrence": occurrence, "decision": decision, "route": route}

        def expand_context(state):
            decision = state["decision"]
            admitted_text = self.stage_context_text(decision)
            for target_id in decision["expand_targets"]:
                if target_id in self.discovered:
                    raise SpecError(
                        "main discovery requested an already admitted target",
                        "invalid_completion",
                    )
                if (
                    target_id != self.task.get("target_id")
                    and target_id not in admitted_text
                ):
                    raise SpecError(
                        "main discovery requested a target absent from admitted Specs",
                        "incompatible_handoff",
                        target_id,
                    )
                target = self.repository.select(target_id)
                if target.kind != "module":
                    raise SpecError(
                        "main discovery accepts only Module Specs",
                        "permission_denied",
                        target_id,
                    )
                self.discovered.append(target_id)
            return {"occurrence": state["occurrence"] + 1}

        def bind_routes(state):
            decision = state["decision"]
            original_constraints = self.task.get("constraints", [])
            routing_text = self.stage_context_text(decision)
            bound_routes = []
            for index, route in enumerate(decision["routes"]):
                self.repository.select(route["target_id"], route["focus_id"])
                if (
                    route["target_id"] not in self.discovered
                    and route["target_id"] not in routing_text
                ):
                    raise SpecError(
                        "main routed a target absent from admitted Module Specs",
                        "incompatible_handoff",
                        route["target_id"],
                    )
                if self.operation != MAIN_OPERATION:
                    mismatches = [
                        field
                        for field, expected in (
                            ("task", self.task["task"]),
                            ("constraints", original_constraints),
                        )
                        if field in route and route[field] != expected
                    ]
                    if mismatches:
                        fields = ", ".join(
                            f"routes[{index}].{field}" for field in mismatches
                        )
                        raise SpecError(
                            f"main route changed single-target task intent: {fields}",
                            "incompatible_handoff",
                            fields,
                        )
                    route = {
                        **route,
                        "task": self.task["task"],
                        "constraints": list(original_constraints),
                    }
                else:
                    missing = [
                        field for field in ("task", "constraints") if field not in route
                    ]
                    if missing:
                        raise SpecError(
                            f"main route omitted fields: routes[{index}]."
                            + ", ".join(missing),
                            "incompatible_handoff",
                        )
                    if any(
                        item not in route["constraints"]
                        for item in original_constraints
                    ):
                        raise SpecError(
                            f"main route dropped a user constraint: routes[{index}].constraints",
                            "incompatible_handoff",
                        )
                bound_routes.append(route)
            return {"routes": bound_routes, "decision": None}

        def finish(state):
            if self.host.mode == "describe-policy":
                if self.action != "ask" and self.task.get("target_id"):
                    return {
                        "routes": [
                            {
                                "target_id": self.task["target_id"],
                                "focus_id": self.task.get("focus_id"),
                                "task": self.task["task"],
                                "constraints": self.task.get("constraints", []),
                            }
                        ],
                        "decision": None,
                    }
            else:
                self.completed.append("concorde-router-route")
            return {"routes": []}

        nodes = {
            "decide": decide,
            "expand_context": expand_context,
            "bind_routes": bind_routes,
            "finish": finish,
        }
        return nodes

    def stage_context_text(self, decision: dict) -> str:
        """Return only source text bound to the decision's complete context identity."""

        if decision["context_id"] != self.last_context or self.last_snapshot is None:
            raise SpecError(
                "main route no longer matches its discovery context", "stale_context"
            )
        value = self.last_snapshot.value
        granted = context_documents(self.repository, value)
        return "\n".join(
            granted[source["path"]].decode("utf-8") for source in value["documents"]
        )

    def select_one(self) -> tuple[dict | None, dict | None]:
        return self.select_discovered(*self.discover_routes())

    def select_discovered(self, routes, decision) -> tuple[dict | None, dict | None]:
        """Admit the result of this invocation's executed discovery subgraph."""
        if decision is not None:
            outcome = (
                "described"
                if self.host.mode == "describe-policy"
                else decision["outcome"]
            )
            return None, self.operation_response(
                outcome, decision["answer"], blockers=decision["blockers"]
            )
        if len(routes) != 1:
            raise SpecError(
                f"{self.operation} requires one owning target; route cross-target work through a coordinating Module",
                "ambiguous_route",
            )
        self.completed.append("concorde-router-route")
        return routes[0], None

    def run_answer(self) -> dict:
        _, decision = self.discover_routes()
        return self.answer_response(decision)

    def answer_response(self, decision):
        if decision is None:
            raise SpecError(
                "questions require a direct answerer result", "invalid_completion"
            )
        outcome = (
            "described" if self.host.mode == "describe-policy" else decision["outcome"]
        )
        return self.main_response(
            outcome, decision["answer"], blockers=decision["blockers"]
        )

    def run_topology_design(self) -> dict:
        _, decision = self.discover_routes()
        return self.topology_response(decision)

    def topology_response(self, decision):
        if self.host.mode == "describe-policy":
            return self.main_response("described")
        if decision is None or decision["outcome"] != "topology_proposed":
            if decision is None:
                raise SpecError(
                    "topology design returned worker routes", "invalid_completion"
                )
            return self.main_response(
                decision["outcome"], decision["answer"], blockers=decision["blockers"]
            )
        _inspect_topology_design(
            self.repository,
            decision["topology_design"],
            tuple(self.discovered),
        )
        if self.last_snapshot is None:
            raise SpecError(
                "topology design has no admitted discovery snapshot",
                "invalid_completion",
            )
        payload = {
            "base_registry_digest": digest(self.repository.registry_bytes),
            "protocol_binding": self.repository.config["protocol"],
            "context_id": self.last_context,
            "discovered_targets": list(self.discovered),
            "task": self.task["task"],
            "constraints": self.task.get("constraints", []),
            "target_hint": self.task.get("target_id"),
            "focus_hint": self.task.get("focus_id"),
            "design": decision["topology_design"],
            "workspace": self.last_snapshot.value["workspace"],
        }
        proposal = typed(
            "concorde-topology-proposal",
            {
                "proposal_id": digest(payload),
                **payload,
            },
        )
        self.completed.append("concorde-topology-designer-design")
        return self.main_response(
            "topology_proposed", decision["answer"], topology_proposal=proposal
        )


def _inspect_topology_design(
    repository: SpecRepository, design_value: dict, discovered_targets: tuple[str, ...]
) -> tuple[dict, dict, bytes, dict[str, dict], dict[str, dict], dict[str, str]]:
    """Validate everything knowable before target-local document authoring."""

    design = validate_typed(design_value, "concorde-topology-design")["data"]
    candidate = copy.deepcopy(design["registry"])
    if candidate["project_id"] != repository.registry["project_id"]:
        raise SpecError(
            "topology design cannot replace project identity", "invalid_proposal"
        )
    candidate_bytes = (json.dumps(candidate, indent=2, sort_keys=True) + "\n").encode()
    # This validates IDs, parentage, ownership, focus/check references and entry selection without
    # opening the candidate document paths. Their existence/content is validated after authoring.
    try:
        SpecRepository(
            repository.root,
            repository.package_root,
            registry_bytes=candidate_bytes,
            _defer_document_admission=True,
        )
    except SpecError as error:
        raise SpecError(
            "topology candidate registry is invalid: " + str(error),
            "invalid_proposal",
            error.field,
        ) from error
    current_targets = {item["id"]: item for item in repository.registry["targets"]}
    candidate_targets = {item["id"]: item for item in candidate["targets"]}
    tasks = {item["target_id"]: item["task"] for item in design["spec_tasks"]}
    if len(tasks) != len(design["spec_tasks"]):
        raise SpecError(
            "topology design contains duplicate Spec tasks", "invalid_proposal"
        )
    if any(target_id not in candidate_targets for target_id in tasks):
        raise SpecError(
            "topology Spec task names a removed or unknown target", "invalid_proposal"
        )
    changed = {
        target_id
        for target_id, target in candidate_targets.items()
        if current_targets.get(target_id) != target
    }
    changed.update(set(current_targets) - set(candidate_targets))
    current_document_references: dict[str, set[str]] = {}
    candidate_document_references: dict[str, set[str]] = {}
    for target_id, target in current_targets.items():
        for path in target["documents"]:
            current_document_references.setdefault(path, set()).add(target_id)
    for target_id, target in candidate_targets.items():
        for path in target["documents"]:
            candidate_document_references.setdefault(path, set()).add(target_id)
    changed_memberships = {
        path
        for path in set(current_document_references)
        | set(candidate_document_references)
        if current_document_references.get(path, set())
        != candidate_document_references.get(path, set())
    }
    affected_document_targets = set()
    for path in changed_memberships:
        affected_document_targets.update(current_document_references.get(path, set()))
        affected_document_targets.update(candidate_document_references.get(path, set()))
    missing_document_tasks = sorted(
        target_id
        for target_id in affected_document_targets
        if target_id in candidate_targets and target_id not in tasks
    )
    if missing_document_tasks:
        raise SpecError(
            f"changed document ownership requires every retained owner task: {missing_document_tasks}",
            "invalid_proposal",
        )

    def relations(targets):
        result = {
            (target_id, peer)
            for target_id, target in targets.items()
            for peer in target["uses"]
        }
        result.update(
            (target["parent"], target_id)
            for target_id, target in targets.items()
            if target["parent"] is not None
        )
        return result

    affected_modules = {
        owner for owner, _ in relations(current_targets) ^ relations(candidate_targets)
    }
    affected_modules.update(
        finding.subject_id
        for finding in module_dependency_findings(repository)
        if finding.subject_id is not None
    )
    # A Module whose listed files change must rewrite its own entity declarations, and every
    # Module that lists a file whose listing set changed is affected by that shared change.
    current_file_users: dict[str, set[str]] = {}
    candidate_file_users: dict[str, set[str]] = {}
    for target_id, target in current_targets.items():
        for path in target["files"]:
            current_file_users.setdefault(path, set()).add(target_id)
    for target_id, target in candidate_targets.items():
        for path in target["files"]:
            candidate_file_users.setdefault(path, set()).add(target_id)
    affected_modules.update(
        target_id
        for target_id, target in candidate_targets.items()
        if list(current_targets.get(target_id, {}).get("files", []))
        != list(target["files"])
    )
    for path in set(current_file_users) | set(candidate_file_users):
        if current_file_users.get(path, set()) != candidate_file_users.get(path, set()):
            affected_modules.update(current_file_users.get(path, set()))
            affected_modules.update(candidate_file_users.get(path, set()))
    missing_dependency_tasks = sorted(
        target_id
        for target_id in affected_modules
        if target_id in candidate_targets and target_id not in tasks
    )
    if missing_dependency_tasks:
        raise SpecError(
            f"changed dependencies or shared file listings require Module tasks: {missing_dependency_tasks}",
            "invalid_proposal",
        )
    discovered = set(discovered_targets)
    unread_existing = sorted(
        target_id
        for target_id in (changed | tasks.keys())
        if target_id in current_targets
        and current_targets[target_id]["kind"] == "module"
        and target_id not in discovered
    )
    if unread_existing:
        raise SpecError(
            f"topology design did not admit affected Module Specs: {unread_existing}",
            "invalid_proposal",
        )
    missing_tasks = sorted((changed & candidate_targets.keys()) - tasks.keys())
    if missing_tasks:
        raise SpecError(
            f"changed topology targets require local Spec tasks: {missing_tasks}",
            "invalid_proposal",
        )
    if candidate == repository.registry and not tasks:
        raise SpecError("topology proposal contains no change", "invalid_proposal")
    return design, candidate, candidate_bytes, current_targets, candidate_targets, tasks


def _validate_topology_proposal(
    host: OperationHost, proposal: dict
) -> tuple[SpecRepository, dict]:
    value = validate_typed(proposal, "concorde-topology-proposal")
    data = value["data"]
    identity = {key: item for key, item in data.items() if key != "proposal_id"}
    if digest(identity) != data["proposal_id"]:
        raise SpecError("topology proposal identity is invalid", "invalid_proposal")
    repository = SpecRepository(host.project_root, host.package_root)
    if digest(repository.registry_bytes) != data["base_registry_digest"]:
        raise SpecError("topology proposal registry base changed", "stale_proposal")
    if repository.config["protocol"] != data["protocol_binding"]:
        raise SpecError("topology proposal Protocol binding changed", "stale_proposal")
    prompt = load_model_instructions(
        host.package_root, DISCOVERY_NODES["design-topology"]
    )
    snapshot = resolve_discovery_context(
        repository,
        tuple(data["discovered_targets"]),
        operation=MAIN_OPERATION,
        phase="route",
        action="design-topology",
        task=data["task"],
        target_hint=data["target_hint"],
        focus_hint=data["focus_hint"],
        constraints=tuple(data["constraints"]),
        instructions=prompt.body,
        workspace=data["workspace"],
    )
    if snapshot.id != data["context_id"]:
        raise SpecError("topology proposal discovery context changed", "stale_proposal")
    return repository, value


def _topology_author(
    repository: SpecRepository,
    configuration: dict,
    host: OperationHost,
    target: dict,
    task: str,
    occurrence: int,
    candidate_document_references: tuple[dict, ...],
    candidate_repository: SpecRepository | None = None,
) -> dict:
    role = TOPOLOGY_AUTHOR_NODE
    prompt = load_model_instructions(host.package_root, role)
    agent = worker_profile(prompt.binding.agent)
    snapshot = resolve_topology_author_context(
        repository,
        target,
        task=task,
        instructions=prompt.body,
        candidate_document_references=candidate_document_references,
        candidate_repository=candidate_repository,
    )
    before_registry = repository.registry_bytes
    with tempfile.TemporaryDirectory(prefix="concorde-topology-author-") as directory:
        capsule = Path(directory)
        project_workspace = agent.workspace == "project"
        project = host.project_root if project_workspace else capsule
        context_file = capsule / "context.json"
        granted = context_documents(
            repository, snapshot.value, candidate_repository=candidate_repository
        )
        if host.mode != "describe-policy":
            context_file.write_text(snapshot.serialized + "\n")
            if not project_workspace:
                materialize_documents(capsule, granted)
        roles = {prompt.effects.reads[0]: ("context.json", *sorted(granted))}
        try:
            policy = compile_policy(
                prompt.effects,
                PolicyBinding(
                    MAIN_OPERATION,
                    "topology-author",
                    occurrence,
                    role,
                    role,
                    write_roles=(),
                ),
                roles,
            )
        except PermissionPolicyError as error:
            raise SpecError(str(error), "permission_denied") from error
        receipt = {
            "schema_version": 16,
            "target_id": target["id"],
            "phase": "topology-author",
            "context_id": snapshot.id,
            "source_digest": snapshot.id,
            "registry_digest": digest(before_registry),
            "role_paths": {k: list(v) for k, v in roles.items()},
        }
        runtime = typed("concorde-topology-author-context", snapshot.value)
        invocation = _worker_invocation(
            configuration,
            operation=MAIN_OPERATION,
            stage="topology-author",
            prompt=prompt,
            workspace=project,
            context_value=runtime,
            receipt=receipt,
            policy=policy,
            protocol=_protocol_documents(snapshot.value, granted),
        )
        host.descriptions.append(
            _worker_description(
                prompt,
                invocation,
                policy,
                operation=MAIN_OPERATION,
                phase="topology-author",
                target_id=target["id"],
                context_id=snapshot.id,
                project_root=str(project),
            )
        )
        if host.mode == "describe-policy":
            return {
                "context_id": snapshot.id,
                "target_id": target["id"],
                "outcome": "completed",
                "answer": "",
                "blockers": [],
                "documents": [],
            }
        from ..harness.operation_node import OperationNode

        result = None

        def launch_author(context):
            nonlocal result
            result, data = _run_worker(
                host,
                invocation,
                prompt,
                operation=MAIN_OPERATION,
                stage="topology-author",
                target_id=target["id"],
                result_type="concorde-topology-author-result",
            )
            return data

        data = OperationNode(agent.name).invoke(runtime, launch_author)
        if data["context_id"] != snapshot.id or data["target_id"] != target["id"]:
            raise SpecError(
                "topology author returned a different target/context",
                "incompatible_handoff",
            )
        if (data["outcome"] == "spec_incomplete" and not data["blockers"]) or (
            data["outcome"] == "completed" and data["blockers"]
        ):
            raise SpecError(
                "topology author blockers do not match its outcome",
                "invalid_completion",
            )
        paths = [item["path"] for item in data["documents"]]
        if data["outcome"] == "completed":
            if paths != [
                member
                for path in target["documents"]
                for member in (path, path + ".json")
            ]:
                raise SpecError(
                    "topology author must return every target document in order",
                    "invalid_completion",
                )
        elif data["documents"]:
            raise SpecError(
                "blocked topology author cannot return document replacements",
                "invalid_completion",
            )
        if read_file(repository.root, repository.registry_path) != before_registry:
            raise SpecError(
                "registry changed during topology authoring", "stale_context"
            )
        recheck_topology_author_context(
            repository, snapshot, candidate_repository=candidate_repository
        )
        if load_configuration(repository.root) != configuration:
            raise SpecError(
                "configuration changed during topology authoring",
                "configuration_mismatch",
            )
        if context_file.read_text() != snapshot.serialized + "\n":
            raise SpecError(
                "topology author changed its frozen context", "stale_context"
            )
        host.evidence.append(result)
        return data


def _main_topology_response(
    action: str,
    repository: SpecRepository,
    proposal: dict,
    *,
    outcome: str,
    answer: str,
    application=None,
    files=(),
    blockers=(),
    completed=(),
) -> dict:
    data = proposal["data"]
    design = data["design"]["data"]
    return typed(
        "concorde-main-response",
        {
            "action": action,
            "entry_target": design["registry"]["entry_target"],
            "context_id": data["context_id"],
            "outcome": outcome,
            "answer": answer,
            "discovered_targets": data["discovered_targets"],
            "routes": [],
            "topology_proposal": proposal if action == "accept-topology" else None,
            "application": application,
            "files": list(files),
            "blockers": list(blockers),
            "completed_operations": list(completed),
            "workspace": workspace_context(repository.root),
        },
    )


def _review_candidate_contexts(
    repository,
    candidate,
    configuration,
    host,
    intent,
    constraints,
    completed,
    records: dict | None = None,
    change_id: str | None = None,
    owner_id: str | None = None,
    focus_id: str | None = None,
):
    """Review changed complete contexts before any proposed source bytes are applied.

    Each completed review is collected in ``records`` under the exact intent the later Spec-review
    stage uses for that context: the owner (``owner_id``) under the authoring task itself and every
    consumer under the consumer intent. Once the candidate bytes are applied they equal the reviewed
    bytes, so the stage can recheck and reuse this revision-bound evidence instead of reviewing the
    identical context a second time.
    """
    from .review import consumer_intent, review

    def review_context(target_id):
        if target_id not in candidate.targets:
            return None
        owner = target_id == owner_id
        task = {
            "target_id": target_id,
            "review_mode": "spec",
            "task": intent if owner else consumer_intent(intent),
            "constraints": constraints,
            **({"focus_id": focus_id} if owner and focus_id else {}),
            **({"change_id": change_id} if change_id else {}),
        }
        reviewer = Invocation(
            "concorde-review",
            configuration,
            task,
            replace(host, coordinated=True, track_gaps=False),
            candidate_repository=candidate,
        )
        result = review(reviewer, "spec")["data"]
        if (
            records is not None
            and result["outcome"] == "completed"
            and result["reviews"]
        ):
            reference = next(
                (
                    ref
                    for ref in result["artifacts"]
                    if ref["id"] == f"review.{target_id}.spec"
                ),
                None,
            )
            evidence = result["reviews"][0]["data"]
            if reference is not None:
                records[target_id] = {
                    "artifact": reference,
                    "task": task["task"],
                    "constraints": list(constraints),
                    "focus_id": task.get("focus_id"),
                    "input_digest": evidence["input_digest"],
                    "status": evidence["status"],
                }
        if result["blockers"] or result["outcome"] == "completed":
            from ..harness.change_worktree import record_task_gaps

            evidence = result["reviews"][0]["data"] if result["reviews"] else None
            record_task_gaps(
                repository.root,
                target_id,
                task["task"],
                "spec-review",
                result["blockers"],
                _target_revision(candidate, candidate.select(target_id)),
                review_input_digest=evidence["input_digest"] if evidence else None,
                spec_resolution=candidate.spec_context(target_id).value,
            )
        if result["outcome"] != "completed":
            return result
        completed.append("concorde-review")

    from ..harness.batch_graph import run_batch_graph

    return run_batch_graph(
        repository.affected_contexts(candidate),
        review_context,
        name="candidate_review_graph",
        item_node="review_module",
    )


def _prepare_topology(configuration: dict, proposal: dict, host: OperationHost) -> dict:
    from .topology_graph import build_topology_graph

    author_count = len(
        proposal.get("data", {}).get("design", {}).get("data", {}).get("spec_tasks", [])
    )
    return build_topology_graph(
        _topology_nodes(configuration, proposal, host).__getitem__
    ).invoke({}, {"recursion_limit": max(25, author_count + 8)})["output"]


def _topology_nodes(configuration, proposal, host):
    from langgraph.graph import END

    repository = candidate_bytes = candidate_targets = candidate_repository = None
    proposals = completed = candidate_references = ordered_authors = authored = None

    def prepare_authors(state):
        nonlocal repository, proposal, candidate_bytes, candidate_targets
        nonlocal proposals, completed, candidate_references, ordered_authors
        if host.mode == "execute":
            progress(
                host.project_root,
                phase="topology_authoring",
                status="active",
                invalidate=True,
            )
        repository, proposal = _validate_topology_proposal(host, proposal)
        (
            design,
            candidate,
            candidate_bytes,
            current_targets,
            candidate_targets,
            tasks,
        ) = _inspect_topology_design(
            repository,
            proposal["data"]["design"],
            tuple(proposal["data"]["discovered_targets"]),
        )
        proposals = {}
        completed = ["concorde-topology-designer-design"]
        candidate_references = {}
        for candidate_target in candidate["targets"]:
            for path in candidate_target["documents"]:
                candidate_references.setdefault(path, []).append(candidate_target["id"])
                candidate_references.setdefault(path + ".json", []).append(
                    candidate_target["id"]
                )
        # Stage known provider authors before their consumers so candidate inventory additions
        # are available through explicit references. Cycles retain declared task order.
        pending_authors = dict(tasks)
        ordered_authors = []
        document_ids = repository._document_index()
        while pending_authors:

            def providers(target_id):
                assert (
                    candidate_references is not None and candidate_targets is not None
                ), "Graph node requires admitted predecessor state"
                selected = set()
                for reference in candidate_targets[target_id]["references"]:
                    if reference["kind"] == "module":
                        selected.add(reference["id"])
                    elif (
                        reference["kind"] == "document"
                        and reference["id"] in document_ids
                    ):
                        selected.update(
                            candidate_references.get(document_ids[reference["id"]], [])
                        )
                return selected

            ready = next(
                (
                    key
                    for key in pending_authors
                    if not providers(key) & pending_authors.keys()
                ),
                next(iter(pending_authors)),
            )
            ordered_authors.append((ready, pending_authors.pop(ready)))
        return {
            "occurrence": 0,
            "route": "author_module" if ordered_authors else "validate_candidate",
        }

    def author_module(state):
        assert (
            candidate_bytes is not None
            and candidate_references is not None
            and candidate_targets is not None
            and completed is not None
            and ordered_authors is not None
            and proposals is not None
            and repository is not None
        ), "Graph node requires admitted predecessor state"
        occurrence = state["occurrence"]
        target_id, task = ordered_authors[occurrence]
        target = candidate_targets[target_id]
        references = tuple(
            {"path": path, "owner": candidate_references[path][0]}
            for path in target["documents"]
        )
        author_repository = SpecRepository(
            repository.root,
            host.package_root,
            registry_bytes=candidate_bytes,
            document_overrides={
                path: items[0][1].encode() for path, items in proposals.items()
            },
            _defer_document_admission=True,
        )
        result = _topology_author(
            repository,
            configuration,
            host,
            target,
            task,
            occurrence,
            references,
            candidate_repository=author_repository,
        )
        if result["outcome"] != "completed":
            return {
                "output": _main_topology_response(
                    "accept-topology",
                    repository,
                    proposal,
                    outcome=result["outcome"],
                    answer=result["answer"],
                    blockers=result["blockers"],
                    completed=completed,
                ),
                "route": END,
            }
        for item in result["documents"]:
            path = item["path"]
            if (
                path not in repository.source_documents
                and checked_path(repository.root, path).exists()
            ):
                raise SpecError(
                    "topology author cannot replace an unregistered existing file",
                    "permission_denied",
                    path,
                )
            proposals.setdefault(path, []).append((target_id, item["content"]))
        completed.append("concorde-topology-author")
        occurrence += 1
        return {
            "occurrence": occurrence,
            "route": "author_module"
            if occurrence < len(ordered_authors)
            else "validate_candidate",
        }

    def validate_candidate(state):
        nonlocal authored, candidate_repository
        assert (
            candidate_bytes is not None
            and candidate_references is not None
            and completed is not None
            and proposals is not None
            and repository is not None
        ), "Graph node requires admitted predecessor state"
        if host.mode == "describe-policy":
            return {
                "output": _main_topology_response(
                    "accept-topology",
                    repository,
                    proposal,
                    outcome="described",
                    answer="Topology author policies described.",
                    completed=completed,
                ),
                "route": END,
            }
        authored = {}
        for path, items in proposals.items():
            if len(items) != 1 or items[0][0] != candidate_references[path][0]:
                raise SpecError(
                    "only the unique candidate owner may propose document bytes",
                    "permission_denied",
                    path,
                )
            authored[path] = items[0][1]
        overrides = {path: content.encode() for path, content in authored.items()}
        report = validate_repository(
            repository.root,
            package_root=host.package_root,
            registry_bytes=candidate_bytes,
            document_overrides=overrides,
        )
        if report.status != "success":
            raise SpecError(
                "topology candidate validation failed: "
                + "; ".join(finding.message for finding in report.findings),
                "invalid_proposal",
            )
        candidate_repository = SpecRepository(
            repository.root,
            host.package_root,
            registry_bytes=candidate_bytes,
            document_overrides=overrides,
        )
        return {"route": "review_contexts"}

    def review_contexts(state):
        assert (
            candidate_repository is not None
            and completed is not None
            and repository is not None
        ), "Graph node requires admitted predecessor state"
        failure = _review_candidate_contexts(
            repository,
            candidate_repository,
            configuration,
            host,
            proposal["data"]["task"],
            proposal["data"]["constraints"],
            completed,
        )
        if failure is not None:
            return {
                "output": _main_topology_response(
                    "accept-topology",
                    repository,
                    proposal,
                    outcome=failure["outcome"],
                    answer=failure["answer"],
                    blockers=failure["blockers"],
                    completed=completed,
                ),
                "route": END,
            }
        return {"route": "persist_application"}

    def persist_application(state):
        assert (
            authored is not None
            and candidate_bytes is not None
            and completed is not None
            and repository is not None
        ), "Graph node requires admitted predecessor state"
        _validate_topology_proposal(host, proposal)
        changes = [
            file_change(
                repository.root, repository.registry_path, candidate_bytes.decode()
            )
        ]
        changes.extend(
            file_change(repository.root, path, content)
            for path, content in authored.items()
        )
        application_payload = {
            "topology_proposal": proposal,
            "base_registry_digest": digest(repository.registry_bytes),
            "protocol_binding": repository.config["protocol"],
            "files": changes,
        }
        application = typed(
            "concorde-topology-application",
            {"application_id": digest(application_payload), **application_payload},
        )
        relative = (
            ".concorde/topology-proposals/"
            + application["data"]["application_id"][7:]
            + ".json"
        )
        stored = file_change(repository.root, relative, canonical(application) + "\n")
        apply_files(repository.root, [stored], {relative})
        application_ref = artifact(
            repository.root, application["data"]["application_id"], relative
        )
        completed.append("concorde-main-prepare-topology")
        return {
            "output": _main_topology_response(
                "accept-topology",
                repository,
                proposal,
                outcome="topology_prepared",
                answer="Exact topology application prepared for developer review.",
                application=application_ref,
                completed=completed,
            ),
            "route": END,
        }

    nodes = {
        "prepare_authors": prepare_authors,
        "author_module": author_module,
        "validate_candidate": validate_candidate,
        "review_contexts": review_contexts,
        "persist_application": persist_application,
    }
    return nodes


def _apply_topology(application_ref: dict, host: OperationHost) -> dict:
    from .topology_graph import build_topology_apply_graph

    return build_topology_apply_graph(
        _topology_apply_nodes(application_ref, host).__getitem__
    ).invoke({})["output"]


def _topology_apply_nodes(application_ref, host):
    from langgraph.graph import END

    repository = proposal = design = candidate_bytes = files = changed = None

    def admit_application(state):
        nonlocal repository, proposal, design, candidate_bytes, files
        if host.mode == "execute":
            progress(
                host.project_root,
                phase="topology_apply",
                status="active",
                invalidate=True,
            )
        repository = SpecRepository(host.project_root, host.package_root)
        verify_artifacts(repository.root, application_ref)
        raw = read_file(repository.root, application_ref["path"])
        application = validate_typed(
            decode(raw.decode()), "concorde-topology-application"
        )
        data = application["data"]
        identity = {key: item for key, item in data.items() if key != "application_id"}
        if (
            digest(identity) != data["application_id"]
            or application_ref["id"] != data["application_id"]
        ):
            raise SpecError(
                "topology application identity is invalid", "invalid_proposal"
            )
        expected_path = (
            ".concorde/topology-proposals/" + data["application_id"][7:] + ".json"
        )
        if application_ref["path"] != expected_path:
            raise SpecError(
                "topology application is outside the host proposal area",
                "invalid_proposal",
            )
        _, proposal = _validate_topology_proposal(host, data["topology_proposal"])
        if data["base_registry_digest"] != digest(repository.registry_bytes):
            raise SpecError(
                "topology application registry base changed", "stale_proposal"
            )
        if data["protocol_binding"] != repository.config["protocol"]:
            raise SpecError(
                "topology application Protocol binding changed", "stale_proposal"
            )
        design, _, candidate_bytes, _, _, _ = _inspect_topology_design(
            repository,
            proposal["data"]["design"],
            tuple(proposal["data"]["discovered_targets"]),
        )
        files = data["files"]
        registry_files = [
            item for item in files if item["path"] == repository.registry_path
        ]
        if (
            len(registry_files) != 1
            or registry_files[0]["content"].encode() != candidate_bytes
        ):
            raise SpecError(
                "topology application does not contain the exact candidate registry",
                "invalid_proposal",
            )
        task_ids = {item["target_id"] for item in design["spec_tasks"]}
        targets = {item["id"]: item for item in design["registry"]["targets"]}
        expected_documents = {
            member
            for target_id in task_ids
            for path in targets[target_id]["documents"]
            for member in (path, path + ".json")
        }
        actual_documents = {
            item["path"] for item in files if item["path"] != repository.registry_path
        }
        if actual_documents != expected_documents or len(
            {item["path"] for item in files}
        ) != len(files):
            raise SpecError(
                "topology application document set differs from accepted design",
                "invalid_proposal",
            )
        if host.mode == "describe-policy":
            return {
                "output": _main_topology_response(
                    "apply-topology",
                    repository,
                    proposal,
                    outcome="described",
                    answer="Topology application is deterministic and launches no agent.",
                ),
                "route": END,
            }
        return {"route": "validate_application"}

    def validate_application(state):
        assert (
            candidate_bytes is not None and files is not None and repository is not None
        ), "Graph node requires admitted predecessor state"
        overrides = {
            item["path"]: item["content"].encode()
            for item in files
            if item["path"] != repository.registry_path
        }
        report = validate_repository(
            repository.root,
            package_root=host.package_root,
            registry_bytes=candidate_bytes,
            document_overrides=overrides,
        )
        if report.status != "success":
            raise SpecError(
                "topology application validation failed: "
                + "; ".join(finding.message for finding in report.findings),
                "invalid_proposal",
            )
        return {}

    def apply_atomically(state):
        nonlocal changed
        assert (
            candidate_bytes is not None
            and design is not None
            and files is not None
            and proposal is not None
            and repository is not None
        ), "Graph node requires admitted predecessor state"
        allowed = {item["path"] for item in files}

        def verify():
            assert repository is not None, (
                "Graph node requires admitted predecessor state"
            )
            current = validate_repository(
                repository.root, package_root=host.package_root
            )
            if current.status != "success":
                raise SpecError(
                    "applied topology failed validation: "
                    + "; ".join(finding.message for finding in current.findings),
                    "invalid_proposal",
                )

        change = read_change(repository.root)
        transaction = list(files)
        if change is not None:
            owner = design["registry"]["entry_target"]
            if change["target_id"] is not None and (
                change["target_id"] != owner
                or change["task"] != proposal["data"]["task"]
                or change["constraints"] != proposal["data"]["constraints"]
            ):
                raise SpecError(
                    "topology application differs from this worktree's owning task",
                    "incompatible_handoff",
                )
            change.update(
                target_id=owner,
                focus_id=None,
                task=proposal["data"]["task"],
                constraints=proposal["data"]["constraints"],
                phase="specified",
                status="active",
                outcome="topology_applied",
                blockers=[],
            )
            candidate_repository = SpecRepository(
                repository.root,
                host.package_root,
                registry_bytes=candidate_bytes,
                document_overrides={
                    item["path"]: item["content"].encode()
                    for item in files
                    if item["path"] != repository.registry_path
                },
            )
            impacts = change.setdefault("spec_context_impacts", {})
            impacts[owner] = sorted(
                set(impacts.get(owner, []))
                | set(repository.affected_contexts(candidate_repository))
            )
            change["validated_tree"] = None
            change["validation"] = None
            transaction.append(
                file_change(repository.root, STATE_PATH, canonical(change) + "\n")
            )
            allowed.add(STATE_PATH)
        changed = [
            path
            for path in apply_files(
                repository.root, transaction, allowed, verify=verify
            )
            if path != STATE_PATH
        ]
        if change is not None:
            refresh_registry(repository.root)
        return {}

    def cleanup(state):
        assert (
            changed is not None and proposal is not None and repository is not None
        ), "Graph node requires admitted predecessor state"
        try:
            checked_path(repository.root, application_ref["path"]).unlink()
            proposal_dir = checked_path(repository.root, ".concorde/topology-proposals")
            if proposal_dir.is_dir() and not any(proposal_dir.iterdir()):
                proposal_dir.rmdir()
        except OSError:
            # The application is already committed; stale host artifacts remain ignored and digest-bound.
            pass
        return {
            "output": _main_topology_response(
                "apply-topology",
                SpecRepository(repository.root, host.package_root),
                proposal,
                outcome="topology_applied",
                answer="Accepted topology application applied atomically.",
                files=changed,
                completed=("concorde-main-apply-topology",),
            ),
            "route": END,
        }

    nodes = {
        "admit_application": admit_application,
        "validate_application": validate_application,
        "apply_atomically": apply_atomically,
        "cleanup": cleanup,
    }
    return nodes


class Invocation:
    def __init__(
        self,
        operation: str,
        configuration: dict,
        task: dict,
        host: OperationHost,
        *,
        candidate_repository: SpecRepository | None = None,
    ):
        self.operation, self.configuration, self.task, self.host = (
            operation,
            configuration,
            task,
            host,
        )
        self.candidate_review = candidate_repository is not None
        if candidate_repository is not None and (
            operation != "concorde-review"
            or task.get("review_mode") != "spec"
            or candidate_repository.root != host.project_root.resolve()
            or candidate_repository.package_root != host.package_root.resolve()
        ):
            raise SpecError(
                "candidate overlays are limited to the bound read-only Spec review",
                "permission_denied",
            )
        self.repository = candidate_repository or SpecRepository(
            host.project_root, host.package_root
        )
        self.target = self.repository.select(task["target_id"], task.get("focus_id"))
        change = read_change(host.project_root)
        if task.get("change_id") is not None and (
            change is None or task["change_id"] != change["change_id"]
        ):
            raise SpecError(
                "change identity does not belong to the current worktree",
                "incompatible_handoff",
            )
        self.change_id = task.get("change_id") or (
            change["change_id"] if change else None
        )
        self.work_directory = f"{WORK_PATH}/{self.target.id}" if change else None
        self.last_context = None
        self.completed: list[str] = []

    def response(
        self,
        outcome="completed",
        answer="",
        *,
        blockers=(),
        checks=(),
        artifacts=(),
        reviews=(),
    ) -> dict:
        data = {
            "target_id": self.target.id,
            "focus_id": self.task.get("focus_id"),
            "change_id": self.change_id,
            "context_id": self.last_context,
            "outcome": outcome,
            "answer": answer,
            "blockers": list(blockers),
            "checks": list(checks),
            "artifacts": list(artifacts),
            "completed_operations": list(self.completed),
        }
        if self.operation == "concorde-review":
            data["reviews"] = list(reviews)
        if self.operation == "concorde-issues":
            data.update(issues=[], decision=None)
        return typed(OPERATION_CONTRACTS[self.operation][1], data)

    def blocker_revision(self, phase):
        spec = _target_revision(self.repository, self.target)
        return (
            digest(
                {
                    "spec": spec,
                    "code": _implementation_digest(self.repository, self.target),
                }
            )
            if phase in {"implementation", "code-review"}
            else spec
        )

    def record_gaps(self, phase, blockers, *, review_input_digest=None):
        if getattr(self, "candidate_review", False):
            return
        if self.host.mode != "execute":
            return
        change = read_change(self.repository.root)
        required_review = bool(
            phase in {"spec-review", "code-review"}
            and change
            and change.get("review_requirements", {})
            .get(self.target.id, {})
            .get(phase.split("-")[0])
            and change.get("review_intents", {}).get(self.target.id)
            == {
                "task": self.task["task"],
                "focus_id": self.task.get("focus_id"),
                "constraints": self.task.get("constraints", []),
            }
        )
        if (
            self.host.track_gaps
            or required_review
            or self.operation
            not in {"concorde-main", "concorde-context-solve", "concorde-review"}
        ):
            from ..harness.change_worktree import record_task_gaps

            record_task_gaps(
                self.repository.root,
                self.target.id,
                self.task["task"],
                phase,
                blockers,
                self.blocker_revision(phase),
                review_input_digest=review_input_digest,
                spec_resolution=self.repository.spec_context(self.target.id).value,
            )

    def pending_gaps(
        self,
        phase,
        snapshot=None,
        *,
        include_prerequisites=True,
        review_input_digest=None,
    ):
        if getattr(self, "candidate_review", False):
            return []
        from ..harness.change_worktree import unchanged_task_gaps

        if phase == "specify" or self.host.mode != "execute":
            return []
        blockers = unchanged_task_gaps(
            self.repository.root,
            self.target.id,
            self.task["task"],
            phase,
            self.blocker_revision(phase),
            review_input_digest=review_input_digest,
        )
        if include_prerequisites:
            order = (
                "specify",
                "spec-review",
                "context-solve",
                "plan",
                "tasks",
                "implementation",
                "code-review",
            )
            prerequisites = (
                set(order[: order.index(phase)]) if phase in order else set()
            )
            change = read_change(self.repository.root)
            blockers.extend(
                dict(item["blocker"])
                for item in (change or {}).get("issue_blockers", [])
                if item["status"] == "open"
                and item["target_id"] == self.target.id
                and item["scope_id"]
                == blocker_scope(change or {}, self.target.id, self.task["task"])
                and item["phase"] in prerequisites
            )
        # No reviewer ran again. Retain the actual observation's provenance.
        return blockers

    def stage(
        self,
        operation: str,
        *,
        inputs: tuple[dict, ...] = (),
        readonly=False,
        defer_gap_resolution=False,
        mode: str | None = None,
    ) -> dict:
        phase, role = MODEL_STAGES[operation]
        if self.host.issue_intent and operation != "concorde-issues":
            inputs = (
                *inputs,
                typed("concorde-issue-intent", {"intent": self.host.issue_intent}),
            )
        if mode not in {None, phase}:
            raise SpecError("unsupported stage worker selection", "invalid_input")
        prompt = load_model_instructions(self.host.package_root, role)
        agent = worker_profile(prompt.binding.agent)
        reviews = [
            value for value in inputs if value["type_id"] == "concorde-review-result"
        ]
        if reviews:
            from ..issues.references import observation_context

            inputs = (
                *inputs,
                observation_context(self.repository.root, reviews[0]["data"]["issues"]),
            )
        snapshot = resolve_context(
            self.repository,
            self.target.id,
            phase=phase,
            task=self.task["task"],
            focus_id=self.task.get("focus_id"),
            constraints=tuple(self.task.get("constraints", [])),
            instructions=prompt.body,
            stage_inputs=inputs,
            agent=agent,
        )
        self.last_context = snapshot.id
        if self.operation not in {"concorde-main", "concorde-context-solve"}:
            pending = self.pending_gaps(
                phase, snapshot, include_prerequisites=not readonly
            )
            if pending:
                return {
                    "context_id": snapshot.id,
                    "outcome": "spec_incomplete",
                    "answer": "Repair the recorded necessary contracts before resuming this step.",
                    "blockers": pending,
                    "documents": [],
                    "plan": "",
                    "tasks": [],
                }
        implementation = phase == "implementation"
        if implementation and not self.target.files:
            raise SpecError(
                "implementation requires a Module whose entities list implementation files",
                "unsupported_target",
            )
        if self.host.mode != "describe-policy" and phase == "context-solve":
            participant_findings = module_dependency_findings(
                self.repository, self.target.id
            )
            if participant_findings:
                self.completed.append(operation)
                conflicts = [
                    finding
                    for finding in participant_findings
                    if not finding.message.startswith(
                        "missing local dependency promises:"
                    )
                ]
                if conflicts:
                    return {
                        "context_id": snapshot.id,
                        "outcome": "conflicting",
                        "answer": "Module dependency promises conflicts with its registered topology: "
                        + "; ".join(finding.message for finding in conflicts),
                        "blockers": [],
                        "documents": [],
                        "plan": "",
                        "tasks": [],
                    }
                from ..issues.store import report_issue

                blockers = []
                for finding in participant_findings:
                    receipt = report_issue(
                        self.repository.root,
                        {
                            "report_key": digest(
                                [self.target.id, finding.rule_id, finding.message]
                            ),
                            "type": "gap",
                            "subtype": "missing-contract",
                            "title": "Missing dependency promise",
                            "description": finding.message,
                            "impact": "Context assessment cannot admit planning.",
                            "basis": finding.remediation,
                            "owner_target_id": self.target.id,
                            "evidence": [],
                        },
                        {
                            "invocation_id": self.host.invocation_id,
                            "agent": "host",
                            "operation": operation,
                            "phase": phase,
                            "target_id": self.target.id,
                            "context_id": snapshot.id,
                            "change_id": self.change_id,
                            "head": None,
                        },
                    )
                    blockers.append(
                        {
                            **receipt,
                            "blocked_step": "Assess context sufficiency before Module planning",
                        }
                    )
                self.record_gaps(phase, blockers)
                return {
                    "context_id": snapshot.id,
                    "outcome": "spec_incomplete",
                    "answer": "Module dependency promises is incomplete or inconsistent.",
                    "blockers": blockers,
                    "documents": [],
                    "plan": "",
                    "tasks": [],
                }
        before_registry = self.repository.registry_bytes
        with tempfile.TemporaryDirectory(prefix="concorde-context-") as directory:
            capsule = Path(directory)
            # Spec-only tasks see a private capsule, not a repository or inherited conversation.
            project_workspace = agent.workspace == "project"
            project = self.host.project_root if project_workspace else capsule
            if project_workspace:
                relative = f".concorde/runs/{self.host.invocation_id}/{uuid.uuid4()}/context.json"
                context_file = checked_path(project, relative)
            else:
                relative, context_file = "context.json", capsule / "context.json"
            if self.host.mode != "describe-policy":
                context_file.parent.mkdir(parents=True, exist_ok=True)
                context_file.write_text(snapshot.serialized + "\n")
            # Spec context is the index above plus the read-only grant of every document and Protocol
            # file it lists: copied byte for byte into a capsule, granted in place in a workspace.
            granted = context_documents(self.repository, snapshot.value)
            if not project_workspace and self.host.mode != "describe-policy":
                materialize_documents(capsule, granted)
            roles: dict[str, tuple[str, ...]] = {
                "spec-context": (relative, *sorted(granted))
            }
            if project_workspace:
                roles["implementation"] = (
                    self.repository.implementation_files(self.target)
                    if readonly
                    else self.repository.implementation_paths(self.target)
                )
            if "references" in prompt.effects.reads:
                # Resource context: the Module's external references, read-only. A capsule
                # receives byte-identical copies of their readable files at the same paths.
                records = snapshot.value["external_references"]
                if not project_workspace and self.host.mode != "describe-policy":
                    materialize_references(self.repository, capsule, records)
                roles["references"] = reference_grants(records)
            write_roles = ("implementation",) if implementation and not readonly else ()
            try:
                policy = compile_policy(
                    prompt.effects,
                    PolicyBinding(
                        operation, phase, 0, role, role, write_roles=write_roles
                    ),
                    roles,
                )
            except PermissionPolicyError as error:
                raise SpecError(str(error), "permission_denied") from error
            receipt = {
                "schema_version": 16,
                "target_id": self.target.id,
                "phase": phase,
                "context_id": snapshot.id,
                "source_digest": snapshot.id,
                "registry_digest": digest(before_registry),
                "role_paths": {k: list(v) for k, v in roles.items()},
            }
            value = typed(
                "concorde-agent-stage-context",
                {
                    "snapshot": typed("concorde-context-snapshot", snapshot.value),
                    "change_id": self.change_id,
                    "expected_artifacts": [],
                },
            )
            invocation = _worker_invocation(
                self.configuration,
                operation=operation,
                stage=phase,
                prompt=prompt,
                workspace=project,
                context_value=value,
                receipt=receipt,
                policy=policy,
                protocol=_protocol_documents(snapshot.value, granted),
            )
            self.host.descriptions.append(
                _worker_description(
                    prompt,
                    invocation,
                    policy,
                    operation=operation,
                    phase=phase,
                    context_id=snapshot.id,
                    project_root=str(project),
                )
            )
            if self.host.mode == "describe-policy":
                return {
                    "context_id": snapshot.id,
                    "outcome": "completed",
                    "answer": "",
                    "blockers": [],
                    "documents": [],
                    "plan": "",
                    "tasks": [],
                }
            from ..harness.operation_node import OperationNode

            result = None
            checks = (
                _check_service(self.repository, self.target, self.host.invocation_id)
                if project_workspace
                else None
            )

            def launch_agent(context):
                # The OperationNode's typed state carries the admitted context in and the validated
                # result out; the Pi worker launch and its admission checks stay host-private.
                nonlocal result
                result, data = _run_worker(
                    self.host,
                    invocation,
                    prompt,
                    operation=operation,
                    stage=phase,
                    target_id=self.target.id,
                    result_type="concorde-agent-stage-result",
                    change_id=self.change_id,
                    checks=checks,
                )
                return data

            data = OperationNode(agent.name).invoke(value, launch_agent)
            if data["context_id"] != snapshot.id:
                raise SpecError(
                    "agent returned a different context identity",
                    "incompatible_handoff",
                )
            if (data["outcome"] == "spec_incomplete" and not data["blockers"]) or (
                data["outcome"] in {"completed", "sufficient"} and data["blockers"]
            ):
                raise SpecError(
                    "stage outcome does not match its task blockers",
                    "invalid_completion",
                )
            if (
                read_file(self.repository.root, self.repository.registry_path)
                != before_registry
            ):
                raise SpecError(
                    "registry changed during agent execution", "stale_context"
                )
            recheck_context(
                self.repository,
                snapshot,
                check_implementation=not implementation or readonly,
            )
            if load_configuration(self.repository.root) != self.configuration:
                raise SpecError(
                    "configuration changed during agent execution",
                    "configuration_mismatch",
                )
            if context_file.read_text() != snapshot.serialized + "\n":
                raise SpecError("frozen context capsule changed", "stale_context")
            if phase != "specify" and data["documents"]:
                # There is no Implementation Spec any more: only the Spec author writes Spec text.
                raise SpecError(
                    "this phase cannot author Spec documents", "permission_denied"
                )
            if implementation and not readonly:
                current = SpecRepository(self.repository.root, self.host.package_root)
                self.repository = current
                self.target = current.select(self.target.id)
            self.host.evidence.append(result)
            self.completed.append(operation)
            if (
                data["blockers"]
                or not defer_gap_resolution
                and data["outcome"] in {"completed", "sufficient"}
            ):
                self.record_gaps(phase, data["blockers"])
            return data

    def author(self, operation: str) -> dict:
        before_contexts = self.repository.context_identities()
        if not self.host.coordinated:
            progress(
                self.repository.root, phase="specify", status="active", invalidate=True
            )
        result = self.stage(operation, defer_gap_resolution=True)
        if result["outcome"] not in {"completed", "sufficient"}:
            return self.response(
                result["outcome"], result["answer"], blockers=result["blockers"]
            )
        if self.host.mode == "describe-policy":
            return self.response("described")
        if result["documents"]:
            if len({item["path"] for item in result["documents"]}) != len(
                result["documents"]
            ):
                raise SpecError(
                    "Spec author repeats a source member", "invalid_completion"
                )
            if any(
                item["path"] not in self.target.sources for item in result["documents"]
            ):
                raise SpecError(
                    "Spec author returned a source outside its target",
                    "permission_denied",
                )
            changes = [
                file_change(self.repository.root, item["path"], item["content"])
                for item in result["documents"]
                if item["content"].encode()
                != read_file(self.repository.root, item["path"])
            ]
            overlay = {item["path"]: item["content"].encode() for item in changes}
            candidate_repository = SpecRepository(
                self.repository.root,
                self.host.package_root,
                document_overrides=overlay,
                _defer_document_admission=True,
            )
            for path in self.target.documents:
                current_document = self.repository.document(path)
                candidate_document = candidate_repository.document(path)
                if (candidate_document.document_id, candidate_document.owner) != (
                    current_document.document_id,
                    current_document.owner,
                ):
                    raise SpecError(
                        "document identity and ownership require a topology change",
                        "permission_denied",
                        path,
                    )

            def verify():
                current = SpecRepository(self.repository.root, self.host.package_root)
                current.documents(current.select(self.target.id))
                current.contracts(current.select(self.target.id))
                document_findings = document_context_findings(current)
                if document_findings:
                    raise SpecError(
                        "authored Spec document context is invalid: "
                        + "; ".join(finding.message for finding in document_findings),
                        "invalid_spec",
                    )
                participant_findings = module_dependency_findings(
                    current, self.target.id
                )
                if participant_findings:
                    raise SpecError(
                        "authored Module dependency promises is invalid: "
                        + "; ".join(
                            finding.message for finding in participant_findings
                        ),
                        "invalid_spec",
                    )
                from ..spec.validation import definition_findings, module_findings

                source_findings = tuple(
                    finding
                    for finding in (
                        *module_findings(current, self.target.id),
                        *definition_findings(current, self.target.id),
                    )
                    if finding.severity == "error"
                )
                if source_findings:
                    raise SpecError(
                        "authored Module sections, definitions or architecture are invalid: "
                        + "; ".join(f.message for f in source_findings),
                        "invalid_spec",
                    )

            if changes:
                candidate = SpecRepository(
                    self.repository.root,
                    self.host.package_root,
                    document_overrides={
                        item["path"]: item["content"].encode() for item in changes
                    },
                )
                consumer_records: dict = {}
                if set(self.repository.affected_contexts(candidate)) - {self.target.id}:
                    failure = _review_candidate_contexts(
                        self.repository,
                        candidate,
                        self.configuration,
                        self.host,
                        self.task["task"],
                        self.task.get("constraints", []),
                        self.completed,
                        records=consumer_records,
                        change_id=self.change_id,
                        owner_id=self.target.id,
                        focus_id=self.task.get("focus_id"),
                    )
                    if failure is not None:
                        return self.response(
                            failure["outcome"],
                            failure["answer"],
                            blockers=failure["blockers"],
                            artifacts=failure["artifacts"],
                        )
                if (
                    read_file(self.repository.root, self.repository.registry_path)
                    != self.repository.registry_bytes
                ):
                    raise SpecError(
                        "registry changed during canonical document review",
                        "stale_context",
                    )
                apply_files(
                    self.repository.root,
                    changes,
                    set(self.target.sources),
                    verify=verify,
                )
                self.repository = SpecRepository(
                    self.host.project_root, self.host.package_root
                )
                if consumer_records and self.host.mode == "execute":
                    # The applied bytes equal the reviewed candidate bytes, so these reviews stay
                    # revision-bound; the Spec-review stage rechecks each one before reuse.
                    state = read_change(self.repository.root)
                    if state is not None:
                        owner_record = consumer_records.pop(self.target.id, None)
                        intent = {
                            "task": self.task["task"],
                            "focus_id": self.task.get("focus_id"),
                            "constraints": self.task.get("constraints", []),
                        }
                        if (
                            owner_record is not None
                            and state.get("review_intents", {}).get(self.target.id)
                            == intent
                        ):
                            state.setdefault("reviews", {}).setdefault(
                                self.target.id, {}
                            )["spec"] = {
                                "artifact": owner_record["artifact"],
                                "input_digest": owner_record["input_digest"],
                                "status": owner_record["status"],
                                **intent,
                            }
                        shared = state.setdefault("shared_spec_reviews", {}).setdefault(
                            self.target.id, {}
                        )
                        shared.update(
                            {
                                key: {
                                    "artifact": value["artifact"],
                                    "task": value["task"],
                                    "constraints": value["constraints"],
                                }
                                for key, value in consumer_records.items()
                            }
                        )
                        save_change(self.repository.root, state)
        self.record_gaps("specify", [])
        change = read_change(self.repository.root)
        if change is not None:
            after_contexts = self.repository.context_identities()
            affected = {
                key
                for key in before_contexts.keys() | after_contexts.keys()
                if before_contexts.get(key) != after_contexts.get(key)
            }
            impacts = change.setdefault("spec_context_impacts", {})
            impacts[self.target.id] = sorted(
                set(impacts.get(self.target.id, [])) | affected
            )
            if affected:
                change["validated_tree"] = None
                change["validation"] = None
            revision = _target_revision(self.repository, self.target)
            change.setdefault("authored_specs", {})[self.target.id] = {
                "task": self.task["task"],
                "focus_id": self.task.get("focus_id"),
                "constraints": self.task.get("constraints", []),
                "context_id": self.last_context,
                "spec_digest": revision,
            }
            if self.target.id in change.get("graph", {}):
                # Keep the graph's own baseline in sync with every real (admitted) authoring, so
                # the next loop() invocation's reset check only fires for an out-of-band (human)
                # Spec edit, mirroring how implement() tracks last_implementation_digest. This
                # covers specify-loop's authoring, whether called by dev-loop or independently
                # for a target that already has a graph record from an earlier dev-loop run.
                change["graph"][self.target.id]["spec_digest"] = revision
            save_change(self.repository.root, change)
        return self.response(answer=result["answer"])

    def require_spec_review(self) -> None:
        if self.host.mode != "execute":
            return
        from .review import current

        change = read_change(self.repository.root)
        if change and change.get("review_requirements", {}).get(self.target.id, {}).get(
            "spec"
        ):
            current(self, "spec", required=True)

    def plan(self) -> dict:
        from .plan_graph import build_plan_graph

        return build_plan_graph(self.plan_nodes().__getitem__).invoke({})["output"]

    def plan_nodes(self):
        from langgraph.graph import END

        result = None

        def assess_context(state):
            self.require_spec_review()
            if not self.host.coordinated:
                progress(
                    self.repository.root, phase="plan", status="active", invalidate=True
                )
            assessment = self.stage("concorde-context-solve")
            if assessment["outcome"] not in {"completed", "sufficient"}:
                return {
                    "output": self.response(
                        assessment["outcome"],
                        assessment["answer"],
                        blockers=assessment["blockers"],
                    ),
                    "route": END,
                }
            return {"route": "author_plan"}

        def author_plan(state):
            nonlocal result
            result = self.stage("concorde-plan", defer_gap_resolution=True)
            if result["outcome"] not in {"completed", "sufficient"}:
                return {
                    "output": self.response(
                        result["outcome"], result["answer"], blockers=result["blockers"]
                    ),
                    "route": END,
                }
            if self.host.mode == "describe-policy":
                return {"output": self.response("described"), "route": END}
            return {"route": "persist_plan"}

        def persist_plan(state):
            assert result is not None, (
                "plan persistence requires an admitted planner result"
            )
            if not result["plan"].strip():
                raise SpecError(
                    "planning produced no usable plan", "invalid_completion"
                )
            change = read_change(self.repository.root, required=True)
            self.change_id = change["change_id"]
            self.work_directory = f"{WORK_PATH}/{self.target.id}"
            state = target_state(
                self.repository.root,
                self.target.id,
                self.task.get("focus_id"),
                create=True,
            )
            state.pop("coordination", None)
            state.pop("component_revisions", None)
            state.update(
                plan=result["plan"],
                tasks=[],
                checks=[],
                spec_digest=_target_revision(self.repository, self.target),
                task=self.task["task"],
                constraints=self.task.get("constraints", []),
                implementation_digest=None,
                completed_operations=list(self.completed),
                phase="plan",
                status="active",
            )
            path = work_path(self.target.id, "plan.md")
            apply_files(
                self.repository.root,
                [file_change(self.repository.root, path, result["plan"])],
                {path},
            )
            save_target_state(self.repository.root, state)
            self.record_gaps("plan", [])
            return {
                "output": self.response(
                    answer=result["answer"],
                    artifacts=[artifact(self.repository.root, "plan", path)],
                ),
                "route": END,
            }

        return {
            "assess_context": assess_context,
            "author_plan": author_plan,
            "persist_plan": persist_plan,
        }

    def tasks(self) -> dict:
        self.require_spec_review()
        if not self.work_directory:
            raise SpecError(
                "task authoring requires a managed change", "missing_change"
            )
        if not self.host.coordinated:
            progress(
                self.repository.root, phase="tasks", status="active", invalidate=True
            )
        state = target_state(
            self.repository.root, self.target.id, self.task.get("focus_id")
        )
        scope_repair = self.task.get("repair_task_scope")
        self.check_state(state, allow_stale_spec=bool(scope_repair))
        if not state["plan"]:
            raise SpecError("tasks require an authored plan", "missing_plan")
        change = read_change(self.repository.root, required=True)
        repair = change.get("graph", {}).get(self.target.id, {}).get("repair")
        if scope_repair and (
            not state["tasks"]
            or scope_repair["tasks_digest"]
            != digest(canonical(state["tasks"]).encode())
            or all(task["complete"] for task in state["tasks"])
            or repair is not None
        ):
            raise SpecError(
                "task scope repair requires the exact current incomplete task list and no pending review repair",
                "incompatible_handoff",
            )
        reserved_ids = {
            t["id"] for entry in state.get("task_history", []) for t in entry["tasks"]
        }
        if scope_repair or repair is not None:
            reserved_ids.update(t["id"] for t in state["tasks"])
        inputs = (
            typed("concorde-plan-artifact", {"plan": state["plan"]}),
            typed(
                "concorde-task-identity-constraints",
                {"reserved_task_ids": sorted(reserved_ids)},
            ),
        )
        if scope_repair:
            inputs = (
                *inputs,
                typed(
                    "concorde-implementation-task",
                    {"plan": state["plan"], "tasks": state["tasks"]},
                ),
                typed(
                    "concorde-task-scope-feedback",
                    {**scope_repair, "reason": "implementation_boundary"},
                ),
            )
        if repair is not None:
            verify_artifacts(self.repository.root, repair["artifact"])
            review_value = validate_typed(
                decode(
                    read_file(self.repository.root, repair["artifact"]["path"]).decode()
                ),
                "concorde-review-result",
            )
            review_data = review_value["data"]
            if (
                review_data["review_mode"] != "code"
                or review_data["target_id"] != self.target.id
                or review_data["status"] != "findings"
            ):
                raise SpecError(
                    "repair review artifact does not match this target's blocking code-review findings",
                    "incompatible_handoff",
                )
            inputs = (
                *inputs,
                typed(
                    "concorde-implementation-task",
                    {"plan": state["plan"], "tasks": state["tasks"]},
                ),
                review_value,
            )
        result = self.stage("concorde-tasks", inputs=inputs, defer_gap_resolution=True)
        if result["outcome"] not in {"completed", "sufficient"}:
            return self.response(
                result["outcome"], result["answer"], blockers=result["blockers"]
            )
        if self.host.mode == "describe-policy":
            return self.response("described")
        tasks = result["tasks"]
        collisions = sorted({t["id"] for t in tasks} & reserved_ids)
        if collisions:
            raise SpecError(
                "task IDs are reserved by retained task history or the list being replaced: "
                + ", ".join(collisions),
                "invalid_completion",
            )
        if (
            not tasks
            or len({t["id"] for t in tasks}) != len(tasks)
            or any(t["complete"] for t in tasks)
        ):
            raise SpecError(
                "tasks must be nonempty, uniquely identified and initially incomplete",
                "invalid_completion",
            )
        for task in tasks:
            self.repository.select(task["target_id"])
            if task["target_id"] not in {
                self.target.id,
                *self.target.uses,
                *(child.id for child in self.repository.children(self.target)),
            }:
                raise SpecError(
                    "Module tasks may target only this Module, its declared dependencies or direct submodules",
                    "permission_denied",
                )
        prior_coordination = None
        if scope_repair and state.get("coordination"):
            old_targets = {
                task["target_id"]
                for task in state["tasks"]
                if task["target_id"] != self.target.id
            }
            grouped = {}
            for task in tasks:
                if task["target_id"] != self.target.id:
                    grouped.setdefault(task["target_id"], []).append(task)
            if set(grouped) != old_targets:
                raise SpecError(
                    "task scope repair must preserve component routing",
                    "incompatible_handoff",
                )
            replacements = {
                key: _component_intent(items)
                for key, items in grouped.items()
                if key in state["coordination"]
                and _component_intent(items) != state["coordination"][key]["task"]
            }
            for key in replacements:
                record = state["coordination"][key]
                owners = set()
                pending = [(key, record["task"])]
                while pending:
                    owner, intent = pending.pop()
                    if (owner, intent) in owners:
                        continue
                    owners.add((owner, intent))
                    component = change["targets"].get(owner, {})
                    if component.get("task") == intent:
                        for child, nested in component.get("coordination", {}).items():
                            declarations = [
                                item
                                for item in component.get("tasks", [])
                                if item["target_id"] == child
                            ]
                            if declarations and nested["task"] != _component_intent(
                                declarations
                            ):
                                raise SpecError(
                                    "component coordination differs from its accepted task list",
                                    "incompatible_handoff",
                                )
                            pending.append((child, nested["task"]))
                history = [
                    item
                    for item in change.get("issue_blockers", [])
                    if item["target_id"] in {owner for owner, _ in owners}
                    and item["scope_id"] == "module:" + item["target_id"]
                ]
                # Match immutable observations, not duplicated free text or a previous task label.
                unresolved_cache = any(
                    not any(
                        item["status"] == "resolved"
                        and item["blocker"]["issue_id"] == blocker.get("issue_id")
                        and item["blocker"]["report_id"] == blocker.get("report_id")
                        for item in history
                    )
                    for blocker in record.get("blockers", [])
                )
                if unresolved_cache or any(
                    item["status"] == "open" for item in history
                ):
                    raise SpecError(
                        "resolve the component's contract gaps before repairing its task boundary",
                        "spec_incomplete",
                    )
            prior_coordination = copy.deepcopy(state["coordination"])
            for key, intent in replacements.items():
                # Keep current Spec bytes and unaffected participants. The changed
                # child intent makes its ordinary loop re-review and replan; no
                # child task or completion evidence is rewritten here.
                state["coordination"][key].update(
                    task=intent,
                    implementation_status="pending",
                    implementation_digest=None,
                    outcome=None,
                )
            state.pop("component_revisions", None)
        if repair is not None:
            state.setdefault("task_history", []).append(
                {
                    "iteration": repair["iteration"],
                    "tasks": state["tasks"],
                    "implementation_digest": state.get("implementation_digest"),
                }
            )
            state["repair_review"] = repair["artifact"]
        if scope_repair:
            state.setdefault("task_history", []).append(
                {
                    "reason": "implementation_boundary",
                    "tasks_digest": scope_repair["tasks_digest"],
                    "tasks": state["tasks"],
                    "implementation_digest": state.get("implementation_digest"),
                    "spec_digest": state["spec_digest"],
                }
            )
            if prior_coordination is not None:
                state["task_history"][-1]["coordination"] = prior_coordination
            state["spec_digest"] = _target_revision(self.repository, self.target)
        state.update(
            tasks=tasks,
            checks=[],
            implementation_digest=None,
            phase="tasks",
            status="active",
        )
        save_target_state(self.repository.root, state)
        if repair is not None:
            change = read_change(self.repository.root, required=True)
            change["graph"][self.target.id]["repair"] = None
            save_change(self.repository.root, change)
        self.record_gaps("tasks", [])
        return self.response(
            answer=result["answer"],
            artifacts=[artifact(self.repository.root, "change", STATE_PATH)],
        )

    def implement(self) -> dict:
        self.require_spec_review()
        pending = self.pending_gaps("implementation")
        if pending:
            return self.response(
                "spec_incomplete",
                "Resolve the prerequisite task gaps before implementation.",
                blockers=pending,
            )
        if not self.work_directory:
            raise SpecError(
                "implementation requires a managed change and authored tasks",
                "missing_change",
            )
        state = target_state(
            self.repository.root, self.target.id, self.task.get("focus_id")
        )
        self.check_state(state)
        if not state["tasks"]:
            raise SpecError("implementation requires tasks", "missing_tasks")
        if state.get("coordination") or any(
            task["target_id"] != self.target.id for task in state["tasks"]
        ):
            return self.implement_scope(state)
        if (
            validate_repository(
                self.repository.root, package_root=self.host.package_root
            ).status
            != "success"
        ):
            raise SpecError(
                "reconcile all shared contracts before implementation",
                "incompatible_contracts",
            )
        if not self.host.coordinated:
            progress(
                self.repository.root,
                phase="implementation",
                status="active",
                invalidate=True,
            )
        inputs = (
            typed(
                "concorde-implementation-task",
                {"plan": state["plan"], "tasks": state["tasks"]},
            ),
        )
        repair_review = state.get("repair_review")
        if repair_review:
            verify_artifacts(self.repository.root, repair_review)
            review_value = validate_typed(
                decode(read_file(self.repository.root, repair_review["path"]).decode()),
                "concorde-review-result",
            )
            inputs = (*inputs, review_value)
        result = self.stage(
            "concorde-implement", inputs=inputs, defer_gap_resolution=True
        )
        if result["outcome"] not in {"completed", "sufficient"}:
            return self.response(
                result["outcome"], result["answer"], blockers=result["blockers"]
            )
        if self.host.mode == "describe-policy":
            return self.response("described")
        returned = result["tasks"]
        expected = [{**task, "complete": True} for task in state["tasks"]]
        if returned != expected:
            raise SpecError(
                "implementation must report every exact task complete",
                "incomplete_tasks",
            )
        missing = _unconfirmed_files(self.repository, self.target)
        if missing:
            raise SpecError(
                "implementation did not materialize required listed files: "
                + ", ".join(missing),
                "incomplete_tasks",
            )
        state["tasks"] = returned
        state["implementation_digest"] = _implementation_digest(
            self.repository, self.target
        )
        state["checks"] = []
        state.pop("repair_review", None)
        state.update(phase="implementation", status="completed")
        save_target_state(self.repository.root, state)
        change = read_change(self.repository.root)
        if change is not None and self.target.id in change.get("graph", {}):
            # Keep the graph's own baseline in sync with every real implementation, so the next
            # loop() invocation's reset check only fires for an out-of-band (human) code edit.
            change["graph"][self.target.id]["last_implementation_digest"] = state[
                "implementation_digest"
            ]
            save_change(self.repository.root, change)
        self.record_gaps("implementation", [])
        return self.response(answer=result["answer"])

    def check_state(self, state: dict, *, allow_stale_spec: bool = False) -> None:
        if not allow_stale_spec and state.get("spec_digest") != _target_revision(
            self.repository, self.target
        ):
            raise SpecError(
                "selected Spec or its registered authority changed; replan this change",
                "stale_context",
            )
        if state.get("task") != self.task["task"] or state.get(
            "constraints"
        ) != self.task.get("constraints", []):
            raise SpecError(
                "change intent differs from the authored plan; replan explicitly",
                "incompatible_handoff",
            )

    def implement_scope(self, state: dict) -> dict:
        """Retain resumable component drafts inside this one candidate worktree."""
        grouped = {}
        review_artifacts = []
        for task in state["tasks"]:
            component = self.repository.select(task["target_id"])
            allowed = {
                self.target.id,
                *self.target.uses,
                *(child.id for child in self.repository.children(self.target)),
            }
            if component.id not in allowed:
                raise SpecError(
                    "coordinated task must name a declared dependency or direct submodule",
                    "permission_denied",
                )
            grouped.setdefault(component.id, []).append(task)
        local_tasks = grouped.pop(self.target.id, [])
        component_tasks = {
            target_id: _component_intent(tasks) for target_id, tasks in grouped.items()
        }
        coordination = state.setdefault("coordination", {})
        # Local repair tasks do not erase already completed participating work. Its final
        # contract evidence must still be refreshed if the repair changes a shared implementation.
        for target_id, record in coordination.items():
            component_tasks.setdefault(target_id, record["task"])
        for target_id, task_text in component_tasks.items():
            record = coordination.setdefault(
                target_id,
                {
                    "task": task_text,
                    "spec_status": "pending",
                    "implementation_status": "pending",
                    "spec_digest": None,
                    "implementation_digest": None,
                    "blockers": [],
                    "outcome": None,
                },
            )
            if record["task"] != task_text:
                raise SpecError(
                    "component intent changed; replan this worktree change",
                    "stale_context",
                )
        progress(
            self.repository.root,
            phase="spec_reconciliation",
            status="active",
            invalidate=True,
        )
        state.update(phase="spec_reconciliation", status="active")
        save_target_state(self.repository.root, state)

        def blocked(result, target_id, phase):
            record = coordination[target_id]
            record[phase + "_status"] = "blocked"
            child = result["output"]["data"] if result["output"] else None
            record["outcome"] = child["outcome"] if child else "failed"
            record["blockers"] = child["blockers"] if child else []
            state["status"] = "blocked"
            save_target_state(self.repository.root, state)
            progress(
                self.repository.root,
                status="blocked",
                outcome=record["outcome"],
                blockers=record["blockers"],
            )
            if child:
                return self.response(
                    child["outcome"],
                    "Component " + target_id + ": " + child["answer"],
                    blockers=child["blockers"],
                    artifacts=child["artifacts"],
                )
            raise SpecError(
                "component " + phase + " blocked: " + target_id, "child_blocked"
            )

        from ..harness.batch_graph import run_batch_graph
        from .coordination_graph import build_coordination_graph

        def reconcile_specs(_graph_state):
            def reconcile_component(item):
                target_id, task_text = item
                component = self.repository.select(target_id)
                record = coordination[target_id]
                revision = _target_revision(self.repository, component)
                if (
                    record["spec_status"] == "completed"
                    and record["spec_digest"] == revision
                ):
                    return None
                record.update(
                    spec_status="running",
                    implementation_status="pending",
                    blockers=[],
                    outcome=None,
                )
                save_target_state(self.repository.root, state)
                payload = {
                    "target_id": target_id,
                    "task": task_text,
                    "change_id": self.change_id,
                    "constraints": self.task.get("constraints", []),
                }
                child_host = replace(
                    self.host,
                    routed_target=target_id,
                    coordinated=True,
                    defer_component_checks=True,
                    finalize_components=False,
                )
                result = run_operation(
                    "concorde-specify",
                    self.configuration,
                    typed("concorde-specify-request", payload),
                    host_context=child_host,
                )
                if result["status"] != "succeeded":
                    return blocked(result, target_id, "spec")
                self.repository = SpecRepository(
                    self.host.project_root, self.host.package_root
                )
                record.update(
                    spec_status="completed",
                    outcome="completed",
                    spec_digest=_target_revision(
                        self.repository, self.repository.select(target_id)
                    ),
                )
                save_target_state(self.repository.root, state)

            from ..harness.batch_graph import run_batch_graph

            failure = run_batch_graph(
                component_tasks.items(),
                reconcile_component,
                name="component_spec_graph",
                item_node="author_module",
            )
            if failure is not None:
                return {"output": failure}

            return {"output": None}

        def validate_specs(_graph_state):
            # Transitional consumer/provider disagreement is allowed until every
            # participating author has completed. It must not prevent resuming a draft.
            progress(self.repository.root, phase="spec_validation", status="active")
            if (
                validate_repository(
                    self.repository.root, package_root=self.host.package_root
                ).status
                != "success"
            ):
                state.update(phase="spec_validation", status="blocked")
                save_target_state(self.repository.root, state)
                progress(
                    self.repository.root,
                    status="blocked",
                    outcome="incompatible_contracts",
                )
                raise SpecError(
                    "reconcile all consumer/provider contracts before implementation",
                    "incompatible_contracts",
                )
            progress(self.repository.root, phase="implementation", status="active")
            state.update(phase="implementation", status="active")
            return {"output": None}

        def implement_components(_graph_state):
            def implement_component(item):
                target_id, task_text = item
                component = self.repository.select(target_id)
                record = coordination[target_id]
                payload = {
                    "target_id": target_id,
                    "task": task_text,
                    "change_id": self.change_id,
                    "constraints": self.task.get("constraints", []),
                }
                child_host = replace(
                    self.host,
                    routed_target=target_id,
                    coordinated=True,
                    defer_component_checks=True,
                    finalize_components=False,
                )
                from .review import require_reviews

                require_reviews(
                    Invocation(
                        "concorde-review", self.configuration, payload, child_host
                    ),
                    bool(
                        read_change(self.repository.root, required=True)
                        .get("review_requirements", {})
                        .get(self.target.id, {})
                        .get("spec")
                    ),
                )
                if record["implementation_status"] == "completed" and record[
                    "implementation_digest"
                ] == _implementation_digest(self.repository, component):
                    try:
                        Invocation(
                            "concorde-validate", self.configuration, payload, child_host
                        ).verify_completion()
                        review_artifacts.extend(
                            item["artifact"]
                            for item in read_change(self.repository.root, required=True)
                            .get("reviews", {})
                            .get(target_id, {})
                            .values()
                        )
                        return None
                    except SpecError:
                        pass
                record.update(
                    implementation_status="running", blockers=[], outcome=None
                )
                save_target_state(self.repository.root, state)
                result = run_operation(
                    "concorde-dev-loop",
                    self.configuration,
                    typed(
                        "concorde-dev-loop-request",
                        {
                            **payload,
                            "specify": False,
                            "run_reviews": bool(
                                read_change(self.repository.root, required=True)
                                .get("review_requirements", {})
                                .get(self.target.id, {})
                                .get("spec")
                            ),
                        },
                    ),
                    host_context=child_host,
                )
                if result["status"] != "succeeded":
                    return blocked(result, target_id, "implementation")
                review_artifacts.extend(
                    item
                    for item in result["output"]["data"]["artifacts"]
                    if item["id"].startswith("review.")
                )
                self.repository = SpecRepository(
                    self.host.project_root, self.host.package_root
                )
                record.update(
                    implementation_status="completed",
                    outcome="completed",
                    implementation_digest=_implementation_digest(
                        self.repository, self.repository.select(target_id)
                    ),
                )
                save_target_state(self.repository.root, state)

            failure = run_batch_graph(
                component_tasks.items(),
                implement_component,
                name="component_implementation_graph",
                item_node="develop_module",
            )
            if failure is not None:
                return {"output": failure}
            return {"output": None}

        def implement_local(_graph_state):
            if local_tasks:
                # A composite may also own coordination code. Do not recursively start a dev-loop
                # for this same target or replace its enclosing plan with one local subtask.
                current_local = _implementation_digest(self.repository, self.target)
                expected_local = [{**task, "complete": True} for task in local_tasks]
                if (
                    state.get("local_implementation_digest") != current_local
                    or state.get("local_completed_tasks") != expected_local
                ):
                    inputs = (
                        typed(
                            "concorde-implementation-task",
                            {"plan": state["plan"], "tasks": local_tasks},
                        ),
                    )
                    result = self.stage(
                        "concorde-implement", inputs=inputs, defer_gap_resolution=True
                    )
                    if result["outcome"] not in {"completed", "sufficient"}:
                        state.update(phase="implementation", status="blocked")
                        save_target_state(self.repository.root, state)
                        return {
                            "output": self.response(
                                result["outcome"],
                                result["answer"],
                                blockers=result["blockers"],
                            )
                        }
                    if result["tasks"] != expected_local:
                        raise SpecError(
                            "local coordination code did not complete its exact tasks",
                            "incomplete_tasks",
                        )
                    if _unconfirmed_files(self.repository, self.target):
                        raise SpecError(
                            "local implementation did not materialize its listed files",
                            "incomplete_tasks",
                        )
                    state["local_completed_tasks"] = expected_local
                    state["local_implementation_digest"] = _implementation_digest(
                        self.repository, self.target
                    )
                    save_target_state(self.repository.root, state)
            return {"output": None}

        def finalize_components(_graph_state):
            # All coordinated writers finish before any consumer's final code checks. A nested
            # coordinator leaves explicit drafts; the outer coordinator finalizes the whole tree.
            if not self.host.defer_component_checks:
                finalized = set()

                def finalize(target_id, task_text):
                    if target_id in finalized:
                        return None
                    finalized.add(target_id)
                    self.repository = SpecRepository(
                        self.host.project_root, self.host.package_root
                    )
                    component = self.repository.select(target_id)
                    component_state = target_state(
                        self.repository.root, target_id, None
                    )
                    nested = component_state.get("coordination", {})
                    failure = run_batch_graph(
                        nested.items(),
                        lambda item: finalize(item[0], item[1]["task"]),
                        name="nested_finalization_graph",
                        item_node="finalize_module",
                    )
                    if failure is not None:
                        return failure
                    self.repository = SpecRepository(
                        self.host.project_root, self.host.package_root
                    )
                    component = self.repository.select(target_id)
                    component_state = target_state(
                        self.repository.root, target_id, None
                    )
                    component_state["component_revisions"] = {
                        key: {
                            "spec": _target_revision(
                                self.repository, self.repository.select(key)
                            ),
                            "implementation": _implementation_digest(
                                self.repository, self.repository.select(key)
                            ),
                        }
                        for key in nested
                    }
                    component_state.update(
                        implementation_digest=_implementation_digest(
                            self.repository, component
                        ),
                        checks=[],
                        phase="validate",
                        status="active",
                    )
                    save_target_state(self.repository.root, component_state)
                    payload = {
                        "target_id": target_id,
                        "task": task_text,
                        "change_id": self.change_id,
                        "constraints": self.task.get("constraints", []),
                    }
                    child_host = replace(
                        self.host,
                        routed_target=target_id,
                        coordinated=True,
                        defer_ready=True,
                        defer_component_checks=False,
                        finalize_components=True,
                    )
                    change = read_change(self.repository.root, required=True)
                    enabled = bool(
                        change.get("review_requirements", {})
                        .get(target_id, {})
                        .get("spec")
                    )
                    child = Invocation(
                        "concorde-dev-loop",
                        self.configuration,
                        {**payload, "specify": False, "run_reviews": enabled},
                        child_host,
                    )
                    verified = child.loop()["data"]
                    if verified["outcome"] not in {"completed", "ready"}:
                        return verified
                    review_artifacts.extend(verified["artifacts"])
                    return None

                def participating_ids():
                    change = read_change(self.repository.root, required=True)
                    selected = {self.target.id}

                    def visit(target_id):
                        if target_id in selected:
                            return
                        selected.add(target_id)
                        for nested_id in (
                            change["targets"].get(target_id, {}).get("coordination", {})
                        ):
                            visit(nested_id)

                    for target_id in component_tasks:
                        visit(target_id)
                    return selected

                def candidate_implementation():
                    self.repository = SpecRepository(
                        self.host.project_root, self.host.package_root
                    )
                    return digest(
                        [
                            (
                                key,
                                _implementation_digest(
                                    self.repository, self.repository.select(key)
                                ),
                            )
                            for key in sorted(participating_ids())
                        ]
                    )

                # Local repair remains bounded by each Module's loop. A later repair can stale
                # an earlier consumer; rerun final verification until the shared candidate is stable.
                from langgraph.graph import END

                from .coordination_graph import build_stabilization_graph

                remaining = 1 + 2 * len(participating_ids())
                before_finalization = None

                def snapshot(_graph_state):
                    nonlocal remaining, before_finalization
                    if remaining == 0:
                        raise SpecError(
                            "shared implementation repairs did not converge to one verified candidate",
                            "incompatible_contracts",
                        )
                    remaining -= 1
                    before_finalization = candidate_implementation()
                    finalized.clear()
                    return {}

                def verify_component(item):
                    target_id, task_text = item
                    failure = finalize(target_id, task_text)
                    if failure is not None:
                        state.update(phase="validate", status="blocked")
                        save_target_state(self.repository.root, state)
                        return self.response(
                            failure["outcome"],
                            failure["answer"],
                            blockers=failure.get("blockers", []),
                            checks=failure.get("checks", []),
                            artifacts=failure.get("artifacts", []),
                        )
                    coordination[target_id]["implementation_digest"] = (
                        _implementation_digest(
                            self.repository, self.repository.select(target_id)
                        )
                    )

                def verify_components(_graph_state):
                    return {
                        "output": run_batch_graph(
                            component_tasks.items(),
                            verify_component,
                            name="component_finalization_graph",
                            item_node="finalize_module",
                        )
                    }

                def check_stability(_graph_state):
                    return {
                        "route": END
                        if candidate_implementation() == before_finalization
                        else "snapshot"
                    }

                nodes = {
                    "snapshot": snapshot,
                    "verify_components": verify_components,
                    "check_stability": check_stability,
                }
                failure = (
                    build_stabilization_graph(nodes.__getitem__)
                    .invoke({}, {"recursion_limit": 3 * remaining + 3})
                    .get("output")
                )
                if failure is not None:
                    return {"output": failure}
            return {"output": None}

        def record_completion(_graph_state):
            state["component_revisions"] = {
                target_id: {
                    "spec": _target_revision(
                        self.repository, self.repository.select(target_id)
                    ),
                    "implementation": _implementation_digest(
                        self.repository, self.repository.select(target_id)
                    ),
                }
                for target_id in component_tasks
            }
            state["tasks"] = [{**task, "complete": True} for task in state["tasks"]]
            state["implementation_digest"] = _implementation_digest(
                self.repository, self.target
            )
            state.update(phase="implementation", status="completed")
            save_target_state(self.repository.root, state)
            return {
                "output": self.response(
                    answer="Participating components completed in the candidate worktree.",
                    artifacts=list(
                        {
                            reference["id"]: reference for reference in review_artifacts
                        }.values()
                    ),
                )
            }

        nodes = {
            "reconcile_specs": reconcile_specs,
            "validate_specs": validate_specs,
            "implement_components": implement_components,
            "implement_local": implement_local,
            "finalize_components": finalize_components,
            "record_completion": record_completion,
        }
        return build_coordination_graph(nodes.__getitem__).invoke({})["output"]

    def validate(self, run_checks: bool = True) -> dict:
        if not self.host.coordinated:
            progress(
                self.repository.root, phase="validate", status="active", invalidate=True
            )
        before_tree = (
            snapshot_tree(self.repository.root) if self.work_directory else None
        )
        change = read_change(self.repository.root)
        direct_candidate = bool(
            change is not None and not change["targets"] and not self.host.coordinated
        )
        report = validate_repository(
            self.repository.root, self.target.id, self.host.package_root
        )
        if report.status != "success":
            progress(self.repository.root, status="blocked", outcome="invalid_spec")
            return self.response(
                "failed",
                "Spec structure or shared contracts failed deterministic validation.",
            )
        checked_targets = (
            tuple(self.repository.targets.values())
            if direct_candidate
            else _implementation_users(self.repository, self.target)
        )
        impacts = _impact_revisions(self.repository, checked_targets)
        results = (
            [
                result
                for target in checked_targets
                for result in _check(self.repository, target, self.host.invocation_id)
            ]
            if run_checks
            else []
        )
        state = None
        if change and self.target.id in change["targets"]:
            state = target_state(
                self.repository.root, self.target.id, self.task.get("focus_id")
            )
            state.update(
                checks=results,
                implementation_impacts=impacts,
                validation_spec_digest=report.result["source_digest"],
                validation_issue_digest=_issues_revision(self.repository.root),
                phase="validate",
                status="active",
            )
            save_target_state(self.repository.root, state)
        self.completed.append("concorde-validate")
        failed = any(item["status"] != "passed" for item in results)
        if failed:
            if state is not None:
                state["status"] = "blocked"
                save_target_state(self.repository.root, state)
            return self.response(
                "failed", "Deterministic validation failed.", checks=results
            )
        if self.work_directory and snapshot_tree(self.repository.root) != before_tree:
            raise SpecError(
                "candidate files changed while checks were running", "stale_evidence"
            )
        current_repository = SpecRepository(
            self.repository.root, self.host.package_root
        )
        current_target = current_repository.select(self.target.id)
        current_targets = (
            tuple(current_repository.targets.values())
            if direct_candidate
            else _implementation_users(current_repository, current_target)
        )
        if _impact_revisions(current_repository, current_targets) != impacts:
            raise SpecError(
                "a using Module or shared implementation changed during validation",
                "stale_evidence",
            )
        self.repository, self.target = current_repository, current_target
        if direct_candidate:
            change = read_change(self.repository.root, required=True)
            change["validation"] = {
                "target_id": self.target.id,
                "focus_id": self.task.get("focus_id"),
                "task": self.task["task"],
                "constraints": self.task.get("constraints", []),
                "spec_digest": _target_revision(self.repository, self.target),
                "source_digest": report.result["source_digest"],
                "checks": results,
            }
            save_change(self.repository.root, change)
            if self.host.defer_ready:
                return self.response(
                    answer="Deterministic checks completed; required review precedes readiness.",
                    checks=results,
                )
            return self.mark_ready()
        if (
            state
            and state["tasks"]
            and all(task["complete"] for task in state["tasks"])
        ):
            if self.host.defer_ready:
                return self.response(
                    answer="Deterministic checks completed; required review precedes readiness.",
                    checks=results,
                )
            return self.mark_ready()
        return self.response(
            answer="Deterministic validation passed; semantic completeness is not proven.",
            checks=results,
        )

    def mark_ready(self) -> dict:
        before_tree = snapshot_tree(self.repository.root)
        evidence = self.verify_completion()
        if snapshot_tree(self.repository.root) != before_tree:
            raise SpecError(
                "candidate changed during completion verification", "stale_evidence"
            )
        change = read_change(self.repository.root, required=True)
        if self.target.id in change["targets"]:
            change["targets"][self.target.id].update(phase="ready", status="ready")
        if not self.host.coordinated:
            change.update(
                phase="ready",
                status="ready",
                outcome="ready",
                validated_tree=before_tree,
            )
        save_change(self.repository.root, change)
        return self.response(
            "ready",
            "Candidate verified. Request delivery from this source or the destination worktree.",
            checks=evidence.get("checks", []),
        )

    def verify_completion(self) -> dict:
        """Read current target evidence; delivery remains a separate top-level action."""
        from .review import verify_required

        verify_required(self)
        change = read_change(self.repository.root, required=True)
        if any(
            item["status"] == "open"
            and item["target_id"] == self.target.id
            and item["scope_id"]
            == blocker_scope(change, self.target.id, self.task["task"])
            for item in change.get("issue_blockers", [])
        ):
            raise SpecError(
                "current task still has unresolved contract gaps", "spec_incomplete"
            )
        if not change["targets"]:
            validation = change.get("validation")
            if (
                not validation
                or validation["target_id"] != self.target.id
                or validation["focus_id"] != self.task.get("focus_id")
                or validation["task"] != self.task["task"]
                or validation["constraints"] != self.task.get("constraints", [])
            ):
                raise SpecError(
                    "direct candidate has no bound validation evidence",
                    "stale_evidence",
                )
            report = validate_repository(
                self.repository.root, package_root=self.host.package_root
            )
            if (
                report.status != "success"
                or validation["source_digest"] != report.result["source_digest"]
                or validation["spec_digest"]
                != _target_revision(self.repository, self.target)
            ):
                raise SpecError(
                    "direct candidate Spec validation is stale", "stale_evidence"
                )
            required = {
                check_id
                for target in self.repository.targets.values()
                for check_id in target.checks
            }
            if {item["check_id"] for item in validation["checks"]} != required or any(
                item["status"] != "passed"
                or item["source_digest"]
                != _check_revision(
                    self.repository, self.repository.select(item["target_id"])
                )
                for item in validation["checks"]
            ):
                raise SpecError(
                    "direct candidate checks are missing, failed, or stale",
                    "stale_evidence",
                )
            return validation
        state = target_state(
            self.repository.root, self.target.id, self.task.get("focus_id")
        )
        self.check_state(state)
        for target_id, revision in state.get("component_revisions", {}).items():
            component = self.repository.select(target_id)
            if revision != {
                "spec": _target_revision(self.repository, component),
                "implementation": _implementation_digest(self.repository, component),
            }:
                raise SpecError(
                    "a completed component changed before coordinated delivery",
                    "stale_evidence",
                )
            component_state = target_state(self.repository.root, target_id, None)
            payload = {
                "target_id": target_id,
                "task": component_state["task"],
                "constraints": component_state.get("constraints", []),
                "change_id": self.change_id,
            }
            Invocation(
                "concorde-validate",
                self.configuration,
                payload,
                replace(self.host, coordinated=True),
            ).verify_completion()
        if not state["tasks"] or any(not task["complete"] for task in state["tasks"]):
            raise SpecError("delivery requires completed tasks", "incomplete_change")
        if state["implementation_digest"] != _implementation_digest(
            self.repository, self.target
        ):
            raise SpecError("implementation changed since completion", "stale_evidence")
        report = validate_repository(
            self.repository.root, self.target.id, self.host.package_root
        )
        if (
            report.status != "success"
            or state.get("validation_spec_digest") != report.result["source_digest"]
        ):
            raise SpecError("Spec validation is missing or stale", "stale_evidence")
        affected = _implementation_users(self.repository, self.target)
        if state.get("implementation_impacts") != _impact_revisions(
            self.repository, affected
        ):
            raise SpecError(
                "shared implementation consumer evidence is missing or stale",
                "stale_evidence",
            )
        required_checks = {key for target in affected for key in target.checks}
        if {item["check_id"] for item in state["checks"]} != required_checks or any(
            item["status"] != "passed"
            or item["source_digest"]
            != _check_revision(
                self.repository, self.repository.select(item["target_id"])
            )
            for item in state["checks"]
        ):
            raise SpecError(
                "required implementation checks are missing, failed, or stale",
                "stale_evidence",
            )
        return state

    def loop(self) -> dict:
        """The development Graph (G1-G4): a bounded ``review_code -> tasks`` repair edge is the
        only automatic revision; every other non-advancing outcome stops the Graph for a human,
        with the stopping status recorded on the change and the transition recorded under
        ``graph`` in ``.concorde/worktree.json`` (development.md's "AI and human feedback").
        """
        from .loop_graph import build_loop_graph

        return build_loop_graph(self.loop_nodes().__getitem__, dynamic=True).invoke(
            {"output": {}, "artifacts": []}, {"recursion_limit": 100000}
        )["output"]

    def loop_nodes(self):
        from langgraph.graph import END
        from langgraph.types import Command

        from .loop_graph import loop_successors, stage_command
        from .review import current, current_code_scope, require_reviews, skip
        from .specify_graph import has_authored_spec as authored_for_task

        specify = self.task.get("specify", True)
        run_reviews = self.task.get("run_reviews", True)
        require_reviews(self, run_reviews)
        policy = importlib.import_module(
            f"{load_operation_inventory().__name__}.dev_loop"
        ).GRAPH
        graph_state(
            self.repository.root,
            self.target.id,
            policy=policy,
            spec_digest=_target_revision(self.repository, self.target),
            implementation_digest=_implementation_digest(self.repository, self.target)
            if self.target.files
            else None,
        )
        stages = (
            ["specify", "plan", "tasks", "implement", "validate"]
            if specify
            else ["plan", "tasks", "implement", "validate"]
        )
        change = read_change(self.repository.root, required=True)
        existing = change["targets"].get(self.target.id) if change else None
        blocked_phases = {
            item["phase"]
            for item in change.get("issue_blockers", [])
            if item["status"] == "open"
            and item["target_id"] == self.target.id
            and item["scope_id"]
            == blocker_scope(change, self.target.id, self.task["task"])
        }
        has_authored_spec = authored_for_task(change, self.target.id, self.task)
        if specify and has_authored_spec:
            stages.remove("specify")
        if (
            (not specify or has_authored_spec)
            and existing
            and existing.get("plan")
            and not blocked_phases.intersection({"context-solve", "plan"})
            and existing.get("task") == self.task["task"]
            and existing.get("focus_id") == self.task.get("focus_id")
            and existing.get("constraints", []) == self.task.get("constraints", [])
            and existing.get("spec_digest")
            == _target_revision(self.repository, self.target)
        ):
            stages = ["tasks", "implement", "validate"]
            if existing.get("tasks") and "tasks" not in blocked_phases:
                stages = ["implement", "validate"]
                if (
                    not existing.get("coordination")
                    and all(item["complete"] for item in existing["tasks"])
                    and "implementation" not in blocked_phases
                    and existing.get("implementation_digest")
                    == _implementation_digest(self.repository, self.target)
                ):
                    stages = ["validate"]
        if (
            self.host.finalize_components
            and existing
            and all(task["complete"] for task in existing.get("tasks", []))
        ):
            stages = ["validate"]

        scope_repair = self.task.get("repair_task_scope")
        if scope_repair:
            if not existing:
                raise SpecError(
                    "task scope repair requires an existing task list", "missing_tasks"
                )
            self.check_state(existing, allow_stale_spec=True)
            consumed = any(
                item.get("tasks_digest") == scope_repair["tasks_digest"]
                and item.get("reason") == "implementation_boundary"
                for item in existing.get("task_history", [])
            )
            if consumed:
                scope_repair = (
                    None  # replay resumes; it never reauthors an accepted replacement
                )
            elif (
                not existing.get("tasks")
                or all(t["complete"] for t in existing["tasks"])
                or digest(canonical(existing["tasks"]).encode())
                != scope_repair["tasks_digest"]
                or change.get("graph", {}).get(self.target.id, {}).get("repair")
                is not None
                or blocked_phases
            ):
                raise SpecError(
                    "task scope repair requires current incomplete tasks without unresolved gaps or review repair",
                    "incompatible_handoff",
                )
            else:
                stages = ["tasks", "implement", "validate"]

        # Resume trimming (above) only decides where the traversed path *enters*; every node from
        # "tasks" onward is still declared below so a repair can re-enter "tasks" even when this
        # run resumed past it (e.g. straight at "validate").
        include_specify = stages[0] == "specify"
        entry = stages[1] if include_specify else stages[0]
        successor = loop_successors(
            include_specify=include_specify,
            entry=entry,
            has_code=bool(self.target.files),
        )

        def current_iteration() -> int:
            record = (
                read_change(self.repository.root, required=True)
                .get("graph", {})
                .get(self.target.id, {})
            )
            return record.get("repair_iteration", 0)

        def stop(name: str, outcome: str) -> str:
            """A non-advancing, non-repairable outcome: record it and end the Graph for a human."""
            status = (
                "waiting"
                if outcome == "spec_incomplete"
                else "failed"
                if outcome == "failed"
                else "blocked"
            )
            if self.host.lifecycle.get("status") in {"cancelled", "limit_exhausted"}:
                status = self.host.lifecycle["status"]
            self.host.lifecycle["status"] = status
            trigger = (
                "ai-review"
                if name in {"review_spec", "review_code"}
                else "deterministic"
                if name == "validate"
                else "ai-assessment"
            )
            record_transition(
                self.repository.root,
                self.target.id,
                iteration=current_iteration(),
                **{"from": name, "to": "END"},
                trigger=trigger,
                outcome=outcome,
                source="code-driven"
                if name == "validate" or outcome == "failed"
                else "model-driven",
                artifact=None,
                input_digest=None,
                finding_ids=[],
                status=status,
            )
            return END

        def route_review_code(data: dict) -> str:
            """Blocking code-review findings without a gap: repair once, unless unchanged
            feedback or the declared iteration limit says otherwise (G2/G3 "AI review")."""
            if data["outcome"] != "conflicting":
                return stop("review_code", data["outcome"])
            if any(
                value["data"]["target_id"] != self.target.id
                and any(
                    finding["severity"] == "blocking"
                    for finding in value["data"]["issues"]
                )
                for value in data.get("reviews", [])
            ):
                # A peer's contract is not this planner's context. Preserve the peer result
                # for separately routed work instead of inventing a repair from the first artifact.
                return stop("review_code", data["outcome"])
            reference = next(
                item
                for item in data["artifacts"]
                if item["id"] == f"review.{self.target.id}.code"
            )
            verify_artifacts(self.repository.root, reference)
            reviewed = validate_typed(
                decode(read_file(self.repository.root, reference["path"]).decode()),
                "concorde-review-result",
            )["data"]
            blocking = [f for f in reviewed["issues"] if f["severity"] == "blocking"]
            from ..issues.references import receipt
            from ..issues.store import resolve_report

            feedback_digest = digest(
                sorted(
                    canonical(
                        {
                            key: value
                            for key, value in resolve_report(
                                self.repository.root, receipt(f)
                            )["report"].items()
                            if key
                            not in {"report_key", "issue_id", "expected_revision"}
                        }
                    )
                    for f in blocking
                )
            )
            finding_ids = sorted(f["issue_id"] for f in blocking)
            change = read_change(self.repository.root, required=True)
            record = change["graph"][self.target.id]
            common = dict(
                **{"from": "review_code", "to": "tasks"},
                trigger="ai-review",
                outcome="conflicting",
                source="model-driven",
                artifact=reference,
                input_digest=reviewed["input_digest"],
                finding_ids=finding_ids,
            )
            if feedback_digest == record["last_feedback_digest"]:
                self.host.lifecycle["status"] = "waiting"
                record_transition(
                    self.repository.root,
                    self.target.id,
                    iteration=record["repair_iteration"],
                    **{**common, "to": "END", "source": "code-driven"},
                    status="waiting",
                )
                return END
            if record["repair_iteration"] >= record["policy"]["max_repair_iterations"]:
                self.host.lifecycle["status"] = "limit_exhausted"
                record_transition(
                    self.repository.root,
                    self.target.id,
                    iteration=record["repair_iteration"],
                    **{**common, "to": "END", "source": "code-driven"},
                    status="limit_exhausted",
                )
                return END
            iteration = record["repair_iteration"] + 1
            record.update(
                repair_iteration=iteration,
                last_feedback_digest=feedback_digest,
                repair={"artifact": reference, "iteration": iteration},
            )
            save_change(self.repository.root, change)
            record_transition(
                self.repository.root,
                self.target.id,
                iteration=iteration,
                **common,
                status=None,
            )
            return "tasks"

        def execute(name):
            def node(state):
                self.repository = SpecRepository(
                    self.host.project_root, self.host.package_root
                )
                if name == "ready":
                    work = target_state(
                        self.repository.root, self.target.id, self.task.get("focus_id")
                    )
                    if work.get("validation_issue_digest") != _issues_revision(
                        self.repository.root
                    ):
                        # Reviews may report advisory Issues after the earlier checks. Refresh
                        # deterministic evidence for those new deliverable bytes without reusing
                        # a stale ready receipt or making Issue reporting fail the task.
                        validator = Invocation(
                            "concorde-validate",
                            self.configuration,
                            self.task,
                            replace(self.host, defer_ready=True),
                        )
                        checked = validator.validate()["data"]
                        if checked["outcome"] != "completed":
                            return Command(goto="summarize", update={"output": checked})
                    return Command(
                        goto="summarize", update={"output": self.mark_ready()["data"]}
                    )
                mode = name.removeprefix("review_")
                is_review = name.startswith("review_")
                data = None
                review_artifacts: list[dict] = []
                if is_review:
                    mode = name.removeprefix("review_")
                    enabled = read_change(self.repository.root, required=True)[
                        "review_requirements"
                    ][self.target.id][mode]
                    if not enabled:
                        skip(self, mode)
                        reference = read_change(self.repository.root, required=True)[
                            "reviews"
                        ][self.target.id][mode]["artifact"]
                        review_artifacts.append(reference)
                        data = self.response(
                            answer=f"{mode} review explicitly skipped.",
                            artifacts=[reference],
                        )["data"]
                    elif current(self, mode) is not None and (
                        mode != "code" or current_code_scope(self) is not None
                    ):
                        review_artifacts.append(
                            read_change(self.repository.root, required=True)["reviews"][
                                self.target.id
                            ][mode]["artifact"]
                        )
                        data = self.response(answer=f"Current {mode} review retained.")[
                            "data"
                        ]
                    elif not self.host.coordinated:
                        progress(
                            self.repository.root,
                            phase=mode + "-review",
                            status="active",
                            invalidate=True,
                        )
                if data is None:
                    child_operation = "concorde-" + name.replace("_", "-")
                    if is_review:
                        child_operation = "concorde-review"
                    payload = {
                        "target_id": self.target.id,
                        "task": self.task["task"],
                        "constraints": self.task.get("constraints", []),
                    }
                    if name == "specify_loop":
                        payload.update(specify=specify, run_reviews=run_reviews)
                    if (
                        name == "tasks"
                        and scope_repair
                        and not any(
                            item.get("tasks_digest") == scope_repair["tasks_digest"]
                            for item in target_state(
                                self.repository.root,
                                self.target.id,
                                self.task.get("focus_id"),
                            ).get("task_history", [])
                        )
                    ):
                        # The request only binds a list. Host-generated semantic feedback
                        # contains neither source contents nor raw validation output.
                        payload["repair_task_scope"] = scope_repair
                    if is_review:
                        payload["review_mode"] = mode
                    if self.task.get("focus_id"):
                        payload["focus_id"] = self.task["focus_id"]
                    if self.change_id:
                        payload["change_id"] = self.change_id
                    child_host = replace(
                        self.host,
                        evidence=[],
                        descriptions=self.host.descriptions,
                        lifecycle=self.host.lifecycle,
                        track_gaps=True,
                        defer_ready=name == "validate",
                    )
                    result = invoke_operation(
                        self.operation,
                        child_operation,
                        self.configuration,
                        typed(OPERATION_CONTRACTS[child_operation][0], payload),
                        child_host,
                    )
                    self.host.evidence.extend(child_host.evidence)
                    if result["output"] is None:
                        first_code = (
                            result["errors"][0]["code"] if result["errors"] else None
                        )
                        if first_code in {"execution_cancelled", "execution_limit"}:
                            self.host.lifecycle["status"] = (
                                "cancelled"
                                if first_code == "execution_cancelled"
                                else "limit_exhausted"
                            )
                        raise SpecError(
                            f"{child_operation} blocked: "
                            + canonical(result["errors"]),
                            "child_blocked",
                        )
                    data = result["output"]["data"]
                    self.change_id = data["change_id"] or self.change_id
                    self.work_directory = (
                        f"{WORK_PATH}/{self.target.id}" if self.change_id else None
                    )
                    self.last_context = data["context_id"] or self.last_context
                    self.completed.extend(data["completed_operations"])
                    if is_review or name in {"implement", "specify_loop"}:
                        review_artifacts.extend(
                            item
                            for item in data["artifacts"]
                            if item["id"].startswith("review.")
                        )
                    self.repository = SpecRepository(
                        self.host.project_root, self.host.package_root
                    )
                if (
                    self.host.defer_component_checks
                    and data["outcome"] in {"completed", "ready"}
                    and (
                        name == "implement"
                        or name == "specify_loop"
                        and entry == "validate"
                    )
                ):
                    record_transition(
                        self.repository.root,
                        self.target.id,
                        iteration=current_iteration(),
                        **{"from": name, "to": "END"},
                        trigger="deterministic",
                        outcome="completed",
                        source="code-driven",
                        artifact=None,
                        input_digest=None,
                        finding_ids=[],
                        status="active",
                    )
                    data = {
                        **data,
                        "outcome": "completed",
                        "answer": "Component code draft is complete; the enclosing Module verifies the final shared candidate.",
                    }
                    route = END
                elif data["outcome"] in {"completed", "ready"}:
                    route = successor[name]
                elif name == "review_code":
                    route = route_review_code(data)
                else:
                    route = stop(name, data["outcome"])
                return stage_command(route, output=data, artifacts=review_artifacts)

            def observed(state):
                iteration = current_iteration()
                self.host.observe(
                    "stage_started",
                    operation=self.operation,
                    stage=name,
                    invocation_id=self.host.invocation_id,
                    iteration=iteration,
                    trigger="ai-review"
                    if name == "tasks" and iteration
                    else "deterministic",
                )
                try:
                    command = node(state)
                except Exception:
                    self.host.observe(
                        "stage_failed",
                        operation=self.operation,
                        stage=name,
                        invocation_id=self.host.invocation_id,
                    )
                    raise
                if not isinstance(command.update, dict):
                    raise SpecError(
                        "Graph stage returned no typed output update",
                        "invalid_completion",
                    )
                self.host.observe(
                    "stage_finished",
                    operation=self.operation,
                    stage=name,
                    invocation_id=self.host.invocation_id,
                    outcome=command.update["output"].get("outcome"),
                    iteration=current_iteration(),
                    trigger="ai-review" if name == "review_code" else "deterministic",
                )
                return command

            return observed

        def initialize(state):
            return Command(goto="specify_loop")

        def summarize(state):
            if state.get("result"):
                return {}
            result = state["output"]
            artifacts = list(
                {
                    item["id"]: item
                    for item in [*state.get("artifacts", []), *result["artifacts"]]
                }.values()
            )
            coverage = []
            for reference in artifacts:
                if reference["id"].startswith("review."):
                    verify_artifacts(self.repository.root, reference)
                    value = validate_typed(
                        decode(
                            read_file(self.repository.root, reference["path"]).decode()
                        ),
                        "concorde-review-result",
                    )["data"]
                    coverage.append(
                        f"{value['target_id']}/{value['review_mode']}={value['status']}"
                    )
            answer = result["answer"] + (
                " Review coverage: " + "; ".join(coverage) + "." if coverage else ""
            )
            return {
                "output": self.response(
                    result["outcome"],
                    answer,
                    blockers=result["blockers"],
                    checks=result["checks"],
                    artifacts=artifacts,
                )
            }

        names = (
            "specify_loop",
            "plan",
            "tasks",
            "implement",
            "validate",
            "review_code",
            "ready",
        )
        return {
            "initialize": initialize,
            "summarize": summarize,
            **{name: execute(name) for name in names},
        }


def _project_operation(operation, configuration, task, host):
    from .project_graph import build_project_graph

    return build_project_graph(
        _project_nodes(operation, configuration, task, host).__getitem__
    ).invoke({})["output"]


def _project_nodes(operation, configuration, task, host):
    from langgraph.graph import END

    from ..spec.initialize import apply_project_proposal, project_proposal

    def select_action(state):
        if host.mode == "describe-policy":
            raise SpecError(
                "project proposals are the deterministic preview for this operation",
                "use_proposal",
            )
        return {
            "route": "configure"
            if operation == "concorde-configure"
            else "apply"
            if task["action"] == "apply"
            else "propose"
        }

    def configure(state):
        from ..spec.initialize import installed_protocol_binding

        accept = bool(task.get("accept_protocol"))
        if not accept:
            SpecRepository(host.project_root, host.package_root)
        value = decode(read_file(host.project_root, ".concorde/config.json").decode())
        if accept:
            # Explicit acceptance of the Protocol the installer placed under .concorde/protocol/:
            # rebind the configuration to that copy; the repository admission verifies the result
            # before the write is kept.
            value["protocol"] = installed_protocol_binding(host.project_root)
        value["operation_configuration"] = task["configuration"]
        changed = file_change(
            host.project_root, ".concorde/config.json", canonical(value) + "\n"
        )
        apply_files(
            host.project_root,
            [changed],
            {changed["path"]},
            verify=lambda: SpecRepository(host.project_root, host.package_root),
        )
        return {
            "output": typed(
                "concorde-configure-response",
                {"status": "applied", "configuration": task["configuration"]},
            ),
            "route": END,
        }

    def apply(state):
        if "proposal" not in task:
            raise SpecError(
                "apply requires the complete typed proposal", "invalid_input"
            )
        proposal = task["proposal"]
        value = apply_project_proposal(
            host.project_root,
            host.package_root,
            {
                "type_id": proposal["type_id"],
                "schema_version": proposal["schema_version"],
                **proposal["data"],
            },
        )
        return {
            "output": typed(
                OPERATION_CONTRACTS[operation][1],
                {"status": "applied", "proposal": None, "files": value["files"]},
            ),
            "route": END,
        }

    def propose(state):
        if not {"name", "configuration"}.issubset(task):
            raise SpecError(
                "initialization proposal requires name and configuration",
                "invalid_input",
            )
        value = project_proposal(
            host.project_root,
            host.package_root,
            task["name"],
            task["configuration"],
            task.get("target_id", "module.project"),
        )
        proposal = typed(
            "concorde-project-proposal",
            {key: value[key] for key in ("action", "base_digest", "files")},
        )
        return {
            "output": typed(
                OPERATION_CONTRACTS[operation][1],
                {
                    "status": "proposed",
                    "proposal": proposal,
                    "files": [x["path"] for x in value["files"]],
                },
            ),
            "route": END,
        }

    return {
        "select_action": select_action,
        "configure": configure,
        "apply": apply,
        "propose": propose,
    }


def _dispatch(operation, configuration, task, host):
    from .dispatch_graph import build_dispatch_graph

    return build_dispatch_graph(
        _dispatch_nodes(operation, configuration, task, host).__getitem__,
        operation=operation,
    ).invoke({})["output"]


def _dispatch_nodes(operation, configuration, task, host):
    from langgraph.graph import END

    run = None

    def bound_run() -> Invocation:
        if run is None:
            raise SpecError(
                "operation stage requires an admitted target", "invalid_context"
            )
        return run

    target_discovery = None
    target_discovery_nodes = {}

    def select_operation(state):
        if operation == "concorde-deliver":
            route = "deliver"
        elif operation in {"concorde-init", "concorde-configure"}:
            route = "project"
        elif operation == MAIN_OPERATION:
            route = {
                "ask": "answer",
                "design-topology": "design_topology",
                "accept-topology": "prepare_topology",
                "apply-topology": "apply_topology",
            }[task["action"]]
        else:
            route = "prepare_target"
        return {"route": route}

    def initialize_target(state):
        nonlocal task, host, target_discovery, target_discovery_nodes
        if (
            operation in DISCOVERY_OPERATIONS
            and host.routed_target is not None
            and task.get("target_id") != host.routed_target
        ):
            raise SpecError(
                "child target differs from the host's discovery route",
                "incompatible_handoff",
            )
        if operation in DISCOVERY_OPERATIONS:
            if host.routed_target is None and (
                task.get("change_id")
                or operation in {"concorde-dev-loop", "concorde-specify-loop"}
            ):
                change = read_change(host.project_root)
                if change is not None:
                    task = resume_owner(change, task)
                    if change["target_id"] is not None:
                        try:
                            SpecRepository(host.project_root, host.package_root).select(
                                change["target_id"], change["focus_id"]
                            )
                        except SpecError as error:
                            if error.code not in {"unknown_target", "invalid_focus"}:
                                raise
                            raise SpecError(
                                "recorded owner no longer resolves: " + str(error),
                                "invalid_worktree_state",
                            ) from error
                        host = replace(host, routed_target=change["target_id"])
            if host.routed_target is None:
                target_discovery = MainInvocation(operation, configuration, task, host)
                target_discovery_nodes = target_discovery.discovery_nodes()
                return {
                    "route": "discover",
                    "occurrence": 0,
                    "routes": [],
                    "decision": None,
                }
        return {"route": "bind_target"}

    def bind_target(state):
        nonlocal task, host, run
        main_completed: tuple[str, ...] = ()
        if target_discovery is not None:
            route, blocked = target_discovery.select_discovered(
                state["routes"], state["decision"]
            )
            if blocked is not None:
                return {"output": blocked, "route": END}
            if route is None:
                raise SpecError(
                    "discovery did not select an owner", "invalid_completion"
                )
            task = {
                **task,
                "target_id": route["target_id"],
                "task": route["task"],
                "constraints": route["constraints"],
            }
            if route["focus_id"] is not None:
                task["focus_id"] = route["focus_id"]
            else:
                task.pop("focus_id", None)
            host = replace(host, routed_target=route["target_id"])
            main_completed = tuple(target_discovery.completed)
        readonly = operation in {
            "concorde-main",
            "concorde-context-solve",
            "concorde-review",
        }
        readonly = readonly or (
            operation == "concorde-issues"
            and (task["action"] != "solve" or task.get("_issue_closed"))
        )
        if host.mode == "execute" and not readonly:
            SpecRepository(host.project_root, host.package_root).select(
                task["target_id"], task.get("focus_id")
            )
            bind_owner(host.project_root, task, coordinated=host.coordinated)
        run = Invocation(operation, configuration, task, host)
        bound_run().completed.extend(main_completed)
        route = (
            "review"
            if operation == "concorde-review"
            else (
                "describe_policy"
                if host.mode == "describe-policy"
                else {
                    "concorde-issues": "issues",
                    "concorde-specify": "specify",
                    "concorde-plan": "plan",
                    "concorde-tasks": "tasks",
                    "concorde-implement": "implement",
                    "concorde-validate": "validate",
                    "concorde-dev-loop": "development_loop",
                    "concorde-specify-loop": "specify_loop",
                }.get(operation, "context_solve")
            )
        )
        return {"route": route}

    target_nodes = {
        "initialize_target": initialize_target,
        "bind_target": bind_target,
        **{
            name: (lambda state, name=name: target_discovery_nodes[name](state))
            for name in ("decide", "expand_context", "bind_routes", "finish")
        },
    }

    def describe_policy():
        if operation == "concorde-issues" and (
            task["action"] != "solve" or task.get("_issue_closed")
        ):
            return bound_run().response(
                "described",
                "This Issue operation uses host bookkeeping only; no worker or candidate is launched.",
            )
        stages = [operation] if operation in MODEL_STAGES else []
        describe_reviews = False
        if operation == "concorde-dev-loop":
            describe_reviews = task.get("run_reviews", True)
            stages = ["concorde-context-solve", "concorde-plan", "concorde-tasks"]
            if bound_run().target.files:
                stages.append("concorde-implement")
            if task.get("specify", True):
                stages.insert(0, "concorde-specify")
        if operation == "concorde-specify-loop":
            if task.get("specify", True):
                bound_run().stage("concorde-specify")
            if task.get("run_reviews", True):
                from .review import review

                review(bound_run(), "spec")
            return bound_run().response("described")
        for stage in stages:
            if stage == "concorde-context-solve" and describe_reviews:
                from .review import review

                review(bound_run(), "spec")
            bound_run().stage(stage)
        if describe_reviews and bound_run().target.files:
            from .review import review

            review(bound_run(), "code")
        return bound_run().response("described")

    def deliver():
        from ..harness.worktree_delivery import deliver

        return deliver(host, configuration, task)

    def project():
        if host.mode == "describe-policy":
            raise SpecError(
                "project proposals are the deterministic preview for this operation",
                "use_proposal",
            )
        return _project_operation(operation, configuration, task, host)

    def review():
        from .review import review_scope

        return review_scope(bound_run(), task["review_mode"])

    def issues():
        from ..issues.graph import build_issue_graph, issue_nodes

        return build_issue_graph(issue_nodes(bound_run()).__getitem__).invoke(
            {}, {"recursion_limit": 64}
        )["output"]

    def context_solve():
        result = bound_run().stage(operation)
        return bound_run().response(
            "completed" if result["outcome"] == "sufficient" else result["outcome"],
            result["answer"],
            blockers=result["blockers"],
        )

    operations = {
        "deliver": deliver,
        "project": project,
        "answer": lambda: MainInvocation(
            operation, configuration, task, host
        ).run_answer(),
        "design_topology": lambda: MainInvocation(
            operation, configuration, task, host
        ).run_topology_design(),
        "prepare_topology": lambda: _prepare_topology(
            configuration, task["topology_proposal"], host
        ),
        "apply_topology": lambda: _apply_topology(task["application"], host),
        "review": review,
        "describe_policy": describe_policy,
        "issues": issues,
        "specify": lambda: bound_run().author(operation),
        "plan": lambda: bound_run().plan(),
        "tasks": lambda: bound_run().tasks(),
        "implement": lambda: bound_run().implement(),
        "validate": lambda: bound_run().validate(task.get("run_checks", True)),
        "development_loop": lambda: bound_run().loop(),
        "context_solve": context_solve,
    }
    nodes = {
        name: (lambda state, operation=operation: {"output": operation()})
        for name, operation in operations.items()
    }
    subgraphs = {}

    def subgraph(name, child, state):
        if name not in subgraphs:
            if name == "prepare_target":
                subgraphs[name] = target_nodes
            elif name in {"answer", "design_topology"}:
                main = MainInvocation(operation, configuration, task, host)
                response = (
                    main.answer_response if name == "answer" else main.topology_response
                )
                subgraphs[name] = {
                    **main.discovery_nodes(),
                    "respond": lambda state: {"output": response(state["decision"])},
                }
            elif name == "prepare_topology":
                subgraphs[name] = _topology_nodes(
                    configuration, task["topology_proposal"], host
                )
            elif name == "apply_topology":
                subgraphs[name] = _topology_apply_nodes(task["application"], host)
            elif name == "project":
                subgraphs[name] = _project_nodes(operation, configuration, task, host)
            elif name == "plan":
                subgraphs[name] = bound_run().plan_nodes()
            elif name == "specify_loop":
                from .specify_graph import specify_nodes

                subgraphs[name] = specify_nodes(bound_run())
            elif name == "development_loop":
                subgraphs[name] = bound_run().loop_nodes()
            elif name == "issues":
                from ..issues.graph import issue_nodes

                subgraphs[name] = issue_nodes(bound_run())
        return subgraphs[name][child](state)

    from .dispatch_graph import SUBGRAPH_NODES

    return {
        "select_operation": select_operation,
        **nodes,
        **{
            name + "/" + child: (
                lambda state, name=name, child=child: subgraph(name, child, state)
            )
            for name, children in SUBGRAPH_NODES.items()
            for child in children
        },
    }


def run_operation(
    operation: str,
    configuration: dict | None,
    runtime_input: dict,
    *,
    host_context: OperationHost,
) -> dict:
    from .operation_graph import OPERATION_RECURSION_LIMIT, build_operation_graph

    nodes = operation_graph_nodes(
        operation, configuration, runtime_input, host_context=host_context
    )
    try:
        return build_operation_graph(nodes.__getitem__, name=operation).invoke(
            {}, {"recursion_limit": OPERATION_RECURSION_LIMIT}
        )["result"]
    except KeyboardInterrupt:
        # A host interrupt (Ctrl-C, or SIGTERM from the developer's client) that arrives outside
        # a worker launch ends the Graph the way a cancelled worker does: the cancellation is
        # recorded in the change's lifecycle evidence and reported through the result envelope.
        cancelled = OperationExecutionError(
            "operation cancelled by the host", outcome="cancelled"
        )
        return finish_failed_operation_graph(nodes, cancelled)["result"]
    except Exception as error:
        return finish_failed_operation_graph(nodes, error)["result"]


def finish_failed_operation_graph(nodes, error):
    """A scheduler failure still uses the host's error envelope and final lifecycle evidence."""
    nodes["fail"]({"error": error})
    return nodes["finalize"]({})


def operation_graph_nodes(operation, configuration, runtime_input, *, host_context):
    """Fresh trusted node bindings; neither host authority nor callbacks enter the public input."""
    from langgraph.graph import END
    from langgraph.types import Command

    # A depth-1 (top-level) invocation never inherits a lifecycle status a prior invocation on
    # this same host object left behind; nested calls still share the one dict by reference so a
    # child's cancelled/limit_exhausted outcome keeps propagating to its enclosing loop.
    lifecycle = {} if host_context.depth == 0 else host_context.lifecycle
    invocation_id = str(uuid.uuid4())
    host = replace(
        host_context,
        invocation_id=invocation_id,
        evidence=[],
        depth=host_context.depth + 1,
        lifecycle=lifecycle,
        root_invocation_id=host_context.root_invocation_id or invocation_id,
    )
    record_progress = False
    task = None
    mutation = False
    host.observe(
        "operation_started",
        operation=operation,
        invocation_id=host.invocation_id,
        depth=host.depth,
    )
    result = {
        "type_id": "concorde-operation-result",
        "schema_version": 3,
        "operation_id": operation if operation in OPERATION_CONTRACTS else None,
        "invocation_id": host.invocation_id,
        "mode": host.mode,
        "status": "blocked",
        "workspace": None,
        "output": None,
        "errors": [],
    }

    def admit_request():
        nonlocal configuration, task, mutation
        if operation not in OPERATION_CONTRACTS:
            raise SpecError("unknown registered operation", "unknown_operation")
        if host.mode not in {"execute", "describe-policy"}:
            raise SpecError("unknown operation mode", "invalid_input")
        if host.depth == 1 and operation not in DETERMINISTIC_OPERATIONS:
            # The build is the only instruction source. Deterministic operations run no agent
            # cognition and load no WorkerProfile, so they never consume generated/; every other
            # top-level invocation is verified once here, and load_model_instructions verifies it
            # again independently before trusting any generated/agents/*.md body.
            verify_fresh(host.package_root)
        configuration = validate_typed(
            configuration
            if configuration is not None
            else load_configuration(host.project_root),
            "concorde-operation-configuration",
        )
        task = validate_typed(runtime_input, OPERATION_CONTRACTS[operation][0])["data"]
        task = copy.deepcopy(task)
        if operation not in {"concorde-deliver", "concorde-issues"} and not (
            operation == MAIN_OPERATION
            and task.get("action") in {"accept-topology", "apply-topology"}
        ):
            task.setdefault("task", "Inspect the selected records")
        mutation = operation not in {
            "concorde-main",
            "concorde-context-solve",
            "concorde-review",
        }
        if operation == "concorde-init":
            mutation = task["action"] == "apply"
        if operation == MAIN_OPERATION:
            mutation = task["action"] in {"accept-topology", "apply-topology"}
        if operation == "concorde-issues":
            from ..issues.graph import prepare_request

            # Issue selection, attribution and current bytes are host-bound before workspace creation.
            task = prepare_request(host.project_root, host.package_root, task)
            mutation = task["action"] == "solve" and not task.get("_issue_closed")

    def bind_workspace():
        nonlocal host, record_progress
        assert task is not None, "workspace binding requires an admitted task"
        if operation == "concorde-deliver":
            from ..harness.worktree_delivery import require_delivery_session

            primary = require_delivery_session(host, task["change_id"])
            workspace = {"path": primary["path"], "branch": primary["branch"]}
        elif operation == "concorde-issues" and (
            task["action"] != "solve" or task.get("_issue_closed")
        ):
            workspace = (
                None  # bookkeeping operations do not create a development candidate
            )
        else:
            host, workspace = _worktree(host, mutation, task)
        result["workspace"] = workspace
        if workspace and workspace.get("handoff"):
            if operation == "concorde-issues":
                from ..issues.graph import copy_selection

                copy_selection(host.project_root, Path(workspace["path"]), task)
            from ..harness.session_handoff import handoff_prompt

            prompt = handoff_prompt(
                workspace["path"],
                branch=workspace.get("branch"),
                change_id=workspace.get("change_id"),
                task=task["task"]
                if operation == "concorde-issues"
                else runtime_input["data"].get("task"),
                constraints=runtime_input["data"].get("constraints"),
                completed="The host prepared a linked worktree from the committed base and local change state. "
                "No task agent has run in it during this invocation.",
                remaining=f"Resume {operation} for this change with the original task and constraints.",
                checks="Worktree preparation succeeded; task implementation/review/validation have not run "
                "during this invocation.",
                artifacts=[
                    {
                        "path": str(
                            Path(workspace["path"]) / ".concorde/worktree.json"
                        ),
                        "applied": True,
                        "temporary": True,
                        "storage": "create_worktree used a temporary directory; preserve it until completion",
                    }
                ],
                next_steps=f"Resume {operation} with change_id {workspace.get('change_id')} in the initial "
                "directory after policy verification. The host must resolve fresh bounded contexts."
                + (
                    f" Select issue_id {task['issue_id']} with expected_revision {task['expected_revision']}."
                    if operation == "concorde-issues"
                    else ""
                ),
                completion=(
                    "Complete Spec authoring and required Spec review, then return completed before planning "
                    "or implementation. The same change can continue through concorde-dev-loop."
                    if operation == "concorde-specify-loop"
                    else "Complete the accepted task and its required checks; development loops stop at ready. "
                    "Delivery requires the user's separate request from a participating worktree session."
                ),
            )
            raise SpecError(
                "Change worktree prepared at "
                + workspace["path"]
                + ". The outer agent must initiate the P10 handoff to a fresh session in that worktree.\n\n"
                + prompt,
                "worktree_handoff_required",
            )
        record_progress = (
            mutation and operation != "concorde-deliver" and host.depth == 1
        )
        if mutation and operation != "concorde-deliver":
            change = read_change(host.project_root)
            if change and change["status"] in {"delivering", "cleanup_pending"}:
                record_progress = False
                raise SpecError(
                    "this candidate is being delivered; resume delivery from either participating worktree",
                    "delivery_in_progress",
                )

    def check_configuration():
        nonlocal host
        if operation != "concorde-init" and configuration != load_configuration(
            host.project_root
        ):
            raise SpecError(
                "invocation configuration differs from initialized project settings",
                "configuration_mismatch",
            )
        if host.configuration_snapshot and host.configuration_snapshot != canonical(
            configuration
        ):
            raise SpecError(
                "child configuration differs from the host snapshot",
                "configuration_mismatch",
            )
        host = replace(host, configuration_snapshot=canonical(configuration))

    def accept_output(output):
        outcome = output["data"].get("outcome", "completed")
        result.update(
            output=output,
            status="described"
            if host.mode == "describe-policy"
            else "succeeded"
            if outcome
            in {
                "completed",
                "ready",
                "delivered",
                "topology_proposed",
                "topology_prepared",
                "topology_applied",
            }
            else "failed"
            if outcome == "failed"
            else "blocked",
        )

    dispatch_nodes = None

    def dispatch(name, state):
        nonlocal dispatch_nodes
        if dispatch_nodes is None:
            dispatch_nodes = _dispatch_nodes(operation, configuration, task, host)
        updates = dispatch_nodes[name](state)
        payload = (updates.update or {}) if isinstance(updates, Command) else updates
        if (
            isinstance(payload.get("output"), dict)
            and payload["output"].get("type_id") == OPERATION_CONTRACTS[operation][1]
        ):
            accept_output(payload["output"])
        return updates

    def guarded(operation, *, accepts_state=False):
        def node(state):
            updates = {}
            try:
                updates = (operation(state) if accepts_state else operation()) or {}
            except OperationExecutionError as error:
                lifecycle_status = (
                    "cancelled"
                    if error.outcome == "cancelled"
                    else "limit_exhausted"
                    if error.outcome == "limit_exhausted"
                    else "failed"
                )
                code = (
                    "execution_cancelled"
                    if error.outcome == "cancelled"
                    else "execution_limit"
                    if error.outcome == "limit_exhausted"
                    else "execution_failed"
                )
                host.lifecycle["status"] = lifecycle_status
                result.update(
                    status="failed",
                    errors=[{"code": code, "field": "", "message": str(error)}],
                )
                if error.code:
                    host.lifecycle["status"] = "blocked"
                    result.update(
                        status="blocked",
                        errors=[
                            {"code": error.code, "field": "", "message": str(error)}
                        ],
                    )
            except (SpecError, TypedDataError, ContractError) as error:
                result["errors"] = [
                    {"code": error.code, "field": error.field, "message": str(error)}
                ]
            except BuildError as error:
                result["errors"] = [
                    {"code": error.code, "field": "", "message": str(error)}
                ]
            except Exception as error:
                result.update(
                    status="failed",
                    errors=[
                        {"code": "execution_failed", "field": "", "message": str(error)}
                    ],
                )
            if isinstance(updates, Command):
                # A node that selects its own transition keeps it unless the guard recorded an
                # error, which ends the Graph with the typed failure envelope in state.
                if result["errors"]:
                    return Command(
                        goto=END, update={**(updates.update or {}), "result": result}
                    )
                return Command(
                    goto=updates.goto, update={**(updates.update or {}), "result": None}
                )
            return {
                **updates,
                "result": result if result["errors"] else None,
                **({"route": "__end__"} if result["errors"] else {}),
            }

        return node

    def initialize(state):
        return {"result": None}

    def fail(state):
        def raise_failure():
            result["output"] = None
            raise state["error"]

        return guarded(raise_failure)(state)

    def finalize(state):
        nonlocal record_progress
        execution_error = host.lifecycle.get("execution_error")
        if execution_error and not result["errors"]:
            # Preserve the failed Review domain output and its incomplete report while
            # reporting the executor interruption through the existing envelope field.
            result["errors"] = [
                {
                    "code": execution_error,
                    "field": "",
                    "message": "Reviewer execution was interrupted.",
                }
            ]
        persistence_error = host.lifecycle.get("persistence_error")
        if persistence_error and not any(
            error["code"] == "state_persistence_failed" for error in result["errors"]
        ):
            # A lost status write is reported beside the retained typed output, never instead of it.
            result["errors"].append(
                {
                    "code": "state_persistence_failed",
                    "field": "",
                    "message": persistence_error,
                }
            )
        if any(
            error["code"]
            in {"incompatible_handoff", "workspace_mismatch", "invalid_worktree_state"}
            for error in result["errors"]
        ):
            record_progress = False
        if (
            record_progress
            and host.mode == "execute"
            and result["status"] not in {"succeeded", "described"}
        ):
            data = result["output"]["data"] if result["output"] else {}
            try:
                progress(
                    host.project_root,
                    status=host.lifecycle.get("status")
                    or ("blocked" if result["status"] == "blocked" else "failed"),
                    outcome=data.get("outcome")
                    or (result["errors"][0]["code"] if result["errors"] else "failed"),
                    blockers=data.get("blockers", []),
                )
            except (ValueError, OSError) as error:
                result["errors"].append(
                    {
                        "code": "state_persistence_failed",
                        "field": "",
                        "message": str(error),
                    }
                )
        host_context.evidence.extend(host.evidence)
        host.observe(
            "operation_finished",
            operation=operation,
            invocation_id=host.invocation_id,
            depth=host.depth,
            status=(
                host.lifecycle["status"]
                if host.lifecycle.get("status") in {"cancelled", "limit_exhausted"}
                else result["status"]
            ),
        )
        return {"result": result}

    from .dispatch_graph import DISPATCH_NODES

    return {
        "initialize": initialize,
        "admit_request": guarded(admit_request),
        "bind_workspace": guarded(bind_workspace),
        "check_configuration": guarded(check_configuration),
        "finalize": finalize,
        "fail": fail,
        **{
            "dispatch/" + name: guarded(
                lambda state, name=name: dispatch(name, state), accepts_state=True
            )
            for name in DISPATCH_NODES
        },
    }


def validate_invocation(value: Any, operation: str | None = None) -> dict:
    """Validate the shared CLI/Studio envelope before selecting a trusted host."""
    if not isinstance(value, dict) or set(value) != {
        "type_id",
        "schema_version",
        "operation_id",
        "mode",
        "configuration",
        "input",
    }:
        raise SpecError("invocation fields do not match schema 3", "invalid_input")
    if (
        value["type_id"] != "concorde-operation-invocation"
        or type(value["schema_version"]) is not int
        or value["schema_version"] != 3
    ):
        raise SpecError(
            "Profile 15 requires concorde-operation-invocation schema 3",
            "unsupported_version",
        )
    if operation is not None and value["operation_id"] != operation:
        raise SpecError(
            "invocation does not match this entry point", "incompatible_handoff"
        )
    return value


def invocation_failure(operation: str | None, error: Exception) -> dict:
    """The same pre-host failure envelope for paired CLI and Studio entries."""
    return {
        "type_id": "concorde-operation-result",
        "schema_version": 3,
        "operation_id": operation,
        "invocation_id": str(uuid.uuid4()),
        "mode": None,
        "status": "blocked",
        "workspace": None,
        "output": None,
        "errors": [
            {
                "code": getattr(error, "code", "invalid_input"),
                "field": getattr(error, "field", ""),
                "message": str(error),
            }
        ],
    }


def json_main(package_root: Path, operation: str, runner) -> int:
    """Shared stdin/limit/envelope/result handling for every skill's executable boundary.

    ``runner(state, runtime)`` is the Skill's Operation node. This boundary validates the wire
    envelope and adapts it to State plus trusted Runtime context; it does not dispatch by name. Only a skill has an executable
    boundary at all, so every caller already knows and validates its own ``operation`` before
    reaching here (``scripts/run-operation.py``); there is no internal/stage fallback to guard.
    """

    host = None
    try:
        if sys.argv[1:]:
            raise SpecError(
                "Operation inputs must be one JSON invocation on stdin", "invalid_input"
            )
        raw = getattr(sys.stdin, "buffer", sys.stdin).read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise SpecError("invocation exceeds 1 MiB", "invalid_input")
        value = validate_invocation(
            decode(raw.decode() if isinstance(raw, bytes) else raw), operation
        )
        if os.environ.get("CONCORDE_STUDIO_URL"):
            from ..harness.studio_client import run_in_studio

            state = run_in_studio(
                os.environ["CONCORDE_STUDIO_URL"], value, Path.cwd(), package_root
            )
            result = state["result"]
            if state.get("policies"):
                print(canonical({"policies": state["policies"]}), file=sys.stderr)
        else:
            host = OperationHost(Path.cwd(), package_root, mode=value["mode"])
            result = _run_host_node(
                runner, host, value["configuration"], value["input"], operation
            )

    except KeyboardInterrupt:
        result = invocation_failure(
            operation,
            SpecError("operation cancelled by the host", "execution_cancelled"),
        )
    except Exception as error:
        result = invocation_failure(operation, error)
    if host and host.descriptions:
        print(canonical({"policies": host.descriptions}), file=sys.stderr)
    if host is not None and result.get("invocation_id"):
        records = read_usage(host.project_root, result["invocation_id"])
        if records:
            summary = summarize_usage(records)
            print(
                canonical(
                    {
                        "usage": {
                            "root_invocation_id": result["invocation_id"],
                            "schema_version": summary["schema_version"],
                            "complete": summary["complete"],
                            "historical_records": summary["historical_records"],
                            "unsupported_records": summary["unsupported_records"],
                            "total": summary["total"],
                            "by_step": summary["by_step"],
                        }
                    }
                ),
                file=sys.stderr,
            )
    print(canonical(result))
    return 0 if result["status"] in {"succeeded", "described"} else 3
