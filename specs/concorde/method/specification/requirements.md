# Specification requirements

The Module-wide obligations of [Specification](module.md). The
[Spec change](../../glossary.json#concept.spec-change)'s shape is in the
[contracts](contracts.md). The [scenarios](scenarios.md) show the obligations in concrete situations.

## Writing

### req.specification.own-documents — Only the bound Modules' documents are writable

The specify worker's grant SHALL make writable exactly the documents the bound Modules own, both
reading files and metadata, and the project glossary, and nothing else.

The glossary is writable as a whole file. For every glossary entry a worker run added, changed or
removed whose owner before or after is not a bound Module, the run ends `failed` with
`audit_violation`, like a [write audit](../../glossary.json#concept.write-audit) violation. This
holds after every round the round validation checks and once more after each worker run, whatever its
status, before any document is created or another worker launched, as
[Method's workers](../workers.md#the-round-validation) define the check.

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

When both of these conditions hold, a specify run SHALL end `blocked` with the new findings as
evidence:

- Its worker ended `ok`.
- After the last repair round, validation still reports an error the baseline did not have.

Errors present in the baseline are reported as pre-existing. They do not stop the run. Thus, a
specify run can repair [Specs](../../glossary.json#concept.spec) that were already broken. When the worker
itself ended `blocked` or `failed`, the run keeps the worker's status. In that case, its new errors
appear in the Spec change's validation findings.

### req.specification.no-resume — Resumed only to repair its own errors

The specify Operation SHALL resume the worker only with the structural errors its change
introduced, validated against the registry as step 6 would regenerate it from the entries.

A mirror left stale by the worker's edit and a finding located in Concorde's own records under
`.concorde/` are never given to the worker, since it cannot write them.

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
- It is a canonical project-relative path of a Markdown file.
- It lies in the folder of that Module's entry or below it.
- No component of its path or its metadata path is a symbolic link.
- Nothing exists at its path or its metadata path, not even a dangling symbolic link.
- It is proposed only once.
- The metadata of its Module's entry can be read and has an `owns` list.

A document is created as a minimal stub. Its reading file holds a title heading named after the
file and one line that links to its Module's entry by a relative path. Its metadata names its
identity, owner and role and defines and relates nothing. It is registered in its Module's `owns`,
so that the second worker's grant makes it writable. The Operation writes nothing else into it.
The second worker writes its content. Since the change needs all of them, one refused proposal
refuses the whole list. Every proposal is checked before anything is
written, so that no document is created twice and no refusal leaves a partial creation.

### req.specification.creation-transaction — Created documents are written in one file transaction

The specify Operation SHALL write the created documents, their metadata and the changed entry
metadata in one Spec core [file transaction](../../glossary.json#concept.file-transaction) that
refuses a symbolic link at any path component.

When the transaction fails, every file it wrote is restored. The run then stays `blocked` with
`document-creation-failed` evidence, and steps 6–9 still run.

### req.specification.document-identities — Created documents get unique identities

The specify Operation SHALL give each created document a valid document identity that no existing
document and no other created document has.

### req.specification.one-relaunch — Created documents are filled by one more worker

The specify Operation SHALL launch at most one further worker per run, briefed with every document
it created.

## Result

### req.specification.observed-facts — The result reports what the Operation observed

The specify Operation SHALL compute the following fields of the Spec change from the workspace,
never from the worker's result:

- The changed documents.
- The affected Modules.
- The validation findings.

### req.specification.observed-baseline — The observed change spans the whole run

The specify Operation SHALL compare the workspace after its last worker launch and its own writes
with the workspace as it was before that run's first worker launch.

The changed documents are every path that any round's
[write audit](../../glossary.json#concept.write-audit) of either worker launch found changed, and
every file the Operation wrote. Each launch's audit compares with the worktree just before that
launch, so the two lists together cover the whole run. An uncommitted edit made before the run and
left unchanged by it is not listed. A path the run changed and then changed back is still listed,
since it changed during the run. The affected Modules compare the Specs loaded for the baseline,
before the first launch, with the Specs after the run.

### req.specification.glossary-affects — A changed glossary entry affects its Modules

The specify Operation SHALL list among the affected Modules every Module whose Spec context, before
or after the change, carries a glossary entry the change added, changed or removed, and the owner of
each such entry before or after the change.

A [Spec context](../../glossary.json#concept.spec-context) holds the glossary entries of its terms
as well as its documents. So a glossary-only change affects the Modules that read the changed
entries, as [scenario.specification.glossary-change](scenarios.md#scenario.specification.glossary-change)
shows. When the Specs after the change do not load, no entry is known to have changed.
