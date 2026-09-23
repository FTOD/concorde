"""The rendered main-session guidance states every rule of the Main session Module.

The guidance is advice to a model; what a main agent then does is judgment no deterministic test
can observe. These tests check that the rendered text the installer places tells the main agent
each rule the scenarios describe, in the words the scenarios rely on.
"""

from __future__ import annotations

import re
import unittest

from concorde.distribution.build import build
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


def rendered(name: str) -> str:
    outputs = {output.path: output.content for output in build(REPOSITORY_ROOT).outputs}
    return re.sub(r"\s+", " ", outputs[f"generated/main-session/{name}.md"].decode())


class GuidanceTests(unittest.TestCase):
    def setUp(self):
        self.skill = rendered("skill")
        self.block = rendered("claude-md")

    @verifies("scenario.main-session.change-through-task")
    def test_changes_run_as_tasks_through_operations(self):
        self.assertIn(
            "Every change of Spec meaning or code behaviour runs as a task", self.skill
        )
        self.assertIn(
            "Never change Specs or code in the primary worktree yourself", self.skill
        )
        self.assertIn("concorde task open", self.skill)
        self.assertIn("in background Bash", self.skill)
        self.assertIn("concorde run", self.block)

    @verifies("scenario.main-session.parallel-tasks")
    def test_parallelism_only_between_non_overlapping_worktrees(self):
        self.assertIn(
            "Run tasks in parallel only in separate worktrees and only when their Modules and "
            "shared files do not overlap",
            self.skill,
        )

    @verifies("scenario.main-session.merge-delivered")
    def test_delivered_tasks_are_merged_without_asking(self):
        self.assertIn("without asking the developer for authorization", self.skill)
        self.assertIn("concorde task close <task> --merged", self.skill)
        self.assertIn("merge delivered task branches without asking", self.block)

    @verifies("scenario.main-session.ordinary-decision")
    def test_ordinary_decisions_are_made_recorded_and_reported(self):
        self.assertIn(
            "Decide design uncertainties of ordinary scope yourself", self.skill
        )
        self.assertIn(
            "Record the decision in the decision log and report it", self.skill
        )
        self.assertIn(
            "every result that is not `ok` and every decision you made without the developer",
            self.skill,
        )

    @verifies("scenario.main-session.major-decision")
    def test_major_decisions_are_escalated_with_their_evidence(self):
        self.assertIn(
            "Ask the developer before acting only when a decision has a major impact",
            self.skill,
        )
        self.assertIn("changes what a Module promises to its users", self.skill)
        self.assertIn("pass the escalation on in full", self.skill)

    @verifies("scenario.main-session.solve-issue")
    def test_issues_are_solved_by_ordinary_work(self):
        self.assertIn("Solve an Issue like any other work", self.skill)
        self.assertIn("close the Issue on that task's branch", self.skill)


if __name__ == "__main__":
    unittest.main()
