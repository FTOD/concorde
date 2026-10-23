# Decision log: r4-method-work

Goal: Fix the critical and high open Issues of Implementation, Understanding, General work, Validation, Delivery, Adoption, Scaffold and Specification found by the fourth project_review

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

## Escalated to the main agent, 2026-10-17T04:35:54Z

- **task-session** task session (task r4-method-work): `issue_decision_needed`
  I-25f89daafb0b56fc9fedade6ef0063b9 (Specification, high): req.specification.no-code says the specify worker's grant SHALL NOT give read access to the contents of ANY implementation file, and module.md says 'Implementation files show by name only'. But Spec core's req.spec.bound-inclusion (module.spec, not mine) makes a file selected by an `includes` of kind `bound` ro for every task type that does not write the implementation scope, specify included; tests/concorde/spec/test_grants.py:548-557 asserts specify gets ro on such a file, and Specification launches the standard worker unchanged. So today the code honours Spec core and breaks Specification's absolute promise. E2E's SWE-bench cases (module.swe-bench-cases, specs/concorde/e2e/cases/module.md:243-244) cite the absolute promise ('It cannot read the code either').
  Not handled here (decision): Either option changes what a Module promises: A narrows Specification's promise, B changes Spec core's grant (another Module) and the Protocol's semantics of bound inclusions.
  Options: A (recommended): narrow req.specification.no-code, module.md and the specify prompt to: the specify worker reads no implementation file's contents except a file a bound Module explicitly selects into its Spec context with a bound inclusion; every other implementation file only by name. Matches current behaviour; changes Specification's promise (narrowing) and needs a one-sentence mechanical follow-on in E2E cases' module.md (outside my Modules).; B: keep the absolute promise; make Method/Spec core lower bound inclusions to names for specify. Changes Spec core's req.spec.bound-inclusion and Method's req.method.grant-as-data (outside my Modules, a Protocol-level change), and changes behaviour users have today.
  Recommendation: A: a bound inclusion is the Module author's explicit decision that the file is part of the Spec context; hiding it from specify alone would defeat it. A is a narrowing of the promise to what the code already does.

```json
{
  "level": "task-session",
  "actor": "task session (task r4-method-work)",
  "code": "issue_decision_needed",
  "detail": "I-25f89daafb0b56fc9fedade6ef0063b9 (Specification, high): req.specification.no-code says the specify worker's grant SHALL NOT give read access to the contents of ANY implementation file, and module.md says 'Implementation files show by name only'. But Spec core's req.spec.bound-inclusion (module.spec, not mine) makes a file selected by an `includes` of kind `bound` ro for every task type that does not write the implementation scope, specify included; tests/concorde/spec/test_grants.py:548-557 asserts specify gets ro on such a file, and Specification launches the standard worker unchanged. So today the code honours Spec core and breaks Specification's absolute promise. E2E's SWE-bench cases (module.swe-bench-cases, specs/concorde/e2e/cases/module.md:243-244) cite the absolute promise ('It cannot read the code either').",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Either option changes what a Module promises: A narrows Specification's promise, B changes Spec core's grant (another Module) and the Protocol's semantics of bound inclusions."
  },
  "options": [
    "A (recommended): narrow req.specification.no-code, module.md and the specify prompt to: the specify worker reads no implementation file's contents except a file a bound Module explicitly selects into its Spec context with a bound inclusion; every other implementation file only by name. Matches current behaviour; changes Specification's promise (narrowing) and needs a one-sentence mechanical follow-on in E2E cases' module.md (outside my Modules).",
    "B: keep the absolute promise; make Method/Spec core lower bound inclusions to names for specify. Changes Spec core's req.spec.bound-inclusion and Method's req.method.grant-as-data (outside my Modules, a Protocol-level change), and changes behaviour users have today."
  ],
  "recommendation": "A: a bound inclusion is the Module author's explicit decision that the file is part of the Spec context; hiding it from specify alone would defeat it. A is a narrowing of the promise to what the code already does.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-17T04:36:02Z

- **task-session** task session (task r4-method-work): `issue_decision_needed`
  I-5d7bd1c8292c5f9a9a80cb3dc1406f6a (General work, high): contracts.md defines only the aggregate contract.general-work.result; it says 'the worker's answer and the review's summary and findings are the workers' claims' but no Spec states the two job-specific output parts handed to Workers, nor how each worker-result envelope maps into the result. The code already has them (src/concorde/method/general_work/operation.py:50-78): the worker's output part is {answer: non-empty string}, required; the reviewer's is {findings: [finding as in the result]}, required; review.summary is the reviewer envelope's top-level summary; the Operation sets type, read_only, instruction, change and verdict. An answer missing from an ok result shows as '(no answer)' in the code.
  Not handled here (decision): The Issue is tiered decision-needed: it asks to establish two new interface promises of General work (contracts), which only the level above may settle.
  Options: A (recommended): state the existing behaviour as two new contracts in general-work/contracts.md (contract.general-work.worker-output and contract.general-work.review-output) with the envelope-to-result mapping; no code change, no change to a promise users rely on (adds promises that match today's behaviour).; B: define different output parts (e.g. the reviewer also returns its own summary inside output) and change the code to match; changes the worker prompts and behaviour.
  Recommendation: A: it documents the interface already implemented and tested, and changes no earlier developer decision.

```json
{
  "level": "task-session",
  "actor": "task session (task r4-method-work)",
  "code": "issue_decision_needed",
  "detail": "I-5d7bd1c8292c5f9a9a80cb3dc1406f6a (General work, high): contracts.md defines only the aggregate contract.general-work.result; it says 'the worker's answer and the review's summary and findings are the workers' claims' but no Spec states the two job-specific output parts handed to Workers, nor how each worker-result envelope maps into the result. The code already has them (src/concorde/method/general_work/operation.py:50-78): the worker's output part is {answer: non-empty string}, required; the reviewer's is {findings: [finding as in the result]}, required; review.summary is the reviewer envelope's top-level summary; the Operation sets type, read_only, instruction, change and verdict. An answer missing from an ok result shows as '(no answer)' in the code.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is tiered decision-needed: it asks to establish two new interface promises of General work (contracts), which only the level above may settle."
  },
  "options": [
    "A (recommended): state the existing behaviour as two new contracts in general-work/contracts.md (contract.general-work.worker-output and contract.general-work.review-output) with the envelope-to-result mapping; no code change, no change to a promise users rely on (adds promises that match today's behaviour).",
    "B: define different output parts (e.g. the reviewer also returns its own summary inside output) and change the code to match; changes the worker prompts and behaviour."
  ],
  "recommendation": "A: it documents the interface already implemented and tested, and changes no earlier developer decision.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-17T04:36:11Z

