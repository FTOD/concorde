"""Flow execution, viewer inspection and JSON boundaries share real runtime factories."""
import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from langgraph.checkpoint.memory import InMemorySaver

from concorde.development.capability_host import MainInvocation
from concorde.harness.batch_flow import run_batch_flow
from concorde.spec.verification import verifies
from tests.concorde.harness import test_studio as studio_fixtures

invocation = studio_fixtures.invocation


class FlowTests(TestCase):
    def fixture(self):
        fixture = studio_fixtures.StudioTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        return fixture

    @verifies('scenario.harness.flow-inspection')
    def test_inspection_never_resolves_a_context_or_runs_an_agent(self):
        fixture = self.fixture()
        with patch('concorde.development.capability_host.SpecRepository') as repository:
            flow = fixture.graph('concorde-main')
            drawing = flow.get_graph(xray=True)
            repository.assert_not_called()
        self.assertEqual([], fixture.double.calls)
        self.assertTrue(any(name.endswith(':discover:decide') for name in drawing.nodes))
        self.assertTrue(any(name.endswith(':apply_atomically') for name in drawing.nodes))
        self.assertFalse(any(name.endswith(':development_loop') for name in drawing.nodes))

    @verifies('scenario.harness.flow-inspection', 'scenario.development.flow-execution')
    def test_nested_updates_and_checkpoints_contain_json_not_host_objects(self):
        fixture = self.fixture()
        flow = fixture.graph('concorde-main')
        saver = InMemorySaver()
        flow.checkpointer = saver
        config = {'configurable': {'thread_id': 'flow-json'}}
        updates = list(flow.stream({'invocation': invocation('concorde-main', data={'task': 'Explain transfer'})},
                                   config, subgraphs=True, stream_mode='updates'))
        # This also catches callbacks accidentally returned through private state channels.
        json.dumps(updates)
        names = {name for _, update in updates for name in update}
        self.assertIn('decide', names)
        self.assertIn('expand_context', names)
        for checkpoint in saver.list(config):
            channels = checkpoint.checkpoint['channel_values']
            json.dumps(channels)
            self.assertNotIn('session', channels)
        result = flow.get_state(config, subgraphs=True).values['result']
        self.assertEqual('succeeded', result['status'], result)

    @verifies('scenario.harness.flow-inspection')
    def test_concurrent_runs_have_separate_runtime_contexts(self):
        fixture = self.fixture()
        flow = fixture.graph()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: flow.invoke({'invocation': invocation()}), range(2)))
        self.assertEqual(['succeeded', 'succeeded'], [value['result']['status'] for value in results])
        self.assertNotEqual(results[0]['result']['invocation_id'], results[1]['result']['invocation_id'])
        for value in results:
            ids = {event['invocation_id'] for event in value['events']}
            self.assertEqual({value['result']['invocation_id']}, ids)

    @verifies('scenario.development.flow-bounds')
    def test_discovery_can_expand_beyond_the_default_langgraph_limit(self):
        main = MainInvocation.__new__(MainInvocation)
        main.repository = SimpleNamespace(targets={str(i): SimpleNamespace(kind='module') for i in range(40)},
                                          select=lambda name: SimpleNamespace(kind='module', id=name))
        main.host = SimpleNamespace(mode='execute')
        main.task = {}
        main.completed = []
        main.discovered = ['entry']
        main.stage_context_text = lambda _: '\n'.join('module.' + str(i) for i in range(35))
        main.stage = Mock(side_effect=lambda phase, occurrence: {
            'outcome': 'expand', 'expand_targets': ['module.' + str(occurrence)]
        } if occurrence < 35 else {'outcome': 'answered', 'answer': 'Complete'})
        routes, decision = main.discover_routes()
        self.assertEqual([], routes)
        self.assertEqual('answered', decision['outcome'])
        self.assertEqual(36, main.stage.call_count)

    @verifies('scenario.development.flow-bounds', 'scenario.development.flow-execution')
    def test_large_batch_stops_before_running_dependent_items(self):
        visited = []
        def operation(item):
            visited.append(item)
            return {'outcome': 'blocked'} if item == 37 else None
        result = run_batch_flow(range(60), operation, name='review_test_flow', item_node='review_module')
        self.assertEqual({'outcome': 'blocked'}, result)
        self.assertEqual(list(range(38)), visited)

    @verifies('scenario.development.flow-execution')
    def test_scheduler_failure_keeps_the_error_envelope_and_final_event(self):
        from concorde.development.capability_host import CapabilityHost, run_capability
        fixture = self.fixture()
        events = []
        host = CapabilityHost(fixture.root, studio_fixtures.PACKAGE,
                              observer=lambda event, **details: events.append(event))
        value = invocation()
        with patch('concorde.development.capability_flow.build_capability_flow') as build:
            build.return_value.invoke.side_effect = RuntimeError('scheduler failed')
            result = run_capability(value['capability_id'], None, value['input'], host_context=host)
        self.assertEqual('failed', result['status'])
        self.assertEqual('execution_failed', result['errors'][0]['code'])
        self.assertIsNone(result['output'])
        self.assertEqual(['capability_started', 'capability_finished'], events)
        self.assertEqual([], fixture.double.calls)

    @verifies('scenario.development.flow-execution')
    def test_extracted_review_flow_remains_part_of_review_identity(self):
        from concorde.development import review
        from concorde.development.capability_host import CapabilityHost, Invocation
        fixture = self.fixture()
        run = Invocation('concorde-review', studio_fixtures.CONFIGURATION,
            {'target_id': 'service.transfer', 'task': 'Inspect transfer'},
            CapabilityHost(fixture.root, studio_fixtures.PACKAGE))
        before, _ = review.inputs(run, 'code')
        read_file = review.read_file
        def changed_flow(root, path):
            data = read_file(root, path)
            return data + b'\n# revised scheduling\n' if path == 'src/concorde/harness/batch_flow.py' else data
        with patch.object(review, 'read_file', side_effect=changed_flow):
            after, _ = review.inputs(run, 'code')
        self.assertNotEqual(before['input_digest'], after['input_digest'])
        self.assertEqual(before['revision'], after['revision'])
