from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import unittest
from importlib import util
from pathlib import Path
from unittest import mock

from tests.concorde.support.feature_workspace import reflection_entry, write_reflection_collection
from tests.concorde.support.reflection_triage import (
    commit_change,
    create_triage_project,
    git,
    initialize_git,
    tree_hashes,
    write_config,
    write_high_water,
    write_plan,
)
from tests.concorde.support.paths import REPOSITORY_ROOT


SCRIPT = REPOSITORY_ROOT / "scripts/reflections_queue.py"


def load_queue_module():
    spec = util.spec_from_file_location("reflections_queue_under_test", SCRIPT)
    assert spec and spec.loader
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_queue(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), "--root", str(root), *arguments],
        text=True,
        capture_output=True,
        check=check,
    )


class ReflectionsQueueTests(unittest.TestCase):
    def eligible_project(self, root: Path, *identifiers: str) -> tuple[Path, str]:
        create_triage_project(root, entry_count=max(int(item[2:]) for item in identifiers))
        initialize_git(root)
        commit = commit_change(root)
        for identifier in identifiers:
            write_plan(root, identifier, status="merged", commit=commit)
        return root, commit

    def test_status_next_entry_and_plans_are_repeatable_and_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = create_triage_project(Path(temporary))
            self.assertTrue((root / ".concorde/reflections/index.json").is_file())
            self.assertTrue((root / ".concorde/reflections/pending/R-001.md").is_file())
            self.assertFalse((root / ".concorde/reflections/log.md").exists())
            write_plan(root, "R-003")
            before = tree_hashes(root)

            first = json.loads(run_queue(root, "--json").stdout)
            second = json.loads(run_queue(root, "--json").stdout)
            pending = json.loads(run_queue(root, "--next", "2").stdout)
            entry = json.loads(run_queue(root, "--entry", "R-001").stdout)
            plans = json.loads(run_queue(root, "--plans").stdout)

            self.assertEqual(first, second)
            self.assertEqual([item["id"] for item in first["entries"]], ["R-003", "R-002", "R-001"])
            self.assertEqual([item["id"] for item in pending], ["R-003", "R-002"])
            self.assertEqual(entry["path"], ".concorde/reflections/pending/R-001.md")
            self.assertEqual(entry["bucket"], "pending")
            self.assertEqual(entry["feature_path"], "specs/example/features/001-deliver.md")
            self.assertEqual(entry["concerns_path"], "specs/example/architecture.md")
            self.assertEqual(plans["R-003"]["route"], "fast-loop")
            self.assertEqual(tree_hashes(root), before)

    def test_order_skip_and_feature_mapping_use_shared_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = create_triage_project(Path(temporary))
            write_config(root, order="oldest-first", skip=["R-002"])
            payload = json.loads(run_queue(root, "--json").stdout)
            self.assertEqual([item["id"] for item in payload["entries"]], ["R-001", "R-003"])
            self.assertEqual(
                payload["summary"],
                {
                    "open": 2,
                    "pending_triage": 2,
                    "planned": 0,
                    "total": 3,
                    "buckets": {"pending": 3, "planned": 0, "needs-comments": 0},
                },
            )

    def test_set_updates_only_named_plan_and_rejects_invalid_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = create_triage_project(Path(temporary))
            first = write_plan(root, "R-001")
            second = write_plan(root, "R-002")
            second_before = second.read_bytes()
            updated = json.loads(run_queue(root, "--set", "R-001", "status=approved").stdout)
            self.assertEqual(updated["status"], "approved")
            self.assertIn("status: approved", first.read_text(encoding="utf-8"))
            self.assertEqual(second.read_bytes(), second_before)
            for arguments in (
                ("--set", "R-001", "route=dismiss"),
                ("--set", "R-001", "status=merged"),
                ("--set", "R-999", "status=approved"),
            ):
                result = run_queue(root, *arguments, check=False)
                self.assertEqual(result.returncode, 2)

    def test_allocate_id_advances_index_atomically_and_returns_document_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = create_triage_project(Path(temporary))
            index = root / ".concorde/reflections/index.json"
            index.chmod(0o640)
            first = json.loads(run_queue(root, "--allocate-id").stdout)
            second = json.loads(run_queue(root, "--allocate-id").stdout)
            self.assertEqual(first["tool"], "allocate-reflection-id")
            self.assertEqual(first["status"], "allocated")
            self.assertEqual(first["reflection_path"], ".concorde/reflections/pending/R-004.md")
            self.assertEqual(first["bucket"], "pending")
            self.assertTrue((root / ".concorde/reflections/pending").is_dir())
            self.assertEqual((first["previous_high_water"], first["allocated_id"], first["high_water"]), ("R-003", "R-004", "R-004"))
            self.assertEqual(second["allocated_id"], "R-005")
            self.assertRegex(first["before_sha256"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual(stat.S_IMODE(index.stat().st_mode), 0o640)
            self.assertEqual(json.loads(index.read_text())["high_water"], "R-005")

    def test_remove_merged_removes_exact_files_and_preserves_neighbors_and_index(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, _ = self.eligible_project(Path(temporary), "R-001", "R-002", "R-003")
            collection = root / ".concorde/reflections"
            retained = (collection / "pending" / "R-003.md").read_bytes()
            index = (collection / "index.json").read_bytes()
            result = json.loads(run_queue(root, "--remove-merged", "R-002", "R-001").stdout)
            self.assertEqual(result["removed"], ["R-001", "R-002"])
            self.assertEqual(result["removed_paths"], [".concorde/reflections/pending/R-001.md", ".concorde/reflections/pending/R-002.md"])
            self.assertEqual((result["removed_count"], result["remaining_count"]), (2, 1))
            self.assertFalse((collection / "pending" / "R-001.md").exists())
            self.assertFalse((collection / "pending" / "R-002.md").exists())
            self.assertEqual((collection / "pending" / "R-003.md").read_bytes(), retained)
            self.assertEqual((collection / "index.json").read_bytes(), index)

    def test_remove_merged_rejects_mixed_mismatched_or_nonopen_without_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, commit = self.eligible_project(Path(temporary), "R-001", "R-002")
            write_plan(root, "R-002", status="merged", effort="medium", commit=commit)
            before = tree_hashes(root)
            result = run_queue(root, "--remove-merged", "R-001", "R-002", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("effort", result.stderr)
            self.assertEqual(tree_hashes(root), before)

            write_plan(root, "R-002", status="merged", commit=commit, recorded_under="feature.example.other")
            before = tree_hashes(root)
            result = run_queue(root, "--remove-merged", "R-002", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("recorded_under", result.stderr)
            self.assertEqual(tree_hashes(root), before)

            reflection = root / ".concorde/reflections/pending/R-001.md"
            reflection.write_text(reflection.read_text().replace("status: open", "status: resolved\nresolution_note: decided"))
            result = run_queue(root, "--remove-merged", "R-001", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("not open", result.stderr)

    def test_remove_merged_rejects_noncanonical_missing_and_nonancestor_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, _ = self.eligible_project(Path(temporary), "R-001", "R-002")
            for arguments, needle in (("R-01", "canonical"), ("R-003", "open document")):
                before = tree_hashes(root)
                result = run_queue(root, "--remove-merged", arguments, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertIn(needle, result.stderr)
                self.assertEqual(tree_hashes(root), before)

            git(root, "checkout", "--orphan", "side")
            (root / "side.txt").write_text("side\n")
            git(root, "add", "side.txt")
            git(root, "commit", "-m", "side")
            side = git(root, "rev-parse", "HEAD")
            git(root, "checkout", "main")
            write_plan(root, "R-002", status="merged", commit=side)
            before = tree_hashes(root)
            result = run_queue(root, "--remove-merged", "R-002", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("ancestor", result.stderr)
            self.assertEqual(tree_hashes(root), before)

    def test_remove_merged_is_fence_aware_and_rejects_symlinked_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, _ = self.eligible_project(Path(temporary), "R-001", "R-002")
            reflection = root / ".concorde/reflections/pending/R-001.md"
            reflection.write_text(reflection.read_text().replace("## Evidence", "```text\n## Fake Section\n```\n\n## Evidence", 1))
            self.assertEqual(run_queue(root, "--remove-merged", "R-001").returncode, 0)
            plan = root / ".concorde/reflections/plans/R-002.md"
            target = root / "outside-plan.md"
            target.write_bytes(plan.read_bytes())
            plan.unlink()
            plan.symlink_to(target)
            before = (root / ".concorde/reflections/pending/R-002.md").read_bytes()
            failed = run_queue(root, "--remove-merged", "R-002", check=False)
            self.assertEqual(failed.returncode, 2)
            self.assertIn("symlink", failed.stderr)
            self.assertEqual((root / ".concorde/reflections/pending/R-002.md").read_bytes(), before)

    def test_atomic_replace_failure_and_digest_conflict_preserve_index(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = create_triage_project(Path(temporary), entry_count=1)
            queue = load_queue_module()
            index = root / ".concorde/reflections/index.json"
            before = index.read_bytes()
            with mock.patch.object(queue.os, "replace", side_effect=OSError("injected")):
                with self.assertRaises(queue.QueueError):
                    queue.allocate_id(root)
            self.assertEqual(index.read_bytes(), before)
            self.assertFalse((index.parent / ".index.json.reflection-stage").exists())
            with self.assertRaises(queue.QueueError):
                queue._atomic_file_replace(root, index, b"stale", b"replacement", "reflection allocation index")
            self.assertEqual(index.read_bytes(), before)

    def test_multi_file_removal_rolls_back_when_promotion_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, _ = self.eligible_project(Path(temporary), "R-001", "R-002")
            queue = load_queue_module()
            before = tree_hashes(root)
            actual_replace = os.replace
            calls = 0

            def fail_second(source, target):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected")
                return actual_replace(source, target)

            with mock.patch.object(queue.os, "replace", side_effect=fail_second):
                with self.assertRaises(queue.QueueError):
                    queue.remove_merged(root, ["R-001", "R-002"])
            self.assertEqual(tree_hashes(root), before)
            self.assertFalse((root / ".concorde/reflections/.remove-merged-stage").exists())

    def test_high_water_covers_documents_and_plans_and_cli_actions_are_exclusive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = create_triage_project(Path(temporary))
            write_plan(root, "R-004")
            before = tree_hashes(root)
            result = run_queue(root, "--json", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("high_water", result.stderr)
            self.assertEqual(tree_hashes(root), before)
            exclusive = run_queue(root, "--json", "--allocate-id", check=False)
            self.assertEqual(exclusive.returncode, 2)

    @staticmethod
    def completed_entry(identifier: str, human_intervention: str, **extra: str) -> dict[str, str]:
        return reflection_entry(
            identifier,
            Triage="complete",
            **{
                "Human Intervention": human_intervention,
                "Triage Analysis": "Root cause established at the cited path.",
                "Proposed Resolution": "Apply the bounded change.",
                "Intervention Rationale": "Decided by triage.",
                **extra,
            },
        )

    def test_relocate_moves_completed_documents_by_triage_state_without_editing_them(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = create_triage_project(Path(temporary))
            collection = root / ".concorde/reflections"
            # Simulate the parent having persisted two completions in place under pending/.
            write_reflection_collection(root, [
                self.completed_entry("R-001", "not-required", bucket="pending"),
                self.completed_entry("R-002", "required", bucket="pending"),
                reflection_entry("R-003"),
            ])
            write_high_water(collection, 3)
            first = (collection / "pending" / "R-001.md").read_bytes()
            second = (collection / "pending" / "R-002.md").read_bytes()

            refused = run_queue(root, "--json", check=False)
            self.assertEqual(refused.returncode, 2)
            self.assertIn("--relocate", refused.stderr)
            for arguments in (("--allocate-id",), ("--set", "R-001", "status=approved")):
                self.assertEqual(run_queue(root, *arguments, check=False).returncode, 2)

            one = json.loads(run_queue(root, "--relocate", "R-002").stdout)
            self.assertEqual(one["tool"], "relocate-reflections")
            self.assertEqual(one["status"], "relocated")
            self.assertEqual(one["moved"], [{
                "id": "R-002",
                "from": ".concorde/reflections/pending/R-002.md",
                "to": ".concorde/reflections/needs-comments/R-002.md",
                "bucket": "needs-comments",
            }])
            self.assertEqual((one["moved_count"], one["unchanged_count"]), (1, 0))
            self.assertFalse((collection / "pending" / "R-002.md").exists())
            self.assertEqual((collection / "needs-comments" / "R-002.md").read_bytes(), second)
            self.assertTrue((collection / "pending" / "R-001.md").is_file())

            everything = json.loads(run_queue(root, "--relocate").stdout)
            self.assertEqual([item["id"] for item in everything["moved"]], ["R-001"])
            self.assertEqual(everything["moved"][0]["to"], ".concorde/reflections/planned/R-001.md")
            self.assertEqual((collection / "planned" / "R-001.md").read_bytes(), first)
            self.assertEqual(everything["buckets"], {"pending": 1, "planned": 1, "needs-comments": 1})

            again = json.loads(run_queue(root, "--relocate").stdout)
            self.assertEqual((again["status"], again["moved"], again["moved_count"], again["unchanged_count"]), ("unchanged", [], 0, 3))
            self.assertEqual(again["before_sha256"], again["after_sha256"])

            payload = json.loads(run_queue(root, "--json").stdout)
            self.assertEqual(payload["summary"]["buckets"], {"pending": 1, "planned": 1, "needs-comments": 1})
            self.assertEqual({item["id"]: item["bucket"] for item in payload["entries"]}, {"R-001": "planned", "R-002": "needs-comments", "R-003": "pending"})

            # A maintainer decision never moves a file; a changed intervention decision does.
            waiting = collection / "needs-comments" / "R-002.md"
            waiting.write_text(waiting.read_text().replace("status: open", "status: resolved\nresolution_note: decided"))
            self.assertEqual(json.loads(run_queue(root, "--relocate").stdout)["status"], "unchanged")
            waiting.write_text(waiting.read_text().replace("human_intervention: required", "human_intervention: not-required"))
            flipped = json.loads(run_queue(root, "--relocate", "R-002").stdout)
            self.assertEqual(flipped["moved"][0]["to"], ".concorde/reflections/planned/R-002.md")

            for arguments, needle in ((("--relocate", "R-01"), "canonical"), (("--relocate", "R-009"), "no matching"), (("--relocate", "R-001", "R-001"), "repeated")):
                result = run_queue(root, *arguments, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertIn(needle, result.stderr)

    def test_relocate_rolls_back_and_rejects_symlinked_bucket_or_existing_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = create_triage_project(Path(temporary))
            collection = root / ".concorde/reflections"
            write_reflection_collection(root, [
                self.completed_entry("R-001", "required", bucket="pending"),
                self.completed_entry("R-002", "required", bucket="pending"),
                reflection_entry("R-003"),
            ])
            write_high_water(collection, 3)
            queue = load_queue_module()
            before = tree_hashes(root)
            actual_replace = os.replace
            calls = 0

            def fail_second(source, target):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected")
                return actual_replace(source, target)

            with mock.patch.object(queue.os, "replace", side_effect=fail_second):
                with self.assertRaises(queue.QueueError):
                    queue.relocate(root, [])
            self.assertEqual(tree_hashes(root), before)

            # A target that appears between load and move is refused without touching the source.
            source = collection / "pending" / "R-001.md"
            occupied = collection / "needs-comments" / "R-001.md"
            occupied.parent.mkdir(exist_ok=True)
            occupied.write_text("occupied\n", encoding="utf-8")
            with self.assertRaisesRegex(queue.QueueError, "already exists"):
                queue._move_documents(
                    root,
                    [("R-001", ".concorde/reflections/pending/R-001.md", ".concorde/reflections/needs-comments/R-001.md")],
                    {".concorde/reflections/pending/R-001.md": source.read_bytes()},
                )
            self.assertTrue(source.is_file())
            self.assertEqual(occupied.read_text(encoding="utf-8"), "occupied\n")
            occupied.unlink()
            occupied.parent.rmdir()

            outside = Path(temporary) / "outside-bucket"
            outside.mkdir()
            (collection / "needs-comments").symlink_to(outside, target_is_directory=True)
            before = tree_hashes(root)
            result = run_queue(root, "--relocate", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("symlink", result.stderr)
            self.assertEqual(tree_hashes(root), before)


if __name__ == "__main__":
    unittest.main()
