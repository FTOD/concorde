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
        self.pi_session = rendered("task-session-pi")

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
        self.assertIn("`concorde_run` tool", self.skill)
        self.assertIn("runs the task worktree's own `concorde` there", self.skill)
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
        self.assertIn("inside at most one task at a time", self.skill)
        self.assertIn("stay in the primary worktree while any runs", self.skill)
        self.assertIn("naming its escalation as a cause", self.skill)
        self.assertIn("concorde task session", self.block)
        self.assertIn("call the `concorde_task_session` tool with the task", self.skill)
        self.assertIn("Answer with the tool's `answer`", self.skill)
        self.assertIn("so it always runs on your program", self.skill)
        self.assertNotIn("has no task sessions", self.skill)
        self.assertIn("the `concorde_task_session` tool in pi", self.block)

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

    @verifies("scenario.main-session.pi-task-session-role")
    def test_a_pi_task_session_ends_each_round_with_a_report(self):
        self.assertIn("You are a task session", self.pi_session)
        self.assertIn("with the worktree's own command", self.pi_session)
        self.assertIn("in the foreground with bash", self.pi_session)
        self.assertIn(
            "concorde task escalate <task> --by task-session", self.pi_session
        )
        self.assertIn("End every round by calling `concorde_report`", self.pi_session)
        self.assertIn("with `commit` the delivery commit", self.pi_session)
        self.assertIn("with `escalations` the numbers", self.pi_session)
        self.assertIn("its answer is the prompt of your next round", self.pi_session)
        self.assertNotIn("SendMessage", self.pi_session)
        self.assertIn("stage the paths you changed by name", self.pi_session)
        self.assertIn("Do not merge the task branch, close the task", self.pi_session)

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
        self.assertIn(
            "run `concorde task merge <task>` from the primary worktree", self.skill
        )
        self.assertIn("Never merge a task with `git merge` yourself", self.skill)
        self.assertIn("When it fails with `merge_busy`", self.skill)
        self.assertIn(
            "merge the primary branch into the task branch, resolve the conflicts",
            self.skill,
        )
        self.assertIn("merge delivered task branches without asking", self.block)

    @verifies("scenario.main-session.brownfield")
    def test_existing_code_is_adopted_through_the_brownfield_workflow(self):
        self.assertIn(
            "the `brownfield` workflow: open a task bound to the root Module",
            self.skill,
        )
        self.assertIn(
            "start the workflow from the primary worktree and stay there", self.skill
        )
        self.assertIn(
            "Ask the developer which **mode** to use unless they already said",
            self.skill,
        )
        self.assertIn(
            "put every point in `pending` to the developer at once", self.skill
        )
        self.assertIn("start the same workflow again with `answers`", self.skill)
        self.assertIn(".concorde/tasks/<task>.workflow.json", self.skill)
        self.assertIn("Treat it like an Operation result", self.skill)
        self.assertIn("never configured automatically", self.skill)
        self.assertIn("`survey`", self.skill)
        self.assertIn(
            "run a task that follows a known procedure as its workflow", self.block
        )

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

    @verifies("scenario.main-session.record-issue")
    def test_rendered_issue_workflow_distinguishes_inspection_from_writes(self):
        issues = self.skill.split("## Issues", 1)[1].split("## Worker models", 1)[0]
        for instruction in (
            "neither records Issues automatically",
            "`concorde issues list` (open and closed Issues) and `show <id>` first",
            "Run every Issue write (`report`, `close`, `reopen`) in a task worktree",
            "concorde issues report --file <report.json> --task <task>",
            "keep its receipt and revision",
            "`--task` records provenance only: it does not choose the worktree",
            "`issue_id` and current `expected_revision` from `show`",
            "Repeating a creation command creates another Issue",
            "Reopen a closed match before appending",
            "`close` and `reopen` take no `--task`",
        ):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, issues)

    @verifies("scenario.main-session.unmerged-issue")
    def test_rendered_handoff_survives_task_worktree_removal(self):
        issues = self.skill.split("## Issues", 1)[1].split("## Worker models", 1)[0]
        for instruction in (
            "Before ending a task without merging",
            "record it through the command in a subsequent task",
            "leave a handoff in the current task's decision log",
            "Issue identity, branch and commit when available",
            "remaining work and durable locations of the report and evidence",
            "Preserve needed uncommitted material before removal",
            "Closing retains the branch and decision log",
            "forced removal can discard uncommitted material",
            "a log entry alone does not publish them",
        ):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, issues)

    @verifies("scenario.main-session.issue-conflict")
    def test_rendered_conflict_guidance_requires_both_judgment_and_store_check(self):
        issues = self.skill.split("## Issues", 1)[1].split("## Worker models", 1)[0]
        for instruction in (
            "Resolve Git conflicts in Issue records in the task worktree",
            "Preserve accepted reports unchanged",
            "document the decision about competing dispositions, retaining their evidence",
            "Never concatenate incompatible closes or invent reopenings",
            "Run `concorde issues check` explicitly on the resolved records before `validate` and `delivery`",
            "a passing store check does not prove the closure is justified",
        ):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, issues)

    @verifies("scenario.main-session.choose-models")
    def test_the_developer_chooses_worker_models(self):
        self.assertIn("Workers run on your own agent program", self.skill)
        self.assertIn("`.concorde/worker-models.json`", self.skill)
        self.assertIn(
            "copies the primary worktree's file into the new task worktree", self.skill
        )
        self.assertIn("Change worker models only when the developer asks.", self.skill)
        self.assertIn("call the `concorde_configure_workers` tool", self.skill)
        self.assertIn(
            "run `concorde run configure_workers` and ask with the AskUserQuestion tool",
            self.skill,
        )
        self.assertIn(
            "pass `--task <task>` only when the developer asks to change a task that "
            "already exists",
            self.skill,
        )
        self.assertIn("per worker role", self.skill)
        self.assertIn(
            "change the models workers use only when the developer asks", self.block
        )
        self.assertIn(
            "unless the worktree's `.concorde/worker-models.json`", self.skill
        )
        self.assertIn("edit the `backend` section of the file yourself", self.skill)
        self.assertIn("Both programs must be installed", self.skill)

    @verifies("scenario.main-session.no-task-operations")
    def test_questions_and_reviews_may_run_without_a_task(self):
        self.assertIn("Some Operations also run without a task", self.skill)
        self.assertIn(
            "they change no Spec or code, since a run without a task launches only reading "
            "workers",
            self.skill,
        )
        self.assertIn("a question or a review that does not justify a task", self.skill)
        self.assertIn("they run only from the primary worktree", self.skill)
        self.assertIn("Inside a task's worktree, always pass `--task`", self.skill)
        self.assertIn("as an Operation without `--task`", self.block)


if __name__ == "__main__":
    unittest.main()
