from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, REPOSITORY_ROOT


class InstalledCommandSurfaceContractTests(unittest.TestCase):
    def install(self, base: str, integration: str) -> Path:
        root = Path(base) / integration
        result = subprocess.run(
            [
                sys.executable,
                str(REPOSITORY_ROOT / "scripts/install-concorde.py"),
                "--target", str(root),
                "--integration", integration,
                "--apply", "--format", "json",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertEqual(json.loads(result.stdout)["status"], "installed")
        shutil.copytree(CONTEXT_PROJECT / ".concorde", root / ".concorde", dirs_exist_ok=True)
        shutil.copytree(CONTEXT_PROJECT / "specs", root / "specs", dirs_exist_ok=True)
        (root / ".concorde/feature.json").write_text(
            '{"feature_path":"specs/example/features/001-deliver.md"}\n'
        )
        return root

    def test_both_integrations_receive_all_commands_and_reflection_agents(self):
        with tempfile.TemporaryDirectory() as temporary:
            for integration, skill_root in (("codex", ".agents/skills"), ("claude", ".claude/skills")):
                with self.subTest(integration=integration):
                    root = self.install(temporary, integration)
                    skills = sorted((root / skill_root).glob("speckit-*/SKILL.md"))
                    self.assertEqual(len(skills), 16)
                    self.assertTrue((root / skill_root / "reflections-triage/SKILL.md").is_file())
                    if integration == "codex":
                        self.assertTrue((root / ".codex/agents/reflection_investigator.toml").is_file())
                    else:
                        self.assertTrue((root / ".claude/agents/reflection-investigator.md").is_file())
                    for skill in skills:
                        content = skill.read_text()
                        self.assertIn('author: "concorde"', content)
                        self.assertIn('compatibility: "Requires a Concorde project"', content)
                        self.assertNotIn(".specify/", content)
                        self.assertNotIn("github-spec-kit", content)

    def test_phase_commands_use_installed_workspace_and_templates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.install(temporary, "codex")
            plan = (root / ".agents/skills/speckit-plan/SKILL.md").read_text()
            specify = (root / ".agents/skills/speckit-specify/SKILL.md").read_text()
            self.assertIn("python3 .concorde/framework/scripts/workspace.py --phase plan", plan)
            self.assertIn(".concorde/framework/templates/plan-template.md", plan)
            self.assertIn(".concorde/framework/templates/feature-template.md", specify)
            self.assertIn("Protocol 12", plan)
            self.assertNotIn(str(REPOSITORY_ROOT), plan + specify)

    def test_installed_workspace_adapter_executes_protocol12(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.install(temporary, "codex")
            result = subprocess.run(
                [
                    sys.executable,
                    str(root / ".concorde/framework/scripts/workspace.py"),
                    "--project-root", str(root),
                    "--phase", "plan",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["schema_version"], 12)
            self.assertEqual(payload["workspace"]["feature_id"], "feature.example.deliver")
            self.assertEqual(payload["phase_root"], ".concorde/attempts/feature.example.deliver")

    def test_receipt_roles_cover_framework_commands_agents_and_defaults(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.install(temporary, "codex")
            receipt = json.loads((root / ".concorde/install.json").read_text())
            self.assertEqual(receipt["concorde_version"], "1.0.0")
            self.assertEqual(receipt["integration"], "codex")
            roles = {item["role"] for item in receipt["outputs"]}
            self.assertEqual(roles, {"framework", "command", "agent"})
            paths = {item["path"] for item in receipt["outputs"]}
            self.assertIn(".concorde/framework/concorde.json", paths)
            self.assertIn(".agents/skills/speckit-constitution/SKILL.md", paths)
            self.assertNotIn(".concorde/config.json", paths)
            self.assertTrue(os.access(root / ".concorde/framework/scripts/concorde.py", os.X_OK))
            self.assertTrue(os.access(root / ".concorde/framework/scripts/concorde.sh", os.X_OK))

    def test_installed_framework_canonical_bytes_match_root_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.install(temporary, "codex")
            for relative in (
                "concorde.json",
                "commands/speckit.plan.md",
                "templates/feature-template.md",
                "src/concorde/cli.py",
                "agent-assets/reflections/manifest.json",
            ):
                self.assertEqual(
                    (root / ".concorde/framework" / relative).read_bytes(),
                    (REPOSITORY_ROOT / relative).read_bytes(),
                    relative,
                )


if __name__ == "__main__":
    unittest.main()
