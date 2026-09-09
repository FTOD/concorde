"""Global entry: answer questions, route work, and design or apply system topology."""
from concorde.host import contract_shapes as shapes
from agents import coordinator, spec_author

from . import external_name

CLASS = "global"
AGENTS = (coordinator.AGENT, spec_author.AGENT)
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
    "topology_proposal": {"anyOf": [shapes.typed_schema("concorde-topology-proposal"), {"type": "null"}]},
    "application": {"anyOf": [shapes.ARTIFACT, {"type": "null"}]},
    "files": shapes.array(shapes.PATH, unique=True),
    "gaps": shapes.array(shapes.GAP),
    "completed_capabilities": shapes.array(shapes.STRING),
    "workspace": shapes.WORKSPACE_CONTEXT,
})


def run(host, configuration, request):
    from concorde.host.capability_service import run_capability
    return run_capability(EXTERNAL_NAME, configuration, request, host_context=host)
