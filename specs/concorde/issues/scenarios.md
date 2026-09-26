# Issues scenarios

Concrete situations that show the [requirements](requirements.md) at work. Shapes and error codes
are defined in the [Issue interface](interface.md).

## Recording through the command

### scenario.issues.command-report — Record a report from a file

- GIVEN an initialized project and a report file naming a registered owner and existing evidence
- WHEN the main agent runs `report --file` with that file and a task identity
- THEN a new open Issue holds exactly that report
- AND its provenance names `main-agent`, `issues`, `report`, the owner as reporting Module, the registry digest, the task and the Git `HEAD` or `null` outside a Git repository
- AND the command prints the receipt and the revision that `show` reports for the Issue

This illustrates [command attribution](requirements.md#req.issues.main-agent-actor) and the
[initial status](requirements.md#req.issues.status-derived).

### scenario.issues.command-report-repeated — Repeating a creation makes another Issue

- GIVEN an initialized project and a valid report file without an Issue identity or expected revision
- WHEN the main agent runs `report --file` twice with that same file
- THEN the commands return different Issue identities because they supply different invocation identities
- AND both Issues are open with one report each
- BUT matching report keys across CLI invocations do not deduplicate the records

### scenario.issues.command-report-origin — Record a report seen in another project

- GIVEN an initialized project and a report file written in another project, naming that project as its `origin`, evidence paths relative to it and an error chain
- WHEN the main agent runs `report --file` with that file
- THEN the Issue holds the report with its origin and error chain unchanged, and its provenance is this project's
- BUT a report whose evidence is absent from the origin project is refused with `missing_evidence` naming the origin project
- AND a report whose error chain breaks the Framework's error contract is refused with `invalid_issue` naming the field
- AND nothing is written for either

### scenario.issues.command-report-check — Check a report without recording it

- GIVEN an initialized project and a report file
- WHEN the main agent runs `report --file` with that file and `--check`
- THEN a report that passes every check of `report` is answered with `valid`, its report key and reporting Module
- AND a report that fails one is refused exactly as `report` would refuse it, with the code and field
- BUT no Issue is recorded either way

### scenario.issues.command-report-unknown-owner — A report without an owner is filed under the root Module

- GIVEN a registry with one root Module and a report file whose owner is `null`
- WHEN the main agent runs `report --file` with that file
- THEN the Issue is recorded with owner `null` and the root Module as reporting Module
- AND the store check passes

### scenario.issues.command-append — Append a later observation from a file

- GIVEN an open Issue and a report file naming it with its current revision
- WHEN the main agent runs `report --file` with that file
- THEN the Issue holds both reports and the command prints the new revision
- AND its status stays open while its summary follows the latest report's title, classification and owner
- BUT a report file naming the old revision is refused with `stale_issue`, naming the Issue and both revisions
- AND nothing is written for it

### scenario.issues.command-close — Close an Issue with evidence

- GIVEN an open Issue
- WHEN the main agent runs `close` with a reason, a note and evidence items, or with `duplicate` and another open Issue
- THEN the Issue is closed with a disposition whose actor is `main-agent`
- AND the command prints the Issue, its status and its new revision
- BUT a duplicate naming a closed Issue is refused and the Issue stays open

This illustrates [command attribution](requirements.md#req.issues.main-agent-actor) and
[legal transitions](requirements.md#req.issues.legal-transitions).

### scenario.issues.command-reopen — Reopen a closed Issue

- GIVEN a closed Issue
- WHEN the main agent runs `reopen` with a note and evidence items
- THEN the Issue is open again with every report unchanged
- AND the command prints its status and new revision

### scenario.issues.command-usage — An unusable request exits with status 2

- GIVEN a missing argument, an unknown reason, a `duplicate` without `--duplicate-of`, a blank note, a repeated evidence item, an unreadable report file or a directory that is not a Concorde project
- WHEN the command runs
- THEN it prints an error code and a message naming the argument, file or directory
- AND exits with status 2
- BUT writes nothing

### scenario.issues.command-refused — A refused request exits with status 1

- GIVEN a report file with an invalid field, an unregistered owner, missing evidence or half of an append, or an unknown, malformed, open or closed Issue for an action that needs the other state, or an Issue named as its own duplicate
- WHEN the command runs
- THEN it prints the error code and a message naming the report file and field or the Issue
- AND exits with status 1
- BUT writes nothing

## Records

### scenario.issues.store-report — Save a report once

- GIVEN caller-supplied provenance and a classified report
- WHEN the store saves it and then saves the identical report again
- THEN exactly one Issue with one report exists
- AND both calls return the same receipt
- AND the receipt resolves to exactly that report

### scenario.issues.store-empty — Listing without Issues creates nothing

- GIVEN a project without an Issue directory
- WHEN the Issues are listed
- THEN the list is empty
- BUT no directory is created

### scenario.issues.store-key-conflict — A reused key with other content is refused

- GIVEN an accepted report of one invocation and key
- WHEN the same invocation submits different content under the same key
- THEN the store refuses with `issue_key_conflict`
- BUT the accepted report is unchanged

### scenario.issues.store-append — Append a later observation

- GIVEN an open Issue and its current revision
- WHEN a new report appends to it with that revision and a different classification
- THEN the Issue holds both reports and is listed with the new classification
- BUT the first report is unchanged
- AND a later append naming the old revision is refused with `stale_issue`

### scenario.issues.store-concurrency — Concurrent writers never lose a report

- GIVEN several reports, some of them repeated, submitted concurrently to one worktree
- WHEN the store accepts them
- THEN every distinct report is saved exactly once
- BUT no accepted report is lost or duplicated

### scenario.issues.branch-local — Each worktree keeps its own copy

- GIVEN an Issue recorded in one worktree and the same record copied into another, as a branch copy is
- WHEN the Issue is closed in the second worktree
- THEN the second worktree's copy is closed
- BUT the first worktree's copy stays open

### scenario.issues.store-disposition — Close with evidence

- GIVEN an open Issue and its current revision
- WHEN the store receives a disposition with a note, evidence and actor, or a duplicate disposition naming another open Issue
- THEN the Issue gets the disposition and its status follows it
- AND every report stays unchanged
- AND a later reopening at the new revision opens it again

### scenario.issues.store-status-mismatch — A status cannot contradict its history

- GIVEN an Issue record whose status is `closed` but whose disposition history is empty
- WHEN the store reads that record
- THEN it refuses the record with `invalid_issue` because an empty history leaves the Issue open
- BUT it does not repair the status or invent a closing disposition

This illustrates [status derived from history](requirements.md#req.issues.status-derived).

### scenario.issues.store-disposition-stale — A disposition over a changed record is refused

- GIVEN an Issue, or the Issue it would duplicate, whose record changed after its revision was read
- WHEN a disposition names the old revision
- THEN the store refuses with `stale_issue`
- BUT the record is unchanged

### scenario.issues.store-disposition-invalid — An invalid disposition is refused

- GIVEN an Issue and its current revision
- WHEN a disposition has no evidence or names the Issue itself as its duplicate
- THEN the store refuses it
- BUT the record is unchanged

### scenario.issues.store-boundary — Refuse malformed or unsafe records

- GIVEN a malformed report, an unsafe evidence path, an Issue directory that is a symbolic link, a corrupted report digest or a failed file publication
- WHEN the store tries to accept, save or read it
- THEN it does not report success
- AND existing valid records stay readable and unchanged

## The store check

### scenario.issues.store-check-pass — Valid records pass the store check

- GIVEN a project without an Issue directory, or whose Issues are valid and owned by registered Modules
- WHEN the configured store check runs
- THEN it reports no errors and no notes
- AND exits with status zero

### scenario.issues.store-check-invalid — The store check fails for an invalid record

- GIVEN a project whose Issue directory holds a malformed record, a stray file or a misnamed record
- WHEN the configured store check runs
- THEN it reports one error naming each of them
- AND exits with a nonzero status

### scenario.issues.store-check-unknown-owner — The store check reports an unknown owner

- GIVEN an open Issue whose owner is not a registered Module
- WHEN the configured store check runs
- THEN it reports an error naming the Issue and the unknown owner
- AND exits with a nonzero status

### scenario.issues.store-check-closed-unknown-owner — A closed Issue of a removed Module does not fail

- GIVEN a closed Issue whose owner is not a registered Module, and no other problem
- WHEN the configured store check runs
- THEN it reports a note naming the Issue and the unknown owner
- BUT exits with status zero
