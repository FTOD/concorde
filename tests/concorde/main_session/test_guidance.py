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
        self.assertIn(
            "Never change Specs or code in the primary worktree, with one exception: a "
            "**small change**",
            self.skill,
        )
        self.assertIn(
            "only after you told the developer what you would change and why it is small, and "
            "the developer approved that specific change",
            self.skill,
        )
        self.assertIn("concorde task open", self.skill)
        self.assertIn(
            "Hand every task to a task session, even when there is only one", self.skill
        )
        self.assertIn("you never work inside a task worktree yourself", self.skill)
        self.assertNotIn("EnterWorktree", self.skill)
        self.assertNotIn("EnterWorktree", self.block)
        self.assertIn(
            "hand every task, even a single one, to a task session", self.block
        )
        for session in (self.session, self.pi_session):
            self.assertIn(
                "Inside the task worktree you may change Specs and code yourself",
                session,
            )
            self.assertIn(
                "from the task worktree with the worktree's own command, never the primary "
                "worktree's",
                session,
            )
        self.assertIn("in background Bash", self.skill)
        self.assertIn("`concorde_run` tool", self.skill)
        # Runs read the task worktree's workspace binding and never name the task.
        self.assertIn("`concorde task open` binds the task worktree", self.skill)
        self.assertIn(
            "reads that binding from the worktree it starts in and never names the task",
            self.skill,
        )
        self.assertIn("a second is refused with `workspace_busy`", self.skill)
        self.assertIn(
            "`concorde task-validation` shows what would block; `concorde delivery`",
            self.session,
        )
        self.assertIn(
            "`concorde spec-validation` checks the Specs' structure", self.skill
        )
        self.assertNotIn("--task <task>", self.skill.split("## Issues", 1)[0])
        self.assertNotIn("concorde run validate", self.skill)
        self.assertNotIn("concorde run delivery", self.skill)

    @verifies("scenario.main-session.split-into-sessions")
    def test_every_task_goes_to_a_task_session(self):
        self.assertIn(
            "concorde task session <task> --main <your session name>", self.skill
        )
        self.assertIn("Every task is worked by a task session", self.skill)
        self.assertIn("Stay in the primary worktree while any runs", self.skill)
        self.assertIn("record there the task's **brief**", self.skill)
        self.assertIn(
            "put all the others to the developer at once (AskUserQuestion in Claude Code), "
            "and then answer the session once with every answer",
            self.skill,
        )
        self.assertIn(
            "after recording its brief in the task's decision log", self.block
        )
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
            "When the task is delivered, or cannot go further without decisions that are not "
            "yours, send the main agent's session one message",
            self.session,
        )
        self.assertIn(
            "Record every escalation the task needs first. Then send the main agent's session "
            "one message",
            self.session,
        )
        self.assertNotIn("wait for its answer before continuing", self.session)
        self.assertIn(
            "Do not merge the task branch into the primary branch, close the task",
            self.session,
        )
        self.assertIn(
            "Read the task's decision log before you change anything", self.session
        )

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
        self.assertIn(
            "Record every escalation the task needs first, then end the round with a report "
            "naming all their numbers",
            self.pi_session,
        )
        self.assertIn(
            "Do not merge the task branch into the primary branch, close the task",
            self.pi_session,
        )

    @verifies("scenario.main-session.task-session-workflow")
    def test_a_task_session_runs_workflows_in_the_mode_of_its_brief(self):
        for session in (self.session, self.pi_session):
            with self.subTest(session=session[:40]):
                self.assertIn("in the mode the task's brief names", session)
                self.assertIn(
                    "`interactive`, also when the brief names no mode", session
                )
                self.assertIn(
                    "escalate every point in `pending` at once, with `--error-file` naming "
                    "its report",
                    session,
                )
                self.assertIn(
                    "start the same workflow again with `answers` mapping each step's base key",
                    session,
                )
                self.assertIn("**Never ask in place.**", session)
                self.assertIn(
                    "gather every decision the task still needs and escalate them together, "
                    "in one report, rather than one at a time",
                    session,
                )
                self.assertIn(
                    "`.concorde/tasks/<task>/workspace/workflow/reports/<n>.json` of the "
                    "primary worktree",
                    session,
                )
                self.assertIn(
                    "copy its decisions and problems into the decision log", session
                )
                self.assertIn(
                    "give its decisions in your report to the main agent", session
                )
                self.assertIn(
                    "Escalate a result that is not `ok` and that you cannot repair within the "
                    "task with `--error-file` naming that report",
                    session,
                )
                self.assertIn(
                    "Escalate a decision of major impact among those the workflow took, which "
                    "carries no error, naming no run or file, so that your link, with its "
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
        self.assertNotIn("leave the task worktree", self.skill)
        self.assertIn(
            "run `concorde task merge <task>` from the primary worktree", self.skill
        )
        self.assertIn("Never merge a task with `git merge` yourself", self.skill)
        self.assertIn("When it fails with `merge_busy`", self.skill)
        self.assertIn("merge delivered task branches without asking", self.block)
        self.assertIn(
            "In Claude Code, run it in background Bash (`run_in_background`) like a run",
            self.skill,
        )
        self.assertIn("in pi, run it with bash without a timeout", self.skill)

    @verifies("scenario.main-session.merge-conflict")
    def test_a_merge_conflict_goes_back_to_the_task_session(self):
        self.assertIn(
            "answer the task's session (start one again if it has ended) to merge the "
            "primary branch",
            self.skill,
        )
        self.assertIn(
            "run `task-validation` and `delivery` again and report", self.skill
        )
        for session in (self.session, self.pi_session):
            self.assertIn(
                "merge the primary branch it names into your task branch", session
            )
            self.assertIn("It is the only merge you make.", session)
        self.assertIn("merge the primary branch into its task branch", self.block)

    @verifies("scenario.main-session.small-change")
    def test_a_small_change_needs_the_developers_approval(self):
        self.assertIn(
            "a typo, a one-line fix or a wording correction, may be made directly there, but "
            "only after you told the developer what you would change and why it is small",
            self.skill,
        )
        self.assertIn("Without that approval, open a task.", self.skill)
        self.assertIn(
            "that the developer approved after you said what you would change",
            self.block,
        )

    @verifies("scenario.main-session.batched-decisions")
    def test_decisions_go_up_together_and_come_back_together(self):
        for session in (self.session, self.pi_session):
            self.assertIn(
                "never stop in the middle of the work to wait for one answer", session
            )
            self.assertIn(
                "carry on with every part of the work that does not depend on them",
                session,
            )
        self.assertIn(
            "A task never asks the developer in place: its session stops and escalates every "
            "decision it needs to you together",
            self.skill,
        )
        self.assertIn(
            "decide those your authority covers, put all the others to the developer at once",
            self.skill,
        )
        self.assertIn("a task never asks the developer in place", self.block)

    @verifies("scenario.main-session.no-polling")
    def test_every_wait_wakes_or_blocks_once(self):
        self.assertIn("Never wait by polling, with `sleep` loops", self.skill)
        self.assertIn("started with `--wait <seconds>`", self.skill)
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
        self.assertIn("have its task session run it", self.skill)
        self.assertIn(
            "the task's session starts it inside the task worktree", self.skill
        )
        self.assertIn("never names the task", self.skill)
        self.assertIn(
            "Ask the developer which mode to use unless they already said", self.skill
        )
        self.assertIn(
            "put the rest to the developer at once, with their options and recommendations",
            self.skill,
        )
        self.assertIn("it starts the same workflow again with them", self.skill)
        self.assertIn(
            ".concorde/tasks/<task>/workspace/workflow/reports/<n>.json", self.skill
        )
        self.assertIn(
            "The task session copies its decisions and problems into the task's decision log",
            self.skill,
        )
        self.assertIn("treat it like an Operation result", self.skill)
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
            "`--error-file .concorde/unbound/<run-id>/result.json`",
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
            "through the session working that task",
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
            "Git conflicts in Issue records are resolved in the task worktree",
            "preserve accepted reports unchanged",
            "document the decision about competing dispositions, retaining their evidence",
            "never to concatenate incompatible closes or invent reopenings",
            (
                "run `concorde issues check` explicitly on the resolved records before "
                "`task-validation` and `delivery`"
            ),
            "a passing store check does not prove the closure is justified",
        ):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, issues)

    @verifies("scenario.main-session.worker-configuration-required")
    def test_workers_run_only_on_the_models_the_configuration_enables(self):
        models = self.skill.split("## Worker models", 1)[1]
        for instruction in (
            "never takes a worker's model or reasoning level from your or the developer's own pi",
            "only credentials and pi's provider definitions come from there",
            "no worker runs without it",
            "`config_missing`",
            "The installer does not write it",
            "ask the developer which models workers may use",
            "commit it alone on the primary branch before any Operation runs",
            "the required `enabled_models`",
            "`model_not_enabled`",
            "`model_unresolved`, so give the `default` a model",
            "otherwise its model's own level in `enabled_models`",
            "goes into `enabled_models` too",
        ):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, models)
        self.assertNotIn("pi's default model", self.skill)
        self.assertIn("never on anyone's own pi or Claude Code settings", self.block)
        self.assertIn("ask the developer for its models", self.block)

    @verifies("scenario.main-session.choose-models")
    def test_the_developer_chooses_worker_models(self):
        self.assertIn("Workers run on pi, whatever program you are", self.skill)
        self.assertIn(
            "what the worktree's `.concorde/workers.json` chooses", self.skill
        )
        self.assertIn("The file is tracked by Git", self.skill)
        self.assertIn("A task carries the file of its base commit", self.skill)
        self.assertIn("Change worker models only when the developer asks", self.skill)
        self.assertIn("commit that file alone on the primary branch", self.skill)
        self.assertIn("reaches the primary branch when the task merges", self.skill)
        self.assertIn("there is no editor", self.skill)
        self.assertIn("scripts/available_models.py --backend pi", self.skill)
        self.assertIn("custom/offline model names", self.skill)
        self.assertIn("one entry per **worker id**", self.skill)
        self.assertIn("`reviewer1` to `reviewer5` and `chair`", self.skill)
        self.assertIn("`limits` of every worker launch", self.skill)
        self.assertIn(
            "change the models workers use only when the developer asks", self.block
        )
        self.assertIn("tracked `.concorde/workers.json`", self.block)
        self.assertIn('unless an entry sets `backend: "claude"`', self.skill)
        self.assertIn("The chosen backend must be installed then", self.skill)
        for old in (
            "configure-workers",
            "concorde_configure_workers",
            "/concorde-models",
            "worker-models.json",
        ):
            self.assertNotIn(old, self.skill)
            self.assertNotIn(old, self.block)
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
