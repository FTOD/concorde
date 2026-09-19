"""Primary persistence and migration tested only in disposable Git repositories."""

import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from concorde.harness.change_worktree import (
    ensure_change,
    git,
    read_change,
    save_change,
)
from concorde.harness.status_store import (
    all_status,
    migrate_legacy,
    primary_root,
    read_status,
    record_manual_merge,
    run_path,
    status_path,
    write_run,
)
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies


class StatusStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.primary = Path(self.temp.name) / "not-named-primary"
        self.primary.mkdir()
        git(self.primary, "init", "-q", "-b", "trunk")
        git(self.primary, "config", "user.name", "Test")
        git(self.primary, "config", "user.email", "test@example.invalid")
        (self.primary / "file").write_text("base")
        git(self.primary, "add", ".")
        git(self.primary, "commit", "-qm", "base")
        self.candidate = Path(self.temp.name) / "candidate"
        git(self.primary, "worktree", "add", "-b", "task", str(self.candidate))

    @verifies("scenario.harness.primary-status")
    def test_status_and_runs_are_only_primary_and_identity_survives_rename(self):
        state = ensure_change(self.candidate, task={"task": "work"})
        self.assertEqual(self.primary, primary_root(self.candidate))
        self.assertFalse((self.candidate / ".concorde/status").exists())
        self.assertFalse((self.candidate / ".concorde/worktree.json").exists())
        git(self.candidate, "branch", "-m", "renamed")
        observed = read_change(self.candidate, required=True)
        observed["phase"] = "checked"
        save_change(self.candidate, observed)
        self.assertEqual(
            "renamed", read_status(self.primary, state["change_id"])["branch"]
        )
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(
                executor.map(
                    lambda i: write_run(
                        self.candidate,
                        f".concorde/runs/run-{i}/result.json",
                        str(i).encode(),
                    ),
                    range(12),
                )
            )
        self.assertFalse((self.candidate / ".concorde/runs").exists())
        self.assertEqual(
            b"11",
            run_path(self.candidate, ".concorde/runs/run-11/result.json").read_bytes(),
        )
        observed = read_change(self.candidate, required=True)
        observed.update(status="delivered", outcome="delivered", phase="complete")
        save_change(self.candidate, observed)
        git(self.primary, "worktree", "remove", "--force", str(self.candidate))
        self.assertEqual(
            "delivered", read_status(self.primary, state["change_id"])["outcome"]
        )
        self.assertEqual(1, len(all_status(self.primary)))
        self.assertEqual("", git(self.primary, "status", "--porcelain").stdout)

    @verifies("scenario.harness.primary-status")
    def test_unavailable_primary_never_falls_back_to_candidate(self):
        moved = self.primary.with_name("temporarily-unavailable")
        self.primary.rename(moved)
        try:
            with self.assertRaises(SpecError) as error:
                write_run(self.candidate, ".concorde/runs/run/result", b"x")
            self.assertEqual("primary_unavailable", error.exception.code)
            self.assertFalse((self.candidate / ".concorde/runs").exists())
        finally:
            moved.rename(self.primary)

    def legacy(self):
        state = ensure_change(self.candidate, task={"task": "work"})
        (self.primary / status_path(state["change_id"])).unlink()
        old = self.candidate / ".concorde/worktree.json"
        old.parent.mkdir(parents=True, exist_ok=True)
        old.write_text(json.dumps(state))
        run = self.candidate / ".concorde/runs/old-run/result"
        run.parent.mkdir(parents=True)
        run.write_bytes(b"legacy bytes")
        return state, old, run

    @verifies("scenario.harness.status-migration")
    def test_migration_is_explicit_preserves_history_and_retries(self):
        state, old, run = self.legacy()
        before = old.read_bytes()
        with self.assertRaises(SpecError) as error:
            read_change(self.candidate)
        self.assertEqual("migration_required", error.exception.code)
        self.assertEqual("planned", migrate_legacy(self.primary)["status"])
        self.assertEqual(before, old.read_bytes())
        migrate_legacy(self.primary, apply=True)
        archives = list(
            (self.primary / ".concorde/runs/legacy-migration").glob("*/worktree.json")
        )
        self.assertEqual([before], [path.read_bytes() for path in archives])
        self.assertFalse(old.exists())
        self.assertFalse(run.exists())
        self.assertEqual(
            b"legacy bytes",
            run_path(self.primary, ".concorde/runs/old-run/result").read_bytes(),
        )
        current = read_change(self.candidate, required=True)
        self.assertEqual(state["change_id"], current["change_id"])
        self.assertEqual("blocked", current["status"])
        self.assertIsNone(current["validated_tree"])
        self.assertEqual([], migrate_legacy(self.primary, apply=True)["targets"])

    @verifies("scenario.harness.status-migration")
    def test_run_collision_changes_nothing(self):
        state, old, run = self.legacy()
        write_run(self.primary, ".concorde/runs/old-run/result", b"other")
        with self.assertRaises(SpecError):
            migrate_legacy(self.primary, apply=True)
        self.assertTrue(old.exists())
        self.assertTrue(run.exists())
        self.assertFalse((self.primary / status_path(state["change_id"])).exists())

    @verifies("scenario.harness.status-migration")
    def test_interrupted_archive_resumes_journal_without_divergent_copies(self):
        state, old, run = self.legacy()
        unlink = Path.unlink
        failed = False

        def interrupted(path, *args, **kwargs):
            nonlocal failed
            if path == run and not failed:
                failed = True
                raise OSError("interrupted")
            return unlink(path, *args, **kwargs)

        with patch.object(Path, "unlink", interrupted), self.assertRaises(OSError):
            migrate_legacy(self.primary, apply=True)
        self.assertFalse(old.exists())
        self.assertTrue(run.exists())
        self.assertEqual(
            "completed", migrate_legacy(self.primary, apply=True)["status"]
        )
        self.assertFalse(run.exists())
        self.assertEqual(
            state["change_id"], read_change(self.candidate, required=True)["change_id"]
        )

    @verifies("scenario.harness.primary-status")
    def test_direct_primary_task_and_manual_merge_keep_cleanup_separate(self):
        direct = ensure_change(
            self.primary, task={"task": "simple"}, allow_primary=True
        )
        self.assertEqual(str(self.primary), direct["path"])
        state = ensure_change(self.candidate, task={"task": "maintenance"})
        result = record_manual_merge(
            self.primary, state["change_id"], commit="HEAD", cleanup="pending"
        )
        self.assertEqual("merged", result["outcome"])
        self.assertEqual("pending", result["cleanup"]["status"])
        self.assertIsNone(result["delivery"])
        self.assertTrue(self.candidate.exists())

    @verifies("scenario.harness.primary-status")
    def test_one_child_owner_and_stable_id_collision_are_enforced(self):
        from concorde.harness.status_store import coordinate_child

        state = ensure_change(
            self.candidate, task={"task": "maintenance"}, mode="maintenance"
        )
        self.assertFalse((self.candidate / "AGENTS.md").exists())
        coordinate_child(
            self.primary, state["change_id"], child_id="writer", phase="maintenance"
        )
        with self.assertRaises(SpecError):
            coordinate_child(
                self.primary, state["change_id"], child_id="tester", phase="test"
            )
        coordinate_child(
            self.primary,
            state["change_id"],
            child_id="writer",
            phase="maintenance",
            release=True,
        )
        owned = coordinate_child(
            self.primary, state["change_id"], child_id="tester", phase="test"
        )
        self.assertEqual("tester", owned["child"]["id"])
        with self.assertRaises(SpecError):
            ensure_change(
                self.primary, allow_primary=True, change_id=state["change_id"]
            )

    @verifies("scenario.harness.status-migration")
    def test_interrupted_migration_refuses_changed_source(self):
        state, old, run = self.legacy()
        from concorde.harness import status_store

        write = status_store.atomic_write

        def interrupted(root, relative, data):
            if relative.endswith("/result"):
                raise OSError("interrupted")
            return write(root, relative, data)

        with (
            patch.object(status_store, "atomic_write", interrupted),
            self.assertRaises(OSError),
        ):
            migrate_legacy(self.primary, apply=True)
        run.write_bytes(b"new source bytes")
        with self.assertRaises(SpecError):
            migrate_legacy(self.primary, apply=True)
        self.assertEqual(b"new source bytes", run.read_bytes())
        self.assertTrue(old.exists())

    @verifies("scenario.harness.primary-status")
    def test_actual_harness_depth_is_not_reset_by_worker_terminology(self):
        from concorde.harness.pi_worker import (
            bounded_subagent_config,
            WorkerExecutionError,
        )

        self.assertEqual(
            0,
            bounded_subagent_config(
                {"CONCORDE_HARNESS_DEPTH": "1", "CONCORDE_HARNESS_MAX_DEPTH": "2"}
            )["maxSubagentDepth"],
        )
        with self.assertRaises(WorkerExecutionError):
            bounded_subagent_config(
                {"CONCORDE_HARNESS_DEPTH": "1", "CONCORDE_HARNESS_MAX_DEPTH": "1"}
            )
        with self.assertRaises(WorkerExecutionError):
            bounded_subagent_config({"PI_SUBAGENT_MAX_DEPTH": "2"})

    @verifies("scenario.harness.primary-status")
    def test_manual_merge_cannot_be_invented_after_unrecorded_cleanup(self):
        state = ensure_change(
            self.candidate, task={"task": "maintenance"}, mode="maintenance"
        )
        git(self.primary, "worktree", "remove", "--force", str(self.candidate))
        with self.assertRaises(SpecError):
            record_manual_merge(
                self.primary, state["change_id"], commit="HEAD", cleanup="removed"
            )
        self.assertIsNone(read_status(self.primary, state["change_id"])["manual_merge"])

    @verifies("scenario.harness.primary-status")
    def test_terminal_direct_tasks_do_not_claim_subsequent_primary_tasks(self):
        first = ensure_change(
            self.primary, task={"task": "first"}, allow_primary=True, mode="direct"
        )
        self.assertIsNone(first["candidate_worktree"])
        self.assertEqual("not_needed", first["cleanup"]["status"])
        record_manual_merge(
            self.primary, first["change_id"], commit="HEAD", cleanup="retained"
        )
        second = ensure_change(
            self.primary, task={"task": "second"}, allow_primary=True, mode="direct"
        )
        self.assertNotEqual(first["change_id"], second["change_id"])
        self.assertEqual(2, len(all_status(self.primary)))

    @verifies("scenario.harness.status-migration")
    def test_candidate_legacy_runs_require_migration_before_new_persistence(self):
        old = self.candidate / ".concorde/runs/old/result"
        old.parent.mkdir(parents=True)
        old.write_bytes(b"original")
        with self.assertRaises(SpecError) as error:
            write_run(self.candidate, ".concorde/runs/new/result", b"new")
        self.assertEqual("migration_required", error.exception.code)
        migrate_legacy(self.primary, apply=True)
        self.assertFalse(old.exists())
        write_run(self.candidate, ".concorde/runs/new/result", b"new")
        journal = json.loads(
            (self.primary / ".concorde/status/migration.json").read_text()
        )
        self.assertNotIn("payloads", journal)

    @verifies("scenario.harness.primary-status")
    def test_runtime_writes_do_not_replace_tracked_project_files(self):
        tracked = self.primary / ".concorde/runs/tracked/result"
        tracked.parent.mkdir(parents=True)
        tracked.write_bytes(b"project owned")
        git(self.primary, "add", ".")
        git(self.primary, "commit", "-qm", "historical tracked control")
        with self.assertRaises(SpecError):
            write_run(self.candidate, ".concorde/runs/tracked/result", b"replace")
        self.assertEqual(b"project owned", tracked.read_bytes())

    @verifies("scenario.harness.primary-status")
    def test_run_artifacts_survive_candidate_deletion(self):
        from concorde.harness.host import OperationHost
        from concorde.harness.status_store import record_run
        from concorde.spec.typed_data import artifact

        state = ensure_change(self.candidate, task={"task": "work"})
        host = OperationHost(self.candidate, self.candidate, archive_root=self.primary)
        record_run(host, operation="test")
        scratch = self.candidate / ".concorde/work/plan.md"
        scratch.parent.mkdir(parents=True)
        scratch.write_bytes(b"accepted plan")
        ref = artifact(self.candidate, "plan", ".concorde/work/plan.md")
        record_run(
            host, operation="test", result={"status": "succeeded", "artifacts": [ref]}
        )
        git(self.primary, "worktree", "remove", "--force", str(self.candidate))
        record = json.loads(
            run_path(
                self.primary, f".concorde/runs/{host.invocation_id}/run.json"
            ).read_text()
        )
        self.assertEqual("archived", record["artifacts"][0]["status"])
        self.assertEqual(
            b"accepted plan",
            run_path(self.primary, record["artifacts"][0]["archive"]).read_bytes(),
        )
        self.assertFalse(self.candidate.exists())
