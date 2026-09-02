from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class ManifestContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((REPOSITORY_ROOT / "concorde.json").read_text())

    def test_one_manifest_declares_native_identity_profile_and_install_layout(self):
        manifest = self.manifest
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual((manifest["name"], manifest["version"]), ("concorde", "1.1.0"))
        self.assertEqual((manifest["architecture_profile"], manifest["workspace_protocol"]), (7, 12))
        self.assertEqual(manifest["integrations"], ["claude", "codex"])
        self.assertEqual(manifest["install"], {
            "framework_root": ".concorde/framework",
            "receipt": ".concorde/install.json",
            "selection": ".concorde/feature.json",
        })

    def test_runtime_reads_version_from_the_single_manifest(self):
        sys.path.insert(0, str(REPOSITORY_ROOT / "src"))
        try:
            import concorde
            self.assertEqual(concorde.__version__, self.manifest["version"])
        finally:
            sys.path.pop(0)

    def test_manifest_inventory_equals_root_commands_and_templates(self):
        commands = sorted(path.stem for path in (REPOSITORY_ROOT / "commands").glob("*.md"))
        templates = sorted(path.name for path in (REPOSITORY_ROOT / "templates").glob("*.md"))
        self.assertEqual(sorted(self.manifest["commands"]), commands)
        self.assertEqual(sorted(self.manifest["templates"]), templates)
        self.assertEqual((len(commands), len(templates)), (16, 6))

    def test_complete_feature_template_contains_profile_and_product_sections(self):
        body = (REPOSITORY_ROOT / "templates/feature-template.md").read_text()
        for marker in (
            "kind: feature", "related_features", "## Outcome and Scope", "## Usage",
            "## User Scenarios & Testing", "## Interfaces", "## Architecture Zoom",
            "## Requirements", "## Success Criteria",
        ):
            self.assertIn(marker, body)
        self.assertNotIn("[FEATURE BRANCH]", body)

    def test_plan_tasks_and_checklist_are_complete_root_references(self):
        plan = (REPOSITORY_ROOT / "templates/plan-template.md").read_text()
        tasks = (REPOSITORY_ROOT / "templates/tasks-template.md").read_text()
        checklist = (REPOSITORY_ROOT / "templates/checklist-template.md").read_text()
        for marker in ("Concorde Architecture Gate", "Source Structure", "Attempt Artifacts", "Risk Controls"):
            self.assertIn(marker, plan)
        for marker in ("Concorde Task Coverage", "Required Checklist Format", "Evidence Before Completion"):
            self.assertIn(marker, tasks)
        self.assertIn("requirements-quality", checklist)

    def test_reflection_template_keeps_log_v1_and_high_water(self):
        body = (REPOSITORY_ROOT / "templates/reflections-template.md").read_text()
        self.assertIn("Concorde Reflection Log v1", body)
        self.assertIn("concorde-reflection-high-water", body)
        self.assertIn("R-NNN", body)

    def test_removed_host_package_layout_is_absent(self):
        for relative in (".specify", "presets", "extensions", "bundles", "catalogs"):
            self.assertFalse((REPOSITORY_ROOT / relative).exists(), relative)
        serialized = json.dumps(self.manifest).lower()
        for key in ("speckit_version", "bundle_id", "install_policy"):
            self.assertNotIn(key, serialized)

    def test_native_source_install_materializes_framework_and_commands(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPOSITORY_ROOT / "scripts/install-concorde.py"),
                    "--target", str(target),
                    "--integration", "codex",
                    "--apply", "--format", "json",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(result.stdout)["status"], "installed")
            self.assertTrue((target / ".concorde/framework/concorde.json").is_file())
            self.assertTrue((target / ".agents/skills/concorde-constitution/SKILL.md").is_file())
            self.assertFalse((target / ".specify").exists())


if __name__ == "__main__":
    unittest.main()
