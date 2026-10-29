# Decision log: views-protocol-contracts

Goal: Let module.views select, through Protocol 16.6 bound inclusions of module.spec's realization, the Protocol chapters its publisher parses by (protocol/format.md, protocol/views.md), resolving I-2314614b; and promise the scaffold command's outcomes in a table (contract v3) with a failed result naming destination and replaced files and one test per outcome, resolving I-1d73b6e0 as option A

## Task brief (main agent, 2026-10-29)

**Issues resolved.** Both are reopened leftovers of task r4-views. Read
`.concorde/decisions/r4-views.md`, escalations 1 and 2, around lines 132-187, and each Issue.

1. I-2314614b3406514a9c34cb6d39141a02 (module.views, high, preferred-fix): "Publisher parsing
   depends on unselected Protocol definitions".
   - Views parses Specs by `protocol/format.md` and `protocol/views.md`, but its context selects
     neither.
   - Task protocol-used-bound (merged 2026-10-29 as 3af09bf85, Protocol 16.6.0) now lets a `bound`
     inclusion name, read only, a file that a realization of a Module the declaring Module
     directly `uses` binds. module.spec binds `protocol/`.
   - Fix: add bound inclusions of both chapters, or the narrowest paths Views really depends on, to
     module.views. First confirm that module.views directly `uses` module.spec. If it does not,
     escalate before adding a `uses`, since that changes the Module graph.
   - State in Views' Spec which Protocol material governs the publisher's parsing.
   - If the Issue's checked-D2 syntax or glossary format live in other chapters, include those too,
     and record which.
2. I-1d73b6e0ab605372bf59986ac4443f00 (module.views, high, decision-needed): "Scaffold command
   responses lack operation-specific contracts". **Decided: option A** (main agent's answer in
   r4-views):
   - promise the current shapes in an outcome table, as contract v3;
   - give `failed` a result `{destination, replaced}`;
   - add one test per outcome.
   The outcomes the implementation already has:
   - propose returns `proposal` or `unchanged`;
   - apply returns `invalid`, `unchanged` `{identity, template_digest, github_pages}`, `conflict`
     `{conflicts: [paths]}`, `success` `{created, identity, template_digest, github_pages}`, or
     `failed`, which today has no result and names the destination and replaced files only in the
     finding message.
   The Spec already says that a failed result names them, so the code must change to match.

**What the main agent adds (its own decisions).**
- Keep to module.views. Leave its other open Issues out of this task.
- If option A's new `failed` result changes what another Module or the main-session guidance relies
  on, escalate first. A docsite command's caller may be one of them.
- Bump the contract version as the Protocol requires for a field change.

**Verification.**
- Views' own tests, including the TypeScript type check and the docsite checks.
- The full Python suite, `build --check` and `spec-validation`.
- Then `task-validation` and `delivery` from the task worktree.
- The docsite check now works with npm 11 (task checks-bwrap-compat), and d2 v0.9.0 is on PATH.

**Environment notes.**
- uv, node/npm (Node 24, npm 11), pi, rg, fd and d2 are under `/home/scratch.zbai_gpu/opt`.
- Keep large files off `$HOME` (5 GB quota).
- Prettier is in `docsite/node_modules` after `npm --prefix docsite ci`. Use it for TypeScript and
  JavaScript formatting.

**Left to the session.** The exact inclusions, the table's wording, the internal structure and
the tests. Escalate together anything beyond module.views or beyond these two decisions.

## Task session, 2026-10-28: I-2314614b (bound inclusions), commit 746fc5779

- module.views directly `uses` module.spec (`#uses-spec`), so no `uses` was added and no
  escalation was needed.
