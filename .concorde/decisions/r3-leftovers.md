# Decision log: r3-leftovers

Goal: Execution's admission refusal carries its causes (admission half of I-2ebd101b), Method's Issue calls use the workspace's own concorde without the old fallback, and Main session says a Spec challenge is always decision-needed

## Task brief (main agent, 2026-10-13)

Three small leftovers of round 3, each in its Issue (read with `concorde issues show`):
- I-2ebd101b: r3-reviews fixed the round-check half (100feeb79). The admission half needs
  Execution's admission refusal (`Refused`) to carry causes, so a refused admission's error link
  names what below refused it. Change Execution (runner, its error contract if needed), then let
  the review Operations pass their causes through; tests.
- I-4aa68b8b (suggestion): Method's Issue calls still use workflows.step.concorde_command and so
  keep the old fallback that r3-workflows-issues-root removed for workflow steps; make them use the
  workspace's own concorde with no fallback, consistent with I-9c638fd9's fix.
- I-f4f6d09e: specs/concorde/coordination/main-session/module.md (about line 791) says a Spec
  challenge is "usually decision-needed"; r3-reviews settled it is always decision-needed (set by
  code_review). Align it and any guidance prompt repeating it.
Task issue-exception-scope may also edit the main-session guidance (the Issue-system failure
section); keep your edit to the Spec-challenge sentence. Deliver with task-validation then
delivery; full suite once.

## Task session decisions (2026-10-13)

- I-2ebd101b (admission half): Execution's `Refused` gains `causes` (links); the runner keeps them
  below the admission's own `component` link. Method's `specs_unloadable` (specs.py `_registered`)
  and project_review's own `specs_unloadable` now pass `spec_cause(error)` (actor `Spec core`).
  Specs: runner.md (refusal details, Errors table), new scenario
  `scenario.execution.admission-refusal-causes`, Method module.md's Definitions realization. The
  project_review edit is one argument in module.project-review's operation.py, outside the task's
  Modules; done because the brief asks the review Operations to pass their causes through.
- I-4aa68b8b: Method resolves its own launcher (`review_issues.started_concorde`: installed
  `.concorde/bin/concorde`, else the source checkout's `scripts/concorde.py`, else none) and no
  longer imports `workflows.step.concorde_command`; with neither, the call fails with
  `issues_command_failed` (reason `environment`) and runs nothing. Added
  `req.method.issues-own-concorde` and `scenario.method.issues-concorde-missing`. The test
  project `OperationProject` now commits an installed `.concorde/bin/concorde`, as the parallel
  task r3-workflows-issues-root did for `BrownfieldProject`. I left `workflows.step.concorde_command`
  in place (module.workflows is not this task's); once both tasks merge it has no caller left and
  Workflows may delete it.
- I-f4f6d09e: main-session module.md now says a Spec challenge is "always `decision-needed`"; the
  task-session guidance prompt already said "always", so no prompt change.
- Full suite at 561e8b145: first run 1 failed / 1555 passed
  (project_mcp test_register_wait_wakes_on_release_and_on_a_task_state: "the wait outlived its
  server"); not reproduced alone (3/3), in a loaded partial run (4/4) or in two more full runs
  (1556 passed each). Not fixed here; recorded as Issue I-4bb624fc (decision-needed, medium,
  module.main-session), since its cause is not established (possibly related to test projects
  now running .concorde/bin/concorde, a sh script that execs python).

## Report 1 to the main agent (Review流程), 2026-10-13T15:44:47Z

r3-leftovers delivered: delivery commit 4063fa3dddfc on concorde/r3-leftovers (task-validation ready; delivery ok; full suite 1556 passed in two runs). Resolves I-2ebd101b, I-4aa68b8b, I-f4f6d09e (added with task resolve).
1. I-2ebd101b (admission half): Execution's Refused gains causes; the runner keeps them below the admission's component link (runner.md refusal details and Errors table; new scenario.execution.admission-refusal-causes). Method's specs_unloadable and project_review's own specs_unloadable pass Spec core's error via spec_cause, nested causes kept. Preferred fix chosen: carry links on Refused rather than have the runner translate Python exception causes, so Execution stays ignorant of Spec tooling. The project_review edit is one argument in module.project-review's operation.py, outside the task's Modules, done because the brief asked the review Operations to pass causes through.
2. I-4aa68b8b: Method's review_issues has its own started_concorde (installed .concorde/bin/concorde, else scripts/concorde.py, else none); with neither, the call fails with issues_command_failed (environment) and runs nothing. New req.method.issues-own-concorde and scenario.method.issues-concorde-missing. The OperationProject test fixture now commits an installed .concorde/bin/concorde, as r3-workflows-issues-root did for BrownfieldProject. workflows.step.concorde_command is left untouched (module.workflows is not mine); once both tasks merge it has no caller and Workflows may delete it.
3. I-f4f6d09e: main-session module.md now says 'always decision-needed'; the task-session guidance prompt already said 'always'.
Open: one full-suite run failed once in project_mcp test_register_wait_wakes_on_release_and_on_a_task_state ('the wait outlived its server'); it did not happen again in 3 runs alone, 4 loaded partial runs or 2 more full runs. Recorded as Issue I-4bb624fc (decision-needed, medium, module.main-session); cause not established.

## Closed: merged, 2026-10-13T15:45:01Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 4063fa3dddfc849abce32b6cd90f4a06a785046a into main and closed it as merged. Nobody answers a report after that.
