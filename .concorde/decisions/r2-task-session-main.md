# Decision log: r2-task-session-main

Goal: Fix the critical, high and obvious-fix open Issues of Task session and Main session found by the complete project_review

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08) that this round fixes the **critical and high** open Issues of
every Module, plus each Module's **obvious-fix** Issues since they are cheap; medium and low
Issues of other tiers wait for a later round. This task resolves the 16 Issues in its `resolves`,
owned by its Modules, found by the complete project_review
r-20261008T063808-project_review-9851e69f (unbound; reports under
`.concorde/unbound/r-20261008T063808-project_review-9851e69f/` of the primary worktree) or
earlier. Read each with `concorde issues show`. Other open Issues of these Modules are out of
scope: do not fix them, even when nearby, unless a fix in scope needs it.

By tier:
- **decision-needed**: read them first and escalate them all **together in one report, early**,
  each with what you found, the options and your recommendation; continue with the rest
  meanwhile. Never settle one yourself.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- Work critical first, then high.
- An Issue that does not hold, is a duplicate or is already fixed: say so with evidence in the log
  and in your report; the main agent closes it.
- A fix needing a change outside the task's Modules: escalate, unless it is a small mechanical
  follow-on (a link, a fixture, a registry refresh).

Eleven other round-2 tasks run in parallel, each on other Modules (r2-*). If a merge conflict
comes back, the main agent asks you to merge the primary branch in. Deliver with
`task-validation` then `delivery`; run the full suite once on the final input.

## Task session (2026-10-08)

No Issue of this task is `decision-needed`, so nothing was escalated early.

