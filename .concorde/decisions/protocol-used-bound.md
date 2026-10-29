# Decision log: protocol-used-bound

Goal: Change the Spec Protocol so a bound inclusion may also name, read only, a file that a realization of a Module the declaring Module uses binds, as the developer decided for Issue I-062abb6d; update Spec core's checks, Specs, the Protocol manifest and binding

## Task brief (main agent, 2026-10-29)

**Issue resolved.** I-062abb6dcd42543687e5487695e88d0a (module.spec, high, preferred-fix). Read it
first, then escalation 2 of `.concorde/decisions/r4-views.md` (around line 141).

**The developer's decision (2026-10-17, given in task r4-views).** Change the Spec Protocol now.
A `bound` inclusion may also name a file that a realization of a Module the declaring Module
`uses` binds, read only. Today `CHK.includes.bound` admits only the declaring Module's own
realization (Protocol 16.5, `protocol/relations.md`). So module.views cannot select
`protocol/format.md` and `protocol/views.md`, which module.spec binds, although its parser follows
them. `uses` and `relies_on` select only Spec documents, and `external` is refused by
`CHK.external.no-overlap`. The developer rejected restating the rules in a Spec document (option B)
and leaving the gap (option C).

**What the main agent adds (its own decisions).**
- Keep this task to the Protocol and Spec core:
  - the Protocol text;
  - `CHK.includes.bound` and whatever derives grants and context from bound inclusions;
  - module.spec's Specs;
  - the tests;
  - the Protocol manifest and the project's binding.
- Do not change module.views here. A later views task adds Views' inclusions of both chapters and
  resolves I-2314614b, together with I-1d73b6e0. So leave I-2314614b alone.
- Keep "read only" a real property. A file selected this way never enters any grant's `rw` list,
  for any task type, and a worker of the declaring Module never gets write access to the used
  Module's realization through it.
- Decide and record how the change shows in the Protocol's version and in context identity, and
  whether a used Module must be a direct `uses` or may be reached transitively. Prefer the
  narrowest rule that serves the Views case: direct `uses` only.
- After changing Protocol sources, run `python3 scripts/concorde.py build` and
  `python3 scripts/concorde.py protocol-manifest --write --bind-project` from the task worktree,
  as the concorde-development skill says.
- Note for parallel work: task shared-json-tmp (module.execution, module.workers) runs at the same
  time. It touches no Protocol or Spec-core file. Do not touch its Modules.

**Verification.** Add scenarios and tests showing:
- a bound inclusion of a used Module's realization file is accepted and read only;
- one of a Module not used is refused;
- the grant of every writing task type keeps that file out of `rw`.
Then run the full suite, `build --check` and `spec-validation`. Then run `task-validation` and
`delivery` from the task worktree.

**Environment notes.**
- uv, node/npm, pi, rg, fd and d2 are installed under `/home/scratch.zbai_gpu/opt`.
- Keep large files off `$HOME` (5 GB quota).
- Workers, if you use any, run on gpt-6.1-sol (pi) and claude-opus-5-5 (Claude Code).

**Left to the session.** The exact Protocol wording, the rule names, the internal structure and
the tests. Escalate together anything that would change another Module's promises, or a Protocol
point beyond the developer's decision.

## Task session, 2026-10-29: design decisions (taken without the developer)

Worktree prepared (init-references, uv sync, npm ci, build: all ok).

- **Direct `uses` only.** A bound inclusion may name a path at or below an entry of a
  realization of the declaring Module or of a Module it `uses` directly. Not transitively, and not
  through `contains`. Reasons: every selection in the Protocol is one level; the impact of a write
  to a file already concerns every Module that uses its binder, so a direct user is told when the
  text changes; a transitive rule would let a Module read text of a Module it declares no reliance
  on. This is the narrowest rule that serves Views (module.views uses module.spec).
- **Protocol 16.6.0 (minor).** The change only admits inclusions `CHK.includes.bound` refused
  before. Every Spec valid under 16.5 stays valid with the same contexts and grants. Same reasoning
  as the 16.5 precedent (task protocol-own-includes).
- **Context identity.** No new record shape and no new context record schema (stays 5). A file a
  used Module binds is recorded in `Bound(M)` like an own file: path, digest of its bytes, the
  inclusions that selected it. So a byte change of it changes M's context identity, and a context
  without such an inclusion keeps its identity. The bound record's `owner` becomes the Module whose
  realization binds the file: the queried Module when it binds it (every existing record, unchanged),
  otherwise the first by identity of the Modules it uses that bind it. This mirrors a source record,
  whose `owner` is the defining Module, never the selecting one.
- **Read only stays a property of the sets, not a special case.** Such a file lies in the used
  Module's `ImplementationScope`, never in the declaring Module's. A grant for the declaring Module
  alone therefore lists it at most `ro` for every task type; it becomes `rw` only for a task also
  bound to a Module that binds it, through that Module's own scope. Grant computation needs no new
  rule; tests pin it for every task type.
