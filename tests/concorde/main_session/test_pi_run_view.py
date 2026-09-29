"""The pure part of the pi run view, ``pi_runs.ts``, run by Node against progress files.

The extension around it (``pi_extension.ts``) needs a pi session and is exercised by hand in pi;
these tests cover what it shows: which worker belongs to which run of an Operation or recorded
command, the FleetView state of each run, and which ``concorde`` command it starts.

A run is a trace node: ``runs/<run-id>/`` of a current task's workspace folder
``.concorde/tasks/<task>/workspace/``, ``run/`` of one of its workflow's steps, or
``.concorde/unbound/<run-id>/``; each worker run is a node ``workers/<worker run>/`` inside it, and
a runner lives while it holds ``.concorde/locks/runs/<run-id>.lock``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.execution.runs import Store, run_lock
from concorde.spec.verification import verifies
from concorde.tasks.store import ROUND_STATUS, ROUND_TRACE
from concorde.tracing.node import Node
from tests.concorde.support.paths import REPOSITORY_ROOT

SOURCE = REPOSITORY_ROOT / "src/concorde/main_session/pi_runs.ts"
PROBE = """
import {
  recordedRuns, workersOf, view, concordeCommand, alive, taskWorktree, resultText, runError,
  discoveredRuns, runnerAlive, lockedInodes, runFolder,
} from %(source)s;
const root = %(root)s;
const given = %(alive)s;
const out = {};
for (const run of recordedRuns(root)) {
  const workers = workersOf(root, run);
  const hostAlive = given === "lock" ? runnerAlive(root, run) : (given[run.run_id] ?? true);
  const shown = view(root, run, workers, hostAlive);
  out[run.run_id] = {
    workers: workers.map((worker) => worker.run_id),
    view: shown,
    folder: run.folder,
    found: runFolder(root, run.run_id),
    result: resultText(shown, runError(root, run.run_id)),
  };
}
const discovery = %(discovery)s;
out.discovered = discoveredRuns(
  recordedRuns(root),
  new Set(discovery.known),
  Date.parse(discovery.since),
  new Set(discovery.launching),
  (run) => !discovery.dead.includes(run.host_pid),
).map((run) => run.run_id);
out.runnerAlive = Object.fromEntries(
  recordedRuns(root).map((run) => [run.run_id, runnerAlive(root, run)]),
);
out.lockTable = lockedInodes() !== null;
out.command = concordeCommand(root);
out.worktrees = ["t1", "gone", "missing", "../t1"].map((task) => taskWorktree(root, task));
out.self = alive(process.pid);
out.gone = alive(2 ** 22 + 12345);
console.log(JSON.stringify(out));
"""


def operation(run_id, **fields):
    value = {
        "kind": "operation",
        "run_id": run_id,
        "name": "implement",
        "workspace": "t1",
        "modules": ["module.a"],
        "phase": "running",
        "step": "run_implementer",
        "status": None,
        "host_pid": 100,
        "started_at": "2026-09-25T10:00:00.000000Z",
        "updated_at": "2026-09-25T10:00:05.000000Z",
    }
    value.update(fields)
    return value


def worker(run_id, **fields):
    value = {
        "run_id": run_id,
        "operation_run_id": "r-1",
        "task_type": "implement",
        "backend": "pi",
        "phase": "worker",
        "round": 2,
        "last_action": {
            "tool": "bash",
            "target": "pytest -q",
            "at": "2026-09-25T10:00:09Z",
        },
        "status": None,
        "host_pid": 100,
        "started_at": "2026-09-25T10:00:01.000000Z",
        "updated_at": "2026-09-25T10:00:09.000000Z",
    }
    value.update(fields)
    return value


@unittest.skipUnless(shutil.which("node"), "Node is needed to run pi_runs.ts")
class RunViewTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(os.path.realpath(directory.name))
        self.concorde = self.root / ".concorde"

    def folder(self, value) -> Path:
        """Where the runner of the run ``value`` keeps its node: the runs of its task's workspace
        folder, or the unbound runs of the worktree."""
        if value["workspace"] is None:
            return self.concorde / "unbound" / value["run_id"]
        return (
            self.concorde
            / "tasks"
            / value["workspace"]
            / "workspace/runs"
            / value["run_id"]
        )

    def status(self, value, folder: Path | None = None) -> Path:
        folder = folder or self.folder(value)
        folder.mkdir(parents=True)
        (folder / "status.json").write_text(json.dumps(value))
        return folder

    def worker(self, run: Path, value) -> Path:
        return self.status(value, run / "workers" / value["run_id"])

    def probe(self, alive=None, discovery=None) -> dict:
        probe = self.root / "probe.mts"
        probe.write_text(
            PROBE
            % {
                "source": json.dumps(SOURCE.as_posix()),
                "root": json.dumps(self.root.as_posix()),
                "alive": json.dumps(alive or {}),
                "discovery": json.dumps(
                    discovery
                    or {
                        "known": [],
                        "since": "2026-09-25T00:00:00Z",
                        "launching": [],
                        "dead": [],
                    }
                ),
            }
        )
        completed = subprocess.run(
            ["node", "--experimental-strip-types", "--no-warnings", str(probe)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)

    @verifies("scenario.main-session.pi-run-view")
    def test_a_running_operation_shows_its_worker_progress(self):
        run = self.status(operation("r-1"))
        self.worker(run, worker("w-1"))
        # Workers of other runs, even one whose runner recorded the same process identifier in
        # its own PID namespace, and even one that names r-1 as its Operation run.
        other = self.status(operation("r-other", host_pid=200, workspace="t2"))
        self.worker(other, worker("w-other", host_pid=200))
        same = self.status(operation("r-0"))
        self.worker(same, worker("w-same-pid", operation_run_id="r-0"))
        # A run of a workflow step lies in the step's node of the workspace's workflow.
        step = self.status(
            operation(
                "r-step", name="specify", started_at="2026-09-25T10:00:02.000000Z"
            ),
            self.concorde / "tasks/t1/workspace/workflow/steps/1-specify/run",
        )
        self.worker(
            step, worker("w-step", operation_run_id="r-step", task_type="specify")
        )
        out = self.probe()
        self.assertEqual(["w-1"], out["r-1"]["workers"])
        self.assertEqual(["w-other"], out["r-other"]["workers"])
        self.assertEqual(["w-same-pid"], out["r-0"]["workers"])
        self.assertEqual(["w-step"], out["r-step"]["workers"])
        self.assertEqual(
            (step.as_posix(), step.as_posix()),
            (out["r-step"]["folder"], out["r-step"]["found"]),
        )
        self.assertNotIn("w-1", out)
        shown = out["r-1"]["view"]
        self.assertEqual(
            ("running", False, "t1 · implement"),
            (shown["state"], shown["finished"], shown["label"]),
        )
        self.assertEqual(
            "run_implementer · implement worker (pi) round 2 · worker: bash pytest -q",
            shown["currentAction"],
        )
        self.assertEqual((run / "result.json").as_posix(), shown["reportPath"])
        self.assertEqual(run.as_posix(), out["r-1"]["found"])

    @verifies("scenario.main-session.pi-run-view-command")
    def test_recorded_commands_are_shown_without_a_worker(self):
        self.status(
            operation(
                "r-command",
                kind="command",
                name="task-validation",
                step="run_checks",
                host_pid=300,
            )
        )
        self.status(
            operation(
                "r-waiting",
                kind="command",
                name="delivery",
                step="workspace-lock",
                waiting_for="task-validation run r-command (process 300)",
                host_pid=302,
            )
        )
        implement = self.status(operation("r-1"))
        self.worker(implement, worker("w-1"))
        out = self.probe()
        self.assertEqual(
            "waiting for the workspace lock held by task-validation run r-command "
            "(process 300)",
            out["r-waiting"]["view"]["currentAction"],
        )
        command = out["r-command"]
        self.assertEqual([], command["workers"])
        self.assertEqual(
            ("running", "t1 · task-validation", "run_checks"),
            (
                command["view"]["state"],
                command["view"]["label"],
                command["view"]["currentAction"],
            ),
        )
        self.assertNotIn("w-1", out)

    @verifies("scenario.main-session.pi-run-view-unbound")
    def test_unbound_runs_are_shown_without_a_workspace(self):
        folder = self.status(
            operation(
                "r-unbound",
                name="understand",
                workspace=None,
                phase="finished",
                status="ok",
                summary="Answered.",
                host_pid=301,
            )
        )
        out = self.probe()
        self.assertEqual(self.concorde / "unbound/r-unbound", folder)
        self.assertEqual("unbound · understand", out["r-unbound"]["view"]["label"])
        self.assertEqual("completed", out["r-unbound"]["view"]["state"])
        self.assertEqual(
            (folder / "result.json").as_posix(), out["r-unbound"]["view"]["reportPath"]
        )

    @verifies("scenario.main-session.pi-run-finished")
    def test_finished_runs_show_their_status(self):
        self.status(
            operation("r-ok", phase="finished", status="ok", summary="Implemented.")
        )
        blocked = self.status(
            operation(
                "r-blocked",
                phase="finished",
                status="blocked",
                summary="Spec gap.",
                host_pid=101,
            )
        )
        self.status(
            operation(
                "r-failed",
                phase="finished",
                status="failed",
                summary="Checks fail.",
                host_pid=102,
            )
        )
        out = self.probe()
        states = {
            key: out[key]["view"]["state"] for key in ("r-ok", "r-blocked", "r-failed")
        }
        self.assertEqual(
            {"r-ok": "completed", "r-blocked": "stopped", "r-failed": "failed"},
            states,
        )
        self.assertEqual("ok: Implemented.", out["r-ok"]["view"]["preview"])
        result_file = (blocked / "result.json").as_posix()
        self.assertEqual(
            "Concorde run r-blocked (t1 · implement) finished blocked. blocked: Spec gap.\n"
            + "Read the run result: "
            + result_file,
            out["r-blocked"]["result"],
        )

    @verifies("scenario.main-session.pi-run-lost")
    def test_a_run_whose_runner_ended_without_finishing_failed(self):
        self.status(operation("r-dead", host_pid=103))
        out = self.probe(alive={"r-dead": False})
        self.assertEqual(
            ("failed", True),
            (out["r-dead"]["view"]["state"], out["r-dead"]["view"]["finished"]),
        )
        self.assertIn(
            "finished failed. failed: the runner ended without finishing the run: it no "
            "longer holds its run lock",
            out["r-dead"]["result"],
        )
        self.assertTrue(out["self"])
        self.assertFalse(out["gone"])

    @verifies("scenario.main-session.pi-run-lost", "scenario.execution.run-lock")
    def test_a_runner_lives_while_it_holds_its_run_lock(self):
        store = Store(self.concorde)
        # Held by its runner, as a live runner does.
        self.status(operation("r-held", host_pid=2**22 + 12345))
        self.enterContext(run_lock(store, "r-held", "test runner"))
        # Started in a sandbox's PID namespace, where the runner was process 1 or 2: here those
        # name live, unrelated processes, and nobody holds the run lock, whose file is gone.
        self.status(operation("r-sandboxed", host_pid=1))
        self.status(operation("r-kthreadd", host_pid=2))
        # Ended properly just after its progress file was read: not taken for a dead run.
        ended = self.status(operation("r-ended", host_pid=1))
        (ended / "result.json").write_text("{}")
        out = self.probe()
        self.assertTrue(out["lockTable"])
        self.assertEqual(
            {
                "r-held": True,
                "r-sandboxed": False,
                "r-kthreadd": False,
                "r-ended": True,
            },
            out["runnerAlive"],
        )

    @verifies(
        "scenario.main-session.pi-run-lock-file", "scenario.main-session.pi-run-lost"
    )
    def test_a_live_run_is_told_by_its_run_lock_file(self):
        store = Store(self.concorde)
        lock = self.concorde / "locks/runs/r-held.lock"
        # A run of a task's workspace whose runner holds its run lock.
        self.status(operation("r-held", host_pid=2**22 + 12345))
        held = run_lock(store, "r-held", "test runner")
        held.__enter__()
        self.addCleanup(held.__exit__, None, None, None)
        self.assertTrue(lock.is_file())
        # A run without a result whose lock file is missing, though its recorded process lives.
        self.status(operation("r-missing", host_pid=os.getpid()))
        # A run without a result whose lock file is left behind but held by nobody.
        self.status(operation("r-unheld", host_pid=os.getpid()))
        (self.concorde / "locks/runs/r-unheld.lock").write_text("")
        out = self.probe(alive="lock")
        self.assertEqual(
            {"r-held": True, "r-missing": False, "r-unheld": False}, out["runnerAlive"]
        )
        self.assertEqual(
            ("running", False),
            (out["r-held"]["view"]["state"], out["r-held"]["view"]["finished"]),
        )
        for run in ("r-missing", "r-unheld"):
            self.assertEqual(
                ("failed", True, "failed"),
                (
                    out[run]["view"]["state"],
                    out[run]["view"]["finished"],
                    out[run]["view"]["status"],
                ),
            )
            self.assertIn(
                "the runner ended without finishing the run", out[run]["result"]
            )
        # The runner ends without writing a result: its lock file goes with it.
        held.__exit__(None, None, None)
        self.assertFalse(lock.exists())
        out = self.probe(alive="lock")
        self.assertEqual("failed", out["r-held"]["view"]["state"])
        # concorde_run starts the run with --detach, whose runner keeps its output in host.out
        # of the run's node and announces that node; nothing writes a launch log.
        extension = (SOURCE.parent / "pi_extension.ts").read_text()
        launch = extension[extension.index('name: "concorde_run"') :]
        launch = launch[: launch.index("pi.registerTool(")]
        self.assertIn('"--detach",', launch)
        self.assertIn("const folder = announced.trace as string;", launch)
        self.assertIn('stdio: ["ignore", "pipe", "pipe"]', launch)
        self.assertNotIn("launch-", extension)
        self.assertNotIn("launch-", SOURCE.read_text())

    @verifies("scenario.main-session.pi-run-discovered")
    def test_runs_started_elsewhere_are_followed(self):
        # Before the view began: one still running, one finished, one whose runner died.
        self.status(operation("r-running", started_at="2026-09-25T09:00:00.000000Z"))
        self.status(
            operation(
                "r-old",
                phase="finished",
                status="ok",
                started_at="2026-09-25T09:00:01.000000Z",
                host_pid=101,
            )
        )
        self.status(
            operation("r-stale", started_at="2026-09-25T09:00:02.000000Z", host_pid=102)
        )
        # Since the view began: started by bash or another session, one already ended, one
        # unbound.
        self.status(operation("r-bash", host_pid=103))
        self.status(
            operation(
                "r-quick", phase="finished", status="failed", summary="x", host_pid=104
            )
        )
        self.status(
            operation(
                "r-unbound",
                workspace=None,
                started_at="2026-09-25T10:00:01.000000Z",
                host_pid=107,
            )
        )
        # Already followed, or being launched by concorde_run itself.
        self.status(operation("r-known", host_pid=105))
        self.status(operation("r-launching", host_pid=106))
        out = self.probe(
            discovery={
                "known": ["r-known"],
                "since": "2026-09-25T09:30:00Z",
                "launching": [106],
                "dead": [102],
            }
        )
        self.assertEqual(
            ["r-running", "r-bash", "r-quick", "r-unbound"], out["discovered"]
        )

    @verifies("scenario.main-session.pi-run-finished")
    def test_the_wake_message_carries_the_error_chain(self):
        failed = self.status(
            operation(
                "r-failed",
                name="spec_review",
                workspace=None,
                phase="finished",
                status="failed",
                summary="The reviewer failed.",
            )
        )
        chain = {
            "level": "operation",
            "actor": "Operation spec_review r-failed (unbound)",
            "code": "worker_failed",
            "detail": "the reviewer ended failed",
            "unhandled": {
                "reason": "decision",
                "explanation": "the main agent decides",
            },
            "options": ["run it again"],
            "causes": [
                {
                    "level": "worker",
                    "actor": "reviewer",
                    "code": "context_missing",
                    "detail": "a Spec could not be read",
                    "unhandled": {"reason": "input", "explanation": "nothing to read"},
                    "options": [],
                    "causes": [],
                }
            ],
        }
        (failed / "result.json").write_text(
            json.dumps({"status": "failed", "error": chain})
        )
        ok = self.status(
            operation("r-ok", phase="finished", status="ok", summary="Done.")
        )
        (ok / "result.json").write_text(json.dumps({"status": "ok", "error": None}))
        out = self.probe()
        text = out["r-failed"]["result"]
        self.assertIn("finished failed. failed: The reviewer failed.", text)
        self.assertIn(
            "Error chain:\nOperation spec_review r-failed (unbound): worker_failed: "
            "the reviewer ended failed (not handled: the main agent decides)",
            text,
        )
        self.assertIn("  option: run it again", text)
        self.assertIn(
            "  reviewer: context_missing: a Spec could not be read (not handled: nothing "
            "to read)",
            text,
        )
        self.assertNotIn("Error chain", out["r-ok"]["result"])

    def test_the_command_prefers_the_installed_concorde(self):
        self.assertEqual(["concorde"], self.probe()["command"])
        (self.root / "scripts").mkdir()
        (self.root / "scripts/concorde.py").write_text("")
        self.assertEqual(
            ["python3", (self.root / "scripts/concorde.py").as_posix()],
            self.probe()["command"],
        )
        (self.root / ".concorde/bin").mkdir(parents=True)
        (self.root / ".concorde/bin/concorde").write_text("")
        self.assertEqual(
            [(self.root / ".concorde/bin/concorde").as_posix()], self.probe()["command"]
        )

    def tasks(self) -> Path:
        tasks = self.concorde / "tasks"
        worktree = self.root / ".claude/worktrees/t1"
        worktree.mkdir(parents=True)
        for task, path in (("t1", worktree), ("gone", self.root / "removed")):
            (tasks / task).mkdir(parents=True)
            (tasks / task / "task.json").write_text(
                json.dumps({"worktree": path.as_posix()})
            )
        return worktree

    @verifies("scenario.main-session.pi-task-worktree")
    def test_a_task_runs_in_its_own_worktree(self):
        worktree = self.tasks()
        self.assertEqual(worktree.as_posix(), self.probe()["worktrees"][0])

    @verifies("scenario.main-session.pi-task-worktree-missing")
    def test_a_task_without_a_worktree_is_refused_before_anything_starts(self):
        self.tasks()
        # A removed worktree, a task without a record and a name outside the tasks directory.
        self.assertEqual([None, None, None], self.probe()["worktrees"][1:])
        # concorde_run refuses such a task, naming it, before it spawns anything.
        extension = (SOURCE.parent / "pi_extension.ts").read_text()
        refusal = extension.index("if (worktree === null)")
        self.assertIn(
            "`task ${params.task} has no worktree in ${root}",
            extension[refusal : refusal + 200],
        )
        self.assertLess(refusal, extension.index("spawn(", refusal))


ROUNDS = """
import { roundId, roundOutcome, sessionRounds, sessionText, sessionView } from %(source)s;
const root = %(root)s;
const out = {};
for (const status of sessionRounds(root)) {
  out[roundId(status)] = {
    view: sessionView(root, status, %(alive)s),
    outcome: roundOutcome(root, status),
    text: sessionText(root, status),
  };
}
console.log(JSON.stringify(out));
"""


def progress(task, **fields):
    value = {
        "kind": "task-session",
        "task": task,
        "session_id": f"task-{task}-s",
        "round": 1,
        "phase": "running",
        "status": None,
        "summary": None,
        "supervisor_pid": 4242,
        "last_action": {
            "tool": "bash",
            "target": "pytest -q",
            "at": "2026-09-26T10:00:09Z",
        },
        "started_at": "2026-09-26T10:00:00Z",
        "updated_at": "2026-09-26T10:00:09Z",
    }
    value.update(fields)
    return value


def recorded(folder: Path, outcome="running", report=None, error=None) -> None:
    """Write the node ``folder`` of a round of a pi task session as the supervisor and Tasks
    keep it: running, or ended with ``outcome`` and its report or error."""
    node = Node(
        folder,
        "1",
        "round",
        content_type=ROUND_TRACE,
        metadata={"program": "pi"},
        content={
            "round": 1,
            "prompt": "task",
            "answer": None,
            "outcome": "running",
            "supervisor_pid": 4242,
            "report": None,
        },
    ).start()
    if outcome != "running":
        node.finish(
            ROUND_STATUS[outcome],
            outcome=outcome,
            error=error,
            content={
                **node.record["content"]["data"],
                "outcome": outcome,
                "report": report,
            },
        )


@unittest.skipUnless(shutil.which("node"), "Node is needed to run pi_runs.ts")
class TaskSessionViewTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(os.path.realpath(directory.name))
        self.tasks = self.root / ".concorde/tasks"

    def session(self, task, status, *outcome, **fields):
        """The session node of ``task``'s pi task session with its progress file, and the node
        of its first round."""
        folder = self.tasks / task / "sessions" / status["session_id"]
        folder.mkdir(parents=True)
        (folder / "status.json").write_text(json.dumps(status))
        recorded(folder / "rounds/1", *outcome, **fields)

    def probe(self, alive=True) -> dict:
        probe = self.root / "rounds.mts"
        probe.write_text(
            ROUNDS
            % {
                "source": json.dumps(SOURCE.as_posix()),
                "root": json.dumps(self.root.as_posix()),
                "alive": json.dumps(alive),
            }
        )
        completed = subprocess.run(
            ["node", "--experimental-strip-types", "--no-warnings", str(probe)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)

    @verifies(
        "scenario.main-session.pi-task-session-view",
        "scenario.main-session.pi-task-session-wake",
    )
    def test_rounds_show_their_progress_and_wake_with_the_recorded_outcome(self):
        self.session("t1", progress("t1"))
        link = {
            "actor": "Tasks pi task-session supervisor (task t2, session task-t2-s, round 1)",
            "code": "session_no_report",
            "detail": "pi ended round 1 without calling concorde_report: exit code 1",
            "unhandled": {"reason": "environment", "explanation": "nothing to finish"},
            "options": ["read the event stream"],
            "causes": [],
        }
        self.session(
            "t2",
            progress("t2", phase="finished", status="failed", summary="pi ended"),
            "failed",
            error=link,
        )
        report = {
            "status": "escalated",
            "summary": "One question is open.",
            "escalations": [1, 2],
            "decisions": ["Named the enum Severity."],
            "open": ["Whether warnings block delivery."],
        }
        self.session(
            "t3",
            progress("t3"),
            "escalated",
            report=report,
        )
        out = self.probe()
        running = out["t1:task-t1-s:1"]
        self.assertEqual(
            ("running", False, "t1 · task session round 1"),
            (
                running["view"]["state"],
                running["view"]["finished"],
                running["view"]["label"],
            ),
        )
        self.assertIn("bash pytest -q", running["view"]["currentAction"])
        self.assertIsNone(running["outcome"])
        failed = out["t2:task-t2-s:1"]
        self.assertEqual("failed", failed["view"]["state"])
        self.assertIn("ended failed", failed["text"])
        self.assertIn("session_no_report", failed["text"])
        self.assertIn("option: read the event stream", failed["text"])
        escalated = out["t3:task-t3-s:1"]
        self.assertEqual(
            {"status": "escalated", "summary": "One question is open."},
            escalated["outcome"],
        )
        for part in (
            "ended escalated",
            "One question is open.",
            "- Named the enum Severity.",
            "- Whether warnings block delivery.",
            "Escalations: 1, 2",
            "concorde task show t3",
        ):
            self.assertIn(part, escalated["text"])
        gone = self.probe(alive=False)["t1:task-t1-s:1"]["view"]
        self.assertEqual(("failed", True), (gone["state"], gone["finished"]))
        self.assertIn("ended without recording", gone["preview"])


@unittest.skipUnless(shutil.which("node"), "Node is needed to run pi_runs.ts")
class ProjectTermsTests(unittest.TestCase):
    """The project's terms the pi extension adds to every session's system prompt."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(os.path.realpath(directory.name))
        (self.root / ".concorde").mkdir()
        (self.root / ".concorde/config.json").write_text(
            json.dumps({"profile_version": 19})
        )

    def registry(self, **root_fields):
        (self.root / ".concorde/specs.json").write_text(
            json.dumps(
                {
                    "schema_version": 3,
                    "modules": [
                        {"id": "module.child", "entry": "specs/child/module.md"},
                        {
                            "id": "module.root",
                            "entry": "specs/root/module.md",
                            **root_fields,
                        },
                    ],
                }
            )
        )

    def terms(self):
        probe = self.root / "probe.mts"
        probe.write_text(
            f"import {{ glossaryText }} from {json.dumps(SOURCE.as_posix())};\n"
            f"console.log(JSON.stringify(glossaryText({json.dumps(self.root.as_posix())})));\n"
        )
        completed = subprocess.run(
            ["node", "--experimental-strip-types", "--no-warnings", str(probe)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)

    @verifies("scenario.main-session.project-terms")
    def test_every_term_is_given_with_the_rule_to_use_it_exactly(self):
        self.registry(glossary="specs/root/glossary.json")
        (self.root / "specs/root").mkdir(parents=True)
        (self.root / "specs/root/glossary.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "concepts": [
                        {
                            "id": "concept.worker",
                            "title": "Worker",
                            "owner": "module.child",
                            "definition": "One process under a [grant](#concept.grant).",
                            "explanation": "specs/child/module.md#concept.worker",
                        },
                        {
                            "id": "concept.grant",
                            "title": "Grant",
                            "owner": "module.root",
                            "definition": "What a worker may read and write.",
                            "explanation": "specs/root/module.md#concept.grant",
                        },
                    ],
                }
            )
        )
        text = self.terms()
        self.assertIn("glossary `specs/root/glossary.json`", text)
        self.assertIn("Use every term exactly with the meaning given here", text)
        grant = text.index("- **Grant** (`concept.grant`, module.root): What a worker")
        worker = text.index(
            "- **Worker** (`concept.worker`, module.child): One process under a grant."
        )
        self.assertLess(grant, worker)

    @verifies("scenario.main-session.project-terms-missing")
    def test_a_project_without_a_readable_glossary_adds_nothing(self):
        self.registry()
        self.assertIsNone(self.terms())
        self.registry(glossary="specs/root/glossary.json")
        self.assertIsNone(self.terms())


