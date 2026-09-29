# Decision log: review-e2e

Goal: Fix the spec review findings of E2E and Dogfood scenarios

## Brief (main agent, 2026-09-30)

The developer asked for a spec review after `project-model-names` merged and said: fix the small
problems yourselves, and ask the developer only at the end about what needs their decision.

The unbound `spec_review` run `r-20260929T203136-spec_review-a3b63738` examined main at 14e573aa
and ended `changes_required`. Its result, with every finding's evidence and suggestion, is
`/home/zhenyu/concorde/.concorde/unbound/r-20260929T203136-spec_review-a3b63738/result.json`
(read-only for you); this task covers the findings of module.e2e, module.dogfood-scenarios.

### What to do

- Fix every finding of these Modules, blocking and advisory, except those named below as the
  developer's. Typical fixes: split a requirement that holds several obligations into atomic
  requirements, one SHALL each; split a scenario that mixes situations into scenarios of one
  situation each; correct examples, diagrams and wording that contradict the provider's Spec or the
  code. When a scenario identity changes, update the tests whose verification declarations name it.
  Keep what the Modules promise unchanged unless the finding shows the promise is wrong; when the
  code and the Spec disagree, decide which is right from the other Specs and the developer's earlier
  decisions, and record the decision here.
- Findings that say a provider's contracts were not supplied: check whether the Module's
  declarations omit that contract and add it if so; otherwise report it as a possible spec_review
  defect with evidence. Do not change module.spec-review.
- A finding you judge wrong: do not change the Spec; record why here and in your report.
- Anything else you find that needs the developer (it changes a promise's meaning, the design, or an
  earlier developer decision): leave it unchanged and report it with options and a recommendation.
  Do not escalate and stop: deliver the rest and put every such question in your final report.

### Specific to this task

For e2e f.1, define a bounded observation window after the run ends: an owner wake absent at its deadline becomes a named problem of a failed verdict, distinct from infrastructure timeouts (live_timeout); update code, diagram and tests to match.

### Process

Create what Git ignores (`uv sync --locked --group dev`, `npm --prefix docsite ci`, `build`). Format,
`build --check`, `spec-validation`, `registry --write` if a module block changes, the relevant tests
and once the full pytest suite on the final input. Then run `python3 scripts/concorde.py run
spec_review` once in the task worktree (bound; it reviews this task's Modules and updates their
review memory) and handle its findings the same way, without looping further. Then `task-validation`
and `delivery`, and report to the main agent with SendMessage: what you fixed, the findings you
judged wrong, and the open questions for the developer with options and recommendations.

## Task session (2026-09-30)

Fixes of the review `r-20260929T203136-spec_review-a3b63738`, every finding judged right:

- **e2e f.1 (owners case stopping rule).** As the brief asked: after the run writes its result,
  the case waits for the owner's wake and the end of its turn for at most `--wake` seconds (new
  option, default 180), then `--grace` seconds (unchanged, 20), and judges whether or not the owner
  was woken; an owner not woken is the problem `the owner <name> was not woken when its run ended`
  of a `failed` verdict. `live_timeout` stays for what keeps the case from observing (a prompted
  turn that never ends, no run in the run store, no result, within the 600 s limit). New
  `req.e2e.owners-deadline` (one SHALL; the verdict consequence refers to req.e2e.owners-case),
  diagram shows the bounded wait and the unowned run's direct path to the grace; code
  `scripts/e2e/owners.py` (`observe`, `WAKE_SECONDS`), `e2e.py owners --wake`; new test with a
  `claude` stand-in never notified. Chose 180 s as default because a real Claude Code
  notification of a finished background command arrives within seconds, and 180 s leaves ample
  margin while keeping a failed case short; the name `--wake` parallels `--grace`.
- **e2e f.2.** Split `scenario.e2e.worker-configuration` into `worker-model`,
  `copied-configuration` and `unmapped-model`; `stale-result` into `stale-result` and
  `newest-result`; `owners-case` into `owners-passed`, `owners-unwanted-wake`,
  `owners-too-few-sessions` and `owners-no-task`, plus the new `owner-not-woken` of f.1. The old
  identities are gone; tests split to verify one each. The copied-configuration test now points
  `CONCORDE_MODEL_MAP` at a map of its own, since the tests' map does not resolve this checkout's
  models (before, the old combined test never prepared without `--worker-model`).
- **e2e f.3.** `req.e2e.own-result` keeps only the result-selection SHALL; the `no_result` failure
  with its counts lives in `scenario.e2e.stale-result` and the module entry's prose.
- **e2e f.4.** The test-project definition in the module entry now includes "or another that
  `--any` admits", matching the glossary.
- **dogfood-scenarios f.1.** Split `worker-configuration` (success with `--worker-model fast`) from
  new `unmapped-model` (WHEN: the developer prepares with an unmapped model), and `untouched`
  (source and installed file changed) from new `caches-ignored`; tests split accordingly. Also
  fixed "Without it" in the dogfood entry, which after the model-map sentence read as the map, to
  "Without a worker configuration".
- Full suite on 80a7ea54: 795 passed, 4 skipped.
- Bound `spec_review` `r-20260929T205653-spec_review-90427697` (status ok, verdict
  `changes_required`; module.dogfood-scenarios `accepted`, module.e2e 1 blocking, 2 advisory):
  - e2e f.1 (blocking, right): `scenario.e2e.owner-not-woken` said the case ends at `--wake`,
    the entry at `--wake` + `--grace`. The scenario now gives `--wake 2 --grace 1` (as its test)
    and observes 3 seconds after the result before judging.
  - e2e f.2 (advisory, right about the Spec, not the code): `owners.py` already waits, holding the
    workspace lock, for the owner's launching turn to end before it waits for the run in the run
    store and releases the lock; the entry now says so and the diagram shows that step.
  - e2e f.3 (advisory) is about `specs/concorde/execution/module.md` ("The life of a run" says an
    observer of the result never finds the workspace busy, while "Workspaces" says a result on disk
    does not mean the lock is free). It belongs to module.execution, outside this task: left
    unchanged and reported to the main agent for a later task. Not looped further, per the brief.
- `task-validation` `r-20260929T210045-task_validation-770bd30c` ok (ready); `delivery`
  `r-20260929T210104-delivery-c2fd2b34` ok: delivery commit `2f2d6d3b` on `concorde/review-e2e`.

## Closed: merged, 2026-09-29T21:01:53Z
