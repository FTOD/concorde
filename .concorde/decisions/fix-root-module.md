# Decision log: fix-root-module

Goal: Resolve the open non-decision Issues of the root Module module.concorde

## Brief (main agent, 2026-10-02)

Open Issues of this task's Modules, most severe first:

- I-04cc33c58d0a5b339dbc6f7d20022697 (module.concorde, high, preferred-fix): Brownfield's no-file-change promise excludes required test annotations
- I-207f3d582e635d60a1a5409d91b4fbfb (module.concorde, medium, preferred-fix): The test-timing summary counts subtest failures differently from pytest's terminal line without saying so
- I-c6d7ecd61ea75e88ac6417abe175d8e9 (module.concorde, medium, preferred-fix): Boundary definitions conflate Protocol jobs with Concorde Tasks
- I-119dc38ff4065c31811cd1c611ca4b98 (module.concorde, medium, preferred-fix): Capability context has inconsistent contract contents
- I-44cde169a4c95bd79fc1c33b80f655e5 (module.concorde, medium, preferred-fix): The claims-separation requirement is narrower than its explanation
- I-0043f5f633545e3a8fac54b8ad7f0482 (module.concorde, medium, preferred-fix): The access-limit promise lacks its canonical boundary context
- I-01424e7e982d55ceb0f072f975635d6f (module.concorde, medium, preferred-fix): Success scenarios do not establish the conditions for their promised outcomes
- I-73b2e51e1d3f5dd5a694b1455bd56cd0 (module.concorde, medium, preferred-fix): The write-audit scenario exceeds documented audit coverage
- I-9ca2860afd5e50f4b5de7fb806f32adb (module.concorde, medium, preferred-fix): The agent decision policy is outside the root's selected context
- I-f3b333425f6e5c6a830dfcf99b2540d9 (module.concorde, low, obvious-fix): The universal task rule omits the approved small-change exception
- I-9ccd13d6c0115c65a9d1c706a0dd8100 (module.concorde, low, obvious-fix): The detailed-error obligation omits its stated exception
- I-e615d83d9ca85512b52de5dd35b41c1f (module.concorde, low, obvious-fix): Delivery separation combines three independent obligations
- I-16dfaec8d4825376a5cebd82b31243a7 (module.concorde, low, suggestion): Scenario prose maintains a standing verification claim
- I-d802c284162b55a6a03269786a6ec5b2 (module.concorde, low, suggestion): Task-to-merge places an expected outcome among its actions
- I-98b0a71a2b505655bca7b363c954ed2a (module.concorde, low, suggestion): The brownfield scenario leaves its workflow terms unlinked
- I-8b73d5829f9b5521b2569faec1eb8654 (module.concorde, low, suggestion): Several child collaborations could identify their relied-on promises more clearly
- I-6c5dfe9044aa530dbf8ddf09ec635fde (module.concorde, low, suggestion): The seam explanation's exclusive source list omits Git state
- I-a1d60555de22591d95b6b35c6655a26f (module.concorde, low, suggestion): Clarify that the AI-operation rule permits refusal before launch

The developer asked the main agent (2026-10-02) to resolve every Issue that does not need the
developer. This task takes the open Issues listed above, none of them decision-needed (the main
agent triages those separately). For each Issue:

1. Read it with `python3 scripts/concorde.py issues show <id>` and check that it still stands at
   your HEAD: several tasks merged on 2026-10-01/02 (issue-write-recovery, mcp-fresh-code,
   run-lock-before-records, workflow-lock-before-records, lock-recovery-followups). One already
   fixed is closed with `concorde issues close <id> --reason resolved --note … --evidence <commit>`;
   a duplicate with `--reason duplicate --duplicate-of <id>`.
2. Fix it by its tier: `obvious-fix` alone; `preferred-fix` with the fix you judge best, which
   you report; `suggestion` only when it clearly improves the Specs or code at small cost,
   otherwise leave it open and say why in your report.
3. Add every Issue you fixed to this task with `python3 scripts/concorde.py task resolve <task>
   <id>…`, so the merge closes it. Never add one you did not fix.

Rules: change only the Modules this task binds. A fix another Module needs, or a fix that turns
out to need a decision (it would change what a Module promises its users, contradict an earlier
decision of the developer, discard work, or loosen a boundary), is escalated, all together at the
end, after everything else is done; a problem you find in another Module is recorded as an Issue
of that Module. Do not touch module.workers, module.harness, module.execution, module.e2e or
module.dogfood-scenarios: task worker-git-isolation is changing them. Other tasks run in
parallel on module.issues, module.main-session, module.distribution, module.concorde and a group
of small Modules; each keeps to its own. Verify with build --check, spec-validation and the full
suite, then task-validation and delivery, and report: what you fixed (with the fix chosen for
each preferred-fix), what you closed as already resolved or duplicate, the suggestions you left
open and why, and the escalations.

