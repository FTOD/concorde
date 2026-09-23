"""Graph Specs are node, edge and state diagrams kept equal to the compiled LangGraph Graphs."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness.graph_specs import (
    GraphSpec,
    Reading,
    bound_graph_specs,
    compare,
    functional_api_imports,
    graph_spec_findings,
    graph_specs,
    link_problems,
    part_problems,
)
from concorde.operations.graph_catalog import catalog, topology
from concorde.spec.repository import SpecRepository
from concorde.spec.validation import flowchart_model
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

DIAGRAM = """flowchart TB
    %% graph: batch_graph
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


STATE = "**State.** `index` (the next item), `output`, `stop`.\n\n"
CODE = "```python\n# a comment, not a heading\nitems = ()\n```\n\n"
NODES = """**Nodes.**

| Node | Executes | in | out |
| --- | --- | --- | --- |
| `select_item` | Deterministic: stops when no item remains. | index, items | stop |
| `execute_item` | The item operation. | item | output, index, stop |

"""
EDGES = "**Edges.** Both nodes route on `stop` through conditional edges.\n\n"


def spec(text: str) -> GraphSpec:
    nodes, edges = flowchart_model(text)
    return GraphSpec("specs/x.md", "batch_graph", nodes, tuple(edges))


def section(*parts: str, role: str = "implementation") -> GraphSpec:
    """The one bound Graph Spec of a document whose Graph section holds ``parts``."""
    body = (
        "## Earlier section\n\n**State.** Not this Graph's.\n\n"
        "#### Sequential work items Graph (`batch_graph`)\n\n"
        + "".join(parts)
        + "```mermaid\n"
        + DIAGRAM
        + "```\n\n## Later section\n"
    )
    (found,) = bound_graph_specs("specs/x.md", body, role)
    return found


