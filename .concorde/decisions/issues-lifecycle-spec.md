# Decision log: issues-lifecycle-spec

Goal: Clarify main-agent Issue interactions, state transitions, and branch-local record handling in Specs and guidance

## Scope and decisions

- The developer chose task-worktree Issue writes, preservation guidance before ending an unmerged task, manual merge-conflict handling followed by the store check, and explicit lifecycle requirements.
- This is a Spec and guidance change. Keep the CLI's optional `report --task` and existing schemas unchanged: the task-only workflow is guidance, not newly enforced admission logic. Only `report` accepts `--task`; `close` and `reopen` use the selected root.
- Clarify an incorrect premise in the earlier questionnaire: Tasks removes a closed worktree but keeps its branch, record and decision log. Committed Issues remain recoverable on that branch; unmerged records are absent from main, and forced removal may lose uncommitted material.
- Keep accepted reports immutable when resolving Git conflicts. Do not suggest concatenating competing closing dispositions or fabricating reopenings; record the semantic decision and validate the resulting history explicitly with `issues check`.
- Scope the actor requirement to attribution by the Issues command; the store remains a library that trusts caller-supplied provenance and is not an authorization boundary.
- The first task-open invocation was refused as `invalid_command` because Modules were passed as separate words. Retried with the CLI's comma-separated `--modules module.issues,module.main-session`; it succeeded without changing sources in the primary worktree.
- Added a documentation inclusion of Tasks' entry to Issues and selected Issues' report/receipt contracts and status/revision concepts for Main session, so the expanded explanations have explicit Spec context. Refreshed the registry with the task worktree's command.
- Structural validation initially reported five uncovered new scenarios. Delivery treats changed prompts as realization changes and requires coverage for changed scenarios, so added the corresponding store/CLI behavior checks and rendered-guidance assertions using the existing test style. These deterministic checks cannot establish how a model will follow the guidance.

## Verification before the source commit

- Final input: `build --check` and structural `validate` passed with no findings; `issues check` reported no errors or notes.
- Full pytest suite: 572 passed, 4 skipped (12.08 seconds). The preceding run also passed; the final run includes the last Spec wording and diagram correction.
- Both new illustrative D2 diagrams compiled successfully with the installed D2 binary.
- Ruff formatting and its second pass passed for the changed Python tests; Prettier formatting and its second pass passed for changed metadata. Specs retain their existing Markdown table and prose style.
- Active LSP checks reported no errors in the three changed test files. Reviewed the source diff and checked whitespace before staging.

## Delivery

- Source commit: `9dd6c770f1700bb1c172b2d159220cec85e33f55`; staged diff matched the reviewed diff and the worktree was clean after committing.
- `validate` run `r-20260926T173307-validate-fb512f8c`: ready, 15 configured checks passed, no structural findings, warnings or confirmations. Inspected host evidence, the run record and the Issues/Main session check logs.
- `delivery` run `r-20260926T173421-delivery-e151ccc1`: ready with the same 15 checks passed; nine added or changed scenarios have verification declarations. It committed only `.concorde/evidence/issues-lifecycle-spec/1.json` as `1a1f48af73f932f2ea6057979b5fefdd4fa54f1c` and recorded the task as delivered. No runtime implementation was changed by the Operation.

## Closed: merged, 2026-09-26T17:36:04Z
