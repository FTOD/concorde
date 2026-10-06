# Decision log: remove-spec-review

Goal: Remove the spec_review Operation; spec_panel becomes the only Spec review Operation, and the brownfield workflow's review step runs spec_panel with its defaults

## Task brief (main agent, 2026-10-07)

### Developer decisions this task carries out

- The developer judged `spec_review` no longer needed. Remove the `spec_review` Operation
  entirely: its Spec text, requirements, scenarios, contracts, host code, worker prompts that only it
  uses, its `--check-findings` option and its `checker` worker id, its catalog registration, its
  tests and every mention in other Modules' Specs, guidance (`prompts/guidance/**`), worker prompts,
  docsite pages and e2e cases. `spec_panel` becomes the only Spec review Operation.
- The `brownfield` workflow's review step (step 4) runs `spec_panel` **with its defaults**
  (3 reviewers, 2 architects, chair) instead of `spec_review`. The developer chose the defaults over
  a lighter panel.
- No backward compatibility (rapid-iteration rule): no alias, no deprecation path. Old names in
  `.concorde/workers.json` entries for `spec_review` (if any) are removed.

### Context

- A second task, `project-review`, follows after this one merges. It adds a project-level
  `project_review` Operation that reuses the panel's code (per-Module reviewers + chair, one
  project-wide architecture review, Module-scope code review, configured checks, scenario coverage,
  unowned code, and skipping Modules unchanged since their last review). Do not build any of that
  here, but keep the shared parts of the Spec review host (earlier Issues, finding normalization,
  Issue reporting, verdict derivation) intact and reusable by `spec_panel`; move what only
  `spec_review` used out, and what `spec_panel` still needs into the panel's own code if needed.
- Other Modules mention `spec_review` mostly as examples (Execution, Workers, Issues, Coordination,
  Spec tooling, Distribution, the root, Understanding). Replace those with `spec_panel` or another
  fitting example; they are within this task's goal even though not listed in `--modules`.
- Glossary entries owned by `module.spec-review` (review finding, review verdict) stay, reworded if
  they mention a Spec review run.

### Left for the session to decide

- The resulting structure of the Spec review Module's documents (e.g. whether `operation.md` folds
  into `panel.md`), naming, and the replacement examples.
- Whether `spec_panel`'s `--reviewers` lower bound stays 2.

Deliver with `task-validation` then `delivery`; run the full test suite once on the final input.

## Task session decisions (2026-10-07)

- **Document structure.** `operation.md` (the `spec_review` definition) is removed. What `spec_panel`
  still relies on from it (earlier Issues, finding normalization, reporting findings as Issues,
  without the issues part, step output, the worker finding shape, evidence) moves into `panel.md`,
  which becomes the Module's one self-contained Operation definition. Keeping the name `panel.md`
  keeps every existing link to it valid. Reason: the panel is the only Operation left; one
  definition is easier to read than a panel that refers to a removed Operation.
- **Code structure.** `src/concorde/method/spec_review/operation.py` becomes `review.py`, holding
  only what the panel (and the coming `project_review`) reuses: per-Module review state, step 1
  validation, task section and Protocol criteria of a brief, path normalization and repair, earlier
  Issues, Issue reporting and the blocking counts. The checker, its `--check-findings` option, the
  `spec_review` payload and the `SPEC_REVIEW` Operation are removed. The disputed-finding filter
  goes with the checker. Reason: the brief asks to keep the shared host parts intact and reusable.
- **Worker prompts.** `prompts/workers/review-spec.md` (only `spec_review` loaded it) is removed.
  `prompts/workers/spec-review/checklist.md` stays as the shared checklist of the panel brief,
  with its `checker` wording removed.
- **Earlier Issues filter.** `REVIEW_OPERATIONS` becomes `("spec_panel",)`. The primary worktree
  has no open Issue at all (checked `.concorde/issues/`), so no open Issue reported by a
  `spec_review` run is lost. No compatibility path, per the rapid-iteration rule.
- **`--reviewers` lower bound stays 2.** A panel of one reviewer gives the chair nothing to compare
  and makes it a reviewer plus checker, which is what was removed. Two keeps the panel's point:
  independent reviews whose agreement is evidence.
- **Replacement examples.** Where another Module or a test used `spec_review` as an example of a
  reading Operation, it now uses `spec_panel`. Where it used `spec_review`'s worker ids
  (`reviewer`, `checker`), it uses `spec_panel`'s (`reviewer2`, `chair`, ...).
