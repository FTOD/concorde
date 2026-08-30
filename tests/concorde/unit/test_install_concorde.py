from __future__ import annotations

import importlib.util
import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from tests.concorde.support.paths import REPOSITORY_ROOT


INSTALLER_PATH = REPOSITORY_ROOT / "scripts/install-concorde.py"
SPEC = importlib.util.spec_from_file_location("concorde_installer", INSTALLER_PATH)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallerScaffoldTests(unittest.TestCase):
    def test_public_constants_and_parser_exist(self):
        self.assertEqual(installer.SPECIFY_VERSION, "0.16.4")
        self.assertEqual(installer.BUNDLE_ID, "concorde-bundle")
        arguments = installer.parser().parse_args(["--target", "sample", "--integration", "codex", "--preview"])
        self.assertEqual(arguments.target, "sample")
        self.assertEqual(arguments.integration, "codex")
        self.assertTrue(arguments.preview)


class InstallerDecisionTests(unittest.TestCase):
    def pointer(self, **overrides):
        value = {
            "schema_version": "1.0",
            "version": "0.5.0",
            "tag": "v0.5.0",
            "repository": "https://github.com/FTOD/concorde",
            "base_url": "https://github.com/FTOD/concorde/releases/download/v0.5.0",
            "speckit_version": ">=0.16.4,<0.16.5",
            "bundle_id": "concorde-bundle",
            "catalogs": {
                "extensions": "https://github.com/FTOD/concorde/releases/download/v0.5.0/extensions.json",
                "presets": "https://github.com/FTOD/concorde/releases/download/v0.5.0/presets.json",
                "bundles": "https://github.com/FTOD/concorde/releases/download/v0.5.0/bundles.json",
            },
            "archives": {},
        }
        value.update(overrides)
        return value

    def test_version_and_checkout_are_mutually_exclusive(self):
        with self.assertRaises(SystemExit):
            installer.parser().parse_args(["--version", "0.5.0", "--checkout", "."])

    def test_release_pointer_accepts_supported_public_release(self):
        release = installer.validate_release_pointer(self.pointer(), expected_version="0.5.0")
        self.assertEqual(release.version, "0.5.0")
        self.assertEqual(release.catalogs["bundles"], self.pointer()["catalogs"]["bundles"])

    def test_release_pointer_rejects_schema_version_bundle_and_urls(self):
        bad_values = [
            self.pointer(schema_version="2.0"),
            self.pointer(bundle_id="other"),
            self.pointer(catalogs={"extensions": "https://example.test/extensions.json"}),
            self.pointer(
                catalogs={
                    "extensions": "http://example.test/extensions.json",
                    "presets": "https://example.test/presets.json",
                    "bundles": "https://example.test/bundles.json",
                }
            ),
            self.pointer(version="0.3.0", tag="v0.3.0"),
        ]
        for value in bad_values:
            with self.subTest(value=value), self.assertRaises(installer.InstallationError) as raised:
                installer.validate_release_pointer(value, expected_version="0.5.0")
            self.assertEqual(raised.exception.exit_code, installer.EXIT_RELEASE)

    def test_target_classification(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            absent = base / "absent"
            empty = base / "empty"
            empty.mkdir()
            non_project = base / "non-project"
            non_project.mkdir()
            (non_project / "notes.md").write_text("notes\n", encoding="utf-8")
            project = base / "project"
            (project / ".specify").mkdir(parents=True)
            (project / ".specify/init-options.json").write_text("{}\n", encoding="utf-8")

            self.assertEqual(installer.classify_target(absent), "absent")
            self.assertEqual(installer.classify_target(empty), "empty")
            self.assertEqual(installer.classify_target(non_project), "non-project")
            self.assertEqual(installer.classify_target(project), "project")

    def test_catalog_state_is_missing_current_or_replace(self):
        desired = "https://example.test/extensions.json"
        self.assertEqual(installer.catalog_state("extension", {}, desired), "missing")
        current = {"catalogs": [{"name": "concorde", "url": desired, "install_allowed": True}]}
        stale = {"catalogs": [{"name": "concorde", "url": "https://old.test/extensions.json", "install_allowed": True}]}
        unrelated = {"catalogs": [{"name": "team", "url": desired, "install_allowed": True}]}
        self.assertEqual(installer.catalog_state("extension", current, desired), "current")
        self.assertEqual(installer.catalog_state("extension", stale, desired), "replace")
        self.assertEqual(installer.catalog_state("extension", unrelated, desired), "missing")

        bundle = {
            "catalogs": [
                {"id": "concorde", "url": desired, "install_policy": "install-allowed"}
            ]
        }
        self.assertEqual(installer.catalog_state("bundle", bundle, desired), "current")

    def test_action_selection(self):
        self.assertEqual(installer.select_action(None, "0.5.0"), "install")
        self.assertEqual(installer.select_action("0.5.0", "0.5.0"), "already-current")
        self.assertEqual(installer.select_action("0.3.0", "0.5.0"), "update")

    def test_staged_failure_never_claims_success(self):
        error = installer.InstallationError(
            installer.EXIT_SPECIFY,
            "bundle-install",
            "native install failed",
            "Review the Spec Kit diagnostic and retry.",
            "project initialized; catalogs registered; bundle absent",
        )
        rendered = installer.render_failure(error)
        self.assertIn("FAILED", rendered)
        self.assertIn("bundle-install", rendered)
        self.assertIn("Remediation", rendered)
        self.assertIn("Residual state", rendered)
        self.assertNotIn("SUCCESS", rendered)

    def test_bundle_version_reads_native_list_shape(self):
        self.assertIsNone(installer.installed_bundle_version([]))
        value = [{"bundle_id": "concorde-bundle", "version": "0.5.0"}]
        self.assertEqual(installer.installed_bundle_version(value), "0.5.0")
        with self.assertRaises(installer.InstallationError):
            installer.installed_bundle_version(json.loads('{"unexpected": true}'))

    def test_agent_asset_operation_parses_success_and_rejects_conflict(self):
        success = {
            "schema_version": 1,
            "operation": "agent-assets.verify",
            "target": "codex",
            "status": "success",
            "artifacts": [".codex/agents/reflection_investigator.toml"],
            "findings": [],
            "result": {"integration": "codex", "outputs": [".codex/agents/reflection_investigator.toml"]},
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            launcher = root / ".specify/extensions/concorde/scripts/python/concorde.py"
            launcher.parent.mkdir(parents=True)
            launcher.write_text("# fixture\n")
            completed = mock.Mock(returncode=0, stdout=json.dumps(success), stderr="")
            with mock.patch.object(installer.subprocess, "run", return_value=completed) as called:
                payload = installer.run_agent_assets(root, "codex", "verify", "0.5.0")
            self.assertEqual(payload["status"], "success")
            self.assertIn("agent-assets", called.call_args.args[0])

            conflict = {**success, "operation": "agent-assets.sync", "status": "conflict", "findings": [{"message": "modified role"}]}
            completed = mock.Mock(returncode=2, stdout=json.dumps(conflict), stderr="")
            with mock.patch.object(installer.subprocess, "run", return_value=completed):
                with self.assertRaises(installer.InstallationError) as raised:
                    installer.run_agent_assets(root, "codex", "sync", "0.5.0")
            self.assertEqual(raised.exception.stage, "agent-projection-sync")
            self.assertIn("modified role", str(raised.exception))

    def test_development_cleanup_failure_precedes_success_report(self):
        arguments = argparse.Namespace(
            preview=False,
            integration="codex",
            integration_options=None,
        )
        result = installer.InstallResult(
            "installed",
            {"bundle_id": "concorde-bundle", "version": "0.5.0", "contributed_components": []},
            "codex",
            True,
            {"status": "success", "result": {"outputs": []}},
        )
        cleanup_error = installer.InstallationError(
            installer.EXIT_SPECIFY,
            "bundle-catalog-cleanup",
            "seeded cleanup failure",
            "Retry cleanup.",
        )
        output = io.StringIO()
        with mock.patch.object(installer, "execute_install", return_value=result):
            with mock.patch.object(installer, "remove_managed_catalogs", side_effect=cleanup_error):
                with redirect_stdout(output), self.assertRaises(installer.InstallationError):
                    installer._operate(
                        arguments,
                        Path("."),
                        mock.sentinel.release,
                        mock.sentinel.runner,
                        development=True,
                    )
        self.assertNotIn("CONCORDE INSTALL SUCCESS", output.getvalue())


if __name__ == "__main__":
    unittest.main()
