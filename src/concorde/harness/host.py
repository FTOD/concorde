"""The trusted host of one operation invocation and the launch of its bound workers.

An ``OperationHost`` carries the project and package roots, the execution mode and the trusted
services one invocation shares with its nested invocations. The worker helpers below bind one
model-backed launch to its frozen context, compiled policy, worker binding and model selection,
and admit its single typed result.
"""

from __future__ import annotations

import importlib
import json
import tempfile
import uuid
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..spec.contracts import load_operation_inventory
from ..spec.repository import SpecError
from ..spec.typed_data import canonical, validate_typed
from .model_selection import worker_selection
from .usage import record_usage
from .worker_executor import WorkerOutcome, build_worker_invocation, worker_instructions
from .worker_profile import binding_json, external_worker_name, worker_profile
from .worker_sandbox import WORKER_SANDBOX_POLICY


@dataclass(frozen=True)
class OperationHost:
    project_root: Path
    package_root: Path
    mode: str = "execute"
    executor: Any = None
    allow_primary_worktree: bool = False
    outer_sandbox: str | None = None
    # A mutation admitted in the primary worktree runs in a host-created candidate worktree.
    # ``relay`` runs the same invocation there (``relay_operation``, the candidate's own launcher
    # in a subprocess, unless a trusted caller supplies another runner) and ``relay_target``
    # names that candidate once bind_workspace prepared it.
    relay: Any = None
    relay_target: dict | None = None
    configuration_snapshot: str = ""
    session_root: Path | None = None
    archive_root: Path | None = None
    session_provenance: dict | None = None
    coordinated: bool = False
    track_gaps: bool = False
    defer_ready: bool = False
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


def protocol_documents(
    value: dict, granted: dict[str, bytes]
) -> list[tuple[str, bytes]]:
    """The Protocol files a context index lists, in its order, with their verified bytes."""
    return [(record["path"], granted[record["path"]]) for record in value["protocol"]]


def worker_invocation(
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


def worker_description(prompt, invocation, policy, **labels) -> dict:
    """The describe-policy record of one worker launch: its grant, profile and model selection."""
    agent = worker_profile(prompt.binding.agent)
    return {
        **labels,
        "read_paths": list(policy.read_paths),
        "write_paths": list(policy.write_paths),
        "network": False,
        "fresh_session": True,
        "sandbox": WORKER_SANDBOX_POLICY,
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


def _record_worker_failure(host, invocation, error) -> str | None:
    """Keep bounded stderr in a private run artifact, never in events or public State.

    No prompts, RPC events, tool results or credential files are serialized. A diagnostic
    write failure must not replace the original execution failure or cause a retry.
    """
    if error.run is None:
        return None
    try:
        from .status_store import primary_root, run_path

        directory = run_path(
            host.project_root,
            f".concorde/runs/{host.root_invocation_id or host.invocation_id}",
        )
        directory.mkdir(parents=True, exist_ok=True)
        record = {
            "launch_invocation_id": invocation.invocation_id,
            "agent": invocation.agent,
            "outcome": error.outcome,
            "exit_code": error.run.exit_code,
            "wall_seconds": error.run.wall_seconds,
            "stderr_tail": error.run.stderr.encode("utf-8")[-20000:].decode(
                "utf-8", "ignore"
            ),
        }
        # Exclusive creation with mode 0600 avoids exposing diagnostics through umask
        # defaults, existing files or symlink aliases. These are not worker grants.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="worker-",
            suffix=".json",
            dir=directory,
            delete=False,
        ) as stream:
            json.dump(record, stream, sort_keys=True)
            stream.write("\n")
            return (
                Path(stream.name)
                .relative_to(primary_root(host.project_root))
                .as_posix()
            )
    except (OSError, ValueError):
        return None


def run_worker(
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
    from ..issues.reporting import reporter_for_invocation
    from .worker_executor import OperationExecutionError, WorkerExecutor

    executor = host.executor or WorkerExecutor(host.package_root)
    reporter = reporter_for_invocation(
        host.project_root, invocation, target_id=target_id, change_id=change_id
    )
    try:
        outcome = executor(invocation, checks=checks, report_issue=reporter)
    except OperationExecutionError as error:
        diagnostic = _record_worker_failure(host, invocation, error)
        if diagnostic is not None:
            raise OperationExecutionError(
                f"{error}; see host diagnostic {diagnostic}",
                outcome=error.outcome,
                code=error.code,
                usage=error.usage,
                run=error.run,
            ) from error
        raise
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
