from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


INSTALLER = REPOSITORY_ROOT / "scripts/install-concorde.py"


class NativeInstallationLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "target"

    def run_install(self, *arguments: str, checkout: Path = REPOSITORY_ROOT, check: bool = True):
        result = subprocess.run(
            [
                sys.executable, str(INSTALLER),
                "--target", str(self.root),
                "--checkout", str(checkout),
                "--format", "json",
                *arguments,
            ],
            text=True,
            capture_output=True,
        )
        if check and result.returncode:
            self.fail(result.stderr or result.stdout)
        return result, json.loads(result.stdout)

    def package_copy(self, name: str = "package") -> Path:
        destination = Path(self.temporary.name) / name
        destination.mkdir()
        shutil.copy2(REPOSITORY_ROOT / "concorde.json", destination / "concorde.json")
        shutil.copy2(REPOSITORY_ROOT / "LICENSE", destination / "LICENSE")
        shutil.copy2(REPOSITORY_ROOT / "README.md", destination / "README.md")
        for directory in ("agent-assets", "operations", "skills", "src", "templates"):
            shutil.copytree(REPOSITORY_ROOT / directory, destination / directory, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (destination / "scripts").mkdir()
        for script in ("concorde.py", "concorde.ps1", "concorde.sh", "reflections_queue.py", "render-capability-surfaces.py", "workspace.py"):
            shutil.copy2(REPOSITORY_ROOT / "scripts" / script, destination / "scripts" / script)
        return destination

    def tree_digest(self):
        return {
            path.relative_to(self.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(self.root.rglob("*")) if path.is_file()
        }

    def test_preview_apply_repeat_and_receipt_provenance(self):
        _, preview = self.run_install("--integration", "codex")
        self.assertEqual(preview["status"], "preview")
        self.assertEqual({item["action"] for item in preview["actions"]}, {"create"})
        self.assertEqual(list(self.root.rglob("*")), [])
        _, applied = self.run_install("--integration", "codex", "--apply")
        self.assertEqual(applied["status"], "installed")
        receipt = json.loads((self.root / ".concorde/install.json").read_text())
        self.assertEqual(receipt["concorde_version"], "2.1.0")
        self.assertEqual(receipt["architecture_profile"], 7)
        self.assertEqual(receipt["workspace_protocol"], 13)
        before = self.tree_digest()
        _, repeated = self.run_install("--integration", "codex", "--apply")
        self.assertEqual(repeated["status"], "unchanged")
        self.assertEqual(before, self.tree_digest())

    def test_compatible_package_update_changes_only_owned_outputs(self):
        self.run_install("--integration", "codex", "--apply")
        unrelated = self.root / "README.user.md"
        unrelated.write_text("maintainer\n")
        updated = self.package_copy("updated")
        manifest = json.loads((updated / "concorde.json").read_text())
        manifest["version"] = "2.1.0"
        (updated / "concorde.json").write_text(json.dumps(manifest, indent=2) + "\n")
        skill = updated / "skills/concorde-ask/SKILL.md"
        skill.write_text(skill.read_text() + "\nUpdate marker.\n")
        _, preview = self.run_install("--integration", "codex", checkout=updated)
        self.assertTrue(any(item["action"] == "update" for item in preview["actions"]))
        self.run_install("--integration", "codex", "--apply", checkout=updated)
        receipt = json.loads((self.root / ".concorde/install.json").read_text())
        self.assertEqual(receipt["concorde_version"], "2.1.0")
        self.assertEqual(unrelated.read_text(), "maintainer\n")
        self.assertIn("Update marker", (self.root / ".agents/skills/concorde-ask/SKILL.md").read_text())

    def test_modified_owned_output_blocks_update_without_mutation(self):
        self.run_install("--integration", "codex", "--apply")
        modified = self.root / ".agents/skills/concorde-plan/SKILL.md"
        modified.write_text("maintainer edit\n")
        before = self.tree_digest()
        result, preview = self.run_install("--integration", "codex", check=False)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(preview["status"], "conflict")
        self.assertTrue(any(item["path"].endswith("concorde-plan/SKILL.md") and item["action"] == "conflict" for item in preview["actions"]))
        self.assertEqual(before, self.tree_digest())

    def test_integration_switch_reconciles_owned_surfaces_and_preserves_unrelated(self):
        self.run_install("--integration", "codex", "--apply")
        unrelated = self.root / ".agents/skills/team/SKILL.md"
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text("team\n")
        _, preview = self.run_install("--integration", "claude")
        self.assertTrue(any(item["action"] == "remove" and item["path"].startswith(".agents/skills/concorde-") for item in preview["actions"]))
        self.run_install("--integration", "claude", "--apply")
        self.assertTrue((self.root / ".claude/skills/concorde-plan/SKILL.md").is_file())
        self.assertFalse((self.root / ".agents/skills/concorde-plan/SKILL.md").exists())
        self.assertEqual(unrelated.read_text(), "team\n")

    def test_invalid_profile_stops_before_output(self):
        package = self.package_copy("invalid")
        manifest = json.loads((package / "concorde.json").read_text())
        manifest["architecture_profile"] = 6
        (package / "concorde.json").write_text(json.dumps(manifest))
        result, value = self.run_install("--apply", checkout=package, check=False)
        self.assertEqual(result.returncode, 3)
        self.assertEqual(value["status"], "failed")
        self.assertFalse((self.root / ".concorde/framework").exists())

    def test_symlink_output_path_is_a_nonmutating_conflict(self):
        self.root.mkdir()
        outside = Path(self.temporary.name) / "outside.txt"
        outside.write_text("outside\n")
        link = self.root / ".agents/skills/concorde-plan/SKILL.md"
        link.parent.mkdir(parents=True)
        link.symlink_to(outside)
        result, value = self.run_install("--apply", check=False)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(value["status"], "conflict")
        self.assertEqual(outside.read_text(), "outside\n")

    def test_modified_owned_legacy_output_blocks_migration_and_is_preserved(self):
        self.root.mkdir()
        legacy = self.root / ".concorde/framework/commands/concorde.plan.md"
        legacy.parent.mkdir(parents=True)
        legacy.write_text("original legacy\n")
        receipt = {
            "schema_version": 1,
            "outputs": [
                {
                    "path": ".concorde/framework/commands/concorde.plan.md",
                    "role": "command",
                    "sha256": "sha256:"
                    + hashlib.sha256(legacy.read_bytes()).hexdigest(),
                }
            ],
        }
        receipt_path = self.root / ".concorde/install.json"
        receipt_path.parent.mkdir(exist_ok=True)
        receipt_path.write_text(json.dumps(receipt))
        legacy.write_text("maintainer changed legacy\n")
        before = self.tree_digest()
        result, value = self.run_install("--apply", check=False)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(value["status"], "conflict")
        self.assertEqual(before, self.tree_digest())
        self.assertEqual(legacy.read_text(), "maintainer changed legacy\n")


if __name__ == "__main__":
    unittest.main()