r4-method-work, early report: the two decision-needed Issues of the task, escalated together as the brief asks (escalations 1 and 2). I continue with the 12 preferred-fix/obvious-fix Issues meanwhile.

1. I-25f89daa (Specification, high) — req.specification.no-code ('no implementation file contents') contradicts Spec core's req.spec.bound-inclusion, which today gives specify ro on bound-included files (tested). Options: A (recommended) narrow Specification's promise to 'no contents except files a bound Module explicitly includes with a bound inclusion' — changes Specification's promise to match current behaviour; needs a one-sentence mechanical follow-on in specs/concorde/e2e/cases/module.md (module.swe-bench-cases, outside my Modules) which cites the absolute promise. B keep the absolute promise and change Spec core/Method grant semantics — changes another Module's promise and today's behaviour.

2. I-5d7bd1c8 (General work, high) — the worker's and reviewer's output parts and their mapping into contract.general-work.result are not specified. Options: A (recommended) state the existing code's schemas ({answer} and {findings}, review.summary from the reviewer envelope) as two new contracts — adds promises matching today's behaviour, changes no earlier decision. B define different outputs and change code.

Please answer both; may I make the E2E cases one-sentence follow-on under option A of #1?

It carries escalation(s) 1, 2.

## Answer to report(s) 1 of the task session, 2026-10-17T04:36:29Z

Escalations 1-2 (main agent): 1 A — narrow req.specification.no-code to 'no implementation file contents except files a bound Module includes with a bound inclusion', which follows the developer's 2026-10-12 decision (Protocol 16.5 bound inclusions); the one-sentence follow-on in specs/concorde/e2e/cases/module.md is allowed (r4-e2e-dist also edits module.swe-bench-cases; keep it to that sentence). 2 A — state the existing worker and reviewer output schemas and their mapping into contract.general-work.result as two new contracts.

## Task session decisions, 2026-10-17

