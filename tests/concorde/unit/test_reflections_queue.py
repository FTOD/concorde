from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.reflection_triage import (
    create_triage_project,
    tree_hashes,
    write_config,
    write_plan,
)
from tests.concorde.support.paths import REPOSITORY_ROOT


SCRIPT = REPOSITORY_ROOT / "extensions/concorde/scripts/python/reflections_queue.py"


def run_queue(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), "--root", str(root), *arguments],
        text=True,
        capture_output=True,
        check=check,
    )


class ReflectionsQueueTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
