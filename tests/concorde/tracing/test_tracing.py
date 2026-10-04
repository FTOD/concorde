"""Tracing: trace nodes, their reading and roll-up, retention, locks and the trace command."""

from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.kernel.tracing import (
    command,
    kinds,
    layout,
    locks,
    reader,
    retention,
    roots,
)
from concorde.kernel.tracing import node as trace
from concorde.kernel.tracing.node import NODE_SCHEMA, Node, TraceError

# Concorde's trace roots, which Tasks and Execution register when their code loads: the current
# tasks and the history, the unbound runs and the lobby.
from concorde.coordination.tasks.store import TRACE_ROOTS as TASK_ROOTS
from concorde.execution.runs import TRACE_ROOTS as RUN_ROOTS

# Concorde's node kinds, which each producing part registers when its code loads.
import concorde.coordination.tasks.deliver  # noqa: E402,F401
import concorde.execution.checks.checks  # noqa: E402,F401
import concorde.worker_harness.workers  # noqa: E402,F401
import concorde.workflows.store  # noqa: E402,F401

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def spec_contract(identity: str) -> dict:
    text = (REPOSITORY_ROOT / "specs/concorde/kernel/tracing/contracts.md").read_text()
    for fence in re.findall(r"```concorde-contract\n(.*?)\n```", text, re.DOTALL):
        value = json.loads(fence)
        if value["id"] == identity:
            return value
    raise AssertionError(f"no contract {identity}")


def ended(
    folder: Path, identity: str, kind: str, *, status="ok", used=None, **extra
) -> dict:
    """Write a node that started and ended, with ``used`` as its own usage."""
    record = {
        "schema_version": 1,
        "id": identity,
        "kind": kind,
        "started_at": extra.pop("started_at", "2026-09-27T10:00:00.000000Z"),
        "ended_at": extra.pop("ended_at", "2026-09-27T10:05:00.000000Z"),
        "status": status,
        "outcome": status if status != "running" else None,
        "usage": trace.usage(**(used or {})),
        "error": None,
        "metadata": extra.pop("metadata", {}),
        "artifacts": [],
        "references": [],
        "content": None,
    }
    record.update(extra)
    trace.write(folder, record)
    return record


class TaskTrace:
    """A task folder with a workspace whose run launched a worker of two rounds, and delivery."""

    def __init__(self, concorde: Path, task: str = "retry"):
        self.concorde = concorde
        self.folder = Path(concorde) / "tasks" / task
        ended(
            self.folder,
            task,
            "task",
            status="running",
            ended_at=None,
            metadata={"task": task},
        )
        workspace = Path(self.folder) / "workspace"
        self.run = layout.run_folder(workspace, "r-20260927T100100-implement-00000001")
        ended(
            self.run,
            self.run.name,
            "run",
            metadata={"workspace": task, "operation": "implement"},
        )
        worker = layout.worker_folder(self.run, "w-20260927T100101-aaaaaa")
        self.worker = worker
        ended(worker, worker.name, "worker-run", metadata={"worker": "worker"})
        for number, cost in ((1, 0.25), (2, 0.5)):
            ended(
                layout.round_folder(worker, number),
                str(number),
                "worker-round",
                used={
                    "tokens_in": 1000 * number,
                    "tokens_out": 100 * number,
                    "tokens_cache_read": 10,
                    "tokens_cache_write": 1,
                    "cost_usd": cost,
                    "turns": 3,
                },
                started_at=f"2026-09-27T10:0{number}:00.000000Z",
            )
        self.delivery = layout.run_folder(
            workspace, "r-20260927T100900-delivery-00000002"
        )
        ended(
            self.delivery,
            self.delivery.name,
            "run",
            metadata={"command": "delivery"},
            started_at="2026-09-27T10:09:00.000000Z",
        )


class TracingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "project"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.concorde = self.root / ".concorde"

    def tearDown(self):
        self.temporary.cleanup()

    def test_the_parts_register_the_roots_the_contract_names(self):
        registered = {root.name: root for root in roots.registered()}
        self.assertEqual(
            {
                "current tasks": ("tasks", "task", "current", "always", None),
                "history": ("history", "task", "closed", "history", "history_days"),
                "unbound runs": (
                    "unbound",
                    "run",
                    "current",
                    "unbound",
                    "unbound_days",
                ),
                "lobby": ("lobby", "run", "current", "never", "unbound_days"),
            },
            {
                root.name: (
                    root.folder,
                    root.kind,
                    root.state,
                    root.listed,
                    root.period,
                )
                for root in (*TASK_ROOTS, *RUN_ROOTS)
            },
        )
        for root in (*TASK_ROOTS, *RUN_ROOTS):
            self.assertIs(root, registered[root.name])
        with self.assertRaises(roots.RootError) as refused:
            roots.register(replace(TASK_ROOTS[1], state="current"))
        self.assertEqual("duplicate_root", refused.exception.code)

    def test_the_node_schema_is_the_contract(self):
        self.assertEqual(spec_contract("contract.tracing.node")["schema"], NODE_SCHEMA)
        self.assertEqual(
            spec_contract("contract.tracing.configuration")["schema"],
            retention.CONFIGURATION_SCHEMA,
        )
        example = spec_contract("contract.tracing.node")["example"]
        validate(example, NODE_SCHEMA)

    def test_a_node_is_written_at_its_start_and_its_end(self):
        folder = self.root / "node"
        node = Node(
            folder, "7", "check", metadata={"check": "check.a", "module": "module.a"}
        )
        (folder / "output.log").parent.mkdir(parents=True, exist_ok=True)
        node.keep("output", "output.log")
        node.start()
        started = trace.read(folder)
        self.assertEqual("running", started["status"])
        self.assertIsNone(started["ended_at"])
        (folder / "output.log").write_text("ok\n")
        node.finish("ok", outcome="passed", used={"duration_seconds": 1.5})
        finished = trace.read(folder)
        self.assertEqual(
            ("ok", "passed", 1.5),
            (
                finished["status"],
                finished["outcome"],
                finished["usage"]["duration_seconds"],
            ),
        )
        self.assertEqual("output.log", finished["artifacts"][0]["path"])
        self.assertRegex(finished["artifacts"][0]["digest"], r"^sha256:[0-9a-f]{64}$")

    def test_a_failed_write_never_stops_the_work_and_is_kept_for_its_producer(self):
        folder = self.root / "node"
        node = Node(
            folder, "7", "check", metadata={"check": "check.a", "module": "module.a"}
        )
        failure = PermissionError(13, "Permission denied")
        with patch.object(trace, "write", side_effect=failure):
            node.start()
        self.assertIs(failure, node.failure)
        [account] = node.failures
        self.assertIn(str(folder / layout.TRACE), account)
        self.assertIn("at its start", account)
        self.assertIn("Permission denied", account)
        node.finish("ok")
        self.assertIsNone(node.failure)
        self.assertEqual([account], node.failures)
        self.assertEqual("ok", trace.read(folder)["status"])

    def test_a_node_refuses_an_unknown_metadata_dimension_and_an_absolute_artifact(
        self,
    ):
        folder = self.root / "node"
        with self.assertRaises(TraceError):
            Node(folder, "1", "run", metadata={"weather": "sunny"})
        record = ended(folder, "1", "run")
        record["artifacts"] = [{"id": "x", "path": "/etc/passwd", "digest": None}]
        with self.assertRaises(TraceError):
            trace.write(folder, record)

    @verifies("scenario.tracing.kind-registered")
    def test_a_node_is_checked_against_the_registration_of_its_kind(self):
        from concorde.execution.checks.checks import CHECK_TRACE
        from concorde.worker_harness.workers import WORKER_ROUND_TRACE

        own = {"check": "check.a", "module": "module.a"}
        for name, kind, metadata, content_type, code in (
            ("unregistered", "weather", {}, None, "node_invalid"),
            ("metadata", "check", {**own, "workspace": "w"}, None, "node_invalid"),
            ("content", "check", own, WORKER_ROUND_TRACE, "content_invalid"),
        ):
            folder = self.root / name
            with self.subTest(name), self.assertRaises(TraceError) as refused:
                node = Node(folder, "1", kind, metadata=metadata)
                if content_type:
                    node.record["content"] = {
                        "type_id": content_type,
                        "schema_version": 1,
                        "data": {},
                    }
                trace.write(folder, node.record)
            self.assertEqual(code, refused.exception.code)
            self.assertFalse((folder / layout.TRACE).exists())
        self.assertEqual(CHECK_TRACE, kinds.lookup("check").content_type)
        Node(self.root / "kept", "1", "check", metadata=own).start()
        self.assertEqual("check", trace.read(self.root / "kept")["kind"])

    @verifies("scenario.tracing.created-or-found")
    def test_a_node_tells_what_it_created_from_what_it_found(self):
        commit = "4be1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9"
        created = Node(self.root / "created", "r-1", "run")
        created.start()
        created.refer("commit", commit)
        created.finish("ok", outcome="ok")
        found = Node(self.root / "found", "r-2", "run")
        found.start()
        found.refer("found_commit", commit)
        found.finish("ok", outcome="ok")
        records = [trace.read(self.root / name) for name in ("created", "found")]
        for record in records:
            validate(record, spec_contract("contract.tracing.node")["schema"])
        self.assertEqual(
            [
                [(item["relation"], item["target"]) for item in record["references"]]
                for record in records
            ],
            [[("commit", commit)], [("found_commit", commit)]],
        )
        for relation in ("reported_commit", "bundle"):
            record = ended(self.root / "other", "r-3", "run")
            record["references"] = [{"relation": relation, "target": commit}]
            with self.assertRaises(TraceError):
                trace.write(self.root / "other", record)

    @verifies("scenario.tracing.show-task")
    def test_a_tasks_trace_rolls_its_usage_up(self):
        TaskTrace(self.concorde)
        before = sorted(str(path) for path in self.concorde.rglob("*"))
        value = reader.view(Path(self.concorde) / "tasks" / "retry", self.concorde)
        validate(value, spec_contract("contract.tracing.view")["schema"])
        self.assertEqual("task", value["kind"])
        workspace = value["children"][0]
        self.assertEqual("workspace", workspace["kind"])
        runs = workspace["children"]
        self.assertEqual(
            ["implement", "delivery"],
            [
                run["metadata"].get("operation") or run["metadata"].get("command")
                for run in runs
            ],
        )
        worker = runs[0]["children"][0]
        self.assertEqual(["1", "2"], [item["id"] for item in worker["children"]])
        self.assertEqual(3000, value["rolled_up"]["tokens_in"])
        self.assertEqual(0.75, value["rolled_up"]["cost_usd"])
        self.assertEqual(6, value["rolled_up"]["turns"])
        self.assertEqual(0.25, worker["children"][0]["usage"]["cost_usd"])
        self.assertIsNone(runs[0]["usage"]["cost_usd"])
        self.assertEqual(before, sorted(str(path) for path in self.concorde.rglob("*")))
        tree = reader.render(value)
        self.assertIn("worker-round 2", tree)

    @verifies("scenario.tracing.show-by-identity")
    def test_a_run_is_found_by_its_identity_wherever_it_lies(self):
        task = TaskTrace(self.concorde)
        step = layout.step_folder(
            layout.workflow_folder(Path(task.folder) / "workspace"), 1, "survey"
        )
        ended(step, "survey", "step")
        ended(step / "run", "r-20260927T100200-survey-00000003", "run")
        unbound = (
            Path(self.concorde) / "unbound" / "r-20260927T100300-understand-00000004"
        )

        ended(unbound, unbound.name, "run")
        lobby = Path(self.concorde) / "lobby" / "r-20260927T100500-implement-00000005"

        ended(lobby, lobby.name, "run", status="failed")
        roots = [self.concorde]
        found, _ = reader.locate("r-20260927T100200-survey-00000003", roots)
        self.assertEqual(step / "run", found)
        found, _ = reader.locate(unbound.name, roots)
        self.assertEqual(unbound, found)
        found, _ = reader.locate(lobby.name, roots)
        self.assertEqual(lobby, found)
        self.assertEqual("run", reader.view(found, self.concorde)["kind"])
        found, _ = reader.locate("w-20260927T100101-aaaaaa", roots)
        self.assertEqual(task.worker, found)
        with self.assertRaises(reader.ReadError) as refused:
            reader.locate("r-20260927T100400-understand-00000009", roots)
        self.assertEqual("unknown_node", refused.exception.code)
        self.assertIn(str(self.concorde), str(refused.exception))

    @verifies("scenario.tracing.lost-run")
    def test_a_running_run_without_its_lock_holder_is_lost(self):
        task = TaskTrace(self.concorde)
        ended(task.run, task.run.name, "run", status="running", ended_at=None)
        ended(
            task.worker, task.worker.name, "worker-run", status="running", ended_at=None
        )
        value = reader.view(task.run, self.concorde)
        self.assertEqual("lost", value["status"])
        self.assertEqual("lost", value["children"][0]["status"])
        # A worker run or round addressed directly is lost as well.
        round_folder = layout.round_folder(task.worker, 3)
        ended(round_folder, "3", "worker-round", status="running", ended_at=None)
        self.assertEqual("lost", reader.view(task.worker, self.concorde)["status"])
        self.assertEqual("lost", reader.view(round_folder, self.concorde)["status"])
        output = io.StringIO()
        with redirect_stdout(output):
            command.main(["show", task.worker.name], here=self.root)
        self.assertEqual("lost", json.loads(output.getvalue())["status"])
        lock = layout.lock_file(self.concorde, "run", task.run.name)
        with locks.hold(lock, "a runner", remove=True):
            self.assertEqual("running", reader.view(task.run, self.concorde)["status"])
            self.assertEqual(
                "running", reader.view(task.worker, self.concorde)["status"]
            )
        self.assertFalse(lock.exists())

    @verifies("scenario.tracing.list")
    def test_current_tasks_history_and_unbound_runs_are_listed(self):
        TaskTrace(self.concorde, "one")
        TaskTrace(self.concorde, "two")
        closed = TaskTrace(self.concorde, "old")
        shutil.move(closed.folder, Path(self.concorde) / "history" / "old")
        unbound = (
            Path(self.concorde) / "unbound" / "r-20260927T100300-understand-00000004"
        )

        ended(unbound, unbound.name, "run")
        listed = reader.listing(self.concorde, history=True, unbound=True)
        self.assertEqual(
            ["one", "two", "old", unbound.name], [item["id"] for item in listed]
        )
        self.assertTrue(all(item["children"] == [] for item in listed))
        self.assertEqual(0.75, listed[0]["rolled_up"]["cost_usd"])
        self.assertEqual(2, len(reader.listing(self.concorde)))

    def test_a_root_is_looked_for_only_in_its_registered_place(self):
        # A linked worktree, whose .git is a file, keeps no current task: only roots of the
        # worktree a node started in, such as the unbound runs, lie under its .concorde.
        linked = Path(self.temporary.name) / "linked"
        linked.mkdir()
        (linked / ".git").write_text("gitdir: elsewhere\n")
        concorde = linked / ".concorde"
        TaskTrace(concorde, "stray")
        unbound = concorde / "unbound" / "r-20260927T100300-understand-00000005"
        ended(unbound, unbound.name, "run")
        self.assertEqual(
            [unbound.name],
            [
                item["id"]
                for item in reader.listing(concorde, history=True, unbound=True)
            ],
        )
        with self.assertRaises(reader.ReadError):
            reader.locate("stray", [concorde])
        self.assertEqual(unbound, reader.locate(unbound.name, [concorde])[0])
        TaskTrace(self.concorde, "kept")
        self.assertEqual(
            self.concorde / "tasks" / "kept",
            reader.locate("kept", [concorde, self.concorde])[0],
        )

    @verifies("scenario.tracing.history-reads-alike")
    def test_a_task_moved_to_the_history_reads_the_same(self):
        task = TaskTrace(self.concorde)
        before = reader.view(task.folder, self.concorde)
        target = Path(self.concorde) / "history" / "retry"
        target.parent.mkdir(parents=True)
        task.folder.rename(target)
        after = reader.view(target, self.concorde)

        def strip(value):
            return {
                key: [strip(child) for child in item] if key == "children" else item
                for key, item in value.items()
                if key not in ("path", "duration_seconds")
            }

        self.assertEqual(strip(before), strip(after))
        self.assertEqual(str(target), after["path"])
        self.assertEqual(target, reader.locate("retry", [self.concorde])[0])

    @verifies("scenario.tracing.prune")
    def test_retention_removes_only_what_ended_long_enough_ago(self):
        now = datetime(2026, 9, 29, tzinfo=UTC)

        def at(delta: timedelta) -> str:
            return (now - delta).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        old = Path(self.concorde) / "unbound" / "r-20260920T000000-understand-00000001"

        ended(old, old.name, "run", ended_at=at(timedelta(days=8)))
        fresh = (
            Path(self.concorde) / "unbound" / "r-20260928T000000-understand-00000002"
        )

        ended(fresh, fresh.name, "run", ended_at=at(timedelta(days=1)))
        running = (
            Path(self.concorde) / "unbound" / "r-20260920T000000-understand-00000003"
        )

        ended(running, running.name, "run", status="running", ended_at=None)
        refused = Path(self.concorde) / "lobby" / "r-20260920T000000-implement-00000004"

        ended(refused, refused.name, "run", ended_at=at(timedelta(days=8)))
        history = Path(self.concorde) / "history" / "done"
        ended(history, "done", "task", ended_at=at(timedelta(days=365)))
        conversations = [
            history / "sessions" / "s1" / "transcript.jsonl",
            history / "sessions" / "s1" / "transcript" / "subagents" / "a.jsonl",
            history
            / "workspace"
            / "runs"
            / "r-1"
            / "workers"
            / "w-1"
            / "transcript.jsonl",
        ]
        for path in conversations:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n")
        (history / "decisions.md").write_text("# Decision log: done\n")
        recent = Path(self.concorde) / "history" / "recent"
        ended(recent, "recent", "task", ended_at=at(timedelta(days=2)))
        (recent / "sessions" / "s3").mkdir(parents=True)
        (recent / "sessions" / "s3" / "transcript.jsonl").write_text("{}\n")
        removed = [
            str(old),
            str(refused),
            str(history / "sessions" / "s1" / "transcript"),
            *(str(conversations[index]) for index in (0, 2)),
        ]
        dry = retention.prune(self.concorde, dry_run=True, moment=now)
        self.assertEqual((sorted(removed), []), (sorted(dry["removed"]), dry["failed"]))
        self.assertTrue(old.exists() and conversations[0].exists())
        pruned = retention.prune(self.concorde, moment=now)
        self.assertEqual(
            (sorted(removed), []), (sorted(pruned["removed"]), pruned["failed"])
        )
        self.assertFalse(old.exists())
        self.assertFalse(any(path.exists() for path in conversations))
        self.assertTrue(fresh.exists() and running.exists() and history.exists())
        self.assertTrue((history / "decisions.md").exists())
        self.assertTrue((history / layout.TRACE).exists())
        self.assertTrue((recent / "sessions" / "s3" / "transcript.jsonl").exists())
        (self.concorde / "tracing.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "retention": {"unbound_days": 7, "history_days": 30},
                }
            )
        )
        self.assertEqual(
            [str(history)], retention.prune(self.concorde, moment=now)["removed"]
        )
        (self.concorde / "tracing.json").write_text('{"schema_version": 1}')
        with self.assertRaises(retention.ConfigError):
            retention.prune(self.concorde, moment=now)

    @verifies("scenario.tracing.prune")
    def test_a_folder_prune_cannot_remove_is_reported_with_its_error(self):
        run = Path(self.concorde) / "unbound" / "r-20260101T000000-understand-00000001"
        ended(run, run.name, "run", ended_at="2026-01-01T00:00:00.000000Z")
        (run / "kept").mkdir()

        def refused(*arguments, **keywords):
            raise PermissionError(13, "Permission denied", str(arguments[0]))

        with patch("os.rmdir", refused):
            pruned = retention.prune(self.concorde)
        self.assertEqual([], pruned["removed"])
        [failed] = pruned["failed"]
        self.assertEqual(str(run), failed["path"])
        self.assertIn("Permission denied", failed["error"])
        self.assertTrue(run.exists())
        self.assertEqual([str(run)], retention.prune(self.concorde)["removed"])

    def test_the_prune_command_reaches_a_linked_worktree_s_unbound_runs(self):
        identity = ("-c", "user.name=t", "-c", "user.email=t@t")
        subprocess.run(
            [
                "git",
                *identity,
                "-C",
                str(self.root),
                "commit",
                "-q",
                "--allow-empty",
                "-m",
                "start",
            ],
            check=True,
        )
        linked = Path(self.temporary.name) / "linked"
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "worktree",
                "add",
                "-q",
                "--detach",
                str(linked),
            ],
            check=True,
        )
        old = linked / ".concorde" / "unbound" / "r-20260101T000000-understand-00000001"
        ended(old, old.name, "run", ended_at="2026-01-01T00:00:00.000000Z")
        primary = self.concorde / "unbound" / "r-20260101T000000-understand-00000002"
        ended(primary, primary.name, "run", ended_at="2026-01-01T00:00:00.000000Z")
        (self.concorde / "tracing.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "retention": {"unbound_days": None, "history_days": None},
                }
            )
        )
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(0, command.main(["prune"], here=linked))
        self.assertEqual(
            {"removed": [], "failed": [], "dry_run": False},
            json.loads(output.getvalue()),
        )
        (self.concorde / "tracing.json").unlink()
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(0, command.main(["prune", "--dry-run"], here=linked))
        self.assertEqual(
            sorted([str(old), str(primary)]),
            sorted(json.loads(output.getvalue())["removed"]),
        )
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(0, command.main(["prune"], here=linked))
        self.assertFalse(old.exists() or primary.exists())

    def test_a_workspace_node_shows_its_running_or_latest_child_s_status(self):
        task = TaskTrace(self.concorde)
        workspace = Path(task.folder) / "workspace"

        def status() -> str:
            return reader.view(workspace, self.concorde)["status"]

        self.assertEqual("ok", status())
        ended(
            task.delivery,
            task.delivery.name,
            "run",
            status="failed",
            started_at="2026-09-27T10:09:00.000000Z",
        )
        self.assertEqual("failed", status())
        ended(task.run, task.run.name, "run", status="running", ended_at=None)
        lock = layout.lock_file(self.concorde, "run", task.run.name)
        with locks.hold(lock, "a runner", remove=True):
            self.assertEqual("running", status())
        # A lost run is no running child: the latest child's status stands.
        self.assertEqual("failed", status())
        empty = Path(self.temporary.name) / "empty-workspace"
        (empty / "runs").mkdir(parents=True)
        self.assertEqual("unknown", reader.view(empty, self.concorde)["status"])

    def test_listing_orders_roots_before_directories(self):
        linked = Path(self.temporary.name) / "linked"
        linked.mkdir()
        (linked / ".git").write_text("gitdir: elsewhere\n")
        unbound = (
            linked / ".concorde" / "unbound" / "r-20260927T100300-understand-00000005"
        )
        ended(unbound, unbound.name, "run")
        TaskTrace(self.concorde, "current")
        closed = TaskTrace(self.concorde, "old")
        shutil.move(closed.folder, Path(self.concorde) / "history" / "old")
        listed = reader.listing(
            [linked / ".concorde", self.concorde], history=True, unbound=True
        )
        self.assertEqual(
            ["current", "old", unbound.name], [item["id"] for item in listed]
        )

    def test_the_tree_names_a_node_s_error_code(self):
        task = TaskTrace(self.concorde)
        ended(
            task.delivery,
            task.delivery.name,
            "run",
            status="failed",
            error={"code": "checks_failed"},
            started_at="2026-09-27T10:09:00.000000Z",
        )
        tree = reader.render(reader.view(task.folder, self.concorde))
        self.assertIn("error checks_failed", tree)

    def test_a_workspace_folder_without_a_task_is_shown(self):
        workspace = self.root / "elsewhere" / "workspace-folder"
        run = layout.run_folder(workspace, "r-20260927T100100-implement-00000001")
        ended(
            run,
            run.name,
            "run",
            metadata={"workspace": "adhoc"},
            used={"cost_usd": 0.5},
        )
        value = reader.view(workspace, self.concorde)
        self.assertEqual(("workspace", "adhoc"), (value["kind"], value["id"]))
        self.assertEqual(0.5, value["rolled_up"]["cost_usd"])

    def test_a_lock_names_its_holder_and_refuses_a_second_holder(self):
        path = layout.lock_file(self.concorde, "workspace", "retry")
        with locks.hold(path, "implement run r-1"):
            self.assertIn("implement run r-1", locks.holder(path))
            with (
                self.assertRaises(locks.LockBusy) as busy,
                locks.hold(path, "delivery run r-2", wait=0.3),
            ):
                pass
            self.assertIn("implement run r-1", busy.exception.holder)
        self.assertIsNone(locks.holder(path))
        self.assertEqual("", path.read_text())

    def test_the_trace_command_shows_lists_and_refuses(self):
        TaskTrace(self.concorde)
        output = io.StringIO()
        with redirect_stdout(output):
            status = command.main(["show", "retry", "--depth", "1"], here=self.root)
        self.assertEqual(0, status)
        value = json.loads(output.getvalue())
        self.assertEqual("retry", value["id"])
        self.assertEqual([], value["children"][0]["children"])
        self.assertEqual(0.75, value["rolled_up"]["cost_usd"])
        output = io.StringIO()
        with redirect_stdout(output):
            status = command.main(["show", "nothing-here"], here=self.root)
        self.assertEqual(1, status)
        self.assertEqual("unknown_node", json.loads(output.getvalue())["error"]["code"])
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(
                0, command.main(["list", "--format", "tree"], here=self.root)
            )
        self.assertIn("task retry", output.getvalue())
        self.assertEqual(
            2, command.main(["show", "--depth", "-1", "retry"], here=self.root)
        )


if __name__ == "__main__":
    unittest.main()
