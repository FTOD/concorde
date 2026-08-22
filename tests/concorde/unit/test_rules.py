import shutil
import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.validate import validate_project  # noqa: E402


class ValidationRuleTests(unittest.TestCase):
    def project_copy(self, temporary: str) -> Path:
        root = Path(temporary) / "project"
        shutil.copytree(VALID_PROJECT, root)
        return root

    def test_valid_fixture_has_no_errors(self):
        result = validate_project(VALID_PROJECT)
        self.assertEqual(result.status, "success", result.findings)

    def test_broken_reference_has_stable_actionable_finding(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            module = root / "specs/example/module.md"
            module.write_text(module.read_text().replace("module.example.api", "module.example.missing", 1))
            result = validate_project(root)
            finding = next(item for item in result.findings if item.rule_id == "CONCORDE-REF-001")
            self.assertEqual(finding.severity, "error")
            self.assertFalse(Path(finding.source).is_absolute())
            self.assertTrue(finding.remediation)

    def test_cycle_contract_view_and_evidence_rules(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            child = root / "specs/example/modules/api/module.md"
            child.write_text(child.read_text().replace("children: []", "children:\n  - module.example"))
            feature = root / "specs/example/features/001-deliver/spec.md"
            feature.write_text(feature.read_text().replace("evidence_status: unknown", "evidence_status: magical"))
            contract = root / "specs/example/contracts/workflow/contract.md"
            contract.write_text(contract.read_text().replace("counterparties:\n  - external.maintainer", "counterparties: []"))
            result = validate_project(root)
            rules = [finding.rule_id for finding in result.findings]
            self.assertIn("CONCORDE-HIER-001", rules)
            self.assertIn("CONCORDE-CONTRACT-002", rules)
            self.assertIn("CONCORDE-EVIDENCE-001", rules)
            self.assertEqual(rules, sorted(rules))

    def test_scenario_participant_connection_and_view_depth_rules(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            view_path = root / "specs/example/architecture.json"
            view = json.loads(view_path.read_text())
            view["meta"]["views"][0]["focus"].append("missing")
            view["components"].append({"id": "grandchild", "type": "backend", "module_id": "module.example.api.store"})
            view_path.write_text(json.dumps(view))
            rules = {finding.rule_id for finding in validate_project(root).findings}
            self.assertIn("CONCORDE-SCENARIO-002", rules)
            self.assertIn("CONCORDE-VIEW-002", rules)

    def test_module_prose_and_explicit_child_view_identity_are_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            module = root / "specs/example/module.md"
            module.write_text(module.read_text().replace("## Responsibility", "## Missing Responsibility"))
            view_path = root / "specs/example/architecture.json"
            view = json.loads(view_path.read_text())
            child = next(item for item in view["components"] if item.get("module_id") == "module.example.api")
            child.pop("module_id")
            view_path.write_text(json.dumps(view))
            rules = {finding.rule_id for finding in validate_project(root).findings}
            self.assertIn("CONCORDE-MODULE-001", rules)
            self.assertIn("CONCORDE-VIEW-005", rules)


if __name__ == "__main__":
    unittest.main()
