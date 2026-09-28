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
        # Runs read the task worktree's workspace binding and never name the task.
        self.assertIn("`concorde task open` binds the task worktree", self.skill)
        self.assertIn(
            "reads that binding from the worktree it starts in and never names the task",
            self.skill,
        )
        self.assertIn("a second is refused with `workspace_busy`", self.skill)
        self.assertIn(
            "`concorde task-validation` shows what would block; `concorde delivery`",
            self.skill,
        )
        self.assertIn(
            "`concorde spec-validation` checks the Specs' structure", self.skill
        )
        self.assertNotIn("--task <task>", self.skill.split("## Issues", 1)[0])
        self.assertNotIn("concorde run validate", self.skill)
        self.assertNotIn("concorde run delivery", self.skill)

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
        self.assertIn("`escalations: []`", self.pi_session)
        self.assertIn("`commit: null`", self.pi_session)
        self.assertIn("`escalations` a nonempty array of the numbers", self.pi_session)
        self.assertIn("Always include all six fields", self.pi_session)
        self.assertIn(
            "Do not omit the unused field or use an empty string", self.pi_session
        )
        self.assertIn("its answer is the prompt of your next round", self.pi_session)
        self.assertNotIn("SendMessage", self.pi_session)
        self.assertIn("stage the paths you changed by name", self.pi_session)
        self.assertIn("Do not merge the task branch, close the task", self.pi_session)

    @verifies("scenario.main-session.task-session-workflow")
    def test_a_task_session_runs_workflows_in_no_ask_mode(self):
        for session in (self.session, self.pi_session):
            with self.subTest(session=session[:40]):
                self.assertIn(
                    'but only in `no-ask` mode (`"mode": "no-ask"` in its `args`): nobody '
                    "answers you at a decision point",
                    session,
                )
                self.assertIn(
                    "`.concorde/runs/workflows/<task>/reports/<n>.json` of the primary worktree",
                    session,
                )
                self.assertIn(
                    "copy its decisions and problems into the decision log", session
                )
                self.assertIn(
                    "give its decisions in your report to the main agent", session
                )
                self.assertIn(
                    "Escalate to the main agent what needs the developer: a result that is "
                    "not `ok` and that you cannot repair within the task, with "
                    "`--error-file` naming that report",
                    session,
                )
                self.assertIn(
                    "a decision of major impact among those the workflow took, which carries "
                    "no error, escalated naming no run or file, so that your link, with its "
                    "step, its options and your recommendation, is the whole chain",
                    session,
                )
        self.assertIn("with every decision of a workflow you ran", self.session)
        self.assertIn("with every decision of a workflow you ran", self.pi_session)
        self.assertIn(
            "with every workflow decision of major impact for the developer",
            self.pi_session,
        )

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
        self.assertIn(
            "In Claude Code, run it in background Bash (`run_in_background`) like a run",
            self.skill,
        )
        self.assertIn("in pi, run it with bash without a timeout", self.skill)

    @verifies("scenario.main-session.no-polling")
    def test_every_wait_wakes_or_blocks_once(self):
        self.assertIn("Never wait by polling, with `sleep` loops", self.skill)
        self.assertIn("start it with `--wait <seconds>`", self.skill)
        self.assertIn(
            "`concorde task session <task> --wait` in bash without a timeout",
            self.skill,
        )
        self.assertIn("never polling with `sleep`", self.block)
        self.assertIn(
            "Run Operations, `task-validation` and `delivery` in background Bash",
            self.session,
        )
        self.assertIn("Give bash no timeout for them", self.pi_session)
        for session in (self.session, self.pi_session):
            self.assertIn("Never wait for anything with `sleep` loops.", session)

    @verifies("scenario.main-session.merge-interrupted")
    def test_an_interrupted_merge_is_finished_first(self):
        skill = " ".join(self.skill.split())
        self.assertIn("fails with `merge_incomplete`", skill)
        self.assertIn(
            "Finish it before anything else, without asking the developer: run "
            "`concorde task merge <task> --resume`",
            skill,
        )
        self.assertIn(
            "Run `concorde task merge <task> --abort` instead when the refusal says the primary "
            "branch is not at the merge commit or `--resume` answers `not_resumable`",
            skill,
        )
        self.assertIn(
            "`merge_diverged` means the primary branch was changed by hand", skill
        )
        self.assertIn("discarding them is the developer's decision", skill)
        self.assertIn(
            "fails with `workspace_busy`, a run of that task outlasted the wait", skill
        )
        self.assertIn("run the command again with a longer `--wait`", skill)
        self.assertIn(
            "`concorde task merge <task> --resume`", " ".join(self.block.split())
        )
        for session in (self.session, self.pi_session):
            self.assertIn(
                "refused with `merge_incomplete` or `merge_busy`, a merge in the primary "
                "worktree is unfinished or still running",
                " ".join(session.split()),
            )

    @verifies("scenario.main-session.brownfield")
    def test_existing_code_is_adopted_through_the_brownfield_workflow(self):
        self.assertIn(
            "the `brownfield` workflow: open a task bound to the root Module",
            self.skill,
        )
        self.assertIn("start the workflow inside the task worktree", self.skill)
        self.assertIn("never names the task", self.skill)
        self.assertIn(
            "Ask the developer which **mode** to use unless they already said",
            self.skill,
        )
        self.assertIn(
            "put every point in `pending` to the developer at once", self.skill
        )
        self.assertIn("start the same workflow again with `answers`", self.skill)
        self.assertIn(".concorde/runs/workflows/<task>/reports/<n>.json", self.skill)
        self.assertIn(
            "copy the rendering's decisions and problems into the task's decision log "
            "yourself",
            self.skill,
        )
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
            "every result of the task's runs that is not `ok` and every decision you made "
            "without the developer",
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
        self.assertIn(
            "concorde task escalate <task> [--run <run-id>…] [--error-file <json>…]",
            self.skill,
        )
        self.assertIn(
            "A decision with major impact that no error carries, such as one a no-ask workflow "
            "that ended `ok` took, is escalated the same way naming no run, file or "
            "escalation: your link alone is then the whole chain.",
            self.skill,
        )

    @verifies("scenario.main-session.read-error-chain")
    def test_the_main_agent_reads_the_whole_error_chain(self):
        self.assertIn("carries an **error chain** in `error`", self.skill)
        self.assertIn("Read the whole chain before deciding", self.skill)

    @verifies("scenario.main-session.unbound-failure")
    def test_a_failed_unbound_run_reaches_the_developer_whole(self):
        self.assertIn(
            "The decision log and `concorde task escalate` belong to a task, so they cover the "
            "runs of a task. An unbound run belongs to none",
            self.skill,
        )
        self.assertIn(
            "show the developer its whole error chain as rendered", self.skill
        )
        self.assertIn("never a summary of it", self.skill)
        self.assertIn(
            "When the failure leads to work, open a task for that work and escalate in it with "
            "`--error-file .concorde/runs/<run-id>/result.json`",
            self.skill,
        )
        self.assertIn("`--run` names only runs of the task's own workspace", self.skill)
        self.assertIn(
            "show the developer the whole rendered chain of an unbound run that is not `ok`",
            self.block,
        )

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
            (
                "Run `concorde issues check` explicitly on the resolved records before "
                "`task-validation` and `delivery`"
            ),
            "a passing store check does not prove the closure is justified",
        ):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, issues)

    @verifies("scenario.main-session.choose-models")
    def test_the_developer_chooses_worker_models(self):
        self.assertIn("Workers run on pi, whatever program you are", self.skill)
        self.assertIn("`.concorde/worker-models.json`", self.skill)
        self.assertIn(
            "copies the primary worktree's file into the new task worktree", self.skill
        )
        self.assertIn("Change worker models only when the developer asks.", self.skill)
        self.assertIn("call the `concorde_configure_workers` tool", self.skill)
        self.assertIn(
            "For AI-driven changes, edit `.concorde/worker-models.json` directly",
            self.skill,
        )
        self.assertIn("Edits stay in a draft until Save", self.skill)
        self.assertIn("dirty exits offer Keep editing or Discard changes", self.skill)
        self.assertIn("including Ctrl-C", self.skill)
        self.assertIn("concorde configure-workers --show --json", self.skill)
        self.assertIn("concorde configure-workers --check", self.skill)
        self.assertIn("scripts/available_models.py --backend pi", self.skill)
        self.assertIn("custom/offline model names", self.skill)
        self.assertIn(
            "run it in a task worktree only when the developer asks to change a task that "
            "already exists",
            self.skill,
        )
        self.assertIn("`concorde configure-workers` command", self.block)
        self.assertNotIn("concorde run configure_workers", self.skill)
        self.assertIn("keyed by **worker id**", self.skill)
        self.assertIn("`reviewer1` to `reviewer5` and `chair`", self.skill)
        self.assertIn(
            "change the models workers use only when the developer asks", self.block
        )
        self.assertIn(
            "unless the worktree's `.concorde/worker-models.json`", self.skill
        )
        self.assertIn('Set `backend: "claude"`', self.skill)
        self.assertIn(
            "chosen backend must be installed when a worker launches", self.skill
        )
        for old in ("--allow-unlisted", "--candidates", "--unset", "--operation <op>"):
            self.assertNotIn(old, self.skill)

    @verifies("scenario.main-session.no-task-operations")
    def test_questions_and_reviews_may_run_without_a_task(self):
        self.assertIn(
            "Some Operations also run **unbound**, in a worktree without a binding such as "
            "the primary worktree",
            self.skill,
        )
        self.assertIn(
            "they change no Spec or code, since an unbound run launches only reading workers",
            self.skill,
        )
        self.assertIn(
            "They work on a throwaway checkout of that worktree's `HEAD`", self.skill
        )
        self.assertIn("uncommitted changes are not examined", self.skill)
        self.assertIn(
            "their result has `workspace` null and names the examined commit as `commit`",
            self.skill,
        )
        self.assertIn("a question or a review that does not justify a task", self.skill)
        self.assertIn("An `--input` of such a run must be unbound too", self.skill)
        self.assertIn("as an unbound Operation in the primary worktree", self.block)


if __name__ == "__main__":
    unittest.main()
