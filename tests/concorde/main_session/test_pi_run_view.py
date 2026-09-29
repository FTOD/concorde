"""The pure part of the pi run view, ``pi_runs.ts``, run by Node against progress files.

The extension around it (``pi_extension.ts``) needs a pi session and is exercised by hand in pi;
these tests cover what it shows: which worker belongs to which run of an Operation or recorded
command, the FleetView state of each run, and which ``concorde`` command it starts.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.execution.runs import run_lock
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

SOURCE = REPOSITORY_ROOT / "src/concorde/main_session/pi_runs.ts"
PROBE = """
import {
  recordedRuns, workersOf, view, concordeCommand, alive, taskWorktree, resultText, runError,
  discoveredRuns, runnerAlive, lockedInodes,
} from %(source)s;
const root = %(root)s;
const out = {};
for (const run of recordedRuns(root)) {
  const workers = workersOf(root, run);
  const shown = view(root, run, workers, %(alive)s[run.run_id] ?? true);
  out[run.run_id] = {
    workers: workers.map((worker) => worker.run_id),
    view: shown,
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
        self.runs = self.root / ".concorde/runs"

    def status(self, value):
        (self.runs / value["run_id"]).mkdir(parents=True)
        (self.runs / value["run_id"] / "status.json").write_text(json.dumps(value))

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
        self.status(operation("r-1"))
        self.status(worker("w-1"))
        # Workers of other runs, even one whose runner recorded the same process identifier in
        # its own PID namespace.
        self.status(worker("w-other", operation_run_id="r-other", host_pid=200))
        self.status(worker("w-same-pid", operation_run_id="r-0"))
        out = self.probe()
        run = out["r-1"]
        self.assertEqual(["w-1"], run["workers"])
        shown = run["view"]
        self.assertEqual(
            ("running", False, "t1 · implement"),
            (shown["state"], shown["finished"], shown["label"]),
        )
        self.assertEqual(
            "run_implementer · implement worker (pi) round 2 · worker: bash pytest -q",
            shown["currentAction"],
        )
        self.assertEqual(
            (self.runs / "r-1/result.json").as_posix(), shown["reportPath"]
        )

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
        self.status(worker("w-1"))
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
        self.status(
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
        self.assertEqual("unbound · understand", out["r-unbound"]["view"]["label"])
        self.assertEqual("completed", out["r-unbound"]["view"]["state"])

    @verifies("scenario.main-session.pi-run-finished")
    def test_finished_runs_show_their_status(self):
        self.status(
            operation("r-ok", phase="finished", status="ok", summary="Implemented.")
        )
        self.status(
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
        result_file = (self.runs / "r-blocked/result.json").as_posix()
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
        # Held by its runner, as a live runner does.
        self.status(operation("r-held", host_pid=2**22 + 12345))
        self.enterContext(run_lock(self.runs / "r-held"))
        # Started in a sandbox's PID namespace, where the runner was process 1 or 2: here those
        # name live, unrelated processes, and nobody holds the run lock.
        self.status(operation("r-sandboxed", host_pid=1))
        self.status(operation("r-kthreadd", host_pid=2))
        # Ended properly just after its progress file was read: not taken for a dead run.
        self.status(operation("r-ended", host_pid=1))
        (self.runs / "r-ended/result.json").write_text("{}")
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
        # Since the view began: started by bash or another session, one already ended.
        self.status(operation("r-bash", host_pid=103))
        self.status(
            operation(
                "r-quick", phase="finished", status="failed", summary="x", host_pid=104
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
        self.assertEqual(["r-running", "r-bash", "r-quick"], out["discovered"])

    @verifies("scenario.main-session.pi-run-finished")
    def test_the_wake_message_carries_the_error_chain(self):
        self.status(
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
        (self.runs / "r-failed/result.json").write_text(
            json.dumps({"status": "failed", "error": chain})
        )
        self.status(operation("r-ok", phase="finished", status="ok", summary="Done."))
        (self.runs / "r-ok/result.json").write_text(
            json.dumps({"status": "ok", "error": None})
        )
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
        tasks = self.root / ".concorde/tasks"
        tasks.mkdir(parents=True)
        worktree = self.root / ".claude/worktrees/t1"
        worktree.mkdir(parents=True)
        (tasks / "t1.json").write_text(json.dumps({"worktree": worktree.as_posix()}))
        (tasks / "gone.json").write_text(
            json.dumps({"worktree": (self.root / "removed").as_posix()})
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


def recorded(task, round_entry):
    return {
        "id": task,
        "sessions": [
            {
                "program": "pi",
                "id": f"task-{task}-s",
                "rounds": [{"round": 1, "status": "running", **round_entry}],
            }
        ],
    }


@unittest.skipUnless(shutil.which("node"), "Node is needed to run pi_runs.ts")
class TaskSessionViewTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(os.path.realpath(directory.name))
        self.tasks = self.root / ".concorde/tasks"

    def session(self, task, status, record):
        (self.tasks / f"{task}.session").mkdir(parents=True)
        (self.tasks / f"{task}.session/status.json").write_text(json.dumps(status))
        (self.tasks / f"{task}.json").write_text(json.dumps(record))

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
        self.session("t1", progress("t1"), recorded("t1", {}))
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
            recorded("t2", {"status": "failed", "report": None, "error": link}),
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
            recorded("t3", {"status": "escalated", "report": report, "error": None}),
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
        self.assertIn("roundOwner(root, status) === mainId", extension)


OWNER_PROBE = """
import { ownership, roundOwner, wakes, OWNED_RUN_ENTRY, REPORTED_ENTRY } from %(source)s;
const kept = ownership(%(entries)s);
console.log(JSON.stringify({
  names: [OWNED_RUN_ENTRY, REPORTED_ENTRY],
  runs: [...kept.runs].sort(),
  reported: [...kept.reported].sort(),
  wakes: %(followed)s.map((entry) => wakes(entry)),
  owners: ["t1", "t2", "t3", "gone"].map((task) =>
    roundOwner(%(root)s, { task, session_id: `task-${task}-s` }),
  ),
}));
"""


@unittest.skipUnless(shutil.which("node"), "Node is needed to run pi_runs.ts")
class OwnerTests(unittest.TestCase):
    """Which runs and rounds a pi main session owns, and which of them wake it."""

    def probe(self, entries, followed, records) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(os.path.realpath(directory))
            (root / ".concorde/tasks").mkdir(parents=True)
            for task, record in records.items():
                (root / f".concorde/tasks/{task}.json").write_text(json.dumps(record))
            probe = root / "owner.mts"
            probe.write_text(
                OWNER_PROBE
                % {
                    "source": json.dumps(SOURCE.as_posix()),
                    "root": json.dumps(root.as_posix()),
                    "entries": json.dumps(entries),
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
        return json.loads(completed.stdout)

    @verifies(
        "scenario.main-session.pi-wake-owner-only",
        "scenario.main-session.pi-run-finished",
    )
    def test_only_a_finished_run_the_session_owns_wakes_it_once(self):
        followed = [
            {"id": "r-mine", "owned": True, "finished": True, "reported": False},
            {"id": "r-mine-given", "owned": True, "finished": True, "reported": True},
            {
                "id": "r-mine-running",
                "owned": True,
                "finished": False,
                "reported": False,
            },
            {"id": "r-other-main", "owned": False, "finished": True, "reported": False},
            {
                "id": "r-task-session",
                "owned": False,
                "finished": True,
                "reported": False,
            },
            {"id": "r-by-bash", "owned": False, "finished": True, "reported": False},
        ]
        out = self.probe([], followed, {})
        self.assertEqual([True, False, False, False, False, False], out["wakes"])
        # The extension shows every followed run and round but wakes only through this rule.
        extension = (SOURCE.parent / "pi_extension.ts").read_text()
        self.assertEqual(
            2, extension.count("if (wakes({ id, ...entry, finished: shown.finished }))")
        )
        self.assertNotIn("if (shown.finished && !entry.reported)", extension)

    @verifies("scenario.main-session.pi-owner-resumed")
    def test_a_resumed_session_reads_what_it_owns_and_was_given(self):
        entries = [
            {
                "type": "message",
                "customType": "concorde-owned-run",
                "data": {"id": "no"},
            },
            {
                "type": "custom",
                "customType": "concorde-owned-run",
                "data": {"id": "r-1"},
            },
            {
                "type": "custom",
                "customType": "concorde-owned-run",
                "data": {"id": "r-2"},
            },
            {
                "type": "custom",
                "customType": "concorde-reported",
                "data": {"id": "r-1"},
            },
            {
                "type": "custom",
                "customType": "concorde-reported",
                "data": {"id": "t1:s:1"},
            },
            {"type": "custom", "customType": "other-extension", "data": {"id": "r-3"}},
            {"type": "custom", "customType": "concorde-owned-run", "data": {}},
        ]
        out = self.probe(entries, [], {})
        self.assertEqual(["concorde-owned-run", "concorde-reported"], out["names"])
        self.assertEqual(["r-1", "r-2"], out["runs"])
        self.assertEqual(["r-1", "t1:s:1"], out["reported"])
        # The extension appends both entries and reads them back when a session starts.
        extension = (SOURCE.parent / "pi_extension.ts").read_text()
        self.assertIn(
            "pi.appendEntry(OWNED_RUN_ENTRY, { id: operation.run_id });", extension
        )
        self.assertIn("pi.appendEntry(REPORTED_ENTRY, { id });", extension)
        self.assertIn("ownership(ctx.sessionManager.getEntries())", extension)

    @verifies("scenario.main-session.pi-round-owner")
    def test_the_rounds_of_a_task_session_belong_to_the_main_it_names(self):
        def record(task, main):
            return {
                "id": task,
                "sessions": [{"program": "pi", "id": f"task-{task}-s", "main": main}],
            }

        records = {
            "t1": record("t1", "0199a3"),
            "t2": record("t2", None),
            "t3": record("t3", ""),
        }
        out = self.probe([], [], records)
        self.assertEqual(["0199a3", None, None, None], out["owners"])
        # A start names this session with --main; an answer leaves the owner as it is.
        extension = (SOURCE.parent / "pi_extension.ts").read_text()
        self.assertIn('? ["--main", mainId]', extension)
        self.assertIn(
            "params.answer === undefined && !params.stop && mainId", extension
        )
        self.assertIn(
            "which alone is woken when it ends, so you will not be woken", extension
        )


if __name__ == "__main__":
    unittest.main()
