"""Build-time graph inspection for Concorde's own website; never invokes a graph."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))
from concorde.development.loop_flow import build_loop_flow
from concorde.development.specify_flow import build_specify_flow
from concorde.harness.studio import build_studio_flow
from concorde.spec.contracts import capability_modules
from capabilities.dev_loop import FLOW


def inspect_flow(flow):
    drawing = flow.get_graph(xray=True)
    return {'nodes': list(drawing.nodes), 'edges': [
        {'source': edge.source, 'target': edge.target, 'conditional': edge.conditional}
        for edge in drawing.edges]}


def export():
    modules = capability_modules()
    loops = []
    for specify, entry, code, label in (
        (True, 'plan', True, 'New change'),
        (False, 'plan', True, 'Skip authoring'),
        (False, 'tasks', True, 'Resume at tasks'),
        (False, 'implement', True, 'Resume implementation'),
        (False, 'validate', True, 'Resume validation'),
        (True, 'plan', False, 'No local code bindings'),
    ):
        loops.append({'label': label, **inspect_flow(build_loop_flow(
            lambda name: lambda state: state, include_specify=specify, entry=entry, has_code=code))})
    from concorde.development.capability_flow import build_capability_flow
    from concorde.development.dispatch_flow import build_dispatch_flow
    from concorde.development.discovery_flow import build_discovery_flow
    from concorde.development.target_flow import build_target_flow
    from concorde.development.query_flow import build_query_flow
    from concorde.development.topology_flow import build_topology_flow, build_topology_apply_flow
    from concorde.development.plan_flow import build_plan_flow
    from concorde.development.project_flow import build_project_flow
    from concorde.development.coordination_flow import build_coordination_flow, build_stabilization_flow
    from concorde.harness.agent_model import agent_definition
    from concorde.harness.agent_node import AgentNode
    from concorde.harness.batch_flow import build_batch_flow
    from concorde.reflections.triage_flow import build_triage_flow
    factories = {
        'Discovery': build_discovery_flow, 'Target admission and discovery': build_target_flow,
        'Bound target admission': lambda nodes: build_target_flow(nodes, discover=False),
        'Query and topology design': build_query_flow,
        'Topology preparation': build_topology_flow, 'Topology application': build_topology_apply_flow,
        'Spec authoring and review': build_specify_flow, 'Planning': build_plan_flow, 'Initialization and configuration': build_project_flow,
        'Component coordination': build_coordination_flow, 'Shared candidate stabilization': build_stabilization_flow,
        'Reflection triage': build_triage_flow,
        # One worker invocation as a node typed by its contract; every model-backed stage runs one.
        'Agent invocation node': lambda nodes: AgentNode(agent_definition('planner')).flow(),
        'Capability admission': build_capability_flow, 'Capability dispatch': build_dispatch_flow,
        'Sequential work items': lambda nodes: build_batch_flow(nodes, name='batch_flow', item_node='execute_item'),
    }
    flows = {name: inspect_flow(factory(lambda node: lambda state: {})) for name, factory in factories.items()}
    import inspect
    factory_sources = sorted({Path(inspect.getsourcefile(factory)).relative_to(ROOT).as_posix()
        for factory in [*factories.values(), build_batch_flow, build_loop_flow, build_studio_flow, AgentNode.flow]
        if factory.__name__ != '<lambda>'})
    paths = sorted(set(factory_sources) | {
        'src/concorde/development/capability_host.py', 'src/concorde/development/review.py',
        'src/concorde/harness/worker_executor.py', 'src/concorde/reflections/scoped_triage.py',
        'docsite/concorde-only/flows.py'} | {
            Path(module.__file__).relative_to(ROOT).as_posix() for module in modules.values()})
    capabilities = {name: inspect_flow(build_studio_flow(name, ROOT, ROOT) if module.PUBLIC else
        build_capability_flow(lambda node: lambda state: {}, name=name)) for name, module in modules.items()}
    metadata = {name: {'public': module.PUBLIC, 'context_selection': module.CONTEXT_SELECTION,
                      'deterministic': module.DETERMINISTIC,
                      'uses': ['concorde-' + child.replace('_', '-') for child in module.USES]}
                for name, module in modules.items()}
    return {'loops': loops, 'flows': flows, 'capabilities': capabilities, 'capability_info': metadata,
            'factory_sources': factory_sources, 'policy': FLOW,
            'sources': [{'path': path, 'digest': hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
                        for path in paths]}


if __name__ == '__main__':
    print(json.dumps(export()))
