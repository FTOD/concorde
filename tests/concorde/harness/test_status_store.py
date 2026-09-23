"""Primary persistence tested only in disposable Git repositories."""

import copy
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from concorde.harness.change_worktree import (
    ensure_change,
    git,
    progress,
    read_change,
    refresh_registry,
    save_change,
    save_target_state,
    target_state,
)
from concorde.harness.status_store import (
    all_status,
    primary_root,
    read_status,
    record_manual_merge,
    run_path,
    status_path,
    write_run,
    write_status,
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

    @verifies("scenario.harness.primary-status")
    def test_late_write_never_recreates_missing_source(self):
        from concorde.harness.host import OperationHost
        from concorde.harness.status_store import record_run

        ensure_change(self.candidate, task={"task": "work"}, mode="maintenance")
        host = OperationHost(self.candidate, self.candidate, archive_root=self.primary)
        record_run(host, operation="test")
        git(self.primary, "worktree", "remove", "--force", str(self.candidate))
        with self.assertRaises(SpecError) as error:
            write_run(self.candidate, ".concorde/runs/late/result", b"late")
        self.assertEqual("primary_unavailable", error.exception.code)
        record_run(host, operation="test", result={"status": "succeeded"})
        self.assertFalse(self.candidate.exists())
        self.assertEqual(
            "succeeded",
            json.loads(
                run_path(
                    self.primary, f".concorde/runs/{host.invocation_id}/run.json"
                ).read_text()
            )["status"],
        )
        missing = Path(self.temp.name) / "never-existed"
        with self.assertRaises(SpecError):
            write_run(missing, ".concorde/runs/late/result", b"late")
        self.assertFalse(missing.exists())
        unversioned = Path(self.temp.name) / "unversioned"
        unversioned.mkdir()
        write_run(unversioned, ".concorde/runs/run/result", b"supported")
        self.assertEqual(
            b"supported",
            run_path(unversioned, ".concorde/runs/run/result").read_bytes(),
        )

    @verifies("scenario.harness.primary-status")
    def test_explicit_id_registration_race_has_one_winner(self):
        from concorde.harness import change_worktree

        other = self.candidate.with_name("other")
        git(self.primary, "worktree", "add", "-b", "other", str(other))
        barrier = threading.Barrier(2)
        local = threading.local()
        original = change_worktree.repository_lock

        @contextmanager
        def synchronized(root):
            # Synchronize BEFORE the first acquisition, not inside read_status:
            # moving the uniqueness read into the lock must never deadlock the test.
            if not getattr(local, "entered", False):
                local.entered = True
                barrier.wait(timeout=10)
            with original(root):
                yield

        def register(root):
            try:
                return ensure_change(
                    root,
                    task={"task": root.name},
                    change_id="change.shared",
                    mode="maintenance",
                )
            except SpecError as error:
                return error.code

        with patch.object(change_worktree, "repository_lock", synchronized):
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(register, [self.candidate, other]))
        winners = [result for result in results if isinstance(result, dict)]
        self.assertEqual(1, len(winners), results)
        self.assertIn("workspace_mismatch", results)
        self.assertEqual(winners, all_status(self.primary))
        with self.assertRaises(SpecError):
            write_status(self.primary, winners[0], create=True)
        self.assertEqual(winners, all_status(self.primary))

    @verifies("scenario.harness.primary-status", "scenario.harness.workspace-inventory")
    def test_recreated_worktree_never_inherits_old_incarnation(self):
        for same_branch in (True, False):
            with self.subTest(same_branch=same_branch):
                state = ensure_change(
                    self.candidate, task={"task": "old"}, mode="maintenance"
                )
                old_id = state["git_worktree_id"]
                old_head = git(self.candidate, "rev-parse", "HEAD").stdout
                git(self.primary, "worktree", "remove", "--force", str(self.candidate))
                args = ("task",) if same_branch else ("-b", "new-task")
                git(self.primary, "worktree", "add", str(self.candidate), *args)
                self.assertEqual(
                    old_head, git(self.candidate, "rev-parse", "HEAD").stdout
                )
                self.assertIsNone(read_change(self.candidate))
                summary = refresh_registry(self.primary)["worktrees"][0]
                self.assertFalse(summary["managed"])
                self.assertIsNone(summary["change_id"])
                with self.assertRaises(SpecError):
                    save_change(self.candidate, state)
                fresh = ensure_change(
                    self.candidate, task={"task": "new"}, mode="maintenance"
                )
                self.assertNotEqual(old_id, fresh["git_worktree_id"])
                self.assertNotEqual(state["change_id"], fresh["change_id"])
                self.assertEqual(state, read_status(self.primary, state["change_id"]))
                summary = refresh_registry(self.primary)["worktrees"][0]
                self.assertEqual(fresh["change_id"], summary["change_id"])
                git(self.primary, "worktree", "remove", "--force", str(self.candidate))
                git(self.primary, "worktree", "add", str(self.candidate), "task")

    @verifies("scenario.harness.primary-status")
    def test_stale_replacements_reject_all_fields_not_a_preservation_allowlist(self):
        state = ensure_change(self.candidate, task={"task": "work"}, mode="maintenance")
        before = (self.primary / status_path(state["change_id"])).read_bytes()
        save_change(self.candidate, state)
        self.assertEqual(
            before, (self.primary / status_path(state["change_id"])).read_bytes()
        )
        stale = copy.deepcopy(state)
        state.update(
            status="blocked",
            phase="review",
            blockers=[{"reason": "blocked"}],
            validation={"checks": ["new"]},
            validated_tree="new-tree",
        )
        save_change(self.candidate, state)
        stale.update(phase="implementation")
        for save in (save_change, write_status):
            with self.assertRaises(SpecError) as error:
                save(self.candidate, stale)
            self.assertEqual("stale_status", error.exception.code)
            self.assertEqual(state, read_status(self.primary, state["change_id"]))
        progress(self.candidate, phase="waiting")
        current = read_change(self.candidate, required=True)
        self.assertEqual("blocked", current["status"])
        self.assertEqual(state["blockers"], current["blockers"])
        self.assertEqual(state["validation"], current["validation"])
        self.assertEqual("waiting", current["phase"])

    @verifies("scenario.harness.primary-status")
    def test_target_cas_preserves_independent_updates_and_rejects_stale_validation(
        self,
    ):
        state = ensure_change(self.candidate, task={"task": "work"}, mode="maintenance")
        state["target_id"] = "module.example"
        save_change(self.candidate, state)
        target = target_state(self.candidate, "module.example", None, create=True)
        save_target_state(self.candidate, target)
        stale = copy.deepcopy(target)
        # A whole-status caller must advance target revisions as well.
        state = read_change(self.candidate, required=True)
        state["targets"]["module.example"].update(checks=["new validation"])
        save_change(self.candidate, state)
        stale["phase"] = "implementation"
        with self.assertRaises(SpecError) as error:
            save_target_state(self.candidate, stale)
        self.assertEqual("stale_status", error.exception.code)
        first = target_state(self.candidate, "module.example", None)
        other = target_state(self.candidate, "module.other", None, create=True)
        other["plan"] = "independent"
        save_target_state(self.candidate, other)
        progress(self.candidate, status="blocked", blockers=[{"reason": "new blocker"}])
        first["phase"] = "review"
        save_target_state(self.candidate, first)
        # Same in-memory target can save again after a successful update.
        first["phase"] = "complete"
        save_target_state(self.candidate, first)
        result = read_change(self.candidate, required=True)
        self.assertEqual(
            ["new validation"], result["targets"]["module.example"]["checks"]
        )
        self.assertEqual("independent", result["targets"]["module.other"]["plan"])
        self.assertEqual("blocked", result["status"])
        self.assertEqual([{"reason": "new blocker"}], result["blockers"])

    @verifies("scenario.harness.primary-status")
    def test_target_snapshot_rejects_recreated_incarnation_with_equal_revision(self):
        from concorde.spec.contract_shapes import CHECK_RESULT
        from concorde.spec.repository import digest
        from concorde.spec.typed_data import check_schema

        def target(task, status):
            state = ensure_change(
                self.candidate, task={"task": task}, mode="maintenance"
            )
            state["target_id"] = "module.example"
            save_change(self.candidate, state)
            value = target_state(self.candidate, "module.example", None, create=True)
            # Schema-conforming disposable records, not claimed check execution.
            check = {
                "check_id": "check.fixture",
                "target_id": "module.example",
                "status": status,
                "exit_code": 0 if status == "passed" else 1,
                "source_digest": digest(b"fixture"),
                "log_digest": digest(status.encode()),
            }
            check_schema(check, CHECK_RESULT)
            value.update(task=task, plan=task, checks=[check])
            save_target_state(self.candidate, value)
            return state, value

        old, stale = target("unfinished old task", "passed")
        old_bytes = (self.primary / status_path(old["change_id"])).read_bytes()
        head = git(self.candidate, "rev-parse", "HEAD").stdout
        git(self.primary, "worktree", "remove", "--force", str(self.candidate))
        git(self.primary, "worktree", "add", str(self.candidate), "task")
        new, fresh = target("unrelated new task", "failed")
        self.assertEqual(head, git(self.candidate, "rev-parse", "HEAD").stdout)
        self.assertEqual(stale["revision"], fresh["revision"])
        self.assertNotEqual(stale["owner"], fresh["owner"])
        before = (self.primary / status_path(new["change_id"])).read_bytes()
        stale["phase"] = "implementation"
        with self.assertRaises(SpecError) as error:
            save_target_state(self.candidate, stale)
        self.assertEqual("workspace_mismatch", error.exception.code)
        # Whole-status saves must not provide a second laundering entry point.
        current = read_change(self.candidate, required=True)
        current["targets"]["module.example"] = stale
        for writer in (save_change, write_status):
            with self.assertRaises(SpecError):
                writer(self.candidate, current)
        self.assertEqual(
            before, (self.primary / status_path(new["change_id"])).read_bytes()
        )
        self.assertEqual(
            old_bytes, (self.primary / status_path(old["change_id"])).read_bytes()
        )

    @verifies("scenario.harness.primary-status")
    def test_target_ownership_is_required_and_not_just_incarnation(self):
        first = ensure_change(
            self.primary, task={"task": "first"}, allow_primary=True, mode="direct"
        )
        first["target_id"] = "module.example"
        save_change(self.primary, first)
        stale = target_state(self.primary, "module.example", None, create=True)
        save_target_state(self.primary, stale)
        record_manual_merge(
            self.primary, first["change_id"], commit="HEAD", cleanup="retained"
        )
        second = ensure_change(
            self.primary, task={"task": "second"}, allow_primary=True, mode="direct"
        )
        second["target_id"] = "module.example"
        save_change(self.primary, second)
        fresh = target_state(self.primary, "module.example", None, create=True)
        save_target_state(self.primary, fresh)
        self.assertEqual(stale["revision"], fresh["revision"])
        self.assertEqual(
            stale["owner"]["git_worktree_id"], fresh["owner"]["git_worktree_id"]
        )
        before = (self.primary / status_path(second["change_id"])).read_bytes()
        for bad in (
            stale,
            {k: v for k, v in fresh.items() if k != "owner"},
            {**fresh, "owner": {**fresh["owner"], "git_worktree_id": "stale"}},
        ):
            with self.assertRaises(SpecError):
                save_target_state(self.primary, bad)
        self.assertEqual(
            before, (self.primary / status_path(second["change_id"])).read_bytes()
        )
        # Loading an unbound on-disk target refuses it, never adds current ownership.
        saved = read_change(self.primary, required=True)
        saved["targets"]["module.example"].pop("owner")
        path = self.primary / status_path(second["change_id"])
        path.write_text(json.dumps(saved))
        unbound = path.read_bytes()
        with self.assertRaises(SpecError):
            target_state(self.primary, "module.example", None)
        self.assertEqual(unbound, path.read_bytes())

    @verifies("scenario.harness.primary-status")
    def test_unsaved_target_cannot_be_adopted_by_another_task(self):
        old = ensure_change(self.candidate, task={"task": "old"}, mode="maintenance")
        old["target_id"] = "module.example"
        save_change(self.candidate, old)
        stale = target_state(self.candidate, "module.example", None, create=True)
        git(self.primary, "worktree", "remove", "--force", str(self.candidate))
        git(self.primary, "worktree", "add", str(self.candidate), "task")
        new = ensure_change(self.candidate, task={"task": "new"}, mode="maintenance")
        new["target_id"] = "module.example"
        save_change(self.candidate, new)
        before = (self.primary / status_path(new["change_id"])).read_bytes()
        with self.assertRaises(SpecError):
            save_target_state(self.candidate, stale)
        self.assertEqual(
            before, (self.primary / status_path(new["change_id"])).read_bytes()
        )
        self.assertEqual({}, read_change(self.candidate)["targets"])

    @verifies("scenario.harness.primary-status")
    def test_new_unsaved_target_keeps_binding_through_rename_and_noop(self):
        state = ensure_change(self.candidate, task={"task": "work"}, mode="maintenance")
        state["target_id"] = "module.example"
        save_change(self.candidate, state)
        value = target_state(self.candidate, "module.example", None, create=True)
        owner = copy.deepcopy(value["owner"])
        git(self.candidate, "branch", "-m", "renamed")
        save_target_state(self.candidate, value)
        before = (self.primary / status_path(state["change_id"])).read_bytes()
        save_target_state(self.candidate, value)
        self.assertEqual(
            before, (self.primary / status_path(state["change_id"])).read_bytes()
        )
        self.assertEqual(owner, value["owner"])
        self.assertEqual("renamed", read_change(self.candidate)["branch"])

    @verifies("scenario.harness.primary-status")
    def test_manual_merge_refuses_replacement_even_with_prior_evidence(self):
        for recorded in (False, True):
            with self.subTest(recorded=recorded):
                old = ensure_change(
                    self.candidate, task={"task": "old"}, mode="maintenance"
                )
                if recorded:
                    record_manual_merge(
                        self.primary,
                        old["change_id"],
                        commit="HEAD",
                        cleanup="retained",
                    )
                else:
                    (self.candidate / "file").write_text("unfinished old work")
                old_bytes = (self.primary / status_path(old["change_id"])).read_bytes()
                git(self.primary, "worktree", "remove", "--force", str(self.candidate))
                git(self.primary, "worktree", "add", str(self.candidate), "task")
                # Both unmanaged and newly registered replacement paths must refuse.
                for registered in (False, True):
                    if registered:
                        new = ensure_change(
                            self.candidate, task={"task": "new"}, mode="maintenance"
                        )
                    with self.assertRaises(SpecError):
                        record_manual_merge(
                            self.primary,
                            old["change_id"],
                            commit="HEAD",
                            cleanup="retained",
                        )
                    self.assertEqual(
                        old_bytes,
                        (self.primary / status_path(old["change_id"])).read_bytes(),
                    )
                self.assertEqual(new, read_change(self.candidate))
                git(self.primary, "worktree", "remove", "--force", str(self.candidate))
                git(self.primary, "worktree", "add", str(self.candidate), "task")

    @verifies("scenario.harness.primary-status")
    def test_manual_merge_rename_and_absent_source_retry(self):
        state = ensure_change(self.candidate, task={"task": "work"}, mode="maintenance")
        git(self.candidate, "branch", "-m", "renamed")
        recorded = record_manual_merge(
            self.primary, state["change_id"], commit="HEAD", cleanup="retained"
        )
        git(self.primary, "worktree", "remove", "--force", str(self.candidate))
        retried = record_manual_merge(
            self.primary, state["change_id"], commit="HEAD", cleanup="removed"
        )
        self.assertEqual(recorded["manual_merge"], retried["manual_merge"])
        self.assertEqual("removed", retried["cleanup"]["status"])
        self.assertFalse(self.candidate.exists())

    @verifies("scenario.harness.primary-status")
    def test_cleanup_only_update_reuses_recorded_merge_or_is_rejected(self):
        state = ensure_change(self.candidate, task={"task": "work"}, mode="maintenance")
        with self.assertRaises(SpecError) as unrecorded:
            record_manual_merge(
                self.primary, state["change_id"], commit=None, cleanup="retained"
            )
        self.assertEqual("stale_evidence", unrecorded.exception.code)
        untouched = read_status(self.primary, state["change_id"]) or {}
        self.assertIsNone(untouched["manual_merge"])
        recorded = record_manual_merge(
            self.primary, state["change_id"], commit="HEAD", cleanup="pending"
        )
        with self.assertRaises(SpecError):  # candidate still present
            record_manual_merge(
                self.primary, state["change_id"], commit=None, cleanup="removed"
            )
        present = read_status(self.primary, state["change_id"]) or {}
        self.assertEqual("pending", present["cleanup"]["status"])
        git(self.primary, "worktree", "remove", "--force", str(self.candidate))
        updated = record_manual_merge(
            self.primary, state["change_id"], commit=None, cleanup="removed"
        )
        self.assertEqual(recorded["manual_merge"], updated["manual_merge"])
        self.assertEqual("removed", updated["cleanup"]["status"])
        self.assertEqual(updated, read_status(self.primary, state["change_id"]))

    @verifies("scenario.harness.primary-status")
    def test_manual_merge_refuses_other_task_in_same_primary_incarnation(self):
        first = ensure_change(
            self.primary, task={"task": "first"}, allow_primary=True, mode="direct"
        )
        record_manual_merge(
            self.primary, first["change_id"], commit="HEAD", cleanup="retained"
        )
        second = ensure_change(
            self.primary, task={"task": "second"}, allow_primary=True, mode="direct"
        )
        self.assertEqual(first["git_worktree_id"], second["git_worktree_id"])
        before = (self.primary / status_path(first["change_id"])).read_bytes()
        with self.assertRaises(SpecError):
            record_manual_merge(
                self.primary, first["change_id"], commit="HEAD", cleanup="retained"
            )
        self.assertEqual(
            before, (self.primary / status_path(first["change_id"])).read_bytes()
        )
        self.assertEqual(second, read_change(self.primary))

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

    @verifies("scenario.harness.primary-status", "scenario.harness.worktree-relay")
    def test_source_primary_cannot_relay_a_mutation_by_change_id(self):
        from concorde.harness.host import OperationHost
        from concorde.harness.relay import bind_worktree

        state = ensure_change(
            self.candidate, task={"task": "maintenance"}, mode="maintenance"
        )
        (self.primary / "concorde.json").write_text("{}")
        with self.assertRaises(SpecError) as error:
            bind_worktree(
                OperationHost(self.primary, self.primary),
                True,
                {"change_id": state["change_id"]},
            )
        self.assertEqual("fresh_session_required", error.exception.code)
        host, workspace = bind_worktree(
            OperationHost(self.candidate, self.candidate),
            True,
            {"change_id": state["change_id"]},
        )
        self.assertEqual(str(self.candidate), workspace["path"])
        self.assertNotIn("relay", workspace)

    @verifies("scenario.harness.worktree-relay")
    def test_source_carrying_relay_checks_existing_build_without_rebuilding(self):
        from concorde.distribution.build import BuildError
        from concorde.harness.host import OperationHost
        from concorde.harness.relay import relay_operation

        (self.candidate / "concorde.json").write_text("{}")
        (self.candidate / "src/concorde").mkdir(parents=True)
        with (
            patch(
                "concorde.distribution.build.verify_fresh",
                side_effect=BuildError("stale", "stale_build"),
            ) as verify,
            patch("subprocess.Popen") as launch,
        ):
            with self.assertRaises(BuildError):
                relay_operation(
                    OperationHost(self.primary, self.primary),
                    "concorde-main",
                    {},
                    self.candidate,
                )
            verify.assert_called_once_with(self.candidate)
            launch.assert_not_called()
        (self.candidate / ".venv/bin").mkdir(parents=True)
        (self.candidate / ".venv/bin/python").write_text("fixture interpreter")
        (self.candidate / "scripts").mkdir()
        (self.candidate / "scripts/run-operation.py").write_text("fixture launcher")
        with (
            patch("concorde.distribution.build.verify_fresh") as verify,
            patch("subprocess.Popen") as launch,
        ):
            launch.return_value.communicate.return_value = (
                '{"type_id":"concorde-operation-result"}',
                "diagnostics",
            )
            result, diagnostics = relay_operation(
                OperationHost(self.primary, self.primary),
                "concorde-main",
                {},
                self.candidate,
            )
            verify.assert_called_once_with(self.candidate)
            launch.assert_called_once()
            self.assertEqual("concorde-main", launch.call_args.args[0][-1])
            self.assertEqual(
                str(self.candidate / ".venv/bin/python"), launch.call_args.args[0][0]
            )
            self.assertNotIn("PYTHONPATH", launch.call_args.kwargs["env"])
            self.assertNotIn("PYTHONHOME", launch.call_args.kwargs["env"])
            self.assertEqual("diagnostics", diagnostics)

    @verifies("scenario.harness.primary-status")
    def test_private_skill_selection_cannot_redirect_to_source_primary(self):
        import io

        from concorde.harness.entry import json_main

        request = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": "concorde-main",
            "mode": "execute",
            "configuration": None,
            "input": {},
        }
        output = io.StringIO()
        with (
            patch.dict(
                "os.environ",
                {
                    "CONCORDE_SESSION_SELECTION": str(
                        self.candidate / "selection.json"
                    ),
                },
            ),
            patch("sys.argv", ["run-operation.py"]),
            patch("sys.stdin", io.StringIO(json.dumps(request))),
            patch("sys.stdout", output),
            patch("pathlib.Path.cwd", return_value=self.primary),
        ):
            self.assertEqual(3, json_main(self.candidate, "concorde-main", None))
        self.assertEqual(
            "workspace_mismatch", json.loads(output.getvalue())["errors"][0]["code"]
        )
        self.assertFalse((self.primary / ".concorde/status").exists())
        self.assertFalse((self.primary / ".concorde/runs").exists())
