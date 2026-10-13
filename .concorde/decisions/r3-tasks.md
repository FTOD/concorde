# Decision log: r3-tasks

Goal: Fix the remaining open Issues of Tasks and Coordination (medium and low) found by the complete project_review

## Task brief (main agent, 2026-10-13)

Round 3. Rounds 1 and 2 fixed every critical and high Issue. The developer decided (2026-10-13)
that the main agent now resolves everything it can settle itself: this task resolves **every open
Issue owned by its Modules** (15, listed in `resolves`; 4 of them decision-needed), all medium or
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

## Escalated to the main agent, 2026-10-13T11:33:54Z

- **task-session** task session (task r3-tasks): `close_refusal_precedence`
  I-6160711ee1c95dfcbd469793846a10ed (decision-needed): scenario.tasks.close-other-outcome refuses the same close with invalid_transition 'once its decision log holds the closing', and the contracts' invalid_transition row says the same, but req.tasks.log-commit-alone, scenario.tasks.close-commits-log and the decision-log-commit contract require that same close to finish after decision_log_uncommitted, when the log already holds its closing. The code (_close_held, refuse_closed in store.py) already follows the recovery promises: the same outcome finishes a task that is still current in .concorde/tasks/, and only a task whose folder moved to the history is refused with invalid_transition. I-c7da60b2 (preferred-fix, mine) asks for the same alignment.
  Not handled here (decision): The Issue is decision-needed; its fix changes the stated condition of a refusal promise, though only to match the recovery promises and the code.
  Options: A: the same outcome is refused only once the task's folder is in the history; while the task is current, the same close finishes the steps it lacks (aligns scenario + invalid_transition row to the recovery promises and to the code; no code change); B: keep 'once the log holds the closing' and drop the recovery after decision_log_uncommitted (changes code and the recovery promises users rely on)
  Recommendation: A. It changes no behaviour, keeps the recovery promise, and is the fix I make for I-c7da60b2 anyway; I will apply it and you may confirm it.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-tasks)",
  "code": "close_refusal_precedence",
  "detail": "I-6160711ee1c95dfcbd469793846a10ed (decision-needed): scenario.tasks.close-other-outcome refuses the same close with invalid_transition 'once its decision log holds the closing', and the contracts' invalid_transition row says the same, but req.tasks.log-commit-alone, scenario.tasks.close-commits-log and the decision-log-commit contract require that same close to finish after decision_log_uncommitted, when the log already holds its closing. The code (_close_held, refuse_closed in store.py) already follows the recovery promises: the same outcome finishes a task that is still current in .concorde/tasks/, and only a task whose folder moved to the history is refused with invalid_transition. I-c7da60b2 (preferred-fix, mine) asks for the same alignment.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed; its fix changes the stated condition of a refusal promise, though only to match the recovery promises and the code."
  },
  "options": [
    "A: the same outcome is refused only once the task's folder is in the history; while the task is current, the same close finishes the steps it lacks (aligns scenario + invalid_transition row to the recovery promises and to the code; no code change)",
    "B: keep 'once the log holds the closing' and drop the recovery after decision_log_uncommitted (changes code and the recovery promises users rely on)"
  ],
  "recommendation": "A. It changes no behaviour, keeps the recovery promise, and is the fix I make for I-c7da60b2 anyway; I will apply it and you may confirm it.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:33:54Z

