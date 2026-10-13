# Decision log: r3-e2e

Goal: Fix the remaining open Issues of E2E, Headless sessions, SWE-bench cases, Dogfood scenarios and Dogfooding (medium and low) found by the complete project_review

## Task brief (main agent, 2026-10-13)

Round 3. Rounds 1 and 2 fixed every critical and high Issue. The developer decided (2026-10-13)
that the main agent now resolves everything it can settle itself: this task resolves **every open
Issue owned by its Modules** (27, listed in `resolves`; 6 of them decision-needed), all medium or
low, found by project_review r-20261008T063808-project_review-9851e69f or reported since. Read each
with `concorde issues show`.

By tier:
- **decision-needed**: read them all first and escalate them **together in one report, early**,
  each with what you found, the options and your recommendation (say which options change a
  promise users rely on or an earlier developer decision). The main agent settles those within its
  authority and takes the rest to the developer in one batch. Continue with the rest meanwhile.
  An Issue the developer is asked about may stay open: you may deliver without it; the main agent
  reopens it after the merge if needed.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- **suggestion**: apply unless it is wrong or costs more than it is worth; then say why in the
  log and your report, and the main agent closes it as not-actionable.
- An Issue that no longer holds (many Modules changed in rounds 1-2), is a duplicate or is already
  fixed: say so with evidence; it stays in `resolves` and the merge closes it.
- Medium first, then low. A fix needing a change outside the task's Modules: escalate, unless it is
  a small mechanical follow-on (a link, a fixture, a registry refresh).

Eleven other round-3 tasks (r3-*) run in parallel on other Modules. Deliver with
`task-validation` then `delivery`; run the full suite once on the final input.

## Escalated to the main agent, 2026-10-13T11:34:31Z

- **task-session** task session (task r3-e2e): `model_turn_discriminator_undefined`
  I-7019df235e175088a9b29add90b54966 (Headless sessions, decision-needed, medium): the Spec's 'Reading the logs' says the round's result is the last result event 'with a model turn' without saying how stream-json shows it. scripts/e2e/sessions.py read_log already takes a result event whose num_turns is non-zero (truthy); a round with none has no result and the session's cost comes from the last round that had one.
  Not handled here (decision): The Issue is tiered decision-needed: choosing the discriminator fixes an observable contract of Headless sessions.
  Options: A: state Claude Code's stream-json result event field num_turns >= 1 as the discriminator, with the no-result outcome and a minimal replay-plus-answer scenario; matches the code (no promise users rely on changes); B: compare against the replayed turn's content (e.g. a result with an empty result text), a new rule needing code changes
  Recommendation: A

```json
{
  "level": "task-session",
  "actor": "task session (task r3-e2e)",
  "code": "model_turn_discriminator_undefined",
  "detail": "I-7019df235e175088a9b29add90b54966 (Headless sessions, decision-needed, medium): the Spec's 'Reading the logs' says the round's result is the last result event 'with a model turn' without saying how stream-json shows it. scripts/e2e/sessions.py read_log already takes a result event whose num_turns is non-zero (truthy); a round with none has no result and the session's cost comes from the last round that had one.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is tiered decision-needed: choosing the discriminator fixes an observable contract of Headless sessions."
  },
  "options": [
    "A: state Claude Code's stream-json result event field num_turns >= 1 as the discriminator, with the no-result outcome and a minimal replay-plus-answer scenario; matches the code (no promise users rely on changes)",
    "B: compare against the replayed turn's content (e.g. a result with an empty result text), a new rule needing code changes"
  ],
  "recommendation": "A",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:34:31Z

- **task-session** task session (task r3-e2e): `issue_system_exception_scope`
  I-a9045871b20d5a57bfb216401099e45c (Dogfooding, decision-needed, medium): Dogfooding's 'A defect of the Issue system' and req.dogfooding.issue-system-defect send every Concorde defect of the Issue system (a Concorde defect includes design limitations) as a bare error chain, never as a defect report. Issues says a design gap of Issues that the system can still record is an ordinary Issue. The developer's 2026-10-01 rule 'defects of the Issue system never go through Issues' was given for the deadlock of a failing system.
  Not handled here (decision): Narrowing the exception changes Dogfooding's written promise and touches the reading of an earlier developer decision.
  Options: A: narrow Dogfooding to failures of the Issue system (a crash, a wrong result, a refusal such as issues report --check refusing a correct report); a design limitation of Issues that the system can still record goes as an ordinary defect report, as Issues says. Changes Dogfooding's promise; keeps the developer's rule's reason (no deadlock); B: keep Dogfooding's broad exception and change Issues so that no report about Issues, even a recordable design gap, is an Issue (outside this task's Modules: module.issues)
  Recommendation: A

```json
{
  "level": "task-session",
  "actor": "task session (task r3-e2e)",
  "code": "issue_system_exception_scope",
  "detail": "I-a9045871b20d5a57bfb216401099e45c (Dogfooding, decision-needed, medium): Dogfooding's 'A defect of the Issue system' and req.dogfooding.issue-system-defect send every Concorde defect of the Issue system (a Concorde defect includes design limitations) as a bare error chain, never as a defect report. Issues says a design gap of Issues that the system can still record is an ordinary Issue. The developer's 2026-10-01 rule 'defects of the Issue system never go through Issues' was given for the deadlock of a failing system.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Narrowing the exception changes Dogfooding's written promise and touches the reading of an earlier developer decision."
  },
  "options": [
    "A: narrow Dogfooding to failures of the Issue system (a crash, a wrong result, a refusal such as issues report --check refusing a correct report); a design limitation of Issues that the system can still record goes as an ordinary defect report, as Issues says. Changes Dogfooding's promise; keeps the developer's rule's reason (no deadlock)",
    "B: keep Dogfooding's broad exception and change Issues so that no report about Issues, even a recordable design gap, is an Issue (outside this task's Modules: module.issues)"
  ],
  "recommendation": "A",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:34:31Z

