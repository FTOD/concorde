# Understanding requirements

The Module-wide obligations of [Understanding](module.md). The assessment's shape is in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations in concrete
situations.

## Reading

### req.understanding.names-only — Code is known by name only

The understand worker's grant SHALL give read access only to
[Spec](../../glossary.json#concept.spec) documents and included external material, never to the
contents of an implementation file.

Implementation files of the bound Modules appear in the brief by path only, so the worker can place
a planned file without learning what existing code does.

### req.understanding.task-worktree — Assessments describe the run worktree's Specs

The understand [Operation](../../glossary.json#concept.operation) SHALL compute the grant from the Specs of the worktree the run starts in, which for a bound run is its workspace.

## Answers

### req.understanding.gaps-reported — Missing promises are gaps

An assessment SHALL report every promise the stated goal relies on and a bound
[Module](../../glossary.json#concept.module)'s Spec does not state as a
[Spec gap](../../glossary.json#concept.spec-gap) rather than as a fact inferred from code or file
names.

For a goal that changes the Modules, a new promise the change adds is not a gap when the Specs say
where it belongs: it becomes a `specify` step of the plan.

### req.understanding.insufficient-no-plan — No plan on an insufficient Spec

An assessment that finds the Spec insufficient for the goal SHALL carry no plan.

### req.understanding.plan-on-request — Plans only when asked

The understand Operation SHALL return a plan only when `--plan` was given.

### req.understanding.known-modules — Assessments name existing Modules

The understand Operation SHALL end a run `failed` when the assessment names a Module identity that
the Specs of the run's worktree do not define.

The unknown identities are returned as host evidence; the Operation never drops or corrects them.

### req.understanding.consistent — Inconsistent assessments fail the run

The understand Operation SHALL end a run `failed` when the assessment lists Spec gaps although it is
sufficient or none although it is insufficient, carries a plan that was not requested or follows an
insufficient Spec, carries no plan although one was requested and the Spec is sufficient, has no
entry or more than one for a bound Module, or has an entry for a Module that is not bound.

Each inconsistency is returned as host evidence. The run is not resumed to repair it.

## Effects

### req.understanding.no-writes — The worker may write nothing

The understand Operation SHALL run its worker under a grant with no writable path.

The worker has no editing or shell tool.

### req.understanding.change-fails — A change to the worktree fails the run

The understand Operation SHALL end a run `failed` when the
[write audit](../../glossary.json#concept.write-audit) finds any violation in the worktree the
run works on, such as a changed, new or deleted file.

The changed paths are returned as host evidence and the change is left in place for the
caller, never reverted. The run's own
[run progress file](../../glossary.json#concept.run-progress-file) and
[run result](../../glossary.json#concept.run-result), and its worker's
[progress file](../../glossary.json#concept.progress-file) and
[run record](../../glossary.json#concept.run-record), are written into the
[run store](../../glossary.json#concept.run-store), which Git ignores; they are not changes the
audit judges.

### req.understanding.single-round — No resume rounds

The understand Operation SHALL NOT resume the worker after it has returned its result.

## Plan review

### req.understanding.plan-review-bound — A plan is reviewed in its workspace

The `plan_review` Operation SHALL brief its reviewer with the goal of the workspace whose
[workspace binding](../../glossary.json#concept.workspace-binding) lies in the worktree the run
starts in.

A worktree without a binding has no goal to review the plan against, so the run is refused there.

### req.understanding.plan-review-kept — The reviewed plan is kept

The `plan_review` Operation SHALL keep an exact copy of the plan file it reviews in the run's
[trace node](../../glossary.json#concept.trace-node) and return that copy's path and the
digest of its bytes in the report.

A plan file that is missing, unreadable, not UTF-8 text or empty ends the run `failed` with
`plan_unreadable` before any worker launches.

### req.understanding.plan-review-read-only — The reviewer reads Specs and code and writes nothing

The `plan_review` Operation SHALL run one reviewer, [worker id](../../glossary.json#concept.worker-id)
`reviewer`, under the bound Modules' `review-code` [grant](../../glossary.json#concept.grant),
with no writable path, no [configured check](../../glossary.json#concept.configured-check) and no
[resume round](../../glossary.json#concept.resume-round).

Any violation the [write audit](../../glossary.json#concept.write-audit) finds ends the run
`failed`, with the changed paths as host evidence.

### req.understanding.plan-review-answers — Every previous finding is answered once

The `plan_review` Operation SHALL end the run `failed` with `iteration_mismatch`, before any worker
launches, when more than one admitted input is a `plan_review` run, when a finding of the admitted
`plan_review` input is not answered exactly once by `--accept` or `--reject`, when an answer names
no finding of it, or when an answer is given without such an input.

Every problem is listed in the error. The admitted inputs of other Operations are material for the
reviewer and need no answer.

### req.understanding.plan-review-responses — The reviewer answers the previous iteration

The `plan_review` Operation SHALL end the run `failed` with `inconsistent_review` when two of the
reviewer's findings have the same id, when the
reviewer's responses are not exactly one per finding of the previous iteration, when a maintained
finding is not restated by exactly one finding, when a finding restates a finding that is not
maintained, or when a finding names a Module that is not bound.

### req.understanding.plan-review-basis — Bases resolve

The `plan_review` Operation SHALL end the run `failed` with `unresolved_basis` when a finding's
basis does not resolve in the bound Modules' [Spec context](../../glossary.json#concept.spec-context)
or a `violation` finding has no basis.

### req.understanding.plan-review-verdict — The verdict follows the findings

The `plan_review` Operation SHALL set the verdict of an `ok` report to `changes_required` exactly
when one of its findings is blocking and to `accepted` otherwise.

The Operation never changes, drops or adds a finding or a response.
