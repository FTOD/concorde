# Decision log: r3-execution

Goal: Fix the remaining open Issues of Execution, Checks, Operations and Execution commands (medium and low) found by the complete project_review

## Task brief (main agent, 2026-10-13)

Round 3. Rounds 1 and 2 fixed every critical and high Issue. The developer decided (2026-10-13)
that the main agent now resolves everything it can settle itself: this task resolves **every open
Issue owned by its Modules** (18, listed in `resolves`; 4 of them decision-needed), all medium or
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

## Escalated to the main agent, 2026-10-13T11:33:59Z

- **task-session** task session (task r3-execution): `issue_decision_needed`
  I-458160af0a4f5b6fbe4091660dcc2116 (module.checks, medium): timing.md lists interval_record(...) as a library entry point without an input contract. Findings: its only caller is tests/concorde/support/pytest_timing.py; the code takes keyword-only name, trace_id, parent_id=None, layer='C', started_at, start_ns, end_ns, status='ok' and always stamps process_id=os.getpid(), which the pytest plugin then overwrites for xdist units measured in another process. A negative interval yields a negative duration_ns, which summarize ignores.
  Not handled here (decision): The Issue is decision-needed: specifying the adapter's parameters creates new interface promises of Checks.
  Options: A: specify the existing keyword-only signature as the contract, plus an optional process_id parameter (default the calling process) replacing the caller's override: start_ns/end_ns are that process's monotonic nanoseconds, started_at an RFC 3339 UTC wall time for correlation, end_ns null gives a null duration, end_ns before start_ns is refused with ValueError; one concrete example in timing.md. Adds promises, changes none.; B: drop interval_record from the public entry points and move it into the test support that alone uses it. Removes a listed (but unused outside tests) entry point.
  Recommendation: A: it documents what the code does, fixes the cross-process process_id gap the plugin works around, and changes no promise users rely on.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-execution)",
  "code": "issue_decision_needed",
  "detail": "I-458160af0a4f5b6fbe4091660dcc2116 (module.checks, medium): timing.md lists interval_record(...) as a library entry point without an input contract. Findings: its only caller is tests/concorde/support/pytest_timing.py; the code takes keyword-only name, trace_id, parent_id=None, layer='C', started_at, start_ns, end_ns, status='ok' and always stamps process_id=os.getpid(), which the pytest plugin then overwrites for xdist units measured in another process. A negative interval yields a negative duration_ns, which summarize ignores.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: specifying the adapter's parameters creates new interface promises of Checks."
  },
  "options": [
    "A: specify the existing keyword-only signature as the contract, plus an optional process_id parameter (default the calling process) replacing the caller's override: start_ns/end_ns are that process's monotonic nanoseconds, started_at an RFC 3339 UTC wall time for correlation, end_ns null gives a null duration, end_ns before start_ns is refused with ValueError; one concrete example in timing.md. Adds promises, changes none.",
    "B: drop interval_record from the public entry points and move it into the test support that alone uses it. Removes a listed (but unused outside tests) entry point."
  ],
  "recommendation": "A: it documents what the code does, fixes the cross-process process_id gap the plugin works around, and changes no promise users rely on.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:33:59Z

- **task-session** task session (task r3-execution): `issue_decision_needed`
  I-8678cf27790a5d709030d43816883520 (module.execution, medium): req.execution.inputs-same-workspace and runner.md say a result an older Concorde wrote under another contract version is refused like any inadmissible input, yet admission checks only current-contract conformance and no version field is saved, so an older result whose fields still conform is admitted.
  Not handled here (decision): The Issue is decision-needed: the choice changes the compatibility promise of --input admission.
  Options: A (conformance): admission means the saved result satisfies the current run result contract; rewrite the sentence so an older result is refused only when it no longer conforms. Narrows a promise (the 'older version always refused' claim); no code change.; B (exact version): save the producing contract version in result.json, compare it on admission and refuse unversioned results. Adds a field and a contract version bump; existing saved results become inadmissible.
  Recommendation: A: runs are short-lived trace data (the Spec already says no version field or migration exists), the project is in rapid iteration without compatibility, and A matches the code.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-execution)",
  "code": "issue_decision_needed",
  "detail": "I-8678cf27790a5d709030d43816883520 (module.execution, medium): req.execution.inputs-same-workspace and runner.md say a result an older Concorde wrote under another contract version is refused like any inadmissible input, yet admission checks only current-contract conformance and no version field is saved, so an older result whose fields still conform is admitted.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: the choice changes the compatibility promise of --input admission."
  },
  "options": [
    "A (conformance): admission means the saved result satisfies the current run result contract; rewrite the sentence so an older result is refused only when it no longer conforms. Narrows a promise (the 'older version always refused' claim); no code change.",
    "B (exact version): save the producing contract version in result.json, compare it on admission and refuse unversioned results. Adds a field and a contract version bump; existing saved results become inadmissible."
  ],
  "recommendation": "A: runs are short-lived trace data (the Spec already says no version field or migration exists), the project is in rapid iteration without compatibility, and A matches the code.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:34:00Z

