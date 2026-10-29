# Decision log: swe-cases-critical

Goal: Fix module.swe-bench-cases' two critical Issues (truncated PASS_TO_PASS identities use the wrong passing rules; duplicate listed tests produce wrong counts and verdicts) and its other obvious-fix Issues

## Task brief (main agent, 2026-10-29)

**Origin.** Project review r-20261029T060905-project_review-fa4731e2 (unbound, commit 8a5ed4245, verdict changes_required) left 2 critical and 10 high Issues open. The developer chose to fix every critical and high Issue first, in five parallel tasks split by Module, each also fixing the obvious-fix Issues of its own Modules. Read the review's findings for your Modules in `.concorde/unbound/r-20261029T060905-project_review-fa4731e2/result.json` (`output.modules[]`, the panel and code_review reviews) when an Issue's text is not enough.

**Issues this task resolves (5, all in the task's resolves):**

- I-773612e15e185a62b776e466f480d41a (module.swe-bench-cases, critical, obvious-fix): Duplicate listed tests produce incorrect counts and verdicts
- I-d4056271cc365b70adf049ad038a7a44 (module.swe-bench-cases, critical, obvious-fix): Truncated PASS_TO_PASS identities use the wrong passing rules
- I-22041e6373025947b7f6ba4253901513 (module.swe-bench-cases, medium, obvious-fix): The status scenario combines incompatible grading situations
- I-b2711abcb7535212ba3866db91de0050 (module.swe-bench-cases, medium, obvious-fix): Cleanup failure prevents saving completed pytest output
- I-b69fdf23b84253a5be8db3705fc37074 (module.swe-bench-cases, medium, obvious-fix): The bounded-round requirement omits failed-step exits

**How to handle them (the main agent's decisions).**
- Critical and high first. Show each with a test that fails on the old code.
- Fix obvious-fix Issues directly. For a preferred-fix Issue, take the clearly better fix and report it. None of these Issues is decision-needed. If one turns out to need a decision beyond your Modules or beyond the Issue's evident intent, escalate it rather than guess.
- An Issue that turns out to be already fixed, not a real problem, or a duplicate of another open Issue: say so with your evidence in your report. Do not close it yourself. The main agent closes it, or the merge closes it as resolved.
- Leave the other open Issues of your Modules (preferred-fix and decision-needed medium or low) alone, unless a fix here resolves one as a side effect: then name it in your report.
- Add or change Specs first where a fix changes a promise. Keep within your Modules. Escalate a change any other Module would have to make.

**Parallel tasks.** Four other tasks run at the same time. Do not touch their Modules:
- coordination-high: module.tasks, module.task-session
- worker-harness-high: module.harness, module.workers
- checks-execution-high: module.checks, module.execution
- specmcp-workflows-high: module.spec-mcp, module.workflows

**Specific to this task.** Both critical Issues produce wrong SWE-bench verdicts, so the case results Concorde reports today cannot be trusted. Show each with a test that fails on the old code.

**Verification.** Run Concorde's full suite, `build --check` and `spec-validation`. Then run `task-validation` and `delivery` from the task worktree, and report.

**Environment notes.**
- uv, node/npm (Node 24, npm 11), pi, rg, fd and d2 are under `/home/scratch.zbai_gpu/opt`.
- The system bubblewrap is 0.4.0 and works.
- Every worker runs on pi: claude-opus-5-5 and gpt-6.1-sol.
- Keep large files off `$HOME` (5 GB quota).

**Left to the session.** The mechanisms, internal structure, test design and Spec wording.

## Task session decisions (2026-10-29)

Worked directly, without Operations: every fix is small, local to `scripts/e2e/cases.py` and the
Module's four Spec documents, and decidable from the Issues and SWE-bench's pinned harness.

- **I-d4056271 (critical), cut PASS_TO_PASS identities.** `status_of` now takes the list's counted
  statuses and judges whether the identities a cut identity begins agree on passing by that rule.
  Decision: this departs on purpose from SWE-bench's own `_resolve_case`
  (`references/swe-bench/swebench/harness/grading.py:60-82`), which compares by PASSED/XFAIL for
  both lists. With that rule, a PASS_TO_PASS cut identity whose matches are PASSED and SKIPPED fails,
  and one whose matches are SKIPPED and FAILED passes or fails depending on pytest's report order.
  Reason: the Issue (obvious-fix) and our Spec ("agree on passing or not", "a PASS_TO_PASS test
  passed when its status is PASSED, XFAIL or SKIPPED") ask for the list's own rule, and a verdict
  that depends on report order cannot be what SWE-bench intends. module.md now names the
  difference. FAIL_TO_PASS keeps the same behaviour as before and as SWE-bench.
- **I-773612e1 (critical), repeated listings.** `passed` now counts every listing, like `total`
  and like SWE-bench's `get_eval_tests_report`, which appends one success per listing.
  `not_passed` still names a test once. Contract `contract.swe-bench-cases.verdict` keeps version 1:
  its semantics only gain "each listing of a test counting once", which is what "total the number
  listed" already meant.
- **I-b2711abc, log before cleanup.** The finished test run's output is written inside the
  cleanup's `try`, before the worktree removal. A failure to write the log is then a grading
  failure that `cleanup_failed` names as its earlier error, like any other.
- **I-22041e63, scenario split.** `scenario.swe-bench-cases.grade-statuses` keeps its identity for
  the resolved situation, with one input per GIVEN/AND step. New
  `scenario.swe-bench-cases.grade-unresolved-statuses` holds the skipped and never-reported
  FAIL_TO_PASS tests. A failing test was dropped from that test, since `grade` already shows one.
- **I-b69fdf23, bounded round.** The SHALL of `req.swe-bench-cases.repair-specs-only` now says
  `specify` follows only a review that ended `ok` without accepting, and the second review only a
  `specify` that ended `ok`. The code already stopped there (`repair_specs`), so no code change.
- **New scenarios.** `grade-cut-pass-to-pass` (both report orders) and `grade-listed-twice`.
  Test names: `test_a_cut_pass_to_pass_identity_agrees_by_its_lists_rule`,
  `test_a_test_listed_twice_counts_twice`; `test_a_grading_worktree_that_cannot_be_removed_fails_grading`
  now asks for a log.
- **Shown failing on the old code** (old `cases.py` swapped in, new tests): 3 failed, 10 passed.
  Listed twice: `fail_to_pass {'passed': 1, 'total': 2, 'not_passed': {}}`, resolved false. Cut
  PASS_TO_PASS: old code counted `test_skipped_first[x` (a failing match) as maintained and
  `test_kept[x` (all maintained) as `not run`. Cleanup failure: the log still held the earlier
  run's output.
- Commit 5e847dac4 on the task branch.
- **Second step, commit 97963f22a.** The entry now says which status a cut identity takes when the
  identities it begins agree: the first one pytest reported (what the code and SWE-bench's
  `_resolve_case` already do). The log promise moved out of `grade-cleanup-failed` into its own
  scenario, `scenario.swe-bench-cases.grade-log-kept`. Reason: open preferred-fix I-d63aee32
  already faults that scenario for a conditional outcome its GIVEN does not set up, and a second
  conditional step would make that worse.
- **I-761b648b (preferred-fix, not in the brief).** Both of its gaps are now defined in the entry:
  which rule the matches agree by (the list's own rule) and which status is taken (the first
  reported). Its suggested repair asked for PASSED/XFAIL for both lists, which the critical
  I-d4056271 overrules. Left for the main agent to add to the task or close.
- **Not `ok` (full suite, first run on 5e847dac4).** 1 failed, 1662 passed:
  `tests/concorde/tracing/test_locks.py::LockLineTests::test_a_held_lock_is_named_once_while_other_processes_churn_locks`.
  It passed 5 of 5 times when run alone. Module.tracing, which this task does not touch. Already
  tracked by I-25c91daf (decision-needed). I appended a report there (report key
  `flaky-held-lock-churn-test/swe-cases-critical`). The second full-suite run, on 97963f22a:
  1663 passed, 6 skipped.
- **Verification.** `build --check` ok. `spec-validation` 0 errors, 5 warnings, all pre-existing in
  `specs/concorde/spec-tooling/spec/scenarios.md`. `task-validation`
  r-20261029T084911-task_validation-55e7347f ok, ready (no configured checks for this Module).
  `delivery` r-20261029T084955-delivery-1f53510f ok, delivery commit c06ba0e51.

## Report 1 to the main agent (项目中途停止状态检查), 2026-10-29T08:50:50Z

swe-cases-critical delivered: commit c06ba0e51 on concorde/swe-cases-critical (delivery r-20261029T084955-delivery-1f53510f ok). Ready to merge.

Issues this task resolves (the 5 in the brief):
- I-d4056271 (critical): `status_of` now checks whether a cut identity's matches agree on passing using the list's own rule. For PASS_TO_PASS, PASSED+SKIPPED now passes, and SKIPPED+FAILED is `not run` in either report order.
- I-773612e1 (critical): `passed` now counts every listing, like `total`. `not_passed` still names each test once.
- I-b2711abc: a finished test run's output is written to the log before the worktree is removed, so it survives a `cleanup_failed`.
- I-22041e63: `grade-statuses` now covers only the resolved situation. New scenario `grade-unresolved-statuses` covers the skipped and never-reported FAIL_TO_PASS tests.
- I-b69fdf23: the SHALL of `req.swe-bench-cases.repair-specs-only` now states the round's exits on a failed step. The code already stopped there.

Tests that fail on the old code (old cases.py swapped in: 3 failed):
- A passing test listed twice: old code gave passed 1/2, unresolved, with an empty `not_passed`.
- Cut PASS_TO_PASS identities: old code counted a SKIPPED+FAILED identity as maintained and a PASSED+SKIPPED one as `not run`.
- Cleanup failure: the log kept the earlier run's output.
New scenarios: `grade-cut-pass-to-pass`, `grade-listed-twice`, `grade-unresolved-statuses`, `grade-log-kept`.

Decisions I made:
1. For PASS_TO_PASS, the fix of I-d4056271 deliberately differs from SWE-bench's own `_resolve_case`. SWE-bench compares the matches by PASSED/XFAIL for both lists, which makes its verdict depend on report order. Exact parity is impossible anyway, because our statuses come in run order, not in the order of SWE-bench's summary. module.md now states this difference. FAIL_TO_PASS is unchanged.
2. `contract.swe-bench-cases.verdict` stays at version 1. Its semantics only add "each listing of a test counting once".
3. The entry now says which status a cut identity takes when its matches agree: the first one pytest reported, which is what the code already did.
4. The log promise got its own scenario (`grade-log-kept`) instead of another conditional step in `grade-cleanup-failed`, which I-d63aee32 already criticises.

Open, for you:
- I-761b648b (preferred-fix, medium, not in the brief): both of its gaps are now defined in the entry (the comparison rule and the selected status). However, its suggested repair (PASSED/XFAIL for both lists) is the one the critical fix overrules. Add it to the task's resolves or close it as you see fit.
- Flaky test outside this task: the first full-suite run failed only `tests/concorde/tracing/test_locks.py::...churn_locks` (module.tracing). It passed 5 of 5 times alone, and the second full-suite run passed (1663 passed, 6 skipped). This is already I-25c91daf (decision-needed). I appended a report saying it now also fails outside the check boundary under load.

Verification: `build --check` ok. `spec-validation` 0 errors (5 pre-existing warnings, all in Spec tooling's scenarios.md). Full suite green on the final input. `task-validation` r-20261029T084911-task_validation-55e7347f ready.

## Answer to report(s) 1 of the task session, 2026-10-29T08:51:25Z

Accepted. Decision 1 (PASS_TO_PASS by the list's own rule, documented divergence from SWE-bench's order-dependent harness) is the critical Issue's own suggested repair; the main agent accepts it and tells the developer. I-761b648b added to the task's resolves: both of its gaps are now defined in the entry, by the rule I-d4056271 requires. Merging now.

## Closed: merged, 2026-10-29T08:51:44Z
