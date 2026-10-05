# General work requirements

The Module-wide obligations of [General work](module.md). The result's shape is in the
[contracts](contracts.md). The [scenarios](scenarios.md) show the obligations in concrete
situations.

## The work

### req.general-work.grant-by-type — The named task type bounds the worker

The `general` [Operation](../../glossary.json#concept.operation) SHALL launch its worker under the
[grant](../../glossary.json#concept.grant) that the
[task type](../../glossary.json#concept.task-type) `--type` names assigns to the run's
[Modules](../../glossary.json#concept.module).

The grant comes from the [Specs](../../glossary.json#concept.spec) of the worktree the run works on,
through Method's [standard worker sequence](../../glossary.json#concept.standard-worker-sequence). A
write outside it fails the run like any other worker's.

### req.general-work.read-only — Writes are withheld on request

With `--read-only`, the `general` Operation SHALL lower every writable level of the worker's grant
to read.

### req.general-work.unbound-reads — An unbound run only reads

An [unbound run](../../glossary.json#concept.unbound-run) of `general` SHALL launch no worker
whose grant makes a path writable.

Such a run of a type that writes, without `--read-only`, fails with `unbound_write` before any
worker launches.

### req.general-work.instruction-kept — The instruction is kept exactly

The `general` Operation SHALL keep an exact copy of the instruction in the run's
[trace node](../../glossary.json#concept.trace-node), with its digest in the result.

### req.general-work.instruction-in-brief — The instruction is task context

The `general` Operation SHALL give the instruction to the worker in its
[brief](../../glossary.json#concept.brief), after the Operation's own worker prompt.

The instruction never replaces the system prompt or the rules of the boundary that the worker
harness gives every worker.

### req.general-work.change-observed — The host observes the change

The `general` Operation SHALL report the change from Git trees of the worktree that it records
before the worker launches and after the worker ends, never from the worker's account.

## The review

### req.general-work.independent-review — A second worker reviews every result

When the worker ends `ok` and its audit is clean, the `general` Operation SHALL launch the
reviewer as a separate worker, which shares no session with the worker.

### req.general-work.reviewer-reads-only — The reviewer changes nothing

The `general` Operation SHALL launch the reviewer under the same task type's grant with every
writable level lowered to read.

### req.general-work.review-material — The reviewer sees the instruction and the change

The `general` Operation SHALL give the reviewer the instruction, the observed change, the earlier
content of every changed file and the worker's answer, marked as a claim to check.

### req.general-work.verdict — The verdict follows the findings

The `general` Operation SHALL set the verdict to `changes_required` exactly when a finding of the
review is blocking, and to `accepted` otherwise.

A verdict of either value is an `ok` run. Acting on a finding is the caller's decision.

### req.general-work.no-review-without-work — No review follows a failed worker

When the worker does not end `ok`, the `general` Operation SHALL end the run with the worker's
status without launching the reviewer.
