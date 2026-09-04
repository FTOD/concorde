from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.understanding.alignment import ALIGNMENT_SCHEMA_VERSION, UA_EDGE_TYPES, UA_NODE_TYPES  # noqa: E402


FIXTURES = REPOSITORY_ROOT / "tests/concorde/fixtures/interfaces/alignment"


class AlignmentExplorerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {
            name: json.loads((FIXTURES / name).read_text(encoding="utf-8"))
            for name in (
                "knowledge-graph.schema.json",
                "alignment-input.schema.json",
                "alignment-explorer.schema.json",
            )
        }
        registry = Registry()
        for value in cls.schemas.values():
            registry = registry.with_resource(value["$id"], Resource.from_contents(value))
        for name in ("knowledge-graph.schema.json", "alignment-input.schema.json"):
            registry = registry.with_resource(
                "https://concorde.invalid/interfaces/" + name,
                Resource.from_contents(cls.schemas[name]),
            )
        cls.registry = registry

    def test_all_schemas_and_examples_are_executable(self):
        pairs = (
            ("knowledge-graph.schema.json", "knowledge-graph.example.json"),
            ("alignment-input.schema.json", "alignment-input.example.json"),
            ("alignment-explorer.schema.json", "alignment-explorer.example.json"),
        )
        for schema_name, example_name in pairs:
            with self.subTest(example=example_name):
                schema = self.schemas[schema_name]
                Draft202012Validator.check_schema(schema)
                example = json.loads((FIXTURES / example_name).read_text(encoding="utf-8"))
                Draft202012Validator(schema, registry=self.registry).validate(example)

    def test_pinned_formal_counts_match_runtime(self):
        node_enum = self.schemas["knowledge-graph.schema.json"]["$defs"]["node"]["properties"]["type"]["enum"]
        edge_enum = self.schemas["knowledge-graph.schema.json"]["$defs"]["edge"]["properties"]["type"]["enum"]
        self.assertEqual(ALIGNMENT_SCHEMA_VERSION, 1)
        self.assertEqual(tuple(node_enum), UA_NODE_TYPES)
        self.assertEqual(tuple(edge_enum), UA_EDGE_TYPES)
        self.assertEqual((len(node_enum), len(edge_enum)), (27, 38))

    def test_architecture_service_reserves_the_native_tool(self):
        schema = json.loads(
            (REPOSITORY_ROOT / "tests/concorde/fixtures/interfaces/workspace/architecture-service.schema.json").read_text()
        )
        self.assertIn("explore", schema["$defs"]["tool"]["enum"])
        self.assertEqual(schema["$defs"]["response"]["properties"]["schema_version"]["const"], 2)
        self.assertNotIn("operation", schema["$defs"]["response"]["properties"])

    def test_distribution_does_not_add_a_conversational_explorer_skill(self):
        manifest = json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
        self.assertEqual(len(manifest["skills"]), 17)
        self.assertFalse(any("explore" in skill for skill in manifest["skills"]))
        self.assertFalse((REPOSITORY_ROOT / "skills/concorde-explore").exists())

    def test_alignment_input_has_no_similarity_or_confidence_escape_hatch(self):
        record = self.schemas["alignment-input.schema.json"]["$defs"]["record"]
        self.assertFalse(record["additionalProperties"])
        self.assertNotIn("confidence", record["properties"])
        self.assertNotIn("name-similarity", record["properties"]["basis"]["enum"])


if __name__ == "__main__":
    unittest.main()