- **task-session** task session (task r3-tasks): `resume_diverged_code`
  I-70eaab12dfc0566091e94467b3ede387 and I-887c6e3f52cc5645b9a868128d83216f (both decision-needed, same problem): for 'task merge --resume' with the primary branch's head neither the commit before the merge nor the merge commit, req.tasks.merge-recovery and the entry (module.md) say merge_diverged; the contracts' not_resumable row ('head is not the merge commit') and scenario.tasks.merge-resume-refused say not_resumable; the code (_resume in merge.py) returns not_resumable. Both codes have reason decision. not_resumable's message advises --abort, which itself refuses with merge_diverged on such a head, so the advice is wrong there.
  Not handled here (decision): The Issues are decision-needed; choosing one changes an observable refusal code callers and tests rely on.
  Options: A: merge_diverged for --resume too when the head is neither commit (or the worktree is on another branch/detached); not_resumable only when the head is the commit before the merge. Aligns contracts row, scenario and code to the requirement and entry.; B: keep the code: not_resumable for every --resume whose head is not the merge commit; merge_diverged for --resume only on a switched/detached worktree. Aligns the requirement and entry to the contracts and code.
  Recommendation: A: the requirement and entry already promise it, both recovery commands then answer the same situation the same way, and the refusal's advice (restore the branch by hand) is right, whereas not_resumable's '--abort is the way out' is not.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-tasks)",
  "code": "resume_diverged_code",
  "detail": "I-70eaab12dfc0566091e94467b3ede387 and I-887c6e3f52cc5645b9a868128d83216f (both decision-needed, same problem): for 'task merge --resume' with the primary branch's head neither the commit before the merge nor the merge commit, req.tasks.merge-recovery and the entry (module.md) say merge_diverged; the contracts' not_resumable row ('head is not the merge commit') and scenario.tasks.merge-resume-refused say not_resumable; the code (_resume in merge.py) returns not_resumable. Both codes have reason decision. not_resumable's message advises --abort, which itself refuses with merge_diverged on such a head, so the advice is wrong there.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issues are decision-needed; choosing one changes an observable refusal code callers and tests rely on."
  },
  "options": [
    "A: merge_diverged for --resume too when the head is neither commit (or the worktree is on another branch/detached); not_resumable only when the head is the commit before the merge. Aligns contracts row, scenario and code to the requirement and entry.",
    "B: keep the code: not_resumable for every --resume whose head is not the merge commit; merge_diverged for --resume only on a switched/detached worktree. Aligns the requirement and entry to the contracts and code."
  ],
  "recommendation": "A: the requirement and entry already promise it, both recovery commands then answer the same situation the same way, and the refusal's advice (restore the branch by hand) is right, whereas not_resumable's '--abort is the way out' is not.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:33:54Z

- **task-session** task session (task r3-tasks): `show_reused_name`
  I-b3dd1c7f28455542a3dd2a1b9858ddc1 (decision-needed): 'task show <task-id>' gives no rule for a name reused across history incarnations (retry, retry.2, retry.3). The code (found_folder in store.py) already does: the current task first; else a dotted history key such as retry.2 names that incarnation exactly; a bare name names the latest incarnation in the history. So the first incarnation, history key 'retry', is unreachable once retry.2 exists. None of this is in the contracts.
  Not handled here (decision): The Issue is decision-needed; documenting a selector and its precedence is a public interface promise.
  Options: A: document the existing precedence (current, else latest in history; a history key <id>.<n> names that one exactly) and add <id>.1 as the exact key of the first incarnation (folder <id>), with a scenario of a current task and several archived ones; B: document the existing precedence only; the first incarnation stays readable only through its folder once a later one exists; C: add an explicit --history <key> option to show instead of overloading the identity argument
  Recommendation: A: smallest interface addition that makes every incarnation addressable; the rest is documenting what the code does.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-tasks)",
  "code": "show_reused_name",
  "detail": "I-b3dd1c7f28455542a3dd2a1b9858ddc1 (decision-needed): 'task show <task-id>' gives no rule for a name reused across history incarnations (retry, retry.2, retry.3). The code (found_folder in store.py) already does: the current task first; else a dotted history key such as retry.2 names that incarnation exactly; a bare name names the latest incarnation in the history. So the first incarnation, history key 'retry', is unreachable once retry.2 exists. None of this is in the contracts.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed; documenting a selector and its precedence is a public interface promise."
  },
  "options": [
    "A: document the existing precedence (current, else latest in history; a history key <id>.<n> names that one exactly) and add <id>.1 as the exact key of the first incarnation (folder <id>), with a scenario of a current task and several archived ones",
    "B: document the existing precedence only; the first incarnation stays readable only through its folder once a later one exists",
    "C: add an explicit --history <key> option to show instead of overloading the identity argument"
  ],
  "recommendation": "A: smallest interface addition that makes every incarnation addressable; the rest is documenting what the code does.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-13T11:34:09Z

