"""Concorde-only flow publication follows executable factories without running Agents."""
import ast
import importlib.util
import re
from pathlib import Path
import unittest

from concorde.spec.contracts import SKILL_NAMES, CAPABILITY_NAMES
from concorde.spec.verification import verifies
from concorde.views.docsite_template import template_files
from tests.concorde.support.paths import REPOSITORY_ROOT


class AgentFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('concorde_site_graphs',
            REPOSITORY_ROOT / 'docsite/concorde-only/flows.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.data = cls.module.export()

    @verifies('scenario.views.agent-flows')
    def test_all_public_entries_and_executable_flow_factories_are_accounted_for(self):
        self.assertEqual(set(CAPABILITY_NAMES), set(self.data['capabilities']))
        self.assertEqual(set(CAPABILITY_NAMES), set(self.data['capability_info']))
        public = {name for name, info in self.data['capability_info'].items() if info['public']}
        self.assertEqual(set(SKILL_NAMES), public)
        for capability, graph in self.data['capabilities'].items():
            if capability not in public:
                self.assertIn('execute:prepare_target:initialize_target', graph['nodes'])
                self.assertFalse(any(node.endswith(':discover:decide') for node in graph['nodes']))
                self.assertTrue(all(edge['source'] in graph['nodes'] and edge['target'] in graph['nodes']
                                    for edge in graph['edges']))
                continue
            nodes = set(graph['nodes'])
            self.assertTrue({'__start__', '__end__', 'validate_invocation',
                capability + ':admit_request', capability + ':bind_workspace',
                capability + ':execute:select_capability', capability + ':finalize'} <= nodes)
            self.assertTrue(all(edge['source'] in nodes and edge['target'] in nodes for edge in graph['edges']))
        main = self.data['capabilities']['concorde-main']['nodes']
        self.assertTrue(any(node.endswith(':discover:expand_context') for node in main))
        self.assertTrue(any(node.endswith(':author_module') for node in main))
        self.assertFalse(any(node.endswith(':deliver') for node in main))
        for capability in ('concorde-review', 'concorde-dev-loop', 'concorde-specify-loop'):
            self.assertIn(capability + ':execute:prepare_target:discover:expand_context',
                          self.data['capabilities'][capability]['nodes'])
        self.assertIn('Target admission and discovery', self.data['flows'])
        self.assertNotIn('discover', self.data['flows']['Bound target admission']['nodes'])
        # A newly introduced actual graph factory must be explicitly covered by the page.
        factories = []
        for path in (REPOSITORY_ROOT / 'src/concorde').rglob('*.py'):
            tree = ast.parse(path.read_text())
            if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id == 'StateGraph' for node in ast.walk(tree)):
                factories.append(path.relative_to(REPOSITORY_ROOT).as_posix())
        self.assertEqual(sorted(factories), self.data['factory_sources'])
        self.assertIn('Recursive Agent decisions', self.data['flows'])
        self.assertIn('Component coordination', self.data['flows'])

    @verifies('scenario.views.agent-flows')
    def test_variants_expose_repair_stops_resume_and_missing_code_review(self):
        page = (REPOSITORY_ROOT / 'docsite/concorde-only/page.tsx').read_text()
        explained = set(re.findall(r'^  (\w+): \{title:', page, re.MULTILINE))
        self.assertEqual((set(self.data['loops'][0]['nodes'])
                          | set(self.data['flows']['Spec authoring and review']['nodes']))
                         - {'__start__', '__end__'}, explained)
        for graph in self.data['loops']:
            edges = {(e['source'], e['target']) for e in graph['edges']}
            self.assertIn(('ready', '__end__'), edges)
            self.assertIn(('validate', '__end__'), edges)
            if graph['label'] == 'No local code bindings':
                self.assertNotIn('review_code', graph['nodes'])
                self.assertIn(('validate', 'ready'), edges)
            else:
                self.assertIn(('review_code', 'tasks'), edges)
            if graph['label'] == 'Resume validation':
                self.assertIn(('specify_loop', 'validate'), edges)
                self.assertIn('tasks', graph['nodes'])  # retained for repair
            if graph['label'] == 'Skip authoring':
                self.assertNotIn('specify', graph['nodes'])
        self.assertEqual(self.data, self.module.export())

    @verifies('scenario.views.agent-flows')
    def test_consumer_inventory_has_no_flow_assets_or_python_dependency(self):
        files = template_files(REPOSITORY_ROOT)
        self.assertFalse(any('/concorde-only/' in path for path in files))
        self.assertFalse(any(path.endswith('graphs.py') for path in files))
        self.assertFalse(any(path.endswith('flows.py') for path in files))


if __name__ == '__main__':
    unittest.main()
