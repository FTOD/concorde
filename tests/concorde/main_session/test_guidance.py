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
        session = self.session
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
        self.assertNotIn("concorde_run", self.skill)
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
            "put all the others to the developer at once (with AskUserQuestion), "
            "and then answer the session once with every answer",
            self.skill,
        )
        self.assertIn(
            "after recording its brief in the task's decision log", self.block
        )
        self.assertIn("naming its escalation as a cause", self.skill)
        self.assertIn("concorde task session", self.block)
        self.assertIn(
            "a background Claude Code session whose working directory", self.skill
        )
        self.assertNotIn("has no task sessions", self.skill)
        for text in (self.skill, self.block, self.session):
            self.assertNotIn("concorde_task_session", text)
            self.assertNotIn("in pi", text)

    @verifies("scenario.main-session.task-session-report")
    def test_a_task_session_records_its_report_and_follows_a_rebind(self):
        self.assertIn(
            "**Record it first**, in the task record and decision log: "
            '`concorde task report <task> --text "<the report>" [--escalation <n>…]`',
            self.session,
        )
        self.assertIn(
            "**Then send it** with the SendMessage tool, the same text, to that `main`",
            self.session,
        )
        self.assertIn("never from your first prompt", self.session)
        self.assertIn(
            "run `concorde task wait <task> --rebound <that name>` in background Bash",
            self.session,
        )
        self.assertIn("send the same report to that name, without", self.session)

    @verifies("scenario.main-session.reconcile-after-restart")
    def test_the_main_agent_rebinds_its_tasks_after_its_name_changed(self):
        self.assertIn("### When your session name changed", self.skill)
        self.assertIn(
            "`concorde task list --main <former name> --state open,active,delivered,merging`",
            self.skill,
        )
        self.assertIn("once a task has ended nobody answers its", self.skill.lower())
        self.assertIn("`concorde task rebind <task> --main <current name>`", self.skill)
        self.assertIn("whose `answer` is null", self.skill)
        self.assertIn("before anything else", self.skill.split("### When your", 1)[1])
        self.assertIn(
            '`concorde task answer <task> --report <n>… --text "<your answer>"`',
            self.skill,
        )
        self.assertIn("`concorde task rebind`", self.block)
        self.assertIn("recording each answer with `concorde task answer`", self.block)

    @verifies("scenario.main-session.task-session-role")
    def test_a_task_session_stays_within_its_task(self):
        self.assertIn("You are a task session", self.session)
        self.assertIn("with the worktree's own command", self.session)
        self.assertIn("concorde task escalate <task> --by task-session", self.session)
        self.assertIn("SendMessage", self.session)
        self.assertIn(
            "When the task is delivered, or cannot go further without decisions that are not "
            "yours, report to the main agent",
            self.session,
        )
        self.assertIn(
            "Record every escalation the task needs first. Then report them all at once",
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

    @verifies("scenario.main-session.task-session-prepares-workers")
    def test_a_task_session_creates_and_binds_new_files_before_a_worker(self):
        self.assertIn("**Prepare the workers' environment.**", self.session)
        self.assertIn(
            "such as one an `understand` plan lists in `new_files`", self.session
        )
        self.assertIn(
            "create it yourself before you launch the worker that fills it",
            self.session,
        )
        self.assertIn(
            "give it the least content its format needs to be valid", self.session
        )
        self.assertIn("`entries` of the right realization", self.session)
        self.assertIn("commit both together", self.session)
        self.assertIn("The task session prepares the workers' environment", self.skill)
        for text in (self.session, self.skill):
            self.assertIn("creates the delivery commit on the task branch", text)
            self.assertNotIn("commits the result on the task branch", text)

    @verifies("scenario.main-session.task-session-plan-review")
    def test_a_task_session_leads_the_review_of_its_plan(self):
        session = self.session
        self.assertIn("**Have your plan reviewed when it deserves it.**", session)
        self.assertIn("`plan_review` is optional", session)
        self.assertIn("Write the plan yourself", session)
        self.assertIn("delete that file before `task-validation`", session)
        self.assertIn("answer **every** finding", session)
        self.assertIn(
            "run it again with the previous run as `--input` and the answers", session
        )
        self.assertIn("until the verdict is `accepted`", session)
        self.assertIn(
            "A finding the reviewer maintains after you rejected it, and that you still "
            "reject, is a disagreement: do not run again on it, escalate it",
            session,
        )
        self.assertIn("concorde run plan_review --plan <file>", self.skill)
        self.assertIn(
            "optionally `plan_review` of the plan the task session writes", self.skill
        )
        self.assertIn("`reviewer` for `plan_review`", self.skill)

    @verifies("scenario.main-session.task-session-workflow")
    def test_a_task_session_runs_workflows_in_the_mode_of_its_brief(self):
        session = self.session
        self.assertIn("in the mode the task's brief names", session)
        self.assertIn("`interactive`, also when the brief names no mode", session)
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
        self.assertIn("copy its decisions and problems into the decision log", session)
        self.assertIn("give its decisions in your report to the main agent", session)
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
        self.assertIn(
            "with every workflow decision of major impact for the developer",
            self.session,
        )
        self.assertIn("as the installed `/concorde-<name>` workflow", self.session)

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
            "merge it from the primary worktree without asking the developer for "
            "authorization: with the project MCP server's `task_merge`",
            self.skill,
        )
        self.assertIn(
            "or with `concorde task merge <task>` in background Bash", self.skill
        )
        self.assertIn("Never merge a task with `git merge` yourself", self.skill)
        self.assertIn("runs `concorde spec-validation` there", self.skill)
        self.assertIn("merge delivered task branches without asking", self.block)

    @verifies("scenario.main-session.merge-command")
    def test_the_merge_command_runs_in_the_background(self):
        self.assertIn("It waits up to `--wait` seconds", self.skill)
        self.assertIn(
            "Run it in background Bash (`run_in_background`) like a run", self.skill
        )
        self.assertIn(
            "When it fails with `merge_busy`, another session's merge outlasted the wait: "
            "run it again.",
            self.skill,
        )
        self.assertIn(
            "fails with `workspace_busy`, a run of that task outlasted the wait",
            self.skill,
        )
        self.assertIn("run the command again with a longer `--wait`", self.skill)

    @verifies("scenario.main-session.merge-through-server")
    def test_a_busy_task_merge_is_retried_after_a_registered_wait(self):
        self.assertIn(
            "merges a delivered task without ever waiting for a lock", self.skill
        )
        self.assertIn(
            "or is refused at once with `workspace_busy` or `merge_busy` naming who holds "
            "the busy one",
            self.skill,
        )
        self.assertIn(
            "register a wait for that lock with `register_wait` (or, without a channel, run "
            "the `concorde task wait` command it returns in background Bash) and call "
            "`task_merge` again once you are woken: you may be refused again.",
            self.skill,
        )

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
        session = self.session
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
        session = self.session
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
        self.assertIn("never polling with `sleep`", self.block)
        self.assertIn(
            "Run Operations, `task-validation` and `delivery` in background Bash",
            self.session,
        )
        session = self.session
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
            "`concorde task merge <task> --resume`", " ".join(self.block.split())
        )
        session = self.session
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

    def issues(self):
        skill = self.skill.split("## Issues", 1)[1].split("## Worker models", 1)[0]
        session = self.session.split("## Issues", 1)[1].split("## Report", 1)[0]
        return skill, session

    @verifies("scenario.main-session.record-issue")
    def test_sessions_inspect_before_they_record_through_the_server(self):
        skill, session = self.issues()
        for text, instruction in (
            (skill, "Read `issue_list` and `issue_show` first"),
            (skill, "reopen a closed match before appending"),
            (skill, "Repeating a creation creates another Issue"),
            (skill, "`description`, `impact`, `basis` and `evidence`"),
            (skill, "it never writes an Issue record from Bash"),
            (session, "never from Bash"),
            (session, "read and write them only with the project MCP server's"),
            (session, "append to the Issue that already tracks it"),
            (session, "carries its `tier`"),
        ):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, text)

    @verifies("scenario.main-session.issue-tiers")
    def test_the_tier_decides_who_fixes_an_issue(self):
        skill, session = self.issues()
        for text, instruction in (
            (skill, "a review Operation only reports"),
            (skill, "it fixes `obvious-fix` and `preferred-fix` Issues itself"),
            (skill, "escalates a `decision-needed` Issue, naming it by its identity"),
            (skill, "it blocks nothing"),
            (session, "fix an `obvious-fix` Issue yourself"),
            (session, "say in your report which fix you chose and why"),
            (session, "never settle a `decision-needed` Issue: escalate it"),
        ):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, text)

    @verifies("scenario.main-session.review-issues")
    def test_a_reviews_issues_are_handled_by_their_tier(self):
        skill, session = self.issues()
        for text, instruction in (
            (session, "**After a review.**"),
            (session, "report every finding themselves, as an Issue"),
            (session, "(`earlier_issues.carried`)"),
            (session, "(`earlier_issues.resolved`)"),
            (session, "`implement` work of your task, never the review's"),
            (session, "`concorde task resolve` when your task fixed it"),
            (session, "close with `issue_close` as `resolved`"),
            (skill, "reports each of its findings as an Issue"),
            (skill, "closes the resolved ones, through its task when the task fixed them"),
        ):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, text)

    @verifies("scenario.main-session.solve-issue")
    def test_a_fixed_issue_closes_with_its_tasks_merge(self):
        skill, session = self.issues()
        self.assertIn("Solve an Issue like any other work", skill)
        self.assertIn("--resolves <issue>[,<issue>…]", skill)
        self.assertIn("`task_resolve`", skill)
        self.assertIn(
            "the merge closes each Issue the task resolves as `resolved`", skill
        )
        self.assertIn("Starting, fixing or delivering the task changes no Issue", skill)
        self.assertIn("Never close an Issue you fixed", session)
        self.assertIn("concorde task resolve <task> <issue>…", session)

    @verifies("scenario.main-session.issue-system-failure")
    def test_failures_of_the_issue_system_are_never_issues(self):
        skill, session = self.issues()
        self.assertIn("Never record a failure of the Issue system itself", skill)
        self.assertIn(
            "its error chain in the task's decision log and escalation", skill
        )
        self.assertIn(
            "is a failure of the Issue system itself: never report it as an Issue",
            session,
        )

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
            "**project model name** that depends on no installation",
            "never goes into the file",
            "`~/.config/concorde/models.json`",
            "`CONCORDE_MODEL_MAP`",
            "is never committed",
            "write or change it only when the developer asks or agrees",
            "tell them the entry the map needs",
            "`model_unmapped`",
            "`model_map_missing`",
            "`model_map_invalid`",
            "the project model name is never used as the id",
            "`schema_version: 2`",
        ):
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, models)
        # The configuration's example names project model names only.
        example = models.split("```json")[2].split("```")[0]
        self.assertIn('"gpt-6-astra"', example)
        self.assertNotIn("local-openai/", example)
        self.assertNotIn("pi's default model", self.skill)
        self.assertIn("never on anyone's own Claude Code or pi settings", self.block)
        self.assertIn("untracked model map", self.block)
        self.assertIn("ask the developer for its models", self.block)

    @verifies("scenario.main-session.choose-models")
    def test_the_developer_chooses_worker_models(self):
        self.assertIn("Workers run on pi, although you run on Claude Code", self.skill)
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
        self.assertIn("`reviewer1` to `reviewer5`, `architect1`, `architect2` and `chair`", self.skill)
        self.assertIn("`limits` of every worker launch", self.skill)
        self.assertIn(
            "change the models workers use only when the developer asks", self.block
        )
        self.assertIn("tracked `.concorde/workers.json`", self.block)
        self.assertIn('unless an entry sets `backend: "claude"`', self.skill)
        self.assertIn(
            "an entry that only chooses a backend keeps the model and level it inherits",
            self.skill,
        )
        self.assertNotIn(
            "afresh", self.skill.split("## Worker models", 1)[1].split("## ", 1)[0]
        )
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


class ProjectMcpGuidanceTests(unittest.TestCase):
    @verifies("scenario.main-session.project-mcp-guidance")
    def test_the_guidance_says_how_to_start_with_the_server_and_when_to_use_it(self):
        skill, block = rendered("skill"), rendered("claude-md")
        session = rendered("task-session")
        self.assertIn(
            "claude --dangerously-load-development-channels server:concorde", skill
        )
        self.assertIn("--dangerously-load-development-channels server:concorde", block)
        self.assertIn(
            "with the project MCP server's `task_merge`, which returns at once", skill
        )
        self.assertIn("`register_wait`", skill)
        self.assertIn("a research preview", skill)
        self.assertIn(
            "run that command in background Bash, which wakes you when it returns",
            skill,
        )
        self.assertIn(
            "when you are woken for a lock, ask for it again, and you may be refused again",
            skill,
        )
        self.assertIn("The `concorde` commands stay the source of truth", skill)
        self.assertIn("you never merge or close your task", session)
        self.assertIn("A background session is never woken by channel events", session)
        self.assertIn(
            "Task sessions receive the server too, but without a channel", skill
        )


if __name__ == "__main__":
    unittest.main()
