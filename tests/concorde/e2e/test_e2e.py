"""The end-to-end testing tool: its pure parts, without cloning or running agents."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

SPEC = importlib.util.spec_from_file_location(
    "e2e", REPOSITORY_ROOT / "scripts/e2e/e2e.py"
)
e2e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(e2e)


class E2ETests(unittest.TestCase):
    @verifies("scenario.e2e.repositories")
    def test_projects_come_from_swe_bench(self):
        if not e2e.REPO_LIST.is_file():
            self.skipTest("references/swe-bench is not checked out")
        repos = e2e.repositories()
        self.assertIn("psf/requests", repos)
        self.assertIn("pallets/flask", repos)
        with self.assertRaises(e2e.E2EError) as raised:
            e2e.prepare("someone/else", "v1", Path(tempfile.mkdtemp()), "adopt")
        self.assertEqual("unknown_repository", raised.exception.code)

    @verifies("scenario.e2e.trust")
    def test_trust_marks_each_repository_root_and_keeps_the_rest(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "requests"
            (project / "sub").mkdir(parents=True)
            subprocess.run(["git", "init", "-q"], cwd=project, check=True)
            config = base / ".claude.json"
            config.write_text(
                json.dumps({"theme": "dark", "projects": {"/x": {"a": 1}}})
            )
            value = e2e.trust([project / "sub"], config)
            root = str(project.resolve())
            self.assertEqual([root], value["trusted"])
            saved = json.loads(config.read_text())
            self.assertEqual("dark", saved["theme"])
            self.assertEqual({"a": 1}, saved["projects"]["/x"])
            self.assertTrue(saved["projects"][root]["hasTrustDialogAccepted"])
            self.assertTrue((base / ".claude.json.concorde-e2e.bak").is_file())
            self.assertEqual([], e2e.trust([project], config)["trusted"])

    @verifies("scenario.e2e.headless")
    def test_a_headless_session_waits_for_the_workflow_and_needs_no_trust(self):
        args = e2e.workflow_args(
            "adopt", "module.project", "no-ask", {"scaffold": "2"}, []
        )
        command, environment = e2e.claude_command("brownfield", args)
        self.assertEqual("0", environment["CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"])
        tools = command[
            command.index("--allowedTools") + 1 : command.index("--output-format")
        ]
        self.assertIn("Workflow(concorde-brownfield)", tools)
        self.assertIn("Bash(.concorde/bin/concorde workflow step:*)", tools)
        self.assertIn('"restart": {"scaffold": "2"}', command[2])

    def test_the_driver_needs_the_projects_rendered_script(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(e2e.E2EError) as raised:
                e2e.driver_input(Path(directory), "brownfield", {})
            self.assertEqual("script_missing", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