- Inclusions chosen: exactly `protocol/format.md` and `protocol/views.md`, as whole files (a
  bound inclusion cannot name less than a file). The Issue's metadata and glossary format and term
  links are in format.md (*Metadata*, *Glossary*, *Term links*, *Identities and anchors*,
  *Reading structure*); checked-D2 syntax and the publication obligations are in views.md. No
  other chapter was needed:
  - `protocol/model.md` also describes the glossary (*The glossary*, *concept* fields), but only
    restates format.md's entry fields, so it was left out.
  - `protocol/context.md` was left out: the publisher's recomputation of selecting Modules is
    restated in Views' pipeline.md and its equality with `selected-by` is relied on through
    `concept.impact-index`, which Views already relies on.
- Views' Spec (module.md, `#uses-spec`) now names both chapters and what each governs, and says
  which Protocol governs a publisher: the one of the Concorde it comes from; a scaffolded site
  keeps its scaffolding Concorde's publisher until a reviewed template update.
  `req.views.diagram-subset` now names views.md's *Checked diagrams* section.
- Chapters are named by path in code spans, as Spec core's contracts.md does, not linked: the
  Protocol is published as custom docs and a relative link into `protocol/` would not resolve on
  the site.
- Verified: `registry --write` regenerated module.views; `spec-validation` success (0 errors, the
  5 pre-existing style warnings in spec-tooling/spec/scenarios.md); `grant --type specify` and
  `review-spec` for module.views now hold both chapters at `ro` and no other Protocol file.

## Task session, 2026-10-28: I-1d73b6e0 (scaffold outcomes, option A)

- **No other Module relies on apply's result shape.** Searched src/, prompts/, specs/, scripts/,
  docs/ and docsite/: the only callers are Spec core's command dispatch (`spec/commands.py`) and
  user documentation that shows the commands without reading results. Distribution `relies_on`
  `contract.views.scaffold-proposal` only for the template inventory rule, which is unchanged, and
  does not `participates` in it; the main-session guidance never mentions the scaffold. So the new
  `failed` result needed no escalation and no reconciliation outside module.views.
- **Version.** `contract.views.scaffold-proposal` goes from 2 to 3 (fence, participation entry in
  module.md.json and the participation prose), since the Protocol requires an increment for a
  behaviour change and the section's prose, which now holds the outcome table, is part of the
  contract. `proposal_version` stays 2: the proposal value is unchanged, and bumping it would
  invalidate saved proposals for no reason.
- **Outcome table** (contracts.md, anchor `#scaffold-outcomes`): one row per outcome of propose and
  apply, with `status`, `result`, findings and `error`; the exit code follows Spec core's envelope
  mapping, and a malformed command line stays that envelope's `invalid_input` failure. It promises
  the existing shapes exactly (001, 002, 003, 008, 004 refusals; propose `proposal`/`unchanged`;
  apply `unchanged`, `conflict`, `success`) plus the result fields, the propose findings
  (007 per missing/outdated prerequisite, 009 without a GitHub origin) and `artifacts`.
- **`failed` now carries** `result: {destination, replaced}` and, as Spec core's envelope already
  requires for a command that could not do its work, the failure's error record as `error` (it was
  `null`). Its `CONCORDE-DOCSITE-006` finding now has the destination as `source` (was
  `docsite/site.json`) and takes its remediation from the error record (`propose again from the
  current files` for an appeared destination); its message no longer says "Staged promotion", a
  description of the earlier staging design.
- **Shape kept to the decided `{destination, replaced}`.** Created files whose removal the
  operating system refused are not a third result field: the error record already names each as a
  cause, and the contract now says so. Adding `unremoved` would go beyond the decided shape.
- **One more failure path covered.** `create_files` re-raised a path-check refusal (a directory on
  the way that became a link meanwhile) without cleanup facts, so a `failed` result could not
  name its destination there. It now raises the same `CreationError` with code `stale_proposal`
  and the refusal as cause, so every `failed` result has the promised fields.
