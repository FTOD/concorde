"""The end-to-end testing tool: its pure parts, without cloning or running agents."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

SPEC = importlib.util.spec_from_file_location(
    "e2e", REPOSITORY_ROOT / "scripts/e2e/e2e.py"
)
e2e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(e2e)


def git(cwd: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=e2e", "-c", "user.email=e2e@example.com", *arguments],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


class E2ETests(unittest.TestCase):
    @verifies(
        "scenario.e2e.repositories",
        "scenario.e2e.unknown-repository",
        "scenario.e2e.default-root",
    )
    def test_projects_come_from_swe_bench(self):
        if not e2e.REPO_LIST.is_file():
            self.skipTest("references/swe-bench is not checked out")
        repos = e2e.repositories()
        self.assertIn("psf/requests", repos)
        self.assertIn("pallets/flask", repos)
        with self.assertRaises(e2e.E2EError) as raised:
            e2e.prepare("someone/else", "v1", Path(tempfile.mkdtemp()), "adopt")
        self.assertEqual("unknown_repository", raised.exception.code)
        # Test projects are throwaway: they never land in the developer's home.
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CONCORDE_E2E_ROOT", None)
            root = e2e.e2e_root()
        self.assertEqual(Path(tempfile.gettempdir()) / "concorde-e2e", root)
        self.assertFalse(root.is_relative_to(Path.home()))

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
        args = e2e.workflow_args("module.project", "no-ask", {"scaffold": "2"}, [])
        self.assertNotIn("task", args)
        command, environment = e2e.claude_command("brownfield", args, "adopt")
        self.assertEqual("0", environment["CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"])
        tools = command[command.index("--allowedTools") + 1 :]
        self.assertIn("Workflow(concorde-brownfield)", tools)
        self.assertIn("Bash(.concorde/bin/concorde workflow step:*)", tools)
        self.assertIn('"restart": {"scaffold": "2"}', command[2])
        # The session works in the task's worktree and reads the report the workflow saved.
        self.assertIn("`adopt`", command[2])
        self.assertIn("concorde workflow report", command[2])
        self.assertNotIn(".workflow.json", command[2])

    def test_watch_reads_run_progress_and_workflow_records(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run = project / ".concorde/runs/r-20260927T100000-survey-00000000"
            run.mkdir(parents=True)
            (run / "status.json").write_text(
                json.dumps(
                    {"kind": "operation", "name": "survey", "workspace": "adopt"}
                    | {"phase": "worker", "step": "survey", "status": "running"}
                )
            )
            record = project / ".concorde/runs/workflows/adopt/record.json"
            record.parent.mkdir(parents=True)
            step = {"key": "survey", "run_id": run.name, "superseded": False}
            record.write_text(
                json.dumps(
                    {
                        "workspace": "adopt",
                        "workflow": "brownfield",
                        "steps": [step],
                        "reports": [],
                    }
                )
            )
            value = e2e.watch(project)
            self.assertEqual(
                {"adopt": [{"key": "survey", "run": run.name, "superseded": False}]},
                value["workflows"],
            )
            [listed] = value["runs"]
            self.assertEqual(
                (run.name, "adopt", "worker"),
                (listed["run"], listed["workspace"], listed["phase"]),
            )

    def test_a_workflow_result_is_the_workspaces_latest_saved_report(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.assertIsNone(e2e.latest_report(project, "adopt"))
            folder = project / ".concorde/runs/workflows/adopt"
            (folder / "reports").mkdir(parents=True)
            reports = [
                {"status": status, "path": str(folder / f"reports/{n}.json")}
                for n, status in ((1, "running"), (2, "ok"))
            ]
            (folder / "record.json").write_text(
                json.dumps({"workspace": "adopt", "steps": [], "reports": reports})
            )
            self.assertEqual(
                folder / "reports/2.json", e2e.latest_report(project, "adopt")
            )

    def test_the_driver_needs_the_projects_rendered_script(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(e2e.E2EError) as raised:
                e2e.driver_input(Path(directory), Path(directory), "brownfield", {})
            self.assertEqual("script_missing", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
