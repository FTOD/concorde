# Decision log: r3-task-session-main

Goal: Fix the remaining open Issues of Task session and Main session (medium and low) found by the complete project_review

## Task brief (main agent, 2026-10-13)

Round 3. Rounds 1 and 2 fixed every critical and high Issue. The developer decided (2026-10-13)
that the main agent now resolves everything it can settle itself: this task resolves **every open
Issue owned by its Modules** (14, listed in `resolves`; 2 of them decision-needed), all medium or
low, found by project_review r-20261008T063808-project_review-9851e69f or reported since. Read each
with `concorde issues show`.

By tier:
- **decision-needed**: read them all first and escalate them **together in one report, early**,
  each with what you found, the options and your recommendation (say which options change a
  promise users rely on or an earlier developer decision). The main agent settles those within its
  authority and takes the rest to the developer in one batch. Continue with the rest meanwhile.
  An Issue the developer is asked about may stay open: you may deliver without it; the main agent
  reopens it after the merge if needed.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- **suggestion**: apply unless it is wrong or costs more than it is worth; then say why in the
  log and your report, and the main agent closes it as not-actionable.
- An Issue that no longer holds (many Modules changed in rounds 1-2), is a duplicate or is already
  fixed: say so with evidence; it stays in `resolves` and the merge closes it.
- Medium first, then low. A fix needing a change outside the task's Modules: escalate, unless it is
  a small mechanical follow-on (a link, a fixture, a registry refresh).

Eleven other round-3 tasks (r3-*) run in parallel on other Modules. Deliver with
`task-validation` then `delivery`; run the full suite once on the final input.

## Escalated to the main agent, 2026-10-13T11:33:26Z

- **task-session** task session (task r3-task-session-main): `repeated_session_start_settled`
  Issue I-dd8040bd39ab50f8a311a8f750e91d31 (decision-needed, medium): no defined behaviour for a repeated 'concorde task session' launch. It no longer holds: the review head ce20cc748 predates commit 78f2b6ccc (2026-10-08, task fix-task-session), which implemented the main agent's answer B to escalation 'repeated_session_start' of that task: req.task-session.one-working, refusal code session_running (reason decision) while 'claude agents --json --all' lists a recorded session in a state other than done/failed, a start allowed when every recorded session is done, failed or gone, each start its own node, the latest --main becomes main; scenarios task-session.one-working and task-session.replace-ended; the contract's Commands row states it. The one corner left is an 'uncertain' launch: claude --bg exits non-zero or without the 'backgrounded' line although it started a job; the start then fails with session_failed and records nothing, so the guard does not see that job (a started session whose recording fails is already removed with claude rm, scenario start-unrecorded).
  Not handled here (decision): The Issue is decision-needed; settling it, even as already resolved, is not the task session's call.
  Options: A: resolved by the earlier answer B; no change (the merge closes it); B: also add to the session_failed row that a failed launch may leave an unrecorded job and name 'claude agents --json --all' to check, a documentation-only sentence; C: on session_failed, look up a job named task-<task> in 'claude agents --json --all' and remove or record it (new behaviour)
  Recommendation: A, or B if you want the corner named; neither changes a promise. C adds behaviour for a case never seen.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-task-session-main)",
  "code": "repeated_session_start_settled",
  "detail": "Issue I-dd8040bd39ab50f8a311a8f750e91d31 (decision-needed, medium): no defined behaviour for a repeated 'concorde task session' launch. It no longer holds: the review head ce20cc748 predates commit 78f2b6ccc (2026-10-08, task fix-task-session), which implemented the main agent's answer B to escalation 'repeated_session_start' of that task: req.task-session.one-working, refusal code session_running (reason decision) while 'claude agents --json --all' lists a recorded session in a state other than done/failed, a start allowed when every recorded session is done, failed or gone, each start its own node, the latest --main becomes main; scenarios task-session.one-working and task-session.replace-ended; the contract's Commands row states it. The one corner left is an 'uncertain' launch: claude --bg exits non-zero or without the 'backgrounded' line although it started a job; the start then fails with session_failed and records nothing, so the guard does not see that job (a started session whose recording fails is already removed with claude rm, scenario start-unrecorded).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed; settling it, even as already resolved, is not the task session's call."
  },
  "options": [
    "A: resolved by the earlier answer B; no change (the merge closes it)",
    "B: also add to the session_failed row that a failed launch may leave an unrecorded job and name 'claude agents --json --all' to check, a documentation-only sentence",
    "C: on session_failed, look up a job named task-<task> in 'claude agents --json --all' and remove or record it (new behaviour)"
  ],
  "recommendation": "A, or B if you want the corner named; neither changes a promise. C adds behaviour for a case never seen.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:33:35Z

