# Decision log: r4-views

Goal: Fix the critical and high open Issues of Views found by the fourth project_review, the critical first (I-41581ddb I-cefc9d12 I-e8ac09f9)

## Task brief (main agent, 2026-10-17)

Round 4. The fourth project_review (r-20261013T165054-project_review-b4db00b2, unbound; reports
under `.concorde/unbound/r-20261013T165054-project_review-b4db00b2/` of the primary worktree) left
734 open Issues after rounds 1-3 had brought them to 4: most new findings are stricter standards
rather than new defects. The developer decided (2026-10-17): **each round fixes only critical and
high Issues**, medium and low wait until real use runs into them, and project_review is tuned so
its Issues stay actionable (task r4-review-tuning). This task resolves the critical and high Issues
of its Modules listed in `resolves`. Read each with `concorde issues show`. Other open Issues of
these Modules are out of scope: do not fix them unless a fix in scope needs it.

By tier: **decision-needed** — read them first and escalate them all together in one report,
early, each with what you found, the options and your recommendation, saying which options change
a promise users rely on or an earlier developer decision; continue with the rest meanwhile.
**preferred-fix** — fix as you judge best and report the choice. **obvious-fix** — fix. Critical
first. An Issue that no longer holds or is a duplicate: say so with evidence; it stays in
`resolves`. A fix needing a change outside the task's Modules: escalate unless it is a small
mechanical follow-on. Eight other round-4 tasks (r4-*) run in parallel on other Modules. Deliver
with `task-validation` then `delivery`; run the full suite once on the final input.

## Task session decisions (2026-10-17)

All three Issues in scope are critical `preferred-fix`; none is `decision-needed`, so nothing was
escalated. Fixed in commit 6be88a31a.

- **I-41581ddb (build deletes candidate before admission).** Chosen fix: `buildSite` runs
  `preparePublication` (which loads and admits every source) before its first `rm(candidate)` and
  outside the `try` whose handler deletes the candidate. Reason: the smallest reordering that makes
  admission precede every cleanup; the alternative of passing a preloaded registry into
  `preparePublication` would load twice for no gain. Consequence recorded in pipeline.md
  "Promotion": a failure of the configuration check or of staging deletes nothing.
- **I-cefc9d12 (nested staging symlinks).** Chosen fix: a new `PUBLICATION_CLEARED` list in
  `staging.ts` names every path below the outputs that publication clears, renames or writes by
  name (each mode's staging directory with `content/`, `scoped-materialization.json`,
  `specs-sidebar.json`; the production generated directory; the candidate; the backup).
  `requireDisjointOutputs` refuses a symbolic link at any of them or at any directory between it
  and its output. Reason: the Issue's preferred repair (refuse symlinked staging ancestors); refusing
  is simpler and safer than resolving them. `specs-sidebar.json` was added because `writeFile`
  follows a link there and would overwrite its target. The candidate, backup and production
  generated directory names moved into `staging.ts` so model.ts can name them without importing
  the scripts (`prepare-publication.ts` still exports `productionGeneratedDirectory`).
- **I-e8ac09f9 (authored docs unprotected).** Chosen fix: loading parses the site identity and
  protects, beside the registered sources, the user documents directory, each custom docs
  directory and sidebar file, and each docs plugin directory and sidebar file of
  `custom-docs/index.ts`. Loading therefore now loads `custom-docs/index.ts` (factored into
  `loadExtension` in custom-docs.ts) and fails on an invalid site identity, both stated in
  pipeline.md. Reason: the Issue asks for all authored publication inputs; extension docs plugins
  are custom docs too and are cleared by the same staging. Only "inside an output" is refused, not
  an output inside an authored directory, since cleanup then deletes only generated files.
- Spec changes within module.views: pipeline.md (loading-and-admission sources and symlink rule,
  Promotion order), requirements.md (req.views.outputs-disjoint now names the symlink rule for
  cleared paths and the authored documentation), scenarios.md (scenario.views.outputs-disjoint).