## Addendum (main agent, 2026-10-02): decision-needed Issues decided by the main agent

The main agent triaged the decision-needed Issues and decided these within its authority (ordinary scope: each qualifies or documents a promise following existing decisions). Fix each with the decision given, then add it with `task resolve` like the others:

- I-431ebf9d2aba500cab75f1ed74fef3f0 (test evidence fingerprints and --prior): document what tests/concorde/support/pytest_timing.py does today (each fingerprint category's digest, --prior=PATH comparison, missing or invalid prior, report fields) and add a changed/unchanged scenario.
- I-7877eef701b651c5b3de8f3825b9cfa5 (documentation fetcher refresh): specify the current behaviour of fetch-claude-code-docs.py; if it writes in place, make publication atomic (fetch into a temporary directory, then swap), otherwise note that Git restores the tracked docs after a failed refresh.
- I-7c0cd43a20d6500bb52a23c54400432c (flaky pytest-timing fingerprint test under xdist): find which input changes, then compute the fingerprint over a fixture tree copied to a temporary directory so no parallel test changes its inputs; no serial marks or reruns.
Not yours: I-09f5bed334e85150ba1646248b9f1d1a and I-bf0b3e2374d35abf9d30f730b22e8887 wait for the developer.

## Task session, 2026-10-02: fixes and decisions

All 21 Issues (18 of the brief, 3 of the addendum) still stood at 3f370489; none was already
resolved or a duplicate. Fixed in 111e9e20 (root Spec) and 27058b00 (development environment):

- I-04cc33c5 (preferred-fix): adopt-brownfield now allows exactly Adoption's `verifies`
  declarations and helper in existing tests, linking req.adoption.test-edits-limited; Spec first
  says Adoption "never changes what the code does" and links req.adoption.no-code-change. Chosen
  over removing the clause, so the scenario still promises no behaviour change.
- I-207f3d58 (preferred-fix): kept the per-unit convention; plugin docstring and a new
  `counting_note` field in the summary state it; new req.concorde.test-counting and
  scenario.concorde.test-counting, verified by a fixture with a failing subTest. No schema_version
  bump: one field added, nothing removed (rapid iteration, no consumer compares it).
- I-c6d7ecd6 (preferred-fix): the entry says "task" in Context and boundaries is the Protocol's
  word for one worker's job, not a Concorde Task, and that a task session gets the session
  boundary; glossary Boundary and Task type now speak of a worker's job, with contrasts to
  concept.session-boundary and concept.task.
- I-119dc38f (preferred-fix): entry and glossary both name tool contracts and the worker-result
  contract, with their two purposes.
- I-44cde169 (preferred-fix): req.concorde.claims-apart holds for every run result and links
  req.execution.claims-apart.
- I-0043f5f6 (preferred-fix): root `includes` document.spec.contracts (reason: the task-type
  table of grants and the boundary sets) and req.concorde.no-wider-than-type links its #grants and
  #boundary-sets. Chosen over a `uses` of module.spec because the table lives in contracts.md,
  which defines no identity a `relies_on` could name. This widens only the read-only Spec context
  of root-bound workers, not any write or enforcement boundary.
- I-01424e7e (preferred-fix): task-to-merge, parallel-tasks and adopt-brownfield now state their
  success conditions (configured checks pass, Spec states the promises, implement/code_to_spec end
  `ok`, task-validation finds the workspace ready, no concurrent change on the primary branch);
  a note under adopt-brownfield covers the no-ask partial description, linking
  req.workflows.no-ask-describe-continues.
- I-73b2e51e (preferred-fix): worker-escalates' GIVEN is a persistent change to a file Git does not
  ignore; a note links Harness's known limits for ignored and throw-away writes.
- I-9ca2860a (preferred-fix): root `uses` module.main-session with relies_on ordinary-decisions,
  task-session-decides, task-session-escalates, escalation-policy and small-change, explained at
  #uses-main-session. Chosen over `includes` because the Protocol's `relies_on` names exactly the
  promises relied on and selects only Main session's entry and requirements.
- I-f3b33342, I-9ccd13d6 (obvious-fix): exception added to the task rule and to the
  detailed-errors SHALL.
- I-e615d83d (obvious-fix): req.concorde.delivery-separate now only says a task is delivered only
  by a delivery commit (title changed, id kept) and links req.delivery.own-readiness; the
  commit-authority duty is its own req.concorde.delivery-commit-by-delivery, linking
  req.delivery.marked.
- Suggestions, all fixed as small clear improvements: I-16dfaec8 (removed the standing
  verification sentence), I-d802c284 (binding claim moved under THEN), I-98b0a71a (term links),
  I-8b73d582 (Issues, Distribution and End-to-end testing paragraphs link the promises the root
  relies on and their failure reactions), I-6c5dfe90 (seam explanation names Git state beside the
  run store and delivery commits), I-a1d60555 (operations-are-ai scoped to runs not refused before
  their first worker, explained as a classification).
- I-431ebf9d (main agent's decision): development.md specifies the fingerprints
  (req.concorde.test-fingerprints) and --prior (req.concorde.test-prior) as implemented, with
  scenarios test-prior-unchanged/-changed/-unreadable. One behaviour changed: a missing or invalid
  --prior used to crash in pytest_sessionfinish with a traceback after all tests ran; it is now a
  pytest usage error (exit 4) before any test runs. Decided myself as the only sensible
  documented behaviour. The fingerprint now reads pytest's root directory instead of the fixed
  checkout path; identical for this checkout's suite.
- I-7877eef7 (main agent's decision): the fetcher wrote in place (rmtree then write), so it now
  writes into a temporary directory beside references/claude-code and swaps it in, restoring the
  previous snapshot if the swap fails; development.md documents the refresh,
  req.concorde.docs-refresh-whole and two scenarios, verified by a new test with a faked fetch.
- I-7c0cd43a (main agent's decision): all plugin tests now run over a fixture project in a
  temporary directory with its own `git init`, including the pytest subprocess runs whose digests
  are compared. Which input changed in the reported failure is not established: a full suite run
  watched every 0.2 s for changes of the fingerprinted inputs showed no test changing one; the only
  change seen was this session editing specs/concorde/module.md during the run, the kind of
  concurrent change that would explain the failure. The fixture tree removes the dependence either
  way.

Verification: build --check and spec-validation success with no findings; full suite 901 passed,
4 skipped (before the final reflow of module.md; final run follows).

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T17:24:36Z

fix-root-module delivered: delivery commit 44e5c810 on concorde/fix-root-module (steps 111e9e20 root Spec, 27058b00 development environment). build --check and spec-validation pass with no findings, full suite 901 passed and 4 skipped, task-validation ready.

All 21 Issues still stood at 3f370489. None was already resolved or a duplicate. All 21 are fixed and added with task resolve.

Preferred-fix, with the fix chosen:
- I-04cc33c5: adopt-brownfield allows only Adoption's verifies declarations and helper in existing tests (links req.adoption.test-edits-limited). "Spec first" now says Adoption never changes what the code does.
- I-207f3d58: kept per-unit counting. Stated in the plugin docstring and a new counting_note field. Added req/scenario test-counting, tested with a failing subTest.
- I-c6d7ecd6: "task" in Context and boundaries now means the Protocol's worker job. Glossary Boundary and Task type contrast with session-boundary and Task.
- I-119dc38f: entry and glossary now both name the tool contracts and the worker-result contract.
- I-44cde169: claims-apart covers every run result and links req.execution.claims-apart.
- I-0043f5f6: the root includes document.spec.contracts (task-type table, boundary sets), and no-wider-than-type links it. This widens only the read-only Spec context of root-bound workers.
- I-01424e7e: the success scenarios state their conditions. A note covers the no-ask partial description.
- I-73b2e51e: worker-escalates now needs a persistent, non-ignored change. It links Harness's audit limits.
- I-9ca2860a: the root uses module.main-session with relies_on its 5 decision-policy requirements (#uses-main-session).

Obvious-fix:
- I-f3b33342: the task rule now names the approved small-change exception.
- I-9ccd13d6: the detailed-errors SHALL now carries its exception.
- I-e615d83d: delivery-separate now covers only recognition (id kept, retitled). The new req.concorde.delivery-commit-by-delivery holds the commit authority. Both link Delivery.

Suggestions, all fixed because each was small: I-16dfaec8, I-d802c284, I-98b0a71a, I-8b73d582, I-6c5dfe90, I-a1d60555.

Addendum Issues:
- I-431ebf9d: fingerprints and --prior are documented as implemented, with scenarios test-prior-unchanged, -changed and -unreadable. One behaviour changed, my decision: an unreadable --prior used to crash after all tests ran; it is now a pytest usage error (exit 4) before any test runs. The fingerprint now reads pytest's rootdir, which is the same path for this checkout.
- I-7877eef7: the fetcher wrote in place. It now writes beside the target and swaps the snapshot in, restoring the old one on failure. Documented with req.concorde.docs-refresh-whole and 2 scenarios, plus a new test.
- I-7c0cd43a: the plugin tests now run over a temporary git fixture project. Which input changed in the reported failure is not established: a watched full run showed no test changing an input, only a concurrent edit by this session, the likely kind of cause.

Escalations: none. Issues of other Modules: none found. Details are in the decision log.

## Closed: merged, 2026-10-02T02:17:15Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 44e5c810d6d82f1b4de2490c5c343c4f80a3e9d9 into main and closed it as merged. Nobody answers a report after that.
