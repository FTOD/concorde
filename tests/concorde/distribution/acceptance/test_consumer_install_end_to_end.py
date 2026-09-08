"""Acceptance: a real, out-of-process ``install-concorde.py --apply`` run for a consumer project.

Unlike ``tests/concorde/distribution/unit/test_install_concorde.py`` (which calls the installer's
Python functions in-process) and ``tests/concorde/specification/test_distribution.py`` (which
writes ``desired_outputs()`` bytes directly), this drives the actual command-line entry point as a
subprocess, the way a consumer would, and inspects the resulting project tree and receipt.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.host.contracts import SKILL_NAMES

from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.managed_runtime import create_langgraph_index, runtime_install_environment


class ConsumerInstallEndToEndAcceptance(unittest.TestCase):
    """Proposal section 15 (Stage D): "a consumer install test in a temporary project"."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime_temporary = tempfile.TemporaryDirectory()
        index = create_langgraph_index(Path(cls.runtime_temporary.name))
        cls.runtime_environment = runtime_install_environment(index)

        cls.project_temporary = tempfile.TemporaryDirectory()
        cls.target = Path(cls.project_temporary.name) / "consumer"
        subprocess.run(["git", "init", "--quiet", str(cls.target)], check=True)

        cls.install_result = subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "scripts/install-concorde.py"),
             "--target", str(cls.target), "--integration", "claude", "--apply", "--format", "json"],
            capture_output=True, text=True, env=cls.runtime_environment,
        )
        if cls.install_result.returncode != 0:
            raise AssertionError(
                "install-concorde.py --apply failed:\n"
                f"stdout: {cls.install_result.stdout}\nstderr: {cls.install_result.stderr}"
            )
        cls.install_payload = json.loads(cls.install_result.stdout)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.project_temporary.cleanup()
        cls.runtime_temporary.cleanup()

    def test_apply_installs_cleanly(self):
        self.assertEqual(0, self.install_result.returncode, self.install_result.stderr)
        self.assertEqual("installed", self.install_payload["status"], self.install_payload)

    def test_framework_generated_projections_exist(self):
        self.assertTrue((self.target / ".concorde/framework/generated/build-manifest.json").is_file())
        self.assertTrue((self.target / ".concorde/framework/generated/protocol/principles.md").is_file())

    def test_seven_skills_are_installed_and_receipt_owned(self):
        skill_paths = {f".claude/skills/{name}/SKILL.md" for name in SKILL_NAMES}
        self.assertEqual(7, len(skill_paths))
        for relative in skill_paths:
            self.assertTrue((self.target / relative).is_file(), relative)
        receipt = json.loads((self.target / ".concorde/install.json").read_text(encoding="utf-8"))
        owned = {item["path"] for item in receipt["outputs"] if item["role"] == "skill"}
        self.assertEqual(skill_paths, owned)

    def test_no_legacy_operation_tier_roots_are_installed(self):
        framework = self.target / ".concorde/framework"
        self.assertTrue(framework.is_dir())
        for legacy in ("operations", "roles", "agent-assets"):
            self.assertFalse((framework / legacy).exists(), legacy)

    def test_consumer_claude_md_protocol_block_references_the_framework_build(self):
        claude_md = (self.target / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("concorde-protocol:start", claude_md)
        self.assertIn("@.concorde/framework/generated/protocol/principles.md", claude_md)

    def test_describe_policy_init_propose_works_without_the_consumer_building(self):
        # The installer already built the framework as part of --apply; a consumer never runs a
        # Concorde build themselves (AGENTS.md's "Building this worktree" is source-checkout-only
        # guidance). concorde-init has no project registry yet to resolve configuration=null
        # against, so this passes an explicit configuration instead. describe-policy cannot preview
        # init/configure at all (workflow-host-boundary.md: "use_proposal"); it always reports that
        # documented deterministic-proposal response rather than "described", so both are accepted.
        invocation = {
            "type_id": "concorde-capability-invocation", "schema_version": 3,
            "capability_id": "concorde-init", "mode": "describe-policy",
            "configuration": {"type_id": "concorde-capability-configuration", "schema_version": 1,
                              "data": {"integration": "claude", "enforcement": "native"}},
            "input": {"type_id": "concorde-init-request", "schema_version": 1,
                      "data": {"action": "propose"}},
        }
        process = subprocess.run(
            [sys.executable, str(self.target / ".concorde/framework/scripts/run-capability.py"),
             "concorde-init"],
            cwd=self.target, input=json.dumps(invocation), capture_output=True, text=True,
            env={**os.environ, "CONCORDE_STUDIO_URL": ""},
        )
        result = json.loads(process.stdout)
        if result["status"] == "described":
            return
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("use_proposal", result["errors"][0]["code"], result)


if __name__ == "__main__":
    unittest.main()
