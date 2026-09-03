from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.managed_runtime import (
    create_langgraph_index,
    runtime_install_environment,
)

INSTALLER_PATH = REPOSITORY_ROOT / "scripts/install-concorde.py"
SPEC = importlib.util.spec_from_file_location("concorde_installer", INSTALLER_PATH)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)

from concorde import managed_runtime  # noqa: E402


class NativeInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package = installer.load_package(REPOSITORY_ROOT)
        cls.runtime_temporary = tempfile.TemporaryDirectory()
        index = create_langgraph_index(Path(cls.runtime_temporary.name))
        cls.runtime_environment = mock.patch.dict(
            os.environ,
            runtime_install_environment(index),
        )
        cls.runtime_environment.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.runtime_environment.stop()
        cls.runtime_temporary.cleanup()

    def test_parser_previews_by_default_and_apply_is_explicit(self):
        arguments = installer.create_parser().parse_args(["--target", "sample"])
        self.assertFalse(arguments.apply)
        self.assertEqual(arguments.integration, "codex")
        self.assertEqual(arguments.checkout, str(REPOSITORY_ROOT))

    def test_manifest_is_single_profile_and_inventory_authority(self):
        self.assertEqual(self.package.version, "2.1.0")
        self.assertEqual(self.package.manifest["architecture_profile"], 7)
        self.assertEqual(self.package.manifest["workspace_protocol"], 13)
        self.assertEqual(len(self.package.manifest["skills"]), 17)
        self.assertEqual(len(self.package.manifest["operations"]), 3)
        self.assertEqual(len(self.package.manifest["templates"]), 6)
        self.assertEqual(
            self.package.manifest["operation_runtime"]["venv"],
            ".concorde/.venv",
        )

    def test_desired_codex_outputs_use_native_paths_only(self):
        outputs = installer.desired_outputs(self.package, "codex")
        self.assertIn(".concorde/framework/src/concorde/cli.py", outputs)
        self.assertIn(".concorde/framework/src/concorde/alignment.py", outputs)
        self.assertIn(".concorde/framework/docsite/docusaurus.config.ts", outputs)
        self.assertIn(".concorde/framework/docsite/scaffold/deploy-docsite.yml", outputs)
        self.assertNotIn(".concorde/framework/docsite/site.json", outputs)
        self.assertNotIn(".concorde/framework/docsite/sidebars.docs.ts", outputs)
        self.assertTrue(all("node_modules" not in path and "/build/" not in path for path in outputs if path.startswith(".concorde/framework/docsite/")))
        self.assertTrue(all(not path.startswith(".concorde/framework/docsite/tests/repository/") for path in outputs))
        self.assertIn(".agents/skills/concorde-plan/SKILL.md", outputs)
        self.assertIn(".agents/skills/concorde-standard-dev-loop/SKILL.md", outputs)
        self.assertIn(
            ".concorde/framework/operations/concorde-standard-dev-loop/operation.py",
            outputs,
        )
        self.assertIn(".concorde/framework/operations/requirements.lock", outputs)
        self.assertIn(".concorde/framework/scripts/run-operation.py", outputs)
        self.assertIn(".codex/agents/reflection_implementer.toml", outputs)
        plan = outputs[".agents/skills/concorde-plan/SKILL.md"][0].decode()
        self.assertIn(".concorde/framework/operations/concorde-plan/operation.py", plan)
        self.assertIn('kind: "operation"', plan)
        self.assertNotIn("concorde-plan-context", outputs)
        self.assertNotIn("concorde-plan-author", outputs)
        self.assertNotIn(".specify", plan)
        operation = outputs[".agents/skills/concorde-standard-dev-loop/SKILL.md"][0].decode()
        self.assertIn(
            ".concorde/framework/operations/concorde-standard-dev-loop/operation.py",
            operation,
        )
        self.assertIn(
            "python3 .concorde/framework/scripts/run-operation.py ",
            operation,
        )
        self.assertEqual(outputs[".agents/skills/concorde-plan/SKILL.md"][1], "operation")
        self.assertEqual(
            outputs[".agents/skills/concorde-standard-dev-loop/SKILL.md"][1],
            "operation",
        )
        self.assertTrue(all(not path.startswith(("presets/", "extensions/", "bundles/")) for path in outputs))

    def test_empty_target_preview_apply_and_repeat_are_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            actions, desired, _ = installer.installation_plan(target, self.package, "codex")
            self.assertTrue(actions)
            self.assertEqual({item["action"] for item in actions}, {"create"})
            runtime_action = next(item for item in actions if item["role"] == "runtime")
            self.assertEqual(runtime_action["path"], ".concorde/.venv")
            self.assertEqual(installer.apply_plan(target, self.package, "codex", actions, desired), "installed")
            second, desired_again, _ = installer.installation_plan(target, self.package, "codex")
            self.assertEqual({item["action"] for item in second}, {"unchanged", "preserve"})
            self.assertEqual(installer.apply_plan(target, self.package, "codex", second, desired_again), "unchanged")
            receipt = json.loads((target / ".concorde/install.json").read_text())
            self.assertEqual(receipt["integration"], "codex")
            self.assertEqual(receipt["runtime"]["path"], ".concorde/.venv")
            self.assertEqual(
                receipt["runtime"]["verified_operations"],
                self.package.manifest["operations"],
            )
            self.assertTrue((target / ".concorde/.venv/.concorde-runtime.json").is_file())
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

    def test_target_root_venv_is_ignored_and_managed_runtime_rebuild_removes_obsolete_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            user_sentinel = target / ".venv/user-package.txt"
            user_sentinel.parent.mkdir()
            user_sentinel.write_text("user-owned\n", encoding="utf-8")
            before = user_sentinel.read_bytes()
            actions, desired, _ = installer.installation_plan(target, self.package, "codex")
            installer.apply_plan(target, self.package, "codex", actions, desired)
            obsolete = target / ".concorde/.venv/obsolete-package.txt"
            obsolete.write_text("obsolete\n", encoding="utf-8")
            marker = target / ".concorde/.venv/.concorde-runtime.json"
            value = json.loads(marker.read_text(encoding="utf-8"))
            value["requirements_sha256"] = "sha256:" + "0" * 64
            marker.write_text(json.dumps(value), encoding="utf-8")

            rebuild, desired_again, _ = installer.installation_plan(
                target, self.package, "codex"
            )
            runtime_action = next(item for item in rebuild if item["role"] == "runtime")
            self.assertEqual(runtime_action["action"], "rebuild")
            real_verify = managed_runtime._verify_operations

            def verify_after_cleanup(*args, **kwargs):
                self.assertFalse(obsolete.exists())
                return real_verify(*args, **kwargs)

            with mock.patch.object(
                managed_runtime,
                "_verify_operations",
                side_effect=verify_after_cleanup,
            ):
                installer.apply_plan(
                    target, self.package, "codex", rebuild, desired_again
                )

            self.assertEqual(user_sentinel.read_bytes(), before)
            self.assertFalse(obsolete.exists())
            self.assertTrue(marker.is_file())

    def test_unowned_or_symlinked_managed_runtime_is_a_nonmutating_conflict(self):
        for symlink in (False, True):
            with self.subTest(symlink=symlink), tempfile.TemporaryDirectory() as temporary:
                target = Path(temporary)
                runtime = target / ".concorde/.venv"
                runtime.parent.mkdir(parents=True)
                if symlink:
                    outside = target / "outside"
                    outside.mkdir()
                    runtime.symlink_to(outside, target_is_directory=True)
                else:
                    runtime.mkdir()
                    (runtime / "user.txt").write_text("mine\n", encoding="utf-8")
                actions, desired, _ = installer.installation_plan(
                    target, self.package, "codex"
                )
                item = next(entry for entry in actions if entry["role"] == "runtime")
                self.assertEqual(item["action"], "conflict")
                with self.assertRaises(installer.InstallError):
                    installer.apply_plan(target, self.package, "codex", actions, desired)
                self.assertTrue(runtime.exists() or runtime.is_symlink())

    def test_dependency_or_smoke_failure_removes_partial_runtime_and_rolls_back_files(self):
        failures = ("pip", "smoke")
        for failure in failures:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temporary:
                target = Path(temporary)
                actions, desired, _ = installer.installation_plan(
                    target, self.package, "codex"
                )
                if failure == "pip":
                    real_run = managed_runtime._run

                    def fail_pip(command, **kwargs):
                        if "pip" in command:
                            return subprocess.CompletedProcess(command, 1, "", "injected pip failure")
                        return real_run(command, **kwargs)

                    patcher = mock.patch.object(
                        managed_runtime, "_run", side_effect=fail_pip
                    )
                else:
                    patcher = mock.patch.object(
                        managed_runtime,
                        "_verify_operations",
                        side_effect=managed_runtime.ManagedRuntimeError(
                            "injected smoke failure"
                        ),
                    )
                with patcher, self.assertRaises(installer.InstallError):
                    installer.apply_plan(target, self.package, "codex", actions, desired)
                self.assertFalse((target / ".concorde/.venv").exists())
                self.assertFalse((target / ".concorde/install.json").exists())
                self.assertEqual(list(target.rglob("*")), [])

    def test_unmigrated_legacy_config_blocks_installation_instead_of_seeding_default(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            legacy = target / ".claude/reflections.config.json"
            legacy.parent.mkdir(parents=True)
            legacy.write_text('{"order": "newest-first"}\n')
            actions, desired, _ = installer.installation_plan(target, self.package, "codex")
            item = next(entry for entry in actions if entry["path"] == ".concorde/reflections/config.json")
            self.assertEqual(item["action"], "conflict")
            self.assertIn(".claude/reflections.config.json", item["reason"])
            self.assertIn("agent-asset sync", item["reason"])
            with self.assertRaises(installer.InstallError):
                installer.apply_plan(target, self.package, "codex", actions, desired)
            self.assertFalse((target / ".concorde/reflections/config.json").exists())
            self.assertTrue(legacy.is_file())

    def test_exact_existing_desired_bytes_are_adopted(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            desired = installer.desired_outputs(self.package, "codex")
            relative = ".agents/skills/concorde-plan/SKILL.md"
            path = target / relative
            path.parent.mkdir(parents=True)
            path.write_bytes(desired[relative][0])
            actions, _, _ = installer.installation_plan(target, self.package, "codex")
            action = next(item for item in actions if item["path"] == relative)
            self.assertEqual(action["action"], "adopt")

    def test_unowned_or_modified_owned_file_is_a_conflict(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            collision = target / ".agents/skills/concorde-plan/SKILL.md"
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
            self.assertTrue(any(item["action"] == "remove" and item["path"].startswith(".agents/skills/concorde-") for item in claude_actions))
            self.assertTrue(any(item["action"] == "create" and item["path"].startswith(".claude/skills/concorde-") for item in claude_actions))
            installer.apply_plan(target, self.package, "claude", claude_actions, claude_desired)
            self.assertFalse((target / ".agents/skills/concorde-plan/SKILL.md").exists())
            self.assertTrue((target / ".claude/skills/concorde-plan/SKILL.md").is_file())

    def test_update_removes_only_unchanged_owned_legacy_capability_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            legacy = target / ".concorde/framework/commands/concorde.plan.md"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("owned legacy\n")
            examples = target / ".concorde/framework/examples/standard_dev_loop.py"
            examples.parent.mkdir(parents=True)
            examples.write_text("owned example\n")
            receipt = {
                "schema_version": 1,
                "outputs": [
                    {
                        "path": legacy.relative_to(target).as_posix(),
                        "role": "command",
                        "sha256": installer._sha256(legacy.read_bytes()),
                    },
                    {
                        "path": examples.relative_to(target).as_posix(),
                        "role": "framework",
                        "sha256": installer._sha256(examples.read_bytes()),
                    },
                ],
            }
            receipt_path = target / ".concorde/install.json"
            receipt_path.parent.mkdir(exist_ok=True)
            receipt_path.write_text(json.dumps(receipt))
            actions, desired, _ = installer.installation_plan(target, self.package, "codex")
            removed = {
                item["path"] for item in actions if item["action"] == "remove"
            }
            self.assertEqual(
                removed,
                {
                    ".concorde/framework/commands/concorde.plan.md",
                    ".concorde/framework/examples/standard_dev_loop.py",
                },
            )
            installer.apply_plan(target, self.package, "codex", actions, desired)
            self.assertFalse(legacy.exists())
            self.assertFalse(examples.exists())

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
