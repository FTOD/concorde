"""Flow Specs are node, edge and state diagrams kept equal to the compiled LangGraph Flows."""
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.development.flow_catalog import catalog, topology
from concorde.development.flow_specs import FlowSpec, compare, flow_spec_findings, flow_specs
from concorde.spec.repository import SpecRepository
from concorde.spec.validation import flowchart_model
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


DIAGRAM = """flowchart TB
    %% flow: batch_flow
    __start__["start"]
    select_item["select_item<br/>in: index, items<br/>out: stop"]
    execute_item["execute_item<br/>in: item<br/>out: output, index, stop"]
    __end__["end"]
    __start__ --> select_item
    select_item -->|items remain| execute_item
    select_item -->|no item left| __end__
    execute_item -->|item returned None| select_item
    execute_item -->|item returned a result| __end__
"""


def spec(text: str) -> FlowSpec:
    nodes, edges = flowchart_model(text)
    return FlowSpec("specs/x.md", "batch_flow", nodes, tuple(edges))


class FlowSpecTests(unittest.TestCase):
    @verifies("scenario.development.flow-specs")
    def test_every_compiled_flow_has_one_matching_spec_in_this_repository(self):
        repository = SpecRepository(REPOSITORY_ROOT, REPOSITORY_ROOT)
        with patch("concorde.harness.context.resolve_context") as resolve:
            findings = flow_spec_findings(repository)
            resolve.assert_not_called()
        self.assertEqual((), findings, [finding.message for finding in findings])
        bound = {item.flow for item in flow_specs(repository)}
        self.assertEqual(set(catalog()), bound)

    @verifies("scenario.development.flow-specs")
    def test_catalog_compiles_every_flow_without_a_repository_or_agent(self):
        with patch("concorde.development.capability_host.SpecRepository") as repository:
            for name, build in catalog().items():
                with self.subTest(flow=name):
                    shape = topology(build())
                    self.assertIn("__start__", shape["nodes"])
                    self.assertIn("__end__", shape["nodes"])
                    self.assertTrue(shape["edges"])
            repository.assert_not_called()

    @verifies("scenario.development.flow-specs")
    def test_comparison_reports_missing_nodes_edges_conditions_and_state(self):
        compiled = topology(catalog()["batch_flow"]())
        self.assertEqual([], compare(spec(DIAGRAM), compiled))
        extra_node = DIAGRAM + '    phantom["phantom<br/>in: nothing<br/>out: nothing"]\n'
        self.assertTrue(any("nodes differ" in problem for problem in compare(spec(extra_node), compiled)))
        renamed = DIAGRAM.replace("execute_item", "run_item")
        self.assertTrue(any("nodes differ" in problem and "run_item" in problem
                            for problem in compare(spec(renamed), compiled)))
        extra_edge = DIAGRAM + "    __start__ -->|shortcut| execute_item\n"
        self.assertTrue(any("edges differ" in problem for problem in compare(spec(extra_edge), compiled)))
        unlabeled = DIAGRAM.replace("select_item -->|items remain| execute_item", "select_item --> execute_item")
        self.assertTrue(any("needs its routing condition" in problem for problem in compare(spec(unlabeled), compiled)))
        labeled_single = DIAGRAM.replace("__start__ --> select_item", "__start__ -->|always| select_item")
        self.assertTrue(any("only transition" in problem for problem in compare(spec(labeled_single), compiled)))
        no_state = DIAGRAM.replace('select_item["select_item<br/>in: index, items<br/>out: stop"]', 'select_item["select_item"]')
        self.assertTrue(any("'in:' and 'out:'" in problem for problem in compare(spec(no_state), compiled)))
        misnamed = DIAGRAM.replace('select_item["select_item<br/>', 'select_item["Select item<br/>')
        self.assertTrue(any("must start with its identifier" in problem for problem in compare(spec(misnamed), compiled)))

    @verifies("scenario.development.flow-specs")
    def test_unknown_duplicate_and_missing_bindings_are_findings(self):
        repository = SpecRepository(REPOSITORY_ROOT, REPOSITORY_ROOT)
        limited = {"batch_flow": catalog()["batch_flow"]}
        findings = flow_spec_findings(repository, limited)
        messages = [finding.message for finding in findings]
        self.assertTrue(any("binds unknown Flow development_flow" in message for message in messages), messages)
        self.assertFalse(any("has no Flow Spec" in message for message in messages))
        none = flow_spec_findings(repository, {**limited, "phantom_flow": limited["batch_flow"]})
        self.assertTrue(any("compiled Flow phantom_flow has no Flow Spec diagram" in finding.message for finding in none))
        self.assertTrue((Path(REPOSITORY_ROOT) / "scripts/development/check-flow-specs.py").is_file())


if __name__ == "__main__":
    unittest.main()
