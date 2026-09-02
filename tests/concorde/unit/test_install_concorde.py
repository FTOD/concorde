from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.concorde.support.paths import REPOSITORY_ROOT


INSTALLER_PATH = REPOSITORY_ROOT / "scripts/install-concorde.py"
SPEC = importlib.util.spec_from_file_location("concorde_installer", INSTALLER_PATH)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)


class NativeInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package = installer.load_package(REPOSITORY_ROOT)

    def test_parser_previews_by_default_and_apply_is_explicit(self):
        arguments = installer.create_parser().parse_args(["--target", "sample"])
        self.assertFalse(arguments.apply)
        self.assertEqual(arguments.integration, "codex")
        self.assertEqual(arguments.checkout, str(REPOSITORY_ROOT))

    def test_manifest_is_single_profile_and_inventory_authority(self):
        self.assertEqual(self.package.version, "1.0.0")
        self.assertEqual(self.package.manifest["architecture_profile"], 7)
        self.assertEqual(self.package.manifest["workspace_protocol"], 12)
        self.assertEqual(len(self.package.manifest["commands"]), 16)
        self.assertEqual(len(self.package.manifest["templates"]), 6)

    def test_desired_codex_outputs_use_native_paths_only(self):
        outputs = installer.desired_outputs(self.package, "codex")
        self.assertIn(".concorde/framework/src/concorde/cli.py", outputs)
        self.assertIn(".agents/skills/speckit-plan/SKILL.md", outputs)
        self.assertIn(".codex/agents/reflection_implementer.toml", outputs)
        plan = outputs[".agents/skills/speckit-plan/SKILL.md"][0].decode()
        self.assertIn(".concorde/framework/scripts/workspace.py --phase plan", plan)
        self.assertNotIn(".specify", plan)
        self.assertTrue(all(not path.startswith(("presets/", "extensions/", "bundles/")) for path in outputs))

    def test_empty_target_preview_apply_and_repeat_are_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            actions, desired, _ = installer.installation_plan(target, self.package, "codex")
            self.assertTrue(actions)
            self.assertEqual({item["action"] for item in actions}, {"create"})
            self.assertEqual(installer.apply_plan(target, self.package, "codex", actions, desired), "installed")
            second, desired_again, _ = installer.installation_plan(target, self.package, "codex")
            self.assertEqual({item["action"] for item in second}, {"unchanged", "preserve"})
            self.assertEqual(installer.apply_plan(target, self.package, "codex", second, desired_again), "unchanged")
            receipt = json.loads((target / ".concorde/install.json").read_text())
            self.assertEqual(receipt["integration"], "codex")
            self.assertEqual(len(receipt["outputs"]), len(desired) - 2)
            self.assertNotIn("project-default", {item["role"] for item in receipt["outputs"]})

    def test_existing_project_defaults_are_preserved_and_not_owned(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            config = target / ".concorde/reflections/config.json"
            config.parent.mkdir(parents=True)
            config.write_text('{"schema_version":1,"maintainer":"custom"}\n')
            actions, desired, _ = installer.installation_plan(target, self.package, "codex")
            item = next(entry for entry in actions if entry["path"] == ".concorde/reflections/config.json")
            self.assertEqual(item["action"], "preserve")
            installer.apply_plan(target, self.package, "codex", actions, desired)
            self.assertIn('"maintainer":"custom"', config.read_text())
            paths = {entry["path"] for entry in json.loads((target / ".concorde/install.json").read_text())["outputs"]}
            self.assertNotIn(".concorde/reflections/config.json", paths)
            self.assertNotIn(".concorde/reflections/.gitignore", paths)

    def test_exact_existing_desired_bytes_are_adopted(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            desired = installer.desired_outputs(self.package, "codex")
            relative = ".agents/skills/speckit-plan/SKILL.md"
            path = target / relative
            path.parent.mkdir(parents=True)
            path.write_bytes(desired[relative][0])
            actions, _, _ = installer.installation_plan(target, self.package, "codex")
            action = next(item for item in actions if item["path"] == relative)
            self.assertEqual(action["action"], "adopt")

    def test_unowned_or_modified_owned_file_is_a_conflict(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            collision = target / ".agents/skills/speckit-plan/SKILL.md"
            collision.parent.mkdir(parents=True)
            collision.write_text("maintainer file\n")
            actions, _, _ = installer.installation_plan(target, self.package, "codex")
            item = next(entry for entry in actions if entry["path"] == collision.relative_to(target).as_posix())
            self.assertEqual(item["action"], "conflict")

    def test_integration_change_removes_only_prior_unchanged_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            actions, desired, _ = installer.installation_plan(target, self.package, "codex")
            installer.apply_plan(target, self.package, "codex", actions, desired)
            claude_actions, claude_desired, _ = installer.installation_plan(target, self.package, "claude")
            self.assertTrue(any(item["action"] == "remove" and item["path"].startswith(".agents/skills/speckit-") for item in claude_actions))
            self.assertTrue(any(item["action"] == "create" and item["path"].startswith(".claude/skills/speckit-") for item in claude_actions))
            installer.apply_plan(target, self.package, "claude", claude_actions, claude_desired)
            self.assertFalse((target / ".agents/skills/speckit-plan/SKILL.md").exists())
            self.assertTrue((target / ".claude/skills/speckit-plan/SKILL.md").is_file())

    def test_safe_relative_rejects_escape_absolute_and_backslash(self):
        for value in ("../escape", "/absolute", "bad\\path"):
            with self.subTest(value=value), self.assertRaises(installer.InstallError):
                installer._safe_relative(value, "fixture")

    def test_mid_apply_failure_removes_created_files_and_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            actions, desired, _ = installer.installation_plan(target, self.package, "codex")
            original = installer.tempfile.NamedTemporaryFile
            calls = 0

            def injected(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError("injected write failure")
                return original(*args, **kwargs)

            with mock.patch.object(installer.tempfile, "NamedTemporaryFile", side_effect=injected):
                with self.assertRaisesRegex(OSError, "injected write failure"):
                    installer.apply_plan(target, self.package, "codex", actions, desired)
            self.assertEqual(list(target.rglob("*")), [])


if __name__ == "__main__":
    unittest.main()