r3-tasks, early report: the four decision-needed Issues need three decisions (escalations 1-3); I continue with the other eleven Issues meanwhile.
1. I-6160711e (close refusal vs close recovery): recommend A, refuse the same close only once the task's folder is in the history (what the code already does); Spec-only alignment, changes no behaviour. I apply this as my fix of I-c7da60b2 (preferred-fix) unless you say otherwise.
2. I-70eaab12 + I-887c6e3f (same problem, --resume on an unrelated head: merge_diverged per requirement/entry vs not_resumable per contracts/scenario/code): recommend A, merge_diverged; not_resumable only when the head is the commit before the merge. Changes an observable refusal code of --resume.
3. I-b3dd1c7f (task show with a reused name): recommend A, document current, else latest in history, a key <id>.<n> exact, and add <id>.1 for the first incarnation. Adds a small interface promise.
The rendered chains are in the escalations above.

It carries escalation(s) 1, 2, 3.

## Answer to report(s) 1 of the task session, 2026-10-13T11:34:22Z

Escalations 1-3 (main agent), each your recommendation: 1 A — refuse the same close only once the task's folder is in the history; Spec-only alignment, also your fix of I-c7da60b2. 2 A — --resume on a head that is neither the merge commit nor the commit before it refuses merge_diverged (the developer's commits must be shown, as the guidance says for merge_diverged); not_resumable only when the head is the commit before the merge; align code, contracts, scenario and the main-session guidance's merge_incomplete paragraph if it names the old code. 3 A — task show <id>: current task, else latest in history; <id>.<n> exact, with <id>.1 the first incarnation.

## Task session, 2026-10-13: decisions taken without the developer

- **I-6471259 (preferred-fix)**: the update barrier recognizes a given check as the Spec
  validation when it runs `spec-validation` with no target (at most `--format json`) through a
  `concorde` command, a `concorde.py` script or `python -m concorde` (`merge.is_spec_validation`).
  A target or another tool is not recognized, since it may validate something else. Stated in the
  requirement's explanation, the merge contract and the scenario.
- **Escalation 2 (I-70eaab12, I-887c6e3f)**: applied as answered. The main-session guidance is left
  unchanged: it sends `not_resumable` to `--abort`, which is still right now that `not_resumable`
  means the branch is back at the commit before the merge; an unrelated head now answers
  `merge_diverged` at once, which the guidance already brings to the developer. Leaving it avoids
  touching module.main-session, which r3-task-session-main edits in parallel.
- **Escalation 1 / I-c7da60b2 / I-6160711e**: Spec-only, as answered. close-rerun split into
  close-rerun (record not yet written: the rerun closes the task) and new close-rerun-closed (a
  later step failed: the rerun finishes the rest and leaves the record unchanged).
- **I-064062c9 (preferred-fix)**: req.tasks.close-when-ended now requires stopping only runs whose
  run lock a process of this machine holds, as the close contract already said, and states that a
  run it cannot reach waits only in the lobby and is retired.
- **Escalation 3 / I-b3dd1c7f / I-8a4bdf9b**: new contract section "finding-a-task" (show and every
  task wait: current, else latest incarnation; `<id>.<n>` exact; `<id>.1` the first; what each wait
  answers for a task in the history); unknown_task row aligned; new scenario history-lookup.
  Side fix: a bare name now finds the latest incarnation even when an earlier numbered folder was
  removed by retention (found_folder used to return the bare-key folder when `<id>.2` was missing).
