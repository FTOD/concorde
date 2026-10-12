# Decision log: r2-e2e

Goal: Fix the critical, high and obvious-fix open Issues of E2E, Headless sessions, SWE-bench cases, Dogfood scenarios and Dogfooding found by the complete project_review, the critical first (I-1a2535db I-6727657f I-9e8a963d)

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08) that this round fixes the **critical and high** open Issues of
every Module, plus each Module's **obvious-fix** Issues since they are cheap; medium and low
Issues of other tiers wait for a later round. This task resolves the 24 Issues in its `resolves`,
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

## Escalated to the main agent, 2026-10-08T13:38:57Z

- **task-session** task session (task r2-e2e): `headless_detached_survival_scope`
  I-4915a01cdb5d5d5fa8dd0e76fd40270b (decision-needed/high, module.headless-sessions): specs/concorde/e2e/sessions/module.md ('What the session is told') promises unconditionally that a detached run outlives the round and wakes the session when it ends. Execution's #detached-namespace says a runner detached from a sandboxed Bash call is killed when that call returns, and that a main agent's own session may be sandboxed. scripts/e2e/sessions.py runs each round as 'claude -p ... --allowedTools ...' with the user's settings, so whether its Bash is sandboxed depends on the machine (no sandbox in ~/.claude/settings.json here). The wait already treats a run whose runner has gone as ended (sessions.py _ended/_alive), but the unsettled-run scenario excludes a run whose runner is already gone at the round's end, so such a run produces no wake at all.
  Not handled here (decision): Choosing between guaranteeing a launch environment and narrowing the promise changes what Headless sessions promises and touches Execution's detached-run contract; the task brief reserves decision-needed Issues.
  Options: A: Headless sessions guarantees the environment: each round runs with Claude Code's Bash sandbox disabled (e.g. --settings with sandbox.enabled false), stated in the session setup, so the detached-run promise holds as written.; B: Narrow the promise: a detached run outlives the round only when its runner was started outside a sandboxed Bash call (e.g. through the project MCP server or an unsandboxed session); state that prerequisite, and say that a detached run whose runner is gone by the round's end is reported in the wake message as ended without a result instead of being silently dropped.; C: Narrow the promise only (B's prerequisite), keep silently dropping a run whose runner is gone.
  Recommendation: A. A headless session is the test stand-in for the developer's interactive main session; making its rounds unsandboxed keeps the wake behaviour deterministic across machines and matches how task sessions run (req.task-session.no-sandbox). It is one argument in sessions.command and one sentence in the Spec plus a requirement.

```json
{
  "level": "task-session",
  "actor": "task session (task r2-e2e)",
  "code": "headless_detached_survival_scope",
  "detail": "I-4915a01cdb5d5d5fa8dd0e76fd40270b (decision-needed/high, module.headless-sessions): specs/concorde/e2e/sessions/module.md ('What the session is told') promises unconditionally that a detached run outlives the round and wakes the session when it ends. Execution's #detached-namespace says a runner detached from a sandboxed Bash call is killed when that call returns, and that a main agent's own session may be sandboxed. scripts/e2e/sessions.py runs each round as 'claude -p ... --allowedTools ...' with the user's settings, so whether its Bash is sandboxed depends on the machine (no sandbox in ~/.claude/settings.json here). The wait already treats a run whose runner has gone as ended (sessions.py _ended/_alive), but the unsettled-run scenario excludes a run whose runner is already gone at the round's end, so such a run produces no wake at all.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Choosing between guaranteeing a launch environment and narrowing the promise changes what Headless sessions promises and touches Execution's detached-run contract; the task brief reserves decision-needed Issues."
  },
  "options": [
    "A: Headless sessions guarantees the environment: each round runs with Claude Code's Bash sandbox disabled (e.g. --settings with sandbox.enabled false), stated in the session setup, so the detached-run promise holds as written.",
    "B: Narrow the promise: a detached run outlives the round only when its runner was started outside a sandboxed Bash call (e.g. through the project MCP server or an unsandboxed session); state that prerequisite, and say that a detached run whose runner is gone by the round's end is reported in the wake message as ended without a result instead of being silently dropped.",
    "C: Narrow the promise only (B's prerequisite), keep silently dropping a run whose runner is gone."
  ],
  "recommendation": "A. A headless session is the test stand-in for the developer's interactive main session; making its rounds unsandboxed keeps the wake behaviour deterministic across machines and matches how task sessions run (req.task-session.no-sandbox). It is one argument in sessions.command and one sentence in the Spec plus a requirement.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-08T13:39:05Z

- **task-session** task session (task r2-e2e): `repair_factual_basis_scope`
  I-d553bd574811544c980f378e3e781683 (decision-needed/high, module.swe-bench-cases): specs/concorde/e2e/cases/module.md ('Repairing the adopted Specs') says the repair's specify run 'keeps every promise true to the code' and turns only intent decisions into open questions. But the specify worker cannot read implementation contents (req.specification.no-code) and its validation is structural, so nothing in the repair establishes a code fact that a review finding asks to add; the guarantee has no basis.
  Not handled here (decision): Which evidence the repair may rely on changes what repair-specs promises (and possibly which Operation it runs); the task brief reserves decision-needed Issues.
  Options: A: Restrict the promise: the repair changes only what the review's findings and the existing Specs justify; a repair that needs a fact about the code (not only an intent decision) is left as an open question, and the round still completes, reporting those open questions with the second review's findings.; B: Give the repair code-derived evidence: run code_to_spec (which reads the code) instead of specify for the repair, so new promises come from the code itself.; C: Keep specify but add an understand run whose plan (read from the code) is handed to specify as input evidence.
  Recommendation: A. It is a Spec-only narrowing that matches what specify can actually do today, keeps the round's existing steps and scenarios, and leaves B/C as a later improvement if repairs prove too weak.

```json
{
  "level": "task-session",
  "actor": "task session (task r2-e2e)",
  "code": "repair_factual_basis_scope",
  "detail": "I-d553bd574811544c980f378e3e781683 (decision-needed/high, module.swe-bench-cases): specs/concorde/e2e/cases/module.md ('Repairing the adopted Specs') says the repair's specify run 'keeps every promise true to the code' and turns only intent decisions into open questions. But the specify worker cannot read implementation contents (req.specification.no-code) and its validation is structural, so nothing in the repair establishes a code fact that a review finding asks to add; the guarantee has no basis.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Which evidence the repair may rely on changes what repair-specs promises (and possibly which Operation it runs); the task brief reserves decision-needed Issues."
  },
  "options": [
    "A: Restrict the promise: the repair changes only what the review's findings and the existing Specs justify; a repair that needs a fact about the code (not only an intent decision) is left as an open question, and the round still completes, reporting those open questions with the second review's findings.",
    "B: Give the repair code-derived evidence: run code_to_spec (which reads the code) instead of specify for the repair, so new promises come from the code itself.",
    "C: Keep specify but add an understand run whose plan (read from the code) is handed to specify as input evidence."
  ],
  "recommendation": "A. It is a Spec-only narrowing that matches what specify can actually do today, keeps the round's existing steps and scenarios, and leaves B/C as a later improvement if repairs prove too weak.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-08T13:39:10Z

Early escalation of the task's two decision-needed Issues (work on the other 22 continues meanwhile).

1. I-4915a01c (headless-sessions, high) — detached-run survival vs Claude Code's Bash sandbox. Options: A) rounds run with the sandbox disabled so the promise holds; B) narrow the promise to runners started outside a sandboxed call and report a run whose runner is gone in the wake; C) narrow only. Recommendation: A.

2. I-d553bd57 (swe-bench-cases, high) — repair-specs promises 'every promise true to the code' though specify cannot read code. Options: A) restrict: change only what findings and Specs justify, leave code-fact gaps as open questions, round still completes; B) run code_to_spec instead of specify; C) add an understand run whose plan feeds specify. Recommendation: A.

