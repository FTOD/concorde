"""The end-to-end testing tool: its pure parts, without cloning or running agents."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.spec.verification import verifies
from concorde.kernel.tracing import node as trace
from concorde.workflows.store import WORKFLOW_TRACE
from tests.concorde.support.paths import REPOSITORY_ROOT

SPEC = importlib.util.spec_from_file_location(
    "e2e", REPOSITORY_ROOT / "scripts/e2e/e2e.py"
)
e2e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(e2e)
# The module the end-to-end tool loads its shared parts from.
e2e_common = sys.modules["common"]


def workflow_node(workspace: Path, steps: list[dict], reports: list[dict] = ()) -> None:
    """Write the workflow node of the workspace folder ``workspace`` as Workflows does."""
    folder = workspace / "workflow"
    trace.write(
        folder,
        {
            "schema_version": 1,
            "id": "brownfield",
            "kind": "workflow",
            "started_at": "2026-09-27T10:00:00Z",
            "ended_at": None,
            "status": "running",
            "outcome": None,
            "usage": trace.usage(),
            "error": None,
            "metadata": {"workspace": workspace.parent.name, "workflow": "brownfield"},
            "artifacts": [],
            "references": [],
            "content": {
                "type_id": WORKFLOW_TRACE,
                "schema_version": 1,
                "data": {
                    "workflow": "brownfield",
                    "steps": [
                        {
                            "mode": "no-ask",
                            "answers": None,
                            "error": None,
                            "superseded": False,
                            "node": f"steps/{number}-{step['key']}",
                            "at": "2026-09-27T10:00:00Z",
                            **step,
                        }
                        for number, step in enumerate(steps, 1)
                    ],
                    "reports": list(reports),
                },
            },
        },
    )


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
        # Test projects lie in concorde-e2e of the system's temporary directory, as test-<name>.
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CONCORDE_E2E_ROOT", None)
            root = e2e.e2e_root()
        self.assertEqual(
            Path(os.path.realpath(tempfile.gettempdir())) / "concorde-e2e", root
        )
        self.assertEqual(root / "test-requests", e2e.test_directory(root, "requests"))

    @verifies("scenario.e2e.root-inside-checkout")
    def test_a_root_inside_the_checkout_is_refused(self):
        outside = Path(os.path.realpath(tempfile.mkdtemp()))
        self.addCleanup(
            lambda: subprocess.run(["rm", "-rf", str(outside)], check=False)
        )
        for named, refused in (
            (REPOSITORY_ROOT / ".claude/worktrees", True),
            (REPOSITORY_ROOT, True),
            (outside, False),
        ):
            with (
                self.subTest(root=named),
                patch.dict(os.environ, {"CONCORDE_E2E_ROOT": str(named)}),
            ):
                if not refused:
                    self.assertEqual(named, e2e.e2e_root())
                    continue
                with self.assertRaises(e2e.E2EError) as raised:
                    e2e.e2e_root()
                self.assertEqual("root_inside_checkout", raised.exception.code)
                self.assertIn("CONCORDE_E2E_ROOT", raised.exception.detail)
                self.assertIn("CLAUDE.md", raised.exception.detail)
        # The default root is refused alike when the temporary directory lies in the checkout.
        with (
            patch.dict(os.environ, {}, clear=False),
            patch.object(
                e2e_common, "DEFAULT_ROOT", REPOSITORY_ROOT / "tmp/concorde-e2e"
            ),
        ):
            os.environ.pop("CONCORDE_E2E_ROOT", None)
            with self.assertRaises(e2e.E2EError) as raised:
                e2e.e2e_root()
        self.assertEqual("root_inside_checkout", raised.exception.code)
        self.assertIn("default end-to-end root", raised.exception.detail)
        # prepare refuses it before cloning anything.
        printed = io.StringIO()
        with (
            patch.dict(os.environ, {"CONCORDE_E2E_ROOT": str(REPOSITORY_ROOT)}),
            patch.object(e2e, "clone") as clone,
            contextlib.redirect_stdout(printed),
        ):
            status = e2e.main(["prepare", "psf/requests", "--rev", "v2.31.0"])
        self.assertEqual(1, status)
        self.assertEqual(
            "root_inside_checkout", json.loads(printed.getvalue())["error"]["code"]
        )
        clone.assert_not_called()

    @verifies("scenario.e2e.relative-root")
    def test_a_relative_root_is_resolved_before_preparation(self):
        outside = Path(os.path.realpath(tempfile.mkdtemp()))
        self.addCleanup(
            lambda: subprocess.run(["rm", "-rf", str(outside)], check=False)
        )
        here = Path.cwd()
        os.chdir(outside)
        self.addCleanup(os.chdir, here)
        with (
            patch.dict(os.environ, {"CONCORDE_E2E_ROOT": "roots"}),
            patch.object(e2e, "prepare", return_value={}) as prepared,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(outside / "roots", e2e.e2e_root())
            status = e2e.main(["prepare", "psf/requests", "--rev", "v2.31.0"])
        self.assertEqual(0, status)
        # prepare gets the absolute root, whose project path its commands' directories keep.
        self.assertEqual(outside / "roots", prepared.call_args.args[2])

    def prepare_committing(self, worker_model: str | None) -> tuple[dict, dict]:
        """Prepare a test project with the clone and every command stood in for; what `prepare`
        printed, and the worker configuration it committed."""
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(root)], check=False))
        committed = {}

        def fake_run(command, cwd, **options):
            if command[:2] == ["git", "add"]:
                path = Path(cwd) / e2e.WORKERS
                committed["workers"] = json.loads(path.read_text())
            stdout = json.dumps({"result": {}, "record": {"worktree": "w"}})
            return subprocess.CompletedProcess(command, 0, stdout, "")

        def fake_clone(url, rev, project):
            # The clone, and the install that makes `.concorde/`, as far as prepare reads them.
            (project / ".concorde").mkdir(parents=True)

        with (
            patch.object(e2e, "clone", fake_clone),
            patch.object(e2e, "run", fake_run),
        ):
            prepared = e2e.prepare(
                "someone/demo",
                "v1",
                root,
                "adopt",
                allow_any=True,
                name="demo",
                worker_model=worker_model,
            )
        return prepared, committed["workers"]

    @verifies("scenario.e2e.worker-model")
    def test_a_test_project_runs_every_worker_on_the_model_given(self):
        self.assertEqual(
            {
                "schema_version": 2,
                "enabled_models": {"fast": {}},
                "default": {"model": "fast"},
            },
            e2e.worker_configuration("fast"),
        )
        prepared, committed = self.prepare_committing("fast")
        self.assertEqual(e2e.worker_configuration("fast"), committed)
        self.assertEqual(["fast"], prepared["worker_models"])

    @verifies("scenario.e2e.copied-configuration")
    def test_a_test_project_takes_this_checkouts_worker_configuration(self):
        own = json.loads((REPOSITORY_ROOT / e2e.WORKERS).read_text())
        expected = {field: own[field] for field in e2e.WORKER_FIELDS if field in own}
        self.assertNotIn("runtime", expected)
        # A model map that resolves this checkout's models on both programs, as the developer's
        # does.
        mapped = Path(tempfile.mkdtemp()) / "models.json"
        self.addCleanup(
            lambda: subprocess.run(["rm", "-rf", str(mapped.parent)], check=False)
        )
        mapped.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "models": {
                        name: {"pi": f"local/{name}", "claude": name}
                        for name in own["enabled_models"]
                    },
                }
            )
        )
        with patch.dict(os.environ, {"CONCORDE_MODEL_MAP": str(mapped)}):
            prepared, committed = self.prepare_committing(None)
        self.assertEqual(expected, committed)
        self.assertEqual(
            sorted(own["enabled_models"]), sorted(prepared["worker_models"])
        )

    @verifies("scenario.e2e.unmapped-model")
    def test_a_model_the_model_map_cannot_resolve_is_refused_before_cloning(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(root)], check=False))
        with (
            patch.object(e2e, "clone") as cloned,
            self.assertRaises(e2e.E2EError) as raised,
        ):
            e2e.prepare(
                "someone/demo",
                "v1",
                root,
                "adopt",
                allow_any=True,
                name="other",
                worker_model="unmapped",
            )
        self.assertEqual("model_unmapped", raised.exception.code)
        self.assertIn("`models.unmapped.pi`", raised.exception.detail)
        cloned.assert_not_called()

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

    @verifies("scenario.e2e.trust-again")
    def test_trusting_a_trusted_project_again_changes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "requests"
            project.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=project, check=True)
            config = base / ".claude.json"
            config.write_text(json.dumps({"theme": "dark"}))
            e2e.trust([project], config)
            before = config.read_bytes()
            value = e2e.trust([project], config)
            self.assertEqual(before, config.read_bytes())
            self.assertEqual([], value["trusted"])
            self.assertEqual([str(project.resolve())], value["already"])

    @verifies("scenario.e2e.headless")
    def test_a_headless_session_waits_for_the_workflow_and_needs_no_trust(self):
        args = e2e.workflow_args("module.project", "no-ask", {"scaffold": "2"}, [])
        self.assertNotIn("task", args)
        command, environment = e2e.claude_command("brownfield", args, "adopt")
        self.assertEqual("0", environment["CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"])
        tools = command[command.index("--allowedTools") + 1 :]
        self.assertIn("Workflow(concorde-brownfield)", tools)
        self.assertIn("mcp__concorde__workflow_step", tools)
        # Its step agents reach the project MCP server, which starts every step's run.
        config = json.loads(command[command.index("--mcp-config") + 1])
        self.assertEqual(
            {"command": ".concorde/bin/concorde", "args": ["project-mcp"]},
            config["mcpServers"]["concorde"],
        )
        self.assertIn('"restart": {"scaffold": "2"}', command[2])
        # The session works in the task's worktree and reads the report the workflow saved.
        self.assertIn("`adopt`", command[2])
        self.assertIn("concorde workflow report", command[2])
        self.assertNotIn(".workflow.json", command[2])
        # It works as the task's task session, so the main session's test procedure is not
        # appended.
        self.assertIn("task session of the open task", command[2])
        appended = command[command.index("--append-system-prompt") + 1]
        self.assertEqual(e2e.sessions.NOTE, appended)

    def test_watch_reads_run_progress_and_workflow_records(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            workspace = project / ".concorde/tasks/adopt/workspace"
            run_id = "r-20260927T100000-survey-00000000"
            # A workflow step's run lies in the step's node of the workspace's workflow.
            run = workspace / "workflow/steps/1-survey/run"
            run.mkdir(parents=True)
            (run / "status.json").write_text(
                json.dumps(
                    {"kind": "operation", "run_id": run_id, "name": "survey"}
                    | {"workspace": "adopt", "phase": "worker", "step": "survey"}
                    | {"status": "running"}
                )
            )
            # A run started directly, and an unbound one.
            direct = workspace / "runs/r-20260927T100100-implement-00000000"
            direct.mkdir(parents=True)
            (direct / "status.json").write_text(
                json.dumps(
                    {"kind": "operation", "name": "implement", "workspace": "adopt"}
                )
            )
            unbound = (
                project / ".concorde/unbound/r-20260927T100200-understand-00000000"
            )
            unbound.mkdir(parents=True)
            (unbound / "status.json").write_text(
                json.dumps(
                    {"kind": "operation", "name": "understand", "workspace": None}
                )
            )
            # A run waiting in the lobby for its workspace's lock.
            waiting = project / ".concorde/lobby/r-20260927T100300-delivery-00000000"
            waiting.mkdir(parents=True)
            (waiting / "status.json").write_text(
                json.dumps(
                    {"kind": "command", "name": "delivery", "workspace": "adopt"}
                    | {"phase": "waiting"}
                )
            )
            step = {"key": "survey", "name": "survey", "run_id": run_id}
            workflow_node(workspace, [step])
            value = e2e.watch(project)
            self.assertEqual(
                {"adopt": [{"key": "survey", "run": run_id, "superseded": False}]},
                value["workflows"],
            )
            self.assertEqual(
                [
                    (direct.name, "adopt", None),
                    (run_id, "adopt", "worker"),
                    (unbound.name, None, None),
                    (waiting.name, "adopt", "waiting"),
                ],
                [
                    (listed["run"], listed["workspace"], listed["phase"])
                    for listed in value["runs"]
                ],
            )

    def run_after_earlier_result(self, saves: list[tuple[int, str]]) -> dict:
        """A headless `run` of a test project whose workflow record holds one result an earlier
        run saved, with a session that saves ``saves``; what `run` printed."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        project = Path(directory.name)
        (project / ".concorde/tasks/adopt").mkdir(parents=True)
        (project / ".concorde/tasks/adopt/task.json").write_text(
            json.dumps({"worktree": str(project)})
        )
        workspace = project / ".concorde/tasks/adopt/workspace"
        folder = workspace / "workflow"
        (folder / "reports").mkdir(parents=True)
        reports = []

        def save(number: int, status: str) -> None:
            path = folder / f"reports/{number}.json"
            path.write_text(json.dumps({"status": status}))
            (folder / f"reports/{number}.md").write_text(status)
            # The workflow's node names its reports relative to its folder.
            reports.append(
                {
                    "status": status,
                    "path": f"reports/{number}.json",
                    "rendered": f"reports/{number}.md",
                    "at": "2026-09-27T10:00:00Z",
                }
            )
            workflow_node(workspace, [], reports)

        # An earlier run of the task saved a result.
        save(1, "failed")
        self.assertEqual(
            [(folder / "reports/1.json").as_posix()],
            [item["path"] for item in e2e.saved_reports(project, "adopt")],
        )

        def session(*_arguments, **_options):
            for number, status in saves:
                save(number, status)
            return {"end": "idle"}

        log = project / ".concorde/runs/e2e/adopt-claude"
        with patch.object(e2e.sessions, "start", session):
            return e2e.run_workflow(project, "claude", "brownfield", {}, log, "adopt")

    @verifies("scenario.e2e.stale-result")
    def test_a_run_that_saved_no_result_does_not_print_an_earlier_one(self):
        with self.assertRaises(e2e.E2EError) as raised:
            self.run_after_earlier_result([])
        self.assertEqual("no_result", raised.exception.code)
        self.assertIn("held 1 before the run and 1 after", raised.exception.detail)

    @verifies("scenario.e2e.newest-result")
    def test_a_run_prints_the_newest_result_it_saved(self):
        value = self.run_after_earlier_result([(2, "running"), (3, "ok")])
        self.assertEqual({"status": "ok"}, value)

    def test_the_driver_needs_the_projects_rendered_script(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(e2e.E2EError) as raised:
                e2e.driver_input(Path(directory), Path(directory), "brownfield", {})
            self.assertEqual("script_missing", raised.exception.code)

    def test_the_driver_runs_the_claude_code_render_with_the_worktrees_command(self):
        with tempfile.TemporaryDirectory() as directory:
            project, worktree = Path(directory), Path(directory) / "t1"
            script = (
                project
                / ".concorde/framework/generated/workflows/claude/concorde-brownfield.js"
            )
            script.parent.mkdir(parents=True)
            script.write_text("export const meta = {}\n")
            value = e2e.driver_input(
                project, worktree, "brownfield", {"module": "m", "mode": "no-ask"}
            )
        self.assertEqual(str(script), value["script"])
        # The script's own report command names the command relative to the worktree.
        self.assertEqual({"module": "m", "mode": "no-ask"}, value["args"])
        self.assertEqual(
            {
                "cwd": str(worktree),
                "concorde": str(worktree / ".concorde/bin/concorde"),
            },
            value["execute"],
        )

    @verifies("scenario.e2e.driver-paths")
    def test_the_driver_runs_steps_in_a_worktree_whose_path_holds_spaces(self):
        node = shutil.which("node")
        if node is None:
            self.skipTest("node is not installed")
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        project = Path(directory.name) / "a project's home"
        worktree = project / "work tree"
        command = worktree / ".concorde/bin/concorde"
        command.parent.mkdir(parents=True)
        # The worktree's command answers its arguments and where it ran.
        command.write_text(
            "#!/usr/bin/env python3\nimport json, os, sys\n"
            'print(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd()}))\n'
        )
        command.chmod(0o755)
        script = (
            project / ".concorde/framework/generated/workflows/claude/concorde-demo.js"
        )
        script.parent.mkdir(parents=True)
        request = {"key": "survey", "operation": "survey"}
        prompt = "\n".join(
            [
                "Call the MCP tool mcp__concorde__workflow_step with these arguments:",
                "",
                json.dumps({"request": request, "wait": 5}),
            ]
        )
        script.write_text(
            'export const meta = {\n  "name": "demo"\n}\n'
            f"return await agent({json.dumps(prompt)}, {{label: 'survey'}})\n"
        )
        done = subprocess.run(
            [node, str(e2e.HARNESS)],
            cwd=worktree,
            input=json.dumps(e2e.driver_input(project, worktree, "demo", {})),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        self.assertEqual(0, done.returncode, done.stderr)
        value = json.loads(done.stdout)
        self.assertIsNone(value["error"])
        argv = value["result"]["argv"]
        self.assertEqual(["workflow", "step", "--json"], argv[:3])
        self.assertEqual(request, json.loads(argv[3]))
        self.assertEqual(["--wait", "5"], argv[4:])
        self.assertEqual(str(worktree), value["result"]["cwd"])

    @verifies("scenario.e2e.malformed-restart")
    def test_a_malformed_restart_is_a_usage_error(self):
        errors = io.StringIO()
        with (
            patch.object(e2e, "run_workflow") as ran,
            contextlib.redirect_stderr(errors),
            self.assertRaises(SystemExit) as raised,
        ):
            e2e.main(["run", "/nowhere", "--restart", "scaffold"])
        self.assertEqual(2, raised.exception.code)
        self.assertIn("usage:", errors.getvalue())
        self.assertIn("is not KEY=LABEL", errors.getvalue())
        ran.assert_not_called()
        self.assertEqual(("scaffold", "2"), e2e.restart_label("scaffold=2"))

    @verifies("scenario.e2e.runtime-failures")
    def test_runtime_failures_are_printed_as_json_errors(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        base = Path(directory.name)
        # A command that cannot be started.
        with self.assertRaises(e2e.E2EError) as raised:
            e2e.run([str(base / "missing")], cwd=base)
        self.assertEqual("command_failed", raised.exception.code)
        self.assertIn("could not be started", raised.exception.detail)
        # A task whose record is missing or names no worktree.
        (base / ".concorde/tasks/adopt").mkdir(parents=True)
        for text in (None, "[]", "{}"):
            if text is not None:
                (base / ".concorde/tasks/adopt/task.json").write_text(text)
            with self.subTest(record=text), self.assertRaises(e2e.E2EError) as raised:
                e2e.task_worktree(base, "adopt")
            self.assertEqual("no_task", raised.exception.code)
        # This checkout's worker configuration holding JSON that is no object.
        workers = base / "workers.json"
        workers.write_text("[]")
        with (
            patch.object(e2e, "CHECKOUT", base),
            patch.object(e2e, "WORKERS", "workers.json"),
            self.assertRaises(e2e.E2EError) as raised,
        ):
            e2e.worker_configuration()
        self.assertEqual("worker_configuration_unreadable", raised.exception.code)
        # Any other failure is printed as a JSON error with its traceback, not raised.
        printed = io.StringIO()
        with (
            patch.object(e2e, "watch", side_effect=RuntimeError("broken")),
            contextlib.redirect_stdout(printed),
        ):
            status = e2e.main(["watch", str(base)])
        self.assertEqual(1, status)
        error = json.loads(printed.getvalue())["error"]
        self.assertEqual(
            ("unexpected_error", "RuntimeError: broken"),
            (error["code"], error["detail"]),
        )
        self.assertIn("Traceback", error["traceback"])


if __name__ == "__main__":
    unittest.main()
