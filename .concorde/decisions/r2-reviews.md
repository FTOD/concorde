# Decision log: r2-reviews

Goal: Fix the critical, high and obvious-fix open Issues of Spec review, Code review, Project review and Method found by the complete project_review, the critical first (I-0b4d954f)

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08) that this round fixes the **critical and high** open Issues of
every Module, plus each Module's **obvious-fix** Issues since they are cheap; medium and low
Issues of other tiers wait for a later round. This task resolves the 22 Issues in its `resolves`,
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

## Task session (2026-10-08)

Read all 22 Issues: none is `decision-needed`, so nothing is escalated up front. Working directly
(not through Operations), as the development skill allows; code first, the critical one first.

- **I-0b4d954f (critical, preferred-fix)**: the race holds. LangGraph `Send` runs panel seats in
  parallel on one `RunContext`, and Method's `absorb` returned `ctx.worker["output"]` after
  setting it, so another seat could replace it in between. Fix chosen: `absorb` returns the output
  from its own record (the first suggested repair; it fixes every caller of `run_worker`, not only
  the panel). A deterministic test re-enters `absorb` for a second seat inside the first; it
  fails on the old code ('first' != 'second'). Commit 1eabe0ea8.
- **I-3c6e0338 (obvious-fix)**: a panel that stops after reading its earlier Issues now carries
  every one of them (`settle(earlier, [], [])`), instead of `earlier_issues: null`; it stays null
  when they were never read. Applied where the panel graph stops or raises, so it also covers a
  caller that set `earlier` itself (project_review). Commit 42f066704.
- **I-ee6324dd (obvious-fix)**: the workflow note's blocking count now includes the carried
  blocking Issues. Commit 42f066704.
- **I-6125ecad (obvious-fix)** and **I-75bf22f7 (preferred-fix)**: `check_evidence` now checks
  each finding's basis against the context of the Module the finding names (documents and glossary
  terms), not the union of the reviewed Modules. A concept basis that is a term of that context is
  accepted and defined by the glossary file, whether or not its explanation is a selected document
  (preferred fix: term membership, the source the reviewer received). A finding about a Module not
  reviewed keeps only its `unresolved-module` problem. Commit 804027928.
- **I-6f685a0f (obvious-fix)**: the deterministic settlement keeps each resolved Issue's offered
  revision internally (not in the output, whose schema is unchanged); the verdict counts the
  resolution only while the revision is unchanged. Regression test appends a report between
  settlement and verdict. Commit 5d0ec092e.
- Correction to the I-6125ecad/I-75bf22f7 entry above: the first version of the fix rejected a
  finding about an unreviewed Module's basis too, which broke
  `test_a_finding_about_a_module_not_reviewed_is_not_reported`; amended before going on, so such a
  finding keeps only its `unresolved-module` problem (commit 804027928 as amended).

### Spec changes (direct edits; spec-validation `success` after each)

- **Context selections** (I-03936a00, I-3b2108d7, I-205ff263 and the review Modules' part of
  I-a64f2b0a), commit 6adba2c50. Chosen repair: narrow `relies_on` contract identities where the
  provider defines one, and justified `includes` of documents that define no identity:
  - Spec review: Workers' `contract.workers.grant-input`, `worker-result`, `worker-run-record`;
    Issues' `contract.issues.report`, `receipt` (selects `issues/interface.md`, the bookkeeping
    command); Execution's `contract.execution.run-result`; new `uses module.workflows` relying on
    `contract.workflows.step-output` with a `#uses-workflows` explanation and the diagram edge;
    includes `document.spec.contracts`, `document.method.module`, `document.method.workers` and
    (later commit) `document.method.requirements`.
  - Code review: the same Issues, Execution and Workflows reliances; includes
    `document.method.module` and `document.method.workers` (review Issue helpers, worker sequence
    and its errors).
  - Project review: Workers' `contract.workers.worker-run-record` and `req.workers.transient-retried`
    (its link to launch.md#retries), Execution's `contract.execution.run-result` and
    `req.execution.unbound-origin-untouched`, includes `document.method.module`.
  - Method is selected by `includes` rather than `uses module.method` because these Modules are
    Method's children and no child declares `uses` of its parent anywhere in the project.
  - A script checked that every provider document the three Modules' Specs link to is now in
    their context, except consumer and root mentions (Project review, Main session, the root
    requirements), which no Issue of this task concerns.
  - I-a64f2b0a's other parts: Tasks' Execution selection is tracked by I-2a23fd3b (task r2-tasks);
    Views' Spec core selection already holds (commit a7cdea89a includes document.spec.contracts and
    document.spec.errors). No new Issue needed.
