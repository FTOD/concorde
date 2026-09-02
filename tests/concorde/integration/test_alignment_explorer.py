from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.alignment import explore_alignment  # noqa: E402
from concorde.diagnostics import canonical_json, tool_envelope  # noqa: E402


ALIGNMENT_FIXTURES = REPOSITORY_ROOT / "tests/concorde/fixtures/interfaces/alignment"
REVISION = "0123456789abcdef0123456789abcdef01234567"


def bytes_by_path(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


class AlignmentExplorerIntegrationTests(unittest.TestCase):
    def copy_project(self, temporary: str) -> Path:
        root = Path(temporary) / "project"
        shutil.copytree(CONTEXT_PROJECT, root)
        return root

    def write_inputs(
        self,
        root: Path,
        *,
        graph_mutation=None,
        claim_mutation=None,
        sidecar_revision: str = REVISION,
    ) -> tuple[str, str]:
        evidence = root / "evidence"
        evidence.mkdir()
        graph = json.loads((ALIGNMENT_FIXTURES / "knowledge-graph.example.json").read_text())
        if graph_mutation:
            graph_mutation(graph)
        graph_path = evidence / "graph.json"
        graph_path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        alignment = json.loads((ALIGNMENT_FIXTURES / "alignment-input.example.json").read_text())
        alignment["implementation_revision"] = sidecar_revision
        alignment["records"][0]["subject_id"] = "feature.example.deliver"
        if claim_mutation:
            claim_mutation(alignment["records"][0])
        alignment_path = evidence / "alignment.json"
        alignment_path.write_text(json.dumps(alignment, indent=2) + "\n", encoding="utf-8")
        return "evidence/graph.json", "evidence/alignment.json"

    def test_specification_only_feature_is_bounded_unknown_deterministic_and_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_project(temporary)
            before = bytes_by_path(root)
            first = explore_alignment(root, "feature.example.deliver")
            second = explore_alignment(root, "feature.example.deliver")
            self.assertEqual(first.status, "success", first.findings)
            self.assertEqual(first.tool, "explore")
            self.assertEqual(first.target, "feature.example.deliver")
            self.assertTrue(any(item.rule_id == "CONCORDE-ALIGN-005" for item in first.findings))
            self.assertEqual(
                canonical_json(tool_envelope(first)),
                canonical_json(tool_envelope(second)),
            )
            result = first.result
            self.assertEqual(result["alignment_schema_version"], 1)
            self.assertEqual(result["source_profile"], 7)
            self.assertEqual(result["target"], "feature.example.deliver")
            self.assertEqual(result["provenance"]["freshness"], "absent")
            self.assertIsNone(result["implementation"]["project"])
            self.assertEqual(result["implementation"]["nodes"], [])
            self.assertTrue(result["specification"]["subjects"])
            records = result["alignment"]["records"]
            self.assertEqual(len(records), len(result["specification"]["subjects"]))
            self.assertEqual({record["status"] for record in records}, {"unknown"})
            self.assertEqual(result["alignment"]["summary"]["unknown"], len(records))
            self.assertEqual(before, bytes_by_path(root))

    def test_module_target_includes_immediate_child_but_not_child_internals(self):
        result = explore_alignment(CONTEXT_PROJECT, "module.example")
        self.assertEqual(result.status, "success", result.findings)
        subjects = {item["id"] for item in result.result["specification"]["subjects"]}
        self.assertIn("module.example", subjects)
        self.assertIn("module.example.api", subjects)
        self.assertIn("feature.example.deliver", subjects)
        self.assertIn("entity.example.runtime", subjects)
        self.assertNotIn("entity.example.api.handler", subjects)
        self.assertNotIn("module.example.api.store", subjects)

    def test_default_target_is_root_module_and_unknown_target_is_invalid(self):
        default = explore_alignment(CONTEXT_PROJECT)
        self.assertEqual(default.status, "success", default.findings)
        self.assertEqual(default.target, "module.example")
        invalid = explore_alignment(CONTEXT_PROJECT, "entity.example.missing")
        self.assertEqual(invalid.status, "invalid")
        self.assertTrue(any(item.rule_id == "CONCORDE-ALIGN-001" for item in invalid.findings))

    def test_result_artifacts_are_safe_real_sources_only(self):
        result = explore_alignment(CONTEXT_PROJECT, "feature.example.deliver")
        self.assertEqual(result.status, "success", result.findings)
        for relative in result.artifacts:
            path = CONTEXT_PROJECT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertFalse(path.is_symlink(), relative)
            self.assertNotIn("..", Path(relative).parts)

    def test_current_explicit_executable_evidence_verifies_only_its_subject(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_project(temporary)
            graph_path, alignment_path = self.write_inputs(root)
            before = bytes_by_path(root)
            result = explore_alignment(
                root,
                "feature.example.deliver",
                graph_path=graph_path,
                alignment_path=alignment_path,
                expected_revision=REVISION,
            )
            self.assertEqual(result.status, "success", result.findings)
            self.assertEqual(result.result["provenance"]["freshness"], "current")
            records = {item["subject_id"]: item for item in result.result["alignment"]["records"]}
            self.assertEqual(records["feature.example.deliver"]["status"], "verified")
            self.assertEqual(
                {item["status"] for key, item in records.items() if key != "feature.example.deliver"},
                {"unknown"},
            )
            nodes = {item["id"]: item for item in result.result["implementation"]["nodes"]}
            self.assertEqual(nodes["function:src/concorde/alignment.py:explore_alignment"]["type"], "function")
            edge = next(item for item in result.result["implementation"]["edges"] if item["type"] == "tested_by")
            self.assertEqual(edge["direction"], "forward")
            self.assertEqual(before, bytes_by_path(root))

    def test_stale_or_unassessed_revision_reduces_every_claim_to_unknown(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_project(temporary)
            graph_path, alignment_path = self.write_inputs(root)
            stale = explore_alignment(
                root, "feature.example.deliver",
                graph_path=graph_path, alignment_path=alignment_path,
                expected_revision="f" * 40,
            )
            self.assertEqual(stale.status, "success", stale.findings)
            self.assertEqual(stale.result["provenance"]["freshness"], "stale")
            self.assertEqual({item["status"] for item in stale.result["alignment"]["records"]}, {"unknown"})
            self.assertTrue(any(item.rule_id == "CONCORDE-ALIGN-008" for item in stale.findings))

            unknown = explore_alignment(
                root, "feature.example.deliver",
                graph_path=graph_path, alignment_path=alignment_path,
            )
            self.assertEqual(unknown.status, "success", unknown.findings)
            self.assertEqual(unknown.result["provenance"]["freshness"], "unknown")
            self.assertEqual({item["status"] for item in unknown.result["alignment"]["records"]}, {"unknown"})

    def test_sidecar_revision_mismatch_is_stale_not_disagreement(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_project(temporary)
            graph_path, alignment_path = self.write_inputs(root, sidecar_revision="e" * 40)
            result = explore_alignment(
                root, "feature.example.deliver",
                graph_path=graph_path, alignment_path=alignment_path,
                expected_revision=REVISION,
            )
            self.assertEqual(result.status, "success", result.findings)
            self.assertEqual(result.result["provenance"]["freshness"], "stale")
            self.assertNotIn("disagrees", {item["status"] for item in result.result["alignment"]["records"]})

    def test_candidate_only_cannot_verify_and_explicit_finding_can_disagree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_project(temporary)

            def candidate(claim):
                claim["basis"] = "candidate-only"

            graph_path, alignment_path = self.write_inputs(root, claim_mutation=candidate)
            result = explore_alignment(
                root, "feature.example.deliver", graph_path=graph_path,
                alignment_path=alignment_path, expected_revision=REVISION,
            )
            selected = next(item for item in result.result["alignment"]["records"] if item["subject_id"] == "feature.example.deliver")
            self.assertEqual(selected["requested_status"], "verified")
            self.assertEqual(selected["status"], "unknown")

        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_project(temporary)

            def disagreement(claim):
                claim["status"] = "disagrees"
                claim["basis"] = "deterministic-finding"
                claim["evidence_node_ids"] = []
                claim["finding_ids"] = ["CONCORDE-ALIGN-EXAMPLE"]

            graph_path, alignment_path = self.write_inputs(root, claim_mutation=disagreement)
            result = explore_alignment(
                root, "feature.example.deliver", graph_path=graph_path,
                alignment_path=alignment_path, expected_revision=REVISION,
            )
            selected = next(item for item in result.result["alignment"]["records"] if item["subject_id"] == "feature.example.deliver")
            self.assertEqual(selected["status"], "disagrees")

    def test_invalid_graph_or_alignment_is_invalid_and_keeps_unknown_projection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_project(temporary)

            def unsupported(graph):
                graph["nodes"][0]["type"] = "script"

            graph_path, alignment_path = self.write_inputs(root, graph_mutation=unsupported)
            result = explore_alignment(
                root, "feature.example.deliver", graph_path=graph_path,
                alignment_path=alignment_path, expected_revision=REVISION,
            )
            self.assertEqual(result.status, "invalid")
            self.assertEqual({item["status"] for item in result.result["alignment"]["records"]}, {"unknown"})
            self.assertTrue(any(item.rule_id == "CONCORDE-ALIGN-003" for item in result.findings))

        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_project(temporary)

            def missing_node(claim):
                claim["implementation_node_ids"] = ["file:missing.py"]

            graph_path, alignment_path = self.write_inputs(root, claim_mutation=missing_node)
            result = explore_alignment(
                root, "feature.example.deliver", graph_path=graph_path,
                alignment_path=alignment_path, expected_revision=REVISION,
            )
            self.assertEqual(result.status, "invalid")
            self.assertEqual({item["status"] for item in result.result["alignment"]["records"]}, {"unknown"})
            self.assertTrue(any(item.rule_id == "CONCORDE-ALIGN-009" for item in result.findings))

    def test_graph_without_sidecar_is_unknown_and_sidecar_without_graph_is_invalid(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_project(temporary)
            graph_path, alignment_path = self.write_inputs(root)
            graph_only = explore_alignment(
                root, "feature.example.deliver", graph_path=graph_path, expected_revision=REVISION,
            )
            self.assertEqual(graph_only.status, "success", graph_only.findings)
            self.assertEqual({item["status"] for item in graph_only.result["alignment"]["records"]}, {"unknown"})
            self.assertTrue(any(item.rule_id == "CONCORDE-ALIGN-006" for item in graph_only.findings))

            sidecar_only = explore_alignment(
                root, "feature.example.deliver", alignment_path=alignment_path, expected_revision=REVISION,
            )
            self.assertEqual(sidecar_only.status, "invalid")
            self.assertTrue(any(item.rule_id == "CONCORDE-ALIGN-006" for item in sidecar_only.findings))

    def test_query_and_effective_status_filter_bound_both_graphs_with_one_hop(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_project(temporary)

            def add_isolated(graph):
                graph["nodes"].append({
                    "id": "file:src/unmapped.py",
                    "type": "file",
                    "name": "unmapped.py",
                    "filePath": "src/unmapped.py",
                    "summary": "An unrelated isolated implementation node.",
                    "tags": ["unmapped"],
                    "complexity": "simple",
                })

            graph_path, alignment_path = self.write_inputs(root, graph_mutation=add_isolated)
            result = explore_alignment(
                root,
                "feature.example.deliver",
                graph_path=graph_path,
                alignment_path=alignment_path,
                expected_revision=REVISION,
                query="DeLiVeR",
                statuses=("verified",),
            )
            self.assertEqual(result.status, "success", result.findings)
            self.assertEqual(
                [item["id"] for item in result.result["specification"]["subjects"]],
                ["feature.example.deliver"],
            )
            self.assertEqual(
                [item["subject_id"] for item in result.result["alignment"]["records"]],
                ["feature.example.deliver"],
            )
            implementation = result.result["implementation"]
            self.assertEqual(implementation["counts"], {
                "total_nodes": 4,
                "returned_nodes": 3,
                "total_edges": 2,
                "returned_edges": 2,
            })
            self.assertNotIn("file:src/unmapped.py", {item["id"] for item in implementation["nodes"]})
            self.assertEqual(implementation["layers"][0]["id"], "layer:alignment")
            self.assertEqual(implementation["tour"][0]["order"], 1)

    def test_status_filter_uses_effective_not_requested_state(self):
        unknown = explore_alignment(CONTEXT_PROJECT, "feature.example.deliver", statuses=("unknown",))
        self.assertTrue(unknown.result["specification"]["subjects"])
        self.assertEqual({item["status"] for item in unknown.result["alignment"]["records"]}, {"unknown"})
        verified = explore_alignment(CONTEXT_PROJECT, "feature.example.deliver", statuses=("verified",))
        self.assertEqual(verified.result["specification"]["subjects"], [])
        self.assertEqual(verified.result["alignment"]["records"], [])
        self.assertEqual(verified.result["alignment"]["summary"], {
            "unknown": 0, "partial": 0, "verified": 0, "disagrees": 0,
        })

    def test_query_cannot_escape_specification_bound_and_empty_result_is_valid(self):
        hidden = explore_alignment(CONTEXT_PROJECT, "module.example", query="api.handler")
        self.assertEqual(hidden.status, "success", hidden.findings)
        self.assertEqual(hidden.result["specification"]["subjects"], [])
        self.assertNotIn("entity.example.api.handler", repr(hidden.result))

        empty = explore_alignment(CONTEXT_PROJECT, "feature.example.deliver", query="never-present-zzzz")
        self.assertEqual(empty.status, "success", empty.findings)
        self.assertEqual(empty.result["specification"]["subjects"], [])
        self.assertEqual(empty.result["alignment"]["records"], [])

    def test_graph_text_query_returns_match_plus_exactly_one_hop_and_filters_views(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_project(temporary)
            graph_path, _ = self.write_inputs(root)
            result = explore_alignment(
                root,
                "feature.example.deliver",
                graph_path=graph_path,
                expected_revision=REVISION,
                query="strict evidence-qualified",
            )
            self.assertEqual(result.status, "success", result.findings)
            implementation = result.result["implementation"]
            self.assertEqual(
                {item["id"] for item in implementation["nodes"]},
                {
                    "file:src/concorde/alignment.py",
                    "function:src/concorde/alignment.py:explore_alignment",
                },
            )
            self.assertEqual([item["type"] for item in implementation["edges"]], ["contains"])
            self.assertEqual(
                implementation["layers"][0]["nodeIds"],
                [
                    "file:src/concorde/alignment.py",
                    "function:src/concorde/alignment.py:explore_alignment",
                ],
            )
            self.assertEqual(
                implementation["tour"][0]["nodeIds"],
                ["function:src/concorde/alignment.py:explore_alignment"],
            )

    def test_filtered_result_order_and_json_are_byte_equivalent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_project(temporary)
            graph_path, alignment_path = self.write_inputs(root)
            options = {
                "graph_path": graph_path,
                "alignment_path": alignment_path,
                "expected_revision": REVISION,
                "statuses": ("unknown", "verified"),
            }
            first = explore_alignment(root, "feature.example.deliver", **options)
            second = explore_alignment(root, "feature.example.deliver", **options)
            self.assertEqual(canonical_json(tool_envelope(first)), canonical_json(tool_envelope(second)))
            subjects = [item["id"] for item in first.result["specification"]["subjects"]]
            records = [item["subject_id"] for item in first.result["alignment"]["records"]]
            nodes = [item["id"] for item in first.result["implementation"]["nodes"]]
            self.assertEqual(subjects, sorted(subjects))
            self.assertEqual(records, sorted(records))
            self.assertEqual(nodes, sorted(nodes))


if __name__ == "__main__":
    unittest.main()