- **No plan_review.** The brief does not ask for it and the developer fixed the design; the change
  is Protocol text plus one selection function and one check.

## Task session, 2026-10-29: change committed and verified

Commit 942ae95ac on concorde/protocol-used-bound: Protocol 16.6.0, Spec core code, module.spec's
Specs, tests, manifest and project binding.
- Protocol manifest version: `protocol-manifest --write` keeps the tracked manifest's `version`,
  so I set `protocol/manifest.json` to 16.6.0 by hand, then ran build and
  `protocol-manifest --write --bind-project`; `.concorde/config.json` binds 16.6.0.
- Wording choices: the Protocol says a file that *only* a provider binds stays outside the
  declaring Module's write sets, since a file the consumer also binds is a shared file whose write
  the shared-file rule already governs.
- New scenario `scenario.spec.bound-inclusion-used`; `scenario.spec.bound-inclusion-invalid` now
  also refuses a file of a Module not used and of a Module used only transitively. The used-Module
  test fails on the base logic (owner/selection) and passes now.
- Other Modules' statements on bound inclusions (method/specification, e2e/cases, spec-mcp,
  prompts/workers/specify.md) stay true as written; nothing changed there. Views' reader only
  parses the kind, so module.views needs nothing for this task (its inclusions are the later task).
- Verification: build --check ok; spec-validation success (0 errors, 5 pre-existing style
  warnings in spec-tooling/spec/scenarios.md, none in changed text); check-style on protocol/ 0;
  full suite 1641 passed, 6 skipped (twice, the second on the committed input).

## Report 1 to the main agent (项目中途停止状态检查), 2026-10-29T03:59:22Z

protocol-used-bound delivered: delivery commit d576dfadd on concorde/protocol-used-bound (delivery run r-20261029T035019-delivery-024e9925). task-validation r-20261029T034111-task_validation-579cfdb2 was ready: 0 blocking findings, all 28 configured checks passed, and 5 style warnings that were already in spec-tooling/spec/scenarios.md, none in changed text. The change itself is commit 942ae95ac. It resolves I-062abb6d, which is already in the task's resolves.

What changed:
- Protocol 16.6.0. A bound inclusion may also name a path at or below an entry of a realization of a Module the declaring Module uses directly. files(M, p) now covers the realizations of M and of the Modules M uses. Such a file stays in the provider's ImplementationScope, so a task bound only to the declaring Module reads it and never writes it.
- Protocol chapters changed: CHK.includes.bound, relations, context, boundaries, format, module, model.yaml, README and principles, plus a new migration section 16.6.
- The manifest and the project binding are now 16.6.0. protocol-manifest --write keeps the tracked version, so I set protocol/manifest.json's version by hand, then ran build and protocol-manifest --write --bind-project.
- Spec core code: new bound_binders. bound_selection covers the Module and its direct providers, and CHK.includes.bound follows the same rule. A bound record's owner is the Module whose realization binds the file.
- module.spec Specs: req.spec.bound-inclusion and the contracts are updated. New scenario.spec.bound-inclusion-used. scenario.spec.bound-inclusion-invalid now also refuses a file of a Module that is not used, and one of a Module that is used only transitively.
- Tests: a used Module's file is ro in a grant for the declaring Module for all 8 task types. It is rw only in a grant also bound to its binder, through that binder's scope. The new test fails on the base logic.
- Verification: build --check ok. spec-validation: 0 errors. Full suite: 1641 passed, 6 skipped, run twice, the second time on the committed input.

Decisions I took without the developer (details in the decision log):
1. Direct uses only: not transitive, and not through contains. Selection is one level everywhere in the Protocol, and impact already concerns every user of a file's binder.
2. The version is 16.6.0, a minor change. Every 16.5 Spec stays valid with the same contexts and grants, as in the 16.5 precedent.
3. Context identity: the record shape and context record schema 5 are unchanged, so a context without such an inclusion keeps its identity. A used Module's file is digested like any bound file, so a byte change of it changes the declaring Module's identity.
4. A bound record's owner is the Module whose realization binds the file: the queried Module when it binds the file, otherwise the first used Module by identity that binds it. Every existing record keeps the same value.
5. Read only follows from the existing boundary sets, with no special case in grant computation. Tests check it for every task type.
6. I did not run plan_review: the brief did not ask for it, and the developer had fixed the design.

Still open (outside this task, as the brief said):
- module.views has not yet added bound inclusions of protocol/format.md and protocol/views.md, so I-2314614b and I-1d73b6e0 are not done. That is the later views task, which this change now makes possible.
- Other Modules' statements about bound inclusions stay true as written: method/specification, e2e/cases, spec-mcp and prompts/workers/specify.md.
- Nothing is escalated, and no decision of major impact is pending.

## Closed: merged, 2026-10-29T03:59:48Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit d576dfadd4a9a94135695daafae4b296328a311d into main and closed it as merged. Nobody answers a report after that.
