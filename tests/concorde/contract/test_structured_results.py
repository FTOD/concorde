import json
import sys
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.diagnostics import Finding, canonical_json, envelope, exit_code, operation_envelope  # noqa: E402
from concorde.model import OperationResult  # noqa: E402
from concorde.context import bounded_context  # noqa: E402
from concorde.validate import validate_project  # noqa: E402


class StructuredResultTests(unittest.TestCase):
    def test_canonical_envelope_and_finding_order(self):
        findings = [
            Finding("CONCORDE-REF-002", "warning", "z.md", "z", "fix z"),
            Finding("CONCORDE-REF-001", "error", "a.md", "a", "fix a"),
        ]
        result = envelope("validate", "specs/example", "invalid", ["z.md", "a.md"], findings, {})
        encoded = canonical_json(result)
        decoded = json.loads(encoded)
        self.assertEqual(decoded["artifacts"], ["a.md", "z.md"])
        self.assertEqual(decoded["findings"][0]["rule_id"], "CONCORDE-REF-001")
        self.assertTrue(encoded.endswith("\n"))

    def test_status_exit_codes(self):
        self.assertEqual(exit_code("success"), 0)
        self.assertEqual(exit_code("eligible"), 0)
        self.assertEqual(exit_code("accepted"), 0)
        self.assertEqual(exit_code("invalid"), 1)
        self.assertEqual(exit_code("conflict"), 2)
        self.assertEqual(exit_code("failed"), 3)

    def test_acceptance_eligibility_envelope_preserves_proposal_metadata(self):
        result = OperationResult(
            "feature.accept",
            "feature.example.deliver",
            "eligible",
            result={
                "workspace": {"attempt_dir": "specs/example/features/001-deliver/attempt"},
                "source_digest": "sha256:" + "1" * 64,
                "proposal_path": "specs/example/features/001-deliver/attempt/accept-proposal.json",
                "task_summary": {"complete": 1, "incomplete": 0, "malformed": 0},
                "checklist_summary": {"files": 1, "complete": 2, "incomplete": 0, "malformed": 0},
            },
        )
        payload = operation_envelope(result)
        self.assertEqual(payload["proposal_path"], result.result["proposal_path"])
        self.assertEqual(payload["task_summary"], result.result["task_summary"])
        self.assertEqual(payload["checklist_summary"], result.result["checklist_summary"])

    def test_checked_in_examples_have_safe_paths(self):
        examples = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-workflow/contracts/examples"
        for path in examples.glob("*.json"):
            payload = json.loads(path.read_text())
            if "schema_version" not in payload:
                self.assertEqual(payload["proposal_version"], 5)
                self.assertEqual(payload["operation"], "feature.accept")
                proposal_paths = [payload["implementation"]["path"], *payload["remove"]]
                if "module_design" in payload:
                    proposal_paths.append(payload["module_design"]["path"])
                self.assertFalse(any(Path(item).is_absolute() or "\\" in item for item in proposal_paths))
                continue
            expected_version = 7 if payload["operation"].startswith("feature.") else 1
            self.assertEqual(payload["schema_version"], expected_version)
            self.assertFalse(any(Path(item).is_absolute() or "\\" in item for item in payload["artifacts"]))

    def test_context_example_tracks_runtime_projection_shape(self):
        example = json.loads(
            (REPOSITORY_ROOT / "specs/concorde/features/001-concorde-workflow/contracts/examples/context-response.json").read_text()
        )
        actual = bounded_context(VALID_PROJECT, "module.example")
        context = actual.result["context"]
        self.assertEqual(set(context), set(example["result"]["context"]))
        self.assertEqual(set(context["current_module"]["contracts"]), {"provided", "required"})
        self.assertEqual(set(context["children"][0]["contracts"]["provided"][0]), {"id", "role", "flow", "counterparties"})

    def test_validation_result_matches_normative_envelope_fields(self):
        actual = validate_project(VALID_PROJECT)
        payload = envelope(actual.operation, actual.target, actual.status, actual.artifacts, actual.findings, dict(actual.result))
        self.assertEqual(set(payload), {"schema_version", "operation", "target", "status", "artifacts", "findings", "result"})
        self.assertEqual(set(payload["result"]), {"summary", "source_digest"})


if __name__ == "__main__":
    unittest.main()
