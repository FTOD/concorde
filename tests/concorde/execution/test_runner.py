"""The Execution runner: ``concorde run`` and the execution commands, with test definitions
standing in for real ones, the workspace binding it reads and the run store it writes."""

from __future__ import annotations

import contextlib
import errno
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.execution.commands import catalog as commands
from concorde.kernel.errors import ERROR_SCHEMA, LINK_SCHEMA, codes
from concorde.kernel import binding as binding_file
from concorde.execution import runs
from concorde.execution.checkout import PREFIX
from concorde.execution.context import (
    Continue,
    Provider,
    Stop,
    command,
    component,
    evidence,
)
from concorde.method.specs import admission
from concorde.method.workers import operation, run_worker
from concorde.execution import runner
from concorde.execution.runner import (
    ResultUnsaved,
    RunUnrecorded,
    UsageError,
    detach,
    execute,
    run_main,
)
from concorde.execution.runs import RESULT_SCHEMA
from concorde.worker_harness import models, pi_backend
from concorde.execution.checks.checks import run_checks
from concorde.worker_harness.runs import read_record
from concorde.execution.operations import catalog
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.coordination.tasks import store
from concorde.kernel.tracing import locks
from concorde.kernel.tracing import node as trace_node
from concorde.kernel.tracing.node import Node, TraceError
from tests.concorde.harness.workers.test_pi import FAKE as FAKE_PI
from tests.concorde.harness.workers.test_pi import fake_which
from tests.concorde.harness.workers.test_workers import git
from tests.concorde.support.operation_project import OperationProject
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.spec_project import read_checks, write_checks


def head(root: Path) -> str:
    return git(root, "rev-parse", "HEAD").strip()


def worktrees(root: Path) -> list[Path]:
    """The worktrees Git lists for the repository of ``root``, the primary one first."""
    return [
        Path(line.split(" ", 1)[1])
        for line in git(root, "worktree", "list", "--porcelain").splitlines()
        if line.startswith("worktree ")
    ]


def spec_contract(identity: str) -> dict:
    """The ``concorde-contract`` block with ``identity`` in the repository's Specs."""
    for path in sorted((REPOSITORY_ROOT / "specs").rglob("*.md")):
        for block in re.findall(
            r"```concorde-contract\n(.*?)\n```", path.read_text(), re.DOTALL
        ):
            value = json.loads(block)
            if value.get("id") == identity:
                return value
    raise AssertionError(f"no Spec states {identity}")


def worker_step(ctx):
    return run_worker(
        ctx,
        ctx.arguments.goal,
        task_type="implement",
        checks=True,
        rounds=ctx.arguments.rounds,
    )


def goal_arguments(parser):
    parser.add_argument("--goal", default="Do it.")
    parser.add_argument("--rounds", type=int, default=1)


def deterministic_step(ctx):
    return Continue(
        output={"ready": True}, evidence=[evidence("readiness", "", "ready")]
    )


def raising_step(ctx):
    raise RuntimeError("boom")


def admitted_step(ctx):
    return Continue(
        output={
            "inputs": sorted(ctx.inputs),
            "names": [ctx.inputs[key]["name"] for key in sorted(ctx.inputs)],
        }
    )


def refusing_step(ctx):
    return ctx.fail(
        "blocked",
        "nothing_to_do",
        "Nothing to do.",
        "the command found nothing to do in the workspace",
        reason="decision",
        explanation="whether to change the workspace first is the caller's decision",
        options=["change the workspace, then run it again"],
    )


WORKER = operation("implement", "implement", True, (worker_step,), None, goal_arguments)
RAISING = Provider("test", None, False, (raising_step,), admit=admission())
ADMITTED = Provider("understand", None, False, (admitted_step,), admit=admission())
# Execution commands: deterministic, no worker.
# The stand-ins read the Specs as Method's definitions do: they admit their Modules the same way.
DETERMINISTIC = command(
    "task-validation", (deterministic_step,), writes=False, admit=admission()
)
REFUSING = command("delivery", (refusing_step,), writes=True, admit=admission())


def reading_step(ctx):
    return run_worker(ctx, ctx.arguments.goal, task_type="understand", rounds=0)


def writing_step(ctx):
    return run_worker(ctx, ctx.arguments.goal, task_type="implement", rounds=0)


READER = operation(
    "spec_review",
    "review-spec",
    False,
    (reading_step,),
    None,
    goal_arguments,
    binding="optional",
)
WRITER = operation(
    "code_review",
    "review-code",
    False,
    (writing_step,),
    None,
    goal_arguments,
    binding="optional",
)


def probing_step(ctx):
    """Record what the run sees and, with ``--checks``, the configured checks' outcomes there;
    with ``--merge``, commit in the worktree the run started in, as a main session merging a task
    meanwhile would."""
    reference = ctx.worktree / "references/lib"
    ctx.state["probe"] = {
        "worktree": ctx.worktree.as_posix(),
        "started_in": ctx.started_in.as_posix(),
        "commit": ctx.commit,
        "calc": (ctx.worktree / "src/a/calc.py").read_text(),
        "venv": os.path.realpath(ctx.worktree / ".venv")
        if (ctx.worktree / ".venv").exists()
        else None,
        "reference": sorted(
            path.relative_to(reference).as_posix()
            for path in reference.rglob("*")
            if path.is_file() and path.name != ".git"
        ),
    }
    if ctx.arguments.checks:
        ctx.state["probe"]["checks"] = [
            item["status"]
            for item in run_checks(
                ctx.worktree,
                modules=["module.a"],
                trace_directory=ctx.run_dir / "checks",
            )
        ]
    if ctx.arguments.merge:
        (ctx.started_in / "src/bmod/merged.py").write_text("MERGED = 1\n")
        git(ctx.started_in, "add", "src/bmod/merged.py")
        git(
            ctx.started_in,
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "commit",
            "-qm",
            "merged meanwhile",
        )
    return Continue()


def probing_worker(ctx):
    if ctx.arguments.fail:
        raise RuntimeError("the probe failed on purpose")
    return run_worker(ctx, ctx.arguments.goal, task_type="understand", rounds=0)


def probed(ctx):
    return Continue(output=ctx.state["probe"])


def probe_arguments(parser):
    goal_arguments(parser)
    parser.add_argument("--merge", action="store_true")
    parser.add_argument("--checks", action="store_true")
    parser.add_argument("--fail", action="store_true")


