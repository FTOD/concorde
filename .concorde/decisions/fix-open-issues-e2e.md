# Decision log: fix-open-issues-e2e

Goal: Fix the open Issues of the issues part and End-to-end testing

## Brief (main agent, 2026-10-04)

### Context

The developer asked (2026-10-04) to try to resolve the project's open Issues, after the parts
refactor merged into `main` (decision logs of parts-*, fix-* and parts-review* in
`.concorde/decisions/`). Every open Issue was reviewed and classified then; none is high or
critical. Nine tasks run in parallel, one per part or group of parts: fix-open-spec,
fix-open-method, fix-open-execution, fix-open-coordination, fix-open-worker-harness,
fix-open-kernel, fix-open-workflows, fix-open-root-distribution, fix-open-issues-e2e.

### How to work

- Your Issues are listed below with severity and tier; read each with `concorde issues show`
  (the latest report is the verified one). Work on them most severe first.
- **obvious-fix and preferred-fix**: fix them (preferred-fix: record which fix you chose and why).
  **decision-needed**: the main agent's decisions are below; carry them out. **suggestion**: fix it
  when it is cheap and clearly improves the Spec or code; otherwise leave it open.
- After fixing an Issue, add it to this task with `concorde task resolve <task> <issue>`: the
  merge closes exactly the Issues the task resolves, so add none you did not fix. Close an Issue
  that does not hold yourself (`not-actionable`, with the reason) or as `duplicate`. If a fix needs
  a decision with major impact, or another group's files beyond a small edit, escalate it with any
  others together rather than deciding it.
- Work directly in the Specs, code and tests; no Operation or review is needed. Keep edits of files
  other groups may touch small (glossary, registry mirror, shared tests, guidance composition); on a
  merge conflict the main agent asks you to merge `main` in.
- Introduce no regression: every part still works installed with only its dependencies
  (`tests/concorde/acceptance/test_parts.py`), the part-dependency check passes, guidance reads
  correctly whichever parts are installed (`tests/concorde/distribution/test_guidance_parts.py`).
  Rapid-iteration rule: no shims or compatibility paths.
- Verify with `build --check`, `spec-validation` and the full suite, then `task-validation` and
  `delivery`, and report: resolved, closed as not holding, left open (and why).

### Decisions of the main agent for your decision-needed Issues

- I-566e82f1 (owners busy-workspace test flake): make the test deterministic under load (its fake refusal must land on the phase it asserts), without weakening what it checks.

### Your 20 Issues

- I-e189786a4a7c5a65b653ac42a2c802de (medium, preferred-fix, module.issues): Recovery leaves a staged interrupted reopening half restored
- I-994b99ee7cac577489d4584171e7e6ed (medium, preferred-fix, module.e2e): Driver step execution breaks on project paths containing spaces
- I-e430ad4fd4c451489d67eb107183b555 (medium, obvious-fix, module.e2e): Relative end-to-end roots break preparation after cloning
- I-566e82f14dd05300856042bc9472f58b (low, decision-needed, module.e2e): Owners busy-workspace test fails intermittently under full-suite load
- I-a039136654af50e1b683350c63ebf7c6 (low, preferred-fix, module.issues): report reads the revision after the commit and the lock release
- I-6c420b1a49275628be2868e5f7aaea15 (low, preferred-fix, module.e2e): Expected runtime failures escape as tracebacks
- I-25bbb3f57ad556e99d429b0452a689ee (low, preferred-fix, module.e2e): Owners case judges the owned phase although its owner session exited
- I-16245513c17853d6bc8f72be1a970665 (low, preferred-fix, module.dogfood-scenarios): Dogfood evaluation failures bypass the promised JSON error
- I-afa778bbb64e59469f494a73154a05e9 (low, obvious-fix, module.issues): Archive removes source records without checking their revision
- I-02eafc9e1dc359a6ab265a48e469b13e (low, obvious-fix, module.issues): Store writes accept a subdirectory of the primary worktree as root
- I-20dc64aa4c245976acf5085e7b8109c6 (low, obvious-fix, module.issues): Registered receipt schema admits any path
- I-17d06207bc38579d8d07ed93cd47df29 (low, obvious-fix, module.e2e): Malformed restart options bypass the usage-error contract
- I-ad4ee36f790459adbc11a84ebc01a7a7 (low, obvious-fix, module.e2e): Owners preflight does not reject a missing task worktree
- I-2905613306575856acba792c17f2659f (low, obvious-fix, module.issues): Visibility is stated as acknowledgment, and 'no receipt recorded nothing' ignores a reply lost after the commit
- I-a7e1faf1ad8b5779bb19d89c91cb8489 (low, obvious-fix, module.issues): 'A refusal writes nothing' ignores the recovery a write runs before a later refusal
- I-cabec45442545828b8c763bab7e214c1 (low, obvious-fix, module.issues): req.issues.commit-alone says every write commits one record, though archive commits several
- I-a314ad1d492f5c1493308895097d60c3 (low, obvious-fix, module.issues): scenario.issues.store-corrupted-record does not say the corrupted record is committed
- I-0a52f8cd45dc5703a7e4d9a2256653cd (low, suggestion, module.dogfood-scenarios): Report checks and the complete evaluation have no scenario or test
- I-d7054aedbcb252a0b47fdc79140d7469 (low, suggestion, module.issues): The entry's placement wording can suggest that misplaced records stay put
- I-93d7298282365b89a6f3744dfc836f87 (low, suggestion, module.issues): The entry repeats implementation-level persistence details

