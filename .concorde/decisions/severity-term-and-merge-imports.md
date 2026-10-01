# Decision log: severity-term-and-merge-imports

Goal: Stop the Spec Protocol using 'severity' for anything but Issue severity (rename the blocking/advisory 'Severity' of evaluation.md and the error/warning 'severity' of structural checks), and make task merge finish its post-merge steps even when the merged change alters Concorde modules it imports

## Brief (main agent, 2026-10-01)

This task resolves two Issues, both handled by this task session.

### 1. I-d24569b23b345cd3b8e89ae8b3944c17 — "severity" clash (module.spec, decision-needed)

Task issue-severity (merged at bc91d859) made `concept.issue-severity` (critical, high, medium,
low) a glossary term. The developer decided: **the Protocol changes its word**, so that "severity"
means only Issue severity. The main agent decided, to keep one word for one meaning, that this
covers both Protocol uses:

- `protocol/evaluation.md`'s section "Severity" (blocking/advisory, "Severity measures the
  effect on a reader…"), and every place that cites it (e.g. the reviewer prompts and the Spec
  Review Specs that include the Protocol's criteria);
- the error/warning "severity" of a structural check: `protocol/checks.md` (the prose and the
  table column), the glossary definition of `concept.structural-check`, the Spec tooling's
  findings and their contracts (`src/concorde/spec/` — validation, model, content repository,
  initialize — and any consumer such as `scripts/issues.py`, the Spec MCP server, task-validation
  readiness), and their tests. No compatibility with the old field name is needed (rapid
  iteration); bump the contract versions that change.

Choose the new words yourself: they must not be existing glossary terms or common words with
another meaning here (avoid "tier", "level", "priority", "weight" if it reads ambiguously). Record
the choice and why. After changing the Protocol run `build`, then `protocol-manifest --write
--bind-project`. Escalate if the rename turns out to reach a Module not bound here in a way that
changes its promise.

### 2. I-d7660c3554be572693ad17681a8449b8 — task merge fails after merging (module.tasks, high, preferred-fix)

Merging issue-severity, `concorde task merge` merged and passed its checks, then
`store.close_resolved` lazily imported `concorde.issues.command` from the new sources while the old
`concorde.issues.shapes` stayed loaded: ImportError, the error escaped (the import is outside the
try), `end_sessions` never ran and no merge result was printed. Fix it generally, so that no
change a merge brings to Concorde's own sources can break the merge's post-merge steps; report
the fix you chose (preferred-fix). Also make sure a failure in closing Issues never skips
`end_sessions` or the merge result. Add a test that reproduces the stale-module situation.

### Not in this task

Backfilling severities of old Issues: not requested.

## Task session decisions (2026-10-01)

### I-d7660c3554be572693ad17681a8449b8 — merge after a change to Concorde's own sources

