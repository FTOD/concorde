# Issues scenarios

Concrete situations that show the [requirements](requirements.md) at work. Shapes and error codes
are defined in the [Issue interface](interface.md).

## Reporting

### scenario.issues.report-independent — Report without ending the task

- GIVEN a worker whose call has the `report_issue` tool
- WHEN it reports one or more problems and then submits its result
- THEN each report is saved and acknowledged while the worker keeps running
- AND the worker's task completes with its own outcome
- BUT the reports neither stop the worker nor start a repair

### scenario.issues.report-provenance — A report is saved with its caller's provenance

- GIVEN a reporting service bound with provenance and limits for one reporter
- WHEN the reporter submits a report naming an admitted owner and admitted evidence
- THEN the store saves the report with the provenance the caller supplied
- AND answers with a receipt and the record's current revision

### scenario.issues.report-authority — A report outside the reporter's limits is refused

- GIVEN a reporting service bound with admitted owners, evidence paths and selected Issues
- WHEN the reporter names an owner or evidence path outside them, or appends to an Issue neither selected nor created earlier by the same service
- THEN the report is refused with `permission_denied`
- BUT nothing is written

### scenario.issues.report-survives-failure — Keep reports from a failed call

- GIVEN a reporter whose report the store has acknowledged
- WHEN the reporter later submits an invalid result, fails, times out or is cancelled
- THEN the report stays saved

### scenario.issues.reference — A result cannot reference an unknown report

- GIVEN a reporter that reported some problems and may have received admitted receipts as input
- WHEN its result references a report it neither made through its service nor received
- THEN the reference check fails with `permission_denied`
- BUT the reports already saved are kept

### scenario.issues.reference-repeated — A result cannot reference a report twice

- GIVEN a reporter that made one report
- WHEN its result references that report twice
- THEN the reference check fails with `invalid_completion`

### scenario.issues.blocker-independent — Dispositions and Blockers do not touch each other

- GIVEN an Issue whose report a recorded Blocker references
- WHEN the Issue is closed with a disposition
- THEN the store changes only the Issue record
- BUT the Blocker is not released by the store

## Records

### scenario.issues.store-report — Save a report once

- GIVEN Host-issued provenance and a classified report
- WHEN the store saves it and then saves the identical report again
- THEN exactly one Issue with one report exists
- AND both calls return the same receipt

### scenario.issues.store-append — Append a later observation

- GIVEN an open Issue and its current revision
- WHEN a new report appends to it with that revision and a different classification
- THEN the Issue holds both reports
- BUT the first report is unchanged

### scenario.issues.store-key-conflict — A reused key with other content is refused

- GIVEN an accepted report of one invocation and key
- WHEN the same invocation submits different content under the same key
- THEN the store refuses with `issue_key_conflict`
- BUT the accepted report is unchanged

### scenario.issues.store-empty — Listing without Issues creates nothing

- GIVEN a project without an Issue directory
- WHEN the Issues are listed
- THEN the list is empty
- BUT no directory is created

### scenario.issues.store-concurrency — Concurrent writers never lose a report

- GIVEN several reports submitted concurrently from worktrees of one repository
- WHEN the store accepts them
- THEN every accepted report is saved exactly once
- BUT no accepted report is lost or duplicated

### scenario.issues.branch-local — Each worktree keeps its own copy

- GIVEN an Issue committed on the primary branch and a candidate created from it
- WHEN the Issue is closed in the candidate
- THEN the candidate's copy is closed
- BUT the primary worktree's copy stays open until the candidate's branch is merged

### scenario.issues.store-disposition — Close with evidence

- GIVEN an open Issue and its current revision
- WHEN the store receives a disposition with a note, evidence and actor
- THEN the Issue gets the disposition and its status follows it
- AND every report stays unchanged

### scenario.issues.store-disposition-stale — A disposition over a changed record is refused

- GIVEN an Issue whose record changed after its revision was read
- WHEN a disposition names the old revision
- THEN the store refuses with `stale_issue`
- BUT the record is unchanged

### scenario.issues.store-disposition-invalid — An invalid disposition is refused

- GIVEN an Issue and its current revision
- WHEN a disposition has no evidence, names the Issue itself or a closed Issue as its duplicate, or closes a closed Issue or reopens an open one
- THEN the store refuses it
- BUT the record is unchanged

### scenario.issues.store-restore — Restore the open bytes of an unfinished close

- GIVEN an Issue closed over a known revision and the exact open bytes it had before
- WHEN the store restores the open bytes over the closed revision
- THEN the record is the open bytes again
- AND restoring a second time does nothing

### scenario.issues.store-restore-stale — A restoration over other bytes is refused

- GIVEN an Issue whose bytes are neither the closed revision nor the open bytes to restore
- WHEN the store is asked to restore
- THEN it refuses with `stale_issue`
- BUT the record is unchanged

### scenario.issues.store-boundary — Refuse malformed or unsafe records

- GIVEN a malformed report, an unsafe evidence path, a corrupted report digest or a failed file publication
- WHEN the store tries to accept or save it
- THEN it does not report success
- AND existing valid records stay readable and unchanged

## The store check

### scenario.issues.store-check-invalid — The store check fails for an invalid record

- GIVEN a project whose Issue directory holds a malformed or misnamed record
- WHEN the configured store check runs
- THEN it prints a finding naming the record
- AND exits with a nonzero status

### scenario.issues.unknown-owner-listed — An Issue of a removed Module is still listed

- GIVEN an Issue whose owner is not a registered Module
- WHEN the Issues are listed or the record is read
- THEN the Issue is returned like any other

### scenario.issues.store-check-unknown-owner — The store check reports an unknown owner

- GIVEN an open Issue whose owner is not a registered Module
- WHEN the configured store check runs
- THEN it prints a finding naming the Issue and the unknown owner
- AND exits with a nonzero status

### scenario.issues.store-check-closed-unknown-owner — A closed Issue of a removed Module does not fail

- GIVEN a closed Issue whose owner is not a registered Module, and no other problem
- WHEN the configured store check runs
- THEN it prints a finding naming the Issue and the unknown owner
- BUT exits with status zero
