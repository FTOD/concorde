# Decision log: r2-execution

Goal: Fix the critical, high and obvious-fix open Issues of Execution, Checks, Operations and Execution commands found by the complete project_review

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

## Escalated to the main agent, 2026-10-08T13:39:11Z

- **task-session** task session (task r2-execution): `measurement_contract_undefined`
  Issue I-7c75c05ef1755cacb29322186b297953 (decision-needed, high, module.checks): service.md gives run_checks(worktree, *, modules, trace_directory, measured=None, tests=None, ...) and names measured_digest as the revalidation entry point, but defines neither the structures nor the omitted/empty/invalid semantics of measured and tests, nor measured_digest's arguments. What the code does today (src/concorde/execution/checks/checks.py:366-455, 556-640): measured is a mapping from a selected Module label to an iterable of worktree-relative paths, each hashed with read_bytes; None, {} or a Module missing from it measures no implementation file for that Module (its digest still covers its checks' definitions, inputs and CHECK_POLICY); duplicates are measured once; a named file that is missing or a directory raises a raw OSError (not a CheckError, so it escapes service_error), and a symlink is hashed through (also Issue I-479e61fb, which I am fixing to refuse links). tests is an iterable of test identities '<worktree-relative file>[::<name>]'; None or empty keeps no selective check; each distinct file part is hashed. measured_digest(worktree, check, modules, *, checks=None, measured=None, tests=()) recomputes the digest given the same check, the same selected Modules, measured and tests; checks=None reads the checks files again. Nothing in the project calls measured_digest outside checks.py today: Validation compares source_digest values between its own runs, and Method passes measured=measured_files(repository, selected) (the Modules' implementation files from the Specs) and tests=verified_tests(...).
  Not handled here (decision): Choosing the omission semantics, the invalid-argument outcomes and how a consumer reproduces a stored digest establishes new interface promises of Check execution to its callers; the task brief reserves decision-needed Issues for the main agent or developer.
  Options: A: specify today's behaviour as the callable contract in service.md: measured maps a Module label to worktree-relative POSIX paths of regular files, omitted/empty/missing Module measures no implementation file of that Module; tests are '<file>[::<name>]' identities, omitted or empty keeps no selective check; measured_digest's signature and that a consumer passes the same check, selected Modules, measured and tests; a measured or test file that is missing, not a regular file or a symbolic link is refused before any command with check_input_missing (after the run: stale_evidence); a malformed argument (not a mapping, a non-string, absolute or '..' path) is refused with invalid_check, before any command; plus an example of a run followed by revalidation; B: as A, but make a stored result self-describing: the check trace (contract.checks.check-trace, version 3) also records the measured files, so a consumer revalidates from the stored node alone with a new measured_digest_of(node) instead of re-supplying measured and tests; C: as A, but malformed arguments get a new error code invalid_argument (reason input) instead of reusing invalid_check
  Recommendation: A: it promises what the code and Method already do, needs no contract version change, and reuses the existing codes; the only behaviour changes are refusing a missing/non-regular/linked measured file with check_input_missing instead of a raw OSError, and validating the argument shapes

```json
{
  "level": "task-session",
  "actor": "task session (task r2-execution)",
  "code": "measurement_contract_undefined",
  "detail": "Issue I-7c75c05ef1755cacb29322186b297953 (decision-needed, high, module.checks): service.md gives run_checks(worktree, *, modules, trace_directory, measured=None, tests=None, ...) and names measured_digest as the revalidation entry point, but defines neither the structures nor the omitted/empty/invalid semantics of measured and tests, nor measured_digest's arguments. What the code does today (src/concorde/execution/checks/checks.py:366-455, 556-640): measured is a mapping from a selected Module label to an iterable of worktree-relative paths, each hashed with read_bytes; None, {} or a Module missing from it measures no implementation file for that Module (its digest still covers its checks' definitions, inputs and CHECK_POLICY); duplicates are measured once; a named file that is missing or a directory raises a raw OSError (not a CheckError, so it escapes service_error), and a symlink is hashed through (also Issue I-479e61fb, which I am fixing to refuse links). tests is an iterable of test identities '<worktree-relative file>[::<name>]'; None or empty keeps no selective check; each distinct file part is hashed. measured_digest(worktree, check, modules, *, checks=None, measured=None, tests=()) recomputes the digest given the same check, the same selected Modules, measured and tests; checks=None reads the checks files again. Nothing in the project calls measured_digest outside checks.py today: Validation compares source_digest values between its own runs, and Method passes measured=measured_files(repository, selected) (the Modules' implementation files from the Specs) and tests=verified_tests(...).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Choosing the omission semantics, the invalid-argument outcomes and how a consumer reproduces a stored digest establishes new interface promises of Check execution to its callers; the task brief reserves decision-needed Issues for the main agent or developer."
  },
  "options": [
    "A: specify today's behaviour as the callable contract in service.md: measured maps a Module label to worktree-relative POSIX paths of regular files, omitted/empty/missing Module measures no implementation file of that Module; tests are '<file>[::<name>]' identities, omitted or empty keeps no selective check; measured_digest's signature and that a consumer passes the same check, selected Modules, measured and tests; a measured or test file that is missing, not a regular file or a symbolic link is refused before any command with check_input_missing (after the run: stale_evidence); a malformed argument (not a mapping, a non-string, absolute or '..' path) is refused with invalid_check, before any command; plus an example of a run followed by revalidation",
    "B: as A, but make a stored result self-describing: the check trace (contract.checks.check-trace, version 3) also records the measured files, so a consumer revalidates from the stored node alone with a new measured_digest_of(node) instead of re-supplying measured and tests",
    "C: as A, but malformed arguments get a new error code invalid_argument (reason input) instead of reusing invalid_check"
  ],
  "recommendation": "A: it promises what the code and Method already do, needs no contract version change, and reuses the existing codes; the only behaviour changes are refusing a missing/non-regular/linked measured file with check_input_missing instead of a raw OSError, and validating the argument shapes",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-08T13:39:28Z

Early escalation of r2-execution's decision-needed Issues, as the task brief asks. I continue with the other Issues meanwhile.

Of the three decision-needed Issues, only one is still open on the current head:

Escalation 1:
- **task-session** task session (task r2-execution): `measurement_contract_undefined`
  Issue I-7c75c05ef1755cacb29322186b297953 (decision-needed, high, module.checks): run_checks' `measured` and `tests` arguments and measured_digest's revalidation arguments have no defined structure, omission or invalid-input semantics. Today: measured maps a Module label to worktree-relative paths (omitted/empty/missing Module = no implementation file measured for it); tests are '<file>[::<name>]' identities (omitted/empty = no selective check); a missing or directory measured file raises a raw OSError; nothing outside checks.py calls measured_digest.
  Options: A: specify today's behaviour as the callable contract in service.md, refusing missing/non-regular/linked measured or test files with check_input_missing and malformed arguments with invalid_check, before any command, plus a run-then-revalidate example; B: as A, plus the check trace (contract.checks.check-trace v3) records the measured files so revalidation needs only the stored node; C: as A, but a new code invalid_argument for malformed arguments
  Recommendation: A (promises what the code and Method already do; no contract version change; reuses existing codes)

Already fixed before this round (the project_review ran on ce20cc748, which does not contain 6c38b2d77 of fix-operations-commands, merged at faff373fc): the two other decision-needed Issues, I-c75b6c1cb45c5f5fae9a449a09565813 (Operation registration contract and repeat identity) and I-94299e2ac1ce59f88546c2ae7e6cf7bb (command registration contract), are settled by specs/concorde/execution/operations/registration.md (the main agent's answer to fix-operations-commands' escalations 1-3, option A), which both Modules include. The same commit already fixed I-1ffed70fd3fd5206a7c4e343dc95c000, I-f16f4f7bd07959798182a17e42cd98b3, I-63254abb3f0654ef86cf6f271373ce8b, I-0d26d5e1a3b357a59cda3048065e57ca and I-49f9fc1943985f14af82c848f2771936. I will give the evidence for each in the decision log and my final report; you may close them as resolved now or wait for that.

Question: for escalation 1, A, B or C? My recommendation is A.

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-10-08T13:39:52Z

Escalation 1 measurement_contract_undefined (main agent): A — specify today's behaviour as the callable contract in service.md, refusing missing, non-regular or linked measured or test files with check_input_missing and malformed arguments with invalid_check before any command, with a run-then-revalidate example; no contract version change. The seven Issues fix-operations-commands already fixed stay in this task's resolves: put the evidence for each in the decision log and your report; the merge closes them as resolved.

## Task session decisions and findings, 2026-10-08

### Already fixed before this round (evidence)

The project_review r-20261008T063808-project_review-9851e69f examined ce20cc748, which does not
contain 6c38b2d77 (fix-operations-commands, merged at faff373fc). On the current head:

- I-c75b6c1cb45c5f5fae9a449a09565813 (decision-needed): specs/concorde/execution/operations/registration.md
  states the entry point (`register(part, definition)`), the definition fields, the refusals
  (`invalid_definition`, `duplicate_definition`), "A repeated registration" (same part, equal in
  every field, functions by identity) and lookup; req.operations.unique-names carries the repeat
  rule; Operations' module.md.json includes document.execution.runner. Settled by the main
  agent's answer to fix-operations-commands' escalations 1-3 (option A).
- I-94299e2ac1ce59f88546c2ae7e6cf7bb (decision-needed): commands/module.md.json includes
  document.operations.registration and document.execution.runner; "What a provider declares"
  links registration.md#the-definition; `writes` is defined there as what the catalog reports.
- I-1ffed70fd3fd5206a7c4e343dc95c000: Commands relies_on contract.execution.run-result and the
  Execution requirements and includes runner.md; the "same shape" claim is gone (module.md:187
  now says the command catalog is an instance of the same `Catalog`, specified by the included
  registration.md).
- I-f16f4f7bd07959798182a17e42cd98b3: Operations relies_on req.execution.claims-apart,
  error-when-not-ok, reasons, error-detail and contract.execution.run-result and includes
  runner.md. Its worker obligations (workers-through-workers, grant-frozen) are stated as
  Operations' own; method/workers.md is linked only as how Method's Operations do it, the
  illustration the Issue allows.
- I-63254abb3f0654ef86cf6f271373ce8b: catalog.py:66 refuses a command definition whose binding
  is not `required` with invalid_definition (registration.md "Registering"); since no such
  definition can be registered, the runner never sees one; tests/concorde/commands/test_catalog.py.
- I-0d26d5e1a3b357a59cda3048065e57ca: req.operations.worker-ids-declared and
  req.operations.model-work-only are separate requirements.
- I-49f9fc1943985f14af82c848f2771936: operations/scenarios.md has separate registered,
  repeated, unknown, unique-names, definition-complete and listed scenarios; Commands has its
  own scenarios.md.

### Decisions taken without the developer

- I-1a7bcd0d and I-2b9e5f6b (same defect): Execution's entry now says the definition decides
  unbound admission by its binding, names Method's reading Operations as examples (adding
  project_review, and general for work that writes nothing) and refuses only a definition that
  requires a binding. No link to Method's catalog: Execution depends on no Method part.
- I-bc76979d: split into req.execution.checkout-removed (attempt removal before the result) and a
  new req.execution.checkout-leftovers-named (checkout-not-removed evidence; status unchanged).
- I-2baffd16 (preferred-fix): aligned Check execution's overview and diagram with service.md's
  per-check measure/run/measure; added scenario.checks.service-between-checks and its test.
- I-7c75c05e (option A, main agent): service.md now states the `measured`/`tests` contract, its
  omitted/empty semantics, the refusals before any command (invalid_check for shapes,
  check_input_missing for missing/non-regular/linked measured or test files), measured_digest's
  arguments and a run-then-revalidate example; code: `measurement()` and `_measured_file()`.
- I-479e61fb (preferred-fix): measured implementation and selected test files are read only as
  regular files reached through no symbolic link (kernel checked_path); before the run that is
  check_input_missing, after it stale_evidence. Method's bound_files already leaves links out,
  so the before-run refusal is reached only by direct callers.
- I-c621d7cc (preferred-fix): validate_checks now validates argv, env, when and timeout_seconds
  of every check (shared `_command_fields`), without replacing {python} or running anything.
  run_checks keeps its order (when, then argv for every non-readiness-skipped check, timeout and
  env of kept checks), so it still validates only what service.md step 4 says.
- I-13d5e626: Check execution now uses module.kernel (relies_on concept.typed-value) with an
  explained #uses-kernel and includes document.kernel.contracts; the input path rule links it.
- I-c138dca9: req.checks.project-read-only is limited to runs without writable_project.
- I-378d6d45: both standalone timing scenarios trigger on a `timed` function; the entry says a
  direct Span opens no trace even with the variable set; tested.
- I-3058a269, I-918f75fb, I-08ee5bb8: code fixes with regression tests (lifecycle only directly
  below .concorde; summed_span_seconds null when no span has a duration; selective header in the
  refused and interrupted logs).
- I-0be90a1f: _check_own_link also requires the actor to be context.actor.
- I-75b27875 (preferred-fix): summary uses only Module names; _replaced narrows context.modules
  to names before making its link, so the result is replaced and saved.
- I-cb8f573a: Cancelled passes through admission and runtime-path resolver wrappers.
- I-53719d29 (preferred-fix): the detaching parent hands its binding reading to the runner
  (CONCORDE_RUN_BINDING); the runner records where the parent looks; a bound reading is
  revalidated under the workspace lock (workspace_retired in the lobby). runner.md step 5 says so.
- Pre-existing `ruff check` warnings in checks.py (import order, RUF012, ISC004) are not this
  task's; only `ruff format` is applied.

## Report 2 to the main agent (Review流程), 2026-10-08T14:14:37Z

r2-execution delivered: delivery commit 24ffbb820 on concorde/r2-execution (delivery run r-20261008T140331-delivery-63851e09; task-validation ready; full suite 1383 passed, 5 skipped; build --check and spec-validation clean).

All 24 Issues in resolves are handled:
- Fixed in this task (17): Check execution I-7c75c05e (option A as you answered: measured/tests contract, refusals before any command, measured_digest arguments and a revalidation example), I-479e61fb (measured and test files must be regular files reached through no symbolic link: check_input_missing before the run, stale_evidence after), I-c621d7cc (validate_checks validates argv/env/when/timeout_seconds through the same helper, running nothing), I-2baffd16 (overview and diagram now per-check, new scenario.checks.service-between-checks), I-08ee5bb8 (selective header in refused and interrupted logs), I-13d5e626 (Check execution uses module.kernel, concept.typed-value, includes document.kernel.contracts; registry refreshed), I-3058a269, I-918f75fb, I-378d6d45, I-c138dca9; Execution I-1a7bcd0d + I-2b9e5f6b (unbound admission is the definition's binding; names are examples incl. project_review and read-only general), I-bc76979d (split into req.execution.checkout-removed and new req.execution.checkout-leftovers-named), I-0be90a1f (own link must also name this run as actor), I-75b27875, I-cb8f573a, I-53719d29.
- Already fixed by fix-operations-commands (6c38b2d77, after the review's head ce20cc748), evidence per Issue in the decision log: I-c75b6c1c, I-94299e2a, I-1ffed70f, I-f16f4f7b, I-63254abb, I-0d26d5e1, I-49f9fc19.

Preferred-fix choices: I-53719d29 — the detaching parent hands the runner its binding reading (CONCORDE_RUN_BINDING); a bound reading is checked again under the workspace lock, so a binding changed or gone is refused with workspace_retired in the lobby the parent watches, and a parent that read no binding gets the unbound run it announced (runner.md "Detached runs" step 5). I-75b27875 — the summary uses only Module names and the replacement narrows the Modules before its link, so a malformed entry yields a saved invalid_result. I-479e61fb, I-c621d7cc, I-2baffd16 as described above. Every new test fails on the old code.

Nothing is open and nothing needs the developer. Observations, not escalations: pre-existing `ruff check` warnings in checks.py are untouched (only ruff format applied); the branch is not pushed, since the merge is local.

## Closed: merged, 2026-10-12T14:26:49Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 24ffbb820d6b7246a6c7977298c611d4f58af8b7 into main and closed it as merged. Nobody answers a report after that.
