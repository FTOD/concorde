from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.understanding.alignment import (  # noqa: E402
    ALIGNMENT_BASES,
    ALIGNMENT_SCHEMA_VERSION,
    ALIGNMENT_STATUSES,
    UA_EDGE_TYPES,
    UA_NODE_TYPES,
    load_knowledge_graph,
    project_specification,
    qualify_alignment,
    validate_alignment_input,
    validate_knowledge_graph,
)
from concorde.understanding.repository import ProjectRepository  # noqa: E402


FIXTURES = REPOSITORY_ROOT / "tests/concorde/fixtures/interfaces/alignment"


def read_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class AlignmentUnitTests(unittest.TestCase):
    def test_pinned_vocabulary_and_local_contract_versions_are_exact(self):
        self.assertEqual(ALIGNMENT_SCHEMA_VERSION, 1)
        self.assertEqual(len(UA_NODE_TYPES), 27)
        self.assertEqual(len(UA_EDGE_TYPES), 38)
        self.assertEqual(ALIGNMENT_STATUSES, frozenset({"unknown", "partial", "verified", "disagrees"}))
        self.assertEqual(
            ALIGNMENT_BASES,
            frozenset({
                "stable-id", "source-path", "contract", "executable-evidence",
                "deterministic-finding", "candidate-only",
            }),
        )
        self.assertIn("componentSet", UA_NODE_TYPES)
        self.assertIn("uses_token", UA_EDGE_TYPES)

    def test_valid_graph_is_preserved_and_invalid_shapes_are_rejected(self):
        graph = read_json("knowledge-graph.example.json")
        validated, findings = validate_knowledge_graph(graph, "graph.json")
        self.assertEqual(findings, ())
        self.assertEqual(validated, graph)

        mutations = []
        unsupported = copy.deepcopy(graph)
        unsupported["nodes"][0]["type"] = "script"
        mutations.append(unsupported)
        dangling = copy.deepcopy(graph)
        dangling["edges"][0]["target"] = "file:missing.py"
        mutations.append(dangling)
        duplicate = copy.deepcopy(graph)
        duplicate["nodes"].append(copy.deepcopy(graph["nodes"][0]))
        mutations.append(duplicate)
        invalid_weight = copy.deepcopy(graph)
        invalid_weight["edges"][0]["weight"] = True
        mutations.append(invalid_weight)
        missing_revision = copy.deepcopy(graph)
        missing_revision["project"]["gitCommitHash"] = ""
        mutations.append(missing_revision)
        invalid_collection = copy.deepcopy(graph)
        invalid_collection["layers"] = None
        mutations.append(invalid_collection)

        for value in mutations:
            with self.subTest(value=value):
                validated, findings = validate_knowledge_graph(value, "graph.json")
                self.assertIsNone(validated)
                self.assertTrue(findings)
                self.assertTrue(all(item.rule_id.startswith("CONCORDE-ALIGN-") for item in findings))

    def test_layer_and_tour_references_must_resolve(self):
        for collection in ("layers", "tour"):
            graph = read_json("knowledge-graph.example.json")
            graph[collection][0]["nodeIds"].append("file:missing.py")
            with self.subTest(collection=collection):
                validated, findings = validate_knowledge_graph(graph, "graph.json")
                self.assertIsNone(validated)
                self.assertTrue(any("does not resolve" in item.message for item in findings))

    def test_alignment_input_resolves_subjects_nodes_and_unique_claims(self):
        graph = read_json("knowledge-graph.example.json")
        node_ids = {node["id"] for node in graph["nodes"]}
        value = read_json("alignment-input.example.json")
        records, findings = validate_alignment_input(
            value,
            {"feature.understanding.explore-alignment"},
            node_ids,
            "alignment.json",
        )
        self.assertEqual(findings, ())
        self.assertEqual(set(records), {"feature.understanding.explore-alignment"})

        cases = []
        duplicate = copy.deepcopy(value)
        duplicate["records"].append(copy.deepcopy(value["records"][0]))
        cases.append(duplicate)
        unknown_subject = copy.deepcopy(value)
        unknown_subject["records"][0]["subject_id"] = "feature.missing"
        cases.append(unknown_subject)
        unknown_node = copy.deepcopy(value)
        unknown_node["records"][0]["implementation_node_ids"] = ["file:missing.py"]
        cases.append(unknown_node)
        invalid_status = copy.deepcopy(value)
        invalid_status["records"][0]["status"] = "implicit"
        cases.append(invalid_status)
        extra_field = copy.deepcopy(value)
        extra_field["records"][0]["confidence"] = 0.9
        cases.append(extra_field)

        for invalid in cases:
            with self.subTest(invalid=invalid):
                records, findings = validate_alignment_input(
                    invalid,
                    {"feature.understanding.explore-alignment"},
                    node_ids,
                    "alignment.json",
                )
                self.assertEqual(records, {})
                self.assertTrue(findings)

    def test_effective_status_never_comes_from_candidate_or_stale_evidence(self):
        valid = read_json("alignment-input.example.json")["records"][0]
        record, findings = qualify_alignment(
            valid["subject_id"], valid, "current", "0123456789abcdef0123456789abcdef01234567"
        )
        self.assertEqual(record["status"], "verified")
        self.assertEqual(findings, ())

        candidate = {**valid, "basis": "candidate-only"}
        record, findings = qualify_alignment(valid["subject_id"], candidate, "current", "revision")
        self.assertEqual(record["status"], "unknown")
        self.assertTrue(findings)

        record, findings = qualify_alignment(valid["subject_id"], valid, "stale", "revision")
        self.assertEqual(record["status"], "unknown")
        self.assertTrue(findings)

        no_evidence = {**valid, "evidence_node_ids": []}
        record, findings = qualify_alignment(valid["subject_id"], no_evidence, "current", "revision")
        self.assertEqual(record["status"], "unknown")
        self.assertTrue(findings)

        disagreement = {
            **valid,
            "status": "disagrees",
            "basis": "deterministic-finding",
            "evidence_node_ids": [],
            "finding_ids": ["CONCORDE-ALIGN-EXAMPLE"],
        }
        record, findings = qualify_alignment(valid["subject_id"], disagreement, "current", "revision")
        self.assertEqual(record["status"], "disagrees")
        self.assertEqual(findings, ())

    def test_unmapped_subject_is_explicitly_unknown(self):
        record, findings = qualify_alignment("entity.example.unmapped", None, "absent", None)
        self.assertEqual(record, {
            "subject_id": "entity.example.unmapped",
            "status": "unknown",
            "requested_status": None,
            "basis": None,
            "implementation_revision": None,
            "freshness": "absent",
            "implementation_node_ids": [],
            "evidence_node_ids": [],
            "finding_ids": [],
            "rationale": "No explicit alignment claim was supplied.",
        })
        self.assertEqual(findings, ())

    def test_profile_projection_preserves_identity_and_separates_adapter_type(self):
        package = ProjectRepository(REPOSITORY_ROOT).load()
        projection = project_specification(package, "feature.understanding.explore-alignment")
        subjects = {item["id"]: item for item in projection["subjects"]}
        feature = subjects["feature.understanding.explore-alignment"]
        explorer = subjects["entity.understanding.alignment-explorer"]
        self.assertEqual(feature["kind"], "feature")
        self.assertEqual(feature["adapter_type"], "concept")
        self.assertEqual(feature["source_path"], "specs/concorde/modules/understanding/features/006-explore-alignment.md")
        self.assertEqual(explorer["profile_kind"], "program")
        self.assertEqual(explorer["adapter_type"], "concept")
        self.assertEqual(explorer["id"], "entity.understanding.alignment-explorer")
        subject_ids = set(subjects)
        self.assertTrue(all(
            relation["source_id"] in subject_ids and relation["target_id"] in subject_ids
            for relation in projection["relationships"]
        ))

    def test_graph_input_path_must_be_project_relative_real_and_non_symlinked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            graph = root / "graph.json"
            graph.write_text(json.dumps(read_json("knowledge-graph.example.json")), encoding="utf-8")
            loaded, findings = load_knowledge_graph(root, "graph.json")
            self.assertIsNotNone(loaded)
            self.assertEqual(findings, ())
            for unsafe in ("../graph.json", str(graph.resolve())):
                with self.subTest(unsafe=unsafe):
                    loaded, findings = load_knowledge_graph(root, unsafe)
                    self.assertIsNone(loaded)
                    self.assertTrue(findings)

            if hasattr(os, "symlink"):
                linked = root / "linked.json"
                linked.symlink_to(graph)
                loaded, findings = load_knowledge_graph(root, "linked.json")
                self.assertIsNone(loaded)
                self.assertTrue(any("symlink" in item.message.lower() for item in findings))


if __name__ == "__main__":
    unittest.main()
