# Decision log: issue-exception-scope

Goal: Dogfooding sends only failures of the Issue system (crash, wrong result, wrong refusal) as bare error chains; a recordable design limitation of Issues goes as an ordinary defect report

## Task brief (main agent, 2026-10-13)

Resolves I-a9045871 (read it with `concorde issues show`). The developer's 2026-10-01 rule is that
Issue-system defects never go through Issues, because a failed Issue system cannot be trusted to
record its own failure. Dogfooding today sends every Issue-system defect, design limitations
included, as a bare error chain, while Issues says a recordable design gap of Issues is an ordinary
Issue.

Developer decision (2026-10-13): **read the rule by its reason**. Only failures of the Issue system
(a crash, a wrong result, a wrong refusal, the environment refusals the guidance lists) go as bare
error chains; a design limitation of Issues that the working store can record goes as an ordinary
defect report. Align Dogfooding's Spec (and its guidance under prompts/), Issues' Spec where it
states the rule, the main-session guidance's "When the Issue system fails" section if it says
otherwise, and the scenarios. Update the memory-backed wording only in the repository. Deliver with
task-validation then delivery; full suite once.

## Task session decisions (2026-10-13)

- Renamed `req.dogfooding.issue-system-defect`, `-kept` and `-named` to `issue-system-failure`,
  `-kept`, `-named` (titles and text say "failure"), and added
  `req.dogfooding.issue-design-limitation-reported`. Reason: the ids now name what they cover; no
  other Spec or test referenced the old ids (rapid iteration, no compatibility kept).
- Renamed Dogfooding's section "A defect of the Issue system" to "A failure of the Issue system";
  no anchor pointed to the old heading. Its example of a wrong refusal stays
  `concorde issues report --check` refusing a correct report. Added that a failure met while
  checking or writing a design-limitation report goes as a failure.
- Issues' "Failures of the Issue system" got one sentence saying the exception covers failures only
  (crash, wrong result, wrong refusal, `environment` refusals). No link to Dogfooding, since Issues
  depends on the Kernel alone.
- Main-session guidance ("When the Issue system fails"), its Spec, Issues' requirements and the
  review Modules already speak only of failures: left unchanged.
- `specs/concorde/e2e/dogfood/module.md` (module.dogfood-scenarios, outside the task's Modules)
  still says Dogfooding sends "such a defect" as a bare chain. Not changed here; recorded as Issue
  I-2d958da33dcb5acd9663f0f3e0ca8a7d (obvious-fix, low).
- Added I-a9045871b20d5a57bfb216401099e45c to the task's resolves.
- Full suite (non-ok): first run 1 failed, 1544 passed:
  `tests/concorde/e2e/test_owners.py::OwnersCaseTests::test_a_run_refused_for_a_busy_workspace_stops_the_case_with_an_error`.
  It passed alone 4/4 and a second full run passed (1545 passed, 5 skipped). It is unrelated to
  this change (Spec/prompt/test-fragment only). Reopened its earlier Issue
  I-566e82f14dd05300856042bc9472f58b as a recurrence.

## Report 1 to the main agent (Review流程), 2026-10-13T15:13:57Z

Task issue-exception-scope delivered: delivery commit 4a80ba00efb1df495ad45d65ef9dc897ab3fc190 (change 57c320953). Resolves I-a9045871b20d5a57bfb216401099e45c (added to the task's resolves).

What changed:
- Dogfooding Spec: section renamed to "A failure of the Issue system". Only a crash, a wrong result or a wrong refusal of the Issue store, `concorde issues` or the Issue tools goes as a bare error chain. The example of a wrong refusal is `report --check` refusing a correct report. A design limitation of Issues that the working Issue system can record goes as an ordinary defect report. A failure met while checking or writing that report goes as a failure. Requirements renamed issue-system-defect{,-kept,-named} -> issue-system-failure{,-kept,-named}. New req.dogfooding.issue-design-limitation-reported. The scenario.dogfooding.guidance lines were updated to match.
- prompts/dogfooding/skill.md: the same change; its test fragments in tests/concorde/dogfooding were updated.
- Issues Spec, "Failures of the Issue system": one sentence saying the exception covers failures only. It has no link to Dogfooding, since Issues depends on the Kernel alone.
- Main-session guidance ("When the Issue system fails"), its Spec, Issues' requirements and the review Modules already speak only of failures, so they are unchanged.

Decisions I made (all in the decision log): the requirement ids were renamed, because nothing else referenced them. Issues got no back-link to Dogfooding.

Still open:
- specs/concorde/e2e/dogfood/module.md (module.dogfood-scenarios, outside this task) still says Dogfooding sends "such a defect" as a bare chain. I recorded it as I-2d958da33dcb5acd9663f0f3e0ca8a7d (obvious-fix, low) and did not change it.
- Full suite: the first run had 1 failure, tests/concorde/e2e/test_owners.py::...test_a_run_refused_for_a_busy_workspace_stops_the_case_with_an_error. It passed alone 4/4. A second full run passed (1545 passed, 5 skipped). This flakiness was fixed before, so I reopened I-566e82f14dd05300856042bc9472f58b as a recurrence.

Checks: build and build --check pass. spec-validation has 0 errors and 5 earlier warnings, none in the changed files. task-validation is ready with no blocking findings, and delivery is ok.

## Closed: merged, 2026-10-13T15:14:16Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 4a80ba00efb1df495ad45d65ef9dc897ab3fc190 into main and closed it as merged. Nobody answers a report after that.