PROBE = operation(
    "understand",
    "understand",
    False,
    (probing_step, probing_worker, probed),
    None,
    probe_arguments,
    binding="optional",
)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        self.records = self.root / ".concorde"
        self.project.open_task("t1")
        self.worktree = self.project.worktree("t1")
        for table, entries in (
            (
                catalog.OPERATIONS.definitions,
                {
                    "implement": WORKER,
                    "test": RAISING,
                    "understand": ADMITTED,
                    "spec_review": READER,
                    "code_review": WRITER,
                },
            ),
            (
                commands.COMMANDS.definitions,
                {
                    "task-validation": DETERMINISTIC,
                    "delivery": REFUSING,
                },
            ),
        ):
            patcher = patch.dict(table, entries)
            patcher.start()
            self.addCleanup(patcher.stop)

    def implement(self, steps, *extra):
        return self.project.run(
            "implement",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan(steps),
            *extra,
        )

    def store(self, workspace: str | None = "t1") -> runs.Store:
        """The run store of ``workspace``'s runs, or of the primary worktree's unbound runs."""
        if workspace is None:
            return runs.Store(self.records)
        return runs.Store(
            self.records, self.records / "tasks" / workspace / "workspace"
        )

    def run_folder(self, envelope, concorde: Path | None = None) -> Path:
        """Where the run's trace node lies: in its workspace's folder, or with the unbound runs
        of the ``.concorde`` of the worktree it started in."""
        if envelope["workspace"] is None:
            return (concorde or self.records) / "unbound" / envelope["run_id"]
        return (
            self.records
            / "tasks"
            / envelope["workspace"]
            / "workspace/runs"
            / envelope["run_id"]
        )

    def worker_record(self, envelope) -> dict:
        [worker] = envelope["worker_runs"]
        return read_record(self.run_folder(envelope), worker)

    def worker_progress(self, envelope) -> dict:
        [worker] = envelope["worker_runs"]
        folder = self.run_folder(envelope) / "workers" / worker
        return json.loads((folder / "status.json").read_text())

    def launched(self, envelope) -> list[str]:
        """The argument list the fake claude received in the first round."""
        work = self.project.runtime(self.worker_record(envelope)) / "work"
        return json.loads((work / "fake-round-1.json").read_text())["argv"]

    def saved(self, envelope, concorde: Path | None = None):
        return json.loads(
            (self.run_folder(envelope, concorde) / "result.json").read_text()
        )

    def lobby(self, run_id: str) -> Path:
        """Where a bound run waits for its workspace's lock, and stays when refused before."""
        return self.records / "lobby" / run_id

    def run_status(self, envelope, workspace: str | None = "t1"):
        """The status the run store lists for the run among the workspace's runs."""
        return {
            run["run_id"]: run["status"]
            for run in runs.workspace_runs(self.store(workspace), workspace)
        }.get(envelope["run_id"])

    def node(self, envelope, concorde: Path | None = None) -> dict:
        """The run's trace node record."""
        return json.loads(
            (self.run_folder(envelope, concorde) / "trace.json").read_text()
        )

    def binding(self) -> dict:
        return json.loads((self.worktree / binding_file.BINDING).read_text())

    @verifies("scenario.method.worker-model")
    def test_a_worker_runs_with_the_task_worktrees_model(self):
        (self.worktree / models.CONFIG).write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "enabled_models": {"sonnet": {}, "opus": {}},
                    "default": {
                        "backend": "claude",
                        "model": "sonnet",
                        "reasoning": "medium",
                    },
                    "operations": {
                        "implement": {"workers": {"worker": {"model": "opus"}}}
                    },
                }
            )
        )
        status, envelope = self.implement([{}])
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        argv = self.launched(envelope)
        self.assertEqual("opus", argv[argv.index("--model") + 1])
        self.assertEqual("medium", argv[argv.index("--effort") + 1])
        record = self.worker_record(envelope)
        self.assertEqual(
            ("claude", "worker", "opus", "opus", "medium"),
            (
                record["backend"],
                record["worker"],
                record["model"],
                record["local_model"],
                record["reasoning"],
            ),
        )
        self.assertEqual(os.environ["CONCORDE_MODEL_MAP"], record["model_map"])
        [shown] = [
            item for item in envelope["host_evidence"] if item["kind"] == "worker-model"
        ]
        self.assertEqual("claude", shown["ref"])
        self.assertIn("model opus as opus (model map ", shown["detail"])
        self.assertIn("reasoning medium", shown["detail"])
        (self.root / models.CONFIG).write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "enabled_models": {"haiku": {}},
                    "default": {"backend": "claude", "model": "haiku"},
                }
            )
        )
        status, envelope = self.implement([{}])
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        argv = self.launched(envelope)
        self.assertEqual("opus", argv[argv.index("--model") + 1])

    def fake_pi(self) -> dict:
        """A fake ``pi``, sandbox-runtime and pi configuration, as the variables naming them."""
        base = self.project.base
        pi = base / "pi"
        pi.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{FAKE_PI}" "$@"\n')
        pi.chmod(0o755)
        runtime = base / "sandbox-runtime"
        (runtime / "dist").mkdir(parents=True)
        (runtime / "dist/index.js").write_text("export {};\n")
        agent = base / "pi-agent"
        agent.mkdir()
        (agent / "auth.json").write_text('{"local": {"key": "k"}}')
        (agent / "models.json").write_text('{"providers": {}}')
        which = patch.object(pi_backend, "which", side_effect=fake_which)
        which.start()
        self.addCleanup(which.stop)
        return {
            "CONCORDE_PI": str(pi),
            "CONCORDE_SANDBOX_RUNTIME": str(runtime),
            "PI_CODING_AGENT_DIR": str(agent),
        }

    @verifies("scenario.method.worker-backend-configured")
    def test_a_claude_code_main_session_runs_its_workers_on_pi(self):
        environ = self.fake_pi()
        (self.worktree / models.CONFIG).write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "enabled_models": {"fast": {}, "sonnet": {}},
                    "operations": {
                        "implement": {"workers": {"worker": {"model": "fast"}}},
                        "spec_review": {
                            "workers": {
                                "worker": {"backend": "claude", "model": "sonnet"}
                            }
                        },
                    },
                }
            )
        )
        status, envelope = self.project.run(
            "implement",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan([{}]),
            environ=environ,
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        record = self.worker_record(envelope)
        # The project model name is resolved to pi's own id through the model map.
        self.assertEqual(
            ("pi", "Concorde's default worker backend", "fast", "local/fast"),
            (
                record["backend"],
                record["backend_source"],
                record["model"],
                record["local_model"],
            ),
        )
        argv = self.launched(envelope)
        self.assertEqual("local/fast", argv[argv.index("--model") + 1])
        self.assertIn("--no-extensions", argv)
        [shown] = [
            item for item in envelope["host_evidence"] if item["kind"] == "worker-model"
        ]
        self.assertEqual("pi", shown["ref"])
        self.assertIn("Concorde's default worker backend", shown["detail"])
        self.assertIn("model fast as local/fast", shown["detail"])
        status, envelope = self.project.run(
            "spec_review",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan([{}]),
            environ=environ,
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        record = self.worker_record(envelope)
        self.assertEqual(
            ("claude", "operations.spec_review.workers.worker"),
            (record["backend"], record["backend_source"]),
        )

    @verifies("scenario.execution.unbound-run")
    def test_an_unbound_run_works_on_a_checkout_of_its_worktree(self):
        before = store.load_task(self.root, "t1")
        status, envelope = self.project.run(
            "spec_review",
            "--modules",
            "module.a",
            "--goal",
            OperationProject.plan([{}]),
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual(
            ("operation", "spec_review"), (envelope["kind"], envelope["name"])
        )
        self.assertIsNone(envelope["workspace"])
        self.assertEqual(["module.a"], envelope["modules"])
        self.assertEqual(head(self.root), envelope["commit"])
        # The reviewer worked in a throwaway checkout of the primary worktree's HEAD, which is
        # gone once the run ended.
        checkout = Path(self.worker_progress(envelope)["worktree"])
        self.assertNotEqual(self.root, checkout)
        self.assertEqual(
            self.root / ".claude/worktrees" / f"{PREFIX}{envelope['run_id']}", checkout
        )
        self.assertFalse(checkout.exists())
        self.assertEqual([self.root, self.worktree], worktrees(self.root))
        self.assertEqual(before, store.load_task(self.root, "t1"))
        # The run's node lies with the unbound runs of the worktree it started in.
        self.assertEqual(envelope, self.saved(envelope))
        node = self.node(envelope)
        self.assertEqual(
            ("run", "ok", None),
            (node["kind"], node["status"], node["metadata"].get("workspace")),
        )
        self.assertEqual(
            {
                "kind": "trace",
                "ref": envelope["run_id"],
                "detail": self.run_folder(envelope).as_posix(),
            },
            envelope["host_evidence"][0],
        )
        self.assertEqual("ok", self.run_status(envelope, None))
        self.assertIsNone(self.run_status(envelope, "t1"))
        validate(envelope, RESULT_SCHEMA)
        status, envelope = self.project.run(
            "spec_review", "--modules", "module.a", "--input", envelope["run_id"]
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        # An Operation that needs a binding is refused in an unbound worktree.
        status, envelope = self.project.run("implement", "--goal", "x")
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual([], envelope["worker_runs"])
        self.assertEqual(["refused", "binding_required"], codes(envelope["error"]))
        self.assertEqual("scope", envelope["error"]["unhandled"]["reason"])
        self.assertIn(binding_file.BINDING, envelope["error"]["causes"][0]["detail"])
        self.assertEqual(envelope, self.saved(envelope))

    @verifies("scenario.execution.bound-run")
    def test_a_run_in_a_bound_worktree_works_on_its_workspace(self):
        # The binding of the worktree the run starts in decides its workspace: no argument
        # names it, and a run there is never unbound.
        status, envelope = self.project.run(
            "spec_review",
            "--goal",
            OperationProject.plan([{}]),
            cwd=self.worktree / "src",
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual("t1", envelope["workspace"])
        self.assertEqual(self.binding()["modules"], envelope["modules"])
        self.assertEqual(str(self.worktree), self.worker_progress(envelope)["worktree"])
        # The run is traced where the binding says: runs/<run-id>/ of the task's workspace
        # folder in the primary worktree's .concorde, its worker run inside it.
        self.assertEqual(
            str(self.records / "tasks/t1/workspace"), self.binding()["traces"]
        )
        folder = self.records / "tasks/t1/workspace/runs" / envelope["run_id"]
        self.assertEqual(folder, self.run_folder(envelope))
        self.assertEqual(envelope, self.saved(envelope))
        [worker] = envelope["worker_runs"]
        self.assertTrue((folder / "workers" / worker / "trace.json").is_file())
        node = self.node(envelope)
        self.assertEqual(
            ("run", envelope["run_id"], "ok", "concorde-run-trace"),
            (node["kind"], node["id"], node["status"], node["content"]["type_id"]),
        )
        self.assertEqual([worker], node["content"]["data"]["worker_runs"])
        for place in ("tasks", "unbound", "runs"):
            self.assertFalse((self.worktree / ".concorde" / place).exists(), place)
        self.assertEqual("ok", self.run_status(envelope))

    @verifies("scenario.method.unbound-write")
    def test_an_unbound_run_launches_no_writing_worker(self):
        status, envelope = self.project.run(
            "code_review",
            "--modules",
            "module.a",
            "--goal",
            OperationProject.plan([{}]),
        )
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual([], envelope["worker_runs"])
        self.assertEqual("unbound_write", envelope["error"]["code"])
        self.assertEqual("scope", envelope["error"]["unhandled"]["reason"])
        self.assertIn("(unbound, ", envelope["error"]["actor"])

    @verifies("scenario.execution.unbound-bound-input-refused")
    def test_an_unbound_run_refuses_the_output_of_a_bound_run(self):
        status, bound_run = self.implement([{}])
        self.assertEqual(0, status, bound_run)
        status, envelope = self.project.run(
            "spec_review", "--modules", "module.a", "--input", bound_run["run_id"]
        )
        self.assertEqual(1, status)
        self.assertIn(
            "input_not_admissible", [item["ref"] for item in envelope["host_evidence"]]
        )
        self.assertIn("a run of t1, not of no workspace", envelope["error"]["detail"])

    @verifies(
        "scenario.method.worker-model-unavailable",
        "scenario.method.worker-backend-missing",
        "scenario.method.worker-model-unmapped",
    )
    def test_a_worker_whose_backend_or_model_cannot_be_settled_fails_before_launch(
        self,
    ):
        (self.worktree / models.CONFIG).write_text("{broken")
        status, envelope = self.implement([{}])
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        [cause] = envelope["error"]["causes"]
        self.assertEqual("config_invalid", cause["code"])
        self.assertIn(str(self.worktree / models.CONFIG), cause["detail"])
        (self.worktree / models.CONFIG).write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "enabled_models": {"fast": {}},
                    "default": {"model": "fast"},
                }
            )
        )
        status, envelope = self.project.run(
            "implement",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan([{}]),
            environ={"CONCORDE_PI": str(self.project.base / "nowhere")},
        )
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual([], envelope["worker_runs"])
        assert envelope is not None
        self.assertEqual("worker_model_unavailable", envelope["error"]["code"])
        [cause] = envelope["error"]["causes"]
        self.assertEqual("backend_missing", cause["code"])
        self.assertEqual("environment", cause["unhandled"]["reason"])
        self.assertIn("Concorde's default worker backend", cause["detail"])
        self.assertIn("CONCORDE_PI", cause["detail"])
        self.assertIn(f"edit its backend in {models.CONFIG}", cause["detail"])
        self.assertTrue(
            any("commit it" in option for option in envelope["error"]["options"])
        )
        self.assertNotIn("--backend", json.dumps(envelope["error"]))
        validate(envelope["error"], ERROR_SCHEMA)
        # A model the machine's model map gives no id for its backend is refused too.
        unmapped = self.project.base / "unmapped.json"
        unmapped.write_text(json.dumps({"schema_version": 1, "models": {}}))
        status, envelope = self.project.run(
            "implement",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan([{}]),
            environ={**self.fake_pi(), "CONCORDE_MODEL_MAP": str(unmapped)},
        )
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual([], envelope["worker_runs"])
        [cause] = envelope["error"]["causes"]
        self.assertEqual("model_unmapped", cause["code"])
        self.assertIn(str(unmapped), cause["detail"])
        self.assertTrue(
            any("model map" in option for option in envelope["error"]["options"])
        )
        validate(envelope["error"], ERROR_SCHEMA)

    @verifies("scenario.method.worker-ok")
    def test_a_worker_backed_run_succeeds(self):
        status, envelope = self.implement(
            [
                {
                    "writes": {
                        f"{self.worktree}/src/a/calc.py": "def add(a, b):\n    return a + b\n"
                    }
                }
            ]
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual(
            ("operation", "implement", "t1"),
            (envelope["kind"], envelope["name"], envelope["workspace"]),
        )
        kinds = {item["kind"] for item in envelope["host_evidence"]}
        self.assertTrue(
            {"grant", "context-identity", "audit", "check", "rounds"} <= kinds
        )
        self.assertEqual("done", envelope["worker"]["summary"])
        self.assertEqual(1, len(envelope["worker_runs"]))
        self.assertIsNone(envelope["error"])
        self.assertEqual(envelope, self.saved(envelope))
        self.assertEqual("ok", self.run_status(envelope))
        # The run released the workspace lock.
        self.assertIsNone(runs.lock_holder(self.store(), "t1"))

    @verifies("scenario.execution.progress-file", "scenario.execution.run-lock")
    def test_the_progress_file_follows_the_run(self):
        from concorde.execution import runner

        # Whether the run lock is held at every progress write, probed as another reader would.
        # Whether the run's node is already written, and where its lock file lies.
        held, traced, lock_files = [], [], []
        original = runner._progress

        def progress(context, **fields):
            held.append(runs.runner_alive(context.store, context.run_id))
            traced.append((context.run_dir / "trace.json").is_file())
            lock_files.append(context.store.run_lock(context.run_id))
            original(context, **fields)

        with patch.object(runner, "_progress", side_effect=progress):
            status, envelope = self.implement([{}])
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        run = self.run_folder(envelope)
        self.assertTrue(held and all(held), held)
        self.assertTrue(all(traced), traced)
        # The run lock is a file of the primary worktree's locks/, never inside the run's folder,
        # and it is gone once the runner ended.
        lock = self.records / "locks/runs" / f"{envelope['run_id']}.lock"
        self.assertEqual({lock}, set(lock_files))
        self.assertFalse(lock.exists())
        self.assertEqual([], list(run.rglob("*.lock")))
        self.assertFalse(runs.runner_alive(self.store(), envelope["run_id"]))
        self.assertEqual("finished", runs.run_state(self.store(), envelope["run_id"]))
        node = self.node(envelope)
        self.assertEqual(
            ("ok", 0, envelope["summary"]),
            (
                node["status"],
                node["content"]["data"]["exit_code"],
                node["content"]["data"]["summary"],
            ),
        )
        self.assertEqual(
            ["check_worker_models", "worker_step"],
            [step["name"] for step in node["content"]["data"]["steps"]],
        )
        progress = json.loads((run / "status.json").read_text())
        self.assertEqual(
            (
                "operation",
                "implement",
                "t1",
                str(self.worktree),
                "finished",
                "ok",
                envelope["summary"],
            ),
            (
                progress["kind"],
                progress["name"],
                progress["workspace"],
                progress["worktree"],
                progress["phase"],
                progress["status"],
                progress["summary"],
            ),
        )
        self.assertEqual(os.getpid(), progress["host_pid"])
        worker_progress = self.worker_progress(envelope)
        self.assertEqual(progress["host_pid"], worker_progress["host_pid"])
        self.assertEqual(envelope["run_id"], worker_progress["operation_run_id"])

    @verifies("scenario.method.worker-blocked")
    def test_a_blocked_worker_escalates(self):
        status, envelope = self.implement(
            [
                {
                    "result": {
                        "status": "blocked",
                        "error": {
                            "code": "spec_gap",
                            "detail": "the Spec does not state the rounding rule",
                            "evidence": [],
                            "attempts": ["read specs/a/module.md"],
                            "unhandled": {
                                "reason": "decision",
                                "explanation": "the rounding rule is the Spec's to state",
                            },
                            "options": ["round per line", "round per order"],
                            "recommendation": "round per order",
                        },
                    }
                }
            ]
        )
        self.assertEqual((1, "blocked"), (status, envelope["status"]))
        error = envelope["error"]
        self.assertEqual(["worker_blocked", "worker_blocked", "spec_gap"], codes(error))
        self.assertEqual(
            ["operation", "workers", "worker"],
            [
                error["level"],
                error["causes"][0]["level"],
                error["causes"][0]["causes"][0]["level"],
            ],
        )
        self.assertEqual(
            f"Operation implement {envelope['run_id']} (workspace t1)", error["actor"]
        )
        worker = error["causes"][0]["causes"][0]
        self.assertEqual("the Spec does not state the rounding rule", worker["detail"])
        self.assertEqual("round per order", worker["recommendation"])
        self.assertEqual("decision", worker["unhandled"]["reason"])
        self.assertEqual("decision", error["unhandled"]["reason"])
        self.assertIn("round per line", error["options"])
        host_text = json.dumps(envelope["host_evidence"]) + envelope["summary"]
        self.assertNotIn("rounding rule", host_text)

    @verifies("scenario.method.spec-error")
    def test_a_spec_tooling_error_keeps_its_reason_and_causes(self):
        from concorde.spec.errors import SpecError, system_cause

        refused = SpecError(
            "the implement grant would make src/shared.py writable, which module.b binds",
            "shared_file",
            "modules",
            causes=[system_cause(PermissionError(13, "denied", "src/shared.py"))],
        )
        with patch("concorde.spec.grants.grant", side_effect=refused):
            status, envelope = self.implement([{}])
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        error = envelope["error"]
        self.assertEqual("grant_unavailable", error["code"])
        [spec] = error["causes"]
        self.assertEqual(("component", "shared_file"), (spec["level"], spec["code"]))
        self.assertIn("src/shared.py", spec["detail"])
        self.assertEqual(refused.reason, spec["unhandled"]["explanation"])
        self.assertEqual([refused.remediation], spec["options"])
        [system] = spec["causes"]
        self.assertEqual(
            ("system_error", "environment"),
            (system["code"], system["unhandled"]["reason"]),
        )
        self.assertIn("src/shared.py", system["detail"])

    @verifies("scenario.method.checks-exhausted")
    def test_checks_still_failing_after_the_last_round(self):
        status, envelope = self.implement(
            [{"writes": {f"{self.worktree}/src/a/flag": "broken"}}], "--rounds", "1"
        )
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual("ok", envelope["worker"]["status"])
        checks = [item for item in envelope["host_evidence"] if item["kind"] == "check"]
        self.assertTrue(
            checks
            and "exit 1" in checks[-1]["detail"]
            and "log" in checks[-1]["detail"]
        )
        self.assertIn("2 round(s)", json.dumps(envelope["host_evidence"]))
        error = envelope["error"]
        self.assertEqual(
            ["checks_failed", "checks_failed", "check_failed"], codes(error)
        )
        self.assertEqual("decision", error["unhandled"]["reason"])
        self.assertEqual("exhausted", error["causes"][0]["unhandled"]["reason"])
        check = error["causes"][0]["causes"][0]
        self.assertEqual(("check", "check.a"), (check["level"], check["actor"]))
        self.assertIn("exit code 1", check["detail"])

    @verifies("scenario.method.audit-violation")
    def test_a_write_outside_the_grant_fails_the_run(self):
        _, envelope = self.implement(
            [{"writes": {f"{self.worktree}/src/bmod/secret.py": "SECRET = 2\n"}}]
        )
        self.assertEqual("failed", envelope["status"])
        audits = [item for item in envelope["host_evidence"] if item["kind"] == "audit"]
        self.assertIn("src/bmod/secret.py", audits[0]["detail"])
        self.assertFalse(
            any(item["kind"] == "check" for item in envelope["host_evidence"])
        )

    @verifies("scenario.execution.command-run")
    def test_a_recorded_command_launches_no_worker(self):
        status, envelope = self.project.run("task-validation", "--task", "t1")
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual(
            ("command", "task-validation", "t1"),
            (envelope["kind"], envelope["name"], envelope["workspace"]),
        )
        self.assertIsNone(envelope["worker"])
        self.assertEqual([], envelope["worker_runs"])
        self.assertEqual({"ready": True}, envelope["output"])
        # The run identity carries the name with underscores only.
        self.assertRegex(
            envelope["run_id"], r"^r-\d{8}T\d{6}-task_validation-[0-9a-f]{8}$"
        )
        self.assertEqual(envelope, self.saved(envelope))
        self.assertEqual("ok", self.run_status(envelope))
        validate(envelope, RESULT_SCHEMA)

    def test_a_recorded_commands_error_is_a_command_link(self):
        status, envelope = self.project.run("delivery", "--task", "t1")
        self.assertEqual((1, "blocked"), (status, envelope["status"]))
        error = envelope["error"]
        self.assertEqual(("command", "nothing_to_do"), (error["level"], error["code"]))
        self.assertEqual(
            f"Command delivery {envelope['run_id']} (workspace t1)", error["actor"]
        )
        validate(error, ERROR_SCHEMA)
        self.assertEqual("blocked", self.run_status(envelope))
        # A command is not an Operation: `concorde run` refuses it before any run exists.
        folder = self.records / "tasks/t1/workspace/runs"
        before = sorted(folder.iterdir())
        with self.assertRaisesRegex(UsageError, "is a command, not an Operation"):
            execute("operation", "delivery", [], cwd=self.worktree)
        self.assertEqual(before, sorted(folder.iterdir()))

    @verifies("scenario.execution.workspace-busy")
    def test_a_busy_workspace_refuses_a_second_run(self):
        with runs.workspace_lock(self.store(), "t1", "implement run r-other"):
            # The workspace lock is a file of the primary worktree's locks/.
            lock = self.records / "locks/workspaces/t1.lock"
            self.assertIn("implement run r-other", lock.read_text())
            status, envelope = self.project.run("task-validation", "--task", "t1")
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertIn(
            "workspace_busy", [item["ref"] for item in envelope["host_evidence"]]
        )
        error = envelope["error"]
        self.assertEqual(["refused", "workspace_busy"], codes(error))
        self.assertEqual("decision", error["unhandled"]["reason"])
        self.assertIn("r-other", error["detail"])
        self.assertIsNone(envelope["output"])
        # The refusal is recorded like any run, in the lobby, since the run never entered its
        # workspace; its identity finds it there, and the lock is free again afterwards.
        refused = self.lobby(envelope["run_id"])
        self.assertEqual(envelope, json.loads((refused / "result.json").read_text()))
        self.assertFalse(self.run_folder(envelope).exists())
        self.assertEqual(refused, self.store().find(envelope["run_id"]))
        self.assertEqual(envelope, runs.load_result(self.store(), envelope["run_id"]))
        node = json.loads((refused / "trace.json").read_text())
        self.assertEqual((envelope["run_id"], "failed"), (node["id"], node["status"]))
        self.assertIsNone(runs.lock_holder(self.store(), "t1"))
        # An admitted run writes its result while it still holds the lock, so the next run
        # admitted finds that result written.
        holders = []
        replace = os.replace

        def observed(source, target, *args, **kwargs):
            if Path(target).name == "result.json":
                holders.append(runs.lock_holder(self.store(), "t1"))
            return replace(source, target, *args, **kwargs)

        with patch("concorde.execution.runner.os.replace", observed):
            status, envelope = self.project.run("task-validation", "--task", "t1")
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        [holder] = holders
        self.assertIn(envelope["run_id"], holder)
        self.assertIsNone(runs.lock_holder(self.store(), "t1"))
        status, following = self.project.run("task-validation", "--task", "t1")
        self.assertEqual("ok", following["status"])
        self.assertEqual(envelope, self.saved(envelope))

    def hold_workspace(self) -> threading.Event:
        """Hold the workspace lock of t1 as a running implement run would, in a thread, until
        the returned event is set."""
        taken, release = threading.Event(), threading.Event()

        def hold():
            with runs.workspace_lock(self.store(), "t1", "implement run r-other"):
                taken.set()
                release.wait(60)

        holder = threading.Thread(target=hold)
        holder.start()
        self.addCleanup(holder.join)
        self.addCleanup(release.set)
        self.assertTrue(taken.wait(10))
        return release

    @verifies("scenario.execution.workspace-wait-timeout")
    def test_a_wait_the_holder_outlasts_is_refused(self):
        self.hold_workspace()
        status, envelope = self.project.run(
            "task-validation", "--task", "t1", "--wait", "0.3"
        )
        self.assertEqual(
            (1, ["refused", "workspace_busy"]), (status, codes(envelope["error"]))
        )
        self.assertIn("after waiting 0 s", json.dumps(envelope["error"]))
        self.assertIn("--wait <seconds>", json.dumps(envelope["error"]["options"]))
        self.assertEqual([], envelope["worker_runs"])
        # It never entered its workspace: its node and result stay in the lobby.
        lobby = self.lobby(envelope["run_id"])
        self.assertEqual(
            envelope, json.loads((lobby / "result.json").read_text(encoding="utf-8"))
        )
        self.assertTrue((lobby / "trace.json").is_file())
        self.assertFalse(self.run_folder(envelope).exists())

    @verifies("scenario.execution.workspace-wait")
    def test_a_waiting_run_queues_behind_the_running_one(self):
        release = self.hold_workspace()
        # A detached run waits in its own process, naming the run it waits for.
        status, announced = detach(
            "command", "task-validation", ["--wait", "60"], cwd=self.worktree
        )
        self.assertEqual(0, status, announced)
        # It waits in the lobby: nothing of it lies in the workspace folder yet.
        lobby = Path(announced["lobby"])
        self.assertEqual(self.lobby(announced["run_id"]), lobby)
        deadline = time.monotonic() + 30
        shown = {}
        while time.monotonic() < deadline:
            shown = json.loads((lobby / "status.json").read_text())
            if shown.get("step") == "workspace-lock":
                break
            time.sleep(0.05)
        self.assertEqual(
            ("running", "workspace-lock", "implement run r-other"),
            (shown["phase"], shown["step"], shown["waiting_for"].split(" (process")[0]),
        )
        self.assertFalse(Path(announced["trace"]).exists())
        self.assertTrue((lobby / "trace.json").is_file())
        self.assertTrue((lobby / "host.out").is_file())
        listed = runs.workspace_runs(self.store(), "t1")
        self.assertIn(
            (announced["run_id"], "running"),
            [(r["run_id"], r["status"]) for r in listed],
        )
        progress = Path(announced["progress"])
        release.set()
        envelope = self.wait_for(Path(announced["result"]))
        # Once the lock was free the run entered its workspace, its whole node and its runner's
        # output moving out of the lobby, and did its own work: a readiness, not a refusal.
        self.assertFalse(lobby.exists())
        self.assertTrue((Path(announced["trace"]) / "host.out").is_file())
        self.assertIsNotNone(envelope["output"], envelope)
        self.assertNotIn(
            "workspace_busy", [item["ref"] for item in envelope["host_evidence"]]
        )
        self.assertIsNone(json.loads(progress.read_text())["waiting_for"])
        with self.assertRaisesRegex(UsageError, "negative"):
            execute("command", "task-validation", ["--wait", "-1"], cwd=self.worktree)

    @verifies("scenario.execution.workspace-wait-merge")
    def test_a_run_waiting_behind_a_merge_names_the_merge(self):
        taken, release = threading.Event(), threading.Event()
        lock = self.records / "locks/workspaces/t1.lock"

        def hold():
            # A task merge holds the workspace lock with a holder line of its own, naming its task.
            with locks.hold(lock, "task merge t1", task="t1"):
                taken.set()
                release.wait(60)

        holder = threading.Thread(target=hold)
        holder.start()
        self.addCleanup(holder.join)
        self.addCleanup(release.set)
        self.assertTrue(taken.wait(10))
        status, envelope = self.project.run(
            "task-validation", "--task", "t1", "--wait", "0.3"
        )
        self.assertEqual(
            (1, ["refused", "workspace_busy"]), (status, codes(envelope["error"]))
        )
        # The refusal names the merge as Tracing's holder line describes it, not as a run.
        [refused] = [
            item for item in envelope["host_evidence"] if item["kind"] == "refused"
        ]
        self.assertIn("task merge t1 (process", refused["detail"])
        self.assertIn("task t1", refused["detail"])
        status, announced = detach(
            "command", "task-validation", ["--wait", "60"], cwd=self.worktree
        )
        self.assertEqual(0, status, announced)
        progress = Path(announced["lobby"]) / "status.json"
        deadline = time.monotonic() + 30
        shown = {}
        while time.monotonic() < deadline:
            shown = json.loads(progress.read_text())
            if shown.get("step") == "workspace-lock":
                break
            time.sleep(0.05)
        self.assertEqual("workspace-lock", shown["step"])
        self.assertTrue(shown["waiting_for"].startswith("task merge t1 (process"))
        self.assertIn("task t1", shown["waiting_for"])
        release.set()
        # Once the merge let go, the run did its own work: a readiness, not a refusal.
        envelope = self.wait_for(Path(announced["result"]))
        self.assertIsNotNone(envelope["output"], envelope)

    @verifies("scenario.execution.workspace-retired")
    def test_a_run_waiting_for_a_retired_workspace_is_refused(self):
        lock = self.records / "locks/workspaces/t1.lock"
        path = binding_file.path_of(self.worktree)
        good = path.read_text()
        workspace = self.records / "tasks/t1/workspace"

        def waiting() -> bool:
            for progress in (self.records / "lobby").glob("*/status.json"):
                if json.loads(progress.read_text()).get("step") == "workspace-lock":
                    return True
            return False

        def files() -> list[Path]:
            return sorted(workspace.rglob("*"))

        for retire, said in (
            # A close removes the lock file while it holds the lock.
            (lambda: lock.unlink(), "removed the lock file"),
            (lambda: path.unlink(), "is gone"),
            (
                lambda: path.write_text(
                    json.dumps({**json.loads(good), "goal": "another goal"})
                ),
                "changed: goal",
            ),
        ):
            with self.subTest(said=said):
                taken = threading.Event()

                def hold(retire=retire):
                    # Hold the lock as a close does until the run waits for it, then retire
                    # the workspace and release the lock.
                    with runs.workspace_lock(self.store(), "t1", "close of t1"):
                        taken.set()
                        deadline = time.monotonic() + 30
                        while not waiting() and time.monotonic() < deadline:
                            time.sleep(0.05)
                        retire()

                holder = threading.Thread(target=hold)
                holder.start()
                self.assertTrue(taken.wait(10))
                before = files()
                status, envelope = self.project.run(
                    "task-validation", "--task", "t1", "--wait", "30"
                )
                holder.join(30)
                path.write_text(good)
                self.assertEqual(
                    (1, ["refused", "workspace_retired"]),
                    (status, codes(envelope["error"])),
                    envelope["error"],
                )
                [cause] = envelope["error"]["causes"]
                self.assertEqual("Execution (workspace binding)", cause["actor"])
                self.assertIn(said, cause["detail"])
                self.assertEqual(
                    "environment", envelope["error"]["unhandled"]["reason"]
                )
                self.assertEqual([], envelope["worker_runs"])
                # It never entered the workspace: its node and result stay in the lobby, and
                # nothing was written into the workspace folder.
                self.assertEqual(before, files())
                lobby = self.lobby(envelope["run_id"])
                self.assertEqual(
                    envelope, json.loads((lobby / "result.json").read_text())
                )
                self.assertEqual(lobby, self.store().find(envelope["run_id"]))
                self.assertNotIn(
                    envelope["run_id"],
                    [run["run_id"] for run in runs.workspace_runs(self.store(), "t1")],
                )
        # Once the workspace is bound again, a run enters it as before.
        status, envelope = self.project.run("task-validation", "--task", "t1")
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertFalse(self.lobby(envelope["run_id"]).exists())
        self.assertTrue((self.run_folder(envelope) / "result.json").is_file())

    @verifies("scenario.execution.binding-refused")
    def test_a_broken_binding_refuses_the_run(self):
        path = self.worktree / binding_file.BINDING
        good = path.read_text()
        other = self.project.base / "elsewhere"
        for text, code in (
            ("{not json", "binding_unreadable"),
            (json.dumps({**json.loads(good), "modules": []}), "binding_invalid"),
            (json.dumps({**json.loads(good), "root": str(other)}), "binding_misplaced"),
        ):
            with self.subTest(code=code):
                path.write_text(text)
                status, envelope = self.project.run(
                    "task-validation", cwd=self.worktree
                )
                self.assertEqual((1, "failed"), (status, envelope["status"]))
                self.assertEqual(["refused", code], codes(envelope["error"]))
                [cause] = envelope["error"]["causes"]
                self.assertEqual("Execution (workspace binding)", cause["actor"])
                self.assertIn(str(path), cause["detail"])
                # A binding that cannot be trusted leaves the run unbound, recorded in the
                # worktree it started in.
                self.assertIsNone(envelope["workspace"])
                self.assertEqual(
                    envelope, self.saved(envelope, self.worktree / ".concorde")
                )
                self.assertFalse(
                    (self.records / "unbound" / envelope["run_id"]).exists()
                )
        path.write_text(good)
        self.assertEqual(json.loads(good), binding_file.load(self.worktree))

    @verifies("scenario.execution.binding-required")
    def test_a_command_needing_a_binding_is_refused_when_unbound(self):
        status, envelope = self.project.run("task-validation")
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual(["refused", "binding_required"], codes(envelope["error"]))
        self.assertIn(f"(unbound, {self.root})", envelope["error"]["actor"])
        self.assertEqual("refused", envelope["error"]["code"])
        self.assertEqual("failed", self.run_status(envelope, None))

    @verifies("scenario.execution.modules-as-names")
    def test_a_definition_without_admission_takes_the_modules_as_names(self):
        labels = command("labels", (deterministic_step,), writes=False)
        binding_file.write(
            self.worktree, {**self.binding(), "modules": ["module.a", "module.gone"]}
        )
        with patch.dict(commands.COMMANDS.definitions, {"labels": labels}):
            status, envelope = self.project.run(
                "labels", "--task", "t1", "--modules", "module.nowhere"
            )
            self.assertEqual((0, ["module.nowhere"]), (status, envelope["modules"]))
            status, envelope = self.project.run("labels", "--task", "t1")
            self.assertEqual(
                (0, ["module.a", "module.gone"]), (status, envelope["modules"])
            )

    @verifies("scenario.execution.unknown-module-refused")
    def test_a_definitions_admission_refuses_an_unknown_module(self):
        # The test project's task-validation admits its Modules through Method's admission.
        status, envelope = self.project.run(
            "task-validation", "--task", "t1", "--modules", "module.a,module.nowhere"
        )
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        # No step ran: the refusal came from the admission, before the steps.
        self.assertEqual([], self.node(envelope)["content"]["data"]["steps"])
        self.assertEqual(["refused", "unknown_module"], codes(envelope["error"]))
        cause = envelope["error"]["causes"][0]
        self.assertEqual("Method (Module admission)", cause["actor"])
        self.assertIn("module.nowhere", cause["detail"])

    @verifies("scenario.execution.removed-module", "scenario.execution.modules-removed")
    def test_a_module_the_workspace_removed_is_left_out(self):
        def bind(modules):
            binding_file.write(self.worktree, {**self.binding(), "modules": modules})

        # module.gone stands for a Module the workspace removed or renamed.
        bind(["module.a", "module.gone"])
        status, envelope = self.project.run("task-validation", "--task", "t1")
        self.assertEqual((0, "ok"), (status, envelope["status"]))
        self.assertEqual(["module.a"], envelope["modules"])
        [removed] = [
            item
            for item in envelope["host_evidence"]
            if item["kind"] == "removed-module"
        ]
        self.assertEqual("module.gone", removed["ref"])
        self.assertIn("no longer registers", removed["detail"])
        # The runner never rewrites the binding; the run store lists what the run used.
        self.assertEqual(["module.a", "module.gone"], self.binding()["modules"])
        [listed] = [
            run
            for run in runs.workspace_runs(self.store(), "t1")
            if run["run_id"] == envelope["run_id"]
        ]
        self.assertEqual(["module.a"], listed["modules"])

        bind(["module.gone"])
        status, envelope = self.project.run("task-validation", "--task", "t1")
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual(["refused", "modules_removed"], codes(envelope["error"]))
        self.assertIn("module.gone", envelope["error"]["causes"][0]["detail"])
        self.assertIn("--modules", envelope["error"]["causes"][0]["detail"])
        status, envelope = self.project.run(
            "task-validation", "--task", "t1", "--modules", "module.a"
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]))

    def wait_for(self, path: Path) -> dict:
        deadline = time.monotonic() + 120
        while not path.is_file() and time.monotonic() < deadline:
            time.sleep(0.1)
        return json.loads(path.read_text())

    def wait_ended(self, run_id: str) -> None:
        """Wait until the runner of ``run_id`` has ended: its run lock is gone. Its result is
        written before that, while it still writes under ``.concorde``."""
        lock = self.records / "locks/runs" / f"{run_id}.lock"
        deadline = time.monotonic() + 120
        while lock.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertFalse(lock.exists())

    @verifies("scenario.execution.detached")
    def test_a_detached_run_is_announced_and_finishes_on_its_own(self):
        # The detached runner is a process of its own, so it runs the real task-validation.
        status, announced = detach(
            "command", "task-validation", ["--detach"], cwd=self.worktree
        )
        self.assertEqual(0, status, announced)
        self.assertEqual(
            ("command", "task-validation"), (announced["kind"], announced["name"])
        )
        # Its progress file exists once announced: in the lobby, or in its node once it entered
        # its workspace. The lobby first: a run moves from it into its node, never back.
        self.assertTrue(
            (Path(announced["lobby"]) / "status.json").is_file()
            or Path(announced["progress"]).is_file()
        )
        folder = self.records / "tasks/t1/workspace/runs" / announced["run_id"]
        self.assertEqual(
            (folder, folder / "result.json"),
            (Path(announced["trace"]), Path(announced["result"])),
        )
        envelope = self.wait_for(Path(announced["result"]))
        self.wait_ended(announced["run_id"])
        validate(envelope, RESULT_SCHEMA)
        self.assertEqual(announced["run_id"], envelope["run_id"])
        self.assertEqual("t1", envelope["workspace"])
        self.assertEqual(envelope["status"], self.run_status(envelope))
        # The detached runner's own output is kept in the run's node.
        self.assertTrue((folder / "host.out").is_file())
        with self.assertRaises(UsageError):
            detach("operation", "frobnicate", ["--detach"], cwd=self.worktree)

    @verifies("scenario.execution.detached-busy")
    def test_a_detached_run_of_a_busy_workspace_is_refused_in_the_lobby(self):
        # A workspace already running something still gets its refusal as the result.
        with runs.workspace_lock(self.store(), "t1", "implement run r-other", wait=30):
            status, announced = detach(
                "command", "task-validation", [], cwd=self.worktree
            )
            self.assertEqual(0, status, announced)
            refused = self.wait_for(Path(announced["lobby"]) / "result.json")
            self.wait_ended(announced["run_id"])
        self.assertEqual("failed", refused["status"])
        self.assertFalse(Path(announced["trace"]).exists())
        self.assertIn(
            "workspace_busy", [item["ref"] for item in refused["host_evidence"]]
        )

    @verifies("scenario.execution.detached-namespace")
    def test_a_run_detached_inside_a_pid_namespace_dies_with_it(self):
        from tests.concorde.workflows.test_workflows import _pid_sandbox

        sandbox = _pid_sandbox()
        if sandbox is None:
            self.skipTest("bubblewrap cannot make a PID namespace here")
        # The run queues behind a lock the test holds, so it is still running when the namespace
        # it was detached in ends.
        taken, release = threading.Event(), threading.Event()

        def hold():
            with runs.workspace_lock(self.store(), "t1", "implement run r-other"):
                taken.set()
                release.wait(60)

        holder = threading.Thread(target=hold)
        holder.start()
        self.addCleanup(holder.join)
        self.addCleanup(release.set)
        self.assertTrue(taken.wait(10))
        started = subprocess.run(
            [
                *sandbox,
                sys.executable,
                str(REPOSITORY_ROOT / "scripts/concorde.py"),
                "task-validation",
                "--detach",
                "--wait",
                "60",
            ],
            cwd=self.worktree,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, started.returncode, started.stdout + started.stderr)
        announced = json.loads(started.stdout)
        run_id = announced["run_id"]
        # The call is over and its namespace with it: the runner was killed without a word.
        deadline = time.monotonic() + 30
        while runs.runner_alive(self.store(), run_id) and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertFalse(runs.runner_alive(self.store(), run_id))
        self.assertIsNone(runs.load_result(self.store(), run_id))
        self.assertEqual("lost", runs.run_state(self.store(), run_id))
        output = Path(announced["lobby"]) / "host.out"
        self.assertEqual("", output.read_text())

    @verifies("scenario.execution.detach-failed")
    def test_a_detached_runner_that_never_announces_leaves_no_run(self):
        # No announcement wait: the runner is killed before it can write its progress file.
        before = sorted((self.records / "lobby").glob("*"))
        status, announced = detach(
            "command", "task-validation", [], cwd=self.worktree, wait=0
        )
        self.assertEqual(1, status, announced)
        error = announced["error"]
        self.assertEqual(
            ("component", "detach_failed"), (error["level"], error["code"])
        )
        self.assertIn("no step ran", error["detail"])
        # Nothing of the run is left: no lobby folder, no node, no run lock.
        self.assertFalse(Path(announced["lobby"]).exists())
        self.assertFalse(Path(announced["trace"]).exists())
        self.assertEqual(before, sorted((self.records / "lobby").glob("*")))
        self.assertFalse(
            (self.records / "locks/runs" / f"{announced['run_id']}.lock").exists()
        )
        self.assertIsNone(runs.load_result(self.store(), announced["run_id"]))

    @verifies("scenario.execution.result-published-whole")
    def test_a_result_is_published_whole_or_not_at_all(self):
        seen = []
        replace = os.replace

        def observed(source, target, *args, **kwargs):
            if Path(target).name == "result.json":
                # Until the rename, an observer finds no result; the file renamed into place
                # already holds the whole result.
                seen.append(
                    (Path(target).exists(), json.loads(Path(source).read_text()))
                )
            return replace(source, target, *args, **kwargs)

        with patch("concorde.execution.runner.os.replace", observed):
            status, envelope = self.project.run("task-validation", "--task", "t1")
        self.assertEqual([(False, envelope)], seen)
        self.assertEqual(envelope, self.saved(envelope))
        self.assertEqual(
            ["result.json"],
            [path.name for path in self.run_folder(envelope).glob("*result*")],
        )

    def refusing(self, *kinds: str):
        """A patch under which the operating system refuses every ``trace.json`` of a node of
        ``kinds``, its folder being made as the file system would before the file."""
        original = trace_node.write

        def write(folder, record):
            if record["kind"] in kinds:
                Path(folder).mkdir(parents=True, exist_ok=True)
                raise OSError(errno.ENOSPC, "No space left on device")
            return original(folder, record)

        return patch.object(trace_node, "write", write)

    @verifies("scenario.execution.trace-write-reported")
    def test_a_refused_trace_write_is_in_the_result_and_never_fatal(self):
        with self.refusing("run"):
            status, envelope = self.project.run("task-validation", "--task", "t1")
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        writes = [
            item for item in envelope["host_evidence"] if item["kind"] == "trace-write"
        ]
        self.assertEqual({envelope["run_id"]}, {item["ref"] for item in writes})
        moments = " ".join(item["detail"] for item in writes)
        self.assertIn("could not be written at its start", moments)
        self.assertIn("could not be written at its end", moments)
        for item in writes:
            self.assertIn("trace.json", item["detail"])
            self.assertIn("No space left on device", item["detail"])
        # The final write follows the result, which is published again with it.
        self.assertEqual(envelope, self.saved(envelope))
        self.assertFalse((self.run_folder(envelope) / "trace.json").exists())
        self.assertIsNone(runs.lock_holder(self.store(), "t1"))

    @verifies("scenario.method.trace-write-reported")
    def test_a_refused_trace_write_below_the_run_is_in_its_result(self):
        with self.refusing("worker-run", "check"):
            status, envelope = self.implement(
                [
                    {
                        "writes": {
                            f"{self.worktree}/src/a/calc.py": "def add(a, b):\n    return a + b\n"
                        }
                    }
                ]
            )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        [worker] = envelope["worker_runs"]
        writes = [
            item for item in envelope["host_evidence"] if item["kind"] == "trace-write"
        ]
        checks = [
            item["ref"] for item in envelope["host_evidence"] if item["kind"] == "check"
        ]
        self.assertTrue(checks)
        refs = {item["ref"] for item in writes}
        self.assertEqual({worker, *checks}, refs)
        for item in writes:
            self.assertIn("No space left on device", item["detail"])
        # The worker run's failures include its first and its final write.
        worker_writes = " ".join(
            item["detail"] for item in writes if item["ref"] == worker
        )
        self.assertIn("at its start", worker_writes)
        self.assertIn("at its end", worker_writes)

    @verifies("scenario.execution.result-unsaved")
    def test_a_result_that_cannot_be_saved_is_printed_and_the_run_is_lost(self):
        def full(path, text):
            raise OSError(28, "No space left on device", str(path))

        with patch.object(runner, "_publish", full):
            with self.assertRaises(ResultUnsaved) as unsaved:
                self.project.run("task-validation", "--task", "t1")
        envelope, link = unsaved.exception.envelope, unsaved.exception.link
        self.assertEqual((1, "ok"), (unsaved.exception.status, envelope["status"]))
        self.assertEqual(["result_unsaved", "run_store_unwritable"], codes(link))
        self.assertEqual("environment", link["unhandled"]["reason"])
        validate(link, ERROR_SCHEMA)
        # Nothing was saved, both locks are free again and every observer finds the run lost.
        folder = self.run_folder(envelope)
        self.assertFalse((folder / "result.json").exists())
        self.assertEqual("running", self.node(envelope)["status"])
        self.assertFalse(
            (self.records / "locks/runs" / f"{envelope['run_id']}.lock").exists()
        )
        self.assertIsNone(runs.lock_holder(self.store(), "t1"))
        self.assertEqual("lost", runs.run_state(self.store(), envelope["run_id"]))
        # The command line still prints the result, and the chain on standard error.
        old = Path.cwd()
        os.chdir(self.worktree)
        self.addCleanup(os.chdir, old)
        out, err = io.StringIO(), io.StringIO()
        with (
            patch.object(runner, "_publish", full),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            self.assertEqual(1, run_main("command", "task-validation", []))
        printed = json.loads(out.getvalue())
        self.assertEqual(
            ("task-validation", "ok"), (printed["name"], printed["status"])
        )
        self.assertIn("result_unsaved", err.getvalue())
        self.assertIn("No space left on device", err.getvalue())

    @verifies("scenario.execution.result-unsaved")
    def test_a_final_trace_that_cannot_be_written_leaves_the_run_lost(self):
        def refused(*args, **kwargs):
            raise TraceError("node_invalid", "the final trace.json was refused")

        with patch.object(runner, "_finish_node", refused):
            with self.assertRaises(ResultUnsaved) as unsaved:
                self.project.run("task-validation", "--task", "t1")
        envelope = unsaved.exception.envelope
        self.assertEqual(
            ["result_unsaved", "node_invalid"], codes(unsaved.exception.link)
        )
        # The result was saved before the failing write; the trace node still says it runs,
        # with nobody holding its run lock.
        self.assertEqual(envelope, self.saved(envelope))
        self.assertEqual("running", self.node(envelope)["status"])
        self.assertFalse(runs.runner_alive(self.store(), envelope["run_id"]))
        self.assertIsNone(runs.lock_holder(self.store(), "t1"))

    @verifies("scenario.execution.run-unrecorded")
    def test_a_run_whose_first_records_fail_runs_no_step(self):
        ran = []

        def unwritable(*args, **kwargs):
            raise OSError(30, "Read-only file system")

        with (
            patch.object(runner, "_start_node", unwritable),
            patch.object(runner, "_steps", lambda *a: ran.append(a)),
        ):
            with self.assertRaises(RunUnrecorded) as unrecorded:
                self.project.run("task-validation", "--task", "t1")
        link = unrecorded.exception.link
        self.assertEqual(["run_unrecorded", "run_store_unwritable"], codes(link))
        self.assertIn("no step ran", link["detail"])
        validate(link, ERROR_SCHEMA)
        self.assertEqual([], ran)
        self.assertEqual([], list((self.records / "locks/runs").glob("*.lock")))
        self.assertIsNone(runs.lock_holder(self.store(), "t1"))
        old = Path.cwd()
        os.chdir(self.worktree)
        self.addCleanup(os.chdir, old)
        out, err = io.StringIO(), io.StringIO()
        with (
            patch.object(runner, "_start_node", unwritable),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            self.assertEqual(1, run_main("command", "task-validation", []))
        self.assertEqual("", out.getvalue())
        self.assertIn("run_unrecorded", err.getvalue())

    @verifies("scenario.tracing.run-lock-lifetime")
    def test_a_run_lock_exists_only_while_its_runner_runs(self):
        # The detached run queues behind a workspace lock the test holds, so it runs as long as
        # the test lets it.
        taken, release = threading.Event(), threading.Event()

        def hold():
            with runs.workspace_lock(self.store(), "t1", "implement run r-other"):
                taken.set()
                release.wait(60)

        holder = threading.Thread(target=hold)
        holder.start()
        self.addCleanup(holder.join)
        self.addCleanup(release.set)
        self.assertTrue(taken.wait(10))
        status, announced = detach(
            "command", "task-validation", ["--wait", "60"], cwd=self.worktree
        )
        self.assertEqual(0, status, announced)
        run_id = announced["run_id"]
        lock = self.records / "locks/runs" / f"{run_id}.lock"
        progress = Path(announced["lobby"]) / "status.json"
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if json.loads(progress.read_text()).get("step") == "workspace-lock":
                break
            time.sleep(0.05)
        # While the run runs its lock file exists and is held by its runner.
        self.assertTrue(lock.is_file())
        self.assertTrue(locks.held(lock))
        self.assertIn(run_id, locks.holder(lock))
        self.assertTrue(runs.runner_alive(self.store(), run_id))
        self.assertEqual("running", runs.run_state(self.store(), run_id))
        release.set()
        self.wait_for(Path(announced["result"]))
        deadline = time.monotonic() + 30
        while runs.pid_alive(announced["host_pid"]) and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertFalse(runs.pid_alive(announced["host_pid"]))
        # Once the runner exited its lock file is gone, and no lock ever lay in its folder.
        self.assertFalse(lock.exists())
        self.assertFalse(runs.runner_alive(self.store(), run_id))
        self.assertEqual("finished", runs.run_state(self.store(), run_id))
        folder = Path(announced["trace"])
        self.assertEqual(self.records / "tasks/t1/workspace/runs" / run_id, folder)
        self.assertEqual([], list(folder.rglob("*.lock")))

    @verifies("scenario.execution.bad-command")
    def test_a_malformed_command_line_writes_nothing(self):
        def written():
            return sorted(
                path
                for folder in ("tasks/t1/workspace/runs", "unbound", "locks/runs")
                for path in (self.records / folder).glob("*")
            )

        before = written()
        with self.assertRaisesRegex(UsageError, "unknown operation 'frobnicate'"):
            self.project.run("frobnicate", "--task", "t1")
        with self.assertRaisesRegex(UsageError, "unrecognized arguments: --bogus"):
            self.project.run("task-validation", "--task", "t1", "--bogus")
        with self.assertRaisesRegex(UsageError, "not inside a"):
            outside = self.project.base / "outside"
            outside.mkdir()
            execute("command", "task-validation", [], cwd=outside)
        self.assertEqual(before, written())
        with patch("sys.stderr") as stderr:
            self.assertEqual(2, run_main("operation", None, []))
            self.assertEqual(2, run_main("operation", "frobnicate", []))
        self.assertIn("unknown operation", str(stderr.write.call_args_list))

    @verifies("scenario.execution.host-error")
    def test_a_raising_step_is_a_failed_result(self):
        status, envelope = self.project.run("test", "--task", "t1")
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        [error] = [
            item for item in envelope["host_evidence"] if item["kind"] == "host-error"
        ]
        self.assertEqual("step raising_step", error["ref"])
        self.assertIn("RuntimeError: boom", error["detail"])
        [cause] = envelope["error"]["causes"]
        self.assertEqual(
            ("component", "RuntimeError: boom"), (cause["level"], cause["detail"])
        )
        trace = [item for item in cause["evidence"] if item["kind"] == "traceback"]
        self.assertEqual(self.run_folder(envelope), Path(trace[0]["ref"]).parent)
        self.assertTrue(Path(trace[0]["ref"]).is_file())
        self.assertIn("raising_step", Path(trace[0]["ref"]).read_text())
        self.assertEqual("failed", self.run_status(envelope))

    @verifies("scenario.execution.admission-error")
    def test_a_raising_admission_is_a_failed_result(self):
        def raising_admission(ctx):
            raise RuntimeError("admission boom")

        with patch.dict(
            catalog.OPERATIONS.definitions,
            {
                "test": Provider(
                    "test", None, False, (deterministic_step,), admit=raising_admission
                )
            },
        ):
            status, envelope = self.project.run("test", "--task", "t1")
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual("host_error", envelope["error"]["code"])
        [error] = [
            item for item in envelope["host_evidence"] if item["kind"] == "host-error"
        ]
        self.assertEqual("test admission", error["ref"])
        self.assertIn("RuntimeError: admission boom", error["detail"])
        self.assertEqual([], self.node(envelope)["content"]["data"]["steps"])
        self.assertEqual("failed", self.run_status(envelope))

    @verifies("scenario.execution.cancelled")
    def test_a_cancelled_run_ends_its_worker(self):
        pid_file = self.project.base / "child.pid"

        def cancel():
            deadline = time.monotonic() + 20
            while not pid_file.exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            time.sleep(0.2)
            os.kill(os.getpid(), signal.SIGTERM)

        threading.Thread(target=cancel, daemon=True).start()
        _, envelope = self.implement([{"spawn": str(pid_file), "sleep": 60}])
        self.assertEqual("failed", envelope["status"])
        self.assertIn("cancelled", {item["kind"] for item in envelope["host_evidence"]})
        self.assertEqual(envelope, self.saved(envelope))
        self.assertIsNone(runs.lock_holder(self.store(), "t1"))
        # The result names the worker run it started, and that run ended too.
        [worker] = envelope["worker_runs"]
        self.assertIn(worker, envelope["error"]["detail"])
        [named] = [
            item
            for item in envelope["error"]["evidence"]
            if item["kind"] == "worker-run"
        ]
        directory = self.run_folder(envelope) / "workers" / worker
        self.assertEqual((directory / "trace.json").as_posix(), named["ref"])
        progress = json.loads((directory / "status.json").read_text())
        self.assertEqual(
            ("finished", "failed"), (progress["phase"], progress["status"])
        )
        record = read_record(self.run_folder(envelope), worker)
        self.assertEqual("interrupted", record["error"]["code"])
        self.assertEqual("cancelled", self.node(envelope)["outcome"])
        child = int(pid_file.read_text())
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and Path(f"/proc/{child}").exists():
            state = Path(f"/proc/{child}/stat")
            if state.exists() and state.read_text().split()[2] == "Z":
                break
            time.sleep(0.05)
        state = Path(f"/proc/{child}/stat")
        self.assertTrue(not state.exists() or state.read_text().split()[2] == "Z")

    @verifies("scenario.execution.inputs")
    def test_earlier_results_are_admitted_as_task_material(self):
        _, first = self.project.run("task-validation", "--task", "t1")
        status, envelope = self.project.run(
            "understand", "--task", "t1", "--input", first["run_id"]
        )
        self.assertEqual(0, status, envelope)
        self.assertEqual(
            {"inputs": [first["run_id"]], "names": ["task-validation"]},
            envelope["output"],
        )
        _, failed = self.project.run("test", "--task", "t1")
        _, refused = self.project.run(
            "understand", "--task", "t1", "--input", failed["run_id"]
        )
        self.assertEqual("failed", refused["status"])
        self.assertIn(
            "input_not_admissible", [item["ref"] for item in refused["host_evidence"]]
        )
        self.assertIn("ended failed", refused["error"]["detail"])
        # A run of another workspace is not admitted either.
        self.project.open_task("t2")
        _, other = self.project.run(
            "understand", "--task", "t2", "--input", first["run_id"]
        )
        self.assertEqual(["refused", "input_not_admissible"], codes(other["error"]))
        self.assertIn("a run of t1, not of t2", other["error"]["detail"])

    def test_the_run_store_lists_a_workspaces_runs(self):
        _, first = self.project.run("task-validation", "--task", "t1")
        _, second = self.project.run("test", "--task", "t1")
        _, unbound = self.project.run(
            "spec_review",
            "--modules",
            "module.a",
            "--goal",
            OperationProject.plan([{}]),
        )
        listed = runs.workspace_runs(self.store(), "t1")
        self.assertEqual(
            [
                (first["run_id"], "command", "task-validation", "ok"),
                (second["run_id"], "operation", "test", "failed"),
            ],
            [
                (run["run_id"], run["kind"], run["name"], run["status"])
                for run in listed
            ],
        )
        self.assertEqual(
            [unbound["run_id"]],
            [run["run_id"] for run in runs.workspace_runs(self.store(None), None)],
        )
        self.assertEqual("finished", runs.run_state(self.store(), first["run_id"]))
        self.assertEqual("refused", runs.run_state(self.store(), None))

    def test_the_result_schema_is_the_contract(self):
        fence = spec_contract("contract.execution.run-result")
        self.assertEqual(RESULT_SCHEMA, fence["schema"])

    def test_the_binding_schema_is_the_contract(self):
        fence = spec_contract("contract.kernel.workspace-binding")
        self.assertEqual(binding_file.BINDING_SCHEMA, fence["schema"])

    def test_the_error_link_is_the_framework_contract(self):
        text = (
            REPOSITORY_ROOT / "specs/concorde/kernel/tracing/contracts.md"
        ).read_text()
        [fence] = [
            json.loads(block)
            for block in re.findall(
                r"```concorde-contract\n(.*?)\n```", text, re.DOTALL
            )
            if json.loads(block).get("id") == "contract.tracing.error"
        ]
        self.assertEqual(fence["schema"], ERROR_SCHEMA)
        self.assertEqual(RESULT_SCHEMA["$defs"]["error"], LINK_SCHEMA)

    def test_a_stopping_step_prevents_every_later_step(self):
        ran = []

        def first(ctx):
            ran.append("first")
            return Continue()

        def stopping(ctx):
            ran.append("stopping")
            return Stop("ok", "Stopped early.")

        def sentinel(ctx):
            ran.append("sentinel")
            return Continue()

        with patch.dict(
            commands.COMMANDS.definitions,
            {
                "task-validation": command(
                    "task-validation", (first, stopping, sentinel), writes=False
                )
            },
        ):
            status, envelope = self.project.run("task-validation", "--task", "t1")
        self.assertEqual((0, "Stopped early."), (status, envelope["summary"]))
        self.assertEqual(["first", "stopping"], ran)
        self.assertEqual(
            [("first", "continue"), ("stopping", "stop")],
            [
                (step["name"], step["outcome"])
                for step in self.node(envelope)["content"]["data"]["steps"]
            ],
        )

    def test_a_failure_of_the_runner_outside_every_step_is_a_failed_result(self):
        from concorde.execution import runner

        def broken(*_arguments):
            raise ValueError("inputs unreadable")

        with patch.object(runner, "admit_inputs", broken):
            status, envelope = self.project.run("task-validation", "--task", "t1")
        self.assertEqual(
            (1, "failed", "host_error"),
            (status, envelope["status"], envelope["error"]["code"]),
        )
        [cause] = envelope["error"]["causes"]
        self.assertTrue(cause["actor"].startswith("Execution runner"), cause)
        self.assertIn("ValueError: inputs unreadable", cause["detail"])
        self.assertEqual(envelope, self.saved(envelope))
        # A failed write of the node between steps changes nothing.
        with patch.object(Node, "update", side_effect=TraceError("io", "disk")):
            status, envelope = self.project.run("task-validation", "--task", "t1")
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        # A step that returns neither continue nor stop raised, as far as the run goes.
        with patch.dict(
            commands.COMMANDS.definitions,
            {
                "task-validation": command(
                    "task-validation", (lambda ctx: None,), writes=False
                )
            },
        ):
            status, envelope = self.project.run("task-validation", "--task", "t1")
        self.assertEqual((1, "host_error"), (status, envelope["error"]["code"]))
        self.assertIn("neither continue nor stop", envelope["error"]["detail"])

    @verifies("scenario.execution.cancelled")
    def test_a_signal_while_the_run_finishes_does_not_cut_it_short(self):
        from concorde.execution import runner

        real = runner._envelope

        def signalled(*arguments):
            os.kill(os.getpid(), signal.SIGTERM)
            return real(*arguments)

        with patch.object(runner, "_envelope", signalled):
            status, envelope = self.project.run("task-validation", "--task", "t1")
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual(envelope, self.saved(envelope))
        self.assertIs(signal.default_int_handler, signal.getsignal(signal.SIGINT))
        # A signal while the first records are created cancels the run before its first step.
        ran = []

        def step(ctx):
            ran.append(ctx.run_id)
            return Continue()

        start = runner._start_node

        def interrupted(*arguments):
            os.kill(os.getpid(), signal.SIGINT)
            return start(*arguments)

        with (
            patch.object(runner, "_start_node", interrupted),
            patch.dict(
                commands.COMMANDS.definitions,
                {"task-validation": command("task-validation", (step,), writes=False)},
            ),
        ):
            status, envelope = self.project.run("task-validation", "--task", "t1")
        self.assertEqual((1, "cancelled"), (status, envelope["error"]["code"]))
        self.assertEqual([], ran)
        self.assertIn("SIGINT", envelope["error"]["detail"])
        self.assertEqual(
            envelope,
            json.loads((self.lobby(envelope["run_id"]) / "result.json").read_text()),
        )

    def test_an_invalid_result_is_replaced_by_one_that_keeps_the_contract(self):
        def malformed(ctx):
            ctx.worker = ["not", "an", "object"]
            return Continue(evidence=[{"kind": 1}, evidence("readiness", "", "ready")])

        def foreign_error(ctx):
            return Stop(
                "failed",
                "Failed.",
                error=component(
                    "Somebody", "boom", "it broke", "input", "only they can"
                ),
            )

        for step, field in (
            (malformed, "/worker"),
            (foreign_error, "/error/level"),
        ):
            with (
                self.subTest(step=step.__name__),
                patch.dict(
                    commands.COMMANDS.definitions,
                    {
                        "task-validation": command(
                            "task-validation", (step,), writes=False
                        )
                    },
                ),
            ):
                status, envelope = self.project.run("task-validation", "--task", "t1")
                self.assertEqual(
                    (1, "invalid_result"), (status, envelope["error"]["code"])
                )
                validate(envelope, RESULT_SCHEMA)
                self.assertEqual(envelope, self.saved(envelope))
                [invalid] = [
                    item
                    for item in envelope["host_evidence"]
                    if item["kind"] == "invalid-output"
                ]
                self.assertEqual(field, invalid["ref"])
                self.assertIsNone(envelope["worker"])
                # The malformed evidence is left out; a well-formed earlier error is the cause.
                self.assertNotIn({"kind": 1}, envelope["host_evidence"])
                self.assertEqual(
                    [] if step is malformed else ["boom"],
                    [cause["code"] for cause in envelope["error"]["causes"]],
                )

    def test_a_running_progress_file_holds_a_null_summary(self):
        seen = []

        def step(ctx):
            seen.append(json.loads((ctx.run_dir / "status.json").read_text()))
            return Continue()

        with patch.dict(
            commands.COMMANDS.definitions,
            {"task-validation": command("task-validation", (step,), writes=False)},
        ):
            status, envelope = self.project.run("task-validation", "--task", "t1")
        self.assertEqual(0, status, envelope)
        [running] = seen
        self.assertEqual(
            ("running", None, None),
            (running["phase"], running["status"], running["summary"]),
        )

    def test_a_run_error_names_the_modules_in_its_detail(self):
        status, envelope = self.project.run(
            "delivery", "--task", "t1", "--modules", "module.a"
        )
        self.assertEqual(1, status)
        self.assertTrue(
            envelope["error"]["detail"].endswith("(Modules: module.a)"),
            envelope["error"]["detail"],
        )

    @verifies("scenario.execution.run-unrecorded", "scenario.execution.detach-failed")
    def test_a_detached_run_that_cannot_be_recorded_or_started_leaves_nothing(self):
        lobby = self.records / "lobby"
        lobby.mkdir(exist_ok=True)
        before = sorted(lobby.iterdir())
        real = subprocess.Popen

        def unstartable(argv, *arguments, **options):
            if "concorde" in argv:
                raise OSError(errno.EMFILE, "Too many open files")
            return real(argv, *arguments, **options)

        with patch("concorde.execution.runner.subprocess.Popen", unstartable):
            status, announced = detach(
                "command", "task-validation", [], cwd=self.worktree
            )
        self.assertEqual(1, status, announced)
        self.assertEqual("detach_failed", announced["error"]["code"])
        self.assertIn("could not be started", announced["error"]["detail"])
        self.assertIsNone(announced["host_pid"])
        self.assertEqual(before, sorted(lobby.iterdir()))
        # A run store that cannot hold the run's folder starts no runner.
        shutil.rmtree(lobby)
        lobby.write_text("not a folder")
        self.addCleanup(lambda: lobby.unlink(missing_ok=True))
        with self.assertRaises(runner.RunUnrecorded) as raised:
            detach("command", "task-validation", [], cwd=self.worktree)
        self.assertEqual("run_unrecorded", raised.exception.link["code"])
        stderr = io.StringIO()
        with contextlib.chdir(self.worktree), contextlib.redirect_stderr(stderr):
            self.assertEqual(
                1, runner.run_main("command", "task-validation", ["--detach"])
            )
        self.assertIn("run_unrecorded", stderr.getvalue())

    def test_an_input_whose_result_breaks_the_contract_is_refused(self):
        _, first = self.project.run("task-validation", "--task", "t1")
        saved = self.run_folder(first) / "result.json"
        older = json.loads(saved.read_text())
        del older["worker_runs"]
        saved.write_text(json.dumps(older))
        _, refused = self.project.run(
            "understand", "--task", "t1", "--input", first["run_id"]
        )
        self.assertEqual(["refused", "input_not_admissible"], codes(refused["error"]))
        self.assertIn("current run result contract", refused["error"]["detail"])

    def test_the_idle_check_finds_the_unbound_runs_of_linked_worktrees(self):
        from concorde.execution.idle import active_runs

        self.assertEqual([], active_runs(self.root))
        # A developer's own linked worktree without a binding keeps its unbound runs' locks in
        # its own .concorde.
        linked = self.project.base / "linked"
        git(self.root, "worktree", "add", "-q", "--detach", str(linked))
        self.addCleanup(git, self.root, "worktree", "remove", "--force", str(linked))
        with (
            runs.run_lock(runs.Store(linked / ".concorde"), "r-1", "Execution runner"),
            runs.run_lock(self.store(), "r-2", "Execution runner"),
        ):
            found = active_runs(self.root)
        self.assertEqual(2, len(found), found)
        self.assertTrue(any("r-1" in item and str(linked) in item for item in found))
        self.assertTrue(any("r-2" in item for item in found))


class UnboundCheckoutTests(unittest.TestCase):
    """An unbound run works in a throwaway detached checkout of its worktree's HEAD."""

    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        self.records = self.root / ".concorde"
        patcher = patch.dict(catalog.OPERATIONS.definitions, {"understand": PROBE})
        patcher.start()
        self.addCleanup(patcher.stop)

    def commit(self, message: str) -> str:
        git(self.root, "add", "-A")
        git(
            self.root,
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "commit",
            "-qm",
            message,
        )
        return head(self.root)

    def probe(self, *extra, cwd: Path | None = None):
        return self.project.run(
            "understand",
            "--modules",
            "module.a",
            "--goal",
            OperationProject.plan([{}]),
            *extra,
            cwd=cwd,
        )

    def run_folder(self, envelope) -> Path:
        return self.records / "unbound" / envelope["run_id"]

    def worker_record(self, envelope) -> dict:
        [worker] = envelope["worker_runs"]
        return read_record(self.run_folder(envelope), worker)

    def worker_progress(self, envelope) -> dict:
        [worker] = envelope["worker_runs"]
        folder = self.run_folder(envelope) / "workers" / worker
        return json.loads((folder / "status.json").read_text())

    @verifies("scenario.execution.unbound-checkout", "scenario.execution.unbound-run")
    def test_an_unbound_run_examines_head_while_its_worktree_changes(self):
        (self.root / ".gitignore").write_text(
            (self.root / ".gitignore").read_text() + ".venv/\n"
        )
        # The configured check runs the interpreter of the environment Git ignores.
        checks = read_checks(self.root)
        checks[0]["argv"] = [".venv/bin/python", "checks/a_check.py"]
        write_checks(self.root, checks)
        # The worker configuration is the committed one of the examined commit.
        (self.root / models.CONFIG).write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "enabled_models": {"sonnet": {}, "opus": {}},
                    "default": {"backend": "claude", "model": "sonnet"},
                    "operations": {
                        "understand": {"workers": {"worker": {"model": "opus"}}}
                    },
                }
            )
        )
        examined = self.commit("check with the environment")
        (self.root / ".venv/bin").mkdir(parents=True)
        (self.root / ".venv/bin/python").symlink_to(sys.executable)
        (self.root / ".venv/bin/tool").write_text("tool\n")
        # An uncommitted change of the worktree the run starts in is not examined.
        (self.root / "src/a/calc.py").write_text("uncommitted\n")
        # An uncommitted change of the worker configuration is not used either.
        (self.root / models.CONFIG).write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "enabled_models": {"haiku": {}},
                    "default": {"backend": "claude", "model": "haiku"},
                }
            )
        )
        status, envelope = self.probe("--merge", "--checks")
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        probe = envelope["output"]
        checkout = Path(probe["worktree"])
        self.assertEqual(
            (str(self.root), examined, examined),
            (probe["started_in"], probe["commit"], envelope["commit"]),
        )
        self.assertEqual(
            self.root / ".claude/worktrees" / f"{PREFIX}{envelope['run_id']}", checkout
        )
        self.assertEqual("def add(a, b):\n    return a - b\n", probe["calc"])
        self.assertEqual(str(self.root / ".venv"), probe["venv"])
        self.assertEqual(["passed"], probe["checks"])
        # The worker worked and was audited in the checkout, so the commit made meanwhile in
        # the starting worktree left its audit clean; its model came from the examined commit.
        record = self.worker_record(envelope)
        self.assertEqual(str(checkout), self.worker_progress(envelope)["worktree"])
        self.assertEqual("opus", record["model"])
        self.assertEqual(
            ["clean"], [item["audit"]["verdict"] for item in record["rounds"]]
        )
        kinds = {item["kind"]: item for item in envelope["host_evidence"]}
        self.assertEqual(examined, kinds["checkout"]["ref"])
        self.assertEqual(".venv", kinds["environment"]["ref"])
        # The run is traced with the unbound runs of the starting worktree, the checks it ran
        # as check nodes inside its node, and its checkout is gone.
        folder = self.run_folder(envelope)
        self.assertTrue((folder / "result.json").exists())
        self.assertTrue((folder / "trace.json").exists())
        check = json.loads((folder / "checks/check.a/trace.json").read_text())
        self.assertEqual(("check", "ok"), (check["kind"], check["status"]))
        progress = json.loads((folder / "status.json").read_text())
        self.assertEqual(
            (str(checkout), examined), (progress["worktree"], progress["commit"])
        )
        self.assertFalse(checkout.exists())
        self.assertEqual([self.root], worktrees(self.root))
        # The starting worktree keeps its change, its environment and the commit made meanwhile.
        self.assertEqual("uncommitted\n", (self.root / "src/a/calc.py").read_text())
        self.assertEqual("tool\n", (self.root / ".venv/bin/tool").read_text())
        self.assertNotEqual(examined, head(self.root))
        validate(envelope, RESULT_SCHEMA)

    @verifies("scenario.execution.unbound-checkout-removed")
    def test_the_checkout_is_removed_however_the_run_ends(self):
        # A task worktree registered before the run keeps its registration.
        self.project.open_task("t1")
        before = worktrees(self.root)
        self.assertEqual(2, len(before))
        examined = head(self.root)
        status, envelope = self.probe("--fail")
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual("host_error", envelope["error"]["code"])
        self.assertIn(
            f"(unbound, {self.root} at {examined})", envelope["error"]["actor"]
        )
        self.assertEqual(examined, envelope["commit"])
        [checkout] = [
            item for item in envelope["host_evidence"] if item["kind"] == "checkout"
        ]
        self.assertEqual(examined, checkout["ref"])
        self.assertEqual(before, worktrees(self.root))
        self.assertFalse(Path(checkout["detail"].split()[4].rstrip(",")).exists())
        self.assertEqual(
            [],
            list(
                Path(os.environ.get("TMPDIR", "/tmp")).glob(
                    f"{PREFIX}*/{envelope['run_id']}"
                )
            ),
        )

    @verifies("scenario.execution.unbound-checkout")
    def test_a_checked_out_submodule_is_checked_out_in_the_checkout_too(self):
        library = self.project.base / "lib"
        library.mkdir()
        (library / "guide.md").write_text("guide\n")
        (library / "media").mkdir()
        (library / "media/picture.png").write_text("png\n")
        git(library, "init", "-q")
        git(library, "add", "-A")
        git(
            library, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "lib"
        )
        git(
            self.root,
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            "-q",
            str(library),
            "references/lib",
        )
        self.commit("vendor lib")
        # The starting worktree checks out only part of it, as a sparse vendored reference does.
        git(
            self.root / "references/lib",
            "sparse-checkout",
            "set",
            "--no-cone",
            "/guide.md",
        )
        status, envelope = self.probe()
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual(["guide.md"], envelope["output"]["reference"])
        [submodule] = [
            item for item in envelope["host_evidence"] if item["kind"] == "submodule"
        ]
        self.assertEqual("references/lib", submodule["ref"])
        self.assertEqual([self.root], worktrees(self.root))
        # The submodule's repository lists only its own checkout again.
        self.assertEqual(1, len(worktrees(self.root / "references/lib")))
        # A submodule the starting worktree has not checked out stays empty in the checkout.
        git(self.root, "submodule", "deinit", "-q", "--force", "references/lib")
        status, envelope = self.probe()
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual([], envelope["output"]["reference"])
        [absent] = [
            item
            for item in envelope["host_evidence"]
            if item["kind"] == "submodule-absent"
        ]
        self.assertEqual("references/lib", absent["ref"])

    @verifies("scenario.execution.unbound-no-commit")
    def test_a_worktree_without_a_commit_refuses_an_unbound_run(self):
        empty = self.project.base / "empty"
        empty.mkdir()
        git(empty, "init", "-q")
        status, envelope = self.probe(cwd=empty)
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual(["refused", "checkout_unavailable"], codes(envelope["error"]))
        self.assertEqual("environment", envelope["error"]["unhandled"]["reason"])
        [cause] = envelope["error"]["causes"]
        self.assertEqual("Execution (unbound checkout)", cause["actor"])
        self.assertIn(f"{empty} has no commit at HEAD", cause["detail"])
        self.assertIsNone(envelope["commit"])
        self.assertEqual([], envelope["worker_runs"])
        self.assertTrue(
            (empty / ".concorde/unbound" / envelope["run_id"] / "result.json").exists()
        )

    @verifies("scenario.execution.unbound-not-ignored")
    def test_a_primary_worktree_not_ignoring_its_worktrees_refuses_an_unbound_run(self):
        bare = self.project.base / "unignored"
        bare.mkdir()
        (bare / "a.txt").write_text("a\n")
        git(bare, "init", "-q")
        git(bare, "add", "-A")
        git(bare, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "a")
        status, envelope = self.probe(cwd=bare)
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual(["refused", "checkout_unavailable"], codes(envelope["error"]))
        [cause] = envelope["error"]["causes"]
        self.assertIn("does not ignore .claude/worktrees/unbound-", cause["detail"])
        self.assertFalse((bare / ".claude").exists())
        self.assertEqual([bare], worktrees(bare))

    def sparse_library(self, *paths: str) -> Path:
        """A vendored library submodule holding ``paths``, committed as references/lib."""
        library = self.project.base / "lib"
        library.mkdir()
        for path in paths:
            (library / path).parent.mkdir(parents=True, exist_ok=True)
            (library / path).write_text(f"{path}\n")
        git(library, "init", "-q")
        git(library, "add", "-A")
        git(
            library, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "lib"
        )
        git(
            self.root,
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            "-q",
            str(library),
            "references/lib",
        )
        self.commit("vendor lib")
        return self.root / "references/lib"

    @verifies("scenario.execution.unbound-checkout")
    def test_a_submodule_keeps_its_sparse_mode_and_patterns(self):
        source = self.sparse_library(
            "docs/guide.md",
            "docs/deep/more.md",
            "my notes.md",
            "other/skip.md",
            "top.md",
        )
        # Cone mode: the directories git lists are read back in cone mode.
        git(source, "sparse-checkout", "set", "--cone", "docs")
        status, envelope = self.probe()
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual(
            ["docs/deep/more.md", "docs/guide.md", "my notes.md", "top.md"],
            envelope["output"]["reference"],
        )
        # Non-cone mode with a pattern holding a space.
        git(source, "sparse-checkout", "set", "--no-cone", "/my notes.md", "/top.md")
        status, envelope = self.probe()
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual(["my notes.md", "top.md"], envelope["output"]["reference"])

    @verifies("scenario.execution.unbound-checkout")
    def test_a_submodule_git_cannot_populate_stays_empty(self):
        from concorde.execution import checkout as module

        self.sparse_library("guide.md", "media/picture.png")
        real = module._git

        def failing(cwd, *arguments, **options):
            done = real(cwd, *arguments, **options)
            if arguments[:1] == ("read-tree",):
                # Some files are already there when the population fails.
                return subprocess.CompletedProcess(done.args, 128, "", "disk full")
            return done

        with patch.object(module, "_git", failing):
            status, envelope = self.probe()
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual([], envelope["output"]["reference"])
        [absent] = [
            item
            for item in envelope["host_evidence"]
            if item["kind"] == "submodule-absent"
        ]
        self.assertIn("disk full", absent["detail"])
        self.assertIn("leaves it empty", absent["detail"])
        self.assertEqual(1, len(worktrees(self.root / "references/lib")))
        self.assertEqual([self.root], worktrees(self.root))

    @verifies("scenario.execution.unbound-checkout")
    def test_runtime_paths_are_linked_below_missing_directories_or_explained(self):
        from concorde.execution.checkout import open_checkout

        (self.root / ".gitignore").write_text(
            (self.root / ".gitignore").read_text() + ".cache/\n"
        )
        (self.root / "tracked").mkdir()
        (self.root / "tracked/file.txt").write_text("tracked\n")
        self.commit("ignore the cache, track a folder")
        (self.root / ".cache/tools/venv/bin").mkdir(parents=True)
        opened = open_checkout(
            self.root,
            "r-20261004T000000-probe-0000abcd",
            lambda root: [".cache/tools/venv", "tracked", "missing"],
        )
        try:
            linked = opened.path / ".cache/tools/venv"
            self.assertTrue(linked.is_symlink())
            self.assertEqual(
                os.path.realpath(self.root / ".cache/tools/venv"),
                os.path.realpath(linked),
            )
            kinds = {(item["kind"], item["ref"]) for item in opened.evidence}
            self.assertIn(("environment", ".cache/tools/venv"), kinds)
            self.assertIn(("environment-not-linked", "tracked"), kinds)
            self.assertNotIn("missing", {ref for _, ref in kinds})
        finally:
            self.assertEqual([], opened.close())
        self.assertFalse(opened.path.exists())
        self.assertTrue((self.root / ".cache/tools/venv/bin").is_dir())

    @verifies("scenario.execution.unbound-checkout-removed")
    def test_a_checkout_the_fallback_cannot_remove_is_named_with_what_is_left(self):
        from concorde.execution import checkout as module

        opened = module.open_checkout(self.root, "r-20261004T000000-probe-0000abce")
        real = module._git

        def refusing(cwd, *arguments, **options):
            if arguments[:2] == ("worktree", "remove"):
                return subprocess.CompletedProcess(arguments, 1, "", "refused")
            return real(cwd, *arguments, **options)

        with (
            patch.object(module, "_git", refusing),
            patch.object(module.shutil, "rmtree"),
        ):
            [left] = opened.close()
        self.addCleanup(
            git, self.root, "worktree", "remove", "--force", str(opened.path)
        )
        self.assertEqual(
            ("checkout-not-removed", opened.path.as_posix()),
            (left["kind"], left["ref"]),
        )
        self.assertIn("could not be deleted directly", left["detail"])
        self.assertIn(f"git worktree remove --force {opened.path}", left["detail"])
        self.assertNotIn("the directory was deleted", left["detail"])