- **task-session** task session (task r3-task-session-main): `transcript_record_policy`
  Issue I-e69c4e01ef4d5493aa7114f5c04f05d8 (decision-needed, medium): no policy for malformed, unreadable or incomplete transcript records. Mostly settled: the main agent's answer B to escalation 'transcript_parse_policy' of task fix-task-session (2026-10-08) is implemented since 78f2b6ccc, after the review head ce20cc748: lines that are no JSON object are skipped and counted in unreadable_lines (session trace v3) and named in a close warning, the session still removed since transcript.jsonl is a verbatim copy; a kept copy that cannot be read counts as not kept (warning, session not removed). Left unspecified by contract.task-session.session-trace: (1) an assistant record whose message has no usage object is skipped (counts no tokens, not counted as unreadable); (2) an assistant record without message.id counts as its own message, keyed by its file and uuid or line number. Probe of the 300 latest real transcripts on this machine: 51,459 assistant records, 0 without usage, 0 without message.id (1 synthetic, already excluded). These are defensive paths only.
  Not handled here (decision): The Issue is decision-needed and the residual choice is a promise of contract.task-session.session-trace.
  Options: A: state the current handling of (1) and (2) in the session-trace semantics (documentation of unchanged behaviour, no version bump), resolving the Issue; B: count such assistant records in a new field (e.g. unaccounted_records, contract v4) and name the count in the close warning beside unreadable_lines; C: make the usage figures null when any such record occurs
  Recommendation: A: the incompleteness the Issue worried about (unreadable lines) is already visible after decision B; (1) and (2) never occur in real transcripts, so a new field would be dead weight. A changes no promise users rely on and no earlier developer decision.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-task-session-main)",
  "code": "transcript_record_policy",
  "detail": "Issue I-e69c4e01ef4d5493aa7114f5c04f05d8 (decision-needed, medium): no policy for malformed, unreadable or incomplete transcript records. Mostly settled: the main agent's answer B to escalation 'transcript_parse_policy' of task fix-task-session (2026-10-08) is implemented since 78f2b6ccc, after the review head ce20cc748: lines that are no JSON object are skipped and counted in unreadable_lines (session trace v3) and named in a close warning, the session still removed since transcript.jsonl is a verbatim copy; a kept copy that cannot be read counts as not kept (warning, session not removed). Left unspecified by contract.task-session.session-trace: (1) an assistant record whose message has no usage object is skipped (counts no tokens, not counted as unreadable); (2) an assistant record without message.id counts as its own message, keyed by its file and uuid or line number. Probe of the 300 latest real transcripts on this machine: 51,459 assistant records, 0 without usage, 0 without message.id (1 synthetic, already excluded). These are defensive paths only.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed and the residual choice is a promise of contract.task-session.session-trace."
  },
  "options": [
    "A: state the current handling of (1) and (2) in the session-trace semantics (documentation of unchanged behaviour, no version bump), resolving the Issue",
    "B: count such assistant records in a new field (e.g. unaccounted_records, contract v4) and name the count in the close warning beside unreadable_lines",
    "C: make the usage figures null when any such record occurs"
  ],
  "recommendation": "A: the incompleteness the Issue worried about (unreadable lines) is already visible after decision B; (1) and (2) never occur in real transcripts, so a new field would be dead weight. A changes no promise users rely on and no earlier developer decision.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-13T11:33:42Z

