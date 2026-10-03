"""Workflows: keyed steps, the workflow result, and the rendered script under a stand-in Claude Code."""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar
from unittest.mock import patch

from concorde.kernel import errors
from concorde.execution.commands.catalog import COMMANDS
from concorde.execution.runs import Store, run_lock, workspace_lock, workspace_runs
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.kernel.tracing import locks
from concorde.kernel.tracing import node as trace
from concorde.method import brownfield  # noqa: F401 -- registers the brownfield workflow
from concorde.workflows import catalog, store
from concorde.workflows.output import StepOutputError, step_output
from concorde.workflows import step as steps
from concorde.workflows.cli import refused
from concorde.workflows.report import RESULT_SCHEMA, report
from concorde.workflows.step import (
    REQUEST_SCHEMA,
    STEP_SCHEMA,
    check_request,
    run_step,
    step_key,
)
from tests.concorde.support.brownfield_project import BrownfieldProject
from tests.concorde.support.brownfield_project import commit as commit_all
from tests.concorde.support.paths import REPOSITORY_ROOT

HARNESS = Path(__file__).with_name("run_script.mjs")


def contract(path: str, identity: str) -> dict:
    text = (REPOSITORY_ROOT / path).read_text()
    for fence in re.findall(r"```concorde-contract\n(.*?)\n```", text, re.DOTALL):
        body = json.loads(fence)
        if body["id"] == identity:
            return body["schema"]
    raise AssertionError(f"{identity} not in {path}")


def run_link(name: str, run_id: str, code: str, reason: str = "decision") -> dict:
    return errors.link(
        "operation",
        f"Operation {name} {run_id} (workspace adopt)",
        code,
        f"{name} stopped with {code}",
        reason=reason,
        explanation="a test stand-in",
    )


def wait_blocked(path: Path, timeout: float = 30) -> None:
    """Return once some process waits for the ``flock`` of ``path``, as ``/proc/locks`` shows."""
    inode = os.stat(path).st_ino
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for line in Path("/proc/locks").read_text().splitlines():
            fields = line.split()
            if "->" in fields and fields[fields.index("->") + 5].endswith(f":{inode}"):
                return
        time.sleep(0.02)
    raise AssertionError(f"nothing waited for the lock {path}")


class Runs:
    """Saved run results written by hand, standing in for finished or dying runners.

    A run is placed where its runner would trace it: in ``folder``, the ``run/`` of a workflow
    step's node, or else among the workspace's directly started runs. A running run's run lock
    is held until ``held`` is closed, as its runner would hold it."""

    def __init__(self, store: Store):
        self.store = store
        self.held = contextlib.ExitStack()

    def make(
        self,
        name: str,
        status: str | None = "ok",
        output: dict | None = None,
        error: dict | None = None,
        modules=("module.shop",),
        running: bool = False,
        folder: Path | None = None,
    ) -> str:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        run_id = f"r-{stamp}-{name.replace('-', '_')}-{secrets.token_hex(4)}"
        directory = folder or self.store.run_folder(run_id)
        directory.mkdir(parents=True)
        trace.Node(directory, run_id, "run", metadata={"workspace": "adopt"}).start()
        # A small process identifier, as a runner in a sandbox's PID namespace records, names
        # a live process here; only the run lock tells whether the runner lives.
        (directory / "status.json").write_text(json.dumps({"host_pid": 1}))
        if running:
            self.held.enter_context(run_lock(self.store, run_id, f"runner of {run_id}"))
        if status is not None:
            if status != "ok" and error is None:
                error = run_link(name, run_id, f"{name.replace('-', '_')}_{status}")
            (directory / "result.json").write_text(
                json.dumps(
                    {
                        "kind": "command" if name in COMMANDS else "operation",
                        "name": name,
                        "workspace": "adopt",
                        "modules": list(modules),
                        "run_id": run_id,
                        "status": status,
                        "summary": f"{name} ended {status}.",
                        "output": output,
                        "worker": None,
                        "worker_runs": [],
                        "host_evidence": [],
                        "error": error,
                        "started_at": "2026-09-25T10:00:00Z",
                        "finished_at": "2026-09-25T10:01:00Z",
                    }
                )
            )
        return run_id


# Stand-in run outputs. Workflows reads only the workflow object of a run's output, so each declares
# what the Operation or command it stands in for would declare there, and nothing else.
QUESTION = {
    "id": "q.retry",
    "kind": "question",
    "question": "retries: declines retried",
    "options": ["keep", "drop"],
    "recommendation": "ask",
    "module": "module.checkout",
}
SURVEY_OUTPUT = {
    "summary": "fields Workflows never reads",
    "workflow": step_output(
        decision_points=[
            {
                "id": "d.db-helper",
                "kind": "decision",
                "question": "own Module?",
                "options": ["yes", "no"],
                "recommendation": "the worker chose 'no': small",
                "module": "module.shop",
            }
        ],
        decisions=[
            {
                "id": "d.db-helper",
                "question": "own Module?",
                "options": ["yes", "no"],
                "decision": "no",
                "reason": "small",
                "decided_by": "worker",
                "module": "module.shop",
            }
        ],
        notes=[
            {
                "kind": "proposed-check",
                "text": "check.checkout.tests for module.checkout: found pytest",
                "data": {"id": "check.checkout.tests", "module": "module.checkout"},
            }
        ],
    ),
}
# What a survey run that followed an answer declares: the decision, no longer a point.
ANSWERED_SURVEY_OUTPUT = {
    "workflow": step_output(
        decisions=[
            {
                "id": "d.db-helper",
                "question": "own Module?",
                "options": ["yes", "no"],
                "decision": "yes",
                "reason": "answered",
                "decided_by": "main-agent",
                "module": "module.shop",
            }
        ]
    )
}


def describe_output(module: str, questions=()) -> dict:
    return {"modules": [module], "workflow": step_output(decision_points=questions)}


def created_output(*created) -> dict:
    return {"workflow": step_output(data={"created_modules": list(created)})}


def ready_output(ready: bool = True) -> dict:
    return {
        "workflow": step_output(
            data={"ready": ready},
            blocking=None
            if ready
            else {"code": "not_ready", "detail": "a check failed"},
        )
    }