- **task-session** task session (task r3-execution): `issue_decision_needed`
  I-daf5e02ca7ee5e3dba6f60fa2463ffac (module.execution, medium): module.md 'The runs of a workspace' tells the preparer to send SIGTERM itself, but the only process number Execution records is host_pid, valid only in the runner's own PID namespace. Findings: the task close (coordination/tasks/store.py stop_task) already signals the holders of the run lock that /proc/locks shows in its own namespace (kernel locks.holder_pids), never host_pid, and skips a run whose holder it cannot see.
  Not handled here (decision): The Issue is decision-needed: it asks to choose the supported cancellation boundary of Execution's records-only integration.
  Options: A: state in module.md (and runner.md's host_pid row) that the preparer finds the runner to signal as the holder of the run lock that the operating system's lock table shows in the preparer's own PID namespace, never by host_pid; when no holder is visible there, the preparer cannot cancel the run and waits on the run lock instead. Matches the existing close; adds no record.; B: restrict cancellation to the process that started the run (it holds the process handle) and say other observers cannot cancel.
  Recommendation: A: it is what the task close already does, follows from req.execution.run-lock-held (the holder is the runner), and B would forbid the close's existing behaviour.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-execution)",
  "code": "issue_decision_needed",
  "detail": "I-daf5e02ca7ee5e3dba6f60fa2463ffac (module.execution, medium): module.md 'The runs of a workspace' tells the preparer to send SIGTERM itself, but the only process number Execution records is host_pid, valid only in the runner's own PID namespace. Findings: the task close (coordination/tasks/store.py stop_task) already signals the holders of the run lock that /proc/locks shows in its own namespace (kernel locks.holder_pids), never host_pid, and skips a run whose holder it cannot see.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: it asks to choose the supported cancellation boundary of Execution's records-only integration."
  },
  "options": [
    "A: state in module.md (and runner.md's host_pid row) that the preparer finds the runner to signal as the holder of the run lock that the operating system's lock table shows in the preparer's own PID namespace, never by host_pid; when no holder is visible there, the preparer cannot cancel the run and waits on the run lock instead. Matches the existing close; adds no record.",
    "B: restrict cancellation to the process that started the run (it holds the process handle) and say other observers cannot cancel."
  ],
  "recommendation": "A: it is what the task close already does, follows from req.execution.run-lock-held (the holder is the runner), and B would forbid the close's existing behaviour.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:34:00Z

- **task-session** task session (task r3-execution): `issue_decision_needed`
  I-f404bffae0545b9593ae18ae0d6d71d9 (module.checks, medium): run_checks writes each check's node <trace_directory>/<check id>/ without saying what happens when that node already exists; today a second call silently overwrites output.log and trace.json that an earlier result names. Findings: every caller passes a fresh directory per call (a worker round's checks folder, a run's checks folder, validation's per-run folder whose ordinary and selective calls keep distinct check ids).
  Not handled here (decision): The Issue is decision-needed: refusal, attempt numbering and replacement are different public policies of the Checks service.
  Options: A: the caller gives each call a location where none of its checks' nodes exists yet; the service refuses, before the first command, a check whose node already exists with a CheckError, leaving the earlier node untouched; plus a scenario.; B: the service numbers attempts (<check id>/<n>/) and never refuses; changes the node layout Tracing and callers read.; C: specify replacement: a later call replaces the node, and the earlier result's log reference may then name the new log.
  Recommendation: A: no caller relies on reuse, earlier evidence stays intact, and it adds a refusal without changing the layout.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-execution)",
  "code": "issue_decision_needed",
  "detail": "I-f404bffae0545b9593ae18ae0d6d71d9 (module.checks, medium): run_checks writes each check's node <trace_directory>/<check id>/ without saying what happens when that node already exists; today a second call silently overwrites output.log and trace.json that an earlier result names. Findings: every caller passes a fresh directory per call (a worker round's checks folder, a run's checks folder, validation's per-run folder whose ordinary and selective calls keep distinct check ids).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: refusal, attempt numbering and replacement are different public policies of the Checks service."
  },
  "options": [
    "A: the caller gives each call a location where none of its checks' nodes exists yet; the service refuses, before the first command, a check whose node already exists with a CheckError, leaving the earlier node untouched; plus a scenario.",
    "B: the service numbers attempts (<check id>/<n>/) and never refuses; changes the node layout Tracing and callers read.",
    "C: specify replacement: a later call replaces the node, and the earlier result's log reference may then name the new log."
  ],
  "recommendation": "A: no caller relies on reuse, earlier evidence stays intact, and it adds a refusal without changing the layout.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-13T11:34:09Z

