"""The Host's `run_checks` answer: each configured check's status and a bounded log tail."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness.check_executor import CheckSandboxError
from concorde.harness.checks import check_service
from concorde.spec.repository import SpecError, SpecRepository
from concorde.spec.verification import verifies
from tests.concorde.spec.support import PACKAGE, project


class CheckServiceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        project(self.root)
        path = self.root / ".concorde/config.json"
        config = json.loads(path.read_text())
        # 30,000 bytes of output, then a marker: only the last 20,000 bytes reach the Agent.
        config["checks"][0].update(
            argv=[
                "{python}",
                "-c",
                "import sys; sys.stdout.write('x' * 30000 + 'END'); sys.exit(3)",
            ],
            timeout_seconds=30,
        )
        path.write_text(json.dumps(config))
        self.check_id = config["checks"][0]["id"]
        repository = SpecRepository(self.root, PACKAGE)
        self.run_checks = check_service(
            repository, repository.module("service.transfer"), "invocation"
        )

    @verifies("scenario.checks.run-checks-tool")
    def test_agent_receives_status_exit_code_and_log_tail(self):
        [item] = self.run_checks()["checks"]
        self.assertEqual(
            (self.check_id, "failed", 3),
            (item["check_id"], item["status"], item["exit_code"]),
        )
        self.assertEqual(20000, len(item["output_tail"].encode()))
        self.assertTrue(item["output_tail"].rstrip().endswith("END"))
        log = self.root / f".concorde/runs/invocation/{self.check_id}.log"
        self.assertEqual(log.read_bytes()[-20000:].decode(), item["output_tail"])

    @verifies("scenario.checks.run-checks-tool")
    def test_unavailable_boundary_fails_the_tool_call(self):
        with (
            patch(
                "concorde.harness.check_executor._bubblewrap",
                side_effect=CheckSandboxError("no sandbox"),
            ),
            self.assertRaises(SpecError) as caught,
        ):
            self.run_checks()
        self.assertEqual("check_sandbox_unavailable", caught.exception.code)
        log = self.root / f".concorde/runs/invocation/{self.check_id}.log"
        self.assertNotIn(b"END", log.read_bytes())


if __name__ == "__main__":
    unittest.main()
