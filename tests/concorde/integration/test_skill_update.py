from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


SPEC = importlib.util.spec_from_file_location(
    "native_installer_skill_update", REPOSITORY_ROOT / "scripts/install-concorde.py"
)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)


class SkillUpdateIntegrationTests(unittest.TestCase):
    def copy_package(self, destination: Path) -> None:
        for name in ("concorde.json", "LICENSE", "README.md"):
            shutil.copy2(REPOSITORY_ROOT / name, destination / name)
        for directory in ("agent-assets", "operations", "skills", "src", "templates"):
            shutil.copytree(
                REPOSITORY_ROOT / directory,
                destination / directory,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
        shutil.copytree(
            REPOSITORY_ROOT / "docsite",
            destination / "docsite",
            ignore=shutil.ignore_patterns("node_modules", "build", ".generated", ".docusaurus", "coverage"),
        )
        (destination / "scripts").mkdir()
        for name in (
            "concorde.py",
            "concorde.ps1",
            "concorde.sh",
            "reflections_queue.py",
            "render-capability-surfaces.py",
            "workspace.py",
        ):
            shutil.copy2(REPOSITORY_ROOT / "scripts" / name, destination / "scripts" / name)

    def test_one_leaf_source_updates_framework_and_projected_owned_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            target = base / "target"
            package = installer.load_package(REPOSITORY_ROOT)
            actions, desired, _ = installer.installation_plan(target, package, "codex")
            target.mkdir()
            installer.apply_plan(target, package, "codex", actions, desired)
            before = {
                item["path"]: item["sha256"]
                for item in json.loads((target / ".concorde/install.json").read_text())[
                    "outputs"
                ]
            }

            changed_root = base / "changed"
            changed_root.mkdir()
            self.copy_package(changed_root)
            skill = changed_root / "skills/concorde-checklist/SKILL.md"
            skill.write_text(skill.read_text() + "\nNative update marker.\n")
            changed_package = installer.load_package(changed_root)
            update_actions, update_desired, _ = installer.installation_plan(
                target, changed_package, "codex"
            )
            updates = {
                item["path"] for item in update_actions if item["action"] == "update"
            }
            self.assertEqual(
                updates,
                {
                    ".concorde/framework/skills/concorde-checklist/SKILL.md",
                    ".agents/skills/concorde-checklist/SKILL.md",
                },
            )
            installer.apply_plan(
                target, changed_package, "codex", update_actions, update_desired
            )
            after = {
                item["path"]: item["sha256"]
                for item in json.loads((target / ".concorde/install.json").read_text())[
                    "outputs"
                ]
            }
            self.assertEqual({path for path in before if before[path] != after[path]}, updates)
            self.assertIn(
                "Native update marker",
                (target / ".agents/skills/concorde-checklist/SKILL.md").read_text(),
            )

    def test_operation_python_updates_framework_without_rewriting_skill_projection(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            target = base / "target"
            package = installer.load_package(REPOSITORY_ROOT)
            actions, desired, _ = installer.installation_plan(target, package, "codex")
            target.mkdir()
            installer.apply_plan(target, package, "codex", actions, desired)

            changed_root = base / "changed"
            changed_root.mkdir()
            self.copy_package(changed_root)
            operation = (
                changed_root
                / "operations/concorde-standard-dev-loop/operation.py"
            )
            operation.write_text(operation.read_text() + "\n# Native update marker.\n")
            changed_package = installer.load_package(changed_root)
            update_actions, _, _ = installer.installation_plan(
                target, changed_package, "codex"
            )
            updates = {
                item["path"] for item in update_actions if item["action"] == "update"
            }
            self.assertEqual(
                updates,
                {
                    ".concorde/framework/operations/concorde-standard-dev-loop/operation.py"
                },
            )

    def test_skill_projection_update_preserves_project_selection(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            selection = target / ".concorde/feature.json"
            selection.parent.mkdir()
            selection.write_text('{"feature_path":"specs/example/features/001-a.md"}\n')
            package = installer.load_package(REPOSITORY_ROOT)
            actions, desired, _ = installer.installation_plan(target, package, "claude")
            installer.apply_plan(target, package, "claude", actions, desired)
            self.assertEqual(
                selection.read_text(),
                '{"feature_path":"specs/example/features/001-a.md"}\n',
            )
            receipt_paths = {
                item["path"]
                for item in json.loads((target / ".concorde/install.json").read_text())[
                    "outputs"
                ]
            }
            self.assertNotIn(".concorde/feature.json", receipt_paths)


if __name__ == "__main__":
    unittest.main()
