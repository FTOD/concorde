# Understanding requirements

The Module-wide obligations of [Understanding](module.md). The assessment's shape is in the
[contracts](contracts.md). The [scenarios](scenarios.md) show the obligations in concrete situations.

## Reading

### req.understanding.names-only — Code is known by name only

The understand worker's grant SHALL give read access only to
[Spec](../../glossary.json#concept.spec) documents and included external material, never to the
contents of an implementation file.

Implementation files of the bound Modules appear in the brief by path only. This lets the worker
place a planned file without learning what existing code does.

### req.understanding.task-worktree — Assessments describe the run worktree's Specs

The understand [Operation](../../glossary.json#concept.operation) SHALL compute the grant from the
Specs of the worktree the run works on.

For a bound run, that worktree is its workspace, uncommitted changes included. For an
[unbound run](../../glossary.json#concept.unbound-run), it is Execution's
[unbound checkout](../../glossary.json#concept.unbound-checkout), which holds the committed head of
the worktree the run starts in. The uncommitted Spec edits of that worktree therefore never reach
the grant, as
[scenario.understanding.unbound-committed-specs](scenarios.md#scenario.understanding.unbound-committed-specs)
shows.

## Answers

### req.understanding.gaps-reported — Missing promises are gaps

An assessment SHALL report as a [Spec gap](../../glossary.json#concept.spec-gap), rather than as a
fact inferred from code or file names, every promise that meets all these conditions:

- The stated goal relies on the promise.
- A bound [Module](../../glossary.json#concept.module)'s Spec does not state the promise.
- The promise is not a new promise of the goal's change for which the Specs already say where it
  belongs.

A goal that changes the Modules adds new promises. When the Specs say where such a promise belongs,
the assessment's plan writes it there in a `specify` step.

### req.understanding.insufficient-no-plan — No plan on an insufficient Spec

An assessment that finds the Spec insufficient for the goal SHALL carry no plan.

### req.understanding.plan-on-request — Plans only when asked

The understand Operation SHALL return a plan only when `--plan` was given.

### req.understanding.known-modules — Assessments name existing Modules

When the assessment names a Module identity that the Specs of the run's worktree do not define,
the understand Operation SHALL end a run `failed`.

The unknown identities are returned as host evidence. The Operation never drops or corrects them.

### req.understanding.consistent — Inconsistent assessments fail the run

When the assessment has any of these inconsistencies, the understand Operation SHALL end a run
`failed`:

- It lists Spec gaps although it is sufficient.
- It lists no Spec gaps although it is insufficient.
- It carries a plan that was not requested.
- It carries a plan that follows an insufficient Spec.
- It carries no plan although one was requested and the Spec is sufficient.
- It has no entry for a bound Module.
- It has more than one entry for a bound Module.
- It has an entry for a Module that is not bound.

Each inconsistency is returned as host evidence. The run is not resumed to repair it.

## Effects

### req.understanding.no-writes — The worker may write nothing

The understand Operation SHALL run its worker under a grant with no writable path.

The worker has no editing or shell tool.

### req.understanding.change-fails — A change to the worktree fails the run

When the [write audit](../../glossary.json#concept.write-audit) finds any violation in the worktree
the run works on, such as a changed, new or deleted file, the understand Operation SHALL end a run
`failed`.

The changed paths are returned as host evidence. The change is left in place for the caller, never
reverted. These files are written into the [run store](../../glossary.json#concept.run-store):

- The run's own [run progress file](../../glossary.json#concept.run-progress-file).
- The run's own [run result](../../glossary.json#concept.run-result).
- Its worker's [progress file](../../glossary.json#concept.progress-file).
- Its worker's [run record](../../glossary.json#concept.run-record).

Git ignores the run store. These files are not changes the audit judges.

### req.understanding.single-round — No resume rounds

After the worker returns its result, the understand Operation SHALL NOT resume the worker.

## Plan review

### req.understanding.plan-review-bound — A plan is reviewed in its workspace

The `plan_review` Operation SHALL brief its reviewer with the goal of the workspace whose
[workspace binding](../../glossary.json#concept.workspace-binding) lies in the worktree the run
starts in.

A worktree without a binding has no goal to review the plan against, so the run is refused there.

### req.understanding.plan-review-kept — The reviewed plan is kept

The `plan_review` Operation SHALL keep an exact copy of the plan file it reviews in the run's
[trace node](../../glossary.json#concept.trace-node).

Before any worker launches, a plan file with any of these problems ends the run `failed` with
`plan_unreadable`:

- It is missing.
- It is unreadable.
- It is not UTF-8 text.
- It is empty.

### req.understanding.plan-review-copy-reported — The report names the kept copy

The `plan_review` Operation SHALL return in its report the path of the copy that
[req.understanding.plan-review-kept](#req.understanding.plan-review-kept) keeps and the digest of
that copy's bytes, which are the bytes the reviewer reviewed.

### req.understanding.plan-review-read-only — The reviewer reads Specs and code and writes nothing

The `plan_review` Operation SHALL run one reviewer,
[worker id](../../glossary.json#concept.worker-id) `reviewer`, under the bound Modules'
`review-code` [grant](../../glossary.json#concept.grant), with no writable path, no
[configured check](../../glossary.json#concept.configured-check) and no
[resume round](../../glossary.json#concept.resume-round).

Any violation the [write audit](../../glossary.json#concept.write-audit) finds ends the run
`failed`. The changed paths are host evidence.

### req.understanding.plan-review-answers — Every previous finding is answered once

When any of these conditions holds, the `plan_review` Operation SHALL end the run `failed` with
`iteration_mismatch` before any worker launches:

- More than one admitted input is a `plan_review` run.
- A finding of the admitted `plan_review` input is not answered exactly once by `--accept` or
  `--reject`.
- An answer names no finding of that input.
- An answer is given without such an input.

Every problem is listed in the error. The admitted inputs of other Operations are material for the
reviewer. They need no answer.

### req.understanding.plan-review-responses — The reviewer answers the previous iteration

When any of these conditions holds, the `plan_review` Operation SHALL end the run `failed` with
`inconsistent_review`:

- Two of the reviewer's findings have the same id.
- The reviewer's responses are not exactly one per finding of the previous iteration.
- A maintained finding is not restated by exactly one finding.
- A finding restates a finding that is not maintained.
- A finding names a Module that is not bound.

### req.understanding.plan-review-basis — Bases resolve

When a finding's basis does not resolve in the bound Modules'
[Spec context](../../glossary.json#concept.spec-context) or a `violation` finding has no basis, the
`plan_review` Operation SHALL end the run `failed` with `unresolved_basis`.

A concept resolves when the Spec context selects its glossary entry, wherever its explanation lies.
A document path resolves when the Spec context selects the document. An anchor after the path
resolves only when that document has it, as one of these:

- A readable anchor, such as an `<a id>` anchor or a requirement or scenario identity.
- The anchor of one of its headings: an explicit `{#…}` anchor, or else the heading's text in lower
  case, without punctuation other than `-` and `_`, with each space a `-`.

### req.understanding.plan-review-verdict — The verdict follows the findings

The `plan_review` Operation SHALL set the verdict of an `ok` report as follows:

- Exactly when one of its findings is blocking, the verdict is `changes_required`.
- Otherwise, the verdict is `accepted`.

The Operation never changes, drops or adds a finding or a response.
