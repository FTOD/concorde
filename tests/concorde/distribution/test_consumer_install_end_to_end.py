"""Acceptance: a real, out-of-process ``install-concorde.py --apply`` run for a consumer project.

Unlike ``tests/concorde/distribution/test_install_concorde.py`` (which calls the installer's
Python functions in-process) and ``tests/concorde/spec/test_distribution.py`` (which
writes ``desired_outputs()`` bytes directly), this drives the actual command-line entry point as a
subprocess, the way a consumer would, and inspects the resulting project tree and receipt.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.spec.verification import verifies
from tests.concorde.support.environment import child_environment
from tests.concorde.support.managed_runtime import independent_runtime_environment
from tests.concorde.support.paths import REPOSITORY_ROOT


class ConsumerInstallEndToEndAcceptance(unittest.TestCase):
    """Proposal section 15 (Stage D): "a consumer install test in a temporary project"."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime_temporary = tempfile.TemporaryDirectory()
        cls.runtime_environment = independent_runtime_environment(
            Path(cls.runtime_temporary.name), REPOSITORY_ROOT
        )

        cls.project_temporary = tempfile.TemporaryDirectory()
        cls.target = Path(cls.project_temporary.name) / "consumer"
        subprocess.run(["git", "init", "--quiet", str(cls.target)], check=True)

        cls.install_result = subprocess.run(
            [
                sys.executable,
                str(REPOSITORY_ROOT / "scripts/install-concorde.py"),
                "--target",
                str(cls.target),
                "--apply",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            env=cls.runtime_environment,
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

    @verifies("scenario.distribution.install-apply")
    def test_apply_installs_cleanly(self):
        self.assertEqual(0, self.install_result.returncode, self.install_result.stderr)
        self.assertEqual(
            "installed", self.install_payload["status"], self.install_payload
        )

    @verifies("scenario.distribution.install-apply")
    def test_framework_generated_projections_exist(self):
        self.assertTrue(
            (
                self.target / ".concorde/framework/generated/build-manifest.json"
            ).is_file()
        )
        self.assertTrue(
            (
                self.target / ".concorde/framework/generated/protocol/principles.md"
            ).is_file()
        )

    @verifies("scenario.distribution.install-pi-session")
    def test_pi_entry_is_the_owned_client_integration(self):
        entry = ".pi/extensions/concorde-session.ts"
        self.assertTrue((self.target / entry).is_file())
        receipt = json.loads((self.target / ".concorde/install.json").read_text())
        self.assertEqual("pi", receipt["client"])
        self.assertEqual(2, receipt["schema_version"])
        self.assertIn(entry, {item["path"] for item in receipt["outputs"]})

    @verifies("scenario.distribution.install-apply")
    def test_consumer_agents_md_protocol_block_references_the_installed_protocol_copy(
        self,
    ):
        agents_md = (self.target / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("concorde-protocol:start", agents_md)
        self.assertIn("Read and follow `.concorde/protocol/principles.md`", agents_md)
        self.assertTrue((self.target / ".concorde/protocol/principles.md").is_file())
        self.assertTrue((self.target / ".concorde/protocol/manifest.json").is_file())

    def test_describe_policy_init_propose_works_without_the_consumer_building(self):
        # The installer already built the framework as part of --apply; a consumer never runs a
        # Concorde build themselves. concorde-init takes its configuration from its request, so the
        # envelope configuration is null. describe-policy cannot preview initialization: the
        # proposal is the preview, so the request is refused with use_proposal.
        invocation = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": "concorde-init",
            "mode": "describe-policy",
            "configuration": None,
            "input": {
                "type_id": "concorde-init-request",
                "schema_version": 3,
                "data": {
                    "action": "propose",
                    "name": "Consumer",
                    "configuration": {
                        "type_id": "concorde-operation-configuration",
                        "schema_version": 2,
                        "data": {
                            "model": "openai-codex/gpt-6-astra",
                            "thinking": "medium",
                        },
                    },
                },
            },
        }
        process = subprocess.run(
            [
                sys.executable,
                str(self.target / ".concorde/framework/scripts/run-operation.py"),
                "concorde-init",
            ],
            cwd=self.target,
            input=json.dumps(invocation),
            capture_output=True,
            text=True,
            env=child_environment(),
        )
        result = json.loads(process.stdout)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("use_proposal", result["errors"][0]["code"], result)


if __name__ == "__main__":
    unittest.main()