- **task-session** task session (task r3-e2e): `observation_failure_outcome_undefined`
  I-e3994b6c334952859a42eabb22be0bf0 (Headless sessions, decision-needed, medium): the Spec gives no outcome when the driver cannot read or interpret what it observes. scripts/e2e/sessions.py today: an unreadable or invalid workspace binding silently falls back to the worktree's own .concorde; an unreadable progress file skips the run (it is never woken for); an unreadable result of a finished run counts as no result; a missing or unlockable run lock counts as runner gone (woken as ended without a result). Skipping can end the session idle with a run unobserved.
  Not handled here (decision): The Issue is tiered decision-needed: the outcome is a new observable promise of Headless sessions (session end codes and session.json).
  Options: A: fail visibly: a present but unreadable or invalid workspace binding refuses the session before its first round with binding_invalid; a run folder whose progress file, or a finished run whose result, cannot be read or interpreted, read again once, ends the session with observation_failed, session.json written first naming the file (as wait_exceeded does); a missing run lock stays 'runner gone'. Adds scenarios.; B: specify today's lenient behaviour as the promise (fallback to own .concorde, skip unreadable runs, treat an unreadable result as none)
  Recommendation: A

```json
{
  "level": "task-session",
  "actor": "task session (task r3-e2e)",
  "code": "observation_failure_outcome_undefined",
  "detail": "I-e3994b6c334952859a42eabb22be0bf0 (Headless sessions, decision-needed, medium): the Spec gives no outcome when the driver cannot read or interpret what it observes. scripts/e2e/sessions.py today: an unreadable or invalid workspace binding silently falls back to the worktree's own .concorde; an unreadable progress file skips the run (it is never woken for); an unreadable result of a finished run counts as no result; a missing or unlockable run lock counts as runner gone (woken as ended without a result). Skipping can end the session idle with a run unobserved.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is tiered decision-needed: the outcome is a new observable promise of Headless sessions (session end codes and session.json)."
  },
  "options": [
    "A: fail visibly: a present but unreadable or invalid workspace binding refuses the session before its first round with binding_invalid; a run folder whose progress file, or a finished run whose result, cannot be read or interpreted, read again once, ends the session with observation_failed, session.json written first naming the file (as wait_exceeded does); a missing run lock stays 'runner gone'. Adds scenarios.",
    "B: specify today's lenient behaviour as the promise (fallback to own .concorde, skip unreadable runs, treat an unreadable result as none)"
  ],
  "recommendation": "A",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-13T11:35:05Z

r3-e2e, early report: the decision-needed Issues (6).

Three no longer hold (fixed by round 2, commit 1bcce36d9 and after, later than the review's head ce20cc748); they stay in resolves:
- I-9ec3c01947ed5c86b0ad7a4877c92be7 and I-d15ee6597eb6506db18f39eab1e476b1 (owners deadlines, duplicates): specs/concorde/e2e/module.md now waits for the result at most the run's wait, 1200 s, after the release ("a refusal for a busy workspace always arrives before the case's deadline"); live_timeout's third case says the same; scripts/e2e/owners.py waits queue_wait(limit); tests/concorde/e2e/test_owners.py test_a_refusal_after_the_cases_limit_is_still_seen uses a stand-in refused 4 s after taking the lock with limit 3 s.
- I-ab6e4af1b1ae5feabcdf74c3a3d8f642 (non-object worker configuration): module.md now refuses a configuration that "cannot be read as a JSON object" with worker_configuration_unreadable and gives config_invalid only to "a JSON object its contract does not admit", matching scenario.e2e.configuration-unreadable.

Three need your decision (escalations 1-3; I continue with the 21 others meanwhile):

1. I-7019df235e175088a9b29add90b54966 model_turn_discriminator_undefined: how "a result event with a model turn" is recognized. A: num_turns >= 1 (what the code does; no promise users rely on changes). B: a content-based rule. Recommendation A.

2. I-a9045871b20d5a57bfb216401099e45c issue_system_exception_scope: Dogfooding sends every Issue-system defect, design limitations included, as a bare error chain; Issues says a recordable design gap of Issues is an ordinary Issue. A: narrow Dogfooding to failures (crash, wrong result, wrong refusal); a recordable design limitation of Issues goes as an ordinary defect report. Changes Dogfooding's written promise and reads the developer's 2026-10-01 rule ("Issue-system defects never go through Issues") by its stated reason, the deadlock. B: keep Dogfooding broad and change Issues (module.issues, outside this task). Recommendation A.

3. I-e3994b6c334952859a42eabb22be0bf0 observation_failure_outcome_undefined: no outcome when the session driver cannot read what it observes; today it silently falls back (invalid binding), skips the run (unreadable progress file) or treats the result as missing. A: fail visibly: binding_invalid before the first round for a present but invalid binding; observation_failed (session.json written first, naming the file, after one re-read) for an unreadable progress file or a finished run's unreadable result; a missing run lock stays "runner gone". New promise of Headless sessions (test tooling only, no user-facing change). B: specify today's lenient behaviour. Recommendation A.

It carries escalation(s) 1, 2, 3.

## Answer to report(s) 1 of the task session, 2026-10-13T11:35:35Z

Escalations (main agent): 1 A — a model turn is num_turns >= 1. 3 A — fail visibly: binding_invalid before the first round for a present but invalid binding; observation_failed (session.json written first, naming the file, after one re-read) for an unreadable progress file or a finished run's unreadable result; a missing run lock stays runner gone. Escalation 2 (I-a9045871, scope of the Issue-system exception) reinterprets the developer's 2026-10-01 rule: the main agent takes it to the developer in one batch with other round-3 decisions. Do not change it; deliver the rest without it. It stays in resolves; the main agent reopens it after the merge if needed. The three Issues that no longer hold: fine, the merge closes them.

## Task session decisions, 2026-10-13

Issues that no longer hold (fixed by round 2, after the review's head ce20cc748); left in resolves:
- I-9ec3c019, I-d15ee659 (owners deadlines): result wait is the run's 1200 s wait after the release (spec, owners.py queue_wait, test_a_refusal_after_the_cases_limit_is_still_seen).
- I-ab6e4af1 (non-object worker configuration): module.md classifies "cannot be read as a JSON object" as worker_configuration_unreadable.
- I-3979db33 (cases' grading reference): cases/module.md.json already includes references/swe-bench/swebench/harness/ and docs/guides/datasets.md (commit a528a485d).
- I-376ed872 (split E2E scenarios): runtime-failures is already split into command-not-started, task-unreadable, configuration-unreadable and unexpected-failure; outside-root is its own scenario.

Decided by the main agent: I-7019 A (num_turns >= 1), I-e3994 A (binding_invalid, observation_failed). I-a9045871 left unchanged for the developer.

Fixes chosen (preferred-fix and suggestions), each because it is the Issue's suggested repair unless said:
- I-36148013: compare start times as parsed instants (datetime.fromisoformat) and stamp the session to the microsecond; rejected text normalisation, which would still break on another precision.
- I-d5c7aa3e: list the lobby before the workspace folders, re-resolve a listed run whose folder moved, count each run id once.
- I-c838fdb7: the last allowed round still waits for its runs (so the project is settled) but records them under left_behind, never woke_for; new requirement left-behind-not-woken.
- I-e3994b6c: re-read once after REREAD_SECONDS = 1 s (a run folder exists a moment before its first status.json); a progress file with an unreadable started_at is also observation_failed; a missing run lock stays runner_gone.
- I-16f2583d: live sessions are an internal Python class for E2E components; documented the LiveSession interaction rather than adding a command.
- I-530597d5: paths from `git apply --numstat -z` plus the header's `---`/rename/copy sources (unquoted), parsed only between `diff --git` and the first `@@`; numstat alone omits rename sources.
- I-68e7348b: worktree creation inside the cleanup; removal, prune and a check of registration and scratch directory; new error cleanup_failed naming what is left and any earlier grading error (evidence `cause`). New requirement cleanup-checked and patched-files-reset.
- I-fd390135: new owned implementation document specs/concorde/e2e/cases/contracts.md with contract.swe-bench-cases.case and .verdict and the error codes; the statuses and verdict rules stay readable in the entry, which links the contracts (moving them was churn without benefit).
- I-07c50195: added uses module.execution (concept.run-result, contract.execution.run-result); Tasks, Validation and Delivery were declared in round 2; Distribution limited to routing.
- I-fa909bfc: specs-not-code is now the sole prohibition "SHALL NOT change the project's code".
- I-09adbd0c: only merge_busy is waited out; every other environment refusal is handled by its options as the Issues guidance says, or escalated; changed the entry, a new requirement, the scenario, prompts/dogfooding/skill.md and its test.
- I-14fc88c4: install prose, overview diagram, update text and install/update scenarios conditioned on the coordination, issues and spec parts; the partial-install scenario lost its alternate selection, which the develop-install scenario covers.
- I-fb3927b0 (suggestion, applied): new owned implementation document specs/concorde/e2e/mechanics.md holds the owners lock/launch mechanics and run's result counting; the entry keeps behaviour, limits and reasons.
- I-2b4befaf, I-36611260, I-41c4efa6, I-b0159776, I-b9881806 (suggestions, applied as suggested).

## Report 2 to the main agent (Review流程), 2026-10-13T12:16:27Z

r3-e2e delivered: delivery commit f768f374756c161b5ebc658e18c2043ae7d5a24c on concorde/r3-e2e (run r-20261013T120558-delivery-dfed79d9). task-validation was ready with no blocking findings. The full suite passed on the final input: 1482 passed, 5 skipped. spec-validation, registry --check and build --check succeed.

All 27 Issues stay in resolves:
- Fixed (21): I-7019 and I-e3994 (your answers: A and A), I-36148013, I-d5c7aa3e, I-c838fdb7, I-8e73eb55, I-4c46a985, I-16f2583d, I-36611260, I-b9881806 (Headless sessions); I-530597d5, I-68e7348b, I-fd390135, I-07c50195, I-fa909bfc, I-b0159776 (SWE-bench cases); I-09adbd0c, I-14fc88c4, I-2b4befaf, I-41c4efa6 (Dogfooding); I-fb3927b0 (E2E).
- No longer hold (5): I-9ec3c019, I-d15ee659 and I-ab6e4af1, as in report 1. I-3979db33: the cases metadata already includes the pinned SWE-bench harness and dataset guide (a528a485d). I-376ed872: the runtime-failures scenario is already split into four, and outside-root is its own scenario.
- Not changed (1): I-a9045871, which you are taking to the developer. Reopen it after the merge if the developer wants a change.

Choices I made (the full list is in the decision log):
- Session start times are compared as parsed instants, not as text.
- The lobby is listed first, and a run that has moved is looked up again.
- The last allowed round records its runs under left_behind and never as woke_for.
- An unreadable file is re-read once after 1 s before the session fails.
- LiveSession is documented as an internal class, not a command.
- Patch paths come from git apply --numstat -z plus the header's rename and copy sources. Paths are read only from headers.
- A grading worktree that cannot be removed fails with the new error cleanup_failed, which names any earlier grading error.
- New Spec documents: specs/concorde/e2e/cases/contracts.md (the case, the verdict and the errors) and specs/concorde/e2e/mechanics.md (the owners-case lock mechanics and how run picks its result).
- The develop guidance now waits out only merge_busy. Every other environment refusal is handled through its options, or escalated.

New observable error codes, all in E2E test tooling only: binding_invalid and observation_failed (headless sessions), and cleanup_failed (grade).

Nothing else is open.

## Closed: merged, 2026-10-13T14:45:57Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit f768f374756c161b5ebc658e18c2043ae7d5a24c into main and closed it as merged. Nobody answers a report after that.