## Task session (2026-10-04)

### Decisions taken without the developer

- I-e189786a (preferred-fix): recovery now judges every changed record before it puts any back
  (`_recover` split into a judging pass and a restoring pass, `_judged` per record), rather than
  ordering the entries specially; a staged reopening is then put back whole whatever the order of
  `git status`. Chosen because it removes the order dependence for every move, not only reopen.
  The interrupted-move test now covers close and reopen, staged and unstaged.
- I-a0391366 (preferred-fix): the store returns the revision it computed under the merge lock, as
  the Issue suggests. New store operation `record_report(root, report, source, wait) ->
  {receipt, revision}`; `report_issue` stays and returns its receipt, so its callers and the
  receipt contract are unchanged. The report command prints `record_report`'s answer and no longer
  reads the record after the lock is released.
- I-afa778bb: `_settle` now takes each removed record with the revision it must still have; an
  archive passes the digest of the bytes it read, so a record changed meanwhile is refused with
  `stale_issue` and nothing moves.
- I-02eafc9e: `_require_primary` also refuses a root that is a directory inside the primary
  worktree (`not_primary`, its detail says so).
- I-20dc64aa: the registered `concorde-issue-receipt` version 2 now carries the contract's record
  path pattern; version kept at 2 since the contract already states that pattern.
- Spec wording Issues I-29056133, I-a7e1faf1, I-cabec454, I-a314ad1d fixed as their reports say;
  suggestions I-d7054aed (misplaced records are moved by a write) and I-93d72982 (the store's
  realization paragraph now explains and links the interface for layout, order and Git commands,
  dropping the type identifiers) fixed since both were cheap.