r3-execution: early escalation of the 4 decision-needed Issues (escalations 1-4); I continue with the other 14 meanwhile.

1. I-458160af (Checks, timing interval_record has no input contract). Options: A specify the existing keyword-only signature plus an optional process_id parameter (default the calling process), null end gives null duration, end before start refused, one example; B move it out of the public entry points into the test support, its only user. Recommendation A (adds promises, changes none).
2. I-8678cf27 (Execution, "older contract version refused" has no discriminator). Options: A conformance: an older result is refused only when it no longer satisfies the current contract (narrows the stated promise, matches code, no code change); B save and compare the producing contract version (new field, version bump). Recommendation A (runs are short-lived trace data; rapid-iteration, no compatibility).
3. I-daf5e02c (Execution, cross-namespace SIGTERM target). Options: A state that the preparer signals the holder of the run lock that the lock table shows in its own PID namespace, never host_pid, and cannot cancel a run whose holder it does not see (what the task close already does); B only the starting process may cancel. Recommendation A (matches existing close; B would forbid it).
4. I-f404bffa (Checks, repeat call reusing a check's trace node). Options: A refuse before the first command a check whose node already exists, earlier node untouched, caller gives a fresh location; B numbered attempt folders (layout change); C specified replacement. Recommendation A (every current caller already passes a fresh folder).

None of the options changes an earlier developer decision. Options 2A narrows a promise (the unconditional refusal of older results); 1B and 3B remove or restrict behaviour.

It carries escalation(s) 1, 2, 3, 4.

## Answer to report(s) 1 of the task session, 2026-10-13T11:34:28Z

Escalations 1-4 (main agent), each your recommendation: 1 A — specify interval_record's keyword-only signature plus an optional process_id, null end gives null duration, end before start refused, one example. 2 A — an older result is refused only when it no longer satisfies the current contract (rapid-iteration: no compatibility; run results are short-lived trace data). 3 A — the preparer signals the run-lock holder its own PID namespace's lock table shows, never host_pid, and cannot cancel a run whose holder it does not see. 4 A — refuse before the first command a check whose node already exists, earlier node untouched.

## Task session decisions, 2026-10-13

- **I-5df335be** (obvious-fix): the two tests that start a detached `task-validation` now wait, with the existing `wait_ended`, until the runner's run lock is gone before the temporary project is removed. The same race was in `test_a_waiting_run_queues_behind_the_running_one`, fixed alike.
- **I-16ce8449** (preferred-fix): every error leaving `run_checks` now carries the refused trace writes in its `trace_failures` attribute (set on the same exception object, so its identity is kept), the earlier checks' first; `service_error` puts them as `trace-write` evidence in every branch (OSError and unexpected errors too). Chosen over wrapping the exception because service.md promises the error goes on unchanged.
- **I-8114071** (preferred-fix): `project_python` makes the worktree absolute with `os.path.abspath` (no symlink resolution, so a venv's own `bin/python` link is kept) before building candidates.
- **I-cfa669db** (preferred-fix): `checks_files(worktree, modules)` skips other Modules' entries before judging them; `configured_checks` passes its narrowing through. Unrestricted reads and `validate_checks` still judge every file.
- **I-458160af** (decided A): `interval_record` gains `process_id` (default the calling process), refuses an end before the start and an unknown status with `ValueError`; timing.md gains "Adapting an interval" with the signature table and an example, and scenario.checks.timing-interval. The pytest timing plugin now passes `process_id` instead of overwriting the record's field (small follow-on in tests/concorde/support).
- **I-f404bffa** (decided A): new code `check_node_exists`, refused before the first command when a kept check's node already exists; scenario.checks.check-node-exists. The service tests' helper now gives each call a fresh directory, as every real caller already does.
- **I-492596e0 + I-c691a2d5** (preferred-fix): `open_checkout` takes an `owner` that receives the Checkout before `git worktree add` starts; the runner registers its removal at once. `Checkout.created` says whether Git finished; a checkout Git did not finish is removed directly and pruned, with evidence only of what is left. Once Git made the checkout, the runner records its commit, `checkout` evidence and the submodule evidence so far even when a submodule or the resolver then fails. Scenarios unbound-setup-failed and unbound-checkout-interrupted added.
- **I-bf6e0070** (preferred-fix): new `runs.validate_result` (schema + error null exactly when ok + error level = kind), used by both publication and `admit_inputs`.
- **I-04ff0cbc** (preferred-fix): trace-started/trace-ended state required attempts with the refusal handling; unbound-prepared split into ordered execution until failure or cancellation and a new gate req.execution.unbound-prepared-first; error-detail names the commit only once the checkout exists; run-lock-held holds until the writes were attempted.
- **I-9b02bc70** (preferred-fix): scenario setups state the exits, the steps ending ok and the merge's lock timing; the unbound-run example admits only an ok result.
- **I-bcac9b1b** (preferred-fix): run-trace example ends with an `output` step that stops, with delivery's real summary form; the run-result example's error detail ends with `(Modules: module.http)`.
- **I-8678cf27** (decided A) and **I-daf5e02c** (decided A): Spec text in requirements.md, runner.md and module.md; a test asserts the lock table names the runner as the run lock's holder.
- **I-947e0a9f** (preferred-fix): took the Issue's second repair: the detached-namespace paragraph no longer states the task session's or main agent's sandboxing (their owners' promises) instead of adding a context selection of Coordination's task-session document to Execution.
- **I-1ecd4c8c** (suggestion, applied): the "Unbound runs" and "Long runs" concept sections moved from Core concepts into "Running unbound" and "Following a long run", after the normal walkthrough; anchors `unbound-runs`, `long-runs` and the concept anchors kept so other Modules' links still resolve.
- **I-e7942ed2**: already fixed: checks/module.md.json includes `document.kernel.contracts` with the canonical-path reason (commit b6e2a82a8, round 2).
- **I-74330614**: already fixed: operations/module.md's realization.operations.tests is two sentences with no inventory or Method claim (commit 6c38b2d77, round 2).

## Report 2 to the main agent (Review流程), 2026-10-13T12:11:31Z

r3-execution delivered: delivery commit 2e92aafebf4c879ddf2cc76c42c12a1cd07a3ee7 (run r-20261013T120027-delivery-a62c8041, ok). task-validation was ready with no blocking finding; the full suite passed on the final input (1479 passed, 5 skipped). Please merge.

All 18 Issues in resolves are handled (details per Issue in the decision log):
- Decided A per your answer: I-458160af (interval_record contract + process_id, scenario.checks.timing-interval), I-8678cf27 (admission = current-contract conformance), I-daf5e02c (preparer signals the run-lock holder from its own namespace's lock table, never host_pid; a test asserts the holder is the runner), I-f404bffa (new check_node_exists refusal before any command, scenario.checks.check-node-exists).
- Code fixes: I-5df335be (detached-run tests wait for the runner's end; same race fixed in a second test), I-16ce8449 (every error leaving run_checks carries trace_failures on the same exception object; service_error reports them in every branch), I-8114071 (absolute interpreter for a relative worktree), I-cfa669db (narrowed reads judge only the selected Modules' checks files), I-492596e0 + I-c691a2d5 (the runner owns the checkout before git worktree add starts; once Git made it, the result names the commit and checkout evidence even when setup fails; two new scenarios), I-bf6e0070 (shared runs.validate_result for publication and input admission: error null exactly when ok, level = kind).
- Spec fixes: I-04ff0cbc (requirements state attempted trace writes, preparation split into ordered execution + new gate req.execution.unbound-prepared-first, commit in the actor only once the checkout exists, run lock held until the writes were attempted), I-9b02bc70 (scenario setups), I-bcac9b1b (contract examples).
- Preferred-fix choice to note: I-947e0a9f took the Issue's second repair: Execution no longer states the task session's/main agent's sandboxing (their owners' promises) rather than adding Coordination's task-session document to Execution's context.
- Suggestion applied: I-1ecd4c8c (Unbound runs / Long runs moved after the normal walkthrough; anchors kept so outside links resolve).
- Already fixed in round 2, no change: I-e7942ed2 (checks already includes document.kernel.contracts, b6e2a82a8), I-74330614 (operations entry has no test inventory, 6c38b2d77).

Small follow-on outside the Modules: tests/concorde/support/pytest_timing.py now passes process_id to interval_record instead of overwriting the field. Nothing is open.

## Closed: merged, 2026-10-13T14:44:06Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 2e92aafebf4c879ddf2cc76c42c12a1cd07a3ee7 into main and closed it as merged. Nobody answers a report after that.
