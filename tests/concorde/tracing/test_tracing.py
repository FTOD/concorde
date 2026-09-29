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
from datetime import UTC, datetime, timedelta
from pathlib import Path

from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.tracing import command, layout, locks, reader, retention
from concorde.tracing import node as trace
from concorde.tracing.node import NODE_SCHEMA, Node, TraceError

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def spec_contract(identity: str) -> dict:
    text = (REPOSITORY_ROOT / "specs/concorde/tracing/contracts.md").read_text()
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
        self.folder = layout.task_folder(concorde, task)
        ended(
            self.folder,
            task,
            "task",
            status="running",
            ended_at=None,
            metadata={"task": task},
        )
        workspace = layout.workspace_folder(self.folder)
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

    @verifies("scenario.tracing.show-task")
    def test_a_tasks_trace_rolls_its_usage_up(self):
        TaskTrace(self.concorde)
        before = sorted(str(path) for path in self.concorde.rglob("*"))
        value = reader.view(layout.task_folder(self.concorde, "retry"), self.concorde)
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
            layout.workflow_folder(layout.workspace_folder(task.folder)), 1, "survey"
        )
        ended(step, "survey", "step")
        ended(step / "run", "r-20260927T100200-survey-00000003", "run")
        unbound = layout.unbound_run_folder(
            self.concorde, "r-20260927T100300-understand-00000004"
        )
        ended(unbound, unbound.name, "run")
        roots = [self.concorde]
        found, _ = reader.locate("r-20260927T100200-survey-00000003", roots)
        self.assertEqual(step / "run", found)
        found, _ = reader.locate(unbound.name, roots)
        self.assertEqual(unbound, found)
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
        lock = layout.lock_file(self.concorde, "run", task.run.name)
        with locks.hold(lock, "a runner", remove=True):
            self.assertEqual("running", reader.view(task.run, self.concorde)["status"])
        self.assertFalse(lock.exists())

    @verifies("scenario.tracing.list")
    def test_current_tasks_history_and_unbound_runs_are_listed(self):
        TaskTrace(self.concorde, "one")
        TaskTrace(self.concorde, "two")
        closed = TaskTrace(self.concorde, "old")
        shutil.move(closed.folder, layout.history_folder(self.concorde) / "old")
        unbound = layout.unbound_run_folder(
            self.concorde, "r-20260927T100300-understand-00000004"
        )
        ended(unbound, unbound.name, "run")
        listed = reader.listing(self.concorde, history=True, unbound=True)
        self.assertEqual(
            ["one", "two", "old", unbound.name], [item["id"] for item in listed]
        )
        self.assertTrue(all(item["children"] == [] for item in listed))
        self.assertEqual(0.75, listed[0]["rolled_up"]["cost_usd"])
        self.assertEqual(2, len(reader.listing(self.concorde)))

    @verifies("scenario.tracing.history-reads-alike")
    def test_a_task_moved_to_the_history_reads_the_same(self):
        task = TaskTrace(self.concorde)
        before = reader.view(task.folder, self.concorde)
        target = layout.history_folder(self.concorde) / "retry"
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

        old = layout.unbound_run_folder(
            self.concorde, "r-20260920T000000-understand-00000001"
        )
        ended(old, old.name, "run", ended_at=at(timedelta(days=8)))
        fresh = layout.unbound_run_folder(
            self.concorde, "r-20260928T000000-understand-00000002"
        )
        ended(fresh, fresh.name, "run", ended_at=at(timedelta(days=1)))
        running = layout.unbound_run_folder(
            self.concorde, "r-20260920T000000-understand-00000003"
        )
        ended(running, running.name, "run", status="running", ended_at=None)
        history = layout.history_folder(self.concorde) / "done"
        ended(history, "done", "task", ended_at=at(timedelta(days=365)))
        dry = retention.prune(self.concorde, dry_run=True, moment=now)
        self.assertEqual([str(old)], dry)
        self.assertTrue(old.exists())
        self.assertEqual([str(old)], retention.prune(self.concorde, moment=now))
        self.assertFalse(old.exists())
        self.assertTrue(fresh.exists() and running.exists() and history.exists())
        (self.concorde / "tracing.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "retention": {"unbound_days": 7, "history_days": 30},
                }
            )
        )
        self.assertEqual([str(history)], retention.prune(self.concorde, moment=now))
        (self.concorde / "tracing.json").write_text('{"schema_version": 1}')
        with self.assertRaises(retention.ConfigError):
            retention.prune(self.concorde, moment=now)

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
