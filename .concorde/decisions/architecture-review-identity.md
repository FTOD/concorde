# Decision log: architecture-review-identity

Goal: Make the review-architecture grant identity cover every ProjectSpecification member and the whole glossary, have spec_panel report its architects' merged findings with provenance phase architecture so project_review offers them as earlier Issues, and fix Project review's open wording Issue

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08): fix every known open Issue before the first full
`project_review`. This task resolves the 4 Issues in its `resolves`:

- **I-26297c83 (module.spec, high, preferred-fix)**: the published grant identity algorithm does
  not include ProjectSpecification specially for `review-architecture`, so an architecture identity
  can stay the same over different project Specs. Specify and implement that a
  `review-architecture` grant's context identity covers every ProjectSpecification member and the
  complete glossary; keep the ordinary helper's scope explicit; add an example where an unrelated
  Module changes. Note: project_review's skip of the architecture review relies on this identity,
  so after the fix that skip must react to any Module's Spec change. The spec part depends on
  nothing (2026-10-03 decision): keep it self-contained.
- **I-9f990232 (decision-needed, decided by the main agent on 2026-10-08, escalation 7 of
  project-review)** and **I-8e98340f (preferred-fix)**: `spec_panel` reports its architects' merged
  findings with provenance phase `architecture` (its reviewer findings keep phase `report`), and
  project_review's architecture review offers spec_panel's architecture-phase Issues as earlier
  Issues, so duplicates stop. Update both Specs, code, tests.
- **I-983bb766 (suggestion)**: apply the wording fix in Project review's Spec.

A later task, `kernel-merge-marker`, will also touch module.project-review; it starts after this
one merges. Escalate anything that changes what spec_panel or project_review promise beyond this.
Deliver with `task-validation` then `delivery`; run the full suite once on the final input.

## Task session decisions (2026-10-08)

- **I-26297c83**: `grants.context_identity` already takes `project_specification` and `grant` passes it
  for `review-architecture`, so the defect is the published contract alone. I specify the parameter, the
  `project_specification` item (every ProjectSpecification member's path and digest, the glossary
  file whole included), keep the ordinary helper's bound-Module scope explicit, and add an example
  with an unrelated Module and an unrelated glossary entry; tests extended to the glossary case.
- **Mixed merges (I-9f990232/I-8e98340f)**: a chair finding is an architects' finding, reported with
  phase `architecture`, when every label it merges is an architect's (`a<n>.<m>`); any finding that
  merges a reviewer's label keeps phase `report`. Reason: the brief keeps reviewer findings at
  `report`, and a problem a reviewer also found is one the Module panels (which have reviewers) can
  judge again. Its report key is then `architecture/<module>/<n>`, as Review Issues prefixes every
  non-`report` phase.
- **Module panels of project_review** now offer only spec_panel's `report`-phase Issues (plus their own
  `spec-panel` phase), so an architecture Issue is offered to exactly one kind of review in a
  project_review run (the architecture review) and is not judged twice. Standalone `spec_panel` keeps
  offering all of spec_panel's Issues, since it has architects.
- **review_issues.report (module.method's file)**: I extend its `phase` to also accept a function of the
  finding, a backwards-compatible change of three lines, instead of duplicating its unreported-finding
  bookkeeping in Spec review. Method's Spec already says "every report carries the phase its review
  gives", so no Spec of module.method changes.

## Main agent, 2026-10-08: one more Issue

Added I-f9acf9f0 (module.spec, obvious-fix, medium), found by task bind-skill-links, to this
task's `resolves`: a symlink realization entry makes spec-validation abort with an unlocated
`invalid_field` error instead of reporting CHK.binds.exists at the entry (expand_entry calls
checked_path unguarded). Fix it here, since this task already works on module.spec.
- **I-f9acf9f0 (added by the main agent)**: `expand_entry` now treats an entry through a symbolic link
  as binding nothing (the same `ValueError` guard `entry_exists` has), so `spec-validation` reports
  `CHK.binds.exists` at the entry; validation.md and scenario.spec.missing-entry say so; new test.
- **I-983bb766**: req.project-review.skip-unchanged now puts its conditions first and lists the parts
  in a second paragraph (the Protocol requires a one-sentence statement); I also added that the
  architecture identity covers every Module's documents and the glossary, as the brief notes.
  req.project-review.record-completed puts its "only when" first.
- Added scenario.project-review.spec-change (a Spec change of one Module re-runs the architecture
  review) and scenario.project-review.architecture-earlier, each with a test. The Spec change also
  re-runs that Module's code review, since the review-code identity covers its Specs; the scenario
  does not claim otherwise.
- spec-review module.md: the caller-given phase is stated to replace the per-finding phase, and a
  run-on list item ("It keeps the parts…") was split into its own paragraph.

## Report 1 to the main agent (concorde-d4), 2026-10-08T02:11:48Z

architecture-review-identity delivered: delivery commit a09d17e8 on concorde/architecture-review-identity (task-validation ready, no blocking; full suite 1288 passed, 5 skipped; spec-validation 0 errors, 12 pre-existing warnings; build --check clean).

Resolves all 5 Issues in resolves:
- I-26297c83 (module.spec): the code already gave review-architecture grants a project_specification identity; only the contract lacked it. contracts.md#grants now specifies context_identity(..., project_specification), whose extra member digests every ProjectSpecification path (every Module's documents + the whole glossary file), keeps the ordinary helper's bound-Module scope explicit, and gives an example with an unrelated Module D and an unrelated glossary entry. Requirement and scenario extended; test covers the glossary case.
- I-f9acf9f0 (module.spec): expand_entry now guards checked_path, so an entry through a symlink binds nothing and spec-validation reports CHK.binds.exists at the entry instead of aborting. validation.md + scenario.spec.missing-entry updated; regression test (fails before the fix).
- I-9f990232 / I-8e98340f: spec_panel reports a chair finding whose every merged label is an architect's (a<n>.<m>) with phase architecture and key architecture/<module>/<n>; any finding merging a reviewer label keeps phase report. project_review's architecture review now offers spec_panel's architecture-phase Issues; its Module panels (no architects) offer only spec_panel's report-phase ones. New scenario.project-review.architecture-earlier with test.
- I-983bb766: req.project-review.skip-unchanged puts its conditions first (statement must stay one sentence, so the part list moved to a second paragraph) and now states the architecture identity covers every Module's Specs and the glossary; record-completed puts "only when" first. New scenario.project-review.spec-change with test (a Spec change of one Module re-runs the architecture review).

Decisions I took (all in the decision log): the "every label is an architect's" rule for mixed merges; narrowing project_review's Module-panel sources to spec_panel's report phase so an architecture Issue goes to one kind of review only; a backwards-compatible 3-line extension of src/concorde/method/review_issues.py (module.method's file) so report() takes a per-finding phase, instead of duplicating its unreported-finding bookkeeping in Spec review (Method's Spec already says each report carries the phase its review gives, so no Method Spec change); a small wording fix in spec-review module.md. No escalations; nothing open.

## Closed: merged, 2026-10-08T02:12:03Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit a09d17e818f3bda25942ef006d504a7d925cb2ee into main and closed it as merged. Nobody answers a report after that.