- **Fix chosen (preferred-fix): freeze the merge process on the sources it started with.**
  `merge_task` first calls `freeze_sources()` (`src/concorde/tasks/merge.py`), which reads every
  `.py` file of the `concorde` package into memory and puts a meta-path finder first, so every
  Concorde module the process imports from then on, before or after `git merge`, is compiled from
  the source as it was when the merge started. Its loader reports no file times, so it neither
  reads nor writes a bytecode cache (a cache written from the kept source would be taken for the
  file's new contents). The checks are processes of their own and run the merged code, as before.
  Rejected alternatives: eagerly importing the modules the post-merge steps need (fragile: every
  new lazy import is a new hole), importing the whole package up front (slow, pulls optional
  dependencies), re-executing from a copied package root (the runtime locates `protocol/`,
  `prompts/`, `scripts/` relative to the package root, so a copy would need the whole checkout).
  Residual, stated in the docstring: data files (not modules) are read as they are when read.
- **Issues never skip the end of a merge.** `close_resolved` imports the Issues command inside a
  guard and turns any failure into one warning with the error chain `issues_unavailable`; the
  merge also guards the call itself, so `end_sessions` and the merge result always follow.
- Spec: `req.tasks.merge-own-sources` (new), `req.tasks.merge-closes-resolved` (extended),
  scenarios `scenario.tasks.merge-own-sources` and `scenario.tasks.merge-issues-unavailable`, and
  the merge paragraph of `coordination/tasks/module.md`. Tests in `tests/concorde/tasks/test_merge.py`
  reproduce the stale-module situation with a throwaway package (the import fails without the
  freeze and succeeds with it) and a merge whose Issues command cannot be imported.

### I-d24569b23b345cd3b8e89ae8b3944c17 — "severity" means only Issue severity

- **Structural checks: `severity` → `strictness`** (values stay `error` and `warning`). Why: it
  says what the property is, how strictly a violation is held against structural conformance; it
  is no glossary term and appears nowhere else in the Specs, Protocol or prompts. Rejected: `level`
  (the error chain's `level`), `effect` (the `Effect` column of every command table), `category`
  (reads as the check families), `kind` (finding kinds of `code_review`), `gravity` (a synonym of
  severity, the very confusion to remove).
- **Evaluation's blocking/advisory: no noun.** `protocol/evaluation.md`'s section "Severity"
  becomes "Blocking and advisory problems", and "Severity measures the effect on a reader…" becomes
  "Whether a problem is blocking depends on its effect on a reader…". Nothing cited the old anchor;
  the reviewer prompts and Spec Review Specs already speak of blocking/advisory and use "severity"
  only for Issue severity, so they need no change.
- Changed: `protocol/checks.md` (prose and the five table columns), `protocol/evaluation.md`, the
  glossary definition of `concept.structural-check`, `Finding.strictness` and
  `content_repository.strictness()` with every consumer (validation, initialize, scaffold,
  task-validation readiness, specify, code_to_spec, spec_review), the Spec Module's documents
  (module, contracts, requirements, scenarios, validation) and tests. The command-line envelope
  carrying the findings goes from `schema_version` 3 to 4 (contract change, no compatibility).
  `scripts/issues.py` and the Issue tools use Issue severity and stay.
- Build and `protocol-manifest --write --bind-project` run after the Protocol change.

## Escalated to the main agent, 2026-10-01T14:18:42Z

- **task-session** task session (task severity-term-and-merge-imports): `severity_outside_task_modules`
  plan_review's report (contract.understanding.plan-review, module.understanding) still names its blocking/advisory field 'severity': the contract schema and example (specs/concorde/execution/operations/understanding/contracts.md), the Findings section of understanding/module.md, prompts/workers/plan-review.md and src/concorde/understanding/plan_review.py. That is the last use of 'severity' for something other than Issue severity. Renaming it changes module.understanding's contract, and module.understanding is not one of this task's Modules. Everything else is delivered at e42e6a21.
  Not handled here (decision): The brief says to escalate when the rename reaches a Module not bound here in a way that changes its promise; renaming the field changes contract.understanding.plan-review.
  Options: Extend this task with module.understanding: rename the field to a boolean 'blocking' (true when following the plan unchanged would miss the goal or break a promise), bump the contract version, update the prompt, code and tests, then deliver again; Open a separate small task bound to module.understanding for the same rename and merge this task as it is; Leave plan_review's field as it is
  Recommendation: Open a separate small task (option 2): this task is delivered and validated, and the plan_review rename is independent of it. A boolean 'blocking' matches the Protocol, which now names no noun for blocking/advisory.

```json
{
  "level": "task-session",
  "actor": "task session (task severity-term-and-merge-imports)",
  "code": "severity_outside_task_modules",
  "detail": "plan_review's report (contract.understanding.plan-review, module.understanding) still names its blocking/advisory field 'severity': the contract schema and example (specs/concorde/execution/operations/understanding/contracts.md), the Findings section of understanding/module.md, prompts/workers/plan-review.md and src/concorde/understanding/plan_review.py. That is the last use of 'severity' for something other than Issue severity. Renaming it changes module.understanding's contract, and module.understanding is not one of this task's Modules. Everything else is delivered at e42e6a21.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The brief says to escalate when the rename reaches a Module not bound here in a way that changes its promise; renaming the field changes contract.understanding.plan-review."
  },
  "options": [
    "Extend this task with module.understanding: rename the field to a boolean 'blocking' (true when following the plan unchanged would miss the goal or break a promise), bump the contract version, update the prompt, code and tests, then deliver again",
    "Open a separate small task bound to module.understanding for the same rename and merge this task as it is",
    "Leave plan_review's field as it is"
  ],
  "recommendation": "Open a separate small task (option 2): this task is delivered and validated, and the plan_review rename is independent of it. A boolean 'blocking' matches the Protocol, which now names no noun for blocking/advisory.",
  "causes": []
}
```

## Closed: merged, 2026-10-01T14:18:43Z
