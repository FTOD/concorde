# Decision log: fix-dogfood-e2e

Goal: Fix every open Issue of Dogfood scenarios and E2E found by the first full project_review, critical first (session evidence overwritten by runs started in the same second)

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08) to fix the project's known open Issues. This task resolves every
open Issue owned by its Modules (listed in the task record's `resolves`), found by the first full
project_review, r-20261008T024839-project_review-a7857ff6 (unbound). Read each with
`concorde issues show`; the review's panel and code-review reports are in
`.concorde/unbound/r-20261008T024839-project_review-a7857ff6/` of the primary worktree.

How to handle them, by tier:
- **decision-needed**: read them first and escalate them all **together in one report, early**,
  each with what you found, the options and your recommendation; continue with the rest while
  waiting. Never settle one yourself.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- **suggestion**: apply unless it turns out wrong; then leave it open and say why in the log.
- Fix by **severity**, critical and high first.
- An Issue that turns out not to hold, or that is already fixed: say so with evidence in the log
  and in your report; the main agent closes it.
- A fix that needs a change outside the task's Modules: escalate it rather than widening the task,
  unless it is a small mechanical follow-on (a link, a test fixture).

Other tasks running in parallel: worker-transient-retry (workers, project-review, method),
main-rename-hook (main-session, coordination, tasks) and the other Issue-fixing tasks of today
(views, dogfood/e2e, task-session, operations/commands, delivery). Deliver with `task-validation`
then `delivery`; run the full suite once on the final input.

## Escalated to the main agent, 2026-10-08T06:20:43Z

- **task-session** task session (task fix-dogfood-e2e): `issue_system_defect_scope`
  I-00a182de358b5d0e9557cb6c47b23a3a (medium): Dogfood scenarios' evaluation requires at least one defect report under .concorde/runs/defects/ passing issues report --check and recorded by a throwaway clone, but Dogfooding says a defect of the Issue system is never written as a defect report; it travels as a bare error chain (.concorde/runs/defects/<name>.error.json). A scenario whose fault breaks the Issue system therefore cannot pass even when the session follows Dogfooding exactly. Today the only scenario (write-hook-rw-directories) breaks the harness, not the Issue system.
  Not handled here (decision): The Issue is decision-needed: the choice changes what the Module promises, which the task brief reserves above the task session.
  Options: A: exclude Issue-system faults: the Purpose and the scenario description say a scenario's fault must not lie in the Issue system (store, concorde issues, the MCP Issue tools), since its evaluation relies on that system; no code change; B: support them: a scenario field (e.g. expect.error_chain) switches reports_checked/reports_accepted to checking a bare error chain file instead, independent of the Issue system
  Recommendation: A: no scenario needs B yet, and B adds an evaluation path nothing exercises; add it with the first such scenario

```json
{
  "level": "task-session",
  "actor": "task session (task fix-dogfood-e2e)",
  "code": "issue_system_defect_scope",
  "detail": "I-00a182de358b5d0e9557cb6c47b23a3a (medium): Dogfood scenarios' evaluation requires at least one defect report under .concorde/runs/defects/ passing issues report --check and recorded by a throwaway clone, but Dogfooding says a defect of the Issue system is never written as a defect report; it travels as a bare error chain (.concorde/runs/defects/<name>.error.json). A scenario whose fault breaks the Issue system therefore cannot pass even when the session follows Dogfooding exactly. Today the only scenario (write-hook-rw-directories) breaks the harness, not the Issue system.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: the choice changes what the Module promises, which the task brief reserves above the task session."
  },
  "options": [
    "A: exclude Issue-system faults: the Purpose and the scenario description say a scenario's fault must not lie in the Issue system (store, concorde issues, the MCP Issue tools), since its evaluation relies on that system; no code change",
    "B: support them: a scenario field (e.g. expect.error_chain) switches reports_checked/reports_accepted to checking a bare error chain file instead, independent of the Issue system"
  ],
  "recommendation": "A: no scenario needs B yet, and B adds an evaluation path nothing exercises; add it with the first such scenario",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-08T06:20:43Z

- **task-session** task session (task fix-dogfood-e2e): `malformed_scenario_policy`
  I-308fcdd16fa05b869ea45473b77a1f1f (medium): the Spec names only unknown_scenario. The runner maps an unreadable or non-JSON file to unknown_scenario, raises an unspecified invalid_scenario for missing top-level fields and checks no nested shape (fault.edits, expect.types, project.rev...).
  Not handled here (decision): The Issue is decision-needed: the choice changes what the Module promises, which the task brief reserves above the task session.
  Options: A: specify and implement full validation when a scenario is read (by every command, before prepare clones anything): a missing file is unknown_scenario naming the known ones; a file that is not JSON, not an object, lacks a field or has a field of the wrong shape (project.repository/rev strings, fault.summary string, fault.edits a non-empty list of {file, old, new} strings, prompt string, expect.types/basis/unchanged lists of strings) is invalid_scenario naming the file and the field; B: specify the current partial behaviour as is (non-JSON as unknown_scenario, only top-level fields checked)
  Recommendation: A: a scenario author gets a precise refusal before a long preparation, and the test of every scenario then checks shapes too

```json
{
  "level": "task-session",
  "actor": "task session (task fix-dogfood-e2e)",
  "code": "malformed_scenario_policy",
  "detail": "I-308fcdd16fa05b869ea45473b77a1f1f (medium): the Spec names only unknown_scenario. The runner maps an unreadable or non-JSON file to unknown_scenario, raises an unspecified invalid_scenario for missing top-level fields and checks no nested shape (fault.edits, expect.types, project.rev...).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: the choice changes what the Module promises, which the task brief reserves above the task session."
  },
  "options": [
    "A: specify and implement full validation when a scenario is read (by every command, before prepare clones anything): a missing file is unknown_scenario naming the known ones; a file that is not JSON, not an object, lacks a field or has a field of the wrong shape (project.repository/rev strings, fault.summary string, fault.edits a non-empty list of {file, old, new} strings, prompt string, expect.types/basis/unchanged lists of strings) is invalid_scenario naming the file and the field",
    "B: specify the current partial behaviour as is (non-JSON as unknown_scenario, only top-level fields checked)"
  ],
  "recommendation": "A: a scenario author gets a precise refusal before a long preparation, and the test of every scenario then checks shapes too",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-08T06:20:43Z

- **task-session** task session (task fix-dogfood-e2e): `nonobject_worker_configuration`
  I-440d25176c7d5b7aad684a13303ecf01 (medium): without --worker-model, prepare copies this checkout's .concorde/workers.json minus runtime. The code already refuses a file that is no JSON object with worker_configuration_unreadable (it must take fields out of an object), and scenario.e2e.runtime-failures says so, but Preparing a test project says that code is only for a file that 'cannot be read as JSON' and sends contract-invalid configurations to Workers' config_invalid.
  Not handled here (decision): The Issue is decision-needed: the choice changes what the Module promises, which the task brief reserves above the task session.
  Options: A: E2E refuses at loading: worker_configuration_unreadable covers a file that cannot be read as a JSON object (the current code); only a JSON object goes on to Workers' check, whose config_invalid covers the rest. Spec wording only, nothing in Workers changes; B: hand non-object JSON to Workers' check unchanged so it is refused with config_invalid
  Recommendation: A: E2E must read fields out of the file before it can build the configuration Workers checks, so the object shape is its own reading precondition; it matches the code and touches no other Module

```json
{
  "level": "task-session",
  "actor": "task session (task fix-dogfood-e2e)",
  "code": "nonobject_worker_configuration",
  "detail": "I-440d25176c7d5b7aad684a13303ecf01 (medium): without --worker-model, prepare copies this checkout's .concorde/workers.json minus runtime. The code already refuses a file that is no JSON object with worker_configuration_unreadable (it must take fields out of an object), and scenario.e2e.runtime-failures says so, but Preparing a test project says that code is only for a file that 'cannot be read as JSON' and sends contract-invalid configurations to Workers' config_invalid.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: the choice changes what the Module promises, which the task brief reserves above the task session."
  },
  "options": [
    "A: E2E refuses at loading: worker_configuration_unreadable covers a file that cannot be read as a JSON object (the current code); only a JSON object goes on to Workers' check, whose config_invalid covers the rest. Spec wording only, nothing in Workers changes",
    "B: hand non-object JSON to Workers' check unchanged so it is refused with config_invalid"
  ],
  "recommendation": "A: E2E must read fields out of the file before it can build the configuration Workers checks, so the object shape is its own reading precondition; it matches the code and touches no other Module",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-08T06:20:43Z

- **task-session** task session (task fix-dogfood-e2e): `fault_reinjection_precondition`
  I-52177b983d425f009a5359f381bfd1c7 (medium): scenario.dogfood-scenarios.fault-reinjected promises that injecting the same fault again is refused with fault_not_applicable, but the only rule is literal exact-once matching: a fault whose new text still contains its old text once (A -> AB) can be injected again.
  Not handled here (decision): The Issue is decision-needed: the choice changes what the Module promises, which the task brief reserves above the task session.
  Options: A: narrow the scenario to the matching rule: GIVEN a clone into which a fault whose new text no longer contains its old text was injected, reinjection is refused naming the file and the count 0; and (with I-308 A) a scenario is invalid when an edit's new text contains its old text, so every valid scenario's fault is refused on reinjection; B: add a separate reinjection prohibition (e.g. refuse a clone whose history already holds an 'Inject fault:' commit)
  Recommendation: A: it keeps one simple rule (exact text, exactly once) and the scenario-shape check makes reinjection always refused for valid scenarios

```json
{
  "level": "task-session",
  "actor": "task session (task fix-dogfood-e2e)",
  "code": "fault_reinjection_precondition",
  "detail": "I-52177b983d425f009a5359f381bfd1c7 (medium): scenario.dogfood-scenarios.fault-reinjected promises that injecting the same fault again is refused with fault_not_applicable, but the only rule is literal exact-once matching: a fault whose new text still contains its old text once (A -> AB) can be injected again.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: the choice changes what the Module promises, which the task brief reserves above the task session."
  },
  "options": [
    "A: narrow the scenario to the matching rule: GIVEN a clone into which a fault whose new text no longer contains its old text was injected, reinjection is refused naming the file and the count 0; and (with I-308 A) a scenario is invalid when an edit's new text contains its old text, so every valid scenario's fault is refused on reinjection",
    "B: add a separate reinjection prohibition (e.g. refuse a clone whose history already holds an 'Inject fault:' commit)"
  ],
  "recommendation": "A: it keeps one simple rule (exact text, exactly once) and the scenario-shape check makes reinjection always refused for valid scenarios",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-08T06:20:44Z

- **task-session** task session (task fix-dogfood-e2e): `repeated_run_verdict`
  I-6487da1620325fb6892a742b596c3f97 (medium): run may be repeated in one scenario directory; each adds a session and evaluates again, but reports and project state accumulate, so a later session that reports nothing still passes on an earlier session's reports, while the rationale speaks of 'one passing session execution'.
  Not handled here (decision): The Issue is decision-needed: the choice changes what the Module promises, which the task brief reserves above the task session.
  Options: A: cumulative: the evaluation judges the scenario directory's accumulated state (every session run there so far); the rationale says so, and to judge one session execution alone the developer prepares a fresh directory with --name. Spec wording only; B: independent trials: each run evaluates only reports written since its session started, and preparation state is reset or re-baselined per run
  Recommendation: A: a session's effects (branches, tasks, Issues) cannot be undone cleanly between runs, so B would judge a later session in an already-changed project anyway; --name already gives a fresh trial

```json
{
  "level": "task-session",
  "actor": "task session (task fix-dogfood-e2e)",
  "code": "repeated_run_verdict",
  "detail": "I-6487da1620325fb6892a742b596c3f97 (medium): run may be repeated in one scenario directory; each adds a session and evaluates again, but reports and project state accumulate, so a later session that reports nothing still passes on an earlier session's reports, while the rationale speaks of 'one passing session execution'.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: the choice changes what the Module promises, which the task brief reserves above the task session."
  },
  "options": [
    "A: cumulative: the evaluation judges the scenario directory's accumulated state (every session run there so far); the rationale says so, and to judge one session execution alone the developer prepares a fresh directory with --name. Spec wording only",
    "B: independent trials: each run evaluates only reports written since its session started, and preparation state is reset or re-baselined per run"
  ],
  "recommendation": "A: a session's effects (branches, tasks, Issues) cannot be undone cleanly between runs, so B would judge a later session in an already-changed project anyway; --name already gives a fresh trial",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-08T06:20:44Z

- **task-session** task session (task fix-dogfood-e2e): `owners_result_deadline`
  I-ce28ff3bae305db28a973cb4c1cf9489 (medium): the owners case launches its run with --wait 1200 (twice its 600 s limit, counted from the launch) but waits for the run's result only 600 s from releasing the lock. When a competing run takes the lock right after the release and holds it, the run's refusal (workspace_busy) can come up to ~1200 s after the release, so the case stops with live_timeout instead of the promised workspace_busy.
  Not handled here (decision): The Issue is decision-needed: the choice changes what the Module promises, which the task brief reserves above the task session.
  Options: A: the case waits for the result for the run's queue wait (1200 s) counted from the release, which always covers the rest of the run's wait, so a refusal is always seen; live_timeout then means no result within that time; B: keep 600 s and narrow the promise: workspace_busy for the case's own run only when the refusal arrives within the limit, otherwise live_timeout
  Recommendation: A: one constant, and both stopping conditions stay satisfiable as written; only a pathological competing run makes the case wait longer

```json
{
  "level": "task-session",
  "actor": "task session (task fix-dogfood-e2e)",
  "code": "owners_result_deadline",
  "detail": "I-ce28ff3bae305db28a973cb4c1cf9489 (medium): the owners case launches its run with --wait 1200 (twice its 600 s limit, counted from the launch) but waits for the run's result only 600 s from releasing the lock. When a competing run takes the lock right after the release and holds it, the run's refusal (workspace_busy) can come up to ~1200 s after the release, so the case stops with live_timeout instead of the promised workspace_busy.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: the choice changes what the Module promises, which the task brief reserves above the task session."
  },
  "options": [
    "A: the case waits for the result for the run's queue wait (1200 s) counted from the release, which always covers the rest of the run's wait, so a refusal is always seen; live_timeout then means no result within that time",
    "B: keep 600 s and narrow the promise: workspace_busy for the case's own run only when the refusal arrives within the limit, otherwise live_timeout"
  ],
  "recommendation": "A: one constant, and both stopping conditions stay satisfiable as written; only a pathological competing run makes the case wait longer",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-08T06:20:54Z

fix-dogfood-e2e, early escalation (task brief: decision-needed Issues together, early). Six decision-needed Issues need answers; I continue with the other 18 meanwhile.

1. issue_system_defect_scope — I-00a182de (scenarios vs. Issue-system defects, whose reports Dogfooding sends as bare error chains). Options: A exclude Issue-system faults from scenarios (Spec wording only); B add an alternate evaluation path for bare error chains. Recommend A.
2. malformed_scenario_policy — I-308fcdd1. Options: A specify and implement full validation on read: missing file → unknown_scenario; not JSON/not object/missing field/wrong nested shape → invalid_scenario naming file and field; B document the current partial behaviour. Recommend A.
3. nonobject_worker_configuration — I-440d2517. Options: A worker_configuration_unreadable covers "cannot be read as a JSON object" (current code; Spec wording only, Workers untouched); B pass non-object to Workers for config_invalid. Recommend A.
4. fault_reinjection_precondition — I-52177b98. Options: A narrow the scenario to the exact-once rule (a fault whose new text drops its old text; reinjection refused with count 0) and, with 2A, make an edit whose new contains its old an invalid scenario; B add a separate reinjection prohibition. Recommend A.
5. repeated_run_verdict — I-6487da16. Options: A cumulative: the evaluation judges the directory's accumulated state, and a fresh trial is a new --name directory (Spec wording only); B independent trials with per-run report attribution and reset. Recommend A.
6. owners_result_deadline — I-ce28ff3b (result wait 600 s from release vs. run queue wait 1200 s from launch). Options: A wait for the result for the run's queue wait (1200 s) from the release so workspace_busy is always observable; B keep 600 s and narrow the workspace_busy promise. Recommend A.

Full chains are in the decision log (escalations 1–6).

It carries escalation(s) 1, 2, 3, 4, 5, 6.

## Answer to report(s) 1 of the task session, 2026-10-08T06:21:59Z

Escalations 1-6 (main agent), each your recommendation: 1 A (exclude Issue-system faults from scenarios), 2 A (full validation on read: unknown_scenario / invalid_scenario naming file and field), 3 A (worker_configuration_unreadable covers a non-object; Spec wording only), 4 A (narrow to the exact-once rule; an edit whose new text contains its old is an invalid scenario), 5 A (cumulative verdict; a fresh trial is a new --name directory), 6 A (wait for the result for the run's queue wait, 1200 s, from the release).

## Task session decisions (2026-10-08)

- Escalations 1-6 (the six decision-needed Issues) were answered by the main agent with option A each; carried out as answered.
- I-561da75c (critical, preferred-fix): a session directory is created exclusively by a new `fresh_directory` in `scripts/e2e/common.py`, named after the time to the microsecond with `-2`, `-3`… on collision, rather than a random suffix: the name stays a time, which Headless sessions' `sessions/<time>/` describes, and terminates even under a frozen clock. Used by `dogfood run` and also by `session start` in `e2e.py` (same defect; the name still reads as `<time>`, so Headless sessions' Spec needs no change).
- I-08d24b88 (high, preferred-fix): the owners case identifies its run as the new run of the task whose runner (`host_pid` of the run progress file, specified by Execution) descends from the launcher process (the case's own child, or the owner's `claude` process), read from Linux `/proc`. Chosen over Execution's private `CONCORDE_RUN_ID` handoff (unspecified, another Module's internal) and over refusing ambiguity (cannot tell which run is the case's). Limitation stated in the Spec: a launcher in another PID namespace (sandbox) is never found and ends `live_timeout`. An owner that ends before its run appears now stops the case with `session_failed` (its run loses its ancestry).
- I-e75b39f1 (high, preferred-fix): `test_directory` refuses a name that is empty, `.`, `..` or holds `/` with a new code `invalid_name`, checked first by both `prepare` and `dogfood prepare`; an existing path is tested with `lexists`, so a symbolic link (dangling or not) is `project_exists`/`scenario_exists`. An empty `--name` is now treated as given (refused) rather than falling back to the default.
- I-fb3d5ed5 (high, preferred-fix): Dogfood scenarios includes `document.e2e.module` (kind document) and links Preparing a test project; no `uses` of its parent added.
- I-273e63e9 (preferred-fix): a refusal's detail keeps the whole stdout and stderr, untruncated, in evaluation.json (no separate artifact file: the evaluation is the place the Spec names).
- I-db9e53ec (preferred-fix): `dogfood.json` records `receipt`, the digest of the install receipt's bytes; any change fails `concorde_untouched`. New scenario `scenario.dogfood-scenarios.receipt-changed`. Old scenario directories without `receipt` are not supported (rapid-iteration rule).
- I-92bf28ed (preferred-fix): the owned phase's judged time starts at the arrival time of the launching turn's `result` event, read from the live session's recorded events (owners.py `turn_end`); live.py (Headless sessions) unchanged.
- I-55ecf918 (preferred-fix): `RunTests` stubs Headless sessions' start for every ending and for `wait_exceeded`; new scenarios `session-ends` and `sessions-kept`.
- I-4693f236 (suggestion): applied: new implementation document `specs/concorde/e2e/dogfood/contracts.md` with contracts `contract.dogfood-scenarios.scenario`, `.record` and `.evaluation`; the entry keeps summaries and links.
- I-21e6969b (suggestion): applied as far as the Protocol allows. CHK.scenario.steps refuses nested lists inside a scenario, so vertical sub-lists are impossible there; joint outcomes became separate THEN/AND/BUT steps and the alternatives of `receipt-unreadable` and `invalid-scenario` moved to explanatory prose after the steps.
- I-185c9998 (obvious-fix): runtime-failures split into `command-not-started`, `task-unreadable`, `configuration-unreadable`, `unexpected-failure` (plus `malformed-prompt` for I-a660f737); outside-root acceptance is its own `scenario.e2e.outside-root`. New `scenario.e2e.invalid-name` and `scenario.e2e.owners-competing-run`.
- I-2deab87f, I-f2771506, I-6ed0546d (suggestions): applied as suggested.
- Owners case: the unowned launch that cannot be started is `command_failed` (I-115a3b97), listed among the case's errors.

## Report 2 to the main agent (Review流程), 2026-10-08T06:38:56Z

fix-dogfood-e2e delivered: delivery commit c113713d (on 1bcce36d). task-validation ready; full suite 1333 passed, 5 skipped; spec-validation success, build --check clean.

Resolves all 24 Issues in the task record (escalations 1-6 carried out as answered, option A each). Choices I made (details in the decision log):
- I-561da75c (critical): session directories created exclusively by common.fresh_directory, named after the time to the microsecond with -2, -3… on collision; used by dogfood run and by session start.
- I-08d24b88: the owners case judges only the run whose runner (host_pid of the run progress file) descends from its launcher process, read from Linux /proc. Rejected Execution's private CONCORDE_RUN_ID. Stated limit: a launcher in another PID namespace (sandbox) is never found → live_timeout. An owner that ends before its run appears now stops with session_failed.
- I-e75b39f1: new code invalid_name for a --name that is empty, ., .. or holds /, checked first by prepare and dogfood prepare; symbolic links count as existing.
- I-fb3d5ed5: Dogfood scenarios includes document.e2e.module.
- I-db9e53ec: dogfood.json records the install receipt's digest; any change fails concorde_untouched (older scenario directories lack it: not supported, rapid-iteration rule).
- I-273e63e9: refusals keep their whole stdout and stderr in evaluation.json.
- I-92bf28ed: the judged time starts at the arrival of the launching turn's result event.
- I-4693f236: new implementation document specs/concorde/e2e/dogfood/contracts.md (contracts scenario, record, evaluation).
- I-21e6969b (suggestion): only partly applicable. CHK.scenario.steps forbids nested lists inside a scenario, so joint outcomes became separate steps and the alternatives moved to prose after the steps. You may close it as fixed or keep it open.
- New error codes: invalid_name (E2E), invalid_scenario (now specified).

Nothing open on my side; no change outside the two Modules besides the registry mirror.

## Closed: merged, 2026-10-08T06:39:08Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit c113713de454455054bbd5a5c9f90c781dfa9b4b into main and closed it as merged. Nobody answers a report after that.
