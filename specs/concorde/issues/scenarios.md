# Issues scenarios

Concrete situations that show the [requirements](requirements.md) at work. Shapes and error codes
are defined in the [Issue interface](interface.md).

## Recording through the command

### scenario.issues.command-report — Record a report from a file

- GIVEN an initialized project and a report file naming a registered owner and existing evidence
- WHEN the [main agent](../glossary.json#concept.main-agent) runs `report --file` with that file and a task identity
- THEN a new open [Issue](../glossary.json#concept.issue) holds exactly that report
- AND its provenance names `main-agent`, `issues`, `report`, the owner as reporting [Module](../glossary.json#concept.module), the registry digest, the task and the Git `HEAD` or `null` outside a Git repository
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

- GIVEN an initialized project and a report file written in another project, naming that project as its `origin`, evidence paths that exist relative to it and an [error chain](../glossary.json#concept.error-chain)
- WHEN the main agent runs `report --file` with that file
- THEN the Issue holds the report with its origin and error chain unchanged
- AND its provenance is this project's, with the root Module as reporting Module when the owner is `null`

### scenario.issues.command-report-origin-missing-evidence — Evidence absent from the origin project is refused

- GIVEN a report file with an `origin` whose evidence path does not exist in that origin project
- WHEN the main agent runs `report --file` with that file
- THEN the command refuses it with `missing_evidence`, naming the report file, the evidence path and the origin project
- AND exits with status 1
- BUT writes nothing

### scenario.issues.command-report-invalid-error-chain — An error chain outside the error contract is refused

- GIVEN a report file whose `error_chain` is not an error of the Framework's error contract
- WHEN the main agent runs `report --file` with that file
- THEN the command refuses it with `invalid_issue`, naming the report file and the field `error_chain`
- AND exits with status 1
- BUT writes nothing

This illustrates [checked reports](requirements.md#req.issues.report-checked).

### scenario.issues.command-report-check — Check a report without recording it

- GIVEN an initialized project and a report file that passes every check of `report`
- WHEN the main agent runs `report --file` with that file and `--check`
- THEN the command answers `valid` with the file, its report key and its reporting Module
- BUT no Issue is recorded

### scenario.issues.command-report-check-refused — Checking a failing report refuses it as recording would

- GIVEN an initialized project and a report file that fails a check of `report`, such as a missing required field or an evidence path absent from the project
- WHEN the main agent runs `report --file` with that file and `--check`
- THEN the command refuses it exactly as `report` would, with the same code and a message naming the file and field
- BUT no Issue is recorded

### scenario.issues.command-report-unknown-owner — A report without an owner is filed under the root Module

- GIVEN a registry with one root Module and a report file whose owner is `null`
- WHEN the main agent runs `report --file` with that file
- THEN the Issue is recorded with the report's `owner_target_id` still `null` and the root Module as its reporting Module, and so as the Issue's owner
- AND the store check passes

### scenario.issues.command-append — Append a later observation from a file

- GIVEN an open Issue and a report file naming it with its current revision and another classification
- WHEN the main agent runs `report --file` with that file
- THEN the Issue holds both reports and the command prints the new revision
- AND its status stays open while its summary follows the latest report's title, classification and owner

### scenario.issues.command-append-stale — Appending at an old revision is refused

- GIVEN an open Issue that changed after the revision a report file names for it
- WHEN the main agent runs `report --file` with that file
- THEN the command refuses it with `stale_issue`, naming the Issue, the revision the file gives and the current revision
- AND exits with status 1
- BUT the Issue keeps only the reports it had

This illustrates [revision-checked writes](requirements.md#req.issues.revision-checked).

### scenario.issues.command-close — Close an Issue with evidence

- GIVEN an open Issue
- WHEN the main agent runs `close` with the reason `resolved`, a note and evidence items
- THEN the Issue is closed with a disposition of that reason, whose actor is `main-agent` and whose evidence is those items
- AND the command prints the Issue, its status `closed` and its new revision

This illustrates [command attribution](requirements.md#req.issues.main-agent-actor) and
[legal transitions](requirements.md#req.issues.legal-transitions).

### scenario.issues.command-close-duplicate — Close an Issue as a duplicate of another

- GIVEN two open Issues
- WHEN the main agent runs `close` on one with the reason `duplicate`, `--duplicate-of` naming the other, a note and evidence
- THEN the first Issue is closed with a disposition whose `duplicate_of` names the other
- AND the other Issue stays open

### scenario.issues.command-close-duplicate-of-closed — A duplicate of a closed Issue is refused

- GIVEN an open Issue and a closed one
- WHEN the main agent runs `close` on the open Issue with the reason `duplicate` and `--duplicate-of` naming the closed one
- THEN the command refuses it with `invalid_issue`, naming the closed Issue
- AND exits with status 1
- BUT the open Issue stays open

### scenario.issues.command-reopen — Reopen a closed Issue

- GIVEN a closed Issue
- WHEN the main agent runs `reopen` with a note and evidence items
- THEN the Issue is open again with every report unchanged
- AND the command prints its status and new revision

### scenario.issues.command-usage — An unusable argument exits with status 2

- GIVEN a missing argument, an unknown reason, a `duplicate` without `--duplicate-of`, a blank note, a repeated evidence item, or a `list` status, tier, severity or sort that is none of the statuses, tiers, severities or sorts
- WHEN the command runs
- THEN it prints the error code `usage` and a message naming the argument
- AND exits with status 2
- BUT writes nothing

This illustrates [specific refusals](requirements.md#req.issues.specific-refusals) and
[refusals that write nothing](requirements.md#req.issues.refusal-writes-nothing).

### scenario.issues.command-unreadable-file — An unreadable report file exits with status 2

- GIVEN a report file path that does not exist or does not hold UTF-8 text
- WHEN the main agent runs `report --file` with it
- THEN the command prints the error code `unreadable_file` and a message naming the file
- AND exits with status 2
- BUT writes nothing

### scenario.issues.command-not-a-project — A directory that is not a Concorde project exits with status 2

- GIVEN a `--root` directory without `.concorde/config.json`
- WHEN any action of the command runs on it
- THEN the command prints the error code `not_a_project` and a message naming the directory
- AND exits with status 2
- BUT writes nothing

### scenario.issues.command-refused — A report file with an invalid field is refused

- GIVEN a report file with a malformed field, such as a blank title or an `issue_id` without an `expected_revision`
- WHEN the main agent runs `report --file` with that file
- THEN the command prints the error code `invalid_issue` and a message naming the report file and the field
- AND exits with status 1
- BUT writes nothing

### scenario.issues.command-report-unregistered-owner — A report naming an unregistered owner is refused

- GIVEN a report file whose `owner_target_id` is not a registered Module
- WHEN the main agent runs `report --file` with that file
- THEN the command prints the error code `unknown_owner` and a message naming the report file, the field `owner_target_id` and the owner
- AND exits with status 1
- BUT writes nothing

### scenario.issues.command-report-missing-evidence — A report naming absent evidence is refused

- GIVEN a report file without an `origin` whose evidence path does not exist in the project
- WHEN the main agent runs `report --file` with that file
- THEN the command prints the error code `missing_evidence` and a message naming the report file, the field `evidence/<index>/path` and the path
- AND exits with status 1
- BUT writes nothing

### scenario.issues.command-unknown-issue — Naming an absent Issue is refused

- GIVEN a well-formed Issue identity that names no record
- WHEN the main agent runs `show`, `close` or `reopen` with it, `close` with it as `--duplicate-of`, or `report --file` with a file appending to it
- THEN the command prints the error code `unknown_issue` and a message naming that identity
- AND exits with status 1
- BUT writes nothing

### scenario.issues.command-malformed-identity — A malformed Issue identity is refused

- GIVEN a string that is not `I-` followed by 32 lowercase hex digits
- WHEN the main agent runs `show` with it
- THEN the command prints the error code `invalid_issue` and a message naming that string
- AND exits with status 1

### scenario.issues.command-close-closed — Closing a closed Issue is refused

- GIVEN a closed Issue
- WHEN the main agent runs `close` on it
- THEN the command prints the error code `closed_issue` and a message naming the Issue
- AND exits with status 1
- BUT the Issue keeps only the disposition it had

### scenario.issues.command-append-closed — Appending to a closed Issue is refused

- GIVEN a closed Issue and a report file naming it with its current revision
- WHEN the main agent runs `report --file` with that file
- THEN the command prints the error code `closed_issue` and a message naming the Issue
- AND exits with status 1
- BUT the Issue keeps only the reports it had

### scenario.issues.command-reopen-open — Reopening an open Issue is refused

- GIVEN an open Issue
- WHEN the main agent runs `reopen` on it
- THEN the command prints the error code `open_issue` and a message naming the Issue
- AND exits with status 1
- BUT the Issue gets no disposition

### scenario.issues.command-close-self-duplicate — An Issue named as its own duplicate is refused

- GIVEN an open Issue
- WHEN the main agent runs `close` on it with the reason `duplicate` and `--duplicate-of` naming the same Issue
- THEN the command prints the error code `invalid_issue` and a message naming the Issue and saying it cannot be its own duplicate
- AND exits with status 1
- BUT the Issue stays open

### scenario.issues.command-write-failed — A failed write is an environment error

- GIVEN a valid report file and a project whose file system refuses to write the record
- WHEN the main agent runs `report --file` with that file
- THEN the command prints the error code `io_error` with the reason `environment` and a message naming the file it could not write
- AND its options say to carry the error chain in the [decision log](../glossary.json#concept.decision-log), escalation or [run result](../glossary.json#concept.run-result) and never to report it as an Issue
- AND exits with status 1
- BUT no Issue is recorded

### scenario.issues.command-write-raced — A record changed during the write is refused as stale

- GIVEN an open Issue, a report file appending to it at its current revision, and another program that changes the record after the command read it and before it publishes
- WHEN the main agent runs `report --file` with that file
- THEN the command prints the error code `stale_issue` and a message naming the Issue
- AND exits with status 1
- BUT the record keeps the other program's bytes

### scenario.issues.command-from-any-worktree — A linked worktree works on the primary worktree's Issues

- GIVEN an Issue recorded in the primary worktree, and a linked worktree holding a file its branch alone has
- WHEN a session runs `report --file` in the linked worktree with a report whose evidence is that file, and then `list`
- THEN the new Issue's record is in the primary worktree, not in the linked worktree
- AND `list` names both Issues

This illustrates [project-level records](requirements.md#req.issues.project-level).

### scenario.issues.command-list-filtered — List only the Issues of one Module, status, tier and severity

- GIVEN Issues owned by two Modules, one of them closed, with different tiers and severities
- WHEN the main agent runs `list --module <module> --status open`, then `list --tier <tier>` with two tiers, then the Module, status and tier filters together, then `list` alone, then `list --severity <severity>` with two severities, then `list --status open --sort severity`
- THEN the first lists only that Module's open Issues, the second only the Issues of either tier, and the third only those passing all three filters
- AND `list` alone names every Issue, open and closed
- AND `--severity` lists only the Issues of either severity
- AND `--sort severity` lists the open Issues most severe first, those of equal severity `decision-needed` before `obvious-fix`, each row with its severity

This illustrates [filtered listing](requirements.md#req.issues.list-filtered) and
[listing by severity](requirements.md#req.issues.list-by-severity).

### scenario.issues.command-commit-failed — A failed commit is an Issue-system failure, never an Issue

- GIVEN a primary worktree whose `HEAD` is detached
- WHEN the main agent runs `report --file` with a valid report
- THEN the command prints the error code `commit_failed` with the reason `environment`, naming the detached `HEAD`
- AND its options say to carry the error chain in the decision log, escalation or run result and never to report it as an Issue
- BUT writes nothing

This illustrates [the Issue system never reporting itself](requirements.md#req.issues.own-failures).

## Records

### scenario.issues.store-report — Save a report once

- GIVEN caller-supplied provenance and a classified report
- WHEN the store saves it and then saves the identical report again with the same provenance, so the same `invocation_id`
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

### scenario.issues.store-append-stale — An append at an old revision is refused

- GIVEN an open Issue that changed after a caller read its revision
- WHEN a report appends to it naming that old revision
- THEN the store refuses with `stale_issue`, naming the Issue, the old and the current revision
- BUT the record is unchanged

### scenario.issues.store-concurrency — Concurrent writers never lose a report

- GIVEN several reports, some of them repeated, submitted concurrently to the primary worktree
- WHEN the store accepts them
- THEN every distinct report is saved exactly once
- BUT no accepted report is lost or duplicated

### scenario.issues.project-level — Only the primary worktree writes the Issues

- GIVEN an Issue recorded in the primary worktree and a linked worktree of the same repository
- WHEN `project_root` is asked for either worktree
- THEN it names the primary worktree, whose records every worktree reads
- BUT a disposition written with the linked worktree as root is refused with `not_primary` and the Issue stays open

This illustrates [project-level records](requirements.md#req.issues.project-level).

### scenario.issues.store-merge-lock — A write waits for the merge lock

- GIVEN another process holding the primary worktree's [merge lock](../glossary.json#concept.merge-lock)
- WHEN the store is asked to save a report without waiting, and again with its default wait
- THEN the first is refused with `merge_busy`, naming the lock file, and writes nothing
- AND the second waits, writes nothing while the lock is held, and saves the report once it is released

This illustrates [Issue writes under the merge lock](requirements.md#req.issues.merge-lock).

### scenario.issues.store-merge-incomplete — No write while a merge is unfinished

- GIVEN a task stored `merging` whose merge process has ended
- WHEN the store is asked to save a report
- THEN it refuses with `merge_incomplete`, naming the task
- BUT no Issue is written

### scenario.issues.store-committed — Every write commits its record alone

- GIVEN a primary worktree with another change staged
- WHEN the store saves a report and then closes its Issue
- THEN each write is a commit on the primary branch holding only the record, with the trailer `Concorde-Issue` naming the Issue
- AND the committed record equals the file, which Git reports unchanged
- BUT the other staged change stays staged and uncommitted

This illustrates [an Issue commit alone](requirements.md#req.issues.commit-alone) and
[committed receipts](requirements.md#req.issues.durable-receipt).

### scenario.issues.store-commit-failed — A write Git cannot commit is refused

- GIVEN a primary worktree whose `HEAD` is detached
- WHEN the store is asked to save a report
- THEN it refuses with `commit_failed`, saying the `HEAD` is detached
- BUT no record is left in the directory and no Issue is listed

### scenario.issues.store-tier — Every report carries a tier

- GIVEN a report without a `tier`, or with a tier that is none of the four
- WHEN the store is asked to save it
- THEN Spec core's typed-value check refuses it, naming the field `tier`, and no Issue is written
- AND a report of tier `suggestion` creates a record of `schema_version` 4 listed with that tier
- AND a record of `schema_version` 2 whose report has no tier stays valid, is listed without a tier and takes a tiered report, which becomes its tier
- BUT a record of `schema_version` 3 or 4 holding an untiered report is refused with `invalid_issue`, naming the field `tier`

This illustrates [required tiers](requirements.md#req.issues.tier-required).

### scenario.issues.store-severity — Every report carries a severity

- GIVEN a report without a `severity`, or with a severity that is none of the four
- WHEN the store is asked to save it
- THEN Spec core's typed-value check refuses it, naming the field `severity`, and no Issue is written
- AND a report of severity `low` creates a record of `schema_version` 4 listed with that severity
- AND a record of `schema_version` 3 whose report has no severity stays valid, is listed without a severity, passes no severity filter and takes a report with a severity, which becomes its severity, keeping its version 3
- BUT a record of `schema_version` 4 holding a report without a severity is refused with `invalid_issue`, naming the field `severity`

This illustrates [required severities](requirements.md#req.issues.severity-required).

### scenario.issues.store-severity-sort — Listing by severity puts the most severe Issues first

- GIVEN open Issues of severities `critical`, `high` and `low`, the `high` ones of tiers `decision-needed` and `obvious-fix`, two of them both `high` and `decision-needed`, and an Issue written before severities whose latest report has none
- WHEN the store lists them sorted by severity, then sorted by severity and filtered to `high`
- THEN the first lists the `critical` Issue, the two `high` `decision-needed` Issues in the order they were reported, the `high` `obvious-fix` Issue, the `low` Issue and last the Issue without a severity
- AND the second lists only the three `high` Issues in that order
- BUT listed without a sort they come by identity

This illustrates [listing by severity](requirements.md#req.issues.list-by-severity).

### scenario.issues.store-disposition — Close with evidence

- GIVEN an open Issue and its current revision
- WHEN the store receives a closing disposition at that revision with a note, evidence and actor
- THEN the Issue gets the disposition and its status is `closed`
- AND the store returns the new revision
- AND every report stays unchanged

### scenario.issues.store-disposition-duplicate — Close as a duplicate of another open Issue

- GIVEN two open Issues and the current revision of the first
- WHEN the store receives a `duplicate` disposition of the first naming the second
- THEN the first Issue is closed with a disposition whose `duplicate_of` names the second

### scenario.issues.store-reopen — Reopen at the current revision

- GIVEN a closed Issue and its current revision
- WHEN the store receives a `reopened` disposition at that revision
- THEN the Issue is open again
- AND every report stays unchanged

### scenario.issues.store-status-mismatch — A status cannot contradict its history

- GIVEN an Issue record whose status is `closed` but whose disposition history is empty
- WHEN the store reads that record
- THEN it refuses the record with `invalid_issue` because an empty history leaves the Issue open
- BUT it does not repair the status or invent a closing disposition

This illustrates [status derived from history](requirements.md#req.issues.status-derived).

### scenario.issues.store-disposition-stale — A disposition over a changed record is refused

- GIVEN an Issue whose record changed after its revision was read
- WHEN a disposition names the old revision
- THEN the store refuses with `stale_issue`, naming the Issue, the old and the current revision
- BUT the record is unchanged

### scenario.issues.store-duplicate-stale — A duplicate of a changed Issue is refused

- GIVEN two open Issues, the second of which changed after a caller read its revision
- WHEN a `duplicate` disposition of the first names the second with that old revision as `duplicate_revision`
- THEN the store refuses with `stale_issue`, naming the second Issue and both of its revisions
- BUT the first Issue stays open and unchanged

### scenario.issues.store-disposition-invalid — A disposition without evidence is refused

- GIVEN an open Issue and its current revision
- WHEN a disposition at that revision has an empty evidence list
- THEN Spec core's [typed-value](../glossary.json#concept.typed-value) check refuses it with `invalid_field`, naming the disposition's `evidence` field
- BUT the record is unchanged

### scenario.issues.store-self-duplicate — An Issue cannot be its own duplicate

- GIVEN an open Issue and its current revision
- WHEN a `duplicate` disposition names the Issue itself
- THEN the store refuses with `invalid_issue`, naming the Issue
- BUT the record is unchanged

## Refusing unsafe input

### scenario.issues.store-boundary — A report that breaks the report schema is refused

- GIVEN a report with an unknown type, a blank title or a field the report contract does not define
- WHEN the store is asked to save it
- THEN Spec core's typed-value check refuses it with `invalid_field`, naming the field
- BUT no Issue is written

### scenario.issues.store-report-inconsistent — A report that breaks an Issue rule is refused

- GIVEN a report that satisfies the report schema but has a subtype that does not match its type, only one of `issue_id` and `expected_revision`, or more than 64 KiB as canonical JSON
- WHEN the store is asked to save it
- THEN the store refuses it with `invalid_issue`, naming the rule it breaks
- BUT no Issue is written

### scenario.issues.store-unsafe-evidence-path — An evidence path outside the project is refused

- GIVEN a report whose evidence path is not a canonical project-relative POSIX path, such as `../outside`
- WHEN the store is asked to save it
- THEN Spec core's typed-value check refuses it with `invalid_field`, naming the evidence path's field
- BUT no Issue is written

### scenario.issues.store-symlinked-directory — An Issue directory that is a symbolic link is refused

- GIVEN a project whose `.concorde/issues` is a symbolic link to another directory
- WHEN the store is asked to save a valid report
- THEN Spec core's path check refuses it with `invalid_field`, because symbolic links are forbidden
- BUT nothing is written into the linked directory

### scenario.issues.store-corrupted-record — A record whose report no longer matches its digest is refused

- GIVEN a record file whose report text was edited after it was accepted, so the report's `id` no longer matches its content
- WHEN the store reads that Issue
- THEN it refuses with `invalid_issue`, naming the Issue and saying the digest differs from the content
- BUT it leaves the file as it found it

### scenario.issues.store-failed-publication — A failed publication is not reported as success

- GIVEN a project with one valid Issue and a file system that refuses to write the next record
- WHEN the store is asked to save another report
- THEN it fails with the [file transaction](../glossary.json#concept.file-transaction)'s `system_error` instead of returning a receipt
- AND the valid Issue stays readable and unchanged
- BUT no other Issue is written

This illustrates [durable receipts](requirements.md#req.issues.durable-receipt).

### scenario.issues.store-publication-stale — A record created or changed during publication is refused

- GIVEN another program that creates or changes an Issue's record file after the store read it and before the store publishes
- WHEN the store creates that Issue, appends a report to it or disposes it
- THEN the store refuses with `stale_issue`, naming the Issue and whether its record was created or changed, and naming the record file
- AND the file transaction's `stale_proposal` is its cause
- BUT the record keeps the other program's bytes

This illustrates [revision-checked writes](requirements.md#req.issues.revision-checked).

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
