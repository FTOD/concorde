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
        self.session = rendered("task-session")

    @verifies("scenario.main-session.change-through-task")
    def test_changes_run_as_tasks_inside_their_worktree(self):
        self.assertIn(
            "Every change of Spec meaning or code behaviour runs as a task", self.skill
        )
        self.assertIn("Never change Specs or code in the primary worktree.", self.skill)
        self.assertIn("concorde task open", self.skill)
        self.assertIn("enter its worktree with the EnterWorktree tool", self.skill)
        self.assertIn(
            "Inside the task worktree you may change Specs and code yourself",
            self.skill,
        )
        self.assertIn("in background Bash", self.skill)
        self.assertIn(
            "from the task worktree with the worktree's own command, never the primary "
            "worktree's",
            self.skill,
        )
        self.assertIn("with that worktree's own copy", self.block)

    @verifies("scenario.main-session.split-into-sessions")
    def test_split_work_goes_to_task_sessions(self):
        self.assertIn(
            "concorde task session <task> --main <your session name>", self.skill
        )
        self.assertIn("You are inside at most one task at a time.", self.skill)
        self.assertIn("stay in the primary worktree while any runs", self.skill)
        self.assertIn("naming its escalation as a cause", self.skill)
        self.assertIn("concorde task session", self.block)

    @verifies("scenario.main-session.task-session-role")
    def test_a_task_session_stays_within_its_task(self):
        self.assertIn("You are a task session", self.session)
        self.assertIn("with the worktree's own command", self.session)
        self.assertIn("concorde task escalate <task> --by task-session", self.session)
        self.assertIn("SendMessage", self.session)
        self.assertIn(
            "When the task is delivered, or cannot go further, send the main agent's session",
            self.session,
        )
        self.assertIn("Do not merge the task branch, close the task", self.session)

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
        self.assertIn("leave the task worktree if you are in it", self.skill)
        self.assertIn("run `concorde validate` there", self.skill)
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
        self.assertIn(
            "never replace the chain with your own summary: add your link on top of it",
            self.skill,
        )
        self.assertIn("concorde task escalate <task> --run <run-id>", self.skill)

    @verifies("scenario.main-session.read-error-chain")
    def test_the_main_agent_reads_the_whole_error_chain(self):
        self.assertIn("carries an **error chain** in `error`", self.skill)
        self.assertIn("Read the whole chain before deciding", self.skill)

    @verifies("scenario.main-session.solve-issue")
    def test_issues_are_solved_by_ordinary_work(self):
        self.assertIn("Solve an Issue like any other work", self.skill)
        self.assertIn("close the Issue on that task's branch", self.skill)


if __name__ == "__main__":
    unittest.main()