- I-566e82f1 (main agent's decision: make the test deterministic): the flake was a real ordering
  bug of the owners case, not only of its test. After it saw the run's result, `phase()` read it a
  second time; `run_folder` finds the run's folder through its `status.json`, which the run
  rewrites right after its result, so under load the second read found no folder and the refusal
  was missed, the case judged the unowned phase and was refused in the next one. The case now
  judges the result it read once. The test injects that lost re-read (every read after the first
  that found the result finds none), so it is deterministic and fails on the old code; what it
  checks is unchanged.
- I-25bbb3f5 (preferred-fix): `LiveSession.require_running` raises `session_failed`; the owners
  case checks the owner while it waits for its wake and every session before judging a phase, so
  a session that ended is reported as `session_failed`, never as an owner not woken. New
  scenario.e2e.owners-session-ended.
- I-ad4ee36f: the owners case refuses a task record whose worktree does not exist with `no_task`
  before any session starts.
- I-994b99ee (preferred-fix): the driver's step agents run the worktree's command through
  `spawnSync` with an argument array (small edit of `tests/concorde/workflows/run_script.mjs`,
  which End-to-end testing lists as shared with Workflows), and `driver_input` no longer passes
  `args.concorde`: the rendered script's own report command line then names
  `.concorde/bin/concorde` relative to the worktree, its working directory, so neither command
  splits a path with spaces. Tested with a project path holding spaces and a quote.
- I-e430ad4f: `e2e_root()` returns the resolved absolute root.
- I-17d06207: `--restart` is parsed by an argparse type, so a value without `=` is a usage error
  (exit 2).
- I-6c420b1a (preferred-fix): both fixes the report names: the named boundaries translate their
  failures (`run` → `command_failed` when a command cannot start, `task_worktree` → `no_task`,
  a non-object worker configuration → `worker_configuration_unreadable`), and `main()` prints any
  other exception as `unexpected_error` with its traceback as evidence, so the one-JSON-object
  contract holds for every command without hiding the traceback.
- I-16245513 (preferred-fix): the fix the report calls better: an unreadable install receipt is a
  failed `concorde_untouched` check (installed_digests raises `receipt_unreadable`, which
  `_untouched` records as a problem), and an installed command that cannot start is
  `command_failed`.
- I-0a52f8cd (suggestion): fixed since cheap: scenarios and local tests for reports_checked,
  reports_accepted, the unreadable receipt and the whole evaluation's verdict and evaluation.json.
- Found and fixed while testing (no Issue recorded, fixed in this task): `e2e.py prepare` without
  `--worker-model` failed at head with `config_invalid: unknown Operation 'spec_panel'`, because
  the tool never loaded the Operations the parts register, so Workers' check saw an empty catalog
  (two e2e tests passed only when another test module had loaded the parts first). `require_mapped`
  now loads the installed parts' registrations as the `concorde` command does.

## Report 1 to the main agent (项目架构分离建议), 2026-10-04T02:34:36Z

fix-open-issues-e2e delivered: delivery commit 93378955 on concorde/fix-open-issues-e2e (fix commits a0e0ec3b Issues, 2bed36dc End-to-end testing). task-validation ready; build --check, spec-validation (0 errors, 0 warnings) and the full suite (1093 passed, 5 skipped) pass.

Resolved, all 20 added with task resolve: I-e189786a, I-994b99ee, I-e430ad4f, I-566e82f1, I-a0391366, I-6c420b1a, I-25bbb3f5, I-16245513, I-afa778bb, I-02eafc9e, I-20dc64aa, I-17d06207, I-ad4ee36f, I-29056133, I-a7e1faf1, I-cabec454, I-a314ad1d, I-0a52f8cd, I-d7054aed, I-93d72982. None closed as not holding; none left open.

Preferred-fix choices:
- I-e189786a: recovery judges every changed record before putting any back, so a move is put back whole whatever the git status order (test covers close and reopen, staged and unstaged).
- I-a0391366: new store operation record_report -> {receipt, revision}, revision taken under the merge lock; report_issue still returns the receipt alone; the report command prints record_report's answer.
- I-994b99ee: the driver's step agents run the worktree's command via spawnSync with an argument array (a small edit of tests/concorde/workflows/run_script.mjs, Workflows' file that E2E also lists), and driver_input no longer passes args.concorde, so the script's report command names .concorde/bin/concorde relative to the worktree. Tested with a path holding spaces and a quote.
- I-6c420b1a: both fixes: the named boundaries raise E2EError (command_failed, no_task, worker_configuration_unreadable), and main() prints any other exception as unexpected_error with its traceback.
- I-25bbb3f5: the owners case checks session liveness while waiting for the owner's wake and before judging -> session_failed (new scenario.e2e.owners-session-ended).
- I-16245513: an unreadable install receipt is a failed concorde_untouched check; an installed command that cannot start is command_failed.
Decision-needed I-566e82f1, as decided: the flake was a real bug in the owners case. It read the run result a second time, the read missed the run's folder while its status.json was being rewritten, and the case went on into the next phase. The case now judges the result it read once; the test injects that missed second read, so it is deterministic and fails on the old code.
Suggestions fixed since cheap: I-0a52f8cd (scenarios and tests for reports_checked, reports_accepted, the evaluation verdict), I-d7054aed and I-93d72982 (issues entry wording).

Also found and fixed in module.e2e: `e2e.py prepare` without --worker-model failed at head with config_invalid "unknown Operation 'spec_panel'", because the tool never loaded the parts' Operation registrations (two e2e tests passed only when other test modules had loaded them). require_mapped now loads the installed parts first.

Nothing open. Details in the decision log.

## Closed: merged, 2026-10-04T02:35:20Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 933789555b663932011aa382b4eb70f5874a9270 into main and closed it as merged. Nobody answers a report after that.