- **Implementation:** `creation.CreationError(SpecError)` with `destination` and `replaced`;
  `apply_docsite` catches only it (other exceptions stay the CLI's `unexpected_error`).
- **Tests:** new `tests/concorde/views/test_scaffold_outcomes.py`, one test per table row (two for
  `failed`: an appeared destination with a replaced file, and an injected EIO), each running the
  CLI and checking status, exit code, result, artifacts, findings and error. New scenario
  `scenario.views.scaffold-outcomes`, verified by those tests; `scaffold-concurrent-create` now
  says the result names the destination and the replaced files. Exactly the two `failed` tests fail
  on the base code (10 pass, pinning the shapes that already existed). Added a creation-level test
  for the path-changed case and `destination`/`replaced` assertions to the replacement test.
- The contract's example of a `failed` apply was generated from a real run (paths shortened to
  `<project>` and `<random>`, as the text says).
- Pre-existing lint findings left alone (not part of the configured checks): PLW1510 in
  docsite_scaffold.py:239 and SIM117 nesting throughout test_scaffold_creation.py, whose idiom the
  new test follows.

## Report 1 to the main agent (项目中途停止状态检查), 2026-10-29T06:05:27Z

views-protocol-contracts delivered: delivery commit 7522e30983580aa16d08b064fabad848a2d70804 on concorde/views-protocol-contracts (delivery run r-20261029T055632-delivery-4cb64959, after task-validation r-20261029T054750-task_validation-0728ac50: ready, every configured check passed). No escalations.

Resolves, both already in the task's resolves (the merge closes them):
- I-2314614b (preferred-fix), commit 746fc5779. module.views directly uses module.spec, so no `uses` was added. Views now has two bound inclusions: protocol/format.md (metadata, glossary, identities and anchors, reading structure, term links) and protocol/views.md (checked-D2 subset, nodes and edges, publication obligations). No other chapter was needed. model.md only restates the glossary fields. The selection that context.md defines is restated in pipeline.md and relied on through concept.impact-index. Views' module.md (#uses-spec) names both chapters and which Protocol governs a publisher: the one of the Concorde it comes from. A scaffolded site keeps its scaffolding Concorde's publisher. req.views.diagram-subset now names views.md's Checked diagrams section. `grant` for specify and review-spec now holds both chapters at ro.
- I-1d73b6e0 (option A, as decided), commit e813bfaba. contract.views.scaffold-proposal is now version 3: the fence, the participation entry and the prose changed. proposal_version stays 2, because the proposal value is unchanged. contracts.md has an outcome table (#scaffold-outcomes): 11 rows giving status, result, findings and error for each outcome, with the result fields, artifacts and an example of a real failed envelope. A failed apply now returns result {destination, replaced} and the failure's error record. Its error was null before, although Spec core's envelope requires the record. Its CONCORDE-DOCSITE-006 finding's source is now the destination. There is a new scenario, scenario.views.scaffold-outcomes, and a new tests/concorde/views/test_scaffold_outcomes.py with one CLI test per row (two for failed). Only the two failed tests fail on the base.

My decisions (all in the decision log):
- No other Module relies on apply's result shape. Distribution relies on this contract only for the template inventory, which did not change, and the main-session guidance never mentions the scaffold. So the change needed no escalation.
- Files whose removal the OS refused are not a third result field. The error record already names each as a cause, and the contract says so. This keeps the decided {destination, replaced} shape.
- One gap is closed. A path-check refusal during creation (a directory that became a link meanwhile) was re-raised without cleanup facts. It is now the same failure, stale_proposal, with destination and replaced, so every failed result has the promised fields. A creation-level test covers it.

Verification: Views' three checks pass (69 Python tests, the TypeScript type check, 318 docsite repository tests). The full suite passes (1660 passed, 6 skipped). build --check passes. spec-validation passes with 0 errors and the 5 style warnings that were already in spec-tooling/spec/scenarios.md, outside Views. check-style on the Views Specs is clean.

Still open: nothing in this task. Two lint findings were already there before this task and are outside the configured checks, so I left them: PLW1510 at docsite_scaffold.py:239 and SIM117 nesting in test_scaffold_creation.py. The task branch is not pushed to any remote; it is ready for task merge.

## Closed: merged, 2026-10-29T06:06:08Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 7522e30983580aa16d08b064fabad848a2d70804 into main and closed it as merged. Nobody answers a report after that.