- **Spec review** (commit d78a62134): split reports-issues / blank-earlier / finding-path into
  separate identities (`req.spec-review.reports-issues` kept, since Main session relies on it, now
  for the installed case only; new `nothing-recorded-without-issues`, `earlier-checked`,
  `finding-path-resumed`, `finding-path-listed`, `finding-path-others-stand`); the no-Issues
  retention and disclosure defer to Method's `req.method.findings-kept` and
  `req.method.issues-absent-stated` instead of duplicating them (I-fc91b0cf). Entry: a
  chair-resolved Issue no longer counts for that review's verdict but stays open and is offered
  again (I-76af6887). panel.md row 6: a refused trace write is `trace-write` evidence, never a
  failure (I-77561d06; the code already behaved so). panel.md also states the carried-on-stop and
  carried-in-count behaviour of the code fixes. Payload contract version unchanged (clarification).
- **Code review** (commit c0c126d49): earlier-Issues requirement includes Project review's
  `code-review` reports, with new `scenario.code-review.project-review-issues` and its test (the
  code already did so; preferred fix as suggested) (I-e3102905). Split evidence-resolves,
  store-refusal and verdict-derived into separate identities (I-e1c7733f). Contract: no-Issues
  verdict branch (I-63ef710f), notice in the run result's summary (I-22b74511), and basis per own
  Module with concepts by glossary entry; `contract.code-review.review` version 6 -> 7 because the
  basis check is a behaviour change.
- **Project review** (commit 73334bce5): standing defined once, current and remembered
  resolutions both revision-qualified, referenced from the requirement, the entry and the report
  contract (I-49cdbd36; contract version unchanged, the promise was already
  req.project-review.skipped-resolutions). record-refused split into three identities (I-3186686d).
- **Method** (commit dd4afd958): purpose qualifies the Spec-gap stop (I-a99b7c87); the blocked-worker
  scenario excludes glossary violations and failed worker-run records (I-ac7e5746); the
  worker-flow diagram ends with the status table's first-match order (I-0a8b4a1a; rendered with d2
  0.9.0).
- Correction: the amended Code review basis commit is d85406f12 (804027928 was the hash before the amend).

## Report 1 to the main agent (Review流程), 2026-10-08T14:21:53Z

r2-reviews delivered: delivery commit 72c19bcd9 on concorde/r2-reviews. All 22 Issues fixed; no escalation (none was decision-needed). Checks: full suite 1378 passed / 5 skipped, build --check clean, spec-validation success, task-validation ready.

Critical
- I-0b4d954f (preferred-fix): the race was real. Parallel panel seats share one RunContext, and Method's absorb read the output back from ctx.worker after setting it. Fix: absorb returns the output from its own record, which covers every run_worker caller. A deterministic re-entrant test fails on the old code. (1eabe0ea8)

Code fixes
- I-3c6e0338: a stopped panel carries every earlier Issue it read instead of returning null.
- I-ee6324dd: the workflow blocking count includes carried blockers. (42f066704)
- I-6125ecad: each Code review basis is checked against the finding's own Module context, not the union of contexts.
- I-75bf22f7 (preferred-fix): a concept basis is accepted when it is a term of that context, and the glossary is its defining file. (d85406f12)
- I-6f685a0f: a deterministic resolution counts only while the Issue keeps its offered revision. A regression test appends a report between settlement and verdict. (5d0ec092e)

Context selections (6adba2c50)
- I-03936a00, I-3b2108d7 (preferred-fix), I-205ff263 and I-a64f2b0a (preferred-fix).
- Choice: narrow relies_on on provider contracts (Issues report/receipt, Execution run-result, Workers contracts, Workflows step-output) plus justified includes of Method's entry, workers.md and requirements, and Spec core contracts.
- Method is reached through includes, not uses, because no child Module uses its parent.
- I-a64f2b0a's other parts: Tasks is already tracked by I-2a23fd3b in r2-tasks. Views already holds since commit a7cdea89a. No new Issue was needed.

Spec fixes
- Spec review (d78a62134):
  - I-fc91b0cf: requirements split. reports-issues is kept for Main session's reliance, and the no-Issues case defers to Method's requirements.
  - I-76af6887 (preferred-fix): a resolved Issue no longer counts for the verdict but stays open.
  - I-77561d06: a refused trace write is evidence only.
- Code review (c0c126d49):
  - I-e3102905 (preferred-fix): Project review's code-review Issues are earlier Issues, with a new scenario and test.
  - I-e1c7733f: requirements split.
  - I-63ef710f: no-Issues verdict branch added.
  - I-22b74511: the no-Issues notice is in the run result's summary.
  - The per-Module basis is a behaviour change, so contract.code-review.review goes from version 6 to 7.
- Project review (73334bce5):
  - I-49cdbd36 (preferred-fix): one revision-qualified definition of a standing Issue.
  - I-3186686d: record-refused split.
- Method (dd4afd958):
  - I-a99b7c87: the purpose qualifies the gap stop.
  - I-ac7e5746: the blocked-worker scenario excludes overriding failures.
  - I-0a8b4a1a: the diagram follows the first-match precedence.

Nothing is open for the developer. Details are in the decision log.

## Closed: merged, 2026-10-12T14:30:29Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 72c19bcd9482b8991ba71e3c7a95397aecb1b0e6 into main and closed it as merged. Nobody answers a report after that.
