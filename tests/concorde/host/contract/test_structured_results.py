import json
import sys
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.diagnostics import Finding, canonical_json, envelope, exit_code, tool_envelope  # noqa: E402
from concorde.model import ToolResult  # noqa: E402
from concorde.understanding.context import bounded_context  # noqa: E402
from concorde.understanding.validate import validate_project  # noqa: E402


class StructuredResultTests(unittest.TestCase):
    def test_canonical_envelope_and_finding_order(self):
        findings = [
            Finding("CONCORDE-REF-002", "warning", "z.md", "z", "fix z"),
            Finding("CONCORDE-REF-001", "error", "a.md", "a", "fix a"),
        ]
        result = envelope("validate", "specs/example", "invalid", ["z.md", "a.md"], findings, {})
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
        self.assertEqual(exit_code("eligible"), 0)
        self.assertEqual(exit_code("delivered"), 0)
        self.assertEqual(exit_code("invalid"), 1)
        self.assertEqual(exit_code("conflict"), 2)
        self.assertEqual(exit_code("failed"), 3)

    def test_delivery_eligibility_envelope_preserves_proposal_metadata(self):
        result = ToolResult(
            "deliver",
            "feature.example.deliver",
            "eligible",
            result={
                "workspace": {"attempt_dir": ".concorde/attempts/feature.example.deliver"},
                "source_digest": "sha256:" + "1" * 64,
                "proposal_path": ".concorde/attempts/feature.example.deliver/deliver-proposal.json",
                "proposal_version": 9,
                "task_summary": {"complete": 1, "incomplete": 0, "malformed": 0},
                "checklist_summary": {"files": 1, "complete": 2, "incomplete": 0, "malformed": 0},
                "evidence_summary": {"passed": 1, "missing": 0},
            },
        )
        payload = tool_envelope(result)
        self.assertEqual(payload["proposal_path"], result.result["proposal_path"])
        self.assertEqual(payload["task_summary"], result.result["task_summary"])
        self.assertEqual(payload["checklist_summary"], result.result["checklist_summary"])
        self.assertEqual(payload["proposal_version"], 9)
        self.assertEqual(payload["schema_version"], 13)
        self.assertEqual(payload["tool"], "deliver")
        self.assertNotIn("operation", payload)

    def test_checked_in_examples_have_safe_paths(self):
        examples = REPOSITORY_ROOT / "tests/concorde/fixtures/interfaces/workspace"
        for name in ("deliver-proposal.json", "deliver-eligible-response.json", "context-response.json", "validation-response.json"):
            path = examples / name
            payload = json.loads(path.read_text())
            if "schema_version" not in payload:
                self.assertEqual(payload["proposal_version"], 9)
                self.assertEqual(payload["tool"], "deliver")
                proposal_paths = payload["remove"]
                self.assertFalse(any(Path(item).is_absolute() or "\\" in item for item in proposal_paths))
                continue
            expected_version = 13 if payload["tool"] == "deliver" else 2
            self.assertEqual(payload["schema_version"], expected_version)
            self.assertFalse(any(Path(item).is_absolute() or "\\" in item for item in payload["artifacts"]))

    def test_context_example_tracks_runtime_projection_shape(self):
        example = json.loads(
            (REPOSITORY_ROOT / "tests/concorde/fixtures/interfaces/workspace/context-response.json").read_text()
        )
        actual = bounded_context(VALID_PROJECT, "module.example")
        context = actual.result["context"]
        self.assertEqual(set(context), set(example["result"]["context"]))
        self.assertIn("entities", context["current_module"])
        self.assertIn("relationships", context["current_module"])
        self.assertIn("interactions", context["current_module"])
        self.assertTrue(context["current_module"]["architecture"].endswith("architecture.md"))

    def test_validation_result_matches_normative_envelope_fields(self):
        actual = validate_project(VALID_PROJECT)
        payload = envelope(actual.tool, actual.target, actual.status, actual.artifacts, actual.findings, dict(actual.result))
        self.assertEqual(set(payload), {"schema_version", "tool", "target", "status", "artifacts", "findings", "result"})
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(set(payload["result"]), {"summary", "source_digest"})


if __name__ == "__main__":
    unittest.main()