class BindingTests(unittest.TestCase):
    """The workspace binding Tasks writes into a task worktree and the runner reads."""

    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root

    def test_opening_a_task_binds_its_worktree(self):
        self.project.open_task("t1", goal="Fix A.")
        worktree = self.project.worktree("t1")
        record = store.load_task(self.root, "t1")
        value = binding_file.load(worktree)
        concorde = os.path.realpath(self.root / ".concorde")
        self.assertEqual(
            {
                "schema_version": 2,
                "workspace": "t1",
                "root": os.path.realpath(worktree),
                "branch": record["branch"],
                "base_commit": record["base_commit"],
                "goal": "Fix A.",
                "modules": ["module.a"],
                "traces": os.path.join(concorde, "tasks/t1/workspace"),
                "concorde": concorde,
            },
            {
                **value,
                "root": os.path.realpath(value["root"]),
                "traces": os.path.realpath(value["traces"]),
                "concorde": os.path.realpath(value["concorde"]),
            },
        )
        # The workspace folder exists once the task is open.
        self.assertTrue(Path(value["traces"]).is_dir())
        self.assertIsNone(binding_file.load(self.root))
        self.assertEqual(
            runs.Store(Path(value["concorde"]), Path(value["traces"])),
            runs.store_of(worktree, value),
        )
        self.assertEqual(
            runs.Store(self.root / ".concorde"), runs.store_of(self.root, None)
        )
        # The binding is ignored by Git: opening a task changes nothing a commit would carry.
        self.assertTrue(
            ".concorde/workspace.json" in (worktree / ".gitignore").read_text()
        )

    def test_a_binding_that_breaks_its_contract_is_never_written(self):
        from concorde.kernel.refusal import KernelError

        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        before = (worktree / binding_file.BINDING).read_text()
        with self.assertRaises(KernelError) as caught:
            binding_file.write(
                worktree, {**binding_file.load(worktree), "workspace": "Not A Name"}
            )
        self.assertEqual("binding_invalid", caught.exception.code)
        self.assertEqual(before, (worktree / binding_file.BINDING).read_text())


if __name__ == "__main__":
    unittest.main()
