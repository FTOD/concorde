"""Global entry: answer questions, route work, and design or apply system topology."""
from concorde.capabilities import contract_shapes as shapes, roles

from . import external_name

CLASS = "global"
ROLES = (roles.COORDINATOR, roles.READER, roles.SPEC_AUTHOR)
USES = ()
EXTERNAL_NAME = external_name(__name__.rsplit(".", 1)[-1])

REQUEST = shapes.obj({
    "action": {"enum": ["ask", "design-topology", "accept-topology", "apply-topology"]},
    "task": shapes.STRING, "target_id": shapes.STRING, "focus_id": shapes.STRING,
    "constraints": shapes.array(shapes.STRING),
    "topology_proposal": shapes.typed_schema("concorde-topology-proposal"),
    "application": shapes.ARTIFACT,
}, ("action", "task", "target_id", "focus_id", "constraints", "topology_proposal", "application"))

RESPONSE = shapes.obj({
    "action": {"enum": ["ask", "design-topology", "accept-topology", "apply-topology"]},
    "entry_target": shapes.STRING,
    "context_id": {"anyOf": [shapes.DIGEST, {"type": "null"}]},
    "outcome": shapes.MAIN_OUTCOMES,
    "answer": {"type": "string"},
    "discovered_targets": shapes.array(shapes.STRING, unique=True),
    "routes": shapes.array(shapes.ROUTE),
    "worker_results": shapes.array(shapes.typed_schema("concorde-main-worker-result")),
    "topology_proposal": {"anyOf": [shapes.typed_schema("concorde-topology-proposal"), {"type": "null"}]},
    "application": {"anyOf": [shapes.ARTIFACT, {"type": "null"}]},
    "files": shapes.array(shapes.PATH, unique=True),
    "gaps": shapes.array(shapes.GAP),
    "completed_operations": shapes.array(shapes.STRING),
    "workspace": shapes.WORKSPACE_CONTEXT,
})


def run(host, configuration, request):
    from concorde.capabilities.operation_service import run_operation
    return run_operation(EXTERNAL_NAME, configuration, request, host_context=host)
