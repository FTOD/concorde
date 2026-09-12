"""Global development loop: route one change, then specify, review, plan, task, implement,
validate and review code to a ready candidate.

``specify=false`` skips Spec authoring (the former fast loop); ``run_reviews=false`` records an
explicit skip for each review mode instead of running it. A review requirement already recorded
for a change cannot be disabled by a later ``run_reviews=false``.

A code-owning target's blocking code-review finding does not immediately stop the Flow: the
loop's only automatic revision edge is ``review_code -> tasks``, bounded by ``FLOW``'s declared
``max_repair_iterations``. Unchanged blocking feedback across a repair, or exhausting the declared
limit, stops the Flow for a human instead of retrying forever (G2). ``FLOW`` is recorded per
target in ``.concorde/worktree.json`` (``change["graph"][target_id]["policy"]``) when the loop
first runs for that target, so a resumed loop keeps using the policy it started with.
"""
from concorde.spec import contract_shapes as shapes
from agents import coordinator

from . import external_name

CLASS = "global"
DETERMINISTIC = False
AGENTS = (coordinator.AGENT,)
USES = ("specify", "review", "plan", "tasks", "implement", "validate")
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

# The only automatic revision edge (review_code -> tasks) is bounded by this declared policy
# (G2: "Limits may be time, iterations, resource budgets or an explicit bounded host policy").
FLOW = {"max_repair_iterations": 2}
# Persisted records and older Python integrations retain their existing identifiers.
GRAPH = FLOW

REQUEST = shapes.obj({
    **shapes.TASK_FIELDS,
    "specify": {"type": "boolean"},
    "run_reviews": {"type": "boolean"},
    "repair_task_scope": shapes.obj({"tasks_digest": shapes.DIGEST}),
}, ("target_id", *shapes.TASK_OPTIONAL, "specify", "run_reviews", "repair_task_scope"))

RESPONSE = shapes.stage_response()


def run(host, configuration, request):
    from concorde.development.capability_service import run_capability
    return run_capability(EXTERNAL_NAME, configuration, request, host_context=host)