- Formatting: `build.ts` and `prepare-publication.ts` were not Prettier-formatted at the base, so
  they keep their own style rather than being reformatted whole; every other changed file passes
  `prettier --check`.
- 14 new regression tests (publication-outputs.test.ts, refused-builds.test.ts); all 14 fail on
  the base implementation and pass with the fix.
- Non-ok result: a first full vitest run failed `tests/repository/production-build.test.ts` with
  "Spec source changed during publication", because I edited Specs while it built the real
  checkout. Not a defect; the re-run on the committed input is the one that counts.

## Escalated to the main agent, 2026-10-17T04:45:10Z

- **task-session** task session (task r4-views): `scaffold_response_contract_undefined`
  I-1d73b6e0 (high, decision-needed): contracts.md 'Scaffold proposal' defines result.proposal/prerequisites for propose but not propose's status nor apply's per-outcome payloads. The implementation (src/concorde/spec/views/docsite_scaffold.py:380-390, 615-680) already has a stable shape: propose -> status 'proposal' or 'unchanged' (artifacts = all paths), result {proposal, prerequisites}; apply -> 'invalid' (CONCORDE-DOCSITE-001/004, error = Spec tooling error record), 'unchanged' (artifacts = paths, result {identity, template_digest, github_pages}), 'conflict' (one CONCORDE-DOCSITE-005 finding per existing path, result {conflicts: [paths]}), 'success' (artifacts = created, result {created, identity, template_digest, github_pages}), 'failed' (one CONCORDE-DOCSITE-006 finding, no result; the appeared/failed destination and replaced files are only in the finding message, whereas the Spec says the failed result names them).
  Not handled here (decision): Writing these payloads down creates new public promises of the docsite command (the Issue's tier is decision-needed), and option A also changes the failed outcome's shape.
  Options: A: Promise the current shapes in an outcome table (contract version 3), and give 'failed' a result {destination, replaced: [paths]} so it names what the Spec already says it names; add a test per outcome; B: Promise exactly the current shapes, failed included (names only in the finding message), and change the Spec sentence about what 'failed' names; C: Leave the contract as it is and close the Issue as not-actionable (consumers read artifacts and findings only)
  Recommendation: A: it documents what callers already get and makes 'failed' carry what the Spec already promises; all within module.views; no other Module's promise changes

```json
{
  "level": "task-session",
  "actor": "task session (task r4-views)",
  "code": "scaffold_response_contract_undefined",
  "detail": "I-1d73b6e0 (high, decision-needed): contracts.md 'Scaffold proposal' defines result.proposal/prerequisites for propose but not propose's status nor apply's per-outcome payloads. The implementation (src/concorde/spec/views/docsite_scaffold.py:380-390, 615-680) already has a stable shape: propose -> status 'proposal' or 'unchanged' (artifacts = all paths), result {proposal, prerequisites}; apply -> 'invalid' (CONCORDE-DOCSITE-001/004, error = Spec tooling error record), 'unchanged' (artifacts = paths, result {identity, template_digest, github_pages}), 'conflict' (one CONCORDE-DOCSITE-005 finding per existing path, result {conflicts: [paths]}), 'success' (artifacts = created, result {created, identity, template_digest, github_pages}), 'failed' (one CONCORDE-DOCSITE-006 finding, no result; the appeared/failed destination and replaced files are only in the finding message, whereas the Spec says the failed result names them).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Writing these payloads down creates new public promises of the docsite command (the Issue's tier is decision-needed), and option A also changes the failed outcome's shape."
  },
  "options": [
    "A: Promise the current shapes in an outcome table (contract version 3), and give 'failed' a result {destination, replaced: [paths]} so it names what the Spec already says it names; add a test per outcome",
    "B: Promise exactly the current shapes, failed included (names only in the finding message), and change the Spec sentence about what 'failed' names",
    "C: Leave the contract as it is and close the Issue as not-actionable (consumers read artifacts and findings only)"
  ],
  "recommendation": "A: it documents what callers already get and makes 'failed' carry what the Spec already promises; all within module.views; no other Module's promise changes",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-17T04:45:21Z

- **task-session** task session (task r4-views): `protocol_text_unselectable`
  I-2314614b (high, preferred-fix): Views' publisher parses metadata, glossary, reading syntax and checked D2 by the Protocol's rules (req.views.diagram-subset: 'The semantic subset is the Protocol's'), but Views' context selects none of protocol/format.md or protocol/views.md. Spec core selects them for itself with 'bound' inclusions (specs/concorde/spec-tooling/spec/module.md.json:47-70), but CHK.includes.bound (protocol/checks.md:73) allows a bound inclusion only at or below the declaring Module's own realization, and protocol/ is realized by module.spec (realization.spec.protocol-text). 'uses' with relies_on selects only Spec documents, never another Module's bound text; 'external' is refused by CHK.external.no-overlap because protocol/ is a realization entry. So no change inside module.views can select the canonical text: the Issue's preferred fix needs a Protocol or Spec-core change. This looks like a Concorde design limitation (the Specs are right, the Protocol cannot express the selection).
  Not handled here (decision): Every fix changes the Protocol or module.spec, both outside this task's Modules, and a Protocol change is the developer's.
  Options: A: Protocol change (Spec-core task): let a Module's bound inclusion also name a file that a realization of a Module it uses binds, read only; then Views adds bound inclusions of protocol/format.md and protocol/views.md; B: Spec core restates the publisher-relevant format and checked-D2 rules in a registered Spec document that Views selects through uses/relies_on (duplicates Protocol text, which Spec core's contracts deliberately avoid); C: Accept the gap for now: Views states which Protocol version governs its parser (the version the project binds) and links the chapters; keep the Issue open, out of this task's resolves, until real use needs it
  Recommendation: C for this round (the fix is not a defect of Views' behaviour and the developer limited rounds to fixing defects), with A recorded as the general repair for a later Spec-core/Protocol task. I can do C's Views-side sentence here; the Issue must then leave r4-views' resolves so the merge does not close it.

```json
{
  "level": "task-session",
  "actor": "task session (task r4-views)",
  "code": "protocol_text_unselectable",
  "detail": "I-2314614b (high, preferred-fix): Views' publisher parses metadata, glossary, reading syntax and checked D2 by the Protocol's rules (req.views.diagram-subset: 'The semantic subset is the Protocol's'), but Views' context selects none of protocol/format.md or protocol/views.md. Spec core selects them for itself with 'bound' inclusions (specs/concorde/spec-tooling/spec/module.md.json:47-70), but CHK.includes.bound (protocol/checks.md:73) allows a bound inclusion only at or below the declaring Module's own realization, and protocol/ is realized by module.spec (realization.spec.protocol-text). 'uses' with relies_on selects only Spec documents, never another Module's bound text; 'external' is refused by CHK.external.no-overlap because protocol/ is a realization entry. So no change inside module.views can select the canonical text: the Issue's preferred fix needs a Protocol or Spec-core change. This looks like a Concorde design limitation (the Specs are right, the Protocol cannot express the selection).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Every fix changes the Protocol or module.spec, both outside this task's Modules, and a Protocol change is the developer's."
  },
  "options": [
    "A: Protocol change (Spec-core task): let a Module's bound inclusion also name a file that a realization of a Module it uses binds, read only; then Views adds bound inclusions of protocol/format.md and protocol/views.md",
    "B: Spec core restates the publisher-relevant format and checked-D2 rules in a registered Spec document that Views selects through uses/relies_on (duplicates Protocol text, which Spec core's contracts deliberately avoid)",
    "C: Accept the gap for now: Views states which Protocol version governs its parser (the version the project binds) and links the chapters; keep the Issue open, out of this task's resolves, until real use needs it"
  ],
  "recommendation": "C for this round (the fix is not a defect of Views' behaviour and the developer limited rounds to fixing defects), with A recorded as the general repair for a later Spec-core/Protocol task. I can do C's Views-side sentence here; the Issue must then leave r4-views' resolves so the merge does not close it.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-17T04:45:37Z

r4-views early escalations (2). Work continues meanwhile on the rest of the task.

Status: the three critical Issues (I-41581ddb, I-cefc9d12, I-e8ac09f9, all preferred-fix) are fixed in commit 6be88a31a, with 14 new regression tests that all fail on the base. Choices are in the decision log. Next: the four non-decision highs. I-b8ea1f0e is the Spec side of I-41581ddb and is already fixed by the Promotion reorder. I-bf27355a and I-317c9fdb are duplicates: the Spec text omits the glossary field, which the code already accepts. I-29fae188 is about docs plugins given as resolved paths or imported functions.

Escalation 1, I-1d73b6e0 (high, decision-needed), scaffold response contracts:
- **task-session** task session (task r4-views): `scaffold_response_contract_undefined`
  contracts.md promises propose's result.proposal and result.prerequisites. It does not promise propose's status or apply's payload for each outcome. The implementation already has stable shapes: propose returns proposal or unchanged; apply returns invalid, unchanged {identity, template_digest, github_pages}, conflict {conflicts: [paths]}, success {created, identity, template_digest, github_pages}, or failed with no result. A failed apply names the destination and replaced files only in the finding message, but the Spec says the failed result names them.
  Options:
  A. Promise the current shapes in an outcome table (contract v3), give failed a result {destination, replaced}, and add one test per outcome.
  B. Promise exactly the current shapes, and change the Spec sentence about failed.
  C. Leave the contract as it is and close the Issue as not-actionable.
  Recommendation: A. Everything stays within module.views, and no promise of another Module changes. A and B both add public promises of the docsite command, and A also changes the failed outcome's shape.

Escalation 2, I-2314614b (high, preferred-fix, but its fix lies outside Views): the Protocol text is not selectable.
- **task-session** task session (task r4-views): `protocol_text_unselectable`
  Views parses by the rules in protocol/format.md and protocol/views.md, but its context selects neither chapter. Spec core selects them with `bound` inclusions. CHK.includes.bound allows a bound inclusion only of the declaring Module's own realization, and protocol/ is module.spec's. `uses` and `relies_on` select only Spec documents. `external` is refused by CHK.external.no-overlap. So nothing inside module.views can select the text. This looks like a Concorde design limitation.
  Options:
  A. A Protocol change in a Spec-core task: let a bound inclusion name a file that a realization of a used Module binds, read only. Views then includes both chapters.
  B. Spec core restates these rules in a registered Spec document. This duplicates Protocol text.
  C. Accept the gap this round. Views says which Protocol version governs its parser. The Issue stays open and leaves r4-views' resolves, so the merge does not close it.
  Recommendation: C now, with A recorded for a later Spec-core/Protocol task. A is a Protocol change and needs the developer.

Please answer both. Neither blocks the rest of the task. If C is chosen for escalation 2, please remove I-2314614b from the task's resolves, or tell me how you want it handled.

It carries escalation(s) 1, 2.

## Task session decisions, the six high Issues (2026-10-17)

The task's `resolves` holds six high Issues besides the three critical ones of the goal. The brief
puts every critical and high Issue in `resolves` in scope, so I handled them too:

- **I-1d73b6e0** (decision-needed): escalated (escalation 1); report 1.
- **I-2314614b** (preferred-fix, but it cannot be fixed within module.views): `CHK.includes.bound`
  allows a bound inclusion only of the declaring Module's own realization, and protocol/ is
  module.spec's. Escalated (escalation 2); report 1.
- **I-b8ea1f0e**: the Spec side of I-41581ddb. pipeline.md "Promotion" was already reordered in
  6be88a31a, with failure cleanup only after admission. In cb3f0d6f1, scenario.views.build-site
  now states that order, and build-failures.test.ts asserts that prepare comes before the first
  rm and that a failed preparation deletes nothing.
- **I-bf27355a and I-317c9fdb** (obvious-fix, duplicates): the code already accepted `glossary`
  (model.ts REQUIRED_RECORD_FIELDS + "glossary"). Only pipeline.md's closed field list was wrong.
  It now allows `glossary` as Spec core's registry-file contract does, and links that contract.
- **I-29fae188** (preferred-fix): chosen fix is identity resolution. A docs plugin is recognized by
  one of the three names, by a module path that resolves (from the site directory, else from the
  publisher) to the same real file as `@docusaurus/plugin-content-docs`, or by being that module or
  its `default` function. Rejected alternative: refusing every unrecognized plugin, which would
  break legitimate non-docs plugins. A wrapper function that calls the docs plugin is still not
  recognized; Docusaurus gives no way to detect it. The same recognition feeds the authored-input
  protection of I-e8ac09f9. Tests: refused-builds.test.ts covers the name, the resolved path and
  the imported function; 2 of the 3 fail on 6be88a31a.

## Main agent, 2026-10-23: deliver what is done

The developer is ending development on this machine. Stop new work; deliver what is committed
(the three criticals and the highs already fixed). Answers: escalation 1 (I-1d73b6e0) — option A
is the main agent's answer, but do not start it now. Escalation 2 (I-2314614b) — the developer
chose to change the Protocol (let a bound inclusion name files a used Module's realization binds);
that is a separate Spec-core task on the next machine, not this task. Before delivering, list in
your report every Issue of this task's resolves you did not fix; the main agent reopens them after
the merge. Validate and deliver now.

## Task session, 2026-10-23: final verification before delivery

Following the main agent's answer, no new work: I deliver the committed state (cb3f0d6f1).
- `build --check` ok; `spec-validation` success (0 errors, 5 style warnings, all in
  spec-tooling/spec/scenarios.md, outside module.views).
- Non-ok result: the first full suite (`pytest -x`) failed one test,
  tests/concorde/tracing/test_locks.py::LockLineTests::test_the_lock_table_names_this_process_as_holder,
  with `LockTableUnsettled` (/proc/locks kept changing for 1 s while 16 xdist workers and other
  worktrees took locks). It is outside module.views and timing-dependent. The re-run of the whole
  suite on the same input passed: 1591 passed, 6 skipped.
- Not fixed, still in `resolves` (the main agent reopens them after the merge):
  I-1d73b6e0 (escalation 1, answered option A, deferred) and I-2314614b (escalation 2, a
  separate Protocol/Spec-core task).

## Report 2 to the main agent (Review流程), 2026-10-23T09:24:36Z

r4-views delivered: delivery commit fbc63f624 on concorde/r4-views (delivery run r-20261023T091434-delivery-177a03ec, task-validation r-20261023T090424-task_validation-9be5ddfa ready with no blocking findings).

Fixed (commits 6be88a31a, cb3f0d6f1):
- I-41581ddb (critical, preferred-fix): buildSite admits every source before its first cleanup.
- I-cefc9d12 (critical, preferred-fix): publication refuses a symlink at, or above, any path it clears or writes.
- I-e8ac09f9 (critical, preferred-fix): user documents, custom docs and docs-plugin directories and sidebars are protected.
- I-b8ea1f0e (high): Spec side of I-41581ddb; the Promotion order is stated and tested.
- I-bf27355a and I-317c9fdb (high, duplicates): pipeline.md now allows the registry's glossary field, which the code already accepted.
- I-29fae188 (high, preferred-fix): a docs plugin is recognized by its name, by a resolved module path, or by being the imported function. A wrapper function is still not recognized.
My choices and their reasons are in the decision log.

Not fixed, still in resolves. Please reopen these after the merge:
- I-1d73b6e0: your answer was option A, deferred.
- I-2314614b: the developer chose the Protocol change, which is a separate Spec-core task.

Verification:
- build --check passed.
- spec-validation: 0 errors and 5 style warnings, all outside module.views.
- Full pytest suite: 1591 passed, 6 skipped.
- Non-ok: the first suite run failed once with tests/concorde/tracing/test_locks.py LockTableUnsettled. This is timing-dependent and outside Views; the whole-suite re-run on the same input passed.

Nothing else is open.

## Closed: merged, 2026-10-23T09:24:52Z

The merge answered report(s) 1, 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit fbc63f624603d8afbf0fabb1105ef6ada879cb2e into main and closed it as merged. Nobody answers a report after that.
