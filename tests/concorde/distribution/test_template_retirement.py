"""Template relocation uses ordinary receipt ownership, never directory ownership."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from concorde.distribution import installation as installer
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

LEGACY = tuple(
    f"{installer.FRAMEWORK_ROOT}/templates/{name}-template.md"
    for name in ("module", "scenario", "plan", "tasks")
)


class TemplateRetirementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = installer.load_package(REPOSITORY_ROOT)

    def setUp(self):
        # Exercise the real package render/plan/apply/receipt transaction, but not
        # dependency acquisition. NativeInstallerTests covers actual provisioning.
        runtime = {
            "path": installer.RUNTIME["venv"],
            "role": "runtime",
            "sha256": "sha256:" + "0" * 64,
            "action": "unchanged",
        }
        for patcher in (
            mock.patch.object(installer, "plan_runtime", return_value=runtime),
            mock.patch.object(installer, "provision_runtime", return_value={}),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def seed_legacy(self, root, schema=2):
        outputs = []
        for relative in LEGACY:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"legacy {relative}\n")
            path.chmod(0o640)
            outputs.append(
                {
                    "path": relative,
                    "role": "framework",
                    "sha256": installer._sha256(path.read_bytes()),
                }
            )
        receipt = root / installer.RECEIPT_PATH
        receipt.write_text(json.dumps({"schema_version": schema, "outputs": outputs}))
        return receipt

    @verifies("scenario.distribution.template-ownership")
    def test_upgrade_retires_only_owned_files_and_repeats(self):
        for schema in (1, 2):
            with self.subTest(schema=schema), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                receipt = self.seed_legacy(root, schema)
                unowned = root / installer.FRAMEWORK_ROOT / "templates/user.md"
                unowned.write_bytes(b"user starter\n")
                actions, desired, _ = installer.installation_plan(root, self.package)
                self.assertEqual(
                    {a["path"] for a in actions if a["action"] == "remove"}, set(LEGACY)
                )
                self.assertFalse(
                    any(
                        p.startswith(f"{installer.FRAMEWORK_ROOT}/templates/")
                        for p in desired
                    )
                )
                installer.apply_plan(root, self.package, actions, desired)
                self.assertTrue(all(not (root / p).exists() for p in LEGACY))
                self.assertEqual(unowned.read_bytes(), b"user starter\n")
                self.assertFalse(
                    set(LEGACY)
                    & {o["path"] for o in json.loads(receipt.read_text())["outputs"]}
                )
                # Retained unowned legacy neighbors cannot become package inputs.
                installed = installer.load_package(root / installer.FRAMEWORK_ROOT)
                self.assertEqual(
                    installer.package_identity(installed),
                    installer.package_identity(self.package),
                )
                again, desired, _ = installer.installation_plan(root, self.package)
                self.assertEqual(
                    installer.apply_plan(root, self.package, again, desired),
                    "unchanged",
                )

    @verifies("scenario.distribution.template-ownership")
    def test_modified_symlinked_and_stale_retirement_blocks_without_writes(self):
        for kind in ("modified", "symlink", "parent-symlink", "stale"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                receipt = self.seed_legacy(root)
                before = receipt.read_bytes()
                path = root / LEGACY[0]
                if kind == "stale":
                    actions, desired, _ = installer.installation_plan(
                        root, self.package
                    )
                if kind == "symlink":
                    path.unlink()
                    path.symlink_to("missing")
                elif kind == "parent-symlink":
                    directory = path.parent
                    directory.rename(directory.with_name("user-templates"))
                    directory.symlink_to("user-templates", target_is_directory=True)
                else:
                    path.write_bytes(b"user modification\n")
                if kind != "stale":
                    actions, desired, _ = installer.installation_plan(
                        root, self.package
                    )
                    self.assertIn("conflict", {a["action"] for a in actions})
                with self.assertRaises(installer.InstallError):
                    installer.apply_plan(root, self.package, actions, desired)
                self.assertEqual(receipt.read_bytes(), before)
                self.assertFalse((root / ".pi").exists())
                if kind == "symlink":
                    self.assertTrue(path.is_symlink())
                elif kind == "parent-symlink":
                    self.assertTrue(path.parent.is_symlink())
                else:
                    self.assertEqual(path.read_bytes(), b"user modification\n")

    @verifies("scenario.distribution.template-ownership")
    def test_failed_apply_restores_retired_bytes_modes_and_receipt(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            receipt = self.seed_legacy(root)
            before = receipt.read_bytes()
            contents = {p: (root / p).read_bytes() for p in LEGACY}
            actions, desired, _ = installer.installation_plan(root, self.package)

            def fail_after_retirement(*args, **kwargs):
                self.assertTrue(all(not (root / p).exists() for p in LEGACY))
                raise installer.ManagedRuntimeError("injected runtime failure")

            with (
                mock.patch.object(
                    installer, "provision_runtime", side_effect=fail_after_retirement
                ),
                self.assertRaisesRegex(
                    installer.InstallError, "injected runtime failure"
                ),
            ):
                installer.apply_plan(root, self.package, actions, desired)
            self.assertEqual(receipt.read_bytes(), before)
            for relative, content in contents.items():
                self.assertEqual((root / relative).read_bytes(), content)
                self.assertEqual((root / relative).stat().st_mode & 0o777, 0o640)
            self.assertFalse((root / ".pi").exists())

    @verifies("scenario.distribution.template-ownership")
    def test_unowned_old_template_names_are_not_adopted_or_removed(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            receipt = self.seed_legacy(root)
            receipt.unlink()
            actions, desired, _ = installer.installation_plan(root, self.package)
            self.assertFalse(set(LEGACY) & {a["path"] for a in actions})
            installer.apply_plan(root, self.package, actions, desired)
            self.assertTrue(all((root / p).is_file() for p in LEGACY))
            self.assertFalse(
                set(LEGACY)
                & {o["path"] for o in json.loads(receipt.read_text())["outputs"]}
            )
