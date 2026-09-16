"""The catalog of Concorde's executable Flows, compiled with inert nodes for inspection.

Every Flow Concorde runs is a LangGraph ``StateGraph`` built by a factory in this package, the
Harness package or the Issues package. This catalog names each factory by its compiled graph
name and builds it with stub node functions, so inspection, publication and the Flow Spec check
all look at exactly the topology execution compiles: the same nodes, the same edges, the same
conditional routing. Building a catalog entry never resolves a context or starts an WorkerProfile.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[3]


def _stub(name: str):
    return lambda state: {}


def catalog() -> dict[str, Callable[[], object]]:
    """Compiled-name to factory of the inert compiled Flow; the same factories execution uses."""
    from ..harness.worker_profile import worker_profile
    from ..harness.capability_node import CapabilityNode
    from ..harness.batch_flow import build_batch_flow
    from ..issues.flow import build_issue_flow, build_issue_verification_flow
    from .capability_flow import build_capability_flow
    from .coordination_flow import build_coordination_flow, build_stabilization_flow
    from .discovery_flow import build_discovery_flow
    from .dispatch_flow import build_dispatch_flow
    from .loop_flow import build_loop_flow
    from .plan_flow import build_plan_flow
    from .project_flow import build_project_flow
    from .query_flow import build_query_flow
    from .specify_flow import build_specify_flow
    from .target_flow import build_target_flow
    from .topology_flow import build_topology_apply_flow, build_topology_flow
    return {
        "capability_flow": lambda: build_capability_flow(_stub, name="capability_flow"),
        "dispatch_flow": lambda: build_dispatch_flow(_stub),
        "target_flow": lambda: build_target_flow(_stub),
        "discovery_flow": lambda: build_discovery_flow(_stub),
        "query_flow": lambda: build_query_flow(_stub),
        "topology_flow": lambda: build_topology_flow(_stub),
        "topology_apply_flow": lambda: build_topology_apply_flow(_stub),
        "plan_flow": lambda: build_plan_flow(_stub),
        "project_flow": lambda: build_project_flow(_stub),
        "development_flow": lambda: build_loop_flow(_stub, dynamic=True),
        "specify_flow": lambda: build_specify_flow(_stub),
        "coordination_flow": lambda: build_coordination_flow(_stub),
        "stabilization_flow": lambda: build_stabilization_flow(_stub),
        "issue_flow": lambda: build_issue_flow(_stub),
        "issue_verification_flow": lambda: build_issue_verification_flow(_stub),
        "batch_flow": lambda: build_batch_flow(_stub, name="batch_flow", item_node="execute_item"),
        "capability_node": lambda: CapabilityNode("planner").flow(),
    }


def topology(flow) -> dict:
    """Nodes and edges of one compiled Flow as the Flow Spec check and publication read them."""
    drawing = flow.get_graph()
    return {"nodes": list(drawing.nodes),
            "edges": [{"source": edge.source, "target": edge.target, "conditional": edge.conditional}
                      for edge in drawing.edges]}
