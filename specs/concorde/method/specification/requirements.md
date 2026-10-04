# Specification requirements

The Module-wide obligations of [Specification](module.md). The
[Spec change](../../glossary.json#concept.spec-change)'s shape is in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations in concrete
situations.

## Writing

### req.specification.own-documents — Only the bound Modules' documents are writable

The specify worker's grant SHALL make writable exactly the documents the bound Modules own, both
reading files and metadata, and the project glossary, and nothing else.

The glossary is writable as a whole file; the
[write audit](../../glossary.json#concept.write-audit) reports as a violation every glossary
entry a round changed whose owner is not a bound Module.

### req.specification.no-code — Code is known by name only

The specify worker's grant SHALL NOT give read or write access to the contents of any
implementation file.

### req.specification.no-implementation-files — Implementation files are neither created nor changed

The specify [Operation](../../glossary.json#concept.operation) SHALL NOT create, change or delete
any implementation file.

A new implementation file is created and bound by the task level before the run that fills it.

### req.specification.audit — Writes outside the grant fail the run

A specify run whose [write audit](../../glossary.json#concept.write-audit) finds a change outside
the grant's writable paths SHALL end `failed` with the offending paths as host evidence.

### req.specification.deletions — Only proposed owned documents are deleted

The specify Operation SHALL delete a file only when the worker's result proposes it, the file lies
inside the grant's writable paths and the audit was clean.

## Reconciliation and validation

### req.specification.registry-mirror — Only mirrored fields are regenerated

The specify Operation SHALL reconcile the project registry only by regenerating the mirrored fields
of Modules that already exist in it.

### req.specification.validate-after — Every change is validated

The specify Operation SHALL run the
[structural checks](../../glossary.json#concept.structural-check) on the workspace after every
worker round that ended `ok` with a clean write audit, and once more after the last worker round
unless a write audit found a violation.

### req.specification.stop-on-new-error — New structural errors stop the run

A specify run whose worker ended `ok` and whose validation still reports an error the baseline did
not have after the last repair round SHALL end `blocked` with the new findings as evidence.

Errors present in the baseline are reported as pre-existing and do not stop the run, so a specify
run can repair [Specs](../../glossary.json#concept.spec) that were already broken. When the worker itself ended `blocked` or `failed`,
the run keeps the worker's status and its new errors appear in the Spec change's validation
findings.

### req.specification.no-resume — Resumed only to repair its own errors

The specify Operation SHALL resume the worker only with the structural errors its change
introduced.

A worker that ends `blocked` or `failed`, or whose change introduced no new error, is not resumed.

### req.specification.resume-limit — At most two repair rounds per worker

The specify Operation SHALL resume each worker it launches at most twice.

The second worker launched to fill created documents has its own two repair rounds.

### req.specification.created-documents — Needed documents are created, once

The specify Operation SHALL create the documents a `blocked` worker proposes only when every one of
them belongs to a bound [Module](../../glossary.json#concept.module), lies in the folder of that
Module's entry and does not exist.

A document is created empty and registered in its Module's `owns`, so that the second worker's
grant makes it writable; the Operation writes nothing else into it. One refused proposal refuses
the whole list, since the change needs all of them.

### req.specification.one-relaunch — Created documents are filled by one more worker

The specify Operation SHALL launch at most one further worker per run, briefed with every document
it created.

## Result

### req.specification.observed-facts — The result reports what the Operation observed

The Spec change's changed documents, affected Modules and validation findings SHALL be computed by the Operation from the workspace, never taken from the worker's
result.
