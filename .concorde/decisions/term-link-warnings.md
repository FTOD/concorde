# Decision log: term-link-warnings

Goal: Clear the two spec-validation warnings CHK.term.unlinked: link Decision point in adoption/module.md and Spec in spec-mcp/requirements.md

## Brief (main agent, 2026-10-02)

spec-validation on main reports two warnings, both CHK.term.unlinked:
- specs/concorde/execution/operations/adoption/module.md line 122: link the first use of
  'Decision point' as [Decision point](../../../glossary.json#concept.decision-point);
- specs/concorde/spec-tooling/spec-mcp/requirements.md line 49: link the first use of 'Spec' as
  [Spec](../../glossary.json#concept.spec).
Link each term at its first use (or rephrase where the word is not the term). Done when
spec-validation reports no warning; then build --check, task-validation and delivery, and report.
No Issue tracks these.

## Task session (2026-10-02)

- spec-mcp/requirements.md line 49: the flagged "Spec" was not the term Spec but the first word of
  the Module title "Spec core", wrapped onto the next line. CHK.term.unlinked blanks Module titles
  line by line, so a title split across lines is not recognised. Decision: rewrap so "Spec core's"
  stays on one line (the brief allows rephrasing where the word is not the term) rather than link
  "Spec" to concept.spec, which would be wrong there.
- adoption/module.md line 122: linked "decision points" to concept.decision-point.
- The checker gap (Module titles split across lines) is reported as an Issue of module.spec.
- task-validation r-20261002T031349-task_validation-f65cfd75: `blocked` by check.tasks.tests,
  test_a_report_is_recorded_before_the_message (task close exited 1). Unrelated to this Spec-only
  change; the test passed 3 times alone and the module.tasks suite 3 times. Reported as an Issue of
  module.tasks (intermittent); decision: re-run task-validation.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-02T03:21:26Z

term-link-warnings delivered: delivery commit d79d6268 on concorde/term-link-warnings (delivery run r-20261002T031921-delivery-3b494f22). spec-validation now reports no warning; build --check clean.
Changes (commit d025a021): adoption/module.md links "decision points" to concept.decision-point. In spec-mcp/requirements.md the flagged "Spec" was not the term Spec: it was the first word of the Module title "Spec core" wrapped onto the next line, so I rewrapped the sentence to keep "Spec core's" on one line instead of linking it (the brief allowed rephrasing).
Decisions without the developer: that rewrap rather than a link, and re-running task-validation once (see below).
Non-ok result: the first task-validation (r-20261002T031349-task_validation-f65cfd75) was blocked by check.tasks.tests, test_a_report_is_recorded_before_the_message (task close exited 1). This is unrelated to the change: the test passed 3 times alone and the module.tasks suite passed 3 times. The re-run (r-20261002T031720-task_validation-b774d111) was ready.
New Issues: I-cf00a5fa111f59c9919cb54bff6084d1 (module.spec, obvious-fix, low): CHK.term.unlinked blanks Module titles line by line, so a title wrapped across lines gives a false warning. I-c496879cc46153919fbd45a38c152858 (module.tasks, decision-needed, medium): that intermittent test failure, cause unknown.
Nothing open for this task; it resolves no Issue.

## Closed: merged, 2026-10-02T03:21:38Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit d79d626886e22c8324d8d071dd5ca9404edeb657 into main and closed it as merged. Nobody answers a report after that.
