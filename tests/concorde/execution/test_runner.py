"""The Execution runner: ``concorde run`` and the execution commands, with test definitions
standing in for real ones, the workspace binding it reads and the run store it writes."""

from __future__ import annotations

import json
import os
import re
import signal
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.commands import catalog as commands
from concorde.errors import ERROR_SCHEMA, LINK_SCHEMA, codes
from concorde.execution import binding as binding_file
from concorde.execution import runs
from concorde.execution.checkout import PREFIX
from concorde.execution.context import Continue, Provider, command, evidence
from concorde.execution.runner import UsageError, detach, execute, run_main
from concorde.execution.runs import RESULT_SCHEMA
from concorde.harness import models, pi_backend
from concorde.harness.checks import run_checks
from concorde.harness.runs import read_record
from concorde.operations import catalog
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.tasks import store
from concorde.tracing import locks
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
    return ctx.run_worker(
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


WORKER = Provider("implement", "implement", True, (worker_step,), None, goal_arguments)
RAISING = Provider("test", None, False, (raising_step,))
ADMITTED = Provider("understand", None, False, (admitted_step,))
# Execution commands: deterministic, no worker.
DETERMINISTIC = command("task-validation", (deterministic_step,), writes=False)
REFUSING = command("delivery", (refusing_step,), writes=True)


def reading_step(ctx):
    return ctx.run_worker(ctx.arguments.goal, task_type="understand", rounds=0)


def writing_step(ctx):
    return ctx.run_worker(ctx.arguments.goal, task_type="implement", rounds=0)


READER = Provider(
    "spec_review",
    "review-spec",
    False,
    (reading_step,),
    None,
    goal_arguments,
    binding="optional",
)
WRITER = Provider(
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
    return ctx.run_worker(ctx.arguments.goal, task_type="understand", rounds=0)


def probed(ctx):
    return Continue(output=ctx.state["probe"])


def probe_arguments(parser):
    goal_arguments(parser)
    parser.add_argument("--merge", action="store_true")
    parser.add_argument("--checks", action="store_true")
    parser.add_argument("--fail", action="store_true")


PROBE = Provider(
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
                catalog.CATALOG,
                {
                    "implement": f"{__name__}:WORKER",
                    "test": f"{__name__}:RAISING",
                    "understand": f"{__name__}:ADMITTED",
                    "spec_review": f"{__name__}:READER",
                    "code_review": f"{__name__}:WRITER",
                },
            ),
            (
                commands.COMMANDS,
                {
                    "task-validation": f"{__name__}:DETERMINISTIC",
                    "delivery": f"{__name__}:REFUSING",
                },
            ),
        ):
            patcher = patch.dict(table, entries)
            patcher.start()
            self.addCleanup(patcher.stop)

    def implement(self, steps, *extra, client="claude"):
        return self.project.run(
            "implement",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan(steps),
            *extra,
            client=client,
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

    @verifies("scenario.operations.worker-model")
    def test_a_worker_runs_with_the_task_worktrees_model(self):
        (self.worktree / models.CONFIG).write_text(
            json.dumps(
                {
                    "schema_version": 1,
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
            ("claude", "worker", "opus", "medium"),
            (record["backend"], record["worker"], record["model"], record["reasoning"]),
        )
        [shown] = [
            item for item in envelope["host_evidence"] if item["kind"] == "worker-model"
        ]
        self.assertEqual("claude", shown["ref"])
        self.assertIn("model opus, reasoning medium", shown["detail"])
        (self.root / models.CONFIG).write_text(
            json.dumps(
                {
                    "schema_version": 1,
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

    @verifies("scenario.operations.worker-backend-configured")
    def test_a_claude_code_main_session_runs_its_workers_on_pi(self):
        environ = self.fake_pi()
        (self.worktree / models.CONFIG).write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "enabled_models": {"local/fast": {}, "sonnet": {}},
                    "operations": {
                        "implement": {"workers": {"worker": {"model": "local/fast"}}},
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
            client="claude",
            environ=environ,
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        record = self.worker_record(envelope)
        self.assertEqual(
            ("pi", "Concorde's default worker backend", "local/fast"),
            (record["backend"], record["backend_source"], record["model"]),
        )
        argv = self.launched(envelope)
        self.assertEqual("local/fast", argv[argv.index("--model") + 1])
        self.assertIn("--no-extensions", argv)
        [shown] = [
            item for item in envelope["host_evidence"] if item["kind"] == "worker-model"
        ]
        self.assertEqual("pi", shown["ref"])
        self.assertIn("Concorde's default worker backend", shown["detail"])
        status, envelope = self.project.run(
            "spec_review",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan([{}]),
            client="claude",
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
        self.assertTrue(checkout.parent.name.startswith(PREFIX), checkout)
        self.assertFalse(checkout.parent.exists())
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

    @verifies("scenario.execution.unbound-read-only", "scenario.execution.unbound-run")
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
        self.assertIn("(unbound, ", envelope["error"]["actor"])
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

    @verifies("scenario.operations.worker-model-unavailable")
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
                    "schema_version": 1,
                    "enabled_models": {"local/fast": {}},
                    "default": {"model": "local/fast"},
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

    @verifies("scenario.operations.worker-ok")
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
            ["worker_step"], [step["name"] for step in node["content"]["data"]["steps"]]
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

    @verifies("scenario.operations.worker-blocked")
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

    @verifies("scenario.operations.spec-error")
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

    @verifies("scenario.operations.checks-exhausted")
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

    @verifies("scenario.operations.audit-violation")
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
        # The refusal is recorded like any run, and the lock is free again afterwards.
        self.assertEqual(envelope, self.saved(envelope))
        self.assertIsNone(runs.lock_holder(self.store(), "t1"))
        # An admitted run writes its result while it still holds the lock, so the next run
        # admitted finds that result written.
        holders = []
        write_text = Path.write_text

        def observed(path, *args, **kwargs):
            if path.name == "result.json":
                holders.append(runs.lock_holder(self.store(), "t1"))
            return write_text(path, *args, **kwargs)

        with patch.object(Path, "write_text", observed):
            status, envelope = self.project.run("task-validation", "--task", "t1")
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        [holder] = holders
        self.assertIn(envelope["run_id"], holder)
        self.assertIsNone(runs.lock_holder(self.store(), "t1"))
        status, following = self.project.run("task-validation", "--task", "t1")
        self.assertEqual("ok", following["status"])
        self.assertEqual(envelope, self.saved(envelope))

    @verifies("scenario.execution.workspace-wait")
    def test_a_waiting_run_queues_behind_the_running_one(self):
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
        # A wait the holder outlasts is still refused, saying how long it waited.
        status, envelope = self.project.run(
            "task-validation", "--task", "t1", "--wait", "0.3"
        )
        self.assertEqual(
            (1, ["refused", "workspace_busy"]), (status, codes(envelope["error"]))
        )
        self.assertIn("after waiting 0 s", json.dumps(envelope["error"]))
        self.assertIn("--wait <seconds>", json.dumps(envelope["error"]["options"]))
        # A detached run waits in its own process, naming the run it waits for.
        status, announced = detach(
            "command", "task-validation", ["--wait", "60"], cwd=self.worktree
        )
        self.assertEqual(0, status, announced)
        progress = Path(announced["progress"])
        deadline = time.monotonic() + 30
        shown = {}
        while time.monotonic() < deadline:
            shown = json.loads(progress.read_text())
            if shown.get("step") == "workspace-lock":
                break
            time.sleep(0.05)
        self.assertEqual(
            ("running", "workspace-lock", "implement run r-other"),
            (shown["phase"], shown["step"], shown["waiting_for"].split(" (process")[0]),
        )
        self.assertFalse(Path(announced["result"]).exists())
        release.set()
        envelope = self.wait_for(Path(announced["result"]))
        # Once the lock was free the run did its own work: a readiness, not a refusal.
        self.assertIsNotNone(envelope["output"], envelope)
        self.assertNotIn(
            "workspace_busy", [item["ref"] for item in envelope["host_evidence"]]
        )
        self.assertIsNone(json.loads(progress.read_text())["waiting_for"])
        with self.assertRaisesRegex(UsageError, "negative"):
            execute("command", "task-validation", ["--wait", "-1"], cwd=self.worktree)

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
        self.assertTrue(Path(announced["progress"]).is_file())
        folder = self.records / "tasks/t1/workspace/runs" / announced["run_id"]
        self.assertEqual(
            (folder, folder / "result.json"),
            (Path(announced["trace"]), Path(announced["result"])),
        )
        envelope = self.wait_for(Path(announced["result"]))
        validate(envelope, RESULT_SCHEMA)
        self.assertEqual(announced["run_id"], envelope["run_id"])
        self.assertEqual("t1", envelope["workspace"])
        self.assertEqual(envelope["status"], self.run_status(envelope))
        # The detached runner's own output is kept in the run's node.
        self.assertTrue((folder / "host.out").is_file())
        # A workspace already running something still gets its refusal as the result.
        with runs.workspace_lock(self.store(), "t1", "implement run r-other"):
            status, announced = detach(
                "command", "task-validation", [], cwd=self.worktree
            )
            self.assertEqual(0, status, announced)
            refused = self.wait_for(Path(announced["result"]))
        self.assertEqual("failed", refused["status"])
        self.assertIn(
            "workspace_busy", [item["ref"] for item in refused["host_evidence"]]
        )
        with self.assertRaises(UsageError):
            detach("operation", "frobnicate", ["--detach"], cwd=self.worktree)

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
        progress = Path(announced["progress"])
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
        fence = spec_contract("contract.execution.workspace-binding")
        self.assertEqual(binding_file.BINDING_SCHEMA, fence["schema"])

    def test_the_error_link_is_the_framework_contract(self):
        text = (REPOSITORY_ROOT / "specs/concorde/tracing/contracts.md").read_text()
        [fence] = [
            json.loads(block)
            for block in re.findall(
                r"```concorde-contract\n(.*?)\n```", text, re.DOTALL
            )
            if json.loads(block).get("id") == "contract.tracing.error"
        ]
        self.assertEqual(fence["schema"], ERROR_SCHEMA)
        self.assertEqual(RESULT_SCHEMA["$defs"]["error"], LINK_SCHEMA)


class UnboundCheckoutTests(unittest.TestCase):
    """An unbound run works in a throwaway detached checkout of its worktree's HEAD."""

    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        self.records = self.root / ".concorde"
        patcher = patch.dict(catalog.CATALOG, {"understand": f"{__name__}:PROBE"})
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
                    "schema_version": 1,
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
                    "schema_version": 1,
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
        self.assertTrue(checkout.parent.name.startswith(PREFIX), checkout)
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
        self.assertFalse(checkout.parent.exists())
        self.assertEqual([self.root], worktrees(self.root))
        # The starting worktree keeps its change, its environment and the commit made meanwhile.
        self.assertEqual("uncommitted\n", (self.root / "src/a/calc.py").read_text())
        self.assertEqual("tool\n", (self.root / ".venv/bin/tool").read_text())
        self.assertNotEqual(examined, head(self.root))
        validate(envelope, RESULT_SCHEMA)

    @verifies("scenario.execution.unbound-checkout")
    def test_the_checkout_is_removed_however_the_run_ends(self):
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
        self.assertEqual([self.root], worktrees(self.root))
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

    @verifies("scenario.execution.unbound-checkout")
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
        self.assertEqual(Path(value["traces"]), binding_file.traces_of(worktree, value))
        self.assertEqual(
            Path(value["concorde"]), binding_file.concorde_of(worktree, value)
        )
        self.assertIsNone(binding_file.traces_of(self.root, None))
        self.assertEqual(
            self.root / ".concorde", binding_file.concorde_of(self.root, None)
        )
        # The binding is ignored by Git: opening a task changes nothing a commit would carry.
        self.assertTrue(
            ".concorde/workspace.json" in (worktree / ".gitignore").read_text()
        )

    def test_a_binding_that_breaks_its_contract_is_never_written(self):
        from concorde.spec.schema import ContractError

        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        before = (worktree / binding_file.BINDING).read_text()
        with self.assertRaises(ContractError):
            binding_file.write(
                worktree, {**binding_file.load(worktree), "workspace": "Not A Name"}
            )
        self.assertEqual(before, (worktree / binding_file.BINDING).read_text())


if __name__ == "__main__":
    unittest.main()