class StepTests(unittest.TestCase):
    def setUp(self):
        self.project = BrownfieldProject(self)
        self.project.open_task()
        self.primary = self.project.root
        self.space = store.workspace(self.project.worktree())
        self.store = self.space.store
        self.runs = Runs(self.store)
        self.addCleanup(self.runs.held.close)
        self.started: list[list[str]] = []
        self.placed: list[Path | None] = []

    def request(
        self, key="survey", argv=("survey", "--modules", "module.shop"), **changes
    ):
        value = {
            "workflow": "brownfield",
            "mode": "no-ask",
            "key": key,
            "argv": list(argv),
            "answers": None,
            "retry": False,
            "restart": None,
        }
        value.update(changes)
        return value

    def starter(self, status="ok", output=None, running=False):
        def start(workflow, space, argv, trace_at=None):
            self.started.append(list(argv))
            self.placed.append(trace_at)
            run_id = self.runs.make(
                argv[0], status, output, running=running, folder=trace_at
            )
            return {"run_id": run_id}

        return patch.object(steps, "start_run", side_effect=start)

    def test_the_schemas_are_the_contracts(self):
        path = "specs/concorde/workflows/contracts.md"
        for identity, schema in (
            ("contract.workflows.step", STEP_SCHEMA),
            ("contract.workflows.step-request", REQUEST_SCHEMA),
            ("contract.workflows.result", RESULT_SCHEMA),
        ):
            with self.subTest(identity=identity):
                self.assertEqual(contract(path, identity), schema)

    def test_the_workspace_is_the_task_worktree_and_its_traces_the_primarys(self):
        self.assertEqual("adopt", self.space.name)
        self.assertEqual(self.project.worktree(), self.space.root)
        concorde = self.primary / ".concorde"
        self.assertEqual(
            (concorde, concorde / "tasks/adopt/workspace"),
            (self.store.concorde, self.store.workspace),
        )
        self.assertEqual(
            concorde / "tasks/adopt/workspace/workflow", self.space.directory
        )
        self.assertEqual(concorde / "locks/workflows/adopt.lock", self.space.lock)

    @verifies("scenario.workflows.step-starts")
    def test_a_step_starts_and_records_a_run(self):
        with self.starter(output=SURVEY_OUTPUT):
            status, outcome = run_step(self.space, self.request())
        self.assertEqual(0, status)
        self.assertEqual([["survey", "--modules", "module.shop"]], self.started)
        self.assertEqual(
            ("finished", "ok", 1, "adopt", "survey"),
            (
                outcome["state"],
                outcome["status"],
                outcome["decision_points"],
                outcome["workspace"],
                outcome["name"],
            ),
        )
        record = store.load(self.space)
        self.assertEqual(
            ("brownfield", "adopt"), (record["workflow"], record["workspace"])
        )
        self.assertEqual(["survey"], [s["key"] for s in record["steps"]])
        self.assertEqual(outcome["run_id"], record["steps"][0]["run_id"])
        validate(outcome, STEP_SCHEMA)
        # The workflow record is the content of the workflow's node in the workspace folder.
        workflow = trace.read(self.store.workspace / "workflow")
        self.assertEqual(
            ("workflow", "concorde-workflow-trace"),
            (workflow["kind"], workflow["content"]["type_id"]),
        )
        [entry] = workflow["content"]["data"]["steps"]
        self.assertEqual(("survey", "steps/1-survey"), (entry["key"], entry["node"]))
        # The run's node lies in run/ of the step's node, which names the key and the run.
        step = self.space.directory / "steps/1-survey"
        self.assertEqual([step / "run"], self.placed)
        self.assertEqual(step / "run", self.store.find(outcome["run_id"]))
        self.assertEqual(outcome["run_id"], trace.read(step / "run")["id"])
        node = trace.read(step)
        self.assertEqual(("step", "survey"), (node["kind"], node["id"]))
        self.assertEqual(
            ("survey", outcome["run_id"], "finished"),
            tuple(node["content"]["data"][k] for k in ("key", "run_id", "state")),
        )
        self.assertEqual("ok", node["status"])

    @verifies("scenario.workflows.step-starts-command")
    def test_a_real_step_runs_detached_with_the_worktrees_concorde(self):
        _status, outcome = run_step(
            self.space, self.request("validate", ("task-validation",)), wait=120
        )
        self.assertIn(outcome["state"], ("finished",), outcome)
        self.assertEqual("task-validation", outcome["name"])
        self.assertIsNotNone(outcome["status"])
        # Validation hands the readiness to the script under the step output convention.
        self.assertIn(outcome["data"].get("ready"), (True, False))
        runs = {run["run_id"]: run for run in workspace_runs(self.store, "adopt")}
        self.assertIn(outcome["run_id"], runs)
        self.assertEqual("command", runs[outcome["run_id"]]["kind"])
        # The detached runner placed the run's node in the step's node.
        self.assertEqual(
            self.space.directory / "steps/1-validate/run",
            self.store.find(outcome["run_id"]),
        )

    @verifies("scenario.workflows.step-waits")
    def test_a_long_run_is_awaited_by_repeated_calls(self):
        with self.starter(status=None, running=True):
            before = time.monotonic()
            status, outcome = run_step(self.space, self.request(), wait=0.3)
            self.assertLess(time.monotonic() - before, 5)
            self.assertEqual((3, "running"), (status, outcome["state"]))
            status, again = run_step(self.space, self.request(), wait=0.1)
        self.assertEqual(1, len(self.started))
        self.assertEqual(outcome["run_id"], again["run_id"])

    @verifies("scenario.workflows.step-retired")
    def test_a_step_waiting_while_its_task_closes_is_refused(self):
        from concorde.coordination.tasks import store as tasks

        with self.starter(output=SURVEY_OUTPUT):
            run_step(self.space, self.request())
        waiting = {}
        threads = []
        dirty = tasks._dirty

        def meanwhile(worktree):
            # The close holds the workflow lock now, before it removes the worktree: a step
            # asked for meanwhile waits for that lock.
            def ask():
                waiting["outcome"] = run_step(
                    self.space, self.request("validate", ("task-validation",))
                )

            thread = threading.Thread(target=ask)
            thread.start()
            threads.append(thread)
            wait_blocked(self.space.lock)
            return dirty(worktree)

        with self.starter(), patch.object(tasks, "_dirty", side_effect=meanwhile):
            tasks.close_task(
                self.primary, "adopt", "failed", note="abandoned", force=True
            )
        [thread] = threads
        thread.join(30)
        history = self.primary / ".concorde/history/adopt"
        closed = {
            path.relative_to(history).as_posix(): path.read_bytes()
            for path in sorted(history.rglob("*"))
            if path.is_file()
        }
        status, value = waiting["outcome"]
        self.assertEqual(
            (1, "refused", None), (status, value["state"], value["run_id"])
        )
        validate(value, STEP_SCHEMA)
        self.assertEqual(
            ["workspace_retired", "lock_removed"], errors.codes(value["error"])
        )
        self.assertEqual("environment", value["error"]["unhandled"]["reason"])
        self.assertIn(str(self.space.lock), json.dumps(value["error"]))
        self.assertEqual([["survey", "--modules", "module.shop"]], self.started)
        # Nothing of the step lies in the history, and no workspace folder came back.
        self.assertFalse((self.primary / ".concorde/tasks/adopt").exists())
        self.assertFalse(any("validate" in name for name in closed))
        # A step that takes the lock after the close finds the binding gone, and so does a
        # report; neither writes anything.
        status, value = run_step(
            self.space, self.request("validate", ("task-validation",))
        )
        self.assertEqual(
            ["workspace_retired", "binding_gone"], errors.codes(value["error"])
        )
        with self.assertRaises(store.WorkspaceRetired) as raised:
            report(self.space)
        self.assertEqual(
            ("workspace_retired", "binding_gone"),
            (raised.exception.code, raised.exception.found),
        )
        self.assertFalse((self.primary / ".concorde/tasks/adopt").exists())
        self.assertEqual(
            closed,
            {
                path.relative_to(history).as_posix(): path.read_bytes()
                for path in sorted(history.rglob("*"))
                if path.is_file()
            },
        )
        self.assertEqual(1, len(self.started))

    @verifies("scenario.workflows.step-retired")
    def test_a_step_whose_binding_changed_is_refused(self):
        path = self.space.root / ".concorde/workspace.json"
        changed = json.loads(path.read_text())
        changed["goal"] = "another goal"
        path.write_text(json.dumps(changed))
        with self.starter(output=SURVEY_OUTPUT):
            status, value = run_step(self.space, self.request())
        self.assertEqual((1, "refused"), (status, value["state"]))
        self.assertEqual(
            ["workspace_retired", "binding_changed"], errors.codes(value["error"])
        )
        self.assertIn("goal", value["error"]["causes"][0]["detail"])
        self.assertEqual([], self.started)
        self.assertFalse(self.space.directory.exists())
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(
                1,
                refused(store.WorkspaceRetired("binding_changed", "changed"), "report"),
            )
        link = json.loads(output.getvalue())["error"]
        self.assertEqual(
            ("workspace_retired", "environment"),
            (link["code"], link["unhandled"]["reason"]),
        )

    def test_a_step_waits_for_the_workspace_without_the_workflow_lock(self):
        # The workflow lock is a leaf: a close holding the workspace lock takes it while a step
        # waits for the workspace.
        with self.starter(output=SURVEY_OUTPUT):
            with workspace_lock(
                self.store, "adopt", "`concorde task close` of task adopt"
            ):
                done = {}
                thread = threading.Thread(
                    target=lambda: done.update(
                        outcome=run_step(self.space, self.request())
                    )
                )
                thread.start()
                deadline = time.monotonic() + 30
                # Once the step has taken the workflow lock and found the workspace busy, the
                # lock is free while it waits.
                while not self.space.lock.exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                while not done and time.monotonic() < deadline:
                    try:
                        with locks.hold(self.space.lock, "close", wait=0):
                            break
                    except locks.LockBusy:
                        time.sleep(0.02)
                else:
                    self.fail("the step kept the workflow lock while it waited")
            thread.join(30)
        self.assertEqual("finished", done["outcome"][1]["state"])

    @verifies("scenario.workflows.step-cached")
    def test_a_finished_step_returns_at_once(self):
        with self.starter(output=SURVEY_OUTPUT):
            _, first = run_step(self.space, self.request())
            status, again = run_step(self.space, self.request())
        self.assertEqual(1, len(self.started))
        self.assertEqual((0, first["run_id"]), (status, again["run_id"]))

    @verifies("scenario.workflows.step-retried")
    def test_retry_runs_a_failed_step_again(self):
        validation = ("validate", ("task-validation",))
        with self.starter(status="failed"):
            run_step(self.space, self.request(*validation))
            _, failed = run_step(self.space, self.request(*validation))
        self.assertEqual("failed", failed["status"])
        self.assertEqual(1, len(self.started))
        with self.starter(status="ok"):
            _status, retried = run_step(
                self.space, self.request(*validation, retry=True)
            )
        self.assertEqual(2, len(self.started))
        self.assertEqual("validate", retried["key"])
        self.assertNotEqual(failed["run_id"], retried["run_id"])

    @verifies("scenario.workflows.restarted")
    def test_a_restart_generation_reruns_an_ok_step_once(self):
        with self.starter(output=SURVEY_OUTPUT):
            run_step(self.space, self.request())
        with self.starter(output=created_output()):
            _, first = run_step(self.space, self.request("scaffold", ("scaffold",)))
            run_step(self.space, self.request("validate", ("task-validation",)))
            _, again = run_step(
                self.space, self.request("scaffold", ("scaffold",), restart="2")
            )
        self.assertEqual("scaffold#2", again["key"])
        self.assertNotEqual(first["run_id"], again["run_id"])
        record = store.load(self.space)
        self.assertEqual(
            ["survey", "scaffold#2"], [s["key"] for s in store.current_steps(record)]
        )
        started = len(self.started)
        with self.starter(output=created_output()):
            _, same = run_step(
                self.space, self.request("scaffold", ("scaffold",), restart="2")
            )
        self.assertEqual(
            (again["run_id"], started), (same["run_id"], len(self.started))
        )

    @verifies("scenario.workflows.step-refused")
    def test_a_step_that_does_not_belong_is_rejected(self):
        with self.starter(output=SURVEY_OUTPUT):
            run_step(self.space, self.request())
            for request, code in (
                (self.request(workflow="other"), "workflow_conflict"),
                (self.request(argv=("task-validation",)), "step_conflict"),
            ):
                with self.subTest(code=code):
                    status, value = run_step(self.space, request)
                    self.assertEqual((1, "refused"), (status, value["state"]))
                    self.assertIsNone(value["run_id"])
                    link = value["error"]
                    self.assertEqual(
                        ("workflow", "step_rejected"), (link["level"], link["code"])
                    )
                    self.assertEqual(code, link["causes"][0]["code"])
        self.assertEqual(1, len(self.started))
        self.assertEqual(1, len(store.load(self.space)["steps"]))

    @verifies("scenario.workflows.refused-step")
    def test_a_step_whose_run_cannot_start_is_recorded_without_a_run(self):
        status, outcome = run_step(
            self.space, self.request("validate", ("task-validation", "--bogus"))
        )
        self.assertEqual((1, "refused"), (status, outcome["state"]))
        self.assertIsNone(outcome["run_id"])
        self.assertEqual("step_refused", outcome["error"]["code"])
        self.assertIn("--bogus", json.dumps(outcome["error"]))
        [recorded] = store.load(self.space)["steps"]
        self.assertIsNone(recorded["run_id"])
        self.assertEqual("step_refused", recorded["error"]["code"])
        result = report(self.space)
        self.assertEqual("failed", result["status"])
        self.assertEqual("step_refused", result["problems"][0]["error"]["code"])

    @verifies("scenario.workflows.lost")
    def test_a_step_whose_host_died_is_lost(self):
        with self.starter(status=None):
            status, outcome = run_step(
                self.space, self.request("describe:module.shop", ("code_to_spec",))
            )
        self.assertEqual((1, "lost"), (status, outcome["state"]))
        self.assertEqual("step_lost", outcome["error"]["code"])
        result = report(self.space, ["describe:module.shop"])
        self.assertEqual("failed", result["status"])
        self.assertEqual("lost", result["problems"][0]["status"])

    @verifies("scenario.workflows.lost-finished")
    def test_a_key_reported_lost_keeps_its_finished_run(self):
        with self.starter(output=SURVEY_OUTPUT):
            run_step(self.space, self.request())
        result = report(self.space, ["survey"])
        self.assertEqual(
            "ok", {s["key"]: s["status"] for s in result["steps"]}["survey"]
        )
        self.assertEqual([], [p for p in result["problems"] if p["step"] == "survey"])

    @verifies("scenario.workflows.superseded")
    def test_a_retried_step_supersedes_later_steps(self):
        with self.starter(output=SURVEY_OUTPUT):
            run_step(self.space, self.request())
        with self.starter(status="failed"):
            run_step(
                self.space,
                self.request("describe:module.checkout", ("code_to_spec",)),
            )
        with self.starter(status="ok", output=ready_output()):
            run_step(self.space, self.request("validate", ("task-validation",)))
            run_step(self.space, self.request("delivery", ("delivery",)))
        with self.starter(status="ok", output=describe_output("module.checkout")):
            run_step(
                self.space,
                self.request("describe:module.checkout", ("code_to_spec",), retry=True),
            )
        record = store.load(self.space)
        current = [s["key"] for s in store.current_steps(record)]
        self.assertEqual(["survey", "describe:module.checkout"], current)
        before = len(self.started)
        with self.starter(status="ok", output=ready_output()):
            run_step(self.space, self.request("validate", ("task-validation",)))
        self.assertEqual(before + 1, len(self.started))
        result = report(self.space)
        self.assertEqual(
            ["describe:module.checkout", "validate", "delivery"],
            [s["key"] for s in result["superseded"]],
        )

    @verifies("scenario.workflows.superseded")
    def test_a_superseded_step_breaking_the_convention_still_reports(self):
        # The step is recorded before its outcome refuses the object, as the step command does.
        with (
            self.starter(output={"workflow": {"decision_points": []}}),
            self.assertRaises(StepOutputError),
        ):
            run_step(self.space, self.request())
        # The run ended ok, so only a restart label runs the step again and supersedes it.
        with self.starter(output=SURVEY_OUTPUT):
            run_step(self.space, self.request(restart="2"))
        result = report(self.space)
        self.assertEqual(["survey"], [s["key"] for s in result["superseded"]])
        self.assertEqual(["d.db-helper"], [d["id"] for d in result["decisions"]])

    @verifies("scenario.workflows.interactive-resume")
    def test_answers_make_a_new_step_that_admits_the_asking_run(self):
        with self.starter(output=SURVEY_OUTPUT):
            _, first = run_step(self.space, self.request(mode="interactive"))
        answers = [
            {
                "id": "d.db-helper",
                "question": "own Module?",
                "answer": "yes",
                "answered_by": "main-agent",
            }
        ]
        followed = ANSWERED_SURVEY_OUTPUT
        with self.starter(output=followed):
            _, second = run_step(
                self.space, self.request(mode="interactive", answers=answers)
            )
        self.assertEqual(step_key("survey", answers), second["key"])
        argv = self.started[-1]
        self.assertEqual(first["run_id"], argv[argv.index("--input") + 1])
        answers_file = Path(argv[argv.index("--answers") + 1])
        self.assertEqual(self.space.directory / "answers", answers_file.parent)
        self.assertEqual({"answers": answers}, json.loads(answers_file.read_text()))
        self.assertEqual(0, second["decision_points"])
        # The result credits the decision to whoever gave the answer.
        decision = report(self.space)["decisions"][0]
        self.assertEqual(
            ("d.db-helper", "main-agent"), (decision["id"], decision["decided_by"])
        )
        # The same answers find the same step again.
        with self.starter(output=followed):
            _, again = run_step(
                self.space, self.request(mode="interactive", answers=answers)
            )
        self.assertEqual(second["run_id"], again["run_id"])

    @verifies("scenario.workflows.step-waits-lock")
    def test_a_step_waits_while_another_run_of_the_workspace_runs(self):
        with self.starter(output=SURVEY_OUTPUT):
            with workspace_lock(self.store, "adopt", "Operation implement r-other"):
                status, value = run_step(self.space, self.request(), wait=0.3)
                self.assertEqual(
                    (3, "running", None), (status, value["state"], value["run_id"])
                )
                self.assertEqual([], self.started)
                self.assertEqual([], store.current_steps(store.load(self.space)))
            status, value = run_step(self.space, self.request())
        self.assertEqual((0, "finished"), (status, value["state"]))
        self.assertEqual(1, len(self.started))

    def test_answered_points_are_no_longer_decision_points(self):
        answers = [
            {
                "id": "q.retry",
                "question": "retries",
                "answer": "keep",
                "answered_by": "developer",
            }
        ]
        with self.starter(output=describe_output("module.checkout", [QUESTION])):
            _, value = run_step(
                self.space,
                self.request(
                    "describe:module.checkout",
                    ("code_to_spec",),
                    mode="interactive",
                    answers=answers,
                ),
            )
        self.assertEqual(0, value["decision_points"])
        self.assertEqual([], report(self.space)["pending"])

    @verifies("scenario.workflows.interactive-resume")
    def test_a_retried_answered_step_still_admits_the_asking_run(self):
        with self.starter(output=SURVEY_OUTPUT):
            _, first = run_step(self.space, self.request(mode="interactive"))
        answers = [
            {
                "id": "d.db-helper",
                "question": "own Module?",
                "answer": "yes",
                "answered_by": "developer",
            }
        ]
        with self.starter(status="failed"):
            run_step(self.space, self.request(mode="interactive", answers=answers))
        with self.starter(output=SURVEY_OUTPUT):
            run_step(
                self.space,
                self.request(mode="interactive", answers=answers, retry=True),
            )
        argv = self.started[-1]
        self.assertEqual(first["run_id"], argv[argv.index("--input") + 1])

    @verifies("scenario.workflows.lost")
    def test_a_lost_step_carries_its_host_output(self):
        validation = ("validate", ("task-validation",))
        with self.starter(status=None):
            _, value = run_step(self.space, self.request(*validation), wait=0)
        (self.store.find(value["run_id"]) / "host.out").write_text(
            "Traceback: KeyError: 'modules'\n"
        )
        _, value = run_step(self.space, self.request(*validation))
        self.assertEqual("lost", value["state"])
        self.assertIn("KeyError", json.dumps(value["error"]["evidence"]))
        self.assertEqual("host_ended", value["error"]["causes"][0]["code"])
        self.assertIn(
            "KeyError",
            report(self.space)["problems"][0]["error"]["causes"][0]["detail"],
        )

    def test_a_started_run_that_cannot_be_recorded_is_named(self):
        with (
            self.starter(output=SURVEY_OUTPUT),
            patch.object(
                store,
                "record_step",
                side_effect=store.WorkflowError("record_conflict", "busy"),
            ),
        ):
            status, value = run_step(self.space, self.request())
        self.assertEqual((1, "refused"), (status, value["state"]))
        self.assertEqual("step_unrecorded", value["error"]["code"])
        self.assertIsNotNone(value["run_id"])
        self.assertIn(value["run_id"], value["error"]["detail"])
        self.assertEqual("record_conflict", value["error"]["causes"][0]["code"])