- **E2E SWE-bench case.** The case runs `spec_panel` with its defaults where it ran `spec_review`
  (step names `spec_panel`, `spec_panel_again`), consistent with the brownfield decision.
- **Acceptance tests without Python dependencies.** The "Method without Issues" acceptance test
  installs Concorde without its Python dependencies, so `spec_panel` (a LangGraph graph) cannot run
  there. It now uses a `code_review --scope module` as its review. The root scenario
  `scenario.concorde.method-without-issues` says "a review" generically. The brownfield acceptance
  flow keeps the real default panel: its test rebuilds the installed environment on the test
  interpreter and borrows the test environment's packages through a `.pth` file, and asserts that
  the `spec_panel` step ended `ok` (the first attempt, a `.pth` alone, failed with
  `langgraph_unavailable` because the installed environment was Python 3.13 and the test one 3.11).
- **Shared helpers.** `review_issues.settle` and `report` lose their `skipped` parameter, which only
  the checker's disputed findings used.
- **Contracts.** `contract.understanding.assessment` goes to version 5 (its plan step enum names
  `spec_panel` instead of `spec_review`). `contract.spec-review.panel-payload` keeps version 6: no
  field or behaviour of the payload changed, only its semantics text no longer refers to the removed
  payload.
- Verification: build and `build --check` clean, `registry --check` clean, `spec-validation` valid
  with only the 12 pre-existing warnings of other Modules, prompt style check 0/0/0, full suite
  1265 passed / 5 skipped, `task-validation` ready (r-20261006T185100-task_validation-178542c5).

## Report 1 to the main agent (concorde-d4), 2026-10-06T19:06:15Z

remove-spec-review delivered: delivery commit 9dfb15d2 on concorde/remove-spec-review (run r-20261006T185829-delivery-2cfe359b), on top of 082f1ee8. Ready to merge.

Done: spec_review is gone (Spec text, requirements, scenarios, contract.spec-review.payload, host code, checker and --check-findings, prompts/workers/review-spec.md, catalog registration, tests, and every mention in other Modules' Specs, guidance, worker prompts, docs and the e2e case). spec_panel is the only Spec review Operation. The brownfield review step (key spec_panel) runs spec_panel with its defaults. .concorde/workers.json had no spec_review entry.

Decisions I took (details in the decision log):
1. Specs: operation.md removed; panel.md is now the one self-contained Operation definition (earlier Issues, normalization, Issue reporting, without-issues, step output, finding shapes, evidence moved in). Name kept so existing links stay valid.
2. Code: spec_review/operation.py renamed to review.py, holding only the shared parts (validation step, brief sections and criteria, normalization and path repair, earlier Issues, reporting, blocking counts), ready for project_review to reuse. review_issues.settle/report lose their checker-only `skipped` parameter.
3. Earlier Issues now come only from spec_panel reports (REVIEW_OPERATIONS = spec_panel). The primary worktree has no open Issue, so nothing is lost.
4. --reviewers lower bound stays 2: one reviewer gives the chair nothing to compare.
5. Replacement examples: spec_panel for reading Operations; spec_panel's reviewer1/reviewer2 and general's reviewer for worker-model examples.
6. contract.understanding.assessment goes to version 5 (plan step enum spec_review -> spec_panel). The panel payload keeps version 6 (only its semantics text changed).
7. The "Method without Issues" acceptance test installs without Python dependencies, where spec_panel (LangGraph) cannot run. It now uses a code_review Module review, and the root scenario says "a review". The brownfield acceptance flow keeps the real default panel: its test rebuilds the installed environment on the test interpreter, borrows the test packages, and asserts the spec_panel step ends ok.
8. The e2e SWE-bench repair round runs spec_panel with its defaults (steps spec_panel, spec_panel_again).

Verification: build and build --check clean, registry --check clean, spec-validation valid (only the 12 pre-existing warnings in other Modules), prompt style 0/0/0, full suite 1265 passed / 5 skipped, task-validation ready.

Open: nothing for this task. No escalations. No Issues resolved.

## Closed: merged, 2026-10-06T19:06:32Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 9dfb15d233a9306a5a222e04c6a5d743fe3e4665 into main and closed it as merged. Nobody answers a report after that.
