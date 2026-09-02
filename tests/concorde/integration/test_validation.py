import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import INVALID_PROJECTS, RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.diagnostics import canonical_json, tool_envelope  # noqa: E402
from concorde.validate import validate_project  # noqa: E402


class ValidationIntegrationTests(unittest.TestCase):
    def test_three_runs_are_byte_equivalent_and_non_mutating(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            outputs = [canonical_json(tool_envelope(validate_project(root))) for _ in range(3)]
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual(outputs[1], outputs[2])
            self.assertEqual(before, {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()})
            self.assertIn('"source_digest":"sha256:', outputs[0])

    def test_bounded_module_target_returns_only_current_level_artifacts(self):
        result = validate_project(VALID_PROJECT, "module.example.api")
        self.assertEqual(result.status, "success", result.findings)
        self.assertIn("specs/example/modules/api/architecture.md", result.artifacts)
        self.assertIn("specs/example/modules/api/features/001-invoke.md", result.artifacts)
        self.assertNotIn("specs/example/features/001-deliver.md", result.artifacts)

    def test_legacy_residue_yields_findings_and_stays_byte_identical(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            features = root / "specs/example/features"
            (features / "abstract.md").write_text("legacy", encoding="utf-8")
            (root / "specs/example/module.md").write_text("legacy", encoding="utf-8")
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            result = validate_project(root)
            self.assertEqual(result.status, "invalid")
            self.assertEqual(len([item for item in result.findings if item.rule_id == "CONCORDE-LAYOUT-LEGACY"]), 2)
            self.assertEqual(before, {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()})

    def test_malformed_reflection_log_fixture_yields_one_finding_per_rule(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            overlay = INVALID_PROJECTS / "reflections-malformed/.concorde/reflections/log.md"
            log = root / ".concorde/reflections/log.md"
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_bytes(overlay.read_bytes())
            rules = sorted(item.rule_id for item in validate_project(root).findings if item.rule_id.startswith("CONCORDE-REFLECT-"))
            self.assertEqual(rules, ["CONCORDE-REFLECT-001", "CONCORDE-REFLECT-002", "CONCORDE-REFLECT-003", "CONCORDE-REFLECT-004"])

    def test_layout_evidence_and_freshness_defects_are_distinct(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            feature = root / "specs/example/features/001-deliver.md"
            (root / "specs/example/plan.md").write_text("invalid root plan", encoding="utf-8")
            feature.write_text(feature.read_text(encoding="utf-8").replace(
                "evidence_status: unknown",
                "evidence_status: disagrees\nevidence:\n  - kind: test\n    target: tests/missing.py\n    status: verified\n    producer: unittest",
            ), encoding="utf-8")
            receipt = root / ".concorde/receipts/archify.json"
            receipt.parent.mkdir(parents=True)
            receipt.write_text(json.dumps({
                "producer": "archify",
                "source_paths": ["specs/example/diagrams/level-view.json"],
                "source_digest": "sha256:" + "0" * 64,
                "output": "generated/architecture/example.html",
            }), encoding="utf-8")
            rules = {item.rule_id for item in validate_project(root).findings}
            self.assertIn("CONCORDE-LAYOUT-001", rules)
            self.assertIn("CONCORDE-EVIDENCE-002", rules)
            self.assertIn("CONCORDE-FRESHNESS-001", rules)

    def test_feature_filename_rename_keeps_stable_id_attempt_binding(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            attempt = root / ".concorde/attempts/feature.example.deliver"
            attempt.mkdir(parents=True)
            (attempt / "plan.md").write_text("# Plan\n", encoding="utf-8")
            feature = root / "specs/example/features/001-deliver.md"
            feature.rename(feature.with_name("002-renamed.md"))
            findings = validate_project(root).findings
            self.assertFalse(any(item.rule_id == "CONCORDE-LAYOUT-012" for item in findings), findings)

    def test_stable_id_change_leaves_old_attempt_orphaned(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            attempt = root / ".concorde/attempts/feature.example.deliver"
            attempt.mkdir(parents=True)
            (attempt / "plan.md").write_text("# Plan\n", encoding="utf-8")
            feature = root / "specs/example/features/001-deliver.md"
            feature.write_text(
                feature.read_text(encoding="utf-8").replace(
                    "id: feature.example.deliver",
                    "id: feature.example.renamed",
                    1,
                ),
                encoding="utf-8",
            )
            findings = validate_project(root).findings
            orphan = next(item for item in findings if item.rule_id == "CONCORDE-LAYOUT-012")
            self.assertIn("orphan", orphan.message.lower())
            self.assertEqual(orphan.source, ".concorde/attempts/feature.example.deliver")

    def test_case_colliding_feature_names_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            source = root / "specs/example/features/001-deliver.md"
            source.with_name("001-DELIVER.md").write_bytes(source.read_bytes())
            findings = validate_project(root).findings
            self.assertTrue(any(item.rule_id == "CONCORDE-LAYOUT-013" for item in findings), findings)

    def test_case_variant_attempt_key_is_rejected_against_stable_feature_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            attempt = root / ".concorde/attempts/FEATURE.EXAMPLE.DELIVER"
            attempt.mkdir(parents=True)
            findings = validate_project(root).findings
            self.assertTrue(any(item.rule_id == "CONCORDE-LAYOUT-013" for item in findings), findings)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_feature_and_attempt_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            feature = root / "specs/example/features/001-deliver.md"
            feature.with_name("002-linked.md").symlink_to(feature)
            external = root / "external-attempt"
            external.mkdir()
            attempts = root / ".concorde/attempts"
            attempts.mkdir()
            (attempts / "feature.example.deliver").symlink_to(external, target_is_directory=True)
            findings = validate_project(root).findings
            unsafe = [item for item in findings if "symlink" in item.message.lower()]
            self.assertGreaterEqual(len(unsafe), 2, findings)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_control_roots_and_reflection_log_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            external_attempts = root / "external-attempts"
            external_attempts.mkdir()
            (root / ".concorde/attempts").symlink_to(external_attempts, target_is_directory=True)
            findings = validate_project(root).findings
            self.assertTrue(any("symlink" in item.message.lower() for item in findings), findings)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            target = root / "external-log.md"
            target.write_text("# Reflections\n", encoding="utf-8")
            reflection_dir = root / ".concorde/reflections"
            reflection_dir.mkdir()
            (reflection_dir / "log.md").symlink_to(target)
            result = validate_project(root)
            self.assertEqual(result.status, "invalid")
            self.assertTrue(any("symlink" in item.message.lower() for item in result.findings), result.findings)


if __name__ == "__main__":
    unittest.main()
