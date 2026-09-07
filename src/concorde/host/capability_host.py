"""Trusted execution of every public Concorde capability under Profile 8.

Agents consume frozen Spec snapshots. Deterministic checks execute separately and their raw
output never becomes a non-implementation agent input. Each stage starts a fresh process.
"""
from __future__ import annotations

import copy
import importlib
import json
import os
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass, field, replace, asdict
from pathlib import Path
from typing import Any

from .typed_data import (CAPABILITY_CONTRACTS, TypedDataError, canonical, checked_path,
    decode, typed, validate_typed, artifact, verify_artifacts)
from .configuration import load_configuration
from .permissions import (PolicyBinding, compile_policy, render_codex_configuration,
    render_claude_configuration, build_launch_specification, CapabilityExecutionResult)
from .build import BuildError, load_role_prompt, verify_fresh
from .effects import EffectDeclaration
from .contracts import (STAGE_ROLES, TARGET_AGENT_STAGES,
    MAIN_CAPABILITY, MAIN_ROUTED_CAPABILITIES, LIFECYCLE_CAPABILITIES, load_capability_inventory)
from .change_worktree import (STATE_PATH, WORK_PATH, bind_owner, create_worktree,
    ensure_change, progress, read_change, refresh_registry, save_change,
    save_target_state, snapshot_tree, target_state, work_path, workspace_context,
    workspace_identity)
from ..specification.repository import SpecRepository, SpecError, digest, read_file, identifier
from ..specification.context import (DiscoveryContext, resolve_context,
    recheck_context, resolve_discovery_context,
    recheck_discovery_context, resolve_topology_author_context,
    recheck_topology_author_context)
from ..specification.changes import file_change, apply_files
from ..specification.validation import (validate_repository, document_context_findings,
    domain_participant_findings)


@dataclass(frozen=True)
class CapabilityHost:
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
    depth: int = 0
    invocation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    descriptions: list[dict] = field(default_factory=list)
    evidence: list[Any] = field(default_factory=list)
    observer: Any = None

    def observe(self, event: str, **details) -> None:
        # Observability must never turn a completed mutation into a retryable failure.
        if self.observer is not None:
            try:
                self.observer(event, **details)
            except Exception:
                pass

    def __post_init__(self):
        if self.project_root.is_symlink() or self.package_root.is_symlink():
            raise SpecError("host roots cannot be symlinks", "workspace_mismatch")
        object.__setattr__(self, "project_root", self.project_root.resolve())
        object.__setattr__(self, "package_root", self.package_root.resolve())
        object.__setattr__(self, "session_root", (self.session_root or self.project_root).resolve())


def _capability_key(capability: str) -> str:
    return capability[len("concorde-"):].replace("-", "_")


def resolve_child_capability(parent_capability: str, child_capability: str):
    """Return the child capability module for one in-process nested dispatch, or refuse it.

    A parent may always invoke itself (recursive fan-out across component targets, as
    ``review_scope`` and ``implement_scope`` do, is not capability composition and needs no
    declared edge). Any other child must appear in the parent capability module's declared
    ``USES``, or this raises ``SpecError(..., "undeclared_capability")``. Pure name resolution
    with no side effect beyond importing the two modules; kept separate from ``invoke_capability``
    so the declared composition graph can be checked exhaustively without executing anything.
    """

    inventory = load_capability_inventory()
    parent_key, child_key = _capability_key(parent_capability), _capability_key(child_capability)
    if parent_key != child_key:
        try:
            parent_module = importlib.import_module(f"{inventory.__name__}.{parent_key}")
        except ImportError as error:
            raise SpecError(f"unknown parent capability: {parent_capability}", "unknown_operation") from error
        if child_key not in parent_module.USES:
            raise SpecError(
                f"{parent_capability} has no declared composition edge to {child_capability}",
                "undeclared_capability",
            )
    try:
        return importlib.import_module(f"{inventory.__name__}.{child_key}")
    except ImportError as error:
        raise SpecError(f"unknown capability: {child_capability}", "unknown_operation") from error


def invoke_capability(parent_capability: str, child_capability: str, configuration: dict, payload: dict,
                      host: CapabilityHost) -> dict:
    """Invoke another capability module's ``run`` in-process (proposal section 6.3).

    Used by every nested dispatch the host performs on a parent capability's behalf: the stage
    graph inside ``dev_loop``'s ``Invocation.loop``, ``reflections_triage``'s composition of
    ``dev_loop`` and a Domain's own recursive per-component review routing. ``run_capability``
    remains the shared machinery every capability module's own ``run`` delegates to; this only
    resolves which module owns the call (see ``resolve_child_capability``).
    """

    child_module = resolve_child_capability(parent_capability, child_capability)
    return child_module.run(host, configuration, payload)


def _worktree(host: CapabilityHost, mutation: bool, task: dict) -> tuple[CapabilityHost, dict | None]:
    if host.mode == "describe-policy":
        return host, None
    primary, current = workspace_identity(host.project_root)
    if current is not None and current["path"] != primary["path"]:
        state = ensure_change(host.project_root, task=task if mutation else None,
                              change_id=task.get("change_id"))
        refresh_registry(host.project_root)
        return host, {key: state[key] for key in
                      ("path", "branch", "base_commit", "change_id", "primary_worktree")}
    if mutation and not host.allow_primary_worktree:
        if primary is None:
            raise SpecError("mutations require a committed Git worktree", "workspace_mismatch")
        # Preparing a worktree is a handoff, never permission to continue the
        # originating agent conversation against a different checkout.
        return host, {**create_worktree(host.project_root, task, package_root=host.package_root), "handoff": True}
    if mutation:
        ensure_change(host.project_root, task=task, change_id=task.get("change_id"),
                      allow_primary=True)
    if current is not None:
        refresh_registry(host.project_root)
    return host, None


def _implementation_digest(repository: SpecRepository, target) -> str:
    return digest([(path, digest(read_file(repository.root, path))) for path in repository.implementation_files(target)])


def _target_revision(repository: SpecRepository, target) -> str:
    return digest({"target": asdict(target), "protocol": repository.config["protocol"],
                   "documents": [(doc.path, doc.digest) for doc in repository.documents(target)]})


def _check_revision(repository: SpecRepository, target) -> str:
    inputs = []
    for check_id in target.checks:
        check=repository.checks[check_id]
        inputs.append((check_id, check))
        for relative in check.get("inputs", []):
            path=checked_path(repository.root, relative)
            members=sorted(p.relative_to(repository.root).as_posix() for p in path.rglob("*")
                if p.is_file() and "__pycache__" not in p.parts and p.suffix not in {".pyc",".pyo"}) if path.is_dir() else [relative]
            if path.is_dir() and any(p.is_symlink() for p in path.rglob("*")):
                raise SpecError("check input cannot contain symlinks", "unsafe_path")
            inputs.extend((member,digest(read_file(repository.root,member))) for member in members)
    return digest({"implementation":_implementation_digest(repository,target),"check_inputs":inputs})


