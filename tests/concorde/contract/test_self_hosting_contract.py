import json
import re
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


CONTRACT = REPOSITORY_ROOT / "specs/concorde/features/004-self-host-concorde/contracts"


class SelfHostingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((CONTRACT / "self-hosting.schema.json").read_text())

    def test_examples_select_exactly_one_protocol_branch(self):
        examples = {
            "proposal.json": ("proposal_version", "self-host.apply"),
            "applied-result.json": ("schema_version", "self-host.apply"),
            "status-current.json": ("schema_version", "self-host.status"),
        }
        for name, (version_field, operation) in examples.items():
            value = json.loads((CONTRACT / "examples" / name).read_text())
            self.assertEqual(value[version_field], 1)
            self.assertEqual(value["operation"], operation)
            self.assertEqual(value["target"], "feature.concorde.self-host-framework")
            self.assertRegex(value["source_digest"], r"^sha256:[0-9a-f]{64}$")

    def test_custom_schema_is_closed_and_defines_all_evidence_dimensions(self):
        definitions = self.schema["$defs"]
        for branch in ("proposal", "result", "status", "component", "change", "finding", "dimension"):
            self.assertFalse(definitions[branch]["additionalProperties"])
        dimensions = definitions["status"]["properties"]["dimensions"]
        self.assertEqual(set(dimensions["required"]), {"source", "installed", "registry", "surfaces", "activation"})

    def test_safe_path_schema_rejects_escape_forms(self):
        patterns = [re.compile(item["pattern"]) for item in self.schema["$defs"]["safePath"]["not"]["anyOf"]]
        for unsafe in ("/tmp/x", "C:\\temp\\x", "../x", "a/../x", "a\\b", "a/"):
            self.assertTrue(any(pattern.search(unsafe) for pattern in patterns), unsafe)
        for safe in (".specify/self-hosting.json", ".agents/skills/speckit-plan/SKILL.md", ".claude/skills/speckit-plan/SKILL.md"):
            self.assertFalse(any(pattern.search(safe) for pattern in patterns), safe)

    def test_integration_field_remains_shape_generic_for_codex_and_claude(self):
        for branch in ("proposal", "result", "status"):
            integration = self.schema["$defs"][branch]["properties"]["integration"]
            self.assertEqual(integration, {"type": "string", "minLength": 1})


if __name__ == "__main__":
    unittest.main()
