# Validation requirements

These are the Module-wide obligations of [Validation](module.md). The exact records and digests
they refer to are in [Validation records](records.md).

## Checks

### req.validation.check-isolation — Configured checks cannot write the project

Validation SHALL run configured checks only through Check execution's sandbox, which denies the
check and its descendants every write in the project.

The rule covers listed and unlisted files, ignored caches, `.concorde/runs/` and the change status
records, and it includes writes that are later undone. Only the Host outside the sandbox writes the
check log. There is no option to disable the sandbox and no fallback to an unrestricted run.

### req.validation.affected-modules — Shared files are checked for every Module that binds them

Validation SHALL run the configured checks of every Module that binds a file the validated Module
binds, of every Module the candidate edits when the validated Module is the one the change is
about, and of every Module in the project for a direct candidate.

A Module the candidate edits owns a Spec document member, or binds a file, that differs from the
change's starting commit. Each of them brings every Module binding one of its files, as the
validated Module does.

### req.validation.deterministic — Validation runs no model

Validation SHALL decide readiness without starting any worker or model.

It also repairs nothing and delivers nothing; those are separate requests of the user session.

### req.validation.confirm-pending — Created pending files are confirmed before validating

In a candidate, Validation SHALL remove each realization entry whose file or directory exists from
that realization's `pending` list before it validates the Specs.

The change is limited to the `pending` lists in document metadata, written as one transaction bound
to the digests of the metadata members it replaces. It is refused with `stale_proposal` when any
other Spec source or the registry changed meanwhile. Entries whose files do not exist stay pending,
and every entry stays in the realization's `entries`.

## Readiness

### req.validation.current-evidence — Ready rests on evidence for the current bytes

Validation SHALL record a candidate as ready only from evidence bound to digests of the candidate's
current files.

A check result whose input digest no longer matches, Spec validation whose source digest changed,
an implementation revision that changed after the tasks completed, or a candidate tree that changed
while validation ran all count as missing evidence. Validation reports them as `stale_evidence`
instead of recording a result.

### req.validation.completion-gates — Ready requires every gate of the change

Validation SHALL NOT record a candidate as ready while an accepted task of the validated Module is
incomplete, a required review is not current, a required check is missing, failed or stale, or an
open blocker exists for the validated task.

Omitting checks with `run_checks: false` does not satisfy a gate that needs them. For a direct
candidate the recorded validation must match the requested Module, focus, task and constraints, and
every configured check of the project must have passed for its current inputs. For a planned change,
every recorded component must pass the same completion check with its own task, and its Spec and
implementation revisions must equal those recorded when it completed.

### req.validation.no-semantic-claim — Structural success is not semantic completeness

Validation SHALL NOT present structural success, passing checks or scenario coverage as proof of
semantic completeness.
