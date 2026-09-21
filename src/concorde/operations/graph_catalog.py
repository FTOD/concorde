"""The catalog of Concorde's executable Graphs, compiled with inert nodes for inspection.

Every Graph Concorde runs is a LangGraph ``StateGraph`` built by a factory in this package, the
Harness package or the Issues package. This catalog names each factory by its compiled graph
name and builds it with stub node functions, so inspection, publication and the Graph Spec check
all look at exactly the topology execution compiles: the same nodes, the same edges, the same
conditional routing. Building a catalog entry never resolves a context or starts an WorkerProfile.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _stub(name: str):
    return lambda state: {}


def catalog() -> dict[str, Callable[[], object]]:
    """Compiled-name to factory of the inert compiled Graph; the same factories execution uses."""
    from ..harness.batch_graph import build_batch_graph
    from ..harness.operation_graph import build_operation_graph
    from ..harness.operation_node import OperationNode
    from ..issues.graph import build_issue_graph, build_issue_verification_graph
    from ..spec.project_graph import build_project_graph
    from .dispatch_graph import build_dispatch_graph
    from .target_graph import build_target_graph

    return {
        "operation_graph": lambda: build_operation_graph(_stub, name="operation_graph"),
        "dispatch_graph": lambda: build_dispatch_graph(_stub),
        "target_graph": lambda: build_target_graph(_stub),
        "project_graph": lambda: build_project_graph(_stub),
        "issue_graph": lambda: build_issue_graph(_stub),
        "issue_verification_graph": lambda: build_issue_verification_graph(_stub),
        "batch_graph": lambda: build_batch_graph(
            _stub, name="batch_graph", item_node="execute_item"
        ),
        "operation_node": lambda: OperationNode("planner").graph(),
    }


def topology(graph) -> dict:
    """Nodes and edges of one compiled Graph as the Graph Spec check and publication read them."""
    drawing = graph.get_graph()
    return {
        "nodes": list(drawing.nodes),
        "edges": [
            {
                "source": edge.source,
                "target": edge.target,
                "conditional": edge.conditional,
            }
            for edge in drawing.edges
        ],
    }