- **I-bed87720 (preferred-fix)**: the rebind wait opens the task folder and watches it through
  `/proc/self/fd/<n>`, so the watch never creates a folder and follows the folder if a close moves
  it; the next reread then ends the wait. Kept inside wait.py (module.tasks) rather than adding a
  no-create option to Tracing's `Changes`, which r3-kernel-tracing edits in parallel. Test patches
  the first read to close the task; it fails on the old code.
- **I-bc4c0157 (preferred-fix)**: record_session writes the session node first and binds the main
  after it; when the bind is refused, the node folder is removed. New scenario
  session-record-refused.
- **I-543079 (obvious-fix)**: the race is the test's: it required the task node's `ended_at` to
  equal `closed.at`, but the node ends at its own `now()` after the closing is logged, a later
  second under load (r2-spec's failure showed exactly that tuple). The test now requires
  `ended_at >= closed.at`.
- **I-1117b8ed**: Coordination's entry names project_review's committed review record beside Issues.
- **Suggestions applied**: I-97f157 (the Task store named as actor), I-e75522 (conditions first in
  worktree-ignored, log-commit-alone, merge-workspace-locked; the refusals moved to the
  explanations because a statement holds one SHALL), I-8b9c0d (a four-command lifecycle example
  first in Core concepts; retention moved to "Where a task lives", lock detail to "Locks").

## Report 2 to the main agent (Review流程), 2026-10-13T12:10:59Z

r3-tasks delivered: delivery commit 52cc75fd0 on concorde/r3-tasks (run r-20261013T115955-delivery-fb7b8306, ok), after task-validation r-20261013T114841-task_validation-b420a424: ready, no blocking findings (its structural warnings are on other Modules' files). Full suite on the final input: 1475 passed, 5 skipped. Resolves all 15 Issues in resolves; none stays open, none is not-actionable.
Decisions you answered (escalations 1-3, all A), as built:
- 1 (I-6160711e, I-c7da60b2): Spec-only. The same close is refused only once the folder is in the history. close-rerun is split by phase: new scenario close-rerun-closed.
- 2 (I-70eaab12, I-887c6e3f): --resume on a head that is neither commit now refuses with merge_diverged. not_resumable means only "back at the commit before the merge". Code, contracts, requirement, entry, scenario and test are aligned. I left the main-session guidance unchanged. It still sends not_resumable to --abort, which stays right; an unrelated head now gets merge_diverged at once, which the guidance already takes to the developer. This also avoids module.main-session, which r3-task-session-main edits.
- 3 (I-b3dd1c7f, with I-8a4bdf9b): new contract section finding-a-task. show and every task wait look up the current task, else the latest incarnation. <id>.<n> is exact, and <id>.1 is the first. It says what each wait answers for a task in the history, and the unknown_task row is aligned. New scenario history-lookup. Side fix: a bare name now finds the latest incarnation even after retention removed an earlier numbered one.
Decisions I took:
- I-6471259: the update barrier counts a given check as the Spec validation when it runs `spec-validation` with no target (optionally --format json) via `concorde`, a `concorde.py` script or `python -m concorde`.
- I-064062c9: the close stops only runs whose run lock a process of this machine holds. A run it cannot reach waits in the lobby and is retired.
- I-bed87720: the rebind wait watches the task folder through an open descriptor (/proc/self/fd), so it never recreates a moved folder. This stays in wait.py, not in Tracing's Changes.
- I-bc4c0157: the session node is written before the main is bound and removed if the bind is refused. New scenario session-record-refused.
- I-543079: it was the test's race. The test required node ended_at == closed.at, but the node ends after the closing is logged. Now it requires >=.
- I-1117b8ed: Coordination's entry names project_review's committed review record.
- Suggestions I-97f157, I-e75522 and I-8b9c0d were applied: the Task store is named as the actor, conditions come first, and a lifecycle example comes first, with retention and locks moved to the design sections.
Details are in the decision log. Nothing is open.

## Closed: merged, 2026-10-13T14:43:40Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 52cc75fd0e110ec0c801d5d305315bb33121ea22 into main and closed it as merged. Nobody answers a report after that.