Early escalation report (r3-task-session-main): the 2 decision-needed Issues, both largely settled already by your answers in task fix-task-session (commit 78f2b6ccc, after this review's head ce20cc748). I continue with the 12 other Issues meanwhile.

Escalation 1 repeated_session_start_settled - I-dd8040bd (repeated task-session launches). Already resolved by answer B (session_running while a recorded session works; replace when done/failed/gone; scenarios one-working, replace-ended). Corner left: a launch that exits without reporting a session yet started a job is not seen by the guard. Options: A resolved, no change; B add one documentation sentence to the session_failed row; C new lookup-and-remove behaviour. Recommendation: A (or B); neither changes a promise.

Escalation 2 transcript_record_policy - I-e69c4e01 (malformed/incomplete transcript records). Unreadable lines already settled by answer B (unreadable_lines, v3, warning). Left: assistant records without usage (skipped) and without message.id (own message). 0 of 51,459 real assistant records have either. Options: A document current handling in the session-trace semantics, no version bump; B new counted field, contract v4; C null figures. Recommendation: A; changes no promise users rely on and no developer decision.

It carries escalation(s) 1, 2.

## Answer to report(s) 1 of the task session, 2026-10-13T11:33:55Z

Escalations 1-2 (main agent): 1 B — add one sentence to the session_failed row documenting the corner (a launch that exits without reporting a session but started a job is not seen by the guard; check claude agents and stop it by hand); I-dd8040bd resolved. 2 A — document the current handling of assistant records without usage or message.id in the session-trace semantics, no version bump; I-e69c4e01 resolved.

## Task session decisions, 2026-10-13

- Escalation answers applied: I-dd8040bd (B) — one sentence on the `session_failed` row says a failed launch may leave an unrecorded job, listed by `claude agents --json --all` under `task-<task-id>`. I-e69c4e01 (A) — the session-trace semantics now state that an assistant record without usage counts no tokens and no message and is not unreadable, one without message.id counts as its own message, a `<synthetic>` one counts no tokens; no version bump (behaviour unchanged).
- I-4652884a (preferred-fix): already fixed before this task by 78f2b6ccc (after the review head ce20cc748): scenario.task-session.mcp-unusable-file separates the unusable file case; node-finished states that no assistant record follows the cost-state record; cost-unaccounted covers the stale account. No change.
- I-f3f24836 (suggestion): already applied by 78f2b6ccc: the entry no longer carries the path encoding, approval-source list, name normalization, totalCostUSD/modelUsage selection or message.id rule; they are in contracts.md only. No change.
- I-ea7fa3ec (preferred-fix): `finish_sessions` now also catches `OSError` from `trace.write` (mkdir/mkstemp/replace), keeping a copy failure and the write failure in one warning, discarding the partial copy, leaving the session unremoved. Chosen over wrapping inside Tracing because the best-effort policy is Task sessions' own (req.task-session.transcript-kept). New test with an unwritable node folder; failed without the fix (unexpected_error). Scenario keep-failed, the requirement and the contract's warning row name the node-write failure.
- I-cb408458 (preferred-fix): entry #uses-issues and req.task-session.boundary now distinguish the primary worktree's Issue records (refused by the hook) from the task branch's copy inside the worktree (allowed by the hook, left unchanged by guidance). Small follow-on outside my Modules: two lines in the Issues part's guidance `prompts/guidance/issues/task-session.md` ("Never change that copy"), since no guidance said it; the Main session guidance test updated for its reworded tool sentence.
- I-b1e06247 (preferred-fix): the task-session guidance, scenario task-session-unrestricted, req.task-session.no-sandbox, the Task sessions entry and session.py's docstring now say the merge checks only the working trees of the primary worktree and of ended or delivered tasks, not commits, a working task's worktree or other paths, so a successful merge proves nothing about out-of-bound writes.
- I-63ed1d68 (preferred-fix): guidance, scenario merge-through-server and entry distinguish the attempt lock (`merge_busy` naming `locks/attempts/<task>.lock`: wait with `concorde task wait <task> --merge`, read its answer, call task_merge again only if that merge did not close the task) from the workspace and merge locks (register_wait). No tool change.
- I-cf5a0648 + I-55d4a562: req.main-session.project-mcp-no-wait rescoped to Coordination's tools (attempt, workspace and merge locks), in active voice with the condition first; it says other parts' tools state their own waiting, citing workflow_step. The skill's "server's only rule" sentence is scoped the same way.
- I-f5684cb7 (preferred-fix): premises added: project-mcp-session (every part installed, plus a pointer to Distribution's part-missing scenario for partial installs, which already verifies absent tools); change-through-task (execution and method installed, plus the `task deliver` fallback); merge-conflict and update-merge (method installed; merge-conflict also names the fallback). The task-session guidance's merge paragraph now points at the "Deliver" commands; new test.
- I-fd7396da (preferred-fix): main-session declares `uses module.project-review` (covered-modules, worker-ids, skip-unchanged, record-commit), explains project_review in "Questions without a task" and a #uses-project-review section, and the scenario links Project review's requirements. Registry refreshed.
- I-9e071de8 (suggestion, applied): the `task session` Commands row keeps syntax and output; its effects are a numbered list with separate passages for dry-run and the refused record.
- I-e5398063 (suggestion, applied): the test inventories left the Main session realizations; the "guidance cannot guarantee model compliance" explanation stays. The same pattern in the Task sessions realization removed for consistency.

## Report 2 to the main agent (Review流程), 2026-10-13T12:05:54Z

r3-task-session-main delivered: delivery commit 8ecef0919 (fix commit 02a2c4968). task-validation and delivery ready (28 checks); full suite 1474 passed, 5 skipped; build --check and spec-validation clean (0 errors, no new warnings).

Resolves all 14 Issues in resolves:
- Answers applied: I-dd8040bd (B: sentence on session_failed), I-e69c4e01 (A: session-trace semantics state assistant records without usage/id, no version bump).
- Already fixed before this task (78f2b6ccc, after review head ce20cc748), no change: I-4652884a (mcp-unusable-file, cost ordering scenarios), I-f3f24836 (algorithms already moved to contracts).
- I-ea7fa3ec: finish_sessions now also catches OSError from the node write; one warning carries both failures, session left listed; new test (fails without the fix); scenario/requirement/contract updated.
- I-cb408458: boundary refuses the primary's Issue records; the task branch's .concorde/issues/ copy is allowed by the hook and left alone by guidance. Small follow-on outside my Modules: 2 lines in prompts/guidance/issues/task-session.md (module.issues) stating that copy is never changed.
- I-b1e06247: merge check described as what it judges (working trees of primary and ended/delivered tasks; not commits, working tasks or other paths) in guidance, scenario, req.task-session.no-sandbox, entry.
- I-63ed1d68: attempt-lock merge_busy -> concorde task wait <task> --merge, then task_merge only if that merge did not close the task; register_wait kept for workspace/merge locks.
- I-cf5a0648 + I-55d4a562: no-wait requirement scoped to Coordination's tools, active voice, condition first; other parts' tools (workflow_step) state their own waiting.
- I-f5684cb7: installed-part premises on project-mcp-session, change-through-task, merge-conflict, update-merge; task deliver fallback named; partial installs point to Distribution's part-missing scenario.
- I-fd7396da: main-session now uses module.project-review (4 requirements), explains project_review in the entry, scenario links them.
- Suggestions applied: I-9e071de8 (command effects as steps), I-e5398063 (test inventories removed; also from Task sessions' realization).

Nothing open; no escalation pending. Decisions are in the decision log.

## Closed: merged, 2026-10-13T14:42:49Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 8ecef09196437f2f62e7545e539f29525f7ed4b4 into main and closed it as merged. Nobody answers a report after that.
