"""Trusted host orchestration for the registered JSON Operation boundaries."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import uuid
from datetime import datetime, timezone
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from .operation_config import load_configuration
from .operation_data import (OPERATION_CONTRACTS, OperationDataError, artifact, canonical,
                             checked_path, decode, typed, validate_typed, verify_artifacts)
from .operation_permissions import OperationExecutionResult
from .operation_runtime import (CapabilityResult, NestedOperationResult, OperationExecution,
                                build_operation, permission_launch_factory,
                                resolve_permission_runtime_context)


def _load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise OperationDataError("execution_failed", "", f"cannot load {path.name}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class OperationHost:
    """Host-only authority; none of these fields is deserialized from caller JSON.

    The serialized configuration snapshot is immutable and inherited by children.
    An injected executor is a trusted host adapter, used by embedding hosts/tests.
    """

    project_root: Path
    package_root: Path
    mode: str = "execute"
    executor: Any = None
    allow_primary_worktree: bool = False
    outer_sandbox: str | None = None
    configuration_snapshot: str = ""
    invocation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    descriptions: list[dict] = field(default_factory=list)
    evidence: list[CapabilityResult] = field(default_factory=list)

    def __post_init__(self):
        if self.project_root.is_symlink():
            raise OperationDataError("workspace_mismatch", "", "project root may not be a symlink")
        object.__setattr__(self, "project_root", self.project_root.resolve())
        object.__setattr__(self, "package_root", self.package_root.resolve())
        if self.mode not in {"execute", "describe-policy"}:
            raise OperationDataError("invalid_field", "/mode", "unsupported execution mode")
        if not self.configuration_snapshot:
            object.__setattr__(self, "configuration_snapshot", canonical(load_configuration(self.project_root)))

    @property
    def configuration(self) -> dict:
        return decode(self.configuration_snapshot)

    def child(self) -> OperationHost:
        return replace(self, evidence=[], invocation_id=str(uuid.uuid4()))

    @property
    def framework_prefix(self) -> str:
        try:
            relative = self.package_root.relative_to(self.project_root).as_posix()
            return "" if relative == "." else relative
        except ValueError:
            # An embedding host may execute a trusted source distribution for a
            # fixture project. It must still enforce each project's task policy.
            return ""


def _selection(project: Path, feature_path: str) -> Any:
    from ..understanding.feature_workspace import WorkspaceError, resolve_selected_workspace

    checked_path(project, feature_path, "/input/data/feature_path")
    try:
        workspace = resolve_selected_workspace(project, feature_path)
    except WorkspaceError as error:
        raise OperationDataError(
            "workspace_mismatch",
            "/input/data/feature_path",
            str(error),
        ) from error
    if not workspace.feature_id:
        raise OperationDataError("workspace_mismatch", "/input/data/feature_path", "an authored direct feature is required")
    return workspace


def _attempt_refs(project: Path, workspace: Any, required: tuple[str, ...] = ()) -> list[dict]:
    root = checked_path(project, workspace.attempt_dir)
    for name in required:
        if not checked_path(project, f"{workspace.attempt_dir}/{name}").is_file():
            raise OperationDataError("incompatible_handoff", "/output/data/artifacts", f"required attempt artifact is missing: {name}")
    refs = []
    if root.exists():
        if not root.is_dir():
            raise OperationDataError("invalid_field", "", "attempt path must be a directory")
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(project).as_posix()
            checked_path(project, relative)
            if path.is_file():
                identifier = f"attempt:{workspace.feature_id}:{path.relative_to(root).as_posix()}"
                refs.append(artifact(project, identifier, relative))
    return refs


def _stage_data(project: Path, feature_path: str, *, required: tuple[str, ...] = ()) -> dict:
    workspace = _selection(project, feature_path)
    context = resolve_permission_runtime_context(project, feature_path)
    return {"feature_id": workspace.feature_id, "feature_path": workspace.feature_path,
            "attempt_dir": workspace.attempt_dir, "source_digest": context.source_digest,
            "artifacts": _attempt_refs(project, workspace, required)}


def _planning_data(project: Path, context: Any) -> dict:
    from ..understanding.repository import ProjectRepository

    workspace = _selection(project, context.feature_path)
    package = ProjectRepository(project).load()
    feature = package.features[context.feature_id]
    members: set[str] = set()
    for role in ("selected-feature", "module-architecture", "module-ancestry", "constitution",
                 "owned-implementation"):
        for relative in context.role_paths.get(role, ()):
            path = checked_path(project, relative)
            candidates = [path] if path.is_file() else sorted(path.rglob("*")) if path.is_dir() else []
            for child in candidates:
                child_relative = child.relative_to(project).as_posix()
                checked_path(project, child_relative)
                if child.is_file() and not any(child_relative == denied or child_relative.startswith(denied + "/")
                                               for denied in context.denied_paths):
                    members.add(child_relative)
    return typed("concorde-planning-context", {
        "feature_id": context.feature_id, "feature_path": context.feature_path,
        "module_id": feature.module,
        "module_architecture": artifact(project, feature.module, context.module_architecture),
        "attempt_dir": workspace.attempt_dir, "source_digest": context.source_digest,
        "owned_artifacts": [artifact(project, context.feature_id if path == context.feature_path else f"source:{path}", path)
                            for path in sorted(members)],
        "provider_features": [{"feature_id": item.feature_id,
                               "artifact": artifact(project, item.feature_id, item.feature_path),
                               "interface_ids": list(item.interface_ids)} for item in context.required_feature_specs],
        "denied_paths": list(context.denied_paths),
    })


def _check_handoff(host: OperationHost, value: dict, feature_path: str) -> None:
    value = validate_typed(value)
    workspace = _selection(host.project_root, feature_path)
    data = value["data"]
    if data.get("feature_id") != workspace.feature_id or data.get("feature_path") != workspace.feature_path:
        raise OperationDataError("workspace_mismatch", "/input", "producer result belongs to another feature")
    verify_artifacts(host.project_root, value, "/input")
    if value["type_id"] == "concorde-plan-result":
        from ..understanding.planning_context import resolve_planning_context

        if resolve_planning_context(host.project_root, feature_path).source_digest != data["source_digest"]:
            raise OperationDataError("stale_reference", "/input/data/source_digest", "planning sources changed after the producer completed")


class _Invocation:
    def __init__(self, operation: str, configuration: dict, runtime_input: dict, host: OperationHost):
        self.operation, self.host = operation, host
        self.configuration = configuration
        self.input = runtime_input
        self.task = runtime_input["data"]
        self.feature_path = self.task.get("feature_path")
        self.context = None
        self.planning_context = None
        self.initial_feature_id = None
        self.plan_result = None
        self.delivery_proposal = None
        self.reflection_ids: list[str] = []
        self.reflection_entries: dict = {}
        self.queue = None
        self.concorde_project = False
        self.investigation_findings: list[dict] = []

    def reflection_inputs(self) -> list[dict]:
        from ..reflections.reflections import parse_auxiliary_reflections
        from ..understanding.repository import ProjectRepository

        entries = {entry.identifier: entry for entry in parse_auxiliary_reflections(ProjectRepository(self.host.project_root).load().auxiliary).entries}
        config = self.queue.load_config(self.host.project_root)
        plans = self.queue._load_plans(self.host.project_root, config)
        values = []
        for identifier in self.reflection_ids:
            entry = entries[identifier]
            item = {"reflection_id": identifier,
                    "document": artifact(self.host.project_root, f"reflection:{identifier}", entry.path)}
            if identifier in plans:
                item["plan"] = artifact(self.host.project_root, f"reflection-plan:{identifier}", plans[identifier]["path"])
            values.append(item)
        return values

    def validate_plan_sources(self, context: dict) -> None:
        from ..frontmatter import parse_document
        from ..reflections.reflections import parse_auxiliary_reflections
        from ..understanding.repository import ProjectRepository

        refs = self.input["data"].get("source_artifacts", [])
        if not refs:
            return
        verify_artifacts(self.host.project_root, refs, "/input/data/source_artifacts")
        feature_id = context["data"]["feature_id"]
        allowed = {item["path"]: item for item in context["data"]["owned_artifacts"]}
        allowed.update({item["artifact"]["path"]: item["artifact"] for item in context["data"]["provider_features"]})
        entries = {entry.identifier: entry for entry in parse_auxiliary_reflections(ProjectRepository(self.host.project_root).load().auxiliary).entries}
        for reference in refs:
            if reference == allowed.get(reference["path"]):
                continue
            kind, _, identifier = reference["id"].partition(":")
            entry = entries.get(identifier)
            if entry is None or entry.feature != feature_id:
                raise OperationDataError("workspace_mismatch", "/input/data/source_artifacts", "supporting source is outside the selected feature's admitted context")
            if kind == "reflection" and reference["path"] == entry.path:
                continue
            if kind == "reflection-plan":
                queue = _load_module(self.host.package_root / "scripts/reflections_queue.py", "concorde_plan_source_queue")
                config = queue.load_config(self.host.project_root)
                expected = f"{config['plans_dir']}/{identifier}.md"
                if reference["path"] == expected:
                    metadata, _ = parse_document(checked_path(self.host.project_root, expected).read_text(), expected)
                    if metadata.get("id") == identifier and metadata.get("implement_in_id") == feature_id:
                        continue
            raise OperationDataError("workspace_mismatch", "/input/data/source_artifacts", "supporting source identity does not match its owner")

    def prepare(self, invocation: OperationExecution) -> OperationExecution:
        from ..understanding.planning_context import resolve_planning_context

        name = invocation.capability.name
        if name == "concorde-plan":
            data = {key: copy.deepcopy(self.task[key]) for key in ("feature_path", "request", "constraints")}
            if self.reflection_ids:
                data["source_artifacts"] = [reference for item in self.reflection_inputs()
                                            for key, reference in item.items() if key in {"document", "plan"}]
            runtime_input = typed("concorde-plan-context", data)
            return replace(invocation, runtime_input=runtime_input, configuration=self.host.configuration,
                           invocation_id=self.host.invocation_id)
        if self.operation == "concorde-plan":
            self.context = resolve_planning_context(self.host.project_root, self.feature_path)
            current = _planning_data(self.host.project_root, self.context)
            self.validate_plan_sources(current)
            if name == "concorde-plan-context":
                runtime_input = self.input
                self.planning_context = current
            else:
                if current != self.planning_context:
                    raise OperationDataError("stale_reference", "/input/data/planning_context", "planning context changed before authoring")
                runtime_input = typed("concorde-plan-author-context", {"task": self.input, "planning_context": current})
        else:
            self.context = resolve_permission_runtime_context(self.host.project_root, self.feature_path)
            if name == "concorde-specify":
                runtime_input = typed("concorde-specify-context", {"task": self.input, "feature_path": self.feature_path})
            else:
                previous = invocation.prior_results[-1].domain_output if invocation.prior_results else None
                if previous is not None and self.host.mode == "execute":
                    _check_handoff(self.host, previous, self.feature_path)
                required = ("plan.md", "tasks.md") if name in {"concorde-tasks", "concorde-implement"} and self.host.mode == "execute" else ()
                data = _stage_data(self.host.project_root, self.feature_path, required=required)
                data = {"task": self.input, **data}
                if name == "concorde-analyze" and self.reflection_ids:
                    data.update(head=self.queue._captured_head(self.host.project_root),
                                verified_on=datetime.now(timezone.utc).date().isoformat(),
                                reflections=self.reflection_inputs())
                elif self.reflection_ids:
                    data["source_artifacts"] = [reference for item in self.reflection_inputs()
                                                for key, reference in item.items() if key in {"document", "plan"}]
                runtime_input = typed(name + "-context", data)
            if name == "concorde-deliver" and self.host.mode == "execute":
                from ..lifecycle.delivery import propose_delivery

                proposal = propose_delivery(self.host.project_root, self.feature_path)
                if proposal.status != "eligible":
                    raise OperationDataError("incompatible_handoff", "/input", "delivery eligibility failed: " + "; ".join(item.message for item in proposal.findings))
                self.delivery_proposal = proposal.result
        verify_artifacts(self.host.project_root, runtime_input, "/input")
        if self.context.feature_id:
            if self.initial_feature_id and self.context.feature_id != self.initial_feature_id:
                raise OperationDataError("workspace_mismatch", "/input", "selected feature identity changed during the Operation")
            self.initial_feature_id = self.context.feature_id
        return replace(invocation, runtime_input=runtime_input, configuration=self.host.configuration,
                       invocation_id=self.host.invocation_id)

    def launch(self, invocation: OperationExecution):
        settings = self.configuration["data"]
        return permission_launch_factory(self.context, settings["integration"],
                                         native_enforcement=settings["enforcement"] == "native",
                                         outer_sandbox=self.host.outer_sandbox)(invocation)

    def execute(self, invocation: OperationExecution):
        specification = invocation.launch_specification
        if self.host.mode == "describe-policy":
            self.host.descriptions.append({"operation": self.operation, "stage": invocation.stage,
                                           "capability": invocation.capability.name,
                                           "runtime_input": invocation.runtime_input,
                                           "policy": asdict(specification.policy)})
            return "policy described"
        from .operation_executor import AgentProcessExecutor

        executor = self.host.executor or AgentProcessExecutor()
        value = executor(specification)
        if not isinstance(value, OperationExecutionResult):
            raise OperationDataError("execution_failed", "", "trusted executor must return validated completion and enforcement evidence")
        receipt, completion = value.receipt, value.completion
        if (receipt.status != "success" or completion.status != "success"
                or receipt.requested_launch_digest != specification.digest
                or (completion.operation, completion.stage, completion.occurrence, completion.capability)
                != (invocation.operation, invocation.stage, invocation.occurrence, invocation.capability.name)
                or completion.workspace_digest != specification.workspace_digest
                or completion.invocation_id != self.host.invocation_id
                or completion.launch_digest != receipt.launch_digest):
            raise OperationDataError("execution_failed", "", "completion evidence does not match the current launch")
        name = invocation.capability.name
        if name == "concorde-analyze" and self.reflection_ids:
            from ..reflections.investigation import apply_investigation

            self.investigation_findings = apply_investigation(
                self.host.project_root, self.queue, invocation.runtime_input, completion.domain_output,
                self.reflection_entries, concorde_project=self.concorde_project)
            output = typed("concorde-analyze-result", _stage_data(self.host.project_root, self.feature_path))
        elif name == "concorde-plan-context":
            # A read-only context leaf must not have changed the resolved inputs.
            from ..understanding.planning_context import resolve_planning_context

            current = _planning_data(self.host.project_root, resolve_planning_context(self.host.project_root, self.feature_path))
            if current != self.planning_context:
                raise OperationDataError("stale_reference", "/output", "context inputs changed during resolution")
            output = current
        elif name == "concorde-plan-author":
            from ..understanding.planning_context import resolve_planning_context

            if resolve_planning_context(self.host.project_root, self.feature_path).source_digest != self.planning_context["data"]["source_digest"]:
                raise OperationDataError("stale_reference", "/output/data/source_digest", "planning author changed its admitted source inputs")
            verify_artifacts(self.host.project_root, self.planning_context, "/output")
            verify_artifacts(self.host.project_root, self.input["data"].get("source_artifacts", []), "/output")
            data = _stage_data(self.host.project_root, self.feature_path, required=("plan.md", "tasks.md"))
            data["source_digest"] = self.planning_context["data"]["source_digest"]
            output = typed("concorde-plan-result", data)
        elif name == "concorde-deliver":
            workspace = _selection(self.host.project_root, self.feature_path)
            if checked_path(self.host.project_root, workspace.attempt_dir).exists():
                raise OperationDataError("incompatible_handoff", "/output", "delivery did not remove the selected attempt")
            if self.delivery_proposal is None:
                raise OperationDataError("incompatible_handoff", "/output", "delivery has no admitted proposal")
            from ..lifecycle.delivery import _resolve_target, _retained_digests
            from ..understanding.repository import ProjectRepository

            package = ProjectRepository(self.host.project_root).load()
            _, paths = _resolve_target(self.host.project_root, package, workspace.feature_id)
            if _retained_digests(self.host.project_root, package, paths) != self.delivery_proposal["retained_digests"]:
                raise OperationDataError("stale_reference", "/output", "delivery changed retained source or executable context")
            output = typed(name + "-result", _stage_data(self.host.project_root, self.feature_path))
        else:
            if name == "concorde-validate":
                from ..understanding.validate import validate_project

                verify_artifacts(self.host.project_root, invocation.runtime_input, "/input")
                validation = validate_project(self.host.project_root, _selection(self.host.project_root, self.feature_path).feature_id)
                if validation.status != "success":
                    raise OperationDataError("incompatible_handoff", "/output", "deterministic architecture validation failed")
            output = typed(name + "-result", _stage_data(self.host.project_root, self.feature_path))
        return replace(value, domain_output=output)

    def nested(self, invocation: OperationExecution):
        child = self.host.child()
        output, evidence = _run(invocation.capability.name, self.host.configuration, invocation.runtime_input, child)
        if self.host.mode == "execute":
            _check_handoff(self.host, output, self.feature_path)
            self.plan_result = output
        self.host.evidence.extend(evidence)
        return NestedOperationResult(invocation.capability.name, output, evidence, self.host.mode == "describe-policy")

    def graph(self):
        module = _load_module(self.host.package_root / f"operations/{self.operation}/operation.py",
                              "concorde_registered_" + self.operation.replace("-", "_"))
        if getattr(module, "OPERATION_NAME", None) != self.operation:
            raise OperationDataError("unknown_type", "/operation_id", "source pair identity does not match registry")
        definition, bindings = module.OPERATION_STAGES, module.OPERATION_BINDINGS
        if self.operation == "concorde-reflections-triage":
            definition, bindings = module._selected_topology(self.task["action"], self.task.get("route"))
        if not definition:
            return []
        graph = build_operation(self.host.package_root, self.operation, definition, bindings, self.execute,
                                framework_prefix=self.host.framework_prefix, launch_factory=self.launch,
                                nested_dispatcher=self.nested, prepare_invocation=self.prepare)
        result = graph.invoke({"request": self.task.get("request", self.task.get("action", "")), "capability_results": []})
        return result["capability_results"]


def _run(operation: str, configuration: dict, runtime_input: dict, host: OperationHost) -> tuple[dict | None, tuple]:
    if operation not in OPERATION_CONTRACTS:
        raise OperationDataError("unknown_type", "/operation_id", "unknown Operation")
    manifest = decode((host.package_root / "concorde.json").read_text(encoding="utf-8"))
    if operation not in manifest["operations"]:
        raise OperationDataError("unknown_type", "/operation_id", "Operation is not registered by this package")
    configuration = validate_typed(configuration, "concorde-operation-configuration", "/configuration")
    if canonical(configuration) != host.configuration_snapshot:
        raise OperationDataError("configuration_mismatch", "/configuration", "caller configuration differs from the initialized project snapshot")
    runtime_input = validate_typed(runtime_input, OPERATION_CONTRACTS[operation][0], "/input")
    if configuration["data"]["enforcement"] == "outer" and not host.outer_sandbox:
        raise OperationDataError("configuration_mismatch", "/configuration/data/enforcement", "outer enforcement requires a verified embedding host")
    task = runtime_input["data"]
    if host.mode == "execute" and not (operation == "concorde-reflections-triage" and task["action"] == "status"):
        from .worktree import require_isolated_worktree

        require_isolated_worktree(host.project_root, allow_primary_worktree=host.allow_primary_worktree)
    if operation in {"concorde-plan", "concorde-standard-dev-loop"}:
        # Both registered lifecycle Operations start from an authored direct
        # feature. After the execute-mode worktree authority gate, admit that
        # identity before graph construction, permission resolution, or any
        # leaf launch so a missing path is a typed caller/workspace rejection
        # rather than an execution failure partway through orchestration.
        _selection(host.project_root, task["feature_path"])
    run = _Invocation(operation, configuration, runtime_input, host)
    if operation == "concorde-reflections-triage":
        return _run_triage(run)
    completed = run.graph()
    evidence = tuple([*host.evidence, *(item for item in completed if item.receipt is not None)])
    if host.mode == "describe-policy":
        return None, evidence
    if operation == "concorde-plan":
        output = completed[-1].domain_output
    else:
        workspace = _selection(host.project_root, task["feature_path"])
        output = typed("concorde-standard-dev-loop-result", {
            "feature_id": workspace.feature_id, "feature_path": workspace.feature_path,
            "completed_capabilities": [item.capability for item in completed],
            "delivery": {"status": "delivered", "attempt_dir": workspace.attempt_dir,
                         "retained_source_digest": "sha256:" + hashlib.sha256(canonical(run.delivery_proposal["retained_digests"]).encode()).hexdigest()},
        })
    return validate_typed(output, OPERATION_CONTRACTS[operation][1], "/output"), evidence


def _run_triage(run: _Invocation):
    from ..reflections.reflections import parse_auxiliary_reflections
    from ..understanding.repository import ProjectRepository

    host, task = run.host, run.task
    package = ProjectRepository(host.project_root).load()
    parsed = parse_auxiliary_reflections(package.auxiliary)
    if parsed.problems:
        raise OperationDataError("invalid_field", "/input/data/reflection_ids", "; ".join(item.message for item in parsed.problems))
    entries = {entry.identifier: entry for entry in parsed.entries}
    queue = _load_module(host.package_root / "scripts/reflections_queue.py", "concorde_operation_reflection_queue")
    if task["reflection_ids"]:
        selected = list(task["reflection_ids"])
    else:
        visible, _ = queue.queue_payload(host.project_root)
        selected = [entry["id"] for entry in visible["entries"]]
    for identifier in selected:
        if identifier not in entries:
            raise OperationDataError("invalid_field", "/input/data/reflection_ids", f"reflection does not exist: {identifier}")
    action = task["action"]
    run.queue = queue
    run.reflection_ids = selected
    run.reflection_entries = entries
    run.concorde_project = package.root_module_id == "module.concorde"
    if run.feature_path:
        workspace = _selection(host.project_root, run.feature_path)
        if any(entries[identifier].feature != workspace.feature_id for identifier in selected):
            raise OperationDataError("workspace_mismatch", "/input/data/reflection_ids", "selected reflections must belong to the same selected feature")
    if package.root_module_id == "module.concorde" and action in {"implement", "merge", "close"}:
        protected = {"feature.concorde.evolve-protocol", "entity.concorde.protocol", ".concorde/constitution.md"}
        if any(entries[identifier].feature in protected
               or entries[identifier].fields.get("Concerns") in protected for identifier in selected):
            raise OperationDataError("incompatible_handoff", "/input", "normative Protocol changes require the explicit protocol-evolution worktree flow")
    if action == "merge" and host.mode == "execute":
        if queue._git(host.project_root, "status", "--porcelain", "--untracked-files=no").stdout.strip():
            raise OperationDataError("workspace_mismatch", "/input", "merged-reflection cleanup requires clean tracked state")
        plans = queue._load_plans(host.project_root, queue.load_config(host.project_root))
        for identifier in selected:
            plan = plans.get(identifier)
            if (not plan or plan["status"] != "merged" or plan["route"] != "fast-loop"
                    or plan["effort"] != "small" or plan["recorded_under"] != entries[identifier].feature):
                raise OperationDataError("incompatible_handoff", "/input", "merge requires a matching merged small fast-loop plan")
            queue._validate_commit(host.project_root, identifier, plan.get("commit"), queue._captured_head(host.project_root))
    completed = run.graph()
    evidence = tuple([*host.evidence, *(item for item in completed if item.receipt is not None)])
    if host.mode == "describe-policy":
        return None, evidence
    if action == "close":
        queue.remove_closed(host.project_root, selected)
    elif action == "merge":
        queue.remove_merged(host.project_root, selected)
    elif action == "implement":
        for identifier in selected:
            queue.update_plan(host.project_root, identifier, ["status=implemented"])
    refreshed = parse_auxiliary_reflections(ProjectRepository(host.project_root).load().auxiliary)
    current = {entry.identifier: entry for entry in refreshed.entries}
    outcomes = []
    for identifier in selected:
        if action in {"close", "merge"}:
            if identifier in current:
                raise OperationDataError("incompatible_handoff", "/output", "disposition did not remove the selected record")
            outcome = "closed" if action == "close" else "merged"
        else:
            entry = current.get(identifier)
            if entry is None or entry.feature != entries[identifier].feature:
                raise OperationDataError("workspace_mismatch", "/output", "selected reflection identity changed during execution")
            outcome = ("needs-comments" if entry.human_intervention == "required" else
                       "implemented" if action == "implement" else
                       "planned" if entry.triage == "complete" else "inspected")
        outcomes.append({"reflection_id": identifier, "outcome": outcome})
    data = {"action": action, "reflection_ids": selected, "dispositions": outcomes}
    if run.plan_result and checked_path(host.project_root, run.plan_result["data"]["attempt_dir"]).is_dir():
        from ..understanding.planning_context import resolve_planning_context

        # A plan result is a reusable handoff only while its admitted durable
        # sources still match. Implementation may legitimately change them.
        source_digest = run.plan_result["data"]["source_digest"]
        if resolve_planning_context(host.project_root, run.feature_path).source_digest == source_digest:
            plan_data = _stage_data(host.project_root, run.feature_path, required=("plan.md", "tasks.md"))
            plan_data["source_digest"] = source_digest
            data["plan_result"] = typed("concorde-plan-result", plan_data)
    return typed("concorde-reflections-triage-result", data), evidence


def run_operation(operation: str, configuration: dict, runtime_input: dict, *, host_context: OperationHost) -> dict:
    invocation_id = str(uuid.uuid4())
    active_host = replace(host_context, invocation_id=invocation_id, evidence=[])
    result = {"type_id": "concorde-operation-result", "schema_version": 1,
              "operation_id": operation if operation in OPERATION_CONTRACTS else None,
              "invocation_id": invocation_id, "mode": host_context.mode,
              "status": "blocked", "output": None, "errors": []}
    try:
        output, evidence = _run(operation, configuration, runtime_input, active_host)
        host_context.evidence[:] = evidence
        result.update(status="described" if host_context.mode == "describe-policy" else "succeeded", output=output)
    except OperationDataError as error:
        result["errors"] = [error.to_dict()]
        if error.code == "execution_failed":
            result["status"] = "failed"
    except Exception as error:
        result.update(status="failed", errors=[{"code": "execution_failed", "field": "", "message": str(error)}])
    return result


def operation_main(operation: str, package_root: Path) -> int:
    """Read exactly one JSON invocation on stdin; reserve stdout for its result."""
    mode = None
    resolved = None
    host = None
    try:
        if sys.argv[1:]:
            raise OperationDataError("invalid_field", "", "Operation domain arguments must be one JSON invocation on stdin")
        raw = getattr(sys.stdin, "buffer", sys.stdin).read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise OperationDataError("invalid_json", "", "invocation exceeds the 1 MiB input limit")
        value = decode(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
        expected = {"type_id", "schema_version", "operation_id", "mode", "configuration", "input"}
        if not isinstance(value, dict) or set(value) != expected:
            raise OperationDataError("invalid_field", "", "invocation fields do not match schema 1")
        if value["type_id"] != "concorde-operation-invocation":
            raise OperationDataError("unknown_type", "/type_id", "expected concorde-operation-invocation")
        if type(value["schema_version"]) is not int or value["schema_version"] != 1:
            raise OperationDataError("unsupported_version", "/schema_version", "invocation requires schema_version 1")
        if value["operation_id"] != operation:
            raise OperationDataError("incompatible_handoff", "/operation_id", "invocation does not match this Python entry point")
        resolved = operation
        if not isinstance(value["mode"], str) or value["mode"] not in {"execute", "describe-policy"}:
            raise OperationDataError("invalid_field", "/mode", "unknown mode")
        mode = value["mode"]
        host = OperationHost(Path.cwd(), package_root, mode=mode)
        result = run_operation(operation, value["configuration"], value["input"], host_context=host)
    except (OperationDataError, OSError, UnicodeError, ValueError, TypeError) as error:
        problem = error if isinstance(error, OperationDataError) else OperationDataError("invalid_json", "", str(error))
        result = {"type_id": "concorde-operation-result", "schema_version": 1,
                  "operation_id": resolved, "invocation_id": str(uuid.uuid4()), "mode": mode,
                  "status": "blocked", "output": None, "errors": [problem.to_dict()]}
    if host is not None and host.descriptions:
        print(canonical({"policies": host.descriptions}), file=sys.stderr)
    print(canonical(result))
    return 0 if result["status"] in {"succeeded", "described"} else 3
