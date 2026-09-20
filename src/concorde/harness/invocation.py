"""One operation invocation bound to a selected Module, and its model-backed stages.

``Invocation`` binds a task to its owning Module and change. ``stage`` freezes that Module's
complete context, compiles the worker's grant and launches the bound worker. Retained providers
consume these stages under explicit caller selection; no stage authors project Specs.
"""

from __future__ import annotations

from ..distribution.build import load_model_instructions
from ..spec.contracts import MODEL_STAGES, REVIEW_OPERATIONS
from ..spec.repository import SpecError, SpecRepository, digest
from ..spec.typed_data import OPERATION_CONTRACTS, typed
from ..spec.validation import module_dependency_findings
from .change_worktree import WORK_PATH, blocker_scope, read_change
from .context import (
    context_documents,
    recheck_context,
    resolve_context,
)
from .host import (
    OperationHost,
)
from .launch import WorkerLaunch, launch_worker
from .revisions import implementation_digest, target_revision
from .worker_profile import worker_profile


class Invocation:
    def __init__(
        self,
        operation: str,
        configuration: dict,
        task: dict,
        host: OperationHost,
    ):
        self.operation, self.configuration, self.task, self.host = (
            operation,
            configuration,
            task,
            host,
        )
        self.repository = SpecRepository(host.project_root, host.package_root)
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
        if self.operation in REVIEW_OPERATIONS:
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
        assessment_intent = False
        if phase == "context-solve" and change:
            intent = {
                "task": self.task["task"],
                "focus_id": self.task.get("focus_id"),
                "constraints": self.task.get("constraints", []),
            }
            records = [
                change if change.get("target_id") == self.target.id else {},
                change.get("targets", {}).get(self.target.id, {}),
                change.get("review_intents", {}).get(self.target.id, {}),
            ]
            for name in ("shared_spec_reviews", "shared_implementation_reviews"):
                records.extend(
                    consumers.get(self.target.id, {})
                    for consumers in change.get(name, {}).values()
                )
            assessment_intent = any(
                {
                    key: record.get(key, [] if key == "constraints" else None)
                    for key in intent
                }
                == intent
                for record in records
            )
            if not assessment_intent:
                return
        if (
            self.host.track_gaps
            or assessment_intent
            or required_review
            or self.operation not in {"concorde-context-solve", *REVIEW_OPERATIONS}
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
                assessment_context_id=self.last_context if assessment_intent else None,
            )

    def pending_gaps(
        self,
        phase,
        snapshot=None,
        *,
        include_prerequisites=True,
        review_input_digest=None,
    ):
        from .change_worktree import unchanged_task_gaps

        if self.host.mode != "execute":
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
            if phase in {
                "spec-review",
                "plan",
                "tasks",
                "implementation",
                "code-review",
            }:
                prerequisites.add("specify")
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
        if self.operation not in {"concorde-context-solve"}:
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

        def validate(data: dict) -> None:
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

        project_workspace = agent.workspace == "project"
        data = launch_worker(
            self.host,
            self.configuration,
            self.repository,
            prompt,
            WorkerLaunch(
                operation=operation,
                stage=phase,
                role=role,
                snapshot=snapshot,
                granted=context_documents(self.repository, snapshot.value),
                value=typed(
                    "concorde-agent-stage-context",
                    {
                        "snapshot": typed("concorde-context-snapshot", snapshot.value),
                        "change_id": self.change_id,
                        "expected_artifacts": [],
                    },
                ),
                index=snapshot.serialized + "\n",
                result_type="concorde-agent-stage-result",
                receipt={"target_id": self.target.id},
                described={
                    "context_id": snapshot.id,
                    "outcome": "completed",
                    "answer": "",
                    "blockers": [],
                    "documents": [],
                    "plan": "",
                    "tasks": [],
                },
                validate=validate,
                recheck=lambda: recheck_context(
                    self.repository,
                    snapshot,
                    check_implementation=not implementation or readonly,
                ),
                target=self.target,
                target_id=self.target.id,
                change_id=self.change_id,
                implementation=(
                    (
                        self.repository.implementation_files(self.target)
                        if readonly
                        else self.repository.implementation_paths(self.target)
                    )
                    if project_workspace
                    else None
                ),
                writable=implementation and not readonly,
            ),
        )
        if self.host.mode == "describe-policy":
            return data
        if data["documents"]:
            # Project Specs are edited by the authorized outer agent, never this worker.
            raise SpecError(
                "this phase cannot author Spec documents", "permission_denied"
            )
        if implementation and not readonly:
            current = SpecRepository(self.repository.root, self.host.package_root)
            self.repository = current
            self.target = current.select(self.target.id)
        self.completed.append(operation)
        if (
            data["blockers"]
            or not defer_gap_resolution
            and data["outcome"] in {"completed", "sufficient"}
        ):
            self.record_gaps(phase, data["blockers"])
        return data

    def check_state(self, state: dict) -> None:
        if state.get("spec_digest") != target_revision(self.repository, self.target):
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
