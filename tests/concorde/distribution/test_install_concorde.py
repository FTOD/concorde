from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from concorde.distribution import installation as installer
from concorde.distribution import managed_runtime  # noqa: E402
from concorde.operations.catalog import PUBLIC_OPERATIONS
from concorde.spec.verification import verifies  # noqa: E402
from tests.concorde.support.managed_runtime import (
    create_langgraph_index,
    runtime_install_environment,
)
from tests.concorde.support.paths import REPOSITORY_ROOT


class NativeInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package = installer.load_package(REPOSITORY_ROOT)
        cls.runtime_temporary = tempfile.TemporaryDirectory()
        index = create_langgraph_index(Path(cls.runtime_temporary.name))
        # The whole mapping is replaced: the in-process installer and the launchers it
        # verifies inherit os.environ, which must carry no ambient candidate selection.
        cls.runtime_environment = mock.patch.dict(
            os.environ, runtime_install_environment(index), clear=True
        )
        cls.runtime_environment.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.runtime_environment.stop()
        cls.runtime_temporary.cleanup()

    def test_parser_previews_by_default(self):
        arguments = installer.create_parser().parse_args(["--target", "sample"])
        self.assertFalse(arguments.apply)
        self.assertEqual(arguments.checkout, str(REPOSITORY_ROOT))

    def test_other_package_schema_or_client_is_rejected(self):
        for changes in (
            {"schema_version": 4},
            {"client": "codex"},
        ):
            with (
                self.subTest(changes=changes),
                tempfile.TemporaryDirectory() as temporary,
            ):
                root = Path(temporary)
                (root / "concorde.json").write_text(
                    json.dumps({**self.package.manifest, **changes})
                )
                with self.assertRaises(installer.InstallError):
                    installer.load_package(root)

    @verifies(
        "scenario.distribution.install-pi-session",
        "scenario.distribution.install-unknown-option",
    )
    def test_unknown_option_is_refused_before_creating_target(self):
        for option in (["--client", "codex"], ["--bogus"], ["--apply", "--force"]):
            with (
                self.subTest(option=option),
                tempfile.TemporaryDirectory() as temporary,
                mock.patch.object(
                    installer,
                    "load_package",
                    side_effect=AssertionError("the package must not be read"),
                ),
            ):
                target = Path(temporary) / "absent"
                with self.assertRaises(SystemExit) as refused:
                    installer.main(["--target", str(target), *option])
                self.assertNotEqual(0, refused.exception.code)
                self.assertFalse(target.exists())

    def test_manifest_is_single_profile_and_inventory_authority(self):
        self.assertEqual(self.package.version, "8.0.0")
        self.assertEqual(self.package.manifest["architecture_profile"], 16)
        self.assertEqual(self.package.manifest["workspace_protocol"], 16)
        self.assertEqual(
            self.package.manifest["runtime"]["venv"],
            ".concorde/.venv",
        )
        self.assertNotIn("viewer", self.package.manifest)

    def test_desired_outputs_are_pi_only(self):
        outputs = installer.desired_outputs(self.package)
        self.assertIn(".concorde/framework/src/concorde/distribution/cli.py", outputs)
        self.assertIn(".concorde/framework/src/concorde/spec/validation.py", outputs)
        self.assertIn(".concorde/framework/docsite/docusaurus.config.ts", outputs)
        self.assertIn(
            ".concorde/framework/docsite/scaffold/deploy-docsite.yml", outputs
        )
        self.assertNotIn(".concorde/framework/docsite/site.json", outputs)
        self.assertNotIn(".concorde/framework/docsite/sidebars.docs.ts", outputs)
        self.assertTrue(
            all(
                "node_modules" not in path and "/build/" not in path
                for path in outputs
                if path.startswith(".concorde/framework/docsite/")
            )
        )
        self.assertTrue(
            all(
                not path.startswith(".concorde/framework/docsite/tests/repository/")
                for path in outputs
            )
        )
        self.assertIn(".pi/extensions/concorde-session.ts", outputs)
        self.assertIn(".concorde/framework/scripts/requirements.lock", outputs)
        self.assertIn(".concorde/framework/scripts/run-operation.py", outputs)
        self.assertIn(".concorde/framework/pi/package-lock.json", outputs)
        for relative in (
            "generated/native/context-assessor.md",
            "generated/native/planner.md",
            "generated/native/task-author.md",
            "generated/native/programmer.md",
            "generated/native/spec-reviewer.md",
            "generated/native/code-reviewer.md",
            "pi/workflows/review.js",
            "pi/native-review-host.mjs",
            "pi/workflows/plan.js",
            "pi/native-plan-host.mjs",
            "pi/native-preflight.ts",
            "pi/extensions/concorde-native-plan.ts",
            "prompts/native/context-assessor.md",
            "pi/extensions/concorde-native-context.ts",
            "pi/extensions/concorde-native-child.ts",
            "src/concorde/harness/native_driver.py",
            "pi/native-host-step.mjs",
        ):
            self.assertIn(".concorde/framework/" + relative, outputs)
        self.assertNotIn(".pi/agents/concorde-context-assessor.md", outputs)

        self.assertIn(".concorde/framework/generated/build-manifest.json", outputs)
        self.assertEqual("extension", outputs[".pi/extensions/concorde-session.ts"][1])
        self.assertTrue(
            all(
                not path.startswith(("presets/", "extensions/", "bundles/"))
                for path in outputs
            )
        )

    @verifies(
        "scenario.distribution.install-preview",
        "scenario.distribution.install-apply",
        "scenario.distribution.runtime-plan",
        "scenario.distribution.runtime-provision",
        "scenario.distribution.template-ownership",
    )
    def test_empty_target_preview_apply_and_repeat_are_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            actions, desired, _ = installer.installation_plan(target, self.package)
            self.assertTrue(actions)
            self.assertEqual({item["action"] for item in actions}, {"create"})
            runtime_action = next(item for item in actions if item["role"] == "runtime")
            self.assertEqual(runtime_action["path"], ".concorde/.venv")
            self.assertEqual(
                installer.apply_plan(target, self.package, actions, desired),
                "installed",
            )
            framework = target / installer.FRAMEWORK_ROOT
            self.assertFalse((framework / "templates").exists())
            for relative in (
                "protocol/templates/module.md",
                "protocol/templates/scenario.md",
            ):
                self.assertEqual(
                    (framework / relative).read_bytes(),
                    (REPOSITORY_ROOT / relative).read_bytes(),
                )
            second, desired_again, _ = installer.installation_plan(target, self.package)
            self.assertEqual(
                {item["action"] for item in second},
                {"unchanged", "preserve"},
            )
            self.assertEqual(
                installer.apply_plan(target, self.package, second, desired_again),
                "unchanged",
            )
            receipt = json.loads((target / ".concorde/install.json").read_text())
            self.assertEqual(receipt["schema_version"], 2)
            self.assertEqual(receipt["client"], "pi")
            self.assertEqual(receipt["runtime"]["path"], ".concorde/.venv")
            self.assertEqual(
                receipt["runtime"]["verified_operations"],
                list(PUBLIC_OPERATIONS),
            )
            self.assertTrue(
                (target / ".concorde/.venv/.concorde-runtime.json").is_file()
            )
            self.assertTrue(
                (
                    target
                    / ".concorde/.venv/share/concorde/pi/node_modules/typebox/build/index.mjs"
                ).is_file()
            )
            self.assertNotIn("viewer", receipt["runtime"])
            self.assertFalse((target / "node_modules").exists())
            self.assertFalse((target / "package.json").exists())
            self.assertFalse((target / "package-lock.json").exists())
            project_defaults = sum(
                role == "project-default" for _, role in desired.values()
            )
            self.assertEqual(len(receipt["outputs"]), len(desired) - project_defaults)
            self.assertNotIn(
                "project-default", {item["role"] for item in receipt["outputs"]}
            )

    @verifies("scenario.distribution.install-apply")
    def test_local_pi_node_modules_are_neither_deployed_nor_inspected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("concorde.json", "LICENSE", "README.md"):
                (root / name).write_text(name + "\n")
            for directory in (
                "operations",
                "prompts",
                "protocol",
                "src",
                "pi",
                "scripts",
            ):
                (root / directory).mkdir()
            for name in (
                "concorde.py",
                "concorde.ps1",
                "concorde.sh",
                "issues.py",
                "install-concorde.py",
                "requirements.lock",
                "run-operation.py",
            ):
                (root / "scripts" / name).write_text("# script\n")
            (root / "pi/package.json").write_text("{}\n")
            entry = root / "pi/node_modules/typebox/build/index.mjs"
            entry.parent.mkdir(parents=True)
            entry.write_text("// typebox\n")
            (root / "pi/node_modules/.bin").mkdir()
            (root / "pi/node_modules/.bin/typebox").symlink_to(
                "../typebox/build/index.mjs"
            )
            package = installer.Package(root, self.package.manifest)
            with mock.patch.object(installer, "template_files", return_value={}):
                desired = installer._package_files(package)
                self.assertIn(f"{installer.FRAMEWORK_ROOT}/pi/package.json", desired)
                self.assertEqual(
                    [], [path for path in desired if "node_modules" in path]
                )
                (root / "pi/link.mjs").symlink_to("package.json")
                with self.assertRaisesRegex(
                    installer.InstallError, "may not contain symlinks"
                ):
                    installer._package_files(package)

    @verifies("scenario.distribution.install-apply")
    def test_existing_project_defaults_are_preserved_and_not_owned(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            config = target / ".concorde/issues/.gitignore"
            config.parent.mkdir(parents=True)
            config.write_text("# developer custom\n")
            legacy = target / ".concorde/reflections/pending/R-001.md"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("Unresolved historical report\n")
            actions, desired, _ = installer.installation_plan(target, self.package)
            item = next(
                entry
                for entry in actions
                if entry["path"] == ".concorde/issues/.gitignore"
            )
            self.assertEqual(item["action"], "preserve")
            installer.apply_plan(target, self.package, actions, desired)
            self.assertEqual("# developer custom\n", config.read_text())
            self.assertEqual("Unresolved historical report\n", legacy.read_text())
            paths = {
                entry["path"]
                for entry in json.loads(
                    (target / ".concorde/install.json").read_text()
                )["outputs"]
            }
            self.assertNotIn(".concorde/reflections/config.json", paths)
            self.assertNotIn(".concorde/reflections/index.json", paths)
            self.assertNotIn(".concorde/reflections/.gitignore", paths)
            self.assertNotIn(".concorde/topology-proposals/.gitignore", paths)
            self.assertNotIn(".concorde/issues/.gitignore", paths)
            self.assertFalse((target / ".concorde/reflections/index.json").exists())
            self.assertIn(".concorde/protocol/manifest.json", paths)

    @verifies(
        "scenario.distribution.runtime-plan", "scenario.distribution.runtime-provision"
    )
    def test_target_root_venv_is_ignored_and_managed_runtime_rebuild_removes_obsolete_files(
        self,
    ):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            user_sentinel = target / ".venv/user-package.txt"
            user_sentinel.parent.mkdir()
            user_sentinel.write_text("user-owned\n", encoding="utf-8")
            before = user_sentinel.read_bytes()
            actions, desired, _ = installer.installation_plan(target, self.package)
            installer.apply_plan(target, self.package, actions, desired)
            obsolete = target / ".concorde/.venv/obsolete-package.txt"
            obsolete.write_text("obsolete\n", encoding="utf-8")
            marker = target / ".concorde/.venv/.concorde-runtime.json"
            value = json.loads(marker.read_text(encoding="utf-8"))
            value["requirements_sha256"] = "sha256:" + "0" * 64
            marker.write_text(json.dumps(value), encoding="utf-8")

            rebuild, desired_again, _ = installer.installation_plan(
                target, self.package
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
                installer.apply_plan(target, self.package, rebuild, desired_again)

            self.assertEqual(user_sentinel.read_bytes(), before)
            self.assertFalse(obsolete.exists())
            self.assertTrue(marker.is_file())

    @verifies("scenario.distribution.runtime-plan")
    def test_unowned_or_symlinked_managed_runtime_is_a_nonmutating_conflict(self):
        for symlink in (False, True):
            with (
                self.subTest(symlink=symlink),
                tempfile.TemporaryDirectory() as temporary,
            ):
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
                actions, desired, _ = installer.installation_plan(target, self.package)
                item = next(entry for entry in actions if entry["role"] == "runtime")
                self.assertEqual(item["action"], "conflict")
                with self.assertRaises(installer.InstallError):
                    installer.apply_plan(target, self.package, actions, desired)
                self.assertTrue(runtime.exists() or runtime.is_symlink())

    @verifies("scenario.distribution.runtime-provision-failure")
    def test_dependency_or_smoke_failure_removes_partial_runtime_and_rolls_back_files(
        self,
    ):
        failures = ("pip", "pi-install", "smoke", "pi-verify")
        for failure in failures:
            with (
                self.subTest(failure=failure),
                tempfile.TemporaryDirectory() as temporary,
            ):
                target = Path(temporary)
                actions, desired, _ = installer.installation_plan(target, self.package)
                if failure == "pip":
                    real_run = managed_runtime._run

                    def fail_pip(command, **kwargs):
                        if "pip" in command:
                            return subprocess.CompletedProcess(
                                command, 1, "", "injected pip failure"
                            )
                        return real_run(command, **kwargs)

                    patcher = mock.patch.object(
                        managed_runtime, "_run", side_effect=fail_pip
                    )
                elif failure == "pi-install":
                    real_run = managed_runtime._run

                    def fail_npm(command, **kwargs):
                        if command and command[0] == "npm" and "ci" in command:
                            return subprocess.CompletedProcess(
                                command, 1, "", "injected npm failure"
                            )
                        return real_run(command, **kwargs)

                    patcher = mock.patch.object(
                        managed_runtime, "_run", side_effect=fail_npm
                    )
                elif failure == "smoke":
                    patcher = mock.patch.object(
                        managed_runtime,
                        "_verify_operations",
                        side_effect=managed_runtime.ManagedRuntimeError(
                            "injected smoke failure"
                        ),
                    )
                else:
                    patcher = mock.patch.object(
                        managed_runtime,
                        "_verify_pi",
                        side_effect=managed_runtime.ManagedRuntimeError(
                            "injected Pi verification failure"
                        ),
                    )
                with patcher, self.assertRaises(installer.InstallError):
                    installer.apply_plan(target, self.package, actions, desired)
                self.assertFalse((target / ".concorde/.venv").exists())
                self.assertFalse((target / ".concorde/install.json").exists())
                self.assertEqual(list(target.rglob("*")), [])

    @verifies("scenario.distribution.runtime-provision-failure")
    def test_missing_npm_blocks_pi_install_and_rolls_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            actions, desired, _ = installer.installation_plan(target, self.package)
            real_run = managed_runtime._run

            def missing_npm(command, **kwargs):
                if command and command[0] == "npm":
                    raise FileNotFoundError("npm")
                return real_run(command, **kwargs)

            with (
                mock.patch.object(managed_runtime, "_run", side_effect=missing_npm),
                self.assertRaisesRegex(
                    installer.InstallError, "npm is required to install the Pi"
                ),
            ):
                installer.apply_plan(target, self.package, actions, desired)
            self.assertFalse((target / ".concorde/.venv").exists())
            self.assertFalse((target / ".concorde/install.json").exists())

    @staticmethod
    def files(target: Path, *, runtime: bool = True) -> dict:
        return {
            path.relative_to(target).as_posix(): (
                path.read_bytes(),
                path.stat().st_mode & 0o777,
            )
            for path in target.rglob("*")
            if path.is_file()
            and not path.is_symlink()
            and (runtime or not path.is_relative_to(target / ".concorde/.venv"))
        }

    @verifies("scenario.distribution.install-apply-rollback")
    def test_a_failure_after_the_runtime_was_created_removes_that_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary).resolve()
            agents = target / "AGENTS.md"
            agents.write_bytes(b"# Developer rules\n")
            agents.chmod(0o600)
            before = self.files(target)
            actions, desired, _ = installer.installation_plan(target, self.package)
            runtime = next(item for item in actions if item["role"] == "runtime")
            self.assertEqual("create", runtime["action"])
            real_identity = installer.package_identity
            provisioned = []
            real_provision = installer.provision_runtime

            def provision(*args, **kwargs):
                record = real_provision(*args, **kwargs)
                provisioned.append((target / ".concorde/.venv").is_dir())
                return record

            def drifting(package):
                identity = real_identity(package)
                if provisioned:
                    identity = {**identity, "digest": "sha256:" + "1" * 64}
                return identity

            with (
                mock.patch.object(
                    installer, "provision_runtime", side_effect=provision
                ),
                mock.patch.object(installer, "package_identity", side_effect=drifting),
                self.assertRaisesRegex(installer.InstallError, "package changed"),
            ):
                installer.apply_plan(target, self.package, actions, desired)
            self.assertEqual([True], provisioned)
            self.assertFalse((target / ".concorde/.venv").exists())
            self.assertFalse((target / installer.RECEIPT_PATH).exists())
            self.assertEqual(before, self.files(target))

    @verifies("scenario.distribution.runtime-rebuild-failure")
    def test_a_failed_rebuild_leaves_no_runtime_and_restores_files_and_receipt(self):
        from concorde.distribution.local_installation import verify_installation

        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary).resolve()
            actions, desired, _ = installer.installation_plan(target, self.package)
            installer.apply_plan(target, self.package, actions, desired)
            # An owned output the next apply removes, so its rollback has a file to restore.
            receipt_path = target / installer.RECEIPT_PATH
            receipt = json.loads(receipt_path.read_text())
            retired = target / ".concorde/framework/retired/old.txt"
            retired.parent.mkdir(parents=True)
            retired.write_bytes(b"retired owned bytes\n")
            retired.chmod(0o600)
            receipt["outputs"].append(
                {
                    "path": retired.relative_to(target).as_posix(),
                    "role": "framework",
                    "sha256": installer._sha256(retired.read_bytes()),
                }
            )
            receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True))
            marker = target / ".concorde/.venv" / managed_runtime.MARKER_NAME
            value = json.loads(marker.read_text(encoding="utf-8"))
            value["requirements_sha256"] = "sha256:" + "0" * 64
            marker.write_text(json.dumps(value), encoding="utf-8")
            rebuild, desired, _ = installer.installation_plan(target, self.package)
            by_path = {item["path"]: item["action"] for item in rebuild}
            self.assertEqual("rebuild", by_path[".concorde/.venv"])
            self.assertEqual("remove", by_path[retired.relative_to(target).as_posix()])
            files = self.files(target, runtime=False)
            with (
                mock.patch.object(
                    managed_runtime,
                    "_verify_operations",
                    side_effect=managed_runtime.ManagedRuntimeError(
                        "injected rebuild verification failure"
                    ),
                ),
                self.assertRaisesRegex(installer.InstallError, "injected rebuild"),
            ):
                installer.apply_plan(target, self.package, rebuild, desired)
            # The previous runtime is gone, the one being built is removed, nothing is marked.
            self.assertFalse((target / ".concorde/.venv").exists())
            self.assertEqual([], list(target.rglob(managed_runtime.MARKER_NAME)))
            # Files and receipt are restored, the runtime is not.
            self.assertEqual(files, self.files(target, runtime=False))
            with self.assertRaisesRegex(
                installer.InstallError, "managed runtime is missing or stale"
            ):
                verify_installation(target)
            # A fresh plan installs again once the cause is gone.
            again, desired, _ = installer.installation_plan(target, self.package)
            self.assertEqual(
                "create",
                next(item for item in again if item["role"] == "runtime")["action"],
            )
            installer.apply_plan(target, self.package, again, desired)
            self.assertTrue(marker.is_file())

    @verifies("scenario.distribution.runtime-plan")
    def test_pi_lock_marker_drift_requires_managed_runtime_rebuild(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            actions, desired, _ = installer.installation_plan(target, self.package)
            installer.apply_plan(target, self.package, actions, desired)
            marker = target / ".concorde/.venv/.concorde-runtime.json"
            value = json.loads(marker.read_text(encoding="utf-8"))
            value["pi_lock_sha256"] = "sha256:" + "0" * 64
            marker.write_text(json.dumps(value), encoding="utf-8")

            rebuild, _, _ = installer.installation_plan(target, self.package)
            runtime = next(item for item in rebuild if item["role"] == "runtime")
            self.assertEqual(runtime["action"], "rebuild")

    @verifies(
        "scenario.distribution.runtime-plan", "scenario.distribution.runtime-provision"
    )
    def test_marker_schema_four_uses_operations_and_old_schema_requires_owned_rebuild(
        self,
    ):
        spec = managed_runtime.load_runtime_spec(REPOSITORY_ROOT, self.package.manifest)
        self.assertEqual(11, len(spec.operations))
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw)
            runtime = target / spec.venv
            runtime.mkdir(parents=True)
            managed_runtime._write_marker(runtime, spec, "3.11.0")
            marker_path = runtime / managed_runtime.MARKER_NAME
            marker = json.loads(marker_path.read_text())
            self.assertEqual(4, marker["schema_version"])
            self.assertEqual(list(spec.operations), marker["verified_operations"])
            with (
                mock.patch.object(managed_runtime, "_healthy", return_value=True),
                mock.patch.object(managed_runtime, "_verify_pi"),
            ):
                self.assertEqual(
                    "unchanged",
                    managed_runtime.plan_runtime(target, spec, {})["action"],
                )
                marker["schema_version"] = 3
                marker_path.write_text(json.dumps(marker))
                before = marker_path.read_bytes()
                self.assertEqual(
                    "conflict", managed_runtime.plan_runtime(target, spec, {})["action"]
                )
                self.assertEqual(
                    "rebuild",
                    managed_runtime.plan_runtime(
                        target, spec, {"runtime": {"path": spec.venv}}
                    )["action"],
                )
                self.assertEqual(before, marker_path.read_bytes())

    def test_exact_existing_desired_bytes_are_adopted(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            desired = installer.desired_outputs(self.package)
            relative = ".pi/extensions/concorde-session.ts"
            path = target / relative
            path.parent.mkdir(parents=True)
            path.write_bytes(desired[relative][0])
            actions, _, _ = installer.installation_plan(target, self.package)
            action = next(item for item in actions if item["path"] == relative)
            self.assertEqual(action["action"], "adopt")

    def test_unowned_or_modified_owned_file_is_a_conflict(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            collision = target / ".pi/extensions/concorde-session.ts"
            collision.parent.mkdir(parents=True)
            collision.write_text("developer file\n")
            actions, _, _ = installer.installation_plan(target, self.package)
            item = next(
                entry
                for entry in actions
                if entry["path"] == collision.relative_to(target).as_posix()
            )
            self.assertEqual(item["action"], "conflict")

    @verifies("scenario.distribution.install-pi-session")
    def test_desired_pi_outputs_project_the_session_shim(self):
        outputs = installer.desired_outputs(self.package)
        content, role = outputs[".pi/extensions/concorde-session.ts"]
        self.assertEqual("extension", role)
        shim = content.decode("utf-8")
        self.assertIn(
            'from "../../.concorde/framework/pi/extensions/concorde-session.ts"', shim
        )
        self.assertIn('".concorde/framework/scripts/run-operation.py"', shim)
        self.assertIn('"explicit_request_only": false', shim)
        self.assertIn(".concorde/framework/pi/extensions/concorde-session.ts", outputs)
        self.assertEqual("protocol-guidance", outputs["AGENTS.md"][1])
        self.assertIn(b"Read and follow", outputs["AGENTS.md"][0])

    @verifies("scenario.distribution.install-upgrade")
    def test_update_removes_only_unchanged_superseded_owned_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            superseded = target / ".concorde/framework/prompts/removed/old.md"
            superseded.parent.mkdir(parents=True)
            superseded.write_text("owned old prompt\n")
            receipt = {
                "schema_version": 2,
                "outputs": [
                    {
                        "path": superseded.relative_to(target).as_posix(),
                        "role": "framework",
                        "sha256": installer._sha256(superseded.read_bytes()),
                    },
                ],
            }
            receipt_path = target / ".concorde/install.json"
            receipt_path.parent.mkdir(exist_ok=True)
            receipt_path.write_text(json.dumps(receipt))
            actions, desired, _ = installer.installation_plan(target, self.package)
            removed = {item["path"] for item in actions if item["action"] == "remove"}
            self.assertEqual(removed, {".concorde/framework/prompts/removed/old.md"})
            installer.apply_plan(target, self.package, actions, desired)
            self.assertFalse(superseded.exists())

    @verifies("scenario.distribution.install-receipt-schema")
    def test_receipt_of_another_schema_is_refused(self):
        record = {"path": ".pi/extensions/concorde-session.ts", "role": "extension"}
        record["sha256"] = "sha256:" + "0" * 64
        for receipt, reason in (
            ({"schema_version": 1, "outputs": []}, "unsupported"),
            ({"schema_version": "2", "outputs": []}, "unsupported"),
            ({"schema_version": 2, "outputs": [record, record]}, "repeats output"),
            (
                {"schema_version": 2, "outputs": [{**record, "path": "AGENTS.md"}]},
                "whole file",
            ),
        ):
            with (
                self.subTest(reason=reason, receipt=receipt),
                tempfile.TemporaryDirectory() as temporary,
            ):
                target = Path(temporary).resolve()
                receipt_path = target / ".concorde/install.json"
                receipt_path.parent.mkdir()
                receipt_path.write_text(json.dumps(receipt))
                before = {p: p.read_bytes() for p in target.rglob("*") if p.is_file()}
                with self.assertRaisesRegex(installer.InstallError, reason):
                    installer.installation_plan(target, self.package)
                with contextlib.redirect_stdout(io.StringIO()) as printed:
                    code = installer.main(
                        ["--target", str(target), "--apply", "--format", "json"]
                    )
                self.assertEqual(3, code)
                self.assertEqual("failed", json.loads(printed.getvalue())["status"])
                self.assertEqual(
                    before,
                    {p: p.read_bytes() for p in target.rglob("*") if p.is_file()},
                )

    def test_safe_relative_rejects_escape_absolute_and_backslash(self):
        for value in ("../escape", "/absolute", "bad\\path"):
            with self.subTest(value=value), self.assertRaises(installer.InstallError):
                installer._safe_relative(value, "fixture")

    def test_mid_apply_failure_removes_created_files_and_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            actions, desired, _ = installer.installation_plan(target, self.package)
            original = installer.tempfile.NamedTemporaryFile
            calls = 0

            def injected(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError("injected write failure")
                return original(*args, **kwargs)

            with mock.patch.object(
                installer.tempfile, "NamedTemporaryFile", side_effect=injected
            ):
                with self.assertRaisesRegex(OSError, "injected write failure"):
                    installer.apply_plan(target, self.package, actions, desired)
            self.assertEqual(list(target.rglob("*")), [])

    @verifies("scenario.distribution.runtime-provision")
    def test_runtime_verification_runs_the_launcher_inside_the_managed_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary).resolve()
            actions, desired, _ = installer.installation_plan(target, self.package)
            real_run = managed_runtime._run
            checks: list[list[str]] = []

            def record(command, **kwargs):
                if "--runtime-check" in command:
                    checks.append(list(command))
                return real_run(command, **kwargs)

            with mock.patch.object(managed_runtime, "_run", side_effect=record):
                installer.apply_plan(target, self.package, actions, desired)
            python = managed_runtime.runtime_python(target / ".concorde/.venv")
            self.assertEqual(
                [command[2] for command in checks],
                list(PUBLIC_OPERATIONS),
            )
            # The check exercises the runtime being verified, never the installer's interpreter.
            self.assertEqual({command[0] for command in checks}, {str(python)})
            self.assertNotEqual(str(python), sys.executable)

    @verifies("scenario.distribution.runtime-provision-failure")
    def test_runtime_check_outside_the_managed_runtime_fails_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary).resolve()
            actions, desired, _ = installer.installation_plan(target, self.package)
            real_run = managed_runtime._run

            def elsewhere(command, **kwargs):
                if "--runtime-check" in command:
                    # The check answers from the installer's interpreter, which also carries
                    # LangGraph, instead of from the runtime under verification.
                    command = [sys.executable, *command[1:]]
                return real_run(command, **kwargs)

            with (
                mock.patch.object(managed_runtime, "_run", side_effect=elsewhere),
                self.assertRaisesRegex(
                    installer.InstallError, "outside the managed runtime"
                ),
            ):
                installer.apply_plan(target, self.package, actions, desired)
            self.assertEqual(list(target.rglob("*")), [])

    @verifies(
        "scenario.distribution.launcher-managed-runtime",
        "scenario.distribution.launcher-missing-runtime",
    )
    def test_installed_launcher_reexecutes_inside_the_managed_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary).resolve()
            actions, desired, _ = installer.installation_plan(target, self.package)
            installer.apply_plan(target, self.package, actions, desired)
            launcher = target / ".concorde/framework/scripts/run-operation.py"
            runtime = target / ".concorde/.venv"

            def check(*interpreter: str) -> subprocess.CompletedProcess:
                return subprocess.run(
                    [
                        *interpreter,
                        str(launcher),
                        "concorde-context-solve",
                        "--runtime-check",
                    ],
                    cwd=target,
                    capture_output=True,
                    text=True,
                )

            # The internal launcher may start with ambient `python3`, which need not carry
            # LangGraph at all; `-S` gives such an interpreter.
            for started_with in ([sys.executable], [sys.executable, "-S"]):
                with self.subTest(started_with=started_with):
                    process = check(*started_with)
                    self.assertEqual(
                        0, process.returncode, process.stderr or process.stdout
                    )
                    payload = json.loads(process.stdout)
                    self.assertEqual(Path(payload["prefix"]).resolve(), runtime)
                    self.assertEqual(
                        payload["python"], str(managed_runtime.runtime_python(runtime))
                    )

            # Without the installer's verified runtime the launcher keeps the interpreter that
            # started it and names the missing runtime instead of failing inside the host.
            (runtime / managed_runtime.MARKER_NAME).unlink()
            process = check(sys.executable, "-S")
            self.assertEqual(3, process.returncode, process.stderr or process.stdout)
            result = json.loads(process.stdout)
            self.assertEqual("blocked", result["status"])
            self.assertEqual("missing_runtime", result["errors"][0]["code"])
            self.assertIn(sys.executable, result["errors"][0]["message"])
            process = check(sys.executable)
            self.assertEqual(0, process.returncode, process.stderr or process.stdout)
            self.assertNotEqual(
                Path(json.loads(process.stdout)["prefix"]).resolve(), runtime
            )


if __name__ == "__main__":
    unittest.main()