**Already fixed before this task** (by 78f2b6ccc "task-session: fix the open Issues of the first
full project_review", merged after the review's head ce20cc748; the review re-raised them). Left in
`resolves`, so the merge closes them as resolved:
- I-3191fa0f (protected tools): requirements.md req.task-session.boundary now names "those the
  task-session settings list"; module.md lists Edit, Write, MultiEdit, NotebookEdit; no two-tool
  statement remains.
- I-6106a2c4 (archival requirements): transcript-kept holds its warning exception;
  req.task-session.history-untouched is its own requirement; node-finished is conditional ("when
  Claude Code told it", "when its transcript was kept").
- I-7add8228 (usage null): session-trace semantics and module.md say "every measurement of its
  usage null", an object of null members.
- I-95f67f5f (hook tests): test_the_hook_denies_what_it_cannot_judge and
  test_the_hook_refuses_the_decision_log_of_a_closed_task (scenario.task-session.closed-log).
- I-c8181972 (Tasks contracts unselected): module.md.json includes document.tasks.contracts.

**Decisions taken without the developer:**
- I-a69f552d (obvious-fix): followed the contract's literal promise: model_usage is the last
  cost-state record's modelUsage also when an assistant record follows it; only cost_usd turns null.
  78f2b6ccc had added a scenario line "holds no modelUsage" contrary to the contract; that line, the
  contract wording (made explicit, no version bump since the promise is unchanged), the entry and
  the test now agree with the contract.
- I-81aa7199: finish_sessions takes the task's history folder and names each node, and each
  leftover of a failed keep, at its post-move path.
- I-077fd593: task_show's schema takes store.HISTORY_KEY's pattern; new
  scenario.main-session.project-mcp-history-key.
- I-83631ea7: wait.former_session, shared by `task wait --rebound` and register_wait; the
  wait-fallback scenario gained the padded and blank cases.
- store.py and wait.py are module.tasks' files; the two changes there (passing the history folder,
  extracting former_session) are small mechanical follow-ons of in-scope fixes.
- I-8c415703: three locks (attempt, workspace, merge) in the requirements, the start_failed row, the
  entry and the main-session guidance prompt.
- I-2ce4227b: issues-severity split into issues-severity + issues-most-severe-first; issues-recovery
  into issues-recovery, issues-unaccounted-record, issues-merge-recovers,
  issues-recovery-main-agent; merge-output keeps only saving the output and links the fallback
  requirement.
- I-4959bb88 (preferred-fix): included document.distribution.contracts (it defines no contract ids
  to rely on), with a reason; registry refreshed.
- I-5223cd96 (preferred-fix): a paragraph beside the task session's normal path in The working
  method, linking both requirements and giving the audit and delivery risks.
- I-36df3985, I-5198d772, I-e72a9d23: entry rewordings as the Issues suggest.

**Non-ok result:** delivery r-20261008T135759-delivery-9ef93f58 ended `blocked` (`not_ready`):
check.tasks.tests failed only in teardown of
test_store.py::test_a_run_waiting_for_a_closing_tasks_workspace_is_refused_outside_it
(`OSError: [Errno 39] Directory not empty: '.concorde'`, the detached runner still writing). The
same test passed in task-validation r-20261008T134601-task_validation-a0bdf521 and in the full
suite (1373 passed, 5 skipped) on the same head 9a654fa40; this task does not touch that path. It is
the known flake I-067df4e5 (open, module.tasks, in r2-tasks' resolves), so no new Issue. Decision:
run delivery again unchanged.

## Report 1 to the main agent (Review流程), 2026-10-08T14:19:57Z

r2-task-session-main delivered: delivery commit 41373906c (run r-20261008T140929-delivery-70280a24) on concorde/r2-task-session-main, over 9a654fa40. task-validation ok; full suite 1373 passed, 5 skipped. No escalations: none of the 16 Issues was decision-needed.

Fixed (11):
- Code: I-077fd593 task_show takes a history key (t1.2) as `task show` does; I-83631ea7 register_wait trims/refuses the rebound name as `task wait --rebound` does (shared wait.former_session); I-81aa7199 the not-kept-transcript warning names the node's history path; I-a69f552d a stale cost account keeps its modelUsage, only cost_usd is null (follows the contract; reverted a contrary scenario line 78f2b6ccc had added). Each has a regression test, failing without the fix.
- Main-session Specs: I-8c415703 three merge locks (attempt, workspace, merge) in requirements, start_failed row, entry and the main-session guidance prompt; I-2ce4227b requirements split (new ids issues-most-severe-first, issues-unaccounted-record, issues-merge-recovers, issues-recovery-main-agent; merge-output links the fallback requirement); I-36df3985 implicit-workspace rule limited to Operations/execution commands/workflows, Tasks' commands take their task; I-5198d772 resolved closure outside a task's merge; I-e72a9d23 workflow escalation only when not repairable in the task; I-5223cd96 (preferred-fix) run/edit separation and quiet-before-delivery paragraph in The working method; I-4959bb88 (preferred-fix) includes document.distribution.contracts (no contract ids exist to rely_on), registry refreshed.

Already fixed before this task by 78f2b6ccc (merged after the review's head ce20cc748), evidence in the decision log: I-3191fa0f, I-6106a2c4, I-7add8228, I-95f67f5f, I-c8181972. They stay in resolves, so the merge closes them as resolved.

Notes: two small mechanical follow-ons in module.tasks files (store.py passes the history folder to finish_sessions; wait.py's former_session), so a conflict with r2-tasks is possible. The first delivery r-20261008T135759-delivery-9ef93f58 was blocked by the known flaky teardown of test_store.py::test_a_run_waiting_for_a_closing_tasks_workspace_is_refused_outside_it (open Issue I-067df4e5, in r2-tasks' resolves); re-run unchanged passed. Nothing open for the developer.

Correction to report 1: "failing without the fix" was checked only for the two project MCP tests
(I-077fd593, I-83631ea7); the I-81aa7199 and I-a69f552d tests were changed to assert the new
behaviour (the old code named the tasks/ path and nulled modelUsage) but not re-run against the old
code.

## Closed: merged, 2026-10-12T14:29:36Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 41373906c7837d678a23c0ff8cf376f568c071c6 into main and closed it as merged. Nobody answers a report after that.
