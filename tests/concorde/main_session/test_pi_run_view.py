"""The pure part of the pi run view, ``pi_runs.ts``, run by Node against progress files.

The extension around it (``pi_extension.ts``) needs a pi session and is exercised by hand in pi;
these tests cover what it shows: which worker belongs to which Operation run, the FleetView state
of each run, and which ``concorde`` command it starts.
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
  operationRuns, workersOf, view, concordeCommand, alive, taskWorktree, resultText,
} from %(source)s;
const root = %(root)s;
const out = {};
for (const operation of operationRuns(root)) {
  const workers = workersOf(root, operation);
  const shown = view(root, operation, workers, %(alive)s[operation.run_id] ?? true);
  out[operation.run_id] = {
    workers: workers.map((worker) => worker.run_id),
    view: shown,
    result: resultText(shown),
  };
}
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
        "operation": "implement",
        "task": "t1",
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

    def probe(self, alive=None) -> dict:
        probe = self.root / "probe.mts"
        probe.write_text(
            PROBE
            % {
                "source": json.dumps(SOURCE.as_posix()),
                "root": json.dumps(self.root.as_posix()),
                "alive": json.dumps(alive or {}),
            }
        )
        completed = subprocess.run(
            ["node", "--experimental-strip-types", "--no-warnings", str(probe)],
            capture_output=True,
            text=True,
            timeout=60,
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
            + "Read the Operation result: "
            + result_file,
            out["r-blocked"]["result"],
        )
        self.assertIn(
            "finished failed. failed: the Operation host", out["r-dead"]["result"]
        )
        self.assertTrue(out["r-dead"]["view"]["finished"])
        self.assertIn("process 103", out["r-dead"]["view"]["preview"])
        self.assertTrue(out["self"])
        self.assertFalse(out["gone"])

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


if __name__ == "__main__":
    unittest.main()
