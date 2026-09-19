import json
import sys
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.spec.diagnostics import Finding, canonical_json, envelope, exit_code  # noqa: E402
from concorde.spec.validation import validate_repository  # noqa: E402


class StructuredResultTests(unittest.TestCase):
    def test_canonical_envelope_and_finding_order(self):
        findings = [
            Finding("CONCORDE-REF-002", "warning", "z.md", "z", "fix z"),
            Finding("CONCORDE-REF-001", "error", "a.md", "a", "fix a"),
        ]
        result = envelope("validate", "module.example", "invalid", ["z.md", "a.md"], findings, {})
        encoded = canonical_json(result)
        decoded = json.loads(encoded)
        self.assertEqual(decoded["schema_version"], 2)
        self.assertEqual(decoded["tool"], "validate")
        self.assertNotIn("operation", decoded)
        self.assertEqual(decoded["artifacts"], ["a.md", "z.md"])
        self.assertEqual(decoded["findings"][0]["rule_id"], "CONCORDE-REF-001")
        self.assertTrue(encoded.endswith("\n"))

    def test_status_exit_codes(self):
        self.assertEqual(exit_code("success"), 0)
        self.assertEqual(exit_code("proposal"), 0)
        self.assertEqual(exit_code("unchanged"), 0)
        self.assertEqual(exit_code("invalid"), 1)
        self.assertEqual(exit_code("conflict"), 2)
        self.assertEqual(exit_code("failed"), 3)

    def test_validation_result_matches_normative_envelope_fields(self):
        actual = validate_repository(REPOSITORY_ROOT)
        payload = envelope(actual.tool, actual.target, actual.status, actual.artifacts, actual.findings, dict(actual.result))
        self.assertEqual(set(payload), {"schema_version", "tool", "target", "status", "artifacts", "findings", "result"})
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(set(payload["result"]), {"summary", "source_digest", "claims", "semantic_completeness"})
        self.assertFalse(any("\\" in item or item.startswith("/") for item in payload["artifacts"]))


if __name__ == "__main__":
    unittest.main()
