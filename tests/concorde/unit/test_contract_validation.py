import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.validate import validate_project  # noqa: E402


class ContractValidationTests(unittest.TestCase):
    def custom_project(self, temporary: str, value: object) -> Path:
        root = Path(temporary) / "project"
        shutil.copytree(VALID_PROJECT, root)
        contract = root / "specs/example/contracts/workflow/contract.md"
        text = contract.read_text()
        text = text.replace("kind: standard", "kind: custom")
        text = text.replace("format: HTTP", "format: JSON")
        text = text.replace("version: \"1.1\"", "version: \"1\"")
        text = text.replace(
            "definition: https://www.rfc-editor.org/rfc/rfc9110",
            "definition: specs/example/contracts/workflow/schema.json\nexamples:\n  - specs/example/contracts/workflow/example.json",
        )
        contract.write_text(text)
        (contract.parent / "schema.json").write_text(json.dumps({
            "type": "object",
            "required": ["message"],
            "properties": {"message": {"type": "string"}},
            "additionalProperties": False,
        }))
        (contract.parent / "example.json").write_text(json.dumps(value))
        return root

    def test_custom_json_example_conforms_to_supported_schema_subset(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = validate_project(self.custom_project(temporary, {"message": "ok"}))
            self.assertNotIn("CONCORDE-CONFORMANCE-001", {item.rule_id for item in result.findings})

    def test_custom_json_example_mismatch_is_actionable(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = validate_project(self.custom_project(temporary, {"message": 42}))
            finding = next(item for item in result.findings if item.rule_id == "CONCORDE-CONFORMANCE-001")
            self.assertIn("example.json", finding.message)
            self.assertTrue(finding.remediation)


if __name__ == "__main__":
    unittest.main()
