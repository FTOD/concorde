"""The catalog of Concorde's executable Graphs, compiled with inert nodes for inspection.

Every Graph Concorde runs is a LangGraph ``StateGraph`` built by a factory in this package, the
Harness package or the Issues package. This catalog names each factory by its compiled graph
name and builds it with stub node functions, so inspection, publication and the Graph Spec check
all look at exactly the topology execution compiles: the same nodes, the same edges, the same
conditional routing. Building a catalog entry never resolves a context or starts an Agent.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _stub(name: str):
    return lambda state: {}


def catalog() -> dict[str, Callable[[], object]]:
    """Only genuine explicitly selected StateGraph Operations; never native flow mirrors."""
    from ..harness.operation_node import OperationNode
    from .catalog import register_types

    # The Graphs' State schemas are the registered typed values of their Agents.
    register_types()
    return {
        "terminal_agent_operation": lambda: OperationNode("context_assessor").graph()
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
