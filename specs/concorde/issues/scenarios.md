# Issues scenarios

Concrete situations that show the [requirements](requirements.md) at work. Shapes and error codes
are defined in the [Issue interface](interface.md).

## Reporting

### scenario.issues.report-unknown-owner — A reporter that does not know the owner says so

- GIVEN a reporting service bound with admitted owners and evidence paths for one reporter
- WHEN the reporter submits one report naming no owner and another naming an admitted owner
- THEN both reports are saved as Issues
- AND the service keeps both receipts

### scenario.issues.report-authority — A report outside the reporter's limits is refused

- GIVEN a reporting service bound with admitted owners, evidence paths and selected Issues
- WHEN the reporter names an owner or evidence path outside them, supplies its own provenance, or appends to an Issue neither selected nor created earlier by the same service
- THEN the report is refused
- BUT nothing is written

### scenario.issues.report-append — A reporter appends to an Issue it was given

- GIVEN an open Issue and a reporting service bound with that Issue among its selected Issues
- WHEN the reporter appends a report at the Issue's current revision
- THEN the report is added to that Issue
- AND the service answers with the receipt and the record's new revision

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
