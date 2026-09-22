"""One operation invocation bound to a selected Module, and its model-backed stages.

``Invocation`` binds a task to its owning Module and change. ``stage`` freezes that Module's
complete context, compiles the worker's grant and launches the bound worker. Retained providers
consume these stages under explicit caller selection; no stage authors project Specs.
"""

from __future__ import annotations

from concorde.distribution.build import load_model_instructions
from concorde.harness.context import (
    context_documents,
    recheck_context,
    resolve_context,
)
from concorde.harness.invocation import Invocation as BaseInvocation
from concorde.harness.invocation import validate_stage_identity
from concorde.harness.launch import WorkerLaunch, launch_worker
from concorde.harness.worker_profile import worker_profile
from concorde.spec.contracts import MODEL_STAGES
from concorde.spec.repository import SpecError, SpecRepository
from concorde.spec.typed_data import typed


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
        from concorde.issues.references import observation_context

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
        pending = self.pending_gaps(phase, snapshot, include_prerequisites=not readonly)
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
        blocked = self.assessment_dependencies(snapshot, operation)
        if blocked is not None:
            return blocked

    def validate(data: dict) -> None:
        validate_stage_identity(data, snapshot.id)

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
        # Project Specs are edited by the task-authorized calling session, never this worker.
        raise SpecError("this phase cannot author Spec documents", "permission_denied")
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


class Invocation(BaseInvocation):
    stage = stage