- I-8dbbac1e (obvious-fix): `staged_differences` now always hashes `git cat-file --filters` output for regular files, not only when the raw blob differs; raw blobs are read in batch only for symlinks. One subprocess per changed regular file; chose this over `cat-file --batch --filters` because batch input separates object and path by whitespace, which breaks on paths with spaces. Regression test: identity clean filter + rewriting smudge filter → `staged_unvalidated`, index given back.
- I-b2bf691e (preferred-fix): the Delivery entry and step 6 now require at least one verifying test per added/changed scenario, linking req.delivery.scenarios-verified.
- I-f6eb5a97, I-16aa8059, I-f255b0cb (preferred-fix): Implementation, Understanding and General work now rely on `contract.execution.run-result` and `req.execution.inputs-same-workspace` (Understanding also `req.execution.unbound-read-only`), include `document.execution.runner`, and link them in uses-execution. Registry refreshed with `registry --write`.
- I-334add58 (obvious-fix): the entry lists `summary` among each worker's claims.
- I-37eaf2e5 (preferred-fix): `ok` stated as the conjunction of worker ok, clean audit, successful deletions and passing checks; zero checks satisfies only the check condition.
- I-d761f05a (preferred-fix): the Spec-gap stop applies only to a gap that prevents the assigned work; test may end `ok` diagnosing a Spec defect (links req.method.gaps-never-repaired). Prompts already said so.
- I-0c1af497 (preferred-fix): scenario.understanding.gap narrowed to an existing relied-on promise; new scenario.understanding.new-promise (verified by a new test) shows a new promise with a known place planned as a specify step.
- I-e348012a (obvious-fix): req.adoption.open-questions statement now says "neither the code nor an admitted answer settles", linking req.adoption.answers-followed.
- I-4fcaf0a7 (preferred-fix): the Specification entry describes the specify tool set by capability and links the Harness's Claude Code and pi tool-set sections, naming the backend's result channel.
- I-25f89daa (decision A by the main agent): req.specification.no-code, the entry and the specify prompt except files a bound Module includes with a bound inclusion (ro); one-sentence follow-on in specs/concorde/e2e/cases/module.md as allowed, with the term link spec-validation asked for. Specification now relies on req.spec.bound-inclusion.
- I-675fe3d8 (preferred-fix): the kept change now lives in `<run node>/change/` (`change.diff`, `before/`), and only that folder is admitted as the reviewer's runtime path. Result contract keeps version 1 (same schema, paths are absolute strings; rapid-iteration rule).
- I-5d7bd1c8 (decision A by the main agent): new contracts `contract.general-work.worker-output` and `contract.general-work.review-output` stating the code's existing schemas, plus a mapping table; the contract test now checks all three schemas against the code.

## Non-ok result: delivery r-20261017T045642-delivery-87b29d65 (blocked, not_ready)

check.views.repository-regressions (module.views, not this task's) failed: in `tests/repository/fresh-project-scaffold.test.ts` the fresh project's `Docusaurus exited with status 1` with no further message, and two dependent cases then missed its build outputs. The same check passed in task-validation r-20261017T044633-task_validation-47ed53c2 on the identical committed input, and nothing this task changed reaches the scaffolded fresh project. Judged a flaky/environmental failure (eight r4 tasks build docsites concurrently); decision: run delivery again unchanged. If it recurs, escalate rather than touch module.views.

## Report 2 to the main agent (Review流程), 2026-10-17T05:17:13Z

r4-method-work delivered: delivery commit 8cf9c98e38ab13c8277c8280c12949428b288e90 on concorde/r4-method-work (run r-20261017T050635-delivery-ad50385a). Full suite on the final input: 1593 passed, 6 skipped. task-validation ready.

All 14 Issues in `resolves` are fixed (none turned out stale or duplicate):
- Delivery: I-8dbbac1e (code) — the staged-content gate now always compares checkout-filtered content, with a regression test (identity clean + rewriting smudge filter → staged_unvalidated, index given back). I-b2bf691e — entry/step 6 require a verifying test per changed scenario.
- Implementation: I-334add58 (summary listed among worker claims), I-37eaf2e5 (ok = worker ok AND clean audit AND deletions succeeded AND checks passed; zero checks satisfies only the last), I-d761f05a (Spec-gap stop only when it prevents the work; test may end ok diagnosing a Spec defect).
- Execution selection: I-f6eb5a97, I-16aa8059, I-f255b0cb — Implementation, Understanding and General work now rely on contract.execution.run-result and req.execution.inputs-same-workspace (Understanding also req.execution.unbound-read-only), include document.execution.runner, and link them. Registry refreshed.
- Understanding: I-0c1af497 — gap scenario narrowed to existing relied-on promises; new scenario.understanding.new-promise with a verifying test.
- Adoption: I-e348012a — the open-question requirement states the admitted-answer exception.
- Specification: I-4fcaf0a7 — backend-neutral tool description linking the Harness tool sets and naming the result channel. I-25f89daa (your answer A) — no-code narrowed to except bound inclusions (requirement, entry, specify prompt); the one allowed follow-on sentence in specs/concorde/e2e/cases/module.md (plus the term link spec-validation asked for in that same sentence).
- General work: I-675fe3d8 — the kept change now lives in <run node>/change/ (change.diff, before/), the only folder admitted to the reviewer. I-5d7bd1c8 (your answer A) — new contract.general-work.worker-output and contract.general-work.review-output plus a mapping table; the contract test checks all three against the code.

Decisions taken myself (all in the decision log): per-file `cat-file --filters` instead of a batch (paths with spaces); contract.general-work.result keeps version 1 (same schema, only absolute path values move); first delivery r-20261017T045642-delivery-87b29d65 was blocked by check.views.repository-regressions (fresh-project Docusaurus build exited 1 without detail), which had passed in task-validation on identical input — judged flaky/environmental and reran delivery unchanged, which passed. You may want an Issue for that Views flake if it shows up in other tasks.

Open: nothing for this task. Validation and Scaffold had no Issues in resolves.

## Closed: merged, 2026-10-23T09:02:00Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 8cf9c98e38ab13c8277c8280c12949428b288e90 into main and closed it as merged. Nobody answers a report after that.
