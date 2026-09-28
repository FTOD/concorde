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

from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

SOURCE = REPOSITORY_ROOT / "src/concorde/main_session/pi_runs.ts"
PROBE = """
import {
  recordedRuns, workersOf, view, concordeCommand, alive, taskWorktree, resultText, runError,
  discoveredRuns,
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
  (pid) => !discovery.dead.includes(pid),
).map((run) => run.run_id);
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
        self.status(worker("w-other", host_pid=200))
        self.status(worker("w-before", started_at="2026-09-25T09:00:00.000000Z"))
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

    @verifies("scenario.main-session.pi-run-view")
    def test_recorded_commands_and_unbound_runs_are_shown(self):
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
                "r-unbound",
                name="understand",
                workspace=None,
                phase="finished",
                status="ok",
                summary="Answered.",
                host_pid=301,
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
        self.assertEqual("unbound · understand", out["r-unbound"]["view"]["label"])
        self.assertEqual("completed", out["r-unbound"]["view"]["state"])
        self.assertNotIn("w-1", out)

    @verifies("scenario.main-session.pi-run-view")
    def test_finished_and_abandoned_runs(self):
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
        self.status(operation("r-dead", host_pid=103))
        out = self.probe(alive={"r-dead": False})
        states = {
            key: out[key]["view"]["state"]
            for key in ("r-ok", "r-blocked", "r-failed", "r-dead")
        }
        self.assertEqual(
            {
                "r-ok": "completed",
                "r-blocked": "stopped",
                "r-failed": "failed",
                "r-dead": "failed",
            },
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
        self.assertIn(
            "finished failed. failed: the runner (process 103) ended without finishing",
            out["r-dead"]["result"],
        )
        self.assertTrue(out["r-dead"]["view"]["finished"])
        self.assertIn("process 103", out["r-dead"]["view"]["preview"])
        self.assertTrue(out["self"])
        self.assertFalse(out["gone"])

    @verifies("scenario.main-session.pi-run-view")
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

    @verifies("scenario.main-session.pi-run-view")
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

    @verifies("scenario.main-session.pi-task-worktree")
    def test_a_task_runs_in_its_own_worktree(self):
        tasks = self.root / ".concorde/tasks"
        tasks.mkdir(parents=True)
        worktree = self.root / ".claude/worktrees/t1"
        worktree.mkdir(parents=True)
        (tasks / "t1.json").write_text(json.dumps({"worktree": worktree.as_posix()}))
        (tasks / "gone.json").write_text(
            json.dumps({"worktree": (self.root / "removed").as_posix()})
        )
        self.assertEqual(
            [worktree.as_posix(), None, None, None], self.probe()["worktrees"]
        )


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

    @verifies("scenario.main-session.pi-task-session-view")
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
            json.dumps({"registry": ".concorde/specs.json"})
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

    @verifies("scenario.main-session.project-terms")
    def test_a_project_without_a_readable_glossary_adds_nothing(self):
        self.registry()
        self.assertIsNone(self.terms())
        self.registry(glossary="specs/root/glossary.json")
        self.assertIsNone(self.terms())


if __name__ == "__main__":
    unittest.main()
