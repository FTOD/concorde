from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.planning_context import (  # noqa: E402
    PlanningContextError,
    resolve_planning_context,
)


FIXTURE = REPOSITORY_ROOT / "tests/concorde/fixtures/permission-planning-project"
SELECTED = "specs/example/modules/consumer/features/001-change.md"


class PlanningContextTests(unittest.TestCase):
    def test_required_interface_owner_is_included_with_reason_and_incidental_relation_is_not(self):
        context = resolve_planning_context(FIXTURE, SELECTED)
        self.assertEqual(context.feature_path, SELECTED)
        self.assertEqual(
            [(item.feature_path, item.interface_ids) for item in context.required_feature_specs],
            [("specs/example/modules/provider/features/001-api.md", ("contract.provider.api",))],
        )
        readable = set(path for paths in context.role_paths.values() for path in paths)
        self.assertIn("specs/example/modules/provider/features/001-api.md", readable)
        self.assertNotIn("specs/example/modules/provider/features/002-unrelated.md", readable)

    def test_selected_module_owned_locators_and_task_paths_are_bounded(self):
        context = resolve_planning_context(FIXTURE, SELECTED)
        self.assertEqual(
            context.owned_implementation_paths,
            ("src/consumer/service.py", "tests/consumer/test_service.py"),
        )
        self.assertEqual(context.task_authorized_paths, context.owned_implementation_paths)
        self.assertEqual(
            context.role_paths["owned-implementation"],
            context.owned_implementation_paths,
        )
        self.assertRegex(context.source_digest, r"^sha256:[0-9a-f]{64}$")

    def test_provider_internals_other_attempts_and_undeclared_paths_are_denied(self):
        context = resolve_planning_context(FIXTURE, SELECTED)
        denied = set(context.denied_paths)
        self.assertTrue(
            {
                "specs/example/modules/provider/architecture.md",
                "src/provider/private.py",
                "tests/provider/test_private.py",
                ".concorde/attempts/feature.example.other",
            }.issubset(denied)
        )
        readable = set(path for paths in context.role_paths.values() for path in paths)
        self.assertTrue(denied.isdisjoint(readable))

    def test_path_escapes_symlinks_and_cross_module_task_writes_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(FIXTURE, project)
            owned = project / "src/consumer/service.py"
            target = project / "src/provider/private.py"
            owned.unlink()
            owned.symlink_to(target)
            with self.assertRaisesRegex(PlanningContextError, "symlink"):
                resolve_planning_context(project, SELECTED)

        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(FIXTURE, project)
            tasks = project / ".concorde/attempts/feature.example.consumer.change/tasks.md"
            tasks.write_text(
                tasks.read_text() + "- [ ] T002 Edit `src/provider/private.py` [FR-002]\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PlanningContextError, "outside providing module"):
                resolve_planning_context(project, SELECTED)


if __name__ == "__main__":
    unittest.main()
