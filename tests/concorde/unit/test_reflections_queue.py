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

from tests.concorde.support.reflection_triage import (
    create_triage_project,
    commit_change,
    git,
    initialize_git,
    tree_hashes,
    write_config,
    write_plan,
)
from tests.concorde.support.paths import REPOSITORY_ROOT


SCRIPT = REPOSITORY_ROOT / "extensions/concorde/scripts/python/reflections_queue.py"


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
            self.assertTrue((root / ".concorde/reflections/log.md").is_file())
            self.assertFalse((root / "specs/example/reflections.md").exists())
            write_plan(root, "R-003")
            before = tree_hashes(root)

            first = json.loads(run_queue(root, "--json").stdout)
            second = json.loads(run_queue(root, "--json").stdout)
            pending = json.loads(run_queue(root, "--next", "2").stdout)
            entry = json.loads(run_queue(root, "--entry", "R-001").stdout)
            plans = json.loads(run_queue(root, "--plans").stdout)

            self.assertEqual(first, second)
            self.assertEqual([item["id"] for item in first["entries"]], ["R-003", "R-002", "R-001"])
            self.assertEqual([item["id"] for item in pending], ["R-002", "R-001"])
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
            self.assertEqual(payload["summary"], {"open": 2, "planned": 0, "total": 3})

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
                with self.subTest(arguments=arguments):
                    result = run_queue(root, *arguments, check=False)
                    self.assertEqual(result.returncode, 2)
                    self.assertTrue(result.stderr.strip())

            invalid = write_plan(root, "R-003")
            invalid.write_text(invalid.read_text().replace("route: fast-loop", "route: unknown"))
            result = run_queue(root, "--plans", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("route", result.stderr)

    def test_allocate_id_advances_tracked_high_water_atomically(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = create_triage_project(Path(temporary))
            log = root / ".concorde/reflections/log.md"
            log.chmod(0o640)
            first = json.loads(run_queue(root, "--allocate-id").stdout)
            second = json.loads(run_queue(root, "--allocate-id").stdout)
            self.assertEqual(first["operation"], "allocate-reflection-id")
            self.assertEqual(first["status"], "allocated")
            self.assertEqual((first["previous_high_water"], first["allocated_id"], first["high_water"]), ("R-003", "R-004", "R-004"))
            self.assertEqual(second["allocated_id"], "R-005")
            self.assertRegex(first["before_sha256"], r"^sha256:[0-9a-f]{64}$")
            self.assertRegex(first["after_sha256"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual(stat.S_IMODE(log.stat().st_mode), 0o640)
            self.assertIn("<!-- concorde-reflection-high-water: R-005 -->", log.read_text(encoding="utf-8"))

    def test_remove_merged_is_multi_id_atomic_and_preserves_raw_neighbors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, _ = self.eligible_project(Path(temporary), "R-001", "R-002", "R-003")
            log = root / ".concorde/reflections/log.md"
            original = log.read_bytes().replace(b"\n", b"\r\n").rstrip(b"\r\n")
            log.write_bytes(original)
            log.chmod(0o640)
            retained = json.loads(run_queue(root, "--entry", "R-003").stdout)["text"].replace("\n", "\r\n").rstrip().encode()

            result = json.loads(run_queue(root, "--remove-merged", "R-002", "R-001").stdout)

            self.assertEqual(result["operation"], "remove-merged-reflections")
            self.assertEqual(result["status"], "removed")
            self.assertEqual(result["removed"], ["R-001", "R-002"])
            self.assertEqual((result["removed_count"], result["remaining_count"]), (2, 1))
            self.assertRegex(result["head"], r"^[0-9a-f]{40,64}$")
            self.assertEqual(stat.S_IMODE(log.stat().st_mode), 0o640)
            self.assertFalse(log.read_bytes().endswith((b"\n", b"\r")))
            self.assertNotIn(b"\n", log.read_bytes().replace(b"\r\n", b""))
            self.assertIn(retained, log.read_bytes())
            self.assertIn(b"concorde-reflection-high-water: R-003", log.read_bytes())

    def test_remove_merged_rejects_mixed_or_mismatched_requests_without_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, commit = self.eligible_project(Path(temporary), "R-001", "R-002")
            write_plan(root, "R-002", status="merged", effort="medium", commit=commit)
            before = tree_hashes(root)
            log = root / ".concorde/reflections/log.md"
            log_before = log.read_bytes()
            result = run_queue(root, "--remove-merged", "R-001", "R-002", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("effort", result.stderr)
            self.assertEqual(tree_hashes(root), before)

            write_plan(root, "R-002", status="merged", commit=commit, recorded_under="feature.example.other")
            result = run_queue(root, "--remove-merged", "R-002", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("recorded_under", result.stderr)
            self.assertEqual(log.read_bytes(), log_before)

    def test_remove_merged_rejects_noncanonical_missing_nonopen_and_nonancestor_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, commit = self.eligible_project(Path(temporary), "R-001", "R-002")
            log = root / ".concorde/reflections/log.md"
            log.write_text(log.read_text().replace("- **Status**: open", "- **Status**: resolved\n- **Note**: decided", 1))
            for arguments, needle in (
                (("R-01",), "canonical"),
                (("R-003",), "open entry"),
                (("R-001",), "open"),
            ):
                with self.subTest(arguments=arguments):
                    before = log.read_bytes()
                    result = run_queue(root, "--remove-merged", *arguments, check=False)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn(needle, result.stderr)
                    self.assertEqual(log.read_bytes(), before)

            git(root, "checkout", "--orphan", "side")
            (root / "side.txt").write_text("side\n")
            git(root, "add", "side.txt")
            git(root, "commit", "-m", "side")
            side = git(root, "rev-parse", "HEAD")
            git(root, "checkout", "main")
            write_plan(root, "R-002", status="merged", commit=side)
            before = log.read_bytes()
            result = run_queue(root, "--remove-merged", "R-002", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("ancestor", result.stderr)
            self.assertEqual(log.read_bytes(), before)

    def test_remove_merged_is_fence_aware_and_rejects_symlinked_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, _ = self.eligible_project(Path(temporary), "R-001", "R-002")
            log = root / ".concorde/reflections/log.md"
            body = log.read_text(encoding="utf-8").replace(
                "- **Observed**: The command failed.",
                "```text\n### R-999 · fenced example\n```\n- **Observed**: The command failed.",
                1,
            )
            log.write_text(body, encoding="utf-8")
            result = run_queue(root, "--remove-merged", "R-001")
            self.assertEqual(result.returncode, 0)
            self.assertNotIn("R-999", log.read_text())
            self.assertIn("### R-002", log.read_text())

            plan = root / ".concorde/reflections/plans/R-002.md"
            target = root / "outside-plan.md"
            target.write_bytes(plan.read_bytes())
            plan.unlink()
            plan.symlink_to(target)
            before = log.read_bytes()
            failed = run_queue(root, "--remove-merged", "R-002", check=False)
            self.assertEqual(failed.returncode, 2)
            self.assertIn("symlink", failed.stderr)
            self.assertEqual(log.read_bytes(), before)

    def test_atomic_replace_failure_and_digest_conflict_preserve_log(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, _ = self.eligible_project(Path(temporary), "R-001")
            queue = load_queue_module()
            log = root / ".concorde/reflections/log.md"
            before = log.read_bytes()
            with mock.patch.object(queue.os, "replace", side_effect=OSError("injected")):
                with self.assertRaises(queue.QueueError):
                    queue.remove_merged(root, ["R-001"])
            self.assertEqual(log.read_bytes(), before)
            self.assertFalse((log.parent / ".log.md.reflection-triage-stage").exists())

            with self.assertRaises(queue.QueueError):
                queue._atomic_log_replace(log, b"stale", b"replacement")
            self.assertEqual(log.read_bytes(), before)

    def test_high_water_covers_entries_and_retained_plans_and_cli_actions_are_exclusive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = create_triage_project(Path(temporary))
            write_plan(root, "R-004")
            before = tree_hashes(root)
            result = run_queue(root, "--json", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("high-water", result.stderr)
            self.assertEqual(tree_hashes(root), before)
            exclusive = run_queue(root, "--json", "--allocate-id", check=False)
            self.assertEqual(exclusive.returncode, 2)


if __name__ == "__main__":
    unittest.main()
