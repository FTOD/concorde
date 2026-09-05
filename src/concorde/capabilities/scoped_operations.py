"""Trusted execution of every public Concorde Operation under Profile 8.

Agents consume frozen Spec snapshots. Deterministic checks execute separately and their raw
output never becomes a non-implementation agent input. Each stage starts a fresh process.
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass, field, replace, asdict
from pathlib import Path
from typing import Any

from .operation_data import (OPERATION_CONTRACTS, OperationDataError, canonical, checked_path,
    decode, typed, validate_typed, artifact)
from .operation_config import load_configuration
from .operation_permissions import (PolicyBinding, compile_policy, render_codex_configuration,
    render_claude_configuration, build_launch_specification, OperationExecutionResult)
from .skill_assets import EffectDeclaration, resolve_skill_prompt
from .protocol_contracts import AGENT_OPERATIONS
from ..specification.repository import SpecRepository, SpecError, digest, read_file, identifier
from ..specification.context import ContextSnapshot, resolve_context, recheck_context
from ..specification.changes import file_change, apply_files
from ..specification.validation import validate_repository


@dataclass(frozen=True)
class OperationHost:
    project_root: Path
    package_root: Path
    mode: str = "execute"
    executor: Any = None
    allow_primary_worktree: bool = False
    outer_sandbox: str | None = None
    configuration_snapshot: str = ""
    invocation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    descriptions: list[dict] = field(default_factory=list)
    evidence: list[Any] = field(default_factory=list)

    def __post_init__(self):
        if self.project_root.is_symlink() or self.package_root.is_symlink():
            raise SpecError("host roots cannot be symlinks", "workspace_mismatch")
        object.__setattr__(self, "project_root", self.project_root.resolve())
        object.__setattr__(self, "package_root", self.package_root.resolve())


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if result.returncode:
        raise SpecError("Git workspace operation failed: " + result.stderr.strip(), "workspace_mismatch")
    return result.stdout.strip()


def _worktree(host: OperationHost, mutation: bool) -> tuple[OperationHost, dict | None]:
    if not mutation or host.mode == "describe-policy":
        return host, None
    from .worktree import require_isolated_worktree, WorktreeBoundaryError
    try:
        require_isolated_worktree(host.project_root, allow_primary_worktree=host.allow_primary_worktree)
        return host, None
    except WorktreeBoundaryError:
        # Work from committed HEAD only; no stash, dirty-file copy, reset, or primary mutation.
        base = _git(host.project_root, "rev-parse", "HEAD")
        branch = "concorde/" + host.invocation_id
        parent = Path(tempfile.mkdtemp(prefix="concorde-worktree-"))
        path = parent / "project"
        _git(host.project_root, "worktree", "add", "-b", branch, str(path), base)
        return replace(host, project_root=path), {"path": str(path), "branch": branch, "base_commit": base}


def _attempt(root: Path, target_id: str, change_id: str) -> str:
    identifier(change_id)
    identifier(target_id)
    return f".concorde/attempts/{change_id}"


def _state(root: Path, attempt: str, target_id: str, focus_id: str | None, *, create=False) -> dict:
    path = checked_path(root, attempt + "/state.json")
    if path.exists():
        value = decode(read_file(root, attempt + "/state.json").decode())
        if value.get("target_id") != target_id or value.get("focus_id") != focus_id or value.get("schema_version") != 1:
            raise SpecError("change belongs to a different target or focus", "incompatible_handoff")
        return value
    if not create:
        raise SpecError("this Operation requires an active change", "missing_attempt")
    return {"schema_version": 1, "target_id": target_id, "focus_id": focus_id, "plan": "", "tasks": [],
            "checks": [], "spec_digest": None, "implementation_digest": None, "completed_operations": []}


def _save_state(root: Path, attempt: str, value: dict) -> None:
    relative = attempt + "/state.json"
    apply_files(root, [file_change(root, relative, canonical(value) + "\n")], {relative})


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


class Invocation:
    def __init__(self, operation: str, configuration: dict, task: dict, host: OperationHost):
        self.operation, self.configuration, self.task, self.host = operation, configuration, task, host
        self.repository = SpecRepository(host.project_root, host.package_root)
        self.target = self.repository.select(task["target_id"], task.get("focus_id"))
        self.change_id = task.get("change_id")
        self.attempt = _attempt(host.project_root, self.target.id, self.change_id) if self.change_id else None
        self.last_context = None
        self.completed: list[str] = []

    def response(self, outcome="completed", answer="", *, gaps=(), checks=(), artifacts=()) -> dict:
        return typed(OPERATION_CONTRACTS[self.operation][1], {
            "target_id": self.target.id, "focus_id": self.task.get("focus_id"), "change_id": self.change_id,
            "context_id": self.last_context, "outcome": outcome, "answer": answer,
            "gaps": list(gaps), "checks": list(checks), "artifacts": list(artifacts),
            "completed_operations": list(self.completed)})

    def stage(self, operation: str, *, inputs: tuple[dict, ...] = (), readonly=False) -> dict:
        phase, role = AGENT_OPERATIONS[operation]
        prompt = resolve_skill_prompt(self.host.package_root / "skills" / role / "SKILL.md", "skill", "")
        snapshot = resolve_context(self.repository, self.target.id, phase=phase, task=self.task["task"],
            focus_id=self.task.get("focus_id"), constraints=tuple(self.task.get("constraints", [])),
            instructions=prompt.body, stage_inputs=inputs)
        self.last_context = snapshot.id
        implementation = phase == "implementation"
        if implementation and not self.target.implementation:
            raise SpecError("implementation requires an explicitly owned Service/Module code scope", "unsupported_target")
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
                PolicyBinding(operation, phase, 0, role, role), roles,
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
            launch = build_launch_specification(operation=operation, stage=phase, occurrence=0, capability=role,
                integration=integration, agent=role, project_root=str(project), request=self.task["task"],
                prompt=prompt.body, prior_results=(), workspace_receipt_json=canonical(receipt),
                workspace_digest=snapshot.id, policy=policy, native_configuration=native,
                runtime_input_json=canonical(value), operation_configuration_json=canonical(self.configuration),
                invocation_id=invocation_id)
            self.host.descriptions.append({"operation": operation, "phase": phase, "context_id": snapshot.id,
                "project_root": str(project), "read_paths": list(policy.read_paths),
                "write_paths": list(policy.write_paths), "network": False, "fresh_session": True,
                "policy_digest": policy.digest})
            if self.host.mode == "describe-policy":
                return {"context_id": snapshot.id, "outcome": "completed", "answer": "", "gaps": [],
                        "documents": [], "plan": "", "tasks": []}
            from .operation_executor import AgentProcessExecutor
            executor = self.host.executor or AgentProcessExecutor()
            result = executor(launch)
            if not isinstance(result, OperationExecutionResult):
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
            self.completed.append(operation)
            return data

    def author(self, operation: str) -> dict:
        result = self.stage(operation)
        if result["outcome"] not in {"completed", "sufficient"}:
            return self.response(result["outcome"], result["answer"], gaps=result["gaps"])
        if self.host.mode == "describe-policy":
            return self.response("described")
        if result["documents"]:
            changes = [file_change(self.repository.root, item["path"], item["content"]) for item in result["documents"]]
            def verify():
                current = SpecRepository(self.repository.root, self.host.package_root)
                current.documents(current.select(self.target.id))
                current.contracts(current.select(self.target.id))
            apply_files(self.repository.root, changes, set(self.target.documents), verify=verify)
            self.repository = SpecRepository(self.host.project_root, self.host.package_root)
        return self.response(answer=result["answer"])

    def plan(self) -> dict:
        assessment = self.stage("concorde-context-solve")
        if assessment["outcome"] not in {"completed", "sufficient"}:
            return self.response(assessment["outcome"], assessment["answer"], gaps=assessment["gaps"])
        result = self.stage("concorde-plan")
        if result["outcome"] not in {"completed", "sufficient"}:
            return self.response(result["outcome"], result["answer"], gaps=result["gaps"])
        if self.host.mode == "describe-policy":
            return self.response("described")
        if not result["plan"].strip():
            raise SpecError("planning produced no usable plan", "invalid_completion")
        if self.change_id is None:
            self.change_id = "change." + self.host.invocation_id
            self.attempt = _attempt(self.repository.root, self.target.id, self.change_id)
        state = _state(self.repository.root, self.attempt, self.target.id, self.task.get("focus_id"), create=True)
        state.update(plan=result["plan"], tasks=[], checks=[], spec_digest=_target_revision(self.repository, self.target),
                     task=self.task["task"], constraints=self.task.get("constraints", []),
                     implementation_digest=None, completed_operations=list(self.completed))
        _save_state(self.repository.root, self.attempt, state)
        path = self.attempt + "/plan.md"
        apply_files(self.repository.root, [file_change(self.repository.root, path, result["plan"])], {path})
        return self.response(answer=result["answer"], artifacts=[artifact(self.repository.root, "plan", path)])

    def tasks(self) -> dict:
        if not self.attempt:
            raise SpecError("task authoring requires change_id", "missing_attempt")
        state = _state(self.repository.root, self.attempt, self.target.id, self.task.get("focus_id"))
        self.check_state(state)
        if not state["plan"]:
            raise SpecError("tasks require an authored plan", "missing_plan")
        inputs = (typed("concorde-plan-artifact", {"plan":state["plan"]}),)
        result = self.stage("concorde-tasks", inputs=inputs)
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
        state.update(tasks=tasks, checks=[], implementation_digest=None)
        _save_state(self.repository.root, self.attempt, state)
        return self.response(answer=result["answer"], artifacts=[artifact(self.repository.root, "change", self.attempt + "/state.json")])

    def implement(self) -> dict:
        if not self.attempt:
            raise SpecError("implementation requires change_id and authored tasks", "missing_attempt")
        state = _state(self.repository.root, self.attempt, self.target.id, self.task.get("focus_id"))
        self.check_state(state)
        if not state["tasks"]:
            raise SpecError("implementation requires tasks", "missing_tasks")
        if validate_repository(self.repository.root, package_root=self.host.package_root).status != "success":
            raise SpecError("reconcile all shared contracts before implementation", "incompatible_contracts")
        if self.target.kind == "domain":
            return self.implement_scope(state)
        inputs = (typed("concorde-implementation-task", {"plan":state["plan"],"tasks":state["tasks"]}),)
        result = self.stage("concorde-implement", inputs=inputs)
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
        _save_state(self.repository.root, self.attempt, state)
        return self.response(answer=result["answer"])

    def check_state(self, state: dict) -> None:
        if state.get("spec_digest") != _target_revision(self.repository, self.target):
            raise SpecError("selected Spec or its registered authority changed; replan this change", "stale_context")
        if state.get("task") != self.task["task"] or state.get("constraints") != self.task.get("constraints", []):
            raise SpecError("change intent differs from the authored plan; replan explicitly", "incompatible_handoff")

    def checklist(self):
        inputs=()
        if self.attempt:
            state=_state(self.repository.root,self.attempt,self.target.id,self.task.get("focus_id")); self.check_state(state)
            inputs=(typed("concorde-plan-artifact",{"plan":state["plan"]}),)
        result=self.stage("concorde-checklist",inputs=inputs)
        if result["outcome"] not in {"completed","sufficient"}: return self.response(result["outcome"],result["answer"],gaps=result["gaps"])
        content=result["plan"] or result["answer"]
        if not content.strip(): raise SpecError("checklist contains no acceptance criteria", "invalid_completion")
        if not self.attempt:return self.response(answer=content)
        path=self.attempt+"/checklist.md"
        apply_files(self.repository.root,[file_change(self.repository.root,path,content)],{path})
        return self.response(answer=result["answer"],artifacts=[artifact(self.repository.root,"checklist",path)])

    def issue_drafts(self):
        if not self.attempt:raise SpecError("issue drafts require authored tasks", "missing_attempt")
        state=_state(self.repository.root,self.attempt,self.target.id,self.task.get("focus_id"));self.check_state(state)
        if not state["tasks"]:raise SpecError("issue drafts require tasks", "missing_tasks")
        drafts=[{"task_id":t["id"],"target_id":t["target_id"],"title":t["description"],"body":"Acceptance:\n"+t["acceptance"]} for t in state["tasks"]]
        path=self.attempt+"/issue-drafts.json"
        apply_files(self.repository.root,[file_change(self.repository.root,path,canonical({"schema_version":1,"issues":drafts})+"\n")],{path})
        return self.response(answer="Local issue drafts prepared.",artifacts=[artifact(self.repository.root,"issues",path)])

    def implement_scope(self, state: dict) -> dict:
        """Coordinate separate component contexts; Domain agents never receive component bodies."""
        components = []
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
            components.append((task, component))
        # Reconcile each local consumer/provider view before any component implementation starts.
        for task, component in components:
            payload = {"target_id": component.id, "task": task["description"] + "\nAcceptance: " + task["acceptance"]}
            result = run_operation("concorde-specify", self.configuration, typed("concorde-specify-request", payload), host_context=self.host)
            if result["status"] != "succeeded":
                if result["output"]:
                    child=result["output"]["data"]
                    return self.response(child["outcome"],"Component "+component.id+": "+child["answer"],gaps=child["gaps"],artifacts=child["artifacts"])
                raise SpecError("component specification blocked: " + component.id, "child_blocked")
        if validate_repository(self.repository.root, package_root=self.host.package_root).status != "success":
            raise SpecError("reconcile all consumer/provider contracts before implementation", "incompatible_contracts")
        for task, component in components:
            payload = {"target_id": component.id, "task": task["description"] + "\nAcceptance: " + task["acceptance"]}
            result = run_operation("concorde-fast-loop", self.configuration, typed("concorde-fast-loop-request", payload), host_context=self.host)
            if result["status"] != "succeeded":
                if result["output"]:
                    child=result["output"]["data"]
                    return self.response(child["outcome"],"Component "+component.id+": "+child["answer"],gaps=child["gaps"],artifacts=child["artifacts"])
                raise SpecError("component implementation blocked: " + component.id, "child_blocked")
        state["component_revisions"] = {component.id: {"spec":_target_revision(self.repository,component),"implementation":_implementation_digest(self.repository,component)} for _,component in components}
        state["tasks"] = [{**task, "complete": True} for task in state["tasks"]]
        state["implementation_digest"] = _implementation_digest(self.repository, self.target)
        _save_state(self.repository.root, self.attempt, state)
        return self.response(answer="Participating components completed through separate contexts.")

    def validate(self, run_checks: bool = True) -> dict:
        report = validate_repository(self.repository.root, self.target.id, self.host.package_root)
        if report.status != "success":
            return self.response("failed", "Spec structure or shared contracts failed deterministic validation.")
        results = _check(self.repository, self.target, self.host.invocation_id) if run_checks else []
        if self.attempt:
            state = _state(self.repository.root, self.attempt, self.target.id, self.task.get("focus_id"))
            state["checks"] = results
            state["validation_spec_digest"] = report.result["source_digest"]
            _save_state(self.repository.root, self.attempt, state)
        self.completed.append("concorde-validate")
        failed = any(item["status"] != "passed" for item in results)
        return self.response("failed" if failed else "completed", "Deterministic validation failed." if failed else "Deterministic validation passed; semantic completeness is not proven.", checks=results)

    def deliver(self) -> dict:
        if not self.attempt:
            raise SpecError("delivery requires an active change", "missing_attempt")
        state = _state(self.repository.root, self.attempt, self.target.id, self.task.get("focus_id"))
        self.check_state(state)
        for target_id, revision in state.get("component_revisions",{}).items():
            component=self.repository.select(target_id)
            if revision!={"spec":_target_revision(self.repository,component),"implementation":_implementation_digest(self.repository,component)}:
                raise SpecError("a completed component changed before Domain delivery", "stale_evidence")
        if not state["tasks"] or any(not task["complete"] for task in state["tasks"]):
            raise SpecError("delivery requires completed tasks", "incomplete_attempt")
        if state["implementation_digest"] != _implementation_digest(self.repository, self.target):
            raise SpecError("implementation changed since completion", "stale_evidence")
        report = validate_repository(self.repository.root, self.target.id, self.host.package_root)
        if report.status != "success" or state.get("validation_spec_digest") != report.result["source_digest"]:
            raise SpecError("Spec validation is missing or stale", "stale_evidence")
        if {item["check_id"] for item in state["checks"]} != set(self.target.checks) or any(
                item["status"] != "passed" or item["source_digest"] != _check_revision(self.repository,self.target) for item in state["checks"]):
            raise SpecError("required implementation checks are missing, failed, or stale", "stale_evidence")
        attempt = checked_path(self.repository.root, self.attempt)
        for path in attempt.rglob("*"):
            if path.is_symlink():
                raise SpecError("delivery attempt contains a symlink", "unsafe_path")
        shutil.rmtree(attempt)
        self.completed.append("concorde-deliver")
        return self.response("delivered", "Removed the completed change attempt.", checks=state["checks"])

    def loop(self, fast=False) -> dict:
        from langgraph.graph import StateGraph, START, END
        from typing import TypedDict
        class State(TypedDict):
            output: dict
        stages = (["plan", "tasks", "implement", "validate", "deliver"] if fast else
                  ["specify", "plan", "tasks", "implement", "validate", "deliver"])
        graph = StateGraph(State)
        def execute(name):
            def node(state):
                operation = "concorde-" + name
                payload = {"target_id": self.target.id, "task": self.task["task"],
                           "constraints": self.task.get("constraints", [])}
                if self.task.get("focus_id"):
                    payload["focus_id"] = self.task["focus_id"]
                if self.change_id:
                    payload["change_id"] = self.change_id
                child_host = replace(self.host, evidence=[], descriptions=self.host.descriptions)
                result = run_operation(operation, self.configuration,
                    typed(OPERATION_CONTRACTS[operation][0], payload), host_context=child_host)
                self.host.evidence.extend(child_host.evidence)
                if result["output"] is None:
                    raise SpecError(f"{operation} blocked: " + canonical(result["errors"]), "child_blocked")
                data = result["output"]["data"]
                self.change_id = data["change_id"] or self.change_id
                self.attempt = _attempt(self.repository.root, self.target.id, self.change_id) if self.change_id else None
                self.last_context = data["context_id"] or self.last_context
                self.completed.extend(data["completed_operations"])
                self.repository = SpecRepository(self.host.project_root, self.host.package_root)
                return {"output": data}
            return node
        for index, stage in enumerate(stages):
            graph.add_node(stage, execute(stage))
            successor = stages[index + 1] if index + 1 < len(stages) else END
            graph.add_conditional_edges(stage, lambda state, next_stage=successor:
                next_stage if state["output"]["outcome"] in {"completed", "delivered"} else END,
                {successor: successor, END: END})
        graph.add_edge(START, stages[0])
        result = graph.compile().invoke({"output": {}})["output"]
        return self.response(result["outcome"], result["answer"], gaps=result["gaps"],
                             checks=result["checks"], artifacts=result["artifacts"])


def _project_operation(operation, configuration, task, host):
    from ..specification.initialize import project_proposal, migration_proposal, apply_project_proposal
    if operation == "concorde-configure":
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
        return typed(OPERATION_CONTRACTS[operation][1], {"status": "applied", "proposal": None, "files": value["files"]})
    if operation == "concorde-init":
        if not {"name", "configuration"}.issubset(task):
            raise SpecError("initialization proposal requires name and configuration", "invalid_input")
        value = project_proposal(host.project_root, host.package_root, task["name"], task["configuration"], task.get("target_id", "domain.project"))
    else:
        if not {"registry_json", "documents"}.issubset(task):
            raise SpecError("migration proposal requires an authored registry and documents", "invalid_input")
        value = migration_proposal(host.project_root, host.package_root, decode(task["registry_json"]), task["documents"], task.get("configuration"))
    proposal = typed("concorde-project-proposal", {key: value[key] for key in ("action", "base_digest", "files")})
    return typed(OPERATION_CONTRACTS[operation][1], {"status": "proposed", "proposal": proposal, "files": [x["path"] for x in value["files"]]})


def _dispatch(operation, configuration, task, host):
    if operation in {"concorde-init", "concorde-migrate", "concorde-configure"}:
        if host.mode == "describe-policy":
            raise SpecError("project proposals are the deterministic preview for this Operation", "use_proposal")
        return _project_operation(operation, configuration, task, host)
    run = Invocation(operation, configuration, task, host)
    if operation in {"concorde-context", "concorde-resolve-context"}:
        snapshot = resolve_context(run.repository, run.target.id, task=task["task"], phase=task.get("phase", "ask"),
            focus_id=task.get("focus_id"), constraints=tuple(task.get("constraints", [])))
        return typed(OPERATION_CONTRACTS[operation][1], {"snapshot": typed("concorde-context-snapshot", snapshot.value)})
    if host.mode == "describe-policy":
        stages = [operation] if operation in AGENT_OPERATIONS else []
        if operation in {"concorde-standard-dev-loop", "concorde-fast-loop"}:
            stages = ["concorde-context-solve", "concorde-plan", "concorde-tasks"]
            if run.target.kind != "domain":
                stages.append("concorde-implement")
            if operation == "concorde-standard-dev-loop":
                stages.insert(0, "concorde-specify")
        for stage in stages:
            run.stage(stage)
        return run.response("described")
    if operation == "concorde-reflections-triage":
        from ..reflections.scoped_triage import triage
        return triage(run)
    if operation in {"concorde-specify", "concorde-clarify", "concorde-constitution"}:
        return run.author(operation)
    if operation == "concorde-plan":
        return run.plan()
    if operation == "concorde-tasks":
        return run.tasks()
    if operation == "concorde-checklist": return run.checklist()
    if operation == "concorde-taskstoissues": return run.issue_drafts()
    if operation in {"concorde-implement", "concorde-converge"}:
        return run.implement()
    if operation == "concorde-validate":
        return run.validate(task.get("run_checks", True))
    if operation == "concorde-deliver":
        return run.deliver()
    if operation in {"concorde-standard-dev-loop", "concorde-fast-loop"}:
        return run.loop(operation == "concorde-fast-loop")
    result = run.stage(operation)
    return run.response("completed" if result["outcome"] == "sufficient" else result["outcome"],
                        result["answer"], gaps=result["gaps"])


def run_operation(operation: str, configuration: dict | None, runtime_input: dict, *, host_context: OperationHost) -> dict:
    host = replace(host_context, invocation_id=str(uuid.uuid4()), evidence=[])
    result = {"type_id": "concorde-operation-result", "schema_version": 2,
              "operation_id": operation if operation in OPERATION_CONTRACTS else None,
              "invocation_id": host.invocation_id, "mode": host.mode, "status": "blocked",
              "workspace": None, "output": None, "errors": []}
    try:
        if operation not in OPERATION_CONTRACTS:
            raise SpecError("unknown registered Operation", "unknown_operation")
        if host.mode not in {"execute", "describe-policy"}:
            raise SpecError("unknown Operation mode", "invalid_input")
        configuration = validate_typed(configuration if configuration is not None else load_configuration(host.project_root), "concorde-operation-configuration")
        task = validate_typed(runtime_input, OPERATION_CONTRACTS[operation][0])["data"]
        task = copy.deepcopy(task)
        task.setdefault("constraints", [])
        task.setdefault("task", "Inspect the selected records")
        mutation = operation not in {"concorde-ask", "concorde-analyze", "concorde-context-solve",
            "concorde-context", "concorde-resolve-context"}
        if operation in {"concorde-init", "concorde-migrate"}:
            mutation = task["action"] == "apply"
        if operation == "concorde-reflections-triage" and task["action"] == "status":
            mutation = False
        host, workspace = _worktree(host, mutation)
        result["workspace"] = workspace
        if operation not in {"concorde-init", "concorde-migrate"}:
            if configuration != load_configuration(host.project_root):
                raise SpecError("invocation configuration differs from initialized project settings", "configuration_mismatch")
        if host.configuration_snapshot and host.configuration_snapshot != canonical(configuration):
            raise SpecError("child configuration differs from the host snapshot", "configuration_mismatch")
        host = replace(host, configuration_snapshot=canonical(configuration))
        output = _dispatch(operation, configuration, task, host)
        outcome = output["data"].get("outcome", "completed")
        result.update(output=output, status="described" if host.mode == "describe-policy" else
            "succeeded" if outcome in {"completed", "delivered"} else "failed" if outcome == "failed" else "blocked")
    except (SpecError, OperationDataError) as error:
        result["errors"] = [{"code": error.code, "field": error.field, "message": str(error)}]
    except Exception as error:
        result.update(status="failed", errors=[{"code": "execution_failed", "field": "", "message": str(error)}])
    host_context.evidence.extend(host.evidence)
    return result


def json_main(package_root: Path, operation: str | None = None) -> int:
    host = None
    try:
        if sys.argv[1:]:
            raise SpecError("Operation inputs must be one JSON invocation on stdin", "invalid_input")
        raw = getattr(sys.stdin, "buffer", sys.stdin).read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise SpecError("invocation exceeds 1 MiB", "invalid_input")
        value = decode(raw.decode() if isinstance(raw, bytes) else raw)
        if not isinstance(value, dict) or set(value) != {"type_id", "schema_version", "operation_id", "mode", "configuration", "input"}:
            raise SpecError("invocation fields do not match schema 2", "invalid_input")
        if value["type_id"] != "concorde-operation-invocation" or type(value["schema_version"]) is not int or value["schema_version"] != 2:
            raise SpecError("Profile 8 requires concorde-operation-invocation schema 2", "unsupported_version")
        operation = operation or value["operation_id"]
        if value["operation_id"] != operation:
            raise SpecError("invocation does not match this entry point", "incompatible_handoff")
        host = OperationHost(Path.cwd(), package_root, mode=value["mode"])
        result = run_operation(operation, value["configuration"], value["input"], host_context=host)
    except Exception as error:
        result = {"type_id": "concorde-operation-result", "schema_version": 2, "operation_id": operation,
            "invocation_id": str(uuid.uuid4()), "mode": None, "status": "blocked", "workspace": None,
            "output": None, "errors": [{"code": getattr(error, "code", "invalid_input"),
                "field": getattr(error, "field", ""), "message": str(error)}]}
    if host and host.descriptions:
        print(canonical({"policies": host.descriptions}), file=sys.stderr)
    print(canonical(result))
    return 0 if result["status"] in {"succeeded", "described"} else 3


def operation_main(operation: str, package_root: Path) -> int:
    return json_main(package_root, operation)
