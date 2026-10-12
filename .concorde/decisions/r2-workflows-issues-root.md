# Decision log: r2-workflows-issues-root

Goal: Fix the critical, high and obvious-fix open Issues of Workflows, Issues and the root Module found by the complete project_review

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08) that this round fixes the **critical and high** open Issues of
every Module, plus each Module's **obvious-fix** Issues since they are cheap; medium and low
Issues of other tiers wait for a later round. This task resolves the 19 Issues in its `resolves`,
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

## Escalated to the main agent, 2026-10-08T13:39:15Z

- **task-session** task session (task r2-workflows-issues-root): `mode_change_replay_reporting`
  Issue I-0c528e32ce525a2ab6bb982de977aea4 (decision-needed, high, module.workflows): an interactive relaunch of a workflow first run no-ask stops at a cached step whose decision points no answer settled, yet its report says ok. Verified in code: a cached step (found, not retried) records nothing new (src/concorde/workflows/step.py run_step); brownfield.js interactiveStop() stops at the first outcome with decision_points > 0, cached or not; report.build() takes mode = steps[-1]['mode'] (report.py:241) and judges only the latest current step, so a completed no-ask brownfield replayed interactively reports the old delivery step's ok with no pending points. Same defect for a no-ask run that failed at a later step and is replayed interactively: the script stops at an earlier cached decision, the report says failed at the later step instead of awaiting_decision. The Spec (workflows/module.md 'The record and the result') states both 'a relaunch may change the mode' and 'the report judges pending points by the latest recorded step's mode'; fixing it changes what contract.workflows.result promises.
  Not handled here (decision): Each fix changes Workflows' promised behaviour (how a result's status is derived, or whether a relaunch may change mode), and the task brief reserves decision-needed Issues for the main agent or the developer.
  Options: A: The report judges by the invocation's mode that the script already passes with --mode (falling back to the latest recorded step's mode only when --mode is absent, as for a report run by hand). In interactive mode it stops, as the script does, at the first current step in recorded order that did not end ok or whose decision points its answers did not settle, and derives failed/blocked/awaiting_decision from that step; no-ask keeps judging the latest current step. No new recorded state; nothing relayed is trusted. Update module.md, contract.workflows.result, req for result status, add the scenario 'completed no-ask workflow replayed interactively with a cached unsettled decision' and its test.; B: The script also passes the key it stopped at (--stopped <key>) and the report judges that step; a report without it judges the latest current step as now. Exact, but the result then depends on a script-supplied argument, and every workflow script must pass it correctly.; C: Forbid mode changes: workflow step refuses a step whose mode differs from the recorded workflow's mode (new refusal mode_changed); changing mode needs restart labels for every step. Removes the promised 'a relaunch may change the mode'.
  Recommendation: A: it keeps mode changes, needs no new state or argument, mirrors the script's own interactive stop rule from recorded facts only, and is a contained change of report.build plus its Spec and contract.

