from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


INSTALLER = REPOSITORY_ROOT / "scripts/install-concorde.py"


class OneCommandInstallAcceptance(unittest.TestCase):
    def run_installer(self, target: Path, *arguments: str):
        return subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(target), "--format", "json", *arguments],
            text=True, capture_output=True,
        )

    def test_preview_is_default_and_apply_is_one_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            preview = self.run_installer(target, "--integration", "codex")
            self.assertEqual(preview.returncode, 0, preview.stderr)
            value = json.loads(preview.stdout)
            self.assertEqual(value["status"], "preview")
            self.assertEqual(list(target.rglob("*")), [])
            applied = self.run_installer(target, "--integration", "codex", "--apply")
            self.assertEqual(applied.returncode, 0, applied.stderr or applied.stdout)
            self.assertEqual(json.loads(applied.stdout)["status"], "installed")
            self.assertTrue((target / ".agents/skills/concorde-init/SKILL.md").is_file())
            self.assertTrue((target / ".concorde/install.json").is_file())

    def test_each_supported_integration_installs_all_commands(self):
        with tempfile.TemporaryDirectory() as temporary:
            for integration, root_name in (("codex", ".agents/skills"), ("claude", ".claude/skills")):
                target = Path(temporary) / integration
                result = self.run_installer(target, "--integration", integration, "--apply")
                self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                self.assertEqual(len(list((target / root_name).glob("concorde-*/SKILL.md"))), 16)

    def test_existing_project_control_and_sources_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            config = target / ".concorde/config.json"
            config.parent.mkdir()
            config.write_text('{"profile_version":7,"root_module_id":"module.app","specification_root":"specs/app"}\n')
            source = target / "specs/app/architecture.md"
            source.parent.mkdir(parents=True)
            source.write_text("project authority\n")
            before = (config.read_bytes(), source.read_bytes())
            result = self.run_installer(target, "--apply")
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(before, (config.read_bytes(), source.read_bytes()))
            receipt_paths = {item["path"] for item in json.loads((target / ".concorde/install.json").read_text())["outputs"]}
            self.assertNotIn(".concorde/config.json", receipt_paths)
            self.assertNotIn("specs/app/architecture.md", receipt_paths)

    def test_unowned_collision_returns_conflict_and_preserves_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            collision = target / ".agents/skills/concorde-plan/SKILL.md"
            collision.parent.mkdir(parents=True)
            collision.write_text("mine\n")
            result = self.run_installer(target, "--apply")
            self.assertEqual(result.returncode, 2)
            value = json.loads(result.stdout)
            self.assertEqual(value["status"], "conflict")
            self.assertEqual(collision.read_text(), "mine\n")
            self.assertFalse((target / ".concorde/install.json").exists())

    def test_invalid_package_fails_without_framework_projection(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            target = base / "target"
            invalid = base / "invalid"
            invalid.mkdir()
            (invalid / "concorde.json").write_text("{}\n")
            result = self.run_installer(target, "--checkout", str(invalid), "--apply")
            self.assertEqual(result.returncode, 3)
            self.assertEqual(json.loads(result.stdout)["status"], "failed")
            self.assertFalse((target / ".concorde/framework").exists())


if __name__ == "__main__":
    unittest.main()
