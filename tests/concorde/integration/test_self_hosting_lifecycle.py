import json
import os
import tempfile
import unittest
from pathlib import Path

from tests.concorde.self_hosting_support import initialize_checkout, load_self_hosting, run_cli, skill_file, skill_root


self_host = load_self_hosting()


class _SelfHostingLifecycleMixin:
    integration = "codex"

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        initialize_checkout(self.root, self.integration)

    def tearDown(self):
        self.temporary.cleanup()

    def propose(self):
        _, value = run_cli(self.root, "propose")
        self.assertEqual(value["status"], "eligible")
        return value

    def apply(self):
        _, value = run_cli(self.root, "apply", "--proposal", ".specify/self-hosting-proposal.json")
        return value

    def test_initial_proposal_and_apply_use_public_local_lifecycle(self):
        adopted = skill_file(self.root, self.integration, "speckit.concorde.ask")
        adopted.parent.mkdir(parents=True)
        adopted.write_text("stale hand-maintained copy\n")
        proposal = self.propose()
        self.assertEqual(len(proposal["components"]), 3)
        self.assertEqual(len(proposal["changes"]), 29)
        self.assertEqual(proposal["activation"], "reload_required")
        adopted_relative = adopted.parent.relative_to(self.root).as_posix()
        adopted_change = next(item for item in proposal["changes"] if item["path"] == adopted_relative)
        self.assertEqual(adopted_change["action"], "adopt")
        result = self.apply()
        self.assertEqual(result["status"], "applied")
        self.assertEqual(result["activation"], "reload_required")
        self.assertTrue((self.root / ".specify/self-hosting.json").is_file())
        fast_loop = skill_file(self.root, self.integration, "speckit.fast-loop")
        self.assertTrue(fast_loop.is_file())
        self.assertIn("--phase fast-loop", fast_loop.read_text(encoding="utf-8"))
        registry = json.loads((self.root / ".specify/presets/.registry").read_text())
        self.assertEqual(registry["presets"]["concorde"]["source"], "local")
        self.assertNotIn("stale hand-maintained", adopted.read_text())
        self.assertEqual(adopted.is_symlink(), self.integration == "claude")
        for relative in self_host.integration_profile(self.integration)["agent_surfaces"]:
            self.assertTrue((self.root / str(relative)).is_file(), relative)
        agent_receipt = json.loads((self.root / ".specify/concorde-agent-assets.json").read_text())
        self.assertIn(self.integration, agent_receipt["integrations"])
        self.assertTrue((self.root / ".concorde/reflections/config.json").is_file())

    def test_foreign_extension_command_collision_is_rejected_in_preview(self):
        registry = self.root / ".specify/extensions/.registry"
        registry.parent.mkdir(parents=True, exist_ok=True)
        registry.write_text(json.dumps({
            "schema_version": "1.0",
            "extensions": {
                "other": {
                    "registered_commands": {self.integration: ["speckit.concorde.ask"]}
                }
            },
        }))
        completed, proposal = run_cli(self.root, "propose", check=False)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(proposal["status"], "invalid")
        self.assertEqual(proposal["findings"][0]["code"], "CONCORDE-SELF-HOST-022")

    def test_stale_proposal_is_rejected_before_mutation(self):
        self.propose()
        source = self.root / "presets/concorde/README.md"
        source.write_text(source.read_text() + "\nstale\n")
        completed, result = run_cli(self.root, "apply", "--proposal", ".specify/self-hosting-proposal.json", check=False)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(result["status"], "invalid")
        self.assertFalse((self.root / ".specify/presets/concorde").exists())

    def test_refresh_and_unchanged_apply_are_deterministic(self):
        self.propose()
        self.assertEqual(self.apply()["status"], "applied")
        self.propose()
        self.assertEqual(self.apply()["status"], "unchanged")
        source = self.root / "extensions/concorde/README.md"
        source.write_text(source.read_text() + "\nrefresh marker\n")
        self.propose()
        self.assertEqual(self.apply()["status"], "applied")
        self.assertIn("refresh marker", (self.root / ".specify/extensions/concorde/README.md").read_text())
        registry = json.loads((self.root / ".specify/extensions/.registry").read_text())
        self.assertEqual(list(registry["extensions"]), ["concorde"])

    def test_status_rejects_receipt_for_different_integration(self):
        self.propose()
        self.apply()
        receipt_path = self.root / ".specify/self-hosting.json"
        receipt = json.loads(receipt_path.read_text())
        receipt["integration"] = "claude" if self.integration == "codex" else "codex"
        receipt_path.write_text(json.dumps(receipt))
        _, result = run_cli(self.root, "status")
        self.assertEqual(result["status"], "drift")
        self.assertEqual(result["dimensions"]["surfaces"]["status"], "drift")

    def test_status_detects_source_installed_registry_and_surface_drift_without_writes(self):
        self.propose()
        self.apply()
        _, current = run_cli(self.root, "status")
        self.assertEqual(current["status"], "current")
        self.assertEqual(current["dimensions"]["activation"]["status"], "reload_required")
        receipt_before = (self.root / ".specify/self-hosting.json").read_bytes()
        (self.root / "presets/concorde/README.md").write_text("changed source\n")
        _, drift = run_cli(self.root, "status")
        self.assertEqual(drift["status"], "drift")
        self.assertEqual(drift["dimensions"]["source"]["status"], "changed")
        self.assertEqual(receipt_before, (self.root / ".specify/self-hosting.json").read_bytes())

    def test_status_distinguishes_installed_registry_missing_and_extra_surface_drift(self):
        self.propose()
        self.apply()

        installed = self.root / ".specify/extensions/concorde/README.md"
        installed_before = installed.read_bytes()
        installed.write_text("locally edited materialization\n")
        _, result = run_cli(self.root, "status")
        self.assertEqual(result["dimensions"]["installed"]["status"], "drift")
        installed.write_bytes(installed_before)

        registry_path = self.root / ".specify/extensions/.registry"
        registry_before = registry_path.read_bytes()
        registry = json.loads(registry_before)
        registry["extensions"]["concorde"]["priority"] = 99
        registry_path.write_text(json.dumps(registry))
        _, result = run_cli(self.root, "status")
        self.assertEqual(result["dimensions"]["registry"]["status"], "drift")
        registry_path.write_bytes(registry_before)

        missing = skill_file(self.root, self.integration, "speckit.concorde.ask")
        missing_before = missing.read_bytes()
        missing.unlink()
        _, result = run_cli(self.root, "status")
        self.assertEqual(result["dimensions"]["surfaces"]["status"], "missing")
        missing.write_bytes(missing_before)

        extra = skill_root(self.root, self.integration) / "speckit-concorde-unexpected/SKILL.md"
        extra.parent.mkdir(parents=True)
        extra.write_text("unexpected\n")
        _, result = run_cli(self.root, "status")
        self.assertEqual(result["dimensions"]["surfaces"]["status"], "extra_owned")

    def test_require_current_is_a_read_only_quality_gate_and_does_not_select_a_feature(self):
        pointer = self.root / ".specify/feature.json"
        pointer.write_text('{"feature_directory":"specs/example"}\n')
        pointer_before = pointer.read_bytes()
        completed, result = run_cli(self.root, "status", "--require-current", check=False)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(result["status"], "absent")
        self.assertEqual(pointer_before, pointer.read_bytes())
        self.propose()
        self.apply()
        completed, result = run_cli(self.root, "status", "--require-current")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(result["status"], "current")
        self.assertEqual(pointer_before, pointer.read_bytes())

    def test_failure_after_mutation_rolls_back_exact_scope(self):
        self.propose()
        prior = self.apply()
        self.assertEqual(prior["status"], "applied")
        receipt = (self.root / ".specify/self-hosting.json").read_bytes()
        installed = (self.root / ".specify/extensions/concorde/README.md").read_bytes()
        source = self.root / "extensions/concorde/README.md"
        source.write_text(source.read_text() + "\nnext\n")
        self.propose()
        completed, result = run_cli(
            self.root,
            "apply",
            "--proposal",
            ".specify/self-hosting-proposal.json",
            environment={"CONCORDE_SELF_HOST_FAIL_STAGE": "verify"},
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(result["status"], "rolled_back")
        self.assertEqual(receipt, (self.root / ".specify/self-hosting.json").read_bytes())
        self.assertEqual(installed, (self.root / ".specify/extensions/concorde/README.md").read_bytes())

    def test_each_mutation_boundary_rolls_back_and_residual_failure_is_exact(self):
        self.propose()
        self.apply()
        source = self.root / "extensions/concorde/README.md"
        source.write_text(source.read_text() + "\nboundary change\n")
        self.propose()
        receipt = (self.root / ".specify/self-hosting.json").read_bytes()
        for stage in ("preset", "extension", "verify"):
            completed, result = run_cli(
                self.root,
                "apply",
                "--proposal",
                ".specify/self-hosting-proposal.json",
                environment={"CONCORDE_SELF_HOST_FAIL_STAGE": stage},
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(result["status"], "rolled_back", stage)
            self.assertEqual(receipt, (self.root / ".specify/self-hosting.json").read_bytes())
        completed, result = run_cli(
            self.root,
            "apply",
            "--proposal",
            ".specify/self-hosting-proposal.json",
            environment={"CONCORDE_SELF_HOST_FAIL_STAGE": "verify,rollback"},
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(result["status"], "failed")
        residual = [item["path"] for item in result["findings"] if item["stage"] == "rollback"]
        self.assertEqual(len(residual), 1)

    def test_preflight_failure_does_not_touch_real_installation(self):
        self.propose()
        completed, result = run_cli(
            self.root,
            "apply",
            "--proposal",
            ".specify/self-hosting-proposal.json",
            environment={"CONCORDE_SELF_HOST_FAIL_STAGE": "preflight"},
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(result["status"], "failed")
        self.assertFalse((self.root / ".specify/presets/concorde").exists())


class CodexSelfHostingLifecycleTests(_SelfHostingLifecycleMixin, unittest.TestCase):
    integration = "codex"


class ClaudeSelfHostingLifecycleTests(_SelfHostingLifecycleMixin, unittest.TestCase):
    integration = "claude"

    def test_regular_file_extension_surface_fallback_verifies(self):
        self.propose()
        self.apply()
        for command in self_host.EXTENSION_COMMANDS:
            path = skill_file(self.root, self.integration, command)
            content = path.read_bytes()
            path.unlink()
            path.write_bytes(content)
        _, _, _, surfaces = self_host.verify_materialization(self.root)
        extension_paths = {skill_file(self.root, self.integration, command).relative_to(self.root).as_posix() for command in self_host.EXTENSION_COMMANDS}
        representations = {item["path"]: item["representation"] for item in surfaces if item["path"] in extension_paths}
        self.assertEqual(representations, {path: "file" for path in extension_paths})

    def test_status_rejects_retargeted_dangling_absolute_and_representation_drift(self):
        self.propose()
        self.apply()
        path = skill_file(self.root, self.integration, "speckit.concorde.ask")
        canonical_content = path.read_bytes()
        unrelated = self.root / "unrelated.md"
        unrelated.write_text("unrelated\n")

        path.unlink()
        path.symlink_to(os.path.relpath(unrelated, path.parent))
        _, result = run_cli(self.root, "status")
        self.assertEqual(result["dimensions"]["surfaces"]["status"], "missing")

        path.unlink()
        path.symlink_to("missing.md")
        _, result = run_cli(self.root, "status")
        self.assertEqual(result["dimensions"]["surfaces"]["status"], "missing")

        path.unlink()
        path.symlink_to(unrelated)
        _, result = run_cli(self.root, "status")
        self.assertEqual(result["dimensions"]["surfaces"]["status"], "missing")

        path.unlink()
        path.write_bytes(canonical_content)
        _, result = run_cli(self.root, "status")
        self.assertEqual(result["dimensions"]["surfaces"]["status"], "drift")


if __name__ == "__main__":
    unittest.main()