Full chains are escalations 1 and 2 in the decision log.

It carries escalation(s) 1, 2.

## Answer to report(s) 1 of the task session, 2026-10-08T13:39:31Z

Escalations 1-2 (main agent): 1 A — each headless round runs with Claude Code's Bash sandbox disabled through the round's own --settings (never the user's settings file), stated in the session setup with a requirement, so the detached-run promise holds; this follows the developer's 2026-10-01 decision that task sessions run unsandboxed, and headless sessions only run in test projects under /tmp/concorde-e2e. Also report in the wake a detached run whose runner is gone as ended without a result instead of dropping it (B's second half), since that costs little and removes a silent case. 2 A — restrict repair-specs' promise to what the review's findings and the existing Specs justify; a repair needing a code fact is left as an open question, reported with the second review's findings; the round still completes.

## Task session decisions (2026-10-08)

- **I-1a2535db (critical, preferred-fix)**: chose a small pytest plugin, written into grading's
  scratch directory and loaded with `-p`, that records every report under its full node identity
  (JSON lines), over repairing the summary-line regex: the short summary cannot carry a SKIPPED
  test's identity at all. Grading also now counts statuses as SWE-bench's own
  `swebench/harness/grading.py` does (XFAIL passes; a skipped PASS_TO_PASS test is maintained; a
  listed identity truncated inside its brackets prefix-matches when its candidates agree), since
  the Spec promises "the way SWE-bench does" and SWE-bench's datasets hold such truncated ids.
  New requirement `req.swe-bench-cases.graded-like-swe-bench` and scenario
  `scenario.swe-bench-cases.grade-statuses`. Commit a528a485d.
- **I-2853f9f7 (high, preferred-fix)**: Cases now includes `references/swe-bench/swebench/harness/`
  and `references/swe-bench/docs/guides/datasets.md` as external material and states the supported
  scope (pytest instances only). Same commit.
- **I-3f3d2610, I-09c7ff1a (obvious-fix)**: PYTHONPATH keeps the caller's entries after the
  worktree directories; a timed-out run writes its whole output to the log before raising and the
  error names the log. Same commit.
- **Already fixed before this task** (the review ran on head ce20cc748, which lacks commit
  1bcce36d9 "e2e, dogfood: fix the Issues of the first project review", now on main):
  - I-6727657f (critical): `owners.new_run` takes only a run whose runner (`host_pid`) descends
    from the case's launcher; test `test_a_competing_run_is_never_judged_as_the_cases_run`.
  - I-9e8a963d (critical): `owners.phase` sets the baseline with `turn_end`, the time the
    launching turn's result event was read by the session's reader thread; test
    `test_the_judged_time_starts_when_the_launching_turn_ended`.
  - I-8f1b4967: `owner_prompt` uses `shlex.quote`; test `test_the_owner_is_told_the_worktree_as_one_shell_word`.
  - I-7340749c: the driver's node launch and the unowned Popen raise `command_failed`; tests
    `test_a_command_that_cannot_be_started_is_a_command_failure`,
    `test_the_unowned_launch_that_cannot_start_is_a_command_failure`.
  - I-33d21d3b: `common.test_directory` refuses a name that is not one directory name
    (`invalid_name`) before cloning; test `test_a_name_that_is_not_one_directory_name_is_refused`.
  The main agent may close these five; the task does not list them as resolved by its own change.
- **Headless sessions** (commit 71e0f53ff):
  - I-4915a01c, as the main agent answered (A + B's second half): `sessions.command` passes
    `--settings '{"sandbox": {"enabled": false}}'` on every round (main and workflow rounds
    alike, since both may detach runs), new `req.headless-sessions.sandbox-off`; an unfinished run
    whose runner no longer holds its run lock is unsettled as `runner_gone` (re-reading the
    progress file after the lock probe to avoid a finish race) and the wake names it as ended
    without a result. Live sessions (`live.py`) are left as they are: the owners case launches
    with `--wait` in background Bash, not detached.
  - I-069369e0, I-bf957df8, I-f7989bae: split on LF only, whole targets, replay-only round has no
    result; tests extended.
  - I-ec048163: new `req.headless-sessions.worktree-tools-granted`; `claude-works-tasks` keeps the
    procedure only.
  - I-4f62fffc: relies on `contract.execution.run-result` and `contract.kernel.workspace-binding`
    and includes `document.execution.runner` (progress-file fields, lobby, detached runs).
  - I-f3e67aa7: declared uses of `module.tasks` (concept.task) and `module.main-session`
    (guidance concept and the two delegation requirements), each explained.
- **SWE-bench cases** (commit after 71e0f53ff, "repair only what evidence justifies"):
  - I-d553bd57, as the main agent answered (A): Spec and `REPAIR_INTENT` now restrict the repair
    to what the findings and existing Specs justify; a code-fact gap becomes an open question that
    does not stop the round. Relies on `req.specification.no-code`.
  - I-c3143277: declared uses of `module.tasks` (concept.task, req.tasks.binding,
    req.tasks.merge-verified), `module.validation` (concept.readiness,
    req.validation.ready-definition, contract.validation.readiness) and `module.delivery`
    (req.delivery.own-readiness, contract.delivery.output), each explained, including that review
    findings left by the second review block neither validation, delivery nor merge.
- **Dogfooding** (commit 742d566b4): I-9b1f1243 — symbolic-ref exit 1 alone means detached, other
  failures and a failed `status` or empty `rev-parse --verify HEAD` refuse as
  `develop_source_unreadable` with Git's message (the `--show-toplevel` failure stays
  `develop_source_not_repository`, which already carries Git's message: telling "not a repository"
  from other Git failures there would need parsing localized text). I-aa048acb: the case added to
  `req.dogfooding.refusal-names-reason`, new `scenario.dogfooding.refused-unreadable` with a test.
  I-2399ac5d: `defect-outside-task` keeps its id for the no-task duty; new `-kept`, `-named`;
  `issue-system-defect` keeps the hand-over representation; new `issue-system-defect-kept`,
  `-named` (conditions kept as written). I-cf457d92: diagram's fix node no longer closes the
  Issue, the merge node does. I-7f2711b4: Issues reliance selects `contract.issues.report`; new use
  of `module.tracing` (concept.error-chain, contract.tracing.error), explained.
- **Dogfood scenarios**: I-a8862251 — End-to-end testing's entry was already included by
  1bcce36d9 (a child cannot `use` its own parent's preparation more than by that inclusion); added
  a use of `module.workers` (configuration and model-map concepts and contracts,
  req.workers.model-map-entry) with its explanation of the refusal before scenario setup.
  (Correction: whether the Protocol lets a child Module `use` its parent was not checked; the existing inclusion was judged sufficient.)

## Report 2 to the main agent (Review流程), 2026-10-08T14:16:57Z

r2-e2e delivered: delivery commit fb78c463e (run r-20261008T140600-delivery-d7e363ff) on concorde/r2-e2e. task-validation ready; full suite 1376 passed, 5 skipped. Ready to merge. All 24 Issues are handled and listed in the task's resolves.

Fixed by this task (19):
- Critical I-1a2535db, plus I-2853f9f7, I-3f3d2610 and I-09c7ff1a (commit a528a485d). Preferred fix chosen: grading reads statuses from a small pytest plugin keyed by full node identity, not from the short summary, because a SKIPPED summary line names no test at all. Grading now also counts like SWE-bench's own grading.py: XFAIL counts as passed, a skipped PASS_TO_PASS test is maintained, and a truncated parametrized identity is prefix-matched. Cases now selects SWE-bench's harness and dataset guide as external material. PYTHONPATH keeps the caller's own entries, and a timed-out run keeps its whole log. New req.swe-bench-cases.graded-like-swe-bench and scenario.swe-bench-cases.grade-statuses.
- Headless sessions (71e0f53ff):
  - I-4915a01c, per your answer: each round passes --settings sandbox.enabled=false (new req.headless-sessions.sandbox-off). An unfinished run whose runner is gone is unsettled as runner_gone, and the wake reports it as ended without a result.
  - I-069369e0, I-bf957df8, I-f7989bae: log records are split at LF only, tool targets are kept whole, and a round with only a replay has no result.
  - I-ec048163: new req.headless-sessions.worktree-tools-granted.
  - I-4f62fffc: the Module now selects the run-result and workspace-binding contracts, and includes the runner document.
  - I-f3e67aa7: declared uses of Tasks and Main session.
- SWE-bench cases (a1ce9939b): I-d553bd57 per your answer (A): the repair intent and the Spec are restricted to what the review's evidence justifies. I-c3143277: declared uses of Tasks, Validation and Delivery. The Spec also explains that review findings left after the second review do not block validation, delivery or merge.
- Dogfooding (742d566b4):
  - I-9b1f1243: a failed Git query now refuses as develop_source_unreadable with Git's message, and an empty commit is never returned.
  - I-aa048acb: that case is added to the refusal requirement, with a new scenario and test.
  - I-2399ac5d: both joined hand-off requirements are split into one duty each, with new ids -kept and -named.
  - I-cf457d92: in the overview diagram, the merge closes the Issue.
  - I-7f2711b4: Dogfooding now selects contract.issues.report and contract.tracing.error.
- Dogfood scenarios (5b75d5b13): I-a8862251. Added the missing use of Workers (configuration and model map). The parent's entry was already included.

Already fixed before this task (5), by 1bcce36d9, which the review's head ce20cc748 did not contain. Each has a test on main:
- I-6727657f: the owners case takes a run only when its runner descends from the case's launcher.
- I-9e8a963d: the judged time starts from turn_end.
- I-8f1b4967: the worktree path is shell-quoted.
- I-7340749c: launches that cannot start return command_failed.
- I-33d21d3b: an invalid --name is refused with invalid_name.
They are in the task's resolves, so the merge will close them as resolved; or close them yourself.

Decisions I made: see the decision log (Task session decisions). Open: nothing for the developer.

## Closed: merged, 2026-10-12T14:28:11Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit fb78c463e9445e2c4298af414fa4cf95577eaf61 into main and closed it as merged. Nobody answers a report after that.
