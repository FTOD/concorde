"""One operation invocation bound to a selected Module, and its model-backed stages.

``Invocation`` binds a task to its owning Module and change. ``stage`` freezes that Module's
complete context, compiles the worker's grant and launches the bound worker; the providers of
planning, authoring, implementation, validation and development compose these stages.
"""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from ..distribution.build import load_model_instructions
from ..spec.contracts import MODEL_STAGES
from ..spec.repository import SpecError, SpecRepository, digest, read_file
from ..spec.typed_data import OPERATION_CONTRACTS, checked_path, typed
from ..spec.validation import module_dependency_findings
from .change_worktree import WORK_PATH, blocker_scope, read_change
from .checks import check_service
from .configuration import load_configuration
from .context import (
    context_documents,
    materialize_documents,
    materialize_references,
    recheck_context,
    reference_grants,
    resolve_context,
)
from .host import (
    OperationHost,
    protocol_documents,
    run_worker,
    worker_description,
    worker_invocation,
)
from .permissions import PermissionPolicyError, PolicyBinding, compile_policy
from .revisions import implementation_digest, target_revision
from .worker_profile import worker_profile


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
        spec = target_revision(self.repository, self.target)
        return (
            digest(
                {
                    "spec": spec,
                    "code": implementation_digest(self.repository, self.target),
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
            from .change_worktree import record_task_gaps

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
        from .change_worktree import unchanged_task_gaps

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
            invocation = worker_invocation(
                self.configuration,
                operation=operation,
                stage=phase,
                prompt=prompt,
                workspace=project,
                context_value=value,
                receipt=receipt,
                policy=policy,
                protocol=protocol_documents(snapshot.value, granted),
            )
            self.host.descriptions.append(
                worker_description(
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
            from .operation_node import OperationNode

            result = None
            checks = (
                check_service(self.repository, self.target, self.host.invocation_id)
                if project_workspace
                else None
            )

            def launch_agent(context):
                # The OperationNode's typed state carries the admitted context in and the validated
                # result out; the Pi worker launch and its admission checks stay host-private.
                nonlocal result
                result, data = run_worker(
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

    def check_state(self, state: dict, *, allow_stale_spec: bool = False) -> None:
        if not allow_stale_spec and state.get("spec_digest") != target_revision(
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
