"""One capability request bound to its selected Module: the invocation a provider works with.

``Invocation`` binds a request's task to its Module and change and builds the capability's typed
response. Model-backed stages are run by the native driver; Planning keeps the pending-gap records.
"""

from __future__ import annotations

from ..spec.repository import SpecError, SpecRepository
from ..spec.typed_data import data_schema, typed
from .change_worktree import WORK_PATH, read_change
from .host import AdmittedRequest, OperationHost
from .revisions import target_revision


def bind(request: AdmittedRequest) -> Invocation:
    """The Module-bound invocation of one admitted request."""
    return Invocation(
        request.operation, request.configuration, request.data, request.host
    )


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
        self.target = self.repository.module(task["target_id"], task.get("focus_id"))
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
        components=(),
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
        response_type = f"{self.operation}-response"
        fields = data_schema(response_type).get("properties", {})
        if "reviews" in fields:
            data["reviews"] = list(reviews)
        if "issues" in fields:
            data.update(issues=[], decision=None)
        if "components" in fields:
            data["components"] = list(components)
        return typed(response_type, data)

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


def validate_stage_identity(data: dict, context_id: str) -> None:
    """Shared identity/outcome predicates of native assessment."""
    if data["context_id"] != context_id:
        raise SpecError(
            "agent returned a different context identity", "incompatible_handoff"
        )
    if (data["outcome"] == "spec_incomplete" and not data["blockers"]) or (
        data["outcome"] in {"completed", "sufficient"} and data["blockers"]
    ):
        raise SpecError(
            "stage outcome does not match its task blockers", "invalid_completion"
        )
