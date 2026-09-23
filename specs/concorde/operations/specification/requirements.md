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

The specify Operation SHALL leave every pending entry it declares absent from the task worktree.

Creating a declared file is the work of an `implement` run, whose host pre-creates it.

### req.specification.audit — Writes outside the grant fail the run

A specify run whose write audit finds a change outside the grant's writable paths SHALL end
`failed` with the offending paths as host evidence.

## Reconciliation and validation

### req.specification.registry-mirror — Only mirrored fields are regenerated

The specify host SHALL reconcile the project registry only by regenerating the mirrored fields of
Modules that already exist in it.

### req.specification.validate-after — Every change is validated

The specify host SHALL run the structural checks on the task worktree after every worker run that
changed a document.

### req.specification.stop-on-new-error — New structural errors stop the run

A specify run whose validation reports an error the baseline did not have SHALL end `blocked` with
the new findings as evidence and without resuming the worker.

Errors present in the baseline are reported as pre-existing and do not stop the run, so a specify
run can repair Specs that were already broken.

### req.specification.no-resume — No automatic resume

The specify host SHALL NOT resume the worker after it has returned its result.

## Result

### req.specification.observed-facts — The result reports what the host observed

The Spec change's changed documents, declared pending entries, affected Modules and validation
findings SHALL be computed by the host from the task worktree, never taken from the worker's
result.
