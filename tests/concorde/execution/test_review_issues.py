"""Method's Issue calls run only the started worktree's own ``concorde``."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from concorde.method import review_issues
from concorde.spec.verification import verifies


class StartedConcordeTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)

    def test_the_installed_command_comes_before_a_source_checkouts_script(self):
        (self.root / "scripts").mkdir()
        (self.root / "scripts/concorde.py").write_text("")
        self.assertEqual(
            [sys.executable, str(self.root / "scripts/concorde.py")],
            review_issues.started_concorde(self.root),
        )
        (self.root / ".concorde/bin").mkdir(parents=True)
        (self.root / ".concorde/bin/concorde").write_text("")
        self.assertEqual(
            [str(self.root / ".concorde/bin/concorde")],
            review_issues.started_concorde(self.root),
        )

    @verifies("scenario.method.issues-concorde-missing")
    def test_a_worktree_without_its_own_concorde_runs_no_other(self):
        context = SimpleNamespace(started_in=str(self.root))
        with (
            patch.object(review_issues.subprocess, "run") as run,
            self.assertRaises(review_issues.Refusal) as raised,
        ):
            review_issues.call(context, "list", "--module", "module.a")
        run.assert_not_called()
        error = raised.exception.link
        self.assertEqual(
            ("component", "issues_command_failed", "environment"),
            (error["level"], error["code"], error["unhandled"]["reason"]),
        )
        self.assertIn(str(self.root), error["detail"])
        self.assertIn(".concorde/bin/concorde", error["detail"])
        self.assertIn("scripts/concorde.py", error["detail"])


if __name__ == "__main__":
    unittest.main()