OWNED_PROBE = """
import { ownedWork } from %(source)s;
console.log(JSON.stringify(ownedWork(%(followed)s, "session-file")));
"""


@unittest.skipUnless(shutil.which("node"), "Node is needed to run pi_runs.ts")
class OwnedWorkTests(unittest.TestCase):
    @verifies("scenario.main-session.pi-owned-work")
    def test_only_the_sessions_own_unfinished_work_is_drained(self):
        followed = [
            {"id": "r-mine", "owned": True, "finished": False},
            {"id": "r-mine-done", "owned": True, "finished": True},
            {"id": "r-other-session", "owned": False, "finished": False},
            {"id": "r-by-bash", "owned": False, "finished": False},
            {"id": "t1/round-2", "owned": True, "finished": False},
            {"id": "t2/round-1", "owned": False, "finished": False},
        ]
        with tempfile.TemporaryDirectory() as directory:
            probe = Path(directory) / "owned.mts"
            probe.write_text(
                OWNED_PROBE
                % {
                    "source": json.dumps(SOURCE.as_posix()),
                    "followed": json.dumps(followed),
                }
            )
            completed = subprocess.run(
                ["node", "--experimental-strip-types", "--no-warnings", str(probe)],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(
            [
                {"id": "r-mine", "sessionId": "session-file"},
                {"id": "t1/round-2", "sessionId": "session-file"},
            ],
            json.loads(completed.stdout),
        )
        # The extension feeds every followed run and round through this rule, marking as owned
        # only what its own tools started.
        extension = (SOURCE.parent / "pi_extension.ts").read_text()
        self.assertIn("listActiveWork: () =>\n        ownedWork(", extension)
        self.assertIn("track(operation, shown.finished, true);", extension)
        self.assertIn("owned: true,", extension)


if __name__ == "__main__":
    unittest.main()
