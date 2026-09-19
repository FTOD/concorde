"""Primary persistence and migration tested only in disposable Git repositories."""

import json
import copy
import threading
from contextlib import contextmanager
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
    refresh_registry,
    progress,
    save_target_state,
    target_state,
    worktree_incarnation,
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

    def legacy_receipt(self, key, status, retained):
        commit = git(self.candidate, "rev-parse", "HEAD").stdout.strip()
        tree = git(self.candidate, "rev-parse", "HEAD^{tree}").stdout.strip()
        return {
            "schema_version": 1,
            "change_id": key,
            "status": status,
            "target_id": "module.example",
            "focus_id": None,
            "source_worktree": str(self.candidate),
            "source_branch": "task",
            "candidate_commit": commit,
            "candidate_tree": tree,
            "target_branch": "concorde/delivered/" + key,
            "target_before": commit,
            "primary_branch": "trunk",
            "primary_merge": None,
            "merged_commit": commit,
            "merged_tree": tree,
            "task": "fixture",
            "constraints": [],
            "targets": {},
            "checks": [],
            "confirmed_files": [],
            "still_pending": [],
            "cleanup_error": None,
            "retained_worktree": retained,
        }

    @verifies("scenario.harness.status-migration")
    def test_migration_preflights_receipt_ownership_before_any_effect(self):
        state, old, run = self.legacy()
        state.update(
            task="fixture", target_id="module.example", focus_id="scenario.example"
        )
        old.write_text(json.dumps(state))
        admin = Path(
            git(self.candidate, "rev-parse", "--absolute-git-dir").stdout.strip()
        )
        (admin / "concorde-incarnation").unlink()
        receipt = self.legacy_receipt(state["change_id"], "delivered", True)
        receipt["focus_id"] = state["focus_id"]
        git(
            self.primary,
            "update-ref",
            "refs/heads/" + receipt["target_branch"],
            receipt["merged_commit"],
        )
        path = self.primary / f".concorde/deliveries/{state['change_id']}.json"
        path.parent.mkdir(parents=True)
        original = old.read_bytes()
        for field, value in (
            ("source_worktree", str(self.candidate.with_name("other"))),
            ("source_branch", "other"),
            ("task", "unrelated work"),
            ("constraints", ["different intent"]),
            ("target_id", "module.other"),
            ("focus_id", "scenario.other"),
        ):
            for apply in (False, True):
                with self.subTest(field=field, apply=apply):
                    path.write_text(json.dumps({**receipt, field: value}))
                    receipt_bytes = path.read_bytes()
                    with self.assertRaises(SpecError) as error:
                        migrate_legacy(self.primary, apply=apply)
                    self.assertEqual("migration_conflict", error.exception.code)
                    self.assertEqual(original, old.read_bytes())
                    self.assertEqual(receipt_bytes, path.read_bytes())
                    self.assertEqual(b"legacy bytes", run.read_bytes())
                    self.assertIsNone(worktree_incarnation(self.candidate))
                    self.assertFalse(
                        (self.primary / status_path(state["change_id"])).exists()
                    )
                    self.assertFalse(
                        (self.primary / ".concorde/status/migration.json").exists()
                    )
                    self.assertFalse((self.primary / ".concorde/runs").exists())

    @verifies("scenario.harness.status-migration")
    def test_legacy_bound_null_focus_is_not_unknown_ownership(self):
        state, old, run = self.legacy()
        state.update(task="fixture", target_id="module.example", focus_id=None)
        old.write_text(json.dumps(state))
        receipt = self.legacy_receipt(state["change_id"], "delivered", True)
        receipt["focus_id"] = "scenario.other"
        path = self.primary / f".concorde/deliveries/{state['change_id']}.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(receipt))
        before = {p: p.read_bytes() for p in (old, run, path)}
        with self.assertRaises(SpecError) as error:
            migrate_legacy(self.primary, apply=True)
        self.assertEqual("migration_conflict", error.exception.code)
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertFalse((self.primary / ".concorde/status/migration.json").exists())

    @verifies("scenario.harness.status-migration")
    def test_compatible_legacy_owners_survive_live_branch_rename_and_retry(self):
        state, old, run = self.legacy()
        state.update(task="fixture", target_id="module.example")
        state["targets"] = {
            "module.example": {
                "target_id": "module.example",
                "focus_id": None,
                "plan": "legacy",
            }
        }
        old.write_text(json.dumps(state))
        original = old.read_bytes()
        receipt = self.legacy_receipt(state["change_id"], "delivered", True)
        path = self.primary / f".concorde/deliveries/{state['change_id']}.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(receipt))
        receipt_bytes = path.read_bytes()
        git(
            self.primary,
            "update-ref",
            "refs/heads/" + receipt["target_branch"],
            receipt["merged_commit"],
        )
        git(self.candidate, "branch", "-m", "renamed")
        unlink = Path.unlink

        def interrupted(source, *args, **kwargs):
            if source == path:
                raise OSError("interrupted receipt removal")
            return unlink(source, *args, **kwargs)

        with patch.object(Path, "unlink", interrupted), self.assertRaises(OSError):
            migrate_legacy(self.primary, apply=True)
        self.assertEqual(
            "completed", migrate_legacy(self.primary, apply=True)["status"]
        )
        imported = read_change(self.candidate, required=True)
        self.assertEqual("delivered", imported["status"])
        value = target_state(self.candidate, "module.example", None)
        self.assertEqual(
            {
                "change_id": state["change_id"],
                "git_worktree_id": worktree_incarnation(self.candidate),
            },
            value["owner"],
        )
        archives = [
            p.read_bytes()
            for p in (self.primary / ".concorde/runs/legacy-migration").rglob("*.json")
        ]
        self.assertIn(original, archives)
        self.assertIn(receipt_bytes, archives)
        save_target_state(self.candidate, value)

    @verifies("scenario.harness.status-migration")
    def test_receipt_migration_matrix_checks_publication_and_cleanup_independently(
        self,
    ):
        template = ensure_change(
            self.candidate, task={"task": "fixture"}, mode="maintenance"
        )
        (self.primary / status_path(template["change_id"])).unlink()
        case = 0
        for local in (False, True):
            for status in ("merging", "cleanup_pending", "delivered", "unknown"):
                for published in (False, True):
                    for retained in (False, True):
                        with self.subTest(
                            local=local,
                            status=status,
                            published=published,
                            retained=retained,
                        ):
                            case += 1
                            key = f"change.matrix-{case}"
                            receipt = self.legacy_receipt(key, status, retained)
                            path = self.primary / f".concorde/deliveries/{key}.json"
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.write_text(json.dumps(receipt, indent=3) + "\n")
                            originals = [path.read_bytes()]
                            if local:
                                state = {
                                    **template,
                                    "change_id": key,
                                    "status": "delivering",
                                    "phase": "deliver",
                                }
                                old = self.candidate / ".concorde/worktree.json"
                                old.parent.mkdir(parents=True, exist_ok=True)
                                old.write_text(json.dumps(state, indent=1))
                                originals.append(old.read_bytes())
                            if published:
                                git(
                                    self.primary,
                                    "update-ref",
                                    "refs/heads/" + receipt["target_branch"],
                                    receipt["merged_commit"],
                                )
                            self.assertEqual(
                                "completed",
                                migrate_legacy(self.primary, apply=True)["status"],
                            )
                            imported = read_status(self.primary, key)
                            delivered = published and status != "unknown"
                            self.assertEqual(
                                "delivered" if delivered else "blocked",
                                imported["status"],
                            )
                            self.assertEqual(
                                "delivered" if delivered else None,
                                imported.get("outcome"),
                            )
                            self.assertEqual(
                                "complete" if delivered else "migration",
                                imported["phase"],
                            )
                            self.assertEqual(
                                "unknown"
                                if status == "unknown"
                                else "retained"
                                if retained
                                else "pending",
                                imported["cleanup"]["status"],
                            )
                            self.assertIsNone(imported["validated_tree"])
                            self.assertIsNone(imported["validation"])
                            self.assertTrue(self.candidate.is_dir())
                            archives = [
                                p.read_bytes()
                                for p in (
                                    self.primary / ".concorde/runs/legacy-migration"
                                ).rglob("*.json")
                            ]
                            for original in originals:
                                self.assertIn(original, archives)
                            self.assertEqual(
                                [], migrate_legacy(self.primary, apply=True)["targets"]
                            )
                            # Do not reuse a local-state archive path with differing bytes.
                            # Keep history, but use a new live path for the next case.
                            if local:
                                new_path = self.candidate.with_name(f"candidate-{case}")
                                git(
                                    self.primary,
                                    "worktree",
                                    "move",
                                    str(self.candidate),
                                    str(new_path),
                                )
                                self.candidate = new_path
                                template["path"] = str(new_path)

    @verifies("scenario.harness.status-migration")
    def test_receipt_cleanup_absence_and_interrupted_import_preserve_original_bytes(
        self,
    ):
        for status in ("merging", "cleanup_pending", "delivered", "unknown"):
            key = "change.absent-" + status.replace("_", "-")
            receipt = self.legacy_receipt(key, status, True)
            # Missing path is not evidence of publication, regardless of receipt state.
            receipt["source_worktree"] = str(self.candidate.with_name("absent"))
            path = self.primary / f".concorde/deliveries/{key}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(receipt, indent=2))
            original = path.read_bytes()
            unlink = Path.unlink

            def interrupted(source, *args, **kwargs):
                if source == path:
                    raise OSError("interrupted receipt removal")
                return unlink(source, *args, **kwargs)

            with patch.object(Path, "unlink", interrupted), self.assertRaises(OSError):
                migrate_legacy(self.primary, apply=True)
            self.assertEqual(original, path.read_bytes())
            self.assertEqual(
                "completed", migrate_legacy(self.primary, apply=True)["status"]
            )
            imported = read_status(self.primary, key)
            self.assertEqual("blocked", imported["status"])
            self.assertIsNone(imported["outcome"])
            self.assertEqual(
                "unknown" if status == "unknown" else "removed",
                imported["cleanup"]["status"],
            )
            self.assertIn(
                original,
                [
                    p.read_bytes()
                    for p in (self.primary / ".concorde/runs/legacy-migration").rglob(
                        "*.json"
                    )
                ],
            )

    @verifies("scenario.harness.status-migration")
    def test_published_receipts_distinguish_removed_from_pending_git_cleanup(self):
        import shutil

        receipts = []
        for status in ("merging", "cleanup_pending", "delivered", "unknown"):
            for registered in (False, True):
                key = f"change.cleanup-{status.replace('_', '-')}-{int(registered)}"
                receipt = self.legacy_receipt(key, status, False)
                if not registered:
                    receipt["source_worktree"] = str(self.candidate.with_name("absent"))
                git(
                    self.primary,
                    "update-ref",
                    "refs/heads/" + receipt["target_branch"],
                    receipt["merged_commit"],
                )
                receipts.append((receipt, registered))
        shutil.rmtree(
            self.candidate
        )  # disposable fixture only; Git registration remains
        for receipt, registered in receipts:
            key = receipt["change_id"]
            path = self.primary / f".concorde/deliveries/{key}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(receipt))
            migrate_legacy(self.primary, apply=True)
            imported = read_status(self.primary, key)
            unknown = receipt["status"] == "unknown"
            self.assertEqual("blocked" if unknown else "delivered", imported["status"])
            self.assertEqual(
                "unknown" if unknown else "pending" if registered else "removed",
                imported["cleanup"]["status"],
            )
        self.assertFalse(self.candidate.exists())

    @verifies("scenario.harness.status-migration", "scenario.harness.primary-status")
    def test_legacy_incarnation_binds_only_on_apply_and_old_primary_path_id_is_refused(
        self,
    ):
        state, old, run = self.legacy()
        admin = Path(
            git(self.candidate, "rev-parse", "--absolute-git-dir").stdout.strip()
        )
        (admin / "concorde-incarnation").unlink()
        state["git_worktree_id"] = str(admin)
        old.write_text(json.dumps(state))
        original = old.read_bytes()
        migrate_legacy(self.primary)
        self.assertIsNone(worktree_incarnation(self.candidate))
        migrate_legacy(self.primary, apply=True)
        current = read_change(self.candidate, required=True)
        self.assertEqual(
            worktree_incarnation(self.candidate), current["git_worktree_id"]
        )
        self.assertIn(
            original,
            [
                p.read_bytes()
                for p in (self.primary / ".concorde/runs/legacy-migration").rglob(
                    "worktree.json"
                )
            ],
        )
        current["git_worktree_id"] = str(admin)
        write_status(self.primary, current)
        with self.assertRaises(SpecError) as error:
            read_change(self.candidate)
        self.assertEqual("migration_required", error.exception.code)
        self.assertFalse(refresh_registry(self.primary)["worktrees"][0]["managed"])

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

    @verifies("scenario.harness.status-migration", "scenario.harness.primary-status")
    def test_existing_unversioned_status_migration_needs_no_git_token(self):
        root = Path(self.temp.name) / "unversioned"
        root.mkdir()
        state = ensure_change(
            root, task={"task": "work"}, allow_primary=True, mode="direct"
        )
        (root / status_path(state["change_id"])).unlink()
        old = root / ".concorde/worktree.json"
        old.write_text(json.dumps(state))
        original = old.read_bytes()
        migrate_legacy(root, apply=True)
        current = read_change(root, required=True)
        self.assertIsNone(current["git_worktree_id"])
        self.assertEqual("blocked", current["status"])
        self.assertIn(
            original,
            [
                p.read_bytes()
                for p in (root / ".concorde/runs/legacy-migration").rglob(
                    "worktree.json"
                )
            ],
        )
        self.assertFalse((root / ".git").exists())

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
        from concorde.harness.host import OperationHost
        from concorde.harness.relay import relay_operation
        from concorde.distribution.build import BuildError

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
                    "CONCORDE_STUDIO_URL": "",
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
