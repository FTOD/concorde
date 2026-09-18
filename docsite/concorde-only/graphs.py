"""Build-time graph inspection for Concorde's own website; never invokes a graph."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from concorde.development.loop_graph import build_loop_graph
from concorde.development.specify_graph import build_specify_graph
from concorde.harness.studio import build_studio_graph
from concorde.spec.contracts import operation_modules
from operations.dev_loop import GRAPH


def inspect_graph(graph):
    drawing = graph.get_graph(xray=True)
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


def export():
    modules = operation_modules()
    loops = []
    for specify, entry, code, label in (
        (True, "plan", True, "New change"),
        (False, "plan", True, "Skip authoring"),
        (False, "tasks", True, "Resume at tasks"),
        (False, "implement", True, "Resume implementation"),
        (False, "validate", True, "Resume validation"),
        (True, "plan", False, "No local code bindings"),
    ):
        loops.append(
            {
                "label": label,
                **inspect_graph(
                    build_loop_graph(
                        lambda name: lambda state: state,
                        include_specify=specify,
                        entry=entry,
                        has_code=code,
                    )
                ),
            }
        )
    from concorde.development.coordination_graph import (
        build_coordination_graph,
        build_stabilization_graph,
    )
    from concorde.development.discovery_graph import build_discovery_graph
    from concorde.development.dispatch_graph import build_dispatch_graph
    from concorde.development.operation_graph import build_operation_graph
    from concorde.development.plan_graph import build_plan_graph
    from concorde.development.project_graph import build_project_graph
    from concorde.development.query_graph import build_query_graph
    from concorde.development.target_graph import build_target_graph
    from concorde.development.topology_graph import (
        build_topology_apply_graph,
        build_topology_graph,
    )
    from concorde.harness.batch_graph import build_batch_graph
    from concorde.harness.operation_node import OperationNode
    from concorde.issues.graph import build_issue_graph, build_issue_verification_graph

    factories = {
        "Discovery": build_discovery_graph,
        "Target admission and discovery": build_target_graph,
        "Bound target admission": lambda nodes: build_target_graph(
            nodes, discover=False
        ),
        "Query and topology design": build_query_graph,
        "Topology preparation": build_topology_graph,
        "Topology application": build_topology_apply_graph,
        "Spec authoring and review": build_specify_graph,
        "Planning": build_plan_graph,
        "Initialization and configuration": build_project_graph,
        "Component coordination": build_coordination_graph,
        "Shared candidate stabilization": build_stabilization_graph,
        "Issue solving": build_issue_graph,
        "Issue verification": build_issue_verification_graph,
        # One worker invocation as a node typed by its contract; every model-backed stage runs one.
        "Operation node": lambda nodes: OperationNode("planner").graph(),
        "Operation admission": build_operation_graph,
        "Operation dispatch": build_dispatch_graph,
        "Sequential work items": lambda nodes: build_batch_graph(
            nodes, name="batch_graph", item_node="execute_item"
        ),
    }
    graphs = {
        name: inspect_graph(factory(lambda node: lambda state: {}))
        for name, factory in factories.items()
    }
    import inspect

    factory_sources = sorted(
        {
            Path(source).relative_to(ROOT).as_posix()
            for factory in [
                *factories.values(),
                build_batch_graph,
                build_loop_graph,
                build_studio_graph,
                OperationNode.graph,
            ]
            if factory.__name__ != "<lambda>"
            and (source := inspect.getsourcefile(factory)) is not None
        }
    )
    paths = sorted(
        set(factory_sources)
        | {
            "src/concorde/development/operation_host.py",
            "src/concorde/development/review.py",
            "src/concorde/harness/worker_executor.py",
            "src/concorde/issues/graph.py",
            "docsite/concorde-only/graphs.py",
        }
        | {
            Path(module.__file__).relative_to(ROOT).as_posix()
            for module in modules.values()
        }
    )
    operations = {
        name: inspect_graph(
            build_studio_graph(name, ROOT, ROOT)
            if module.PUBLIC
            else OperationNode(name).graph()
            if not hasattr(module, "REQUEST")
            else build_operation_graph(lambda node: lambda state: {}, name=name)
        )
        for name, module in modules.items()
    }
    metadata = {
        name: {
            "public": module.PUBLIC,
            "context_selection": module.CONTEXT_SELECTION,
            "deterministic": module.DETERMINISTIC,
            "state": {
                "input": sorted(module.STATE.input_schema.__annotations__),
                "output": sorted(module.STATE.output_schema.__annotations__),
            },
            "uses": ["concorde-" + child.replace("_", "-") for child in module.USES],
        }
        for name, module in modules.items()
    }
    return {
        "loops": loops,
        "graphs": graphs,
        "operations": operations,
        "operation_info": metadata,
        "factory_sources": factory_sources,
        "policy": GRAPH,
        "sources": [
            {
                "path": path,
                "digest": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
            }
            for path in paths
        ],
    }


if __name__ == "__main__":
    print(json.dumps(export()))
