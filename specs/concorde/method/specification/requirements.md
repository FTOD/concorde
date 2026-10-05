# Specification requirements

The Module-wide obligations of [Specification](module.md). The
[Spec change](../../glossary.json#concept.spec-change)'s shape is in the
[contracts](contracts.md). The [scenarios](scenarios.md) show the obligations in concrete situations.

## Writing

### req.specification.own-documents — Only the bound Modules' documents are writable

The specify worker's grant SHALL make writable exactly the documents the bound Modules own, both
reading files and metadata, and the project glossary, and nothing else.

The glossary is writable as a whole file. For every glossary entry a round changed whose owner is
not a bound Module, the [write audit](../../glossary.json#concept.write-audit) reports a violation.

### req.specification.no-code — Code is known by name only

The specify worker's grant SHALL NOT give read or write access to the contents of any
implementation file.

### req.specification.no-implementation-files — Implementation files are neither created nor changed

The specify [Operation](../../glossary.json#concept.operation) SHALL NOT create, change or delete
any implementation file.

A new implementation file is created and bound by the task level before the run that fills it.

### req.specification.audit — Writes outside the grant fail the run

When its [write audit](../../glossary.json#concept.write-audit) finds a change outside the grant's
writable paths, a specify run SHALL end `failed` with the offending paths as host evidence.

### req.specification.deletions — Only proposed owned documents are deleted

The specify Operation SHALL delete a file only when all of these conditions hold:

- The worker's result proposes it.
- The file lies inside the grant's writable paths.
- The audit was clean.

## Reconciliation and validation

### req.specification.registry-mirror — Only mirrored fields are regenerated

The specify Operation SHALL reconcile the project registry only by regenerating the mirrored fields
of Modules that already exist in it.

### req.specification.validate-after — Every change is validated

The specify Operation SHALL run the [structural checks](../../glossary.json#concept.structural-check)
on the workspace at these times:

- After every worker round that ended `ok` with a clean write audit.
- Unless a write audit found a violation, once more after the last worker round.

### req.specification.stop-on-new-error — New structural errors stop the run

A specify run SHALL end `blocked` with the new findings as evidence when both of these conditions
hold:

- Its worker ended `ok`.
- After the last repair round, validation still reports an error the baseline did not have.

Errors present in the baseline are reported as pre-existing. They do not stop the run. Thus, a
specify run can repair [Specs](../../glossary.json#concept.spec) that were already broken. When the worker
itself ended `blocked` or `failed`, the run keeps the worker's status. In that case, its new errors
appear in the Spec change's validation findings.

### req.specification.no-resume — Resumed only to repair its own errors

The specify Operation SHALL resume the worker only with the structural errors its change
introduced.

The worker is not resumed in any of these cases:

- The worker ends `blocked`.
- The worker ends `failed`.
- The worker's change introduced no new error.

### req.specification.resume-limit — At most two repair rounds per worker

The specify Operation SHALL resume each worker it launches at most twice.

The second worker launched to fill created documents has its own two repair rounds.

### req.specification.created-documents — Needed documents are created, once

The specify Operation SHALL create the documents a `blocked` worker proposes only when every one
of them meets all of these conditions:

- It belongs to a bound [Module](../../glossary.json#concept.module).
- It lies in the folder of that Module's entry or below it.
- It does not exist.
- It is proposed only once.

A document is created empty. It is registered in its Module's `owns`, so that the second worker's
grant makes it writable. The Operation writes nothing else into it. Since the change needs all of
them, one refused proposal refuses the whole list. Before anything is written, a path proposed more
than once is refused, so that no document is created twice.

### req.specification.one-relaunch — Created documents are filled by one more worker

The specify Operation SHALL launch at most one further worker per run, briefed with every document
it created.

## Result

### req.specification.observed-facts — The result reports what the Operation observed

The Spec change's changed documents, affected Modules and validation findings SHALL be computed by
the Operation from the workspace, never taken from the worker's result.