```json
{
  "level": "task-session",
  "actor": "task session (task r2-workflows-issues-root)",
  "code": "mode_change_replay_reporting",
  "detail": "Issue I-0c528e32ce525a2ab6bb982de977aea4 (decision-needed, high, module.workflows): an interactive relaunch of a workflow first run no-ask stops at a cached step whose decision points no answer settled, yet its report says ok. Verified in code: a cached step (found, not retried) records nothing new (src/concorde/workflows/step.py run_step); brownfield.js interactiveStop() stops at the first outcome with decision_points > 0, cached or not; report.build() takes mode = steps[-1]['mode'] (report.py:241) and judges only the latest current step, so a completed no-ask brownfield replayed interactively reports the old delivery step's ok with no pending points. Same defect for a no-ask run that failed at a later step and is replayed interactively: the script stops at an earlier cached decision, the report says failed at the later step instead of awaiting_decision. The Spec (workflows/module.md 'The record and the result') states both 'a relaunch may change the mode' and 'the report judges pending points by the latest recorded step's mode'; fixing it changes what contract.workflows.result promises.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Each fix changes Workflows' promised behaviour (how a result's status is derived, or whether a relaunch may change mode), and the task brief reserves decision-needed Issues for the main agent or the developer."
  },
  "options": [
    "A: The report judges by the invocation's mode that the script already passes with --mode (falling back to the latest recorded step's mode only when --mode is absent, as for a report run by hand). In interactive mode it stops, as the script does, at the first current step in recorded order that did not end ok or whose decision points its answers did not settle, and derives failed/blocked/awaiting_decision from that step; no-ask keeps judging the latest current step. No new recorded state; nothing relayed is trusted. Update module.md, contract.workflows.result, req for result status, add the scenario 'completed no-ask workflow replayed interactively with a cached unsettled decision' and its test.",
    "B: The script also passes the key it stopped at (--stopped <key>) and the report judges that step; a report without it judges the latest current step as now. Exact, but the result then depends on a script-supplied argument, and every workflow script must pass it correctly.",
    "C: Forbid mode changes: workflow step refuses a step whose mode differs from the recorded workflow's mode (new refusal mode_changed); changing mode needs restart labels for every step. Removes the promised 'a relaunch may change the mode'."
  ],
  "recommendation": "A: it keeps mode changes, needs no new state or argument, mirrors the script's own interactive stop rule from recorded facts only, and is a contained change of report.build plus its Spec and contract.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-08T13:39:20Z

Early escalation (as the brief asks): the task's only decision-needed Issue, I-0c528e32 (Workflows: mode-changing replay can stop for decisions but report success), is escalation 1. The Issue holds (verified in step.py, brownfield.js interactiveStop, report.py:241). Options A (report judges by the invocation's --mode and, in interactive mode, by the first current step that did not end ok or has unsettled decision points), B (script passes --stopped <key>), C (forbid mode changes). Recommendation: A. I continue meanwhile with the 18 other Issues (preferred-fix and obvious-fix) and will implement the chosen option once answered.

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-10-08T13:39:36Z

Escalation 1 mode_change_replay_reporting (main agent): A — the report judges by the invocation's --mode (falling back to the latest recorded step's mode only when absent); in interactive mode it stops where the script stops, at the first current step in recorded order that did not end ok or has decision points its answers did not settle; no-ask keeps judging the latest current step. Update the Spec and contract.workflows.result, add a scenario and test.

## Task session decisions (2026-10-08)

- I-0c528e32 (decision-needed): escalated as escalation 1; the main agent answered option A.
- I-0dc3fa53 (preferred-fix, high): fixed by checking the `(invocation_id, report_key)` pair across
  every committed record (open and closed) under the merge lock, after the target record's own
  idempotent-retry check. Only records whose bytes contain the invocation id are parsed, so an
  unrelated invalid record never refuses a report. Chosen over a separate key index: no new state
  to keep in step. Interface row of `report_issue` clarified; new
  `scenario.issues.store-key-conflict-across` with its test. Checked that every review keys its
  reports uniquely per run (`<module>/<position>`, kind-prefixed), so no caller relies on reuse.
- I-8ff5c83f (preferred-fix, high): `_end_step_node` takes the step call's remaining deadline; on
  `LockBusy` the step prints the outcome it saw and the next step or report command ends the
  node (both already end nodes of ended runs). Spec: `req.workflows.bounded-wait`, the record
  section of module.md and the semantics of `contract.workflows.step-trace` say so. I did not bump
  the step-trace contract version: its data and shape are unchanged, only when the node ends
  under a busy lock. New `scenario.workflows.step-ends-later` with its test.
- I-0c528e32: implemented option A as answered. `report.build` judges by `--mode` (falling back to
  the latest recorded step's mode) and, in interactive mode, by the first current step that did
  not end ok, declared blocking or has unsettled decision points. I named it the "judged step" in
  module.md (local wording, like the former "latest current step"; not a glossary term).
  `contract.workflows.result` bumped to version 10 (behaviour change), new
  `req.workflows.report-judges-stop` and `scenario.workflows.mode-changed-replay` with two tests.
- I-58cbd364 (preferred-fix, high): qualified `req.concorde.part-dependencies` to imports of
  Concorde code (the `concorde` package); standard-library and third-party imports are outside it,
  pointing to Distribution for installing them. Chosen as the Issue suggested; the table and the
  optional-integration rule are unchanged.
- I-c34c317a, I-6b5aaf2a, I-7437411, I-2ebbccdc, I-30118ac2, I-3ab9d5cf, I-acce1f97,
  I-3a0dd064, I-7b87c9c9, I-317748bf: Spec or prompt rewording as each Issue's suggested repair;
  the root's new include of `document.workers.launch` needed `registry --write`.
  I-7b87c9c9 new requirement ids: `req.workflows.faithful-render`, `req.workflows.tool-answers-outcome`,
  `req.workflows.data-unchanged`, `req.workflows.running-exit`. I-317748bf new scenario ids:
  `relay-exhausted`, `step-unstarted`, `step-binding-gone`, `step-binding-changed`; tests re-pointed.
- I-aff96338, I-4bb72250, I-7f5cd9e6, I-b42ffcc5, I-f9e22638: code fixes with regression tests,
  as each Issue suggested. For I-f9e22638 the `--lost` check runs before the workspace is even
  resolved, so a malformed key never reads or writes anything; the contract's Errors section says so.
- `claude.js` was edited in its existing style, not run through Prettier: the file is not
  Prettier-formatted today and docsite's node_modules has no Prettier binary.
- No Issue turned out invalid, duplicate or already fixed.
- Follow-on: tests/concorde/main_session/test_guidance.py (module.main-session) pinned the old guidance sentence; updated its expected text, a mechanical follow-on of I-acce1f97. The full suite otherwise passed (1380 passed, 5 skipped).

## Report 2 to the main agent (Review流程), 2026-10-08T14:18:50Z

r2-workflows-issues-root delivered: delivery commit 3dc301ad20d49cb7d5c4a9878813b224e0be18d8 (run r-20261008T140810-delivery-dedff145), after task-validation r-20261008T135715-task_validation-4089720b said ready. The full suite passed once on the final input (1380 passed, 5 skipped) after one follow-on fix.

The task resolves all 19 Issues in its resolves. None was invalid, a duplicate or already fixed.

High:
- I-0c528e32 (decision-needed): option A, as you answered. The report judges by --mode; in interactive mode it judges the first current step that did not end ok, declared blocking or has unsettled decision points. contract.workflows.result is now version 10. New req.workflows.report-judges-stop, scenario.workflows.mode-changed-replay and 2 tests.
- I-0dc3fa53 (preferred-fix): record_report checks the (invocation_id, report_key) pair across every committed Issue. Exact retries stay idempotent. Only records containing the invocation id are parsed, so an unrelated broken record never blocks a report. New scenario issues.store-key-conflict-across and its test. I checked that every review keys reports uniquely per run.
- I-8ff5c83f (preferred-fix): ending a step's node waits for the workflow lock only until the step call's deadline. If the lock stays busy, the next step or report command ends the node. Spec updated, new scenario workflows.step-ends-later and its test. The step-trace contract version is not bumped: its data is unchanged.
- I-58cbd364 (preferred-fix): req.concorde.part-dependencies now covers only imports of Concorde code. Standard-library and third-party imports are outside it.
- I-6b5aaf2a, I-c34c317a (obvious-fix): Spec text aligned with the Provenance section and with General work's flow.

Medium/low obvious-fix:
- Root: I-2ebbccdc (includes document.workers.launch, plus registry --write), I-74374117, I-aff96338 (fingerprint uses lstat inside the error handling, with a test).
- Issues: I-30118ac2, I-3ab9d5cf, I-acce1f97.
- Workflows: I-3a0dd064, I-7b87c9c9 (4 new requirement ids), I-317748bf (4 new scenario ids, tests re-pointed). Code fixes with tests: I-4bb72250, I-7f5cd9e6, I-b42ffcc5, I-f9e22638.

Small mechanical follow-on outside the task's Modules: tests/concorde/main_session/test_guidance.py (module.main-session) expected the old guidance sentence. I updated that expected text for I-acce1f97.

Other decisions are in the decision log. claude.js was edited in its existing style, not run through Prettier, because the file is not Prettier-formatted and no Prettier binary is installed. Nothing is open.

## Closed: merged, 2026-10-12T14:30:02Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 3dc301ad20d49cb7d5c4a9878813b224e0be18d8 into main and closed it as merged. Nobody answers a report after that.
