# Code review requirements

The Module-wide obligations of [Code review](module.md). The report's shape is in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations in concrete
situations.

## Inputs

### req.code-review.diff-within-grant — The diff shows only readable contents

The diff given to the reviewer SHALL show the contents of a changed path only when the grant makes
that path readable, listing every other changed path by name only.

### req.code-review.checks-by-host — Checks run through the Operation

The code review [Operation](../../../glossary.json#concept.operation) SHALL run the bound Modules'
[configured checks](../../../glossary.json#concept.configured-check) through Check execution before
it launches the reviewer.

## Reviewing

### req.code-review.reads-check-logs — The reviewer reads the check logs

The code_review Operation SHALL let its reviewer read the log of every check the Operation ran for the run.

### req.code-review.read-only — The reviewer cannot change or run anything

The reviewer's tool list SHALL contain only tools that read files.

### req.code-review.no-edits — The worktree is left unchanged

The code review Operation SHALL leave every file of the workspace unchanged.

A change found by the [write audit](../../../glossary.json#concept.write-audit) ends the run
`failed` with the changed paths as host evidence.

### req.code-review.one-pass — Every blocking finding at once

The reviewer SHALL report every blocking finding it can establish in a single run.

### req.code-review.basis — Blocking findings name their basis

Every blocking finding SHALL name the requirement, scenario, contract, concept or
[Spec](../../../glossary.json#concept.spec) passage from the bound Modules'
[Spec context](../../../glossary.json#concept.spec-context) that it judges the code against.

### req.code-review.basis-resolves — Cited identities exist

The code review Operation SHALL end a run `failed` when a finding cites a stable identity or a
document that the bound Modules' Spec context does not define, or when a blocking finding names no
basis.

## Verdict

### req.code-review.verdict-derived — The Operation derives the verdict

The code review Operation SHALL set the verdict to `changes_required` exactly when at least one
finding is blocking.

### req.code-review.no-resume — No automatic resume

The code review Operation SHALL NOT resume the reviewer after it has returned its result.