class GraphSpecTests(unittest.TestCase):
    @verifies("scenario.execution.graph-spec-match")
    def test_every_compiled_graph_has_one_matching_spec_in_this_repository(self):
        repository = SpecRepository(REPOSITORY_ROOT, REPOSITORY_ROOT)
        with patch("concorde.harness.context.resolve_context") as resolve:
            findings = graph_spec_findings(repository)
            resolve.assert_not_called()
        self.assertEqual((), findings, [finding.message for finding in findings])
        bound = {item.graph for item in graph_specs(repository)}
        self.assertEqual(set(catalog()), bound)

    @verifies("scenario.execution.graph-spec-match")
    def test_catalog_compiles_every_graph_without_a_repository_or_agent(self):
        with patch("concorde.harness.invocation.SpecRepository") as bound:
            for name, build in catalog().items():
                with self.subTest(graph=name):
                    shape = topology(build())
                    self.assertIn("__start__", shape["nodes"])
                    self.assertIn("__end__", shape["nodes"])
                    self.assertTrue(shape["edges"])
            bound.assert_not_called()

    @verifies("scenario.execution.graph-spec-match")
    def test_comparison_reports_missing_nodes_edges_conditions_and_state(self):
        compiled = topology(
            (
                lambda: __import__(
                    "tests.concorde.support.sample_graph",
                    fromlist=["build_batch_graph"],
                ).build_batch_graph(
                    lambda name: lambda state: {},
                    name="batch_graph",
                    item_node="execute_item",
                )
            )()
        )
        self.assertEqual([], compare(spec(DIAGRAM), compiled))
        extra_node = (
            DIAGRAM + '    phantom["phantom<br/>in: nothing<br/>out: nothing"]\n'
        )
        self.assertTrue(
            any(
                "nodes differ" in problem
                for problem in compare(spec(extra_node), compiled)
            )
        )
        renamed = DIAGRAM.replace("execute_item", "run_item")
        self.assertTrue(
            any(
                "nodes differ" in problem and "run_item" in problem
                for problem in compare(spec(renamed), compiled)
            )
        )
        extra_edge = DIAGRAM + "    __start__ -->|shortcut| execute_item\n"
        self.assertTrue(
            any(
                "edges differ" in problem
                for problem in compare(spec(extra_edge), compiled)
            )
        )
        unlabeled = DIAGRAM.replace(
            "select_item -->|items remain| execute_item", "select_item --> execute_item"
        )
        self.assertTrue(
            any(
                "needs its routing condition" in problem
                for problem in compare(spec(unlabeled), compiled)
            )
        )
        labeled_single = DIAGRAM.replace(
            "__start__ --> select_item", "__start__ -->|always| select_item"
        )
        self.assertTrue(
            any(
                "only transition" in problem
                for problem in compare(spec(labeled_single), compiled)
            )
        )
        no_state = DIAGRAM.replace(
            'select_item["select_item<br/>in: index, items<br/>out: stop"]',
            'select_item["select_item"]',
        )
        self.assertTrue(
            any(
                "'in:' and 'out:'" in problem
                for problem in compare(spec(no_state), compiled)
            )
        )
        misnamed = DIAGRAM.replace(
            'select_item["select_item<br/>', 'select_item["Select item<br/>'
        )
        self.assertTrue(
            any(
                "must start with its identifier" in problem
                for problem in compare(spec(misnamed), compiled)
            )
        )

    @verifies("scenario.execution.graph-spec-match")
    def test_parts_require_state_nodes_and_edges_in_order(self):
        compiled = topology(
            (
                lambda: __import__(
                    "tests.concorde.support.sample_graph",
                    fromlist=["build_batch_graph"],
                ).build_batch_graph(
                    lambda name: lambda state: {},
                    name="batch_graph",
                    item_node="execute_item",
                )
            )()
        )

        def problems(*parts: str, role: str = "implementation") -> list[str]:
            return part_problems(section(*parts, role=role), compiled)

        # A '#' line inside fenced code neither ends the section nor hides its State part.
        self.assertEqual([], problems(STATE, CODE, NODES, EDGES))
        self.assertIn(
            "has no **Edges.** part before its diagram", problems(STATE, NODES)
        )
        self.assertIn(
            "has no **State.** part before its diagram", problems(NODES, EDGES)
        )
        self.assertIn(
            "must state its State, Nodes and Edges parts in that order",
            problems(NODES, STATE, EDGES),
        )
        self.assertIn(
            "states its **Edges.** part more than once",
            problems(STATE, NODES, EDGES, EDGES),
        )
        self.assertIn(
            "**State.** part names no channel or record",
            problems("**State.**\n\n", NODES, EDGES),
        )
        self.assertIn(
            "**Edges.** part does not say how the next node is chosen",
            problems(STATE, NODES, "**Edges.**\n\n"),
        )
        self.assertIn(
            "is in a module document, not an implementation-role document",
            problems(STATE, NODES, EDGES, role="module"),
        )

    @verifies("scenario.execution.graph-spec-match")
    def test_nodes_table_names_every_compiled_node_with_its_diagram_state(self):
        compiled = topology(
            (
                lambda: __import__(
                    "tests.concorde.support.sample_graph",
                    fromlist=["build_batch_graph"],
                ).build_batch_graph(
                    lambda name: lambda state: {},
                    name="batch_graph",
                    item_node="execute_item",
                )
            )()
        )

        def problems(nodes: str) -> list[str]:
            return part_problems(section(STATE, nodes, EDGES), compiled)

        self.assertEqual([], problems(NODES))
        missing = NODES.replace(
            "| `execute_item` | The item operation. | item | output, index, stop |\n",
            "",
        )
        self.assertTrue(
            any(
                "Nodes table differs" in problem and "execute_item" in problem
                for problem in problems(missing)
            ),
            problems(missing),
        )
        extra = NODES.replace(
            "| `select_item` |",
            "| `phantom` | Nothing. | nothing | nothing |\n| `select_item` |",
        )
        self.assertTrue(
            any("table-only ['phantom']" in problem for problem in problems(extra))
        )
        drifted = NODES.replace("| index, items | stop |", "| index | stop |")
        self.assertTrue(
            any(
                problem.startswith("Nodes row select_item states in 'index'")
                for problem in problems(drifted)
            ),
            problems(drifted),
        )
        unquoted = NODES.replace("| `select_item` |", "| select_item |")
        self.assertIn(
            "Nodes row 'select_item' must name its node in backticks",
            problems(unquoted),
        )
        self.assertIn(
            "needs a 'Node | Executes | in | out' table between its Nodes and Edges parts",
            problems("**Nodes.** Two nodes.\n\n"),
        )

    @verifies("scenario.execution.graph-spec-match")
    def test_owner_reading_links_the_exact_graph_spec(self):
        body = (
            "#### Sequential work items Graph (`batch_graph`) {#host-batch}\n\n"
            + STATE
            + NODES
            + EDGES
            + "```mermaid\n"
            + DIAGRAM
            + "```\n"
        )
        (found,) = bound_graph_specs(
            "specs/h/execution-reference.md", body, "implementation", "module.h"
        )
        linking = Reading(
            "specs/h/host.md",
            "module.h",
            "See [it](execution-reference.md#host-batch).",
        )
        self.assertEqual([], link_problems(found, [linking]))
        nested = Reading(
            "specs/h/topics/guide.md",
            "module.h",
            "See [it](../execution-reference.md#host-batch).",
        )
        self.assertEqual([], link_problems(found, [nested]))
        unlinked = [
            "is not linked as #host-batch from any module-role document of module.h"
        ]
        foreign = Reading(
            "specs/other/module.md",
            "module.other",
            "See [it](../h/execution-reference.md#host-batch).",
        )
        self.assertEqual(unlinked, link_problems(found, [foreign]))
        section_only = Reading(
            "specs/h/host.md", "module.h", "See [it](execution-reference.md#host)."
        )
        self.assertEqual(unlinked, link_problems(found, [section_only]))
        self.assertEqual(
            [
                "heading needs an explicit {#anchor} that its owner's reading can link to"
            ],
            link_problems(section(STATE, NODES, EDGES), [linking]),
        )

    @verifies("scenario.execution.graph-spec-match")
    def test_unknown_duplicate_and_missing_bindings_are_findings(self):
        repository = SpecRepository(REPOSITORY_ROOT, REPOSITORY_ROOT)
        limited = {
            "batch_graph": (
                lambda: __import__(
                    "tests.concorde.support.sample_graph",
                    fromlist=["build_batch_graph"],
                ).build_batch_graph(
                    lambda name: lambda state: {},
                    name="batch_graph",
                    item_node="execute_item",
                )
            )
        }
        findings = graph_spec_findings(repository, limited)
        messages = [finding.message for finding in findings]
        self.assertTrue(
            any(
                "binds unknown Graph terminal_agent_operation" in message
                for message in messages
            ),
            messages,
        )
        self.assertTrue(
            any("batch_graph has no Graph Spec" in message for message in messages)
        )
        none = graph_spec_findings(
            repository, {**limited, "phantom_graph": limited["batch_graph"]}
        )
        self.assertTrue(
            any(
                "compiled Graph phantom_graph has no Graph Spec diagram"
                in finding.message
                for finding in none
            )
        )
        self.assertTrue(
            (
                Path(REPOSITORY_ROOT) / "scripts/development/check-graph-specs.py"
            ).is_file()
        )

    @verifies("scenario.execution.functional-api-refused")
    def test_a_graph_outside_the_graph_api_is_a_finding(self):
        from langgraph.func import entrypoint

        @entrypoint()
        def functional_graph(state: dict) -> dict:
            return state

        repository = SpecRepository(REPOSITORY_ROOT, REPOSITORY_ROOT)
        findings = graph_spec_findings(
            repository, {**catalog(), "batch_graph": lambda: functional_graph}
        )
        self.assertEqual(
            [
                (
                    "CONCORDE-GRAPH-004",
                    "compiled Graph batch_graph is a Pregel, not a StateGraph of the Graph API",
                ),
                (
                    "CONCORDE-GRAPH-001",
                    "compiled Graph batch_graph has no Graph Spec diagram",
                ),
            ],
            [(finding.rule_id, finding.message) for finding in findings],
        )

    @verifies("scenario.execution.functional-api-refused")
    def test_functional_api_imports_are_found_by_parsing_not_running(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src" / "pkg" / "__pycache__").mkdir(parents=True)
            (root / "scripts").mkdir()
            (root / "src" / "pkg" / "a.py").write_text(
                "import os\nfrom langgraph.func import entrypoint, task\n"
            )
            (root / "src" / "pkg" / "b.py").write_text(
                "import langgraph.func as func\n"
            )
            (root / "src" / "pkg" / "broken.py").write_text("def (\n")
            (root / "src" / "pkg" / "ok.py").write_text(
                "from langgraph.graph import StateGraph\nNAME = 'langgraph.func'\nraise SystemExit(3)\n"
            )
            (root / "src" / "pkg" / "__pycache__" / "skip.py").write_text(
                "from langgraph.func import task\n"
            )
            (root / "scripts" / "c.py").write_text("from langgraph import func\n")
            (root / "operations").mkdir()
            (root / "operations" / "d.py").write_text(
                "from langgraph.func import task\n"
            )
            self.assertEqual(
                (
                    ("src/pkg/a.py", 2, "from langgraph.func import entrypoint, task"),
                    ("src/pkg/b.py", 1, "import langgraph.func as func"),
                    ("src/pkg/broken.py", 1, "file cannot be parsed"),
                    ("scripts/c.py", 1, "from langgraph import func"),
                    ("operations/d.py", 1, "from langgraph.func import task"),
                ),
                functional_api_imports(root),
            )
        self.assertEqual((), functional_api_imports(REPOSITORY_ROOT))


if __name__ == "__main__":
    unittest.main()
