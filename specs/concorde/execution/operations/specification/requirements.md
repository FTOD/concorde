# Specification requirements

The Module-wide obligations of [Specification](module.md). The Spec change's shape is in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations in concrete
situations.

## Writing

### req.specification.own-documents — Only the bound Modules' documents are writable

The specify worker's grant SHALL make writable exactly the documents the bound Modules own, both
reading files and metadata, and nothing else.

### req.specification.no-code — Code is known by name only

The specify worker's grant SHALL NOT give read or write access to the contents of any
implementation file.

### req.specification.declare-not-create — Declared files are not created

The specify Operation SHALL leave every pending entry it declares absent from the workspace.

Creating a declared file is the work of an `implement` run, whose worker sequence pre-creates it.

### req.specification.audit — Writes outside the grant fail the run

A specify run whose write audit finds a change outside the grant's writable paths SHALL end
`failed` with the offending paths as host evidence.

## Reconciliation and validation

### req.specification.registry-mirror — Only mirrored fields are regenerated

The specify Operation SHALL reconcile the project registry only by regenerating the mirrored fields of
Modules that already exist in it.

### req.specification.validate-after — Every change is validated

The specify Operation SHALL run the structural checks on the workspace after every worker round that
changed a document.

### req.specification.stop-on-new-error — New structural errors stop the run

A specify run whose validation still reports an error the baseline did not have after the last
repair round SHALL end `blocked` with the new findings as evidence.

Errors present in the baseline are reported as pre-existing and do not stop the run, so a specify
run can repair Specs that were already broken.

### req.specification.no-resume — Resumed only to repair its own errors

The specify Operation SHALL resume the worker only with the structural errors its change introduced, and at most twice.

A worker that ends `blocked` or `failed`, or whose change introduced no new error, is not resumed.

### req.specification.created-documents — Needed documents are created, once

The specify Operation SHALL create a document a `blocked` worker proposes only when it belongs to a bound Module, lies in the folder of that Module's entry and does not exist, and then launch a worker for it at most once per run.

A document is created empty and registered in its Module's `owns`, so that the second worker's
grant makes it writable; the Operation writes nothing else into it.

## Result

### req.specification.observed-facts — The result reports what the Operation observed

The Spec change's changed documents, declared pending entries, affected Modules and validation
findings SHALL be computed by the Operation from the workspace, never taken from the worker's
result.