def _pid_sandbox() -> list[str] | None:
    """A bubblewrap command prefix that runs a command in a PID namespace of its own, as Claude
    Code's Bash sandbox runs each call, or None where bubblewrap cannot make one.

    As in that sandbox, the system is read-only and only the temporary directory, which holds
    the test project, is writable: the read-only check boundary trusts the system bubblewrap
    that a user namespace shows with an unmapped owner only on a read-only mount, so the run's
    checks can still start inside this namespace."""
    temporary = tempfile.gettempdir()
    prefix = [
        "bwrap",
        "--unshare-pid",
        "--die-with-parent",
        "--ro-bind",
        "/",
        "/",
        "--bind",
        temporary,
        temporary,
        "--dev",
        "/dev",
        "--proc",
        "/proc",
    ]
    try:
        done = subprocess.run(
            [*prefix, "true"], capture_output=True, timeout=30, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return prefix if done.returncode == 0 else None


class SandboxTests(unittest.TestCase):
    """Why a step's run must not be started from a sandboxed Bash call."""

    def setUp(self):
        self.sandbox = _pid_sandbox()
        if self.sandbox is None:
            self.skipTest("bubblewrap cannot make a PID namespace here")
        self.project = BrownfieldProject(self)
        checks = self.project.root / ".concorde/checks/module.shop.json"
        checks.parent.mkdir(parents=True, exist_ok=True)
        checks.write_text(
            json.dumps(
                {
                    "checks": [
                        {
                            "id": "check.shop.slow",
                            "argv": ["sleep", "30"],
                            "timeout_seconds": 120,
                            "inputs": ["src"],
                        }
                    ]
                }
            )
        )
        commit_all(self.project.root, "a slow check")
        self.project.open_task()
        self.worktree = self.project.worktree()

    @verifies("scenario.execution.detached-namespace")
    def test_a_run_detached_inside_a_pid_namespace_dies_with_it(self):
        request = json.dumps(
            {
                "workflow": "brownfield",
                "mode": "no-ask",
                "key": "validate",
                "argv": ["task-validation"],
            }
        )
        command = [
            sys.executable,
            str(REPOSITORY_ROOT / "scripts/concorde.py"),
            "workflow",
            "step",
            "--json",
            request,
        ]
        first = subprocess.run(
            [*self.sandbox, *command, "--wait", "2"],
            cwd=self.worktree,
            capture_output=True,
            text=True,
            check=False,
        )
        started = json.loads(first.stdout)
        self.assertEqual("running", started["state"], first.stdout + first.stderr)
        # The call is over and its namespace with it: the runner was killed without a word.
        again = subprocess.run(
            [*command, "--wait", "5"],
            cwd=self.worktree,
            capture_output=True,
            text=True,
            check=False,
        )
        lost = json.loads(again.stdout)
        self.assertEqual(
            ("lost", started["run_id"], "step_lost", "host_ended"),
            (
                lost["state"],
                lost["run_id"],
                lost["error"]["code"],
                lost["error"]["causes"][0]["code"],
            ),
        )


class CliTests(unittest.TestCase):
    """``concorde workflow step|report`` work only in a bound workspace."""

    def setUp(self):
        self.project = BrownfieldProject(self)

    def main(self, argv, cwd: Path) -> tuple[int, dict]:
        import contextlib
        import io

        from concorde.workflows import cli as workflow_cli

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = workflow_cli.main(argv, cwd)
        return status, json.loads(output.getvalue())

    @verifies("scenario.workflows.unbound-refused")
    def test_an_unbound_worktree_runs_no_workflow(self):
        step = ["step", "--workflow", "brownfield", "--mode", "no-ask"]
        for argv in ([*step, "--key", "survey", "--", "survey"], ["report"]):
            with self.subTest(command=argv[0]):
                status, value = self.main(argv, self.project.root)
                self.assertEqual(1, status)
                link = value["error"]
                self.assertEqual(
                    ("component", "binding_required"), (link["level"], link["code"])
                )
                self.assertIn(str(self.project.root), link["detail"])

    def test_a_report_before_any_step_says_there_is_nothing_to_report(self):
        self.project.open_task()
        status, value = self.main(["report"], self.project.worktree())
        self.assertEqual(1, status)
        self.assertEqual("no_workflow", value["error"]["code"])
        self.assertIn("adopt", value["error"]["detail"])


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.project = BrownfieldProject(self)
        self.project.open_task()
        self.primary = self.project.root
        self.space = store.workspace(self.project.worktree())
        self.runs = Runs(self.space.store)
        self.addCleanup(self.runs.held.close)

    def record(
        self,
        key,
        name,
        status="ok",
        output=None,
        mode="no-ask",
        error=None,
        running=False,
    ):
        """Record a step whose run is traced in the step's node, as a real step's is."""
        folder = store.next_step_folder(self.space, store.load(self.space), key)
        run_id = self.runs.make(
            name, status, output, error=error, running=running, folder=folder / "run"
        )
        store.record_step(
            self.space, "brownfield", key, name, run_id, mode, None, folder=folder
        )
        return run_id

    def complete(self, describe_status="ok"):
        self.record("survey", "survey", output=SURVEY_OUTPUT)
        self.record("scaffold", "scaffold", output=created_output())
        self.record(
            "describe:module.inventory",
            "code_to_spec",
            describe_status,
            describe_output("module.inventory") if describe_status == "ok" else None,
        )
        self.record(
            "describe:module.checkout",
            "code_to_spec",
            output=describe_output("module.checkout", [QUESTION]),
        )
        self.record(
            "spec_review",
            "spec_review",
            output={
                "verdict": "changes_required",
                "workflow": step_output(
                    notes=[
                        {
                            "kind": "review",
                            "text": "spec_review verdict changes_required: "
                            "module.checkout changes_required",
                            "data": {
                                "verdict": "changes_required",
                                "modules": [
                                    {
                                        "module": "module.checkout",
                                        "outcome": "changes_required",
                                        "blocking": 2,
                                    }
                                ],
                            },
                        }
                    ],
                    deviations=[
                        {
                            "subject": "the answer to q.retry",
                            "intended": "keep",
                            "observed": "dropped",
                            "point": "q.retry",
                        }
                    ],
                ),
            },
        )
        self.record("validate", "task-validation", output=ready_output())
        self.record("delivery", "delivery", output={})

    @verifies("scenario.workflows.no-ask-complete")
    @verifies("scenario.workflows.reviews-reported")
    @verifies("scenario.workflows.report-ignores-relay")
    def test_a_no_ask_run_reports_everything(self):
        self.complete(describe_status="blocked")
        result = report(self.space)
        validate(result, RESULT_SCHEMA)
        self.assertEqual(("ok", "adopt"), (result["status"], result["workspace"]))
        self.assertIsNone(result["error"])
        self.assertEqual(["d.db-helper"], [d["id"] for d in result["decisions"]])
        self.assertEqual("small", result["decisions"][0]["reason"])
        # Every declared item, as its run declared it, with its step and run.
        self.assertEqual(
            [("survey", "d.db-helper"), ("describe:module.checkout", "q.retry")],
            [(p["step"], p["id"]) for p in result["decision_points"]],
        )
        self.assertEqual(
            {
                k: v
                for k, v in result["decision_points"][1].items()
                if k not in ("step", "run_id")
            },
            QUESTION,
        )
        self.assertEqual(
            [("survey", "proposed-check"), ("spec_review", "review")],
            [(n["step"], n["kind"]) for n in result["notes"]],
        )
        # The review note is listed unchanged, with its step and run.
        review = result["notes"][1]
        self.assertEqual(
            "spec_review verdict changes_required: module.checkout changes_required",
            review["text"],
        )
        self.assertEqual(2, review["data"]["modules"][0]["blocking"])
        self.assertEqual("changes_required", review["data"]["verdict"])
        self.assertIn("run_id", review)
        self.assertEqual(["q.retry"], [d["point"] for d in result["deviations"]])
        # No interactive stop: a no-ask run reports its points without pending any.
        self.assertEqual([], result["pending"])
        self.assertEqual(
            "task-validation",
            {s["key"]: s["name"] for s in result["steps"]}["validate"],
        )
        [problem] = result["problems"]
        self.assertEqual(
            ("describe:module.inventory", "blocked"),
            (problem["step"], problem["status"]),
        )
        self.assertEqual("code_to_spec_blocked", problem["error"]["code"])
        # The report is saved with its rendering beside the workflow record, not logged.
        [entry] = store.load(self.space)["reports"]
        self.assertEqual("ok", entry["status"])
        self.assertEqual(self.space.directory / "reports/1.json", Path(entry["path"]))
        saved = json.loads(Path(entry["path"]).read_text())
        self.assertEqual(result["summary"], saved["summary"])
        rendering = Path(entry["rendered"]).read_text()
        self.assertIn("Workflow brownfield report: ok", rendering)
        self.assertIn("q.retry", rendering)
        self.assertIn("check.checkout.tests", rendering)
        self.assertIn("spec_review verdict changes_required", rendering)
        log = self.primary / ".concorde/tasks/adopt/decisions.md"
        if log.exists():
            self.assertNotIn("Workflow brownfield report", log.read_text())
        report(self.space)
        self.assertEqual(
            ["1.json", "1.md", "2.json", "2.md"],
            sorted(p.name for p in (self.space.directory / "reports").iterdir()),
        )
        # The report ended the workflow's node with its status; every step's node has ended.
        workflow = trace.read(self.space.directory)
        self.assertEqual(("ok", "ok"), (workflow["status"], workflow["outcome"]))
        self.assertEqual(
            ["reports/1.json", "reports/2.json"],
            [item["path"] for item in workflow["content"]["data"]["reports"]],
        )
        ended = {
            item["key"]: trace.read(self.space.directory / item["node"])["status"]
            for item in workflow["content"]["data"]["steps"]
        }
        self.assertEqual("blocked", ended["describe:module.inventory"])
        self.assertEqual("ok", ended["survey"])

    @verifies("scenario.workflows.interactive-pause")
    def test_an_interactive_run_ends_at_survey_decisions(self):
        self.record("survey", "survey", output=SURVEY_OUTPUT, mode="interactive")
        result = report(self.space)
        self.assertEqual("awaiting_decision", result["status"])
        self.assertEqual(["d.db-helper"], [p["id"] for p in result["pending"]])
        self.assertEqual(["yes", "no"], result["pending"][0]["options"])
        self.assertEqual(
            ("workflow", "awaiting_decision", "decision"),
            (
                result["error"]["level"],
                result["error"]["code"],
                result["error"]["unhandled"]["reason"],
            ),
        )

    @verifies("scenario.workflows.failed-chain")
    def test_a_stopping_step_keeps_its_chain_under_the_workflow_link(self):
        self.record("survey", "survey", output=SURVEY_OUTPUT)
        cause = run_link("scaffold", "r-x", "stale_proposal")
        cause["causes"] = [
            errors.link(
                "component",
                "Spec core",
                "missing",
                "gone",
                reason="input",
                explanation="x",
            )
        ]
        self.record("scaffold", "scaffold", "blocked", error=cause)
        result = report(self.space)
        self.assertEqual("blocked", result["status"])
        error = result["error"]
        self.assertEqual(("workflow", "step_blocked"), (error["level"], error["code"]))
        self.assertEqual([cause], error["causes"])

    def test_only_the_registered_last_step_makes_the_workflow_ok(self):
        self.complete()
        self.record("extra", "task-validation", output=ready_output())
        result = report(self.space)
        self.assertEqual(
            ("failed", "incomplete"), (result["status"], result["error"]["code"])
        )
        self.assertIn("delivery", result["error"]["detail"])

    def test_a_step_declaring_blocking_stops_the_workflow_blocked(self):
        self.record("survey", "survey", output=SURVEY_OUTPUT)
        self.record("validate", "task-validation", output=ready_output(False))
        result = report(self.space)
        self.assertEqual(
            ("blocked", "step_blocked"), (result["status"], result["error"]["code"])
        )
        [evidence] = result["error"]["evidence"]
        self.assertEqual(
            ("blocking", "validate not_ready"), (evidence["kind"], evidence["ref"])
        )

    def test_an_unregistered_workflow_is_never_ok(self):
        self.complete()
        with patch.dict(catalog.WORKFLOWS, clear=True):
            result = report(self.space)
        self.assertEqual(
            ("failed", "incomplete"), (result["status"], result["error"]["code"])
        )
        self.assertIn("no installed part registers", result["error"]["detail"])

    def test_a_run_breaking_the_convention_fails_the_report(self):
        self.record("survey", "survey", output={"workflow": {"decision_points": []}})
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            from concorde.workflows import cli as workflow_cli

            status = workflow_cli.main(["report"], self.project.worktree())
        self.assertEqual(1, status)
        link = json.loads(output.getvalue())["error"]
        self.assertEqual("report_failed", link["code"])
        self.assertIn("contract.workflows.step-output", link["detail"])

    def test_the_report_tool_reads_a_saved_report_by_workspace_folder(self):
        from concorde.workflows import tools

        with self.assertRaises(tools.ToolRefusal) as refused:
            tools.workflow_report(self.project.worktree(), {})
        self.assertEqual("no_report", refused.exception.link["code"])
        self.complete()
        first = report(self.space)
        second = report(self.space)
        # Without a folder, the folder the binding of the session's worktree names.
        value = tools.workflow_report(self.project.worktree(), {})
        folder = self.space.store.workspace.as_posix()
        self.assertEqual((folder, 2), (value["folder"], value["number"]))
        self.assertEqual(second["reported_at"], value["report"]["reported_at"])
        # From anywhere, even an unbound worktree, with the workspace folder.
        value = tools.workflow_report(self.primary, {"folder": folder, "number": 1})
        self.assertEqual(first["summary"], value["report"]["summary"])
        with self.assertRaises(tools.ToolRefusal) as refused:
            tools.workflow_report(self.primary, {})
        self.assertEqual("unbound_worktree", refused.exception.link["code"])
        with self.assertRaises(tools.ToolRefusal) as refused:
            tools.workflow_report(self.primary, {"folder": folder, "number": 9})
        self.assertEqual("no_report", refused.exception.link["code"])

    def test_a_report_during_a_running_step(self):
        self.record("survey", "survey", None, running=True)
        result = report(self.space)
        self.assertEqual("running", result["status"])
        self.assertEqual("step_running", result["error"]["code"])

    def test_a_report_that_cannot_be_built_answers_with_an_error_link(self):
        import contextlib
        import io

        from concorde.workflows import cli as workflow_cli

        output = io.StringIO()
        with (
            patch.object(workflow_cli, "report", side_effect=RuntimeError("boom")),
            contextlib.redirect_stdout(output),
        ):
            status = workflow_cli.main(["report"], self.project.worktree())
        self.assertEqual(1, status)
        link = json.loads(output.getvalue())["error"]
        self.assertEqual("report_failed", link["code"])
        self.assertIn("boom", link["detail"])
        self.assertIn("adopt", link["detail"])


class ScriptTests(unittest.TestCase):
    """The rendered script, run under a stand-in for Claude Code's workflow runtime."""

    def setUp(self):
        self.directory = Path(self.id().replace(".", "_"))

    def run_script(self, args, outcomes, report_status="ok"):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "script.js"
            script.write_text(catalog.render("brownfield"))
            completed = subprocess.run(
                ["node", str(HARNESS)],
                input=json.dumps(
                    {
                        "script": str(script),
                        "args": args,
                        "outcomes": outcomes,
                        "report": {"status": report_status, "summary": "s"},
                    }
                ),
                capture_output=True,
                text=True,
                check=True,
            )
        return json.loads(completed.stdout)

    def outcome(self, key, name, status="ok", points=0, data=None, blocking=None):
        return {
            "workflow": "brownfield",
            "workspace": "adopt",
            "key": key,
            "name": name,
            "run_id": "r-20260925T100000-x-00000000",
            "state": "finished",
            "status": status,
            "summary": "s",
            "result_path": "p",
            "decision_points": points,
            "blocking": blocking,
            "data": dict(data or {}),
            "error": None,
        }

    def full(self, points=0, describe_status="ok"):
        created = [
            {"id": "module.checkout", "uses": ["module.inventory"]},
            {"id": "module.inventory", "uses": []},
        ]
        return {
            "survey": self.outcome("survey", "survey", points=points),
            "scaffold": self.outcome(
                "scaffold", "scaffold", data={"created_modules": created}
            ),
            "describe:module.inventory": self.outcome(
                "describe:module.inventory", "code_to_spec", describe_status
            ),
            "describe:module.checkout": self.outcome(
                "describe:module.checkout", "code_to_spec"
            ),
            "describe:module.shop": self.outcome(
                "describe:module.shop", "code_to_spec"
            ),
            "spec_review": self.outcome("spec_review", "spec_review"),
            "validate": self.outcome(
                "validate", "task-validation", data={"ready": True}
            ),
            "delivery": self.outcome("delivery", "delivery"),
        }

    ARGS: ClassVar[dict] = {"module": "module.shop", "mode": "no-ask"}

    @verifies("scenario.workflows.no-ask-complete")
    def test_the_script_runs_the_whole_procedure_providers_first(self):
        run = self.run_script(self.ARGS, self.full(points=2, describe_status="blocked"))
        self.assertIsNone(run["error"])
        self.assertEqual(
            [
                "survey",
                "scaffold",
                "describe:module.inventory",
                "describe:module.checkout",
                "describe:module.shop",
                "spec_review",
                "validate",
                "delivery",
                "report",
            ],
            [call["key"] for call in run["calls"]],
        )
        review = next(c for c in run["calls"] if c["key"] == "spec_review")
        self.assertEqual(
            [
                "spec_review",
                "--modules",
                "module.inventory,module.checkout,module.shop",
            ],
            review["request"]["argv"],
        )
        self.assertEqual("ok", run["result"]["reported"]["status"])
        self.assertEqual("concorde-brownfield", run["meta"]["name"])
        self.assertEqual("haiku", run["calls"][0]["options"]["model"])

    @verifies("scenario.method.brownfield-mutual-uses")
    def test_modules_that_use_each_other_are_described_as_a_group(self):
        def describe(order, created):
            outcomes = self.full()
            outcomes["scaffold"] = self.outcome(
                "scaffold", "scaffold", data={"created_modules": created}
            )
            for item in created:
                key = "describe:" + item["id"]
                outcomes[key] = self.outcome(key, "code_to_spec")
            run = self.run_script(self.ARGS, outcomes)
            described = [
                c["key"] for c in run["calls"] if c["key"].startswith("describe:")
            ]
            self.assertEqual(["describe:" + m for m in order], described)

        describe(
            ["module.catalog", "module.orders", "module.billing", "module.shop"],
            [
                {"id": "module.orders", "uses": ["module.billing"]},
                {"id": "module.billing", "uses": ["module.orders", "module.catalog"]},
                {"id": "module.catalog", "uses": []},
            ],
        )
        # A cycle followed by an independent Module keeps the scaffold's order.
        describe(
            ["module.a", "module.b", "module.c", "module.shop"],
            [
                {"id": "module.a", "uses": ["module.b"]},
                {"id": "module.b", "uses": ["module.a"]},
                {"id": "module.c", "uses": []},
            ],
        )
        # A consumer listed before its provider waits for it; a later group does not.
        describe(
            ["module.d", "module.c", "module.a", "module.b", "module.shop"],
            [
                {"id": "module.c", "uses": ["module.d"]},
                {"id": "module.a", "uses": ["module.b", "module.c"]},
                {"id": "module.b", "uses": ["module.a"]},
                {"id": "module.d", "uses": ["module.unknown"]},
            ],
        )

    @verifies("scenario.workflows.interactive-pause")
    def test_an_interactive_run_stops_after_the_survey(self):
        run = self.run_script({**self.ARGS, "mode": "interactive"}, self.full(points=1))
        self.assertEqual(["survey", "report"], [c["key"] for c in run["calls"]])

    @verifies("scenario.workflows.interactive-resume")
    def test_answers_and_retries_reach_their_steps(self):
        answers = {
            "survey": [
                {
                    "id": "d.db-helper",
                    "question": "q",
                    "answer": "yes",
                    "answered_by": "main-agent",
                }
            ]
        }
        run = self.run_script(
            {
                **self.ARGS,
                "mode": "interactive",
                "answers": answers,
                "retry": ["validate"],
            },
            self.full(),
        )
        requests = {
            c["key"]: c["request"] for c in run["calls"] if c["key"] != "report"
        }
        self.assertEqual(answers["survey"], requests["survey"]["answers"])
        self.assertNotIn("answers", requests["scaffold"])
        self.assertTrue(requests["validate"]["retry"])
        self.assertNotIn("retry", requests["survey"])

    def test_restart_labels_reach_their_steps(self):
        run = self.run_script({**self.ARGS, "restart": {"scaffold": "2"}}, self.full())
        requests = {
            c["key"]: c["request"] for c in run["calls"] if c["key"] != "report"
        }
        self.assertEqual("2", requests["scaffold"]["restart"])
        self.assertNotIn("restart", requests["survey"])

    def test_interactive_stops_at_a_failed_description_and_no_ask_goes_on(self):
        outcomes = self.full(describe_status="failed")
        interactive = self.run_script({**self.ARGS, "mode": "interactive"}, outcomes)
        self.assertEqual("report", interactive["calls"][-1]["key"])
        self.assertEqual("describe:module.inventory", interactive["calls"][-2]["key"])
        no_ask = self.run_script(self.ARGS, outcomes)
        self.assertIn("delivery", [c["key"] for c in no_ask["calls"]])

    @verifies("scenario.workflows.lost")
    def test_a_step_agent_that_returned_nothing_is_reported_lost(self):
        outcomes = self.full()
        outcomes["scaffold"] = None
        # The step function asks its relay three times before it gives up.
        run = self.run_script(self.ARGS, outcomes)
        self.assertEqual(
            ["survey", *["scaffold"] * 3, "report"], [c["key"] for c in run["calls"]]
        )
        self.assertEqual("scaffold", run["calls"][-1]["lost"])
        self.assertNotIn("relayed", run["result"])

    def test_a_rejected_step_travels_with_the_report(self):
        outcomes = self.full()
        rejected = self.outcome("scaffold", "scaffold")
        rejected.update(
            state="refused",
            status=None,
            run_id=None,
            error={"code": "step_rejected", "level": "workflow"},
        )
        outcomes["scaffold"] = rejected
        run = self.run_script(self.ARGS, outcomes)
        self.assertEqual(
            ["survey", "scaffold", "report"], [c["key"] for c in run["calls"]]
        )
        self.assertEqual("scaffold", run["calls"][-1]["lost"])
        self.assertEqual("step_rejected", run["result"]["rejected"]["error"]["code"])

    def test_a_step_still_running_ends_a_no_ask_run(self):
        outcomes = self.full()
        outcomes["describe:module.inventory"]["state"] = "running"
        run = self.run_script(self.ARGS, outcomes)
        self.assertEqual("report", run["calls"][-1]["key"])
        self.assertEqual("describe:module.inventory", run["calls"][-2]["key"])

    @verifies("scenario.workflows.step-waits")
    def test_the_claude_script_asks_again_while_a_run_is_running(self):
        outcomes = self.full()
        running = dict(
            outcomes["describe:module.inventory"], state="running", status=None
        )
        outcomes["describe:module.inventory"] = [
            running,
            running,
            outcomes["describe:module.inventory"],
        ]
        run = self.run_script(self.ARGS, outcomes)
        keys = [c["key"] for c in run["calls"]]
        self.assertEqual(3, keys.count("describe:module.inventory"))
        self.assertIn("delivery", keys)
        first = next(c for c in run["calls"] if c["key"] == "describe:module.inventory")
        self.assertEqual(100, first["arguments"]["wait"])

    @verifies("scenario.workflows.step-outlives-call")
    def test_step_agents_call_the_project_mcp_servers_step_tool(self):
        run = self.run_script(self.ARGS, self.full())
        steps = [c for c in run["calls"] if c["key"] != "report"]
        self.assertTrue(steps)
        for call in steps:
            with self.subTest(key=call["key"]):
                # One call of the server's tool with the request as an object, never a Bash
                # command, whose sandbox would take the run down with it.
                self.assertEqual("mcp__concorde__workflow_step", call["tool"])
                self.assertEqual({"request", "wait"}, set(call["arguments"]))
                self.assertNotIn("Bash", call["prompt"])
                self.assertNotIn("workflow step", call["prompt"])

    @verifies("scenario.workflows.lost")
    def test_a_relayed_outcome_that_names_no_real_run_counts_as_none(self):
        outcomes = self.full()
        outcomes["scaffold"] = dict(outcomes["scaffold"], run_id="bxy9nbcb9")
        run = self.run_script(self.ARGS, outcomes)
        self.assertEqual(
            ["survey", "scaffold", "scaffold", "scaffold", "report"],
            [c["key"] for c in run["calls"]],
        )
        self.assertEqual("scaffold", run["calls"][-1]["lost"])
        self.assertEqual("bxy9nbcb9", run["result"]["relayed"]["outcome"]["run_id"])

    @verifies("scenario.workflows.relay-refused")
    def test_a_mistyped_request_is_asked_again_and_its_refusal_kept(self):
        refusal = {
            "key": "workflow_step_result",
            "state": "error",
            "error": {"code": "invalid_request", "detail": "/answers: missing"},
        }
        outcomes = self.full()
        outcomes["delivery"] = [refusal, outcomes["delivery"]]
        run = self.run_script(self.ARGS, outcomes)
        keys = [c["key"] for c in run["calls"]]
        self.assertEqual(2, keys.count("delivery"))
        self.assertIsNone(run["calls"][-1]["lost"])
        self.assertNotIn("relayed", run["result"])
        # Requests carry no optional field that holds its default.
        self.assertEqual(
            {"workflow", "mode", "key", "argv"},
            set(run["calls"][-2]["request"]),
        )
        outcomes["delivery"] = [refusal]
        run = self.run_script(self.ARGS, outcomes)
        self.assertEqual(3, [c["key"] for c in run["calls"]].count("delivery"))
        self.assertEqual("delivery", run["calls"][-1]["lost"])
        self.assertEqual(
            {"key": "delivery", "attempts": 3, "outcome": refusal},
            run["result"]["relayed"],
        )

    def test_a_request_without_optional_fields_gets_their_defaults(self):
        value = check_request(
            {
                "workflow": "brownfield",
                "mode": "no-ask",
                "key": "delivery",
                "argv": ["delivery"],
            }
        )
        self.assertEqual(
            (None, False, None), (value["answers"], value["retry"], value["restart"])
        )

    def test_an_unready_validation_ends_the_run_before_delivery(self):
        outcomes = self.full()
        outcomes["validate"] = self.outcome(
            "validate", "task-validation", "blocked", data={"ready": False}
        )
        run = self.run_script(self.ARGS, outcomes)
        self.assertNotIn("delivery", [c["key"] for c in run["calls"]])
        # A step that declares blocking ends the procedure whatever its status.
        outcomes["validate"] = self.outcome(
            "validate",
            "task-validation",
            data={"ready": True},
            blocking={"code": "not_ready", "detail": "d"},
        )
        run = self.run_script(self.ARGS, outcomes)
        self.assertNotIn("delivery", [c["key"] for c in run["calls"]])

    def test_the_last_step_is_the_registered_one(self):
        rendered = catalog.render("brownfield")
        self.assertIn('const LAST_STEP = "delivery"', rendered)
        self.assertEqual("delivery", catalog.get("brownfield").last_step)


if __name__ == "__main__":
    unittest.main()
