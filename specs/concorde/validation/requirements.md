# Validation requirements

These are the Module-wide obligations of [Validation](module.md). The request, flow and gate table
they refer to are in [Validation interface](records.md).

## Evidence

### req.validation.checks-through-runner — Check results come only from Check execution

Validation SHALL record only check results that Check execution's configured-check runner returned
for the current request.

Validation never runs a configured command itself and never copies a result from another request,
worktree or change. The runner's own guarantees, such as the read-only check boundary and the
refusal of a check that changed what it measured, are Check execution's.

### req.validation.affected-modules — Every affected Module is checked

Validation SHALL run the configured checks of every affected Module of the validated Module, and of
every Module in the project for a direct candidate.

The affected Modules include every edited Module when the validated Module is the one the change is
about; each of them brings every Module binding one of its files.

### req.validation.confirm-pending — Created pending files are confirmed before validating

Validation SHALL remove each realization entry whose file or directory exists from that
realization's `pending` list before it validates the Specs.

The change is limited to the `pending` lists in document metadata, written as one transaction bound
to the digests of the metadata members it replaces. Entries whose files do not exist stay pending,
and every entry stays in the realization's `entries`.

### req.validation.current-evidence — Ready rests on evidence for the current bytes

Validation SHALL record a change as ready only from evidence bound to digests of the candidate's
current files.

A check result whose measured-input digest no longer matches, Spec validation whose source digest
changed, an implementation revision that changed after the tasks completed, or a candidate tree
that changed while validation ran all count as missing evidence and are reported as
`stale_evidence`.

## Readiness

### req.validation.completion-gates — Ready requires every gate of the change

Validation SHALL NOT record a change as ready unless the completion check passes for the validated
Module.

The gate table lists every condition. Omitting checks with `run_checks: false` never satisfies a
gate that needs them.

### req.validation.failure-blocks — A failed validation marks the change blocked

Validation SHALL mark the change `blocked` whenever it answers `failed`.

The change's outcome is `invalid_spec` or `failed_checks`; a planned target's progress entry is
marked `blocked` as well. A direct candidate has no progress entry, so only the change is marked.

### req.validation.existing-change — Validation never creates a change

Validation SHALL NOT create a change or a candidate worktree.

A request without an existing change to validate is refused with `missing_change`.

### req.validation.deterministic — Validation runs no model

Validation SHALL decide readiness without starting any worker or model.

It also repairs nothing and delivers nothing; those are separate requests of the user session.

### req.validation.no-semantic-claim — Structural success is not semantic completeness

Validation SHALL NOT present structural success, passing checks or scenario coverage as proof of
semantic completeness.
