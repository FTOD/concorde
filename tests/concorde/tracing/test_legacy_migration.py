"""The one-off migration of the task records and run store from before Tracing."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from concorde.tasks import store
from concorde.tracing import layout, locks, reader
from concorde.tracing import node as trace
from tests.concorde.support.paths import REPOSITORY_ROOT

SCRIPT = REPOSITORY_ROOT / "scripts/development/migrate-legacy-records.py"
_spec = importlib.util.spec_from_file_location("migrate_legacy_records", SCRIPT)
migration = importlib.util.module_from_spec(_spec)
# Its dataclasses look their module up by name.
sys.modules[_spec.name] = migration
_spec.loader.exec_module(migration)

COMMIT = "1c901df3f11178ea5516eb0dc4f24d65f829f281"
AFTER = "58afc57ab038bcdd095e9b11119a9cf5000ac140"


def closed(
    state="closed", outcome="merged", at="2026-09-28T17:24:52Z", **extra
) -> dict:
    return {
        "state": state,
        "outcome": outcome,
        "note": None,
        "errors": [],
        "at": at,
        "primary_commit": AFTER,
        "worktree_removed": True,
        **extra,
    }


def old_record(task: str, **extra) -> dict:
    record = {
        "id": task,
        "goal": f"the goal of {task}",
        "modules": ["module.tracing"],
        "branch": f"concorde/{task}",
        "worktree": f"/home/dev/project/.claude/worktrees/{task}",
        "base_commit": COMMIT,
        "state": "closed",
        "created_at": "2026-09-28T17:13:33Z",
        "updated_at": "2026-09-28T17:24:52Z",
        "escalations": [],
        "sessions": [],
        "merging": None,
        "closed": closed(),
    }
    record.update(extra)
    return record


def snapshot(folder: Path) -> dict[str, str]:
    """Every file below ``folder`` with its digest."""
    return {
        path.relative_to(folder).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


class LegacyMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        base = Path(self.temporary.name)
        self.root = base / "project"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.concorde = self.root / ".concorde"
        self.tasks = self.concorde / "tasks"
        self.tasks.mkdir(parents=True)
        self.archive = base / "old-records.tar.zst"
        self.write_old_layout()

    def tearDown(self):
        self.temporary.cleanup()

    def old(self, task: str, record: dict, *, decisions=True, merge_log=True) -> None:
        (self.tasks / f"{task}.json").write_text(json.dumps(record, indent=2) + "\n")
        if decisions:
            (self.tasks / f"{task}.decisions.md").write_text(
                f"# Decision log: {task}\n\nGoal: {record['goal']}\n\n## A decision\n"
            )
        if merge_log:
            (self.tasks / f"{task}.merge.log").write_text(
                f"# 2026-09-28T17:24:38Z merged concorde/{task}\n$ build\n[exit 0]\n"
            )

    def write_old_layout(self) -> None:
        # A task a Claude Code session worked, delivered once, with an escalation.
        self.old(
            "adoption",
            old_record(
                "adoption",
                sessions=[
                    {
                        "program": "claude",
                        "id": "f335fd1a",
                        "name": "task-adoption",
                        "main": "main session",
                        "settings": "/somewhere/adoption.session/settings.json",
                        "started_at": "2026-09-28T17:16:44Z",
                    }
                ],
                escalations=[
                    {
                        "at": "2026-09-28T17:20:00Z",
                        "error": {"level": "task-session", "code": "needs_decision"},
                    }
                ],
                runs=[
                    {"run_id": "r-20260928T171700-delivery-0000abcd", "status": "ok"}
                ],
                deliveries=[
                    {
                        "run_id": "r-20260928T171700-delivery-0000abcd",
                        "commit": "8c749d065b7ad3063e6d9899bdc587506dc86f79",
                        "bundle": ".concorde/evidence/adoption/1.json",
                        "readiness_run": "r-20260928T171700-delivery-0000abcd",
                        "at": "2026-09-28T17:18:00Z",
                    }
                ],
            ),
        )
        session = self.tasks / "adoption.session"
        session.mkdir()
        (session / "settings.json").write_text("{}\n")
        (session / "write_hook.py").write_text("# hook\n")
        # A task a pi session worked in two rounds.
        self.old(
            "pi-task",
            old_record(
                "pi-task",
                sessions=[
                    {
                        "program": "pi",
                        "id": "task-pi-task-20260928T093118",
                        "name": "task-pi-task",
                        "main": "01a0e758",
                        "directory": "/somewhere/pi-task.session",
                        "model": None,
                        "started_at": "2026-09-28T09:31:18Z",
                        "rounds": [
                            {
                                "round": 1,
                                "prompt": "task",
                                "status": "escalated",
                                "supervisor_pid": 2581539,
                                "started_at": "2026-09-28T09:31:18Z",
                                "ended_at": "2026-09-28T09:38:22Z",
                                "report": {"escalations": [1]},
                                "error": {"level": "task-session", "code": "decision"},
                                "events": "/somewhere/round-1.events.jsonl",
                                "stderr": "/somewhere/round-1.stderr.log",
                            },
                            {
                                "round": 2,
                                "prompt": "answer",
                                "answer": "do it",
                                "status": "delivered",
                                "supervisor_pid": 2581600,
                                "started_at": "2026-09-28T09:40:00Z",
                                "ended_at": "2026-09-28T09:50:00Z",
                                "report": {"commit": COMMIT},
                                "error": None,
                                "events": "/somewhere/round-2.events.jsonl",
                                "stderr": "/somewhere/round-2.stderr.log",
                            },
                        ],
                    }
                ],
            ),
        )
        session = self.tasks / "pi-task.session"
        (session / "pi").mkdir(parents=True)
        (session / "pi" / "2026-09-28T09-31-18_task.jsonl").write_text(
            '{"type":"session"}\n'
        )
        (session / "status.json").write_text('{"state": "idle"}\n')
        (session / "boundary.ts").write_text("// boundary\n")
        for number in (1, 2):
            for name in ("prompt.md", "events.jsonl", "stderr.log", "supervisor.log"):
                (session / f"round-{number}.{name}").write_text(f"{number} {name}\n")
        # A task that failed, never merged, without a merge log.
        self.old(
            "failed-task",
            old_record(
                "failed-task",
                state="failed",
                closed=closed(
                    state="failed", outcome="failed", note="opened by mistake"
                ),
            ),
            merge_log=False,
        )
        # A task opened twice: the history already holds one of that name.
        self.old("again", old_record("again"))
        earlier = trace.Node(
            layout.history_folder(self.concorde) / "again",
            "again",
            "task",
            metadata={"task": "again"},
        )
        earlier.finish("ok", outcome="merged")
        self.earlier = trace.read(earlier.folder)
        # A current task of the new layout, and the old locks.
        current = self.tasks / "current-task"
        current.mkdir()
        (current / "task.json").write_text('{"id": "current-task"}\n')
        (self.tasks / ".lock").write_text("")
        (self.tasks / "merge.lock").write_text("")
        # The old run store.
        runs = self.concorde / "runs"
        for run in ("r-20260928T171700-delivery-0000abcd", "w-20260928T171701-aaaaaa"):
            (runs / run).mkdir(parents=True)
            (runs / run / "result.json").write_text(f'{{"run": "{run}"}}\n')
        (runs / "launch-1.log").write_text("launched\n")
        (runs / "issues.lock").write_text("")
        (runs / "locks").mkdir()
        (runs / "locks" / "adoption.lock").write_text("")
        # What the migration never touches.
        for kept in ("locks/merge.lock", "evidence/adoption/1.json", "issues/i-1.json"):
            (self.concorde / kept).parent.mkdir(parents=True, exist_ok=True)
            # A lock file holds nothing while no process holds it.
            (self.concorde / kept).write_text(
                "" if kept.startswith("locks/") else "kept\n"
            )

    def run_script(self, *arguments: str) -> tuple[int, str]:
        output = io.StringIO()
        with redirect_stdout(output):
            status = migration.main(
                [str(self.root), "--archive", str(self.archive), *arguments]
            )
        return status, output.getvalue()

    def history(self, key: str) -> Path:
        return layout.history_folder(self.concorde) / key

    def test_a_dry_run_prints_every_step_and_changes_nothing(self):
        before = snapshot(self.concorde)
        status, output = self.run_script("--dry-run")
        self.assertEqual(0, status, output)
        self.assertEqual(before, snapshot(self.concorde))
        self.assertFalse(self.archive.exists())
        self.assertIn(f"task adoption (closed) -> {self.history('adoption')}", output)
        self.assertIn(f"task again (closed) -> {self.history('again.2')}", output)
        self.assertIn(
            f"copy {self.tasks / 'adoption.json'} -> legacy/record.json", output
        )
        self.assertIn(
            "write sessions/task-pi-task-20260928T093118/rounds/2/trace.json", output
        )
        self.assertIn(f"remove {self.tasks / 'pi-task.session'}", output)
        self.assertIn(
            f"skip {self.tasks / 'current-task'}: a task folder of the current", output
        )
        self.assertIn(f"archive into {self.archive}:", output)
        self.assertIn(f"  {self.concorde / 'runs/launch-1.log'}", output)
        self.assertIn(f"  {self.tasks / 'merge.lock'}", output)
        self.assertIn("would move 4 old tasks", output)

    def test_old_tasks_move_into_the_history_in_the_tracing_layout(self):
        sources = {
            name: (self.tasks / name).read_bytes()
            for name in ("adoption.json", "adoption.decisions.md", "adoption.merge.log")
        }
        kept = {
            name: (self.concorde / name).read_bytes()
            for name in (
                "locks/merge.lock",
                "evidence/adoption/1.json",
                "issues/i-1.json",
            )
        }
        current = snapshot(self.tasks / "current-task")
        status, output = self.run_script()
        self.assertEqual(0, status, output)

        folder = self.history("adoption")
        self.assertEqual(
            sources["adoption.json"], (folder / "legacy/record.json").read_bytes()
        )
        self.assertEqual(
            sources["adoption.decisions.md"], (folder / "decisions.md").read_bytes()
        )
        self.assertEqual(
            sources["adoption.merge.log"], (folder / "legacy/merge.log").read_bytes()
        )
        self.assertEqual(
            b"{}\n", (folder / "legacy/session/settings.json").read_bytes()
        )
        record = json.loads((folder / "task.json").read_text())
        self.assertEqual(2, record["schema_version"])
        self.assertEqual("adoption", record["closed"]["history"])
        self.assertNotIn("sessions", record)
        node = trace.check(trace.read(folder))
        self.assertEqual(
            ("task", "ok", "merged"), (node["kind"], node["status"], node["outcome"])
        )
        self.assertEqual("2026-09-28T17:24:52Z", node["ended_at"])
        self.assertEqual(
            {
                "record",
                "decision-log",
                "legacy-record",
                "legacy-merge-log",
                "legacy-session:settings.json",
                "legacy-session:write_hook.py",
            },
            {item["id"] for item in node["artifacts"]},
        )
        for item in node["artifacts"]:
            self.assertEqual(trace.digest(folder / item["path"]), item["digest"])
        self.assertIn(
            {
                "relation": "bundle",
                "target": "8c749d065b7ad3063e6d9899bdc587506dc86f79:"
                ".concorde/evidence/adoption/1.json",
            },
            node["references"],
        )
        data = node["content"]["data"]
        self.assertEqual(
            ["open", "closed"], [item["state"] for item in data["transitions"]]
        )
        self.assertEqual("task-session", data["escalations"][0]["by"])

        shown = store.show_task(self.root, "adoption")
        self.assertEqual(folder.as_posix(), shown["folder"])
        self.assertEqual("closed", shown["record"]["state"])
        self.assertEqual(["f335fd1a"], [item["id"] for item in shown["sessions"]])
        self.assertEqual(1, shown["escalations"][0]["number"])

        pi = self.history("pi-task") / "sessions/task-pi-task-20260928T093118"
        self.assertEqual(b'{"state": "idle"}\n', (pi / "status.json").read_bytes())
        self.assertTrue((pi / "pi/2026-09-28T09-31-18_task.jsonl").is_file())
        self.assertEqual(
            b"2 events.jsonl\n", (pi / "rounds/2/events.jsonl").read_bytes()
        )
        self.assertTrue(
            (self.history("pi-task") / "legacy/session/boundary.ts").is_file()
        )
        rounds = store.show_task(self.root, "pi-task")["sessions"][0]["rounds"]
        self.assertEqual(
            ["escalated", "delivered"], [item["status"] for item in rounds]
        )
        self.assertEqual("do it", rounds[1]["answer"])
        self.assertEqual(
            {"level": "task-session", "code": "decision"}, rounds[0]["error"]
        )

        failed = trace.read(self.history("failed-task"))
        self.assertEqual(("failed", "failed"), (failed["status"], failed["outcome"]))
        self.assertEqual(
            "failed", store.show_task(self.root, "failed-task")["record"]["state"]
        )
        self.assertEqual(self.earlier, trace.read(self.history("again")))
        self.assertEqual(
            "again.2",
            trace.read(self.history("again.2"))["content"]["data"]["closing"][
                "history"
            ],
        )

        listed = reader.listing(self.concorde, history=True)
        self.assertEqual(
            ["adoption", "again", "again", "failed-task", "pi-task"],
            sorted(item["id"] for item in listed if item["kind"] == "task"),
        )
        self.assertEqual(["current-task"], [item.name for item in self.tasks.iterdir()])
        self.assertEqual(current, snapshot(self.tasks / "current-task"))
        for name, data in kept.items():
            self.assertEqual(data, (self.concorde / name).read_bytes())
        self.assertFalse(
            list(layout.history_folder(self.concorde).glob(".migrating-*"))
        )

    def test_the_run_store_is_archived_verified_and_then_removed(self):
        runs = snapshot(self.concorde / "runs")
        status, output = self.run_script()
        self.assertEqual(0, status, output)
        self.assertIn("tar --compare found no difference", output)
        self.assertFalse((self.concorde / "runs").exists())
        self.assertFalse((self.tasks / ".lock").exists())
        self.assertFalse((self.tasks / "merge.lock").exists())
        extracted = Path(self.temporary.name) / "extracted"
        extracted.mkdir()
        subprocess.run(
            ["tar", "--zstd", "-xf", str(self.archive), "-C", str(extracted)],
            check=True,
        )
        self.assertEqual(runs, snapshot(extracted / "runs"))
        self.assertTrue((extracted / "tasks/merge.lock").is_file())

    def test_a_gzip_archive_and_a_second_run_that_finds_nothing(self):
        self.archive = Path(self.temporary.name) / "old-records.tar.gz"
        self.assertEqual(0, self.run_script()[0])
        subprocess.run(
            ["tar", "--gzip", "-tf", str(self.archive)], check=True, capture_output=True
        )
        history = snapshot(layout.history_folder(self.concorde))
        self.archive = Path(self.temporary.name) / "second.tar.gz"
        status, output = self.run_script()
        self.assertEqual(0, status, output)
        self.assertIn(
            "moved 0 old tasks, finished 0, skipped 1 entries, archived 0", output
        )
        self.assertEqual(history, snapshot(layout.history_folder(self.concorde)))
        self.assertFalse(self.archive.exists())

    def test_a_held_lock_of_the_run_store_refuses_before_anything_moves(self):
        before = snapshot(self.concorde)
        with locks.hold(self.concorde / "runs/locks/adoption.lock", "an old run"):
            status, output = self.run_script()
        self.assertEqual(1, status)
        error = json.loads(output)["error"]
        self.assertEqual("lock_held", error["code"])
        self.assertIn("runs/locks/adoption.lock", error["detail"])
        self.assertEqual(before, snapshot(self.concorde))

    def test_an_archive_is_never_overwritten_nor_kept_in_the_repository(self):
        self.archive.write_text("earlier")
        self.assertEqual(
            "archive_exists", json.loads(self.run_script()[1])["error"]["code"]
        )
        self.archive = self.root / "old.tar.zst"
        self.assertEqual(
            "archive_inside", json.loads(self.run_script()[1])["error"]["code"]
        )
        self.archive = Path(self.temporary.name) / "old.zip"
        self.assertEqual(
            "archive_format", json.loads(self.run_script()[1])["error"]["code"]
        )
        self.assertTrue((self.tasks / "adoption.json").is_file())

    def test_an_interrupted_run_is_finished_without_a_second_history_folder(self):
        backup = Path(self.temporary.name) / "backup"
        shutil.copytree(self.tasks, backup)
        self.assertEqual(0, self.run_script()[0])
        # As if the run had stopped after moving the folders, before removing the old files.
        for name in ("adoption.json", "adoption.decisions.md", "adoption.merge.log"):
            shutil.copy2(backup / name, self.tasks / name)
        shutil.copytree(backup / "adoption.session", self.tasks / "adoption.session")
        staging = layout.history_folder(self.concorde) / ".migrating-stale"
        staging.mkdir()
        self.archive = Path(self.temporary.name) / "second.tar.zst"
        status, output = self.run_script()
        self.assertEqual(0, status, output)
        self.assertIn(
            f"already in history {self.history('adoption')}: adoption", output
        )
        self.assertFalse((self.tasks / "adoption.json").exists())
        self.assertFalse((self.tasks / "adoption.session").exists())
        self.assertFalse(self.history("adoption.2").exists())

    def test_a_record_that_fits_no_current_format_keeps_the_old_file_and_a_minimal_node(
        self,
    ):
        record = old_record(
            "odd",
            modules=[],
            closed=closed(outcome="abandoned"),
            created_at="2026-09-20T10:00:00Z",
        )
        self.old("odd", record)
        status, output = self.run_script("--dry-run")
        self.assertIn(
            "note the old record does not fit the current task record", output
        )
        self.assertIn(
            "note old task odd gets a minimal node pointing to legacy/", output
        )
        self.assertEqual(0, self.run_script()[0])
        folder = self.history("odd")
        self.assertFalse((folder / "task.json").exists())
        self.assertEqual(
            record, json.loads((folder / "legacy/record.json").read_text())
        )
        node = trace.read(folder)
        self.assertEqual(("abandoned", None), (node["outcome"], node["content"]))
        self.assertIn("legacy-record", {item["id"] for item in node["artifacts"]})
        self.assertIn(
            "odd", {item["id"] for item in reader.listing(self.concorde, history=True)}
        )

    def test_a_task_that_has_not_ended_is_left_where_it_is(self):
        self.old("running", old_record("running", state="open", closed=None))
        status, output = self.run_script()
        self.assertEqual(0, status, output)
        self.assertIn("task running has not ended (state open)", output)
        self.assertTrue((self.tasks / "running.json").is_file())
        self.assertTrue((self.tasks / "running.decisions.md").is_file())
        self.assertFalse(self.history("running").exists())


if __name__ == "__main__":
    unittest.main()