def _check(repository: SpecRepository, target, invocation_id: str) -> list[dict]:
    """Only the host executes configured argv. Never send stdout/stderr to a Spec-only agent."""
    before = _check_revision(repository, target)
    results = []
    for check_id in target.checks:
        configured = repository.checks[check_id]
        argv = list(configured["argv"])
        if argv[0] == "{python}":
            argv[0] = sys.executable
        try:
            result = subprocess.run(argv, cwd=repository.root, capture_output=True,
                timeout=configured["timeout_seconds"], env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(repository.package_root / "src")})
            log = result.stdout + b"\n" + result.stderr
            status, code = ("passed" if result.returncode == 0 else "failed"), result.returncode
        except subprocess.TimeoutExpired as error:
            log = (error.stdout or b"") + b"\n" + (error.stderr or b"")
            status, code = "timeout", -1
        path = f".concorde/runs/{invocation_id}/{check_id}.log"
        # Logs are host/implementation evidence, absent from non-implementation context manifests.
        destination = checked_path(repository.root, path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(log)
        results.append({"check_id": check_id, "target_id": target.id, "status": status, "exit_code": code,
                        "source_digest": before, "log_digest": digest(log)})
    if _check_revision(repository, target) != before:
        raise SpecError("configured validation changed the implementation it measured", "stale_evidence")
    return results


class MainInvocation:
    """Global Domain/Service discovery followed by fresh target workers."""

    def __init__(self, capability: str, configuration: dict, task: dict, host: CapabilityHost):
        self.capability, self.configuration, self.task, self.host = capability, configuration, task, host
        if capability not in MAIN_ROUTED_CAPABILITIES:
            raise SpecError("capability does not support main discovery", "unknown_operation")
        self.action = task.get("action", "route") if capability == MAIN_CAPABILITY else "route"
        self.repository = SpecRepository(host.project_root, host.package_root)
        self.entry = self.repository.select(self.repository.entry_target)
        if self.entry.kind not in {"domain", "service"}:
            raise SpecError("the project entry target must be a Domain or Service for main discovery",
                            "invalid_entry_target")
        if task.get("focus_id") and not task.get("target_id"):
            raise SpecError("a focus hint requires a target hint", "invalid_focus")
        if task.get("target_id"):
            self.repository.select(task["target_id"], task.get("focus_id"))
        self.discovered = [self.entry.id]
        self.last_context: str | None = None
        self.last_snapshot: DiscoveryContext | None = None
        self.completed: list[str] = []

    def main_response(self, outcome: str, answer: str = "", *, routes=(), worker_results=(),
                      topology_proposal=None, application=None, files=(), gaps=()) -> dict:
        if self.last_context is None:
            raise SpecError("main response has no discovery context", "invalid_completion")
        return typed("concorde-main-response", {
            "action": self.action,
            "entry_target": self.entry.id,
            "context_id": self.last_context,
            "outcome": outcome,
            "answer": answer,
            "discovered_targets": list(self.discovered),
            "routes": list(routes),
            "worker_results": list(worker_results),
            "topology_proposal": topology_proposal,
            "application": application,
            "files": list(files),
            "gaps": list(gaps),
            "completed_operations": list(self.completed),
            "workspace": self.last_snapshot.value["workspace"],
        })

    def capability_response(self, outcome: str, answer: str = "", *, gaps=()) -> dict:
        if self.last_context is None:
            raise SpecError("main response has no discovery context", "invalid_completion")
        return typed(CAPABILITY_CONTRACTS[self.capability][1], {
            "target_id": self.entry.id,
            "focus_id": None,
            "change_id": self.task.get("change_id"),
            "context_id": self.last_context,
            "outcome": outcome,
            "answer": answer,
            "artifacts": [],
            "gaps": list(gaps),
            "checks": [],
            "completed_operations": list(self.completed),
            **({"reviews": []} if self.capability == "concorde-review" else {}),
        })

    def stage(self, phase: str, occurrence: int, *, worker_results: tuple[dict, ...] = ()) -> dict:
        role = "concorde-coordinator"
        prompt = load_role_prompt(self.host.package_root, role)
        snapshot = resolve_discovery_context(
            self.repository,
            tuple(self.discovered),
            operation=self.capability,
            phase=phase,
            task=self.task["task"],
            action=self.action,
            target_hint=self.task.get("target_id"),
            focus_hint=self.task.get("focus_id"),
            constraints=tuple(self.task.get("constraints", [])),
            instructions=prompt.body,
            worker_results=worker_results,
        )
        self.last_context = snapshot.id
        self.last_snapshot = snapshot
        before_registry = self.repository.registry_bytes
        with tempfile.TemporaryDirectory(prefix="concorde-discovery-") as directory:
            capsule = Path(directory)
            context_file = capsule / "context.json"
            if self.host.mode != "describe-policy":
                context_file.write_text(snapshot.serialized + "\n")
            roles = {"discovery-context": ("context.json",)}
            policy = compile_policy(
                EffectDeclaration(("discovery-context",), (), False, "none"),
                PolicyBinding(self.capability, phase, occurrence, role, role),
                roles,
                outer_sandbox_required=self.configuration["data"]["enforcement"] == "outer",
            )
            integration = self.configuration["data"]["integration"]
            renderer = render_codex_configuration if integration == "codex" else render_claude_configuration
            native = renderer(
                policy,
                native_enforcement=self.configuration["data"]["enforcement"] == "native",
                outer_sandbox=self.host.outer_sandbox,
            )
            receipt = {
                "schema_version": 14,
                "entry_target": self.entry.id,
                "phase": phase,
                "context_id": snapshot.id,
                "source_digest": snapshot.id,
                "registry_digest": digest(before_registry),
                "discovered_targets": list(self.discovered),
                "role_paths": {key: list(value) for key, value in roles.items()},
            }
            value = typed("concorde-main-stage-context", {
                "snapshot": typed("concorde-discovery-context", snapshot.value),
            })
            invocation_id = str(uuid.uuid4())
            launch = build_launch_specification(
                operation=self.capability,
                stage=phase,
                occurrence=occurrence,
                capability=role,
                integration=integration,
                agent=role,
                project_root=str(capsule),
                request=self.task["task"],
                prompt=prompt.body,
                prior_results=(),
                workspace_receipt_json=canonical(receipt),
                workspace_digest=snapshot.id,
                policy=policy,
                native_configuration=native,
                runtime_input_json=canonical(value),
                operation_configuration_json=canonical(self.configuration),
                invocation_id=invocation_id,
            )
            self.host.descriptions.append({
                "operation": self.capability,
                "phase": phase,
                "context_id": snapshot.id,
                "project_root": str(capsule),
                "read_paths": list(policy.read_paths),
                "write_paths": [],
                "network": False,
                "fresh_session": True,
                "policy_digest": policy.digest,
                "discovered_targets": list(self.discovered),
            })
            if self.host.mode == "describe-policy":
                return {"context_id": snapshot.id, "outcome": "described", "answer": "",
                        "expand_targets": [], "routes": [], "gaps": []}
            from .agent_executor import AgentProcessExecutor
            executor = self.host.executor or AgentProcessExecutor()
            result = executor(launch)
            if not isinstance(result, CapabilityExecutionResult):
                raise SpecError("main executor omitted native completion evidence", "invalid_completion")
            evidence = result.receipt
            if (evidence.requested_launch_digest != launch.digest or evidence.policy_digest != policy.digest
                    or evidence.status != "success" or result.completion.invocation_id != invocation_id
                    or result.completion.workspace_digest != snapshot.id):
                raise SpecError("main completion evidence is not bound to this invocation", "invalid_completion")
            data = validate_typed(result.completion.domain_output, "concorde-main-stage-result")["data"]
            self._validate_result(snapshot, phase, data)
            if read_file(self.repository.root, self.repository.registry_path) != before_registry:
                raise SpecError("registry changed during main discovery", "stale_context")
            recheck_discovery_context(self.repository, snapshot)
            if load_configuration(self.repository.root) != self.configuration:
                raise SpecError("configuration changed during main discovery", "configuration_mismatch")
            if context_file.read_text() != snapshot.serialized + "\n":
                raise SpecError("frozen discovery capsule changed", "stale_context")
            self.host.evidence.append(result)
            return data

    def _validate_result(self, snapshot: DiscoveryContext, phase: str, data: dict) -> None:
        if data["context_id"] != snapshot.id:
            raise SpecError("main returned a different discovery context identity", "incompatible_handoff")
        outcome = data["outcome"]
        expansions, routes, gaps = data["expand_targets"], data["routes"], data["gaps"]
        topology = data["topology_design"]
        if phase == "route":
            if outcome == "completed":
                if (self.capability != MAIN_CAPABILITY or self.action != "ask"
                        or expansions or routes or gaps or topology is not None or not data["answer"].strip()):
                    raise SpecError("direct main answers require only an answer from admitted workspace metadata", "invalid_completion")
            elif outcome == "expand":
                if not expansions or routes or gaps or topology is not None:
                    raise SpecError("expand requires only nonempty Domain/Service targets", "invalid_completion")
            elif outcome == "routed":
                if expansions or not routes or gaps or topology is not None:
                    raise SpecError("routed requires only nonempty worker routes", "invalid_completion")
            elif outcome == "topology_proposed":
                if (self.action != "design-topology" or expansions or routes or gaps
                        or topology is None):
                    raise SpecError("topology design has inconsistent fields", "invalid_completion")
            elif outcome in {"spec_incomplete", "unsupported", "conflicting", "failed"}:
                if (expansions or routes or topology is not None
                        or ((outcome == "spec_incomplete") != bool(gaps))):
                    raise SpecError("blocked main routing has inconsistent fields", "invalid_completion")
            else:
                raise SpecError("route phase returned an unsupported outcome", "invalid_completion")
        elif outcome not in {"completed", "spec_incomplete", "unsupported", "conflicting", "failed"}:
            raise SpecError("synthesis returned an unsupported outcome", "invalid_completion")
        elif expansions or routes or topology is not None or ((outcome == "spec_incomplete") != bool(gaps)):
            raise SpecError("synthesis result has inconsistent fields", "invalid_completion")
        admitted = set(self.discovered)
        worker_gaps = []
        if phase == "synthesize":
            admitted.update(item["data"]["target_id"] for item in snapshot.value["worker_results"])
            worker_gaps = [gap for item in snapshot.value["worker_results"]
                           for gap in item["data"]["gaps"]]
            if any(gap not in gaps for gap in worker_gaps):
                raise SpecError("main synthesis omitted a worker Spec gap", "invalid_completion")
        for gap in gaps:
            if gap.get("target_id") not in admitted:
                raise SpecError("main gap must identify an admitted discovery or worker target", "incompatible_handoff")
            if gap in worker_gaps:
                continue
            if gap.get("context_id", snapshot.id) != snapshot.id:
                raise SpecError("main gap has a different context identity", "incompatible_handoff")
            gap["context_id"] = snapshot.id

    def discover_routes(self) -> tuple[list[dict], dict | None]:
        if self.host.mode == "describe-policy":
            decision = self.stage("route", 0)
            if self.task.get("target_id"):
                return [{"target_id": self.task["target_id"], "focus_id": self.task.get("focus_id"),
                         "task": self.task["task"], "constraints": self.task.get("constraints", [])}], None
            return [], decision

        routable_targets = sum(target.kind in {"domain", "service"}
                               for target in self.repository.targets.values())
        for occurrence in range(routable_targets + 1):
            decision = self.stage("route", occurrence)
            if decision["outcome"] == "expand":
                admitted_text = "\n".join(document["content"]
                    for target in self.stage_context_targets(decision)
                    for section in ("target_spec", "shared_specs")
                    for document in target[section])
                for target_id in decision["expand_targets"]:
                    if target_id in self.discovered:
                        raise SpecError("main discovery requested an already admitted target", "invalid_completion")
                    if target_id != self.task.get("target_id") and target_id not in admitted_text:
                        raise SpecError("main discovery requested a target absent from admitted Specs",
                                        "incompatible_handoff", target_id)
                    target = self.repository.select(target_id)
                    if target.kind not in {"domain", "service"}:
                        raise SpecError("main discovery cannot expand a Module Spec", "permission_denied", target_id)
                    self.discovered.append(target_id)
                continue
            if decision["outcome"] == "routed":
                routes = decision["routes"]
                original_constraints = self.task.get("constraints", [])
                routing_text = "\n".join(document["content"]
                    for target in self.stage_context_targets(decision)
                    for section in ("target_spec", "shared_specs")
                    for document in target[section])
                for route in routes:
                    self.repository.select(route["target_id"], route["focus_id"])
                    if route["target_id"] not in self.discovered and route["target_id"] not in routing_text:
                        raise SpecError("main routed a target absent from admitted Domain/Service Specs",
                                        "incompatible_handoff", route["target_id"])
                    if any(item not in route["constraints"] for item in original_constraints):
                        raise SpecError("main route dropped a user constraint", "incompatible_handoff")
                    if self.capability != MAIN_CAPABILITY and (
                            route["task"] != self.task["task"]
                            or route["constraints"] != original_constraints):
                        raise SpecError("main route changed single-target task intent", "incompatible_handoff")
                return routes, None
            self.completed.append("concorde-coordinator-route")
            return [], decision
        raise SpecError("main discovery step limit exceeded", "context_limit")

    def stage_context_targets(self, decision: dict) -> list[dict]:
        """Return the exact collections bound to the decision's discovery identity."""

        if decision["context_id"] != self.last_context or self.last_snapshot is None:
            raise SpecError("main route no longer matches its discovery context", "stale_context")
        return self.last_snapshot.value["targets"]

    def select_one(self) -> tuple[dict | None, dict | None]:
        routes, decision = self.discover_routes()
        if decision is not None:
            outcome = "described" if self.host.mode == "describe-policy" else decision["outcome"]
            return None, self.capability_response(outcome, decision["answer"], gaps=decision["gaps"])
        if len(routes) != 1:
            raise SpecError(
                f"{self.capability} requires one owning target; route cross-target work through a Domain",
                "ambiguous_route",
            )
        self.completed.append("concorde-coordinator-route")
        return routes[0], None

    def run_answer(self) -> dict:
        routes, decision = self.discover_routes()
        if decision is not None:
            outcome = "described" if self.host.mode == "describe-policy" else decision["outcome"]
            return self.main_response(outcome, decision["answer"], gaps=decision["gaps"])

        if self.host.mode == "describe-policy":
            for route in routes:
                worker_task = {"target_id": route["target_id"], "task": route["task"],
                               "constraints": route["constraints"]}
                if route["focus_id"] is not None:
                    worker_task["focus_id"] = route["focus_id"]
                Invocation(MAIN_CAPABILITY, self.configuration, worker_task, self.host).stage("concorde-read-target")
            self.completed.extend(["concorde-coordinator-route", *("concorde-reader" for _ in routes)])
            return self.main_response("described", routes=routes)

        worker_results = []
        for route in routes:
            self.repository.select(route["target_id"], route["focus_id"])
            worker_task = {"target_id": route["target_id"], "task": route["task"],
                           "constraints": route["constraints"]}
            if route["focus_id"] is not None:
                worker_task["focus_id"] = route["focus_id"]
            worker = Invocation(MAIN_CAPABILITY, self.configuration, worker_task, self.host)
            result = worker.stage("concorde-read-target")
            outcome = "completed" if result["outcome"] == "sufficient" else result["outcome"]
            worker_results.append(typed("concorde-main-worker-result", {
                "target_id": route["target_id"],
                "focus_id": route["focus_id"],
                "context_id": result["context_id"],
                "outcome": outcome,
                "answer": result["answer"],
                "gaps": result["gaps"],
            }))
        self.completed.extend(["concorde-coordinator-route", *("concorde-reader" for _ in routes)])
        synthesis = self.stage("synthesize", len(self.discovered), worker_results=tuple(worker_results))
        if any(item["data"]["outcome"] != "completed" for item in worker_results) and synthesis["outcome"] == "completed":
            raise SpecError("main synthesis cannot hide a blocked worker outcome", "invalid_completion")
        self.completed.append("concorde-coordinator-synthesize")
        return self.main_response(synthesis["outcome"], synthesis["answer"], routes=routes,
                                  worker_results=worker_results, gaps=synthesis["gaps"])

    def run_topology_design(self) -> dict:
        routes, decision = self.discover_routes()
        if self.host.mode == "describe-policy":
            return self.main_response("described")
        if decision is None or decision["outcome"] != "topology_proposed":
            if decision is None:
                raise SpecError("topology design returned worker routes", "invalid_completion")
            return self.main_response(decision["outcome"], decision["answer"], gaps=decision["gaps"])
        _inspect_topology_design(
            self.repository,
            decision["topology_design"],
            tuple(self.discovered),
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
        proposal = typed("concorde-topology-proposal", {
            "proposal_id": digest(payload), **payload,
        })
        self.completed.append("concorde-coordinator-topology-design")
        return self.main_response("topology_proposed", decision["answer"],
                                  topology_proposal=proposal)


def _inspect_topology_design(repository: SpecRepository, design_value: dict,
                             discovered_targets: tuple[str, ...]) -> tuple[dict, dict, bytes,
                                                                          dict[str, dict],
                                                                          dict[str, dict],
                                                                          dict[str, str]]:
    """Validate everything knowable before target-local document authoring."""

    design = validate_typed(design_value, "concorde-topology-design")["data"]
    candidate = copy.deepcopy(design["registry"])
    if candidate["project_id"] != repository.registry["project_id"]:
        raise SpecError("topology design cannot replace project identity", "invalid_proposal")
    candidate_bytes = (json.dumps(candidate, indent=2, sort_keys=True) + "\n").encode()
    # This validates IDs, parentage, ownership, focus/check references and entry selection without
    # opening the candidate document paths. Their existence/content is validated after authoring.
    try:
        SpecRepository(repository.root, repository.package_root, registry_bytes=candidate_bytes)
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
        raise SpecError("topology design contains duplicate Spec tasks", "invalid_proposal")
    if any(target_id not in candidate_targets for target_id in tasks):
        raise SpecError("topology Spec task names a removed or unknown target", "invalid_proposal")
    changed = {target_id for target_id, target in candidate_targets.items()
               if current_targets.get(target_id) != target}
    changed.update(set(current_targets) - set(candidate_targets))
    current_document_references: dict[str, set[str]] = {}
    candidate_document_references: dict[str, set[str]] = {}
    for target_id, target in current_targets.items():
        for path in target["documents"]:
            current_document_references.setdefault(path, set()).add(target_id)
    for target_id, target in candidate_targets.items():
        for path in target["documents"]:
            candidate_document_references.setdefault(path, set()).add(target_id)
    changed_memberships = {path for path in
        set(current_document_references) | set(candidate_document_references)
        if current_document_references.get(path, set()) != candidate_document_references.get(path, set())}
    affected_document_targets = set()
    for path in changed_memberships:
        affected_document_targets.update(current_document_references.get(path, set()))
        affected_document_targets.update(candidate_document_references.get(path, set()))
    missing_document_tasks = sorted(target_id for target_id in affected_document_targets
        if target_id in candidate_targets and target_id not in tasks)
    if missing_document_tasks:
        raise SpecError(
            f"changed document sharing requires every retained referencing target task: {missing_document_tasks}",
            "invalid_proposal",
        )
    current_edges = {(target_id, domain_id)
        for target_id, target in current_targets.items() if target["kind"] != "domain"
        for domain_id in target["participates_in"]}
    candidate_edges = {(target_id, domain_id)
        for target_id, target in candidate_targets.items() if target["kind"] != "domain"
        for domain_id in target["participates_in"]}
    affected_domains = {domain_id for _, domain_id in current_edges ^ candidate_edges}
    for target_id in set(current_targets) & set(candidate_targets):
        if current_targets[target_id]["kind"] != candidate_targets[target_id]["kind"]:
            affected_domains.update(current_targets[target_id]["participates_in"])
            affected_domains.update(candidate_targets[target_id]["participates_in"])
    affected_domains.update(
        finding.subject_id for finding in domain_participant_findings(repository)
        if finding.subject_id is not None
    )
    missing_domain_tasks = sorted(domain_id for domain_id in affected_domains
        if domain_id in candidate_targets and domain_id not in tasks)
    if missing_domain_tasks:
        raise SpecError(
            f"changed or incomplete participation requires Domain Spec tasks: {missing_domain_tasks}",
            "invalid_proposal",
        )
    discovered = set(discovered_targets)
    unread_existing = sorted(target_id for target_id in (changed | tasks.keys())
        if target_id in current_targets and current_targets[target_id]["kind"] in {"domain", "service"}
        and target_id not in discovered)
    if unread_existing:
        raise SpecError(f"topology design did not admit affected Domain/Service Specs: {unread_existing}",
                        "invalid_proposal")
    missing_tasks = sorted((changed & candidate_targets.keys()) - tasks.keys())
    if missing_tasks:
        raise SpecError(f"changed topology targets require local Spec tasks: {missing_tasks}",
                        "invalid_proposal")
    if candidate == repository.registry and not tasks:
        raise SpecError("topology proposal contains no change", "invalid_proposal")
    return design, candidate, candidate_bytes, current_targets, candidate_targets, tasks


def _validate_topology_proposal(host: CapabilityHost, proposal: dict) -> tuple[SpecRepository, dict]:
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
    prompt = load_role_prompt(host.package_root, "concorde-coordinator")
    snapshot = resolve_discovery_context(
        repository,
        tuple(data["discovered_targets"]),
        operation=MAIN_CAPABILITY,
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


def _topology_author(repository: SpecRepository, configuration: dict, host: CapabilityHost,
                     target: dict, task: str, occurrence: int,
                     candidate_document_references: tuple[dict, ...]) -> dict:
    role = "concorde-spec-author"
    prompt = load_role_prompt(host.package_root, role)
    snapshot = resolve_topology_author_context(repository, target, task=task, instructions=prompt.body,
        candidate_document_references=candidate_document_references)
    before_registry = repository.registry_bytes
    with tempfile.TemporaryDirectory(prefix="concorde-topology-author-") as directory:
        capsule = Path(directory)
        context_file = capsule / "context.json"
        if host.mode != "describe-policy":
            context_file.write_text(snapshot.serialized + "\n")
        roles = {"spec-context": ("context.json",)}
        policy = compile_policy(
            EffectDeclaration(("spec-context",), (), False, "none"),
            PolicyBinding(MAIN_CAPABILITY, "topology-author", occurrence, role, role),
            roles,
            outer_sandbox_required=configuration["data"]["enforcement"] == "outer",
        )
        integration = configuration["data"]["integration"]
        renderer = render_codex_configuration if integration == "codex" else render_claude_configuration
        native = renderer(policy,
            native_enforcement=configuration["data"]["enforcement"] == "native",
            outer_sandbox=host.outer_sandbox)
        receipt = {"schema_version": 14, "target_id": target["id"], "phase": "topology-author",
            "context_id": snapshot.id, "source_digest": snapshot.id,
            "registry_digest": digest(before_registry), "role_paths": {"spec-context": ["context.json"]}}
        runtime = typed("concorde-topology-author-context", snapshot.value)
        invocation_id = str(uuid.uuid4())
        launch = build_launch_specification(operation=MAIN_CAPABILITY, stage="topology-author",
            occurrence=occurrence, capability=role, integration=integration, agent=role,
            project_root=str(capsule), request=task, prompt=prompt.body, prior_results=(),
            workspace_receipt_json=canonical(receipt), workspace_digest=snapshot.id, policy=policy,
            native_configuration=native, runtime_input_json=canonical(runtime),
            operation_configuration_json=canonical(configuration), invocation_id=invocation_id)
        host.descriptions.append({"operation": MAIN_CAPABILITY, "phase": "topology-author",
            "target_id": target["id"], "context_id": snapshot.id, "project_root": str(capsule),
            "read_paths": list(policy.read_paths), "write_paths": [], "network": False,
            "fresh_session": True, "policy_digest": policy.digest})
        if host.mode == "describe-policy":
            return {"context_id": snapshot.id, "target_id": target["id"], "outcome": "completed",
                    "answer": "", "gaps": [], "documents": []}
        from .agent_executor import AgentProcessExecutor
        executor = host.executor or AgentProcessExecutor()
        result = executor(launch)
        if not isinstance(result, CapabilityExecutionResult):
            raise SpecError("topology author omitted native completion evidence", "invalid_completion")
        evidence = result.receipt
        if (evidence.requested_launch_digest != launch.digest or evidence.policy_digest != policy.digest
                or evidence.status != "success" or result.completion.invocation_id != invocation_id
                or result.completion.workspace_digest != snapshot.id):
            raise SpecError("topology author evidence is not bound to this invocation", "invalid_completion")
        data = validate_typed(result.completion.domain_output, "concorde-topology-author-result")["data"]
        if data["context_id"] != snapshot.id or data["target_id"] != target["id"]:
            raise SpecError("topology author returned a different target/context", "incompatible_handoff")
        if (data["outcome"] == "spec_incomplete") != bool(data["gaps"]):
            raise SpecError("topology author gaps do not match its outcome", "invalid_completion")
        for gap in data["gaps"]:
            if gap.get("target_id", target["id"]) != target["id"]:
                raise SpecError("topology author gap names another target", "incompatible_handoff")
            if gap.get("context_id", snapshot.id) != snapshot.id:
                raise SpecError("topology author gap names another context", "incompatible_handoff")
            gap.update(target_id=target["id"], context_id=snapshot.id)
        paths = [item["path"] for item in data["documents"]]
        if data["outcome"] == "completed":
            if paths != target["documents"]:
                raise SpecError("topology author must return every target document in order",
                                "invalid_completion")
        elif data["documents"]:
            raise SpecError("blocked topology author cannot return document replacements",
                            "invalid_completion")
        if read_file(repository.root, repository.registry_path) != before_registry:
            raise SpecError("registry changed during topology authoring", "stale_context")
        recheck_topology_author_context(repository, snapshot)
        if load_configuration(repository.root) != configuration:
            raise SpecError("configuration changed during topology authoring", "configuration_mismatch")
        if context_file.read_text() != snapshot.serialized + "\n":
            raise SpecError("topology author changed its frozen context", "stale_context")
        host.evidence.append(result)
        return data


def _main_topology_response(action: str, repository: SpecRepository, proposal: dict, *,
                            outcome: str, answer: str, application=None, files=(), gaps=(),
                            completed=()) -> dict:
    data = proposal["data"]
    design = data["design"]["data"]
    return typed("concorde-main-response", {"action": action,
        "entry_target": design["registry"]["entry_target"], "context_id": data["context_id"],
        "outcome": outcome, "answer": answer,
        "discovered_targets": data["discovered_targets"], "routes": [], "worker_results": [],
        "topology_proposal": proposal if action == "accept-topology" else None,
        "application": application, "files": list(files), "gaps": list(gaps),
        "completed_operations": list(completed),
        "workspace": workspace_context(repository.root)})


def _prepare_topology(configuration: dict, proposal: dict, host: CapabilityHost) -> dict:
    if host.mode == "execute":
        progress(host.project_root, phase="topology_authoring", status="active", invalidate=True)
    repository, proposal = _validate_topology_proposal(host, proposal)
    design, candidate, candidate_bytes, current_targets, candidate_targets, tasks = (
        _inspect_topology_design(
            repository,
            proposal["data"]["design"],
            tuple(proposal["data"]["discovered_targets"]),
        )
    )
    proposals: dict[str, list[tuple[str, str]]] = {}
    completed = ["concorde-coordinator-topology-design"]
    candidate_references: dict[str, list[str]] = {}
    for candidate_target in candidate["targets"]:
        for path in candidate_target["documents"]:
            candidate_references.setdefault(path, []).append(candidate_target["id"])
    for occurrence, (target_id, task) in enumerate(tasks.items()):
        target = candidate_targets[target_id]
        references = tuple({"path": path, "targets": candidate_references[path]}
                           for path in target["documents"])
        result = _topology_author(repository, configuration, host, target, task, occurrence,
                                  references)
        if result["outcome"] != "completed":
            return _main_topology_response("accept-topology", repository, proposal,
                outcome=result["outcome"], answer=result["answer"], gaps=result["gaps"],
                completed=completed)
        for item in result["documents"]:
            path = item["path"]
            if path not in repository.document_targets and checked_path(repository.root, path).exists():
                raise SpecError("topology author cannot replace an unregistered existing file",
                                "permission_denied", path)
            proposals.setdefault(path, []).append((target_id, item["content"]))
        completed.append("concorde-spec-author")
    if host.mode == "describe-policy":
        return _main_topology_response("accept-topology", repository, proposal,
            outcome="described", answer="Topology author policies described.",
            completed=completed)
    authored: dict[str, str] = {}
    for path, items in proposals.items():
        contents = {content for _, content in items}
        if len(contents) != 1:
            return _main_topology_response("accept-topology", repository, proposal,
                outcome="conflicting",
                answer=f"Referencing target authors returned conflicting shared truth: {path}",
                completed=completed)
        content = next(iter(contents))
        references = set(candidate_references[path])
        current = read_file(repository.root, path).decode() if path in repository.document_targets else None
        if len(references) > 1 and content != current:
            represented = {target_id for target_id, _ in items}
            if represented != references:
                return _main_topology_response("accept-topology", repository, proposal,
                    outcome="conflicting",
                    answer=f"Changing shared truth requires every referencing target author: {path}",
                    completed=completed)
        authored[path] = content
    overrides = {path: content.encode() for path, content in authored.items()}
    report = validate_repository(repository.root, package_root=host.package_root,
        registry_bytes=candidate_bytes, document_overrides=overrides)
    if report.status != "success":
        raise SpecError("topology candidate validation failed: " + "; ".join(
            finding.message for finding in report.findings), "invalid_proposal")
    changes = [file_change(repository.root, repository.registry_path, candidate_bytes.decode())]
    changes.extend(file_change(repository.root, path, content) for path, content in authored.items())
    application_payload = {"topology_proposal": proposal,
        "base_registry_digest": digest(repository.registry_bytes),
        "protocol_binding": repository.config["protocol"], "files": changes}
    application = typed("concorde-topology-application", {
        "application_id": digest(application_payload), **application_payload})
    relative = ".concorde/topology-proposals/" + application["data"]["application_id"][7:] + ".json"
    stored = file_change(repository.root, relative, canonical(application) + "\n")
    apply_files(repository.root, [stored], {relative})
    application_ref = artifact(repository.root, application["data"]["application_id"], relative)
    completed.append("concorde-main-prepare-topology")
    return _main_topology_response("accept-topology", repository, proposal,
        outcome="topology_prepared", answer="Exact topology application prepared for maintainer review.",
        application=application_ref, completed=completed)


def _apply_topology(application_ref: dict, host: CapabilityHost) -> dict:
    if host.mode == "execute":
        progress(host.project_root, phase="topology_apply", status="active", invalidate=True)
    repository = SpecRepository(host.project_root, host.package_root)
    verify_artifacts(repository.root, application_ref)
    raw = read_file(repository.root, application_ref["path"])
    application = validate_typed(decode(raw.decode()), "concorde-topology-application")
    data = application["data"]
    identity = {key: item for key, item in data.items() if key != "application_id"}
    if digest(identity) != data["application_id"] or application_ref["id"] != data["application_id"]:
        raise SpecError("topology application identity is invalid", "invalid_proposal")
    expected_path = ".concorde/topology-proposals/" + data["application_id"][7:] + ".json"
    if application_ref["path"] != expected_path:
        raise SpecError("topology application is outside the host proposal area", "invalid_proposal")
    _, proposal = _validate_topology_proposal(host, data["topology_proposal"])
    if data["base_registry_digest"] != digest(repository.registry_bytes):
        raise SpecError("topology application registry base changed", "stale_proposal")
    if data["protocol_binding"] != repository.config["protocol"]:
        raise SpecError("topology application Protocol binding changed", "stale_proposal")
    design, _, candidate_bytes, _, _, _ = _inspect_topology_design(
        repository,
        proposal["data"]["design"],
        tuple(proposal["data"]["discovered_targets"]),
    )
    files = data["files"]
    registry_files = [item for item in files if item["path"] == repository.registry_path]
    if len(registry_files) != 1 or registry_files[0]["content"].encode() != candidate_bytes:
        raise SpecError("topology application does not contain the exact candidate registry",
                        "invalid_proposal")
    task_ids = {item["target_id"] for item in design["spec_tasks"]}
    targets = {item["id"]: item for item in design["registry"]["targets"]}
    expected_documents = {path for target_id in task_ids for path in targets[target_id]["documents"]}
    actual_documents = {item["path"] for item in files if item["path"] != repository.registry_path}
    if actual_documents != expected_documents or len({item["path"] for item in files}) != len(files):
        raise SpecError("topology application document set differs from accepted design",
                        "invalid_proposal")
    candidate_references: dict[str, set[str]] = {}
    for target in design["registry"]["targets"]:
        for path in target["documents"]:
            candidate_references.setdefault(path, set()).add(target["id"])
    for item in files:
        if item["path"] == repository.registry_path:
            continue
        current = (read_file(repository.root, item["path"]).decode()
                   if item["path"] in repository.document_targets else None)
        references = candidate_references[item["path"]]
        if len(references) > 1 and item["content"] != current and not references.issubset(task_ids):
            raise SpecError("shared truth application omitted a referencing target task",
                            "invalid_proposal", item["path"])
    if host.mode == "describe-policy":
        return _main_topology_response("apply-topology", repository, proposal,
            outcome="described", answer="Topology application is deterministic and launches no agent.")
    overrides = {item["path"]: item["content"].encode() for item in files
                 if item["path"] != repository.registry_path}
    report = validate_repository(repository.root, package_root=host.package_root,
        registry_bytes=candidate_bytes, document_overrides=overrides)
    if report.status != "success":
        raise SpecError("topology application validation failed: " + "; ".join(
            finding.message for finding in report.findings), "invalid_proposal")
    allowed = {item["path"] for item in files}
    def verify():
        current = validate_repository(repository.root, package_root=host.package_root)
        if current.status != "success":
            raise SpecError("applied topology failed validation: " + "; ".join(
                finding.message for finding in current.findings), "invalid_proposal")
    change = read_change(repository.root)
    transaction = list(files)
    if change is not None:
        owner = design["registry"]["entry_target"]
        if change["target_id"] is not None and (change["target_id"] != owner
                or change["task"] != proposal["data"]["task"]
                or change["constraints"] != proposal["data"]["constraints"]):
            raise SpecError("topology application differs from this worktree's owning task", "incompatible_handoff")
        change.update(target_id=owner, focus_id=None, task=proposal["data"]["task"],
                      constraints=proposal["data"]["constraints"], phase="specified", status="active",
                      outcome="topology_applied", gaps=[])
        transaction.append(file_change(repository.root, STATE_PATH, canonical(change) + "\n"))
        allowed.add(STATE_PATH)
    changed = [path for path in apply_files(repository.root, transaction, allowed, verify=verify)
               if path != STATE_PATH]
    if change is not None:
        refresh_registry(repository.root)
    try:
        checked_path(repository.root, application_ref["path"]).unlink()
        proposal_dir = checked_path(repository.root, ".concorde/topology-proposals")
        if proposal_dir.is_dir() and not any(proposal_dir.iterdir()):
            proposal_dir.rmdir()
    except OSError:
        # The application is already committed; stale host artifacts remain ignored and digest-bound.
        pass
    return _main_topology_response("apply-topology",
        SpecRepository(repository.root, host.package_root), proposal,
        outcome="topology_applied", answer="Accepted topology application applied atomically.",
        files=changed, completed=("concorde-main-apply-topology",))


class Invocation:
    def __init__(self, capability: str, configuration: dict, task: dict, host: CapabilityHost):
        self.capability, self.configuration, self.task, self.host = capability, configuration, task, host
        self.repository = SpecRepository(host.project_root, host.package_root)
        self.target = self.repository.select(task["target_id"], task.get("focus_id"))
        change = read_change(host.project_root)
        if task.get("change_id") is not None and (change is None or task["change_id"] != change["change_id"]):
            raise SpecError("change identity does not belong to the current worktree", "incompatible_handoff")
        self.change_id = task.get("change_id") or (change["change_id"] if change else None)
        self.work_directory = f"{WORK_PATH}/{self.target.id}" if change else None
        self.last_context = None
        self.completed: list[str] = []

    def response(self, outcome="completed", answer="", *, gaps=(), checks=(), artifacts=(), reviews=()) -> dict:
        data = {
            "target_id": self.target.id, "focus_id": self.task.get("focus_id"), "change_id": self.change_id,
            "context_id": self.last_context, "outcome": outcome, "answer": answer,
            "gaps": list(gaps), "checks": list(checks), "artifacts": list(artifacts),
            "completed_operations": list(self.completed)}
        if self.capability == "concorde-review":
            data["reviews"] = list(reviews)
        return typed(CAPABILITY_CONTRACTS[self.capability][1], data)

    def record_gaps(self, phase, gaps):
        if self.host.mode != "execute":
            return
        change = read_change(self.repository.root)
        required_review = bool(phase in {"spec-review", "code-review"} and change
            and change.get("review_requirements", {}).get(self.target.id, {}).get(phase.split("-")[0])
            and change.get("review_intents", {}).get(self.target.id) == {"task": self.task["task"],
                "focus_id": self.task.get("focus_id"), "constraints": self.task.get("constraints", [])})
        if self.host.track_gaps or required_review or self.capability not in {
                "concorde-main", "concorde-context-solve", "concorde-review"}:
            from .change_worktree import record_task_gaps
            record_task_gaps(self.repository.root, self.target.id, self.task["task"], phase, gaps,
                             _target_revision(self.repository, self.target))

    def pending_gaps(self, phase, snapshot=None, *, include_prerequisites=True):
        from .change_worktree import unchanged_task_gaps
        if phase == "specify" or self.host.mode != "execute":
            return []
        gaps = unchanged_task_gaps(self.repository.root, self.target.id, self.task["task"], phase,
                                  _target_revision(self.repository, self.target))
        if include_prerequisites:
            order = ("specify", "spec-review", "context-solve", "plan", "tasks", "implementation", "code-review")
            prerequisites = set(order[:order.index(phase)]) if phase in order else set()
            change = read_change(self.repository.root)
            gaps.extend(dict(item["gap"]) for item in (change or {}).get("gap_history", [])
                if item["status"] == "open" and item["target_id"] == self.target.id
                and item["task"] == self.task["task"] and item["phase"] in prerequisites)
        # No reviewer ran again. Retain the actual observation's provenance.
        return gaps

    def stage(self, capability: str, *, inputs: tuple[dict, ...] = (), readonly=False,
              defer_gap_resolution=False) -> dict:
        phase, role = {**STAGE_ROLES, **TARGET_AGENT_STAGES}[capability]
        prompt = load_role_prompt(self.host.package_root, role)
        snapshot = resolve_context(self.repository, self.target.id, phase=phase, task=self.task["task"],
            focus_id=self.task.get("focus_id"), constraints=tuple(self.task.get("constraints", [])),
            instructions=prompt.body, stage_inputs=inputs)
        self.last_context = snapshot.id
        if self.capability not in {"concorde-main", "concorde-context-solve"}:
            pending = self.pending_gaps(phase, snapshot, include_prerequisites=not readonly)
            if pending:
                return {"context_id": snapshot.id, "outcome": "spec_incomplete",
                    "answer": "Repair the recorded necessary contracts before resuming this step.",
                    "gaps": pending, "documents": [], "plan": "", "tasks": []}
        implementation = phase == "implementation"
        if implementation and not self.target.implementation:
            raise SpecError("implementation requires an explicitly owned Service/Module code scope", "unsupported_target")
        if (self.host.mode != "describe-policy" and phase == "context-solve"
                and self.target.kind == "domain"):
            participant_findings = domain_participant_findings(self.repository, self.target.id)
            if participant_findings:
                self.completed.append(capability)
                conflicts = [finding for finding in participant_findings
                             if finding.rule_id != "CONCORDE-PARTICIPANT-004"]
                if conflicts:
                    return {"context_id": snapshot.id, "outcome": "conflicting",
                            "answer": "Domain participant routing conflicts with its registered topology: "
                                + "; ".join(finding.message for finding in conflicts),
                            "gaps": [], "documents": [], "plan": "", "tasks": []}
                gaps = [{
                    "question": "How should the Domain participant routing be completed? " + finding.message,
                    "blocked_step": "Assess context sufficiency before Domain planning",
                    "needed_contract": f"{finding.rule_id}: {finding.remediation}",
                    "target_id": self.target.id,
                    "context_id": snapshot.id,
                } for finding in participant_findings]
                self.record_gaps(phase, gaps)
                return {"context_id": snapshot.id, "outcome": "spec_incomplete",
                        "answer": "Domain participant routing is incomplete or inconsistent.",
                        "gaps": gaps, "documents": [], "plan": "", "tasks": []}
        before_registry = self.repository.registry_bytes
        with tempfile.TemporaryDirectory(prefix="concorde-context-") as directory:
            capsule = Path(directory)
            # Spec-only tasks see a private capsule, not a repository or inherited conversation.
            project = self.host.project_root if implementation else capsule
            if implementation:
                relative = f".concorde/runs/{self.host.invocation_id}/{uuid.uuid4()}/context.json"
                context_file = checked_path(project, relative)
            else:
                relative, context_file = "context.json", capsule / "context.json"
            if self.host.mode != "describe-policy":
                context_file.parent.mkdir(parents=True, exist_ok=True)
                context_file.write_text(snapshot.serialized + "\n")
            roles = {"spec-context": (relative,), "implementation": self.target.implementation if implementation else ()}
            read_roles = ("spec-context", "implementation") if implementation else ("spec-context",)
            write_roles = ("implementation",) if implementation and not readonly else ()
            policy = compile_policy(EffectDeclaration(read_roles, write_roles, False, "none"),
                PolicyBinding(capability, phase, 0, role, role), roles,
                outer_sandbox_required=self.configuration["data"]["enforcement"] == "outer")
            integration = self.configuration["data"]["integration"]
            renderer = render_codex_configuration if integration == "codex" else render_claude_configuration
            native = renderer(policy, native_enforcement=self.configuration["data"]["enforcement"] == "native",
                              outer_sandbox=self.host.outer_sandbox)
            receipt = {"schema_version": 14, "target_id": self.target.id, "phase": phase,
                "context_id": snapshot.id, "source_digest": snapshot.id,
                "registry_digest": digest(before_registry), "role_paths": {k: list(v) for k, v in roles.items()}}
            value = typed("concorde-agent-stage-context", {"snapshot": typed("concorde-context-snapshot", snapshot.value),
                "change_id": self.change_id, "expected_artifacts": []})
            invocation_id = str(uuid.uuid4())
            launch = build_launch_specification(operation=capability, stage=phase, occurrence=0, capability=role,
                integration=integration, agent=role, project_root=str(project), request=self.task["task"],
                prompt=prompt.body, prior_results=(), workspace_receipt_json=canonical(receipt),
                workspace_digest=snapshot.id, policy=policy, native_configuration=native,
                runtime_input_json=canonical(value), operation_configuration_json=canonical(self.configuration),
                invocation_id=invocation_id)
            self.host.descriptions.append({"operation": capability, "phase": phase, "context_id": snapshot.id,
                "project_root": str(project), "read_paths": list(policy.read_paths),
                "write_paths": list(policy.write_paths), "network": False, "fresh_session": True,
                "policy_digest": policy.digest})
            if self.host.mode == "describe-policy":
                return {"context_id": snapshot.id, "outcome": "completed", "answer": "", "gaps": [],
                        "documents": [], "plan": "", "tasks": []}
            from .agent_executor import AgentProcessExecutor
            executor = self.host.executor or AgentProcessExecutor()
            result = executor(launch)
            if not isinstance(result, CapabilityExecutionResult):
                raise SpecError("executor omitted native completion evidence", "invalid_completion")
            evidence = result.receipt
            if (evidence.requested_launch_digest != launch.digest or evidence.policy_digest != policy.digest
                    or evidence.status != "success" or result.completion.invocation_id != invocation_id
                    or result.completion.workspace_digest != snapshot.id):
                raise SpecError("completion evidence is not bound to this invocation", "invalid_completion")
            data = validate_typed(result.completion.domain_output, "concorde-agent-stage-result")["data"]
            if data["context_id"] != snapshot.id:
                raise SpecError("agent returned a different context identity", "incompatible_handoff")
            if (data["outcome"] == "spec_incomplete") != bool(data["gaps"]):
                raise SpecError("Spec incomplete requires concrete gaps; other outcomes cannot carry gaps", "invalid_completion")
            for gap in data["gaps"]:
                if any(not gap[key].strip() for key in ("question", "blocked_step", "needed_contract")):
                    raise SpecError("task gaps require a concrete question, step and contract", "invalid_completion")
                if gap.get("target_id",self.target.id)!=self.target.id or gap.get("context_id",snapshot.id)!=snapshot.id:
                    raise SpecError("gap provenance differs from the admitted context", "incompatible_handoff")
                gap.update(target_id=self.target.id,context_id=snapshot.id)
            if read_file(self.repository.root, self.repository.registry_path) != before_registry:
                raise SpecError("registry changed during agent execution", "stale_context")
            recheck_context(self.repository, snapshot, check_implementation=not implementation or readonly)
            if load_configuration(self.repository.root) != self.configuration:
                raise SpecError("configuration changed during agent execution", "configuration_mismatch")
            if context_file.read_text() != snapshot.serialized + "\n":
                raise SpecError("frozen context capsule changed", "stale_context")
            if phase != "specify" and data["documents"]:
                raise SpecError("this phase cannot author Spec documents", "permission_denied")
            self.host.evidence.append(result)
            self.completed.append(capability)
            if (data["outcome"] == "spec_incomplete" or not defer_gap_resolution
                    and data["outcome"] in {"completed", "sufficient"}):
                self.record_gaps(phase, data["gaps"])
            return data

    def author(self, capability: str) -> dict:
        if not self.host.coordinated:
            progress(self.repository.root, phase="specify", status="active", invalidate=True)
        result = self.stage(capability, defer_gap_resolution=True)
        if result["outcome"] not in {"completed", "sufficient"}:
            return self.response(result["outcome"], result["answer"], gaps=result["gaps"])
        if self.host.mode == "describe-policy":
            return self.response("described")
        if result["documents"]:
            changes = []
            for item in result["documents"]:
                if item["path"] not in self.target.documents:
                    raise SpecError("Spec author returned a document outside its target", "permission_denied")
                before = read_file(self.repository.root, item["path"]).decode()
                if (len(self.repository.document_targets[item["path"]]) > 1
                        and item["content"] != before):
                    raise SpecError(
                        "shared Spec truth requires a topology change with every referencing target",
                        "permission_denied",
                        item["path"],
                    )
                if item["content"] != before:
                    candidate_repository = SpecRepository(
                        self.repository.root,
                        self.host.package_root,
                        document_overrides={item["path"]: item["content"].encode()},
                    )
                    current_document = self.repository.document(item["path"])
                    candidate_document = candidate_repository.document(item["path"])
                    current_declaration = (current_document.document_id, current_document.targets,
                                           current_document.main_visible)
                    candidate_declaration = (candidate_document.document_id, candidate_document.targets,
                                             candidate_document.main_visible)
                    if candidate_declaration != current_declaration:
                        raise SpecError(
                            "document identity, references, and main visibility require a topology change",
                            "permission_denied",
                            item["path"],
                        )
                    changes.append(file_change(self.repository.root, item["path"], item["content"]))
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
                participant_findings = domain_participant_findings(current, self.target.id)
                if participant_findings:
                    raise SpecError(
                        "authored Domain participant routing is invalid: "
                        + "; ".join(finding.message for finding in participant_findings),
                        "invalid_spec",
                    )
            if changes:
                apply_files(self.repository.root, changes, set(self.target.documents), verify=verify)
                self.repository = SpecRepository(self.host.project_root, self.host.package_root)
        self.record_gaps("specify", [])
        change = read_change(self.repository.root)
        if change is not None:
            change.setdefault("authored_specs", {})[self.target.id] = {
                "task": self.task["task"], "focus_id": self.task.get("focus_id"),
                "constraints": self.task.get("constraints", []), "context_id": self.last_context,
                "spec_digest": _target_revision(self.repository, self.target)}
            save_change(self.repository.root, change)
        return self.response(answer=result["answer"])

    def require_spec_review(self) -> None:
        if self.host.mode != "execute":
            return
        from .review import current
        change = read_change(self.repository.root)
        if change and change.get("review_requirements", {}).get(self.target.id, {}).get("spec"):
            current(self, "spec", required=True)

    def plan(self) -> dict:
        self.require_spec_review()
        if not self.host.coordinated:
            progress(self.repository.root, phase="plan", status="active", invalidate=True)
        assessment = self.stage("concorde-context-solve")
        if assessment["outcome"] not in {"completed", "sufficient"}:
            return self.response(assessment["outcome"], assessment["answer"], gaps=assessment["gaps"])
        result = self.stage("concorde-plan", defer_gap_resolution=True)
        if result["outcome"] not in {"completed", "sufficient"}:
            return self.response(result["outcome"], result["answer"], gaps=result["gaps"])
        if self.host.mode == "describe-policy":
            return self.response("described")
        if not result["plan"].strip():
            raise SpecError("planning produced no usable plan", "invalid_completion")
        change = read_change(self.repository.root, required=True)
        self.change_id = change["change_id"]
        self.work_directory = f"{WORK_PATH}/{self.target.id}"
        state = target_state(self.repository.root, self.target.id, self.task.get("focus_id"), create=True)
        state.pop("coordination", None)
        state.pop("component_revisions", None)
        state.update(plan=result["plan"], tasks=[], checks=[], spec_digest=_target_revision(self.repository, self.target),
                     task=self.task["task"], constraints=self.task.get("constraints", []),
                     implementation_digest=None, completed_operations=list(self.completed),
                     phase="plan", status="active")
        path = work_path(self.target.id, "plan.md")
        apply_files(self.repository.root, [file_change(self.repository.root, path, result["plan"])], {path})
        save_target_state(self.repository.root, state)
        self.record_gaps("plan", [])
        return self.response(answer=result["answer"], artifacts=[artifact(self.repository.root, "plan", path)])

    def tasks(self) -> dict:
        self.require_spec_review()
        if not self.work_directory:
            raise SpecError("task authoring requires a managed change", "missing_change")
        if not self.host.coordinated:
            progress(self.repository.root, phase="tasks", status="active", invalidate=True)
        state = target_state(self.repository.root, self.target.id, self.task.get("focus_id"))
        self.check_state(state)
        if not state["plan"]:
            raise SpecError("tasks require an authored plan", "missing_plan")
        inputs = (typed("concorde-plan-artifact", {"plan":state["plan"]}),)
        result = self.stage("concorde-tasks", inputs=inputs, defer_gap_resolution=True)
        if result["outcome"] not in {"completed", "sufficient"}:
            return self.response(result["outcome"], result["answer"], gaps=result["gaps"])
        if self.host.mode == "describe-policy":
            return self.response("described")
        tasks = result["tasks"]
        if not tasks or len({t["id"] for t in tasks}) != len(tasks) or any(t["complete"] for t in tasks):
            raise SpecError("tasks must be nonempty, uniquely identified and initially incomplete", "invalid_completion")
        for task in tasks:
            self.repository.select(task["target_id"])
            if self.target.kind != "domain" and task["target_id"] != self.target.id:
                raise SpecError("component tasks must remain in their owning context", "permission_denied")
        state.update(tasks=tasks, checks=[], implementation_digest=None, phase="tasks", status="active")
        save_target_state(self.repository.root, state)
        self.record_gaps("tasks", [])
        return self.response(answer=result["answer"], artifacts=[artifact(self.repository.root, "change", STATE_PATH)])

    def implement(self) -> dict:
        self.require_spec_review()
        pending = self.pending_gaps("implementation")
        if pending:
            return self.response("spec_incomplete", "Resolve the prerequisite task gaps before implementation.", gaps=pending)
        if not self.work_directory:
            raise SpecError("implementation requires a managed change and authored tasks", "missing_change")
        state = target_state(self.repository.root, self.target.id, self.task.get("focus_id"))
        self.check_state(state)
        if not state["tasks"]:
            raise SpecError("implementation requires tasks", "missing_tasks")
        if self.target.kind == "domain":
            return self.implement_scope(state)
        if validate_repository(self.repository.root, package_root=self.host.package_root).status != "success":
            raise SpecError("reconcile all shared contracts before implementation", "incompatible_contracts")
        if not self.host.coordinated:
            progress(self.repository.root, phase="implementation", status="active", invalidate=True)
        inputs = (typed("concorde-implementation-task", {"plan":state["plan"],"tasks":state["tasks"]}),)
        result = self.stage("concorde-implement", inputs=inputs, defer_gap_resolution=True)
        if result["outcome"] not in {"completed", "sufficient"}:
            return self.response(result["outcome"], result["answer"], gaps=result["gaps"])
        if self.host.mode == "describe-policy":
            return self.response("described")
        returned = result["tasks"]
        expected = [{**task, "complete": True} for task in state["tasks"]]
        if returned != expected:
            raise SpecError("implementation must report every exact task complete", "incomplete_tasks")
        state["tasks"] = returned
        state["implementation_digest"] = _implementation_digest(self.repository, self.target)
        state["checks"] = []
        state.update(phase="implementation", status="completed")
        save_target_state(self.repository.root, state)
        self.record_gaps("implementation", [])
        return self.response(answer=result["answer"])

    def check_state(self, state: dict) -> None:
        if state.get("spec_digest") != _target_revision(self.repository, self.target):
            raise SpecError("selected Spec or its registered authority changed; replan this change", "stale_context")
        if state.get("task") != self.task["task"] or state.get("constraints") != self.task.get("constraints", []):
            raise SpecError("change intent differs from the authored plan; replan explicitly", "incompatible_handoff")

    def implement_scope(self, state: dict) -> dict:
        """Retain resumable component drafts inside this one candidate worktree."""
        grouped = {}
        review_artifacts = []
        for task in state["tasks"]:
            component = self.repository.select(task["target_id"])
            scopes = set(component.participates_in)
            for scope in tuple(scopes):
                parent = self.repository.targets[scope].scope_parent
                while parent:
                    scopes.add(parent)
                    parent = self.repository.targets[parent].scope_parent
            if component.kind == "domain" or self.target.id not in scopes:
                raise SpecError("Domain task must target an explicitly participating component", "permission_denied")
            grouped.setdefault(component.id, []).append(task)
        component_tasks = {target_id: "\n\n".join(
            task["description"] + "\nAcceptance: " + task["acceptance"] for task in tasks)
            for target_id, tasks in grouped.items()}
        coordination = state.setdefault("coordination", {})
        if coordination and set(coordination) != set(component_tasks):
            raise SpecError("participating tasks changed; replan this worktree change", "stale_context")
        for target_id, task_text in component_tasks.items():
            record = coordination.setdefault(target_id, {
                "task": task_text, "spec_status": "pending", "implementation_status": "pending",
                "spec_digest": None, "implementation_digest": None, "gaps": [], "outcome": None})
            if record["task"] != task_text:
                raise SpecError("component intent changed; replan this worktree change", "stale_context")
        progress(self.repository.root, phase="spec_reconciliation", status="active", invalidate=True)
        state.update(phase="spec_reconciliation", status="active")
        save_target_state(self.repository.root, state)

        def blocked(result, target_id, phase):
            record = coordination[target_id]
            record[phase + "_status"] = "blocked"
            child = result["output"]["data"] if result["output"] else None
            record["outcome"] = child["outcome"] if child else "failed"
            record["gaps"] = child["gaps"] if child else []
            state["status"] = "blocked"
            save_target_state(self.repository.root, state)
            progress(self.repository.root, status="blocked", outcome=record["outcome"],
                     gaps=record["gaps"])
            if child:
                return self.response(child["outcome"], "Component " + target_id + ": " + child["answer"],
                                     gaps=child["gaps"], artifacts=child["artifacts"])
            raise SpecError("component " + phase + " blocked: " + target_id, "child_blocked")

        for target_id, task_text in component_tasks.items():
            component = self.repository.select(target_id)
            record = coordination[target_id]
            revision = _target_revision(self.repository, component)
            if record["spec_status"] == "completed" and record["spec_digest"] == revision:
                continue
            record.update(spec_status="running", implementation_status="pending", gaps=[], outcome=None)
            save_target_state(self.repository.root, state)
            payload = {"target_id": target_id, "task": task_text, "change_id": self.change_id,
                       "constraints": self.task.get("constraints", [])}
            child_host = replace(self.host, routed_target=target_id, coordinated=True)
            result = run_capability("concorde-specify", self.configuration,
                typed("concorde-specify-request", payload), host_context=child_host)
            if result["status"] != "succeeded":
                return blocked(result, target_id, "spec")
            self.repository = SpecRepository(self.host.project_root, self.host.package_root)
            record.update(spec_status="completed", outcome="completed",
                          spec_digest=_target_revision(self.repository, self.repository.select(target_id)))
            save_target_state(self.repository.root, state)

        # Transitional consumer/provider disagreement is allowed until every
        # participating author has completed. It must not prevent resuming a draft.
        progress(self.repository.root, phase="spec_validation", status="active")
        if validate_repository(self.repository.root, package_root=self.host.package_root).status != "success":
            state.update(phase="spec_validation", status="blocked")
            save_target_state(self.repository.root, state)
            progress(self.repository.root, status="blocked", outcome="incompatible_contracts")
            raise SpecError("reconcile all consumer/provider contracts before implementation", "incompatible_contracts")
        progress(self.repository.root, phase="implementation", status="active")
        state.update(phase="implementation", status="active")
        for target_id, task_text in component_tasks.items():
            component = self.repository.select(target_id)
            record = coordination[target_id]
            payload = {"target_id": target_id, "task": task_text, "change_id": self.change_id,
                       "constraints": self.task.get("constraints", [])}
            child_host = replace(self.host, routed_target=target_id, coordinated=True)
            from .review import require_reviews
            require_reviews(Invocation("concorde-review", self.configuration, payload, child_host), bool(
                read_change(self.repository.root, required=True).get("review_requirements", {})
                .get(self.target.id, {}).get("spec")))
            if (record["implementation_status"] == "completed"
                    and record["implementation_digest"] == _implementation_digest(self.repository, component)):
                try:
                    Invocation("concorde-validate", self.configuration, payload, child_host).verify_completion()
                    review_artifacts.extend(item["artifact"] for item in
                        read_change(self.repository.root, required=True).get("reviews", {}).get(target_id, {}).values())
                    continue
                except SpecError:
                    pass
            record.update(implementation_status="running", gaps=[], outcome=None)
            save_target_state(self.repository.root, state)
            result = run_capability("concorde-dev-loop", self.configuration,
                typed("concorde-dev-loop-request", {**payload, "specify": False, "run_reviews": bool(
                    read_change(self.repository.root, required=True).get("review_requirements", {})
                    .get(self.target.id, {}).get("spec"))}), host_context=child_host)
            if result["status"] != "succeeded":
                return blocked(result, target_id, "implementation")
            review_artifacts.extend(item for item in result["output"]["data"]["artifacts"]
                                    if item["id"].startswith("review."))
            self.repository = SpecRepository(self.host.project_root, self.host.package_root)
            record.update(implementation_status="completed", outcome="completed",
                          implementation_digest=_implementation_digest(self.repository, self.repository.select(target_id)))
            save_target_state(self.repository.root, state)
        state["component_revisions"] = {target_id: {
            "spec": _target_revision(self.repository, self.repository.select(target_id)),
            "implementation": _implementation_digest(self.repository, self.repository.select(target_id))}
            for target_id in component_tasks}
        state["tasks"] = [{**task, "complete": True} for task in state["tasks"]]
        state["implementation_digest"] = _implementation_digest(self.repository, self.target)
        state.update(phase="implementation", status="completed")
        save_target_state(self.repository.root, state)
        return self.response(answer="Participating components completed in the candidate worktree.", artifacts=review_artifacts)

    def validate(self, run_checks: bool = True) -> dict:
        if not self.host.coordinated:
            progress(self.repository.root, phase="validate", status="active", invalidate=True)
        before_tree = snapshot_tree(self.repository.root) if self.work_directory else None
        change = read_change(self.repository.root)
        direct_candidate = bool(change is not None and not change["targets"] and not self.host.coordinated)
        report = validate_repository(self.repository.root, self.target.id, self.host.package_root)
        if report.status != "success":
            progress(self.repository.root, status="blocked", outcome="invalid_spec")
            return self.response("failed", "Spec structure or shared contracts failed deterministic validation.")
        checked_targets = tuple(self.repository.targets.values()) if direct_candidate else (self.target,)
        results = [result for target in checked_targets
                   for result in _check(self.repository, target, self.host.invocation_id)] if run_checks else []
        state = None
        if change and self.target.id in change["targets"]:
            state = target_state(self.repository.root, self.target.id, self.task.get("focus_id"))
            state.update(checks=results, validation_spec_digest=report.result["source_digest"],
                         phase="validate", status="active")
            save_target_state(self.repository.root, state)
        self.completed.append("concorde-validate")
        failed = any(item["status"] != "passed" for item in results)
        if failed:
            if state is not None:
                state["status"] = "blocked"
                save_target_state(self.repository.root, state)
            return self.response("failed", "Deterministic validation failed.", checks=results)
        if self.work_directory and snapshot_tree(self.repository.root) != before_tree:
            raise SpecError("candidate files changed while checks were running", "stale_evidence")
        if direct_candidate:
            change = read_change(self.repository.root, required=True)
            change["validation"] = {"target_id": self.target.id, "focus_id": self.task.get("focus_id"),
                "task": self.task["task"], "constraints": self.task.get("constraints", []),
                "spec_digest": _target_revision(self.repository, self.target),
                "source_digest": report.result["source_digest"], "checks": results}
            save_change(self.repository.root, change)
            if self.host.defer_ready:
                return self.response(answer="Deterministic checks completed; required review precedes readiness.", checks=results)
            return self.mark_ready()
        if state and state["tasks"] and all(task["complete"] for task in state["tasks"]):
            if self.host.defer_ready:
                return self.response(answer="Deterministic checks completed; required review precedes readiness.", checks=results)
            return self.mark_ready()
        return self.response(answer="Deterministic validation passed; semantic completeness is not proven.", checks=results)

    def mark_ready(self) -> dict:
        before_tree = snapshot_tree(self.repository.root)
        evidence = self.verify_completion()
        if snapshot_tree(self.repository.root) != before_tree:
            raise SpecError("candidate changed during completion verification", "stale_evidence")
        change = read_change(self.repository.root, required=True)
        if self.target.id in change["targets"]:
            change["targets"][self.target.id].update(phase="ready", status="ready")
        if not self.host.coordinated:
            change.update(phase="ready", status="ready", outcome="ready", validated_tree=before_tree)
        save_change(self.repository.root, change)
        return self.response("ready", "Candidate verified. Request delivery from this source or the destination worktree.",
                             checks=evidence.get("checks", []))

    def verify_completion(self) -> dict:
        """Read current target evidence; delivery remains a separate top-level action."""
        from .review import verify_required
        verify_required(self)
        change = read_change(self.repository.root, required=True)
        if any(item["status"] == "open" and item["target_id"] == self.target.id
                and item["task"] == self.task["task"] for item in change.get("gap_history", [])):
            raise SpecError("current task still has unresolved contract gaps", "spec_incomplete")
        if not change["targets"]:
            validation = change.get("validation")
            if (not validation or validation["target_id"] != self.target.id
                    or validation["focus_id"] != self.task.get("focus_id")
                    or validation["task"] != self.task["task"]
                    or validation["constraints"] != self.task.get("constraints", [])):
                raise SpecError("direct candidate has no bound validation evidence", "stale_evidence")
            report = validate_repository(self.repository.root, package_root=self.host.package_root)
            if (report.status != "success" or validation["source_digest"] != report.result["source_digest"]
                    or validation["spec_digest"] != _target_revision(self.repository, self.target)):
                raise SpecError("direct candidate Spec validation is stale", "stale_evidence")
            required = {check_id for target in self.repository.targets.values() for check_id in target.checks}
            if {item["check_id"] for item in validation["checks"]} != required or any(
                    item["status"] != "passed" or item["source_digest"] != _check_revision(
                        self.repository, self.repository.select(item["target_id"]))
                    for item in validation["checks"]):
                raise SpecError("direct candidate checks are missing, failed, or stale", "stale_evidence")
            return validation
        state = target_state(self.repository.root, self.target.id, self.task.get("focus_id"))
        self.check_state(state)
        for target_id, revision in state.get("component_revisions", {}).items():
            component = self.repository.select(target_id)
            if revision != {"spec": _target_revision(self.repository, component),
                            "implementation": _implementation_digest(self.repository, component)}:
                raise SpecError("a completed component changed before Domain delivery", "stale_evidence")
            component_state = target_state(self.repository.root, target_id, None)
            payload = {"target_id": target_id, "task": component_state["task"],
                       "constraints": component_state.get("constraints", []), "change_id": self.change_id}
            Invocation("concorde-validate", self.configuration, payload,
                       replace(self.host, coordinated=True)).verify_completion()
        if not state["tasks"] or any(not task["complete"] for task in state["tasks"]):
            raise SpecError("delivery requires completed tasks", "incomplete_change")
        if state["implementation_digest"] != _implementation_digest(self.repository, self.target):
            raise SpecError("implementation changed since completion", "stale_evidence")
        report = validate_repository(self.repository.root, self.target.id, self.host.package_root)
        if report.status != "success" or state.get("validation_spec_digest") != report.result["source_digest"]:
            raise SpecError("Spec validation is missing or stale", "stale_evidence")
        if {item["check_id"] for item in state["checks"]} != set(self.target.checks) or any(
                item["status"] != "passed" or item["source_digest"] != _check_revision(self.repository, self.target)
                for item in state["checks"]):
            raise SpecError("required implementation checks are missing, failed, or stale", "stale_evidence")
        return state

    def loop(self) -> dict:
        from .review import current, require_reviews, skip
        from langgraph.graph import StateGraph, START, END
        from typing import TypedDict
        class State(TypedDict):
            output: dict
        specify = self.task.get("specify", True)
        run_reviews = self.task.get("run_reviews", True)
        require_reviews(self, run_reviews)
        stages = (["specify", "plan", "tasks", "implement", "validate"] if specify else
                  ["plan", "tasks", "implement", "validate"])
        change = read_change(self.repository.root)
        existing = change["targets"].get(self.target.id) if change else None
        blocked_phases = {item["phase"] for item in change.get("gap_history", [])
            if item["status"] == "open" and item["target_id"] == self.target.id
            and item["task"] == self.task["task"]}
        authored = change.get("authored_specs", {}).get(self.target.id, {})
        has_authored_spec = bool(authored and "specify" not in blocked_phases
            and all(authored.get(key) == value for key, value in {
            "task": self.task["task"], "focus_id": self.task.get("focus_id"),
            "constraints": self.task.get("constraints", [])}.items()))
        if specify and has_authored_spec:
            stages.remove("specify")
        if ((not specify or has_authored_spec) and existing and existing.get("plan")
                and not blocked_phases.intersection({"context-solve", "plan"})
                and existing.get("task") == self.task["task"]
                and existing.get("focus_id") == self.task.get("focus_id")
                and existing.get("constraints", []) == self.task.get("constraints", [])
                and existing.get("spec_digest") == _target_revision(self.repository, self.target)):
            stages = ["tasks", "implement", "validate"]
            if existing.get("tasks") and "tasks" not in blocked_phases:
                stages = ["implement", "validate"]
                if (self.target.kind != "domain" and all(item["complete"] for item in existing["tasks"])
                        and "implementation" not in blocked_phases
                        and existing.get("implementation_digest") == _implementation_digest(self.repository, self.target)):
                    stages = ["validate"]
        stages.insert(1 if stages[0] == "specify" else 0, "review_spec")
        if self.target.implementation:
            stages.append("review_code")
        stages.append("ready")
        review_artifacts = []
        graph = StateGraph(State)
        def execute(name):
            def node(state):
                self.repository = SpecRepository(self.host.project_root, self.host.package_root)
                if name == "ready":
                    return {"output": self.mark_ready()["data"]}
                is_review = name.startswith("review_")
                if is_review:
                    mode = name.removeprefix("review_")
                    enabled = read_change(self.repository.root, required=True)["review_requirements"][self.target.id][mode]
                    if not enabled:
                        skip(self, mode)
                        reference = read_change(self.repository.root, required=True)["reviews"][self.target.id][mode]["artifact"]
                        review_artifacts.append(reference)
                        return {"output": self.response(answer=f"{mode} review explicitly skipped.", artifacts=[reference])["data"]}
                    if current(self, mode) is not None:
                        review_artifacts.append(read_change(self.repository.root, required=True)["reviews"][self.target.id][mode]["artifact"])
                        return {"output": self.response(answer=f"Current {mode} review retained.")["data"]}
                    if not self.host.coordinated:
                        progress(self.repository.root, phase=mode + "-review", status="active", invalidate=True)
                child_capability = "concorde-" + name
                if is_review:
                    child_capability = "concorde-review"
                payload = {"target_id": self.target.id, "task": self.task["task"],
                           "constraints": self.task.get("constraints", [])}
                if is_review:
                    payload["review_mode"] = mode
                if self.task.get("focus_id"):
                    payload["focus_id"] = self.task["focus_id"]
                if self.change_id:
                    payload["change_id"] = self.change_id
                child_host = replace(self.host, evidence=[], descriptions=self.host.descriptions,
                                     track_gaps=True, defer_ready=name == "validate")
                result = invoke_capability(self.capability, child_capability, self.configuration,
                    typed(CAPABILITY_CONTRACTS[child_capability][0], payload), child_host)
                self.host.evidence.extend(child_host.evidence)
                if result["output"] is None:
                    raise SpecError(f"{child_capability} blocked: " + canonical(result["errors"]), "child_blocked")
                data = result["output"]["data"]
                self.change_id = data["change_id"] or self.change_id
                self.work_directory = f"{WORK_PATH}/{self.target.id}" if self.change_id else None
                self.last_context = data["context_id"] or self.last_context
                self.completed.extend(data["completed_operations"])
                if is_review or name == "implement":
                    review_artifacts.extend(item for item in data["artifacts"] if item["id"].startswith("review."))
                self.repository = SpecRepository(self.host.project_root, self.host.package_root)
                return {"output": data}
            def observed(state):
                self.host.observe("stage_started", operation=self.capability, stage=name,
                                  invocation_id=self.host.invocation_id)
                try:
                    result = node(state)
                except Exception:
                    self.host.observe("stage_failed", operation=self.capability, stage=name,
                                      invocation_id=self.host.invocation_id)
                    raise
                self.host.observe("stage_finished", operation=self.capability, stage=name,
                                  invocation_id=self.host.invocation_id,
                                  outcome=result["output"].get("outcome"))
                return result
            return observed
        for index, stage in enumerate(stages):
            graph.add_node(stage, execute(stage))
            successor = stages[index + 1] if index + 1 < len(stages) else END
            graph.add_conditional_edges(stage, lambda state, next_stage=successor:
                next_stage if state["output"]["outcome"] in {"completed", "ready"} else END,
                {successor: successor, END: END})
        graph.add_edge(START, stages[0])
        result = graph.compile().invoke({"output": {}})["output"]
        artifacts = list({item["id"]: item for item in [*review_artifacts, *result["artifacts"]]}.values())
        coverage = []
        for reference in artifacts:
            if reference["id"].startswith("review."):
                verify_artifacts(self.repository.root, reference)
                value = validate_typed(decode(read_file(self.repository.root, reference["path"]).decode()),
                                       "concorde-review-result")["data"]
                coverage.append(f"{value['target_id']}/{value['review_mode']}={value['status']}")
        answer = result["answer"] + (" Review coverage: " + "; ".join(coverage) + "." if coverage else "")
        return self.response(result["outcome"], answer, gaps=result["gaps"], checks=result["checks"], artifacts=artifacts)


def _project_capability(capability, configuration, task, host):
    from ..specification.initialize import project_proposal, apply_project_proposal
    if capability == "concorde-configure":
        SpecRepository(host.project_root, host.package_root)
        value = decode(read_file(host.project_root, ".concorde/config.json").decode())
        value["operation_configuration"] = task["configuration"]
        changed = file_change(host.project_root, ".concorde/config.json", canonical(value) + "\n")
        apply_files(host.project_root, [changed], {changed["path"]})
        return typed("concorde-configure-response", {"status": "applied", "configuration": task["configuration"]})
    if task["action"] == "apply":
        if "proposal" not in task:
            raise SpecError("apply requires the complete typed proposal", "invalid_input")
        proposal = task["proposal"]
        value = apply_project_proposal(host.project_root, host.package_root,
            {"type_id": proposal["type_id"], "schema_version": proposal["schema_version"], **proposal["data"]})
        return typed(CAPABILITY_CONTRACTS[capability][1], {"status": "applied", "proposal": None, "files": value["files"]})
    if not {"name", "configuration"}.issubset(task):
        raise SpecError("initialization proposal requires name and configuration", "invalid_input")
    value = project_proposal(host.project_root, host.package_root, task["name"], task["configuration"], task.get("target_id", "domain.project"))
    proposal = typed("concorde-project-proposal", {key: value[key] for key in ("action", "base_digest", "files")})
    return typed(CAPABILITY_CONTRACTS[capability][1], {"status": "proposed", "proposal": proposal, "files": [x["path"] for x in value["files"]]})


def _dispatch(capability, configuration, task, host):
    if capability == "concorde-deliver":
        from .worktree_delivery import deliver
        return deliver(host, configuration, task)
    if capability in {"concorde-init", "concorde-configure"}:
        if host.mode == "describe-policy":
            raise SpecError("project proposals are the deterministic preview for this capability", "use_proposal")
        return _project_capability(capability, configuration, task, host)
    if capability == MAIN_CAPABILITY:
        if task["action"] == "ask":
            return MainInvocation(capability, configuration, task, host).run_answer()
        if task["action"] == "design-topology":
            return MainInvocation(capability, configuration, task, host).run_topology_design()
        if task["action"] == "accept-topology":
            return _prepare_topology(configuration, task["topology_proposal"], host)
        return _apply_topology(task["application"], host)
    main_completed: tuple[str, ...] = ()
    if (capability in MAIN_ROUTED_CAPABILITIES and host.routed_target is not None
            and task.get("target_id") != host.routed_target):
        raise SpecError("child target differs from the host's main route", "incompatible_handoff")
    if capability in MAIN_ROUTED_CAPABILITIES and not task.get("change_id"):
        if host.routed_target is None:
            main = MainInvocation(capability, configuration, task, host)
            route, blocked = main.select_one()
            if blocked is not None:
                return blocked
            task = {**task, "target_id": route["target_id"], "task": route["task"],
                    "constraints": route["constraints"]}
            if route["focus_id"] is not None:
                task["focus_id"] = route["focus_id"]
            else:
                task.pop("focus_id", None)
            host = replace(host, routed_target=route["target_id"])
            main_completed = tuple(main.completed)
    readonly = capability in {"concorde-main", "concorde-context-solve", "concorde-review"}
    readonly = readonly or (capability == "concorde-reflections-triage" and task["action"] == "status")
    if (host.mode == "execute" and not readonly
            and not (capability == "concorde-reflections-triage" and task["action"] == "record-gaps")):
        bind_owner(host.project_root, task, coordinated=host.coordinated)
    run = Invocation(capability, configuration, task, host)
    run.completed.extend(main_completed)
    if capability == "concorde-review":
        from .review import review_scope
        return review_scope(run, task["review_mode"])
    if host.mode == "describe-policy":
        stages = [capability] if capability in STAGE_ROLES else []
        describe_reviews = False
        if capability == "concorde-dev-loop":
            describe_reviews = task.get("run_reviews", True)
            stages = ["concorde-context-solve", "concorde-plan", "concorde-tasks"]
            if run.target.kind != "domain":
                stages.append("concorde-implement")
            if task.get("specify", True):
                stages.insert(0, "concorde-specify")
        for stage in stages:
            if stage == "concorde-context-solve" and describe_reviews:
                from .review import review
                review(run, "spec")
            run.stage(stage)
        if describe_reviews and run.target.implementation:
            from .review import review
            review(run, "code")
        return run.response("described")
    if capability == "concorde-reflections-triage":
        from ..reflections.scoped_triage import triage
        return triage(run)
    if capability == "concorde-specify":
        return run.author(capability)
    if capability == "concorde-plan":
        return run.plan()
    if capability == "concorde-tasks":
        return run.tasks()
    if capability == "concorde-implement":
        return run.implement()
    if capability == "concorde-validate":
        return run.validate(task.get("run_checks", True))
    if capability == "concorde-dev-loop":
        return run.loop()
    result = run.stage(capability)
    return run.response("completed" if result["outcome"] == "sufficient" else result["outcome"],
                        result["answer"], gaps=result["gaps"])


def run_capability(capability: str, configuration: dict | None, runtime_input: dict, *, host_context: CapabilityHost) -> dict:
    host = replace(host_context, invocation_id=str(uuid.uuid4()), evidence=[], depth=host_context.depth + 1)
    record_progress = False
    host.observe("capability_started", operation=capability, invocation_id=host.invocation_id, depth=host.depth)
    result = {"type_id": "concorde-operation-result", "schema_version": 2,
              "operation_id": capability if capability in CAPABILITY_CONTRACTS else None,
              "invocation_id": host.invocation_id, "mode": host.mode, "status": "blocked",
              "workspace": None, "output": None, "errors": []}
    try:
        if capability not in CAPABILITY_CONTRACTS:
            raise SpecError("unknown registered capability", "unknown_operation")
        if host.mode not in {"execute", "describe-policy"}:
            raise SpecError("unknown capability mode", "invalid_input")
        if host.depth == 1 and capability not in LIFECYCLE_CAPABILITIES:
            # The build is the only instruction source. Lifecycle capabilities run no agent
            # cognition and load no role, so they never consume generated/; every other
            # top-level invocation is verified once here, and load_role_prompt verifies it
            # again independently before trusting any generated/roles/*.md body.
            verify_fresh(host.package_root)
        configuration = validate_typed(configuration if configuration is not None else load_configuration(host.project_root), "concorde-operation-configuration")
        task = validate_typed(runtime_input, CAPABILITY_CONTRACTS[capability][0])["data"]
        task = copy.deepcopy(task)
        if capability != "concorde-deliver" and not (capability == MAIN_CAPABILITY
                and task.get("action") in {"accept-topology", "apply-topology"}):
            task.setdefault("constraints", [])
            task.setdefault("task", "Inspect the selected records")
        mutation = capability not in {"concorde-main", "concorde-context-solve", "concorde-review"}
        if capability == "concorde-init":
            mutation = task["action"] == "apply"
        if capability == MAIN_CAPABILITY:
            mutation = task["action"] in {"accept-topology", "apply-topology"}
        if capability == "concorde-reflections-triage" and task["action"] == "status":
            mutation = False
        if capability == "concorde-deliver":
            from .worktree_delivery import require_delivery_session
            primary = require_delivery_session(host, task["change_id"])
            workspace = {"path": primary["path"], "branch": primary["branch"]}
        else:
            host, workspace = _worktree(host, mutation, task)
        result["workspace"] = workspace
        if workspace and workspace.get("handoff"):
            from .session_handoff import handoff_prompt
            prompt = handoff_prompt(
                workspace["path"], branch=workspace.get("branch"), change_id=workspace.get("change_id"),
                task=runtime_input["data"].get("task"), constraints=runtime_input["data"].get("constraints"),
                completed="The host prepared a linked worktree from the committed base and local change state. "
                          "No task agent has run in it during this invocation.",
                remaining=f"Resume {capability} for this change with the original task and constraints.",
                checks="Worktree preparation succeeded; task implementation/review/validation have not run "
                       "during this invocation.",
                artifacts=[{"path": str(Path(workspace["path"]) / ".concorde/worktree.json"),
                            "applied": True, "temporary": True,
                            "storage": "create_worktree used a temporary directory; preserve it until completion"}],
                next_steps=f"Resume {capability} with change_id {workspace.get('change_id')} in the initial "
                           "directory after policy verification. The host must resolve fresh bounded contexts.",
                completion="Complete the accepted task and its required checks; development loops stop at ready. "
                           "Delivery requires the user's separate request from a participating worktree session.")
            raise SpecError("Change worktree prepared at " + workspace["path"]
                + ". Open a new agent in that worktree.\n\n" + prompt, "worktree_handoff_required")
        record_progress = mutation and capability != "concorde-deliver" and host.depth == 1
        if mutation and capability != "concorde-deliver":
            change = read_change(host.project_root)
            if change and change["status"] in {"delivering", "cleanup_pending"}:
                record_progress = False
                raise SpecError("this candidate is being delivered; resume delivery from either participating worktree",
                                "delivery_in_progress")
        if capability != "concorde-init":
            if configuration != load_configuration(host.project_root):
                raise SpecError("invocation configuration differs from initialized project settings", "configuration_mismatch")
        if host.configuration_snapshot and host.configuration_snapshot != canonical(configuration):
            raise SpecError("child configuration differs from the host snapshot", "configuration_mismatch")
        host = replace(host, configuration_snapshot=canonical(configuration))
        output = _dispatch(capability, configuration, task, host)
        outcome = output["data"].get("outcome", "completed")
        result.update(output=output, status="described" if host.mode == "describe-policy" else
            "succeeded" if outcome in {"completed", "ready", "delivered", "topology_proposed",
                                       "topology_prepared", "topology_applied"}
            else "failed" if outcome == "failed" else "blocked")
    except (SpecError, TypedDataError) as error:
        result["errors"] = [{"code": error.code, "field": error.field, "message": str(error)}]
    except BuildError as error:
        result["errors"] = [{"code": error.code, "field": "", "message": str(error)}]
    except Exception as error:
        result.update(status="failed", errors=[{"code": "execution_failed", "field": "", "message": str(error)}])
    if any(error["code"] in {"incompatible_handoff", "workspace_mismatch", "invalid_worktree_state"}
           for error in result["errors"]):
        record_progress = False
    if record_progress and host.mode == "execute" and result["status"] not in {"succeeded", "described"}:
        data = result["output"]["data"] if result["output"] else {}
        try:
            progress(host.project_root, status="blocked" if result["status"] == "blocked" else "failed",
                     outcome=data.get("outcome") or (result["errors"][0]["code"] if result["errors"] else "failed"),
                     gaps=data.get("gaps", []))
        except (ValueError, OSError) as error:
            result["errors"].append({"code": "state_persistence_failed", "field": "", "message": str(error)})
    host_context.evidence.extend(host.evidence)
    host.observe("capability_finished", operation=capability, invocation_id=host.invocation_id,
                 depth=host.depth, status=result["status"])
    return result


def validate_invocation(value: Any, capability: str | None = None) -> dict:
    """Validate the shared CLI/Studio envelope before selecting a trusted host."""
    if not isinstance(value, dict) or set(value) != {"type_id", "schema_version", "operation_id", "mode", "configuration", "input"}:
        raise SpecError("invocation fields do not match schema 2", "invalid_input")
    if value["type_id"] != "concorde-operation-invocation" or type(value["schema_version"]) is not int or value["schema_version"] != 2:
        raise SpecError("Profile 8 requires concorde-operation-invocation schema 2", "unsupported_version")
    if capability is not None and value["operation_id"] != capability:
        raise SpecError("invocation does not match this entry point", "incompatible_handoff")
    return value


def invocation_failure(capability: str | None, error: Exception) -> dict:
    """The same pre-host failure envelope for paired CLI and Studio entries."""
    return {"type_id": "concorde-operation-result", "schema_version": 2, "operation_id": capability,
        "invocation_id": str(uuid.uuid4()), "mode": None, "status": "blocked", "workspace": None,
        "output": None, "errors": [{"code": getattr(error, "code", "invalid_input"),
            "field": getattr(error, "field", ""), "message": str(error)}]}


def json_main(package_root: Path, capability: str, runner) -> int:
    """Shared stdin/limit/envelope/result handling for every skill's executable boundary.

    ``runner(host, configuration, request)`` is the skill's own capability module ``run`` function
    (proposal section 6.3); this never dispatches by name itself. Only a skill has an executable
    boundary at all, so every caller already knows and validates its own ``capability`` before
    reaching here (``scripts/run-capability.py``); there is no internal/stage fallback to guard.
    """

    host = None
    try:
        if sys.argv[1:]:
            raise SpecError("Capability inputs must be one JSON invocation on stdin", "invalid_input")
        raw = getattr(sys.stdin, "buffer", sys.stdin).read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise SpecError("invocation exceeds 1 MiB", "invalid_input")
        value = validate_invocation(decode(raw.decode() if isinstance(raw, bytes) else raw), capability)
        if os.environ.get("CONCORDE_STUDIO_URL"):
            from .studio_client import run_in_studio
            state = run_in_studio(os.environ["CONCORDE_STUDIO_URL"], value, Path.cwd(), package_root)
            result = state["result"]
            if state.get("policies"):
                print(canonical({"policies": state["policies"]}), file=sys.stderr)
        else:
            host = CapabilityHost(Path.cwd(), package_root, mode=value["mode"])
            result = runner(host, value["configuration"], value["input"])

    except Exception as error:
        result = invocation_failure(capability, error)
    if host and host.descriptions:
        print(canonical({"policies": host.descriptions}), file=sys.stderr)
    print(canonical(result))
    return 0 if result["status"] in {"succeeded", "described"} else 3
