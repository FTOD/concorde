"""Planning's typed values, registered with Spec tooling when this module is loaded."""

from __future__ import annotations

from ..harness.native_result import TASK_ITEM
from ..spec.typed_data import DIGEST, STRING, array, obj, register

PLAN_ARTIFACT = obj({"plan": STRING})
TASK_IDENTITY_CONSTRAINTS = obj({"reserved_task_ids": array(STRING, unique=True)})
# contract.planning.implementation-task
IMPLEMENTATION_TASK = obj({"plan": STRING, "tasks": array(TASK_ITEM)})
TASK_SCOPE_FEEDBACK = obj(
    {"tasks_digest": DIGEST, "reason": {"const": "implementation_boundary"}}
)

register("concorde-plan-artifact", 1, PLAN_ARTIFACT)
register("concorde-task-identity-constraints", 1, TASK_IDENTITY_CONSTRAINTS)
register("concorde-implementation-task", 1, IMPLEMENTATION_TASK)
register("concorde-task-scope-feedback", 1, TASK_SCOPE_FEEDBACK)
