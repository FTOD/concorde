# Issues scenarios

Concrete situations that show the [requirements](requirements.md) at work. Shapes and error codes
are defined in the [Issue interface](interface.md).

When a scenario names a command in short, every argument it does not name has a valid form.
For a `close`, the unnamed arguments have these valid forms:

- A closing reason.
- A nonblank note.
- Distinct, nonblank evidence items.

For a `reopen`, the unnamed arguments are a nonblank note and such evidence.
Because these unnamed arguments have valid forms, an expected refusal comes from the condition
the scenario names, never from `usage`.

## Recording through the command

### scenario.issues.command-report — Record a report from a file

- GIVEN an initialized project in a Git repository
- AND a report file names a registered owner and existing evidence
- WHEN the [main agent](../glossary.json#concept.main-agent) runs `report --file` with that file and a task identity
- THEN a new open [Issue](../glossary.json#concept.issue) holds exactly that report
- AND the Issue's provenance names `main-agent`
- AND the provenance names `issues`
- AND the provenance names `report`
- AND the provenance names the owner as reporting [Module](../glossary.json#concept.module)
- AND the provenance names the registry digest
- AND the provenance names the task
- AND when Git cannot name the reporting worktree's Git `HEAD`, the provenance names `null` instead of that `HEAD`
- AND otherwise, the provenance names the reporting worktree's Git `HEAD`
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

- GIVEN an initialized project and a report file written in another project
- AND the report file names that project as its `origin`
- AND the report file names evidence paths that exist relative to that project
- AND the report file names an [error chain](../glossary.json#concept.error-chain)
- WHEN the main agent runs `report --file` with that file
- THEN the Issue holds the report with its origin and error chain unchanged
- AND the Issue's provenance is this project's
- AND when the owner is `null`, the provenance names the root Module as reporting Module

### scenario.issues.command-report-origin-missing-evidence — Evidence absent from the origin project is refused

- GIVEN a report file with an `origin` whose evidence path does not exist in that origin project
- WHEN the main agent runs `report --file` with that file
- THEN the command refuses the report file with `missing_evidence`
- AND the refusal names the report file
- AND the refusal names the evidence path
- AND the refusal names the origin project
- AND the command exits with status 1
- BUT the command writes nothing

### scenario.issues.command-report-invalid-error-chain — An error chain outside the error contract is refused

- GIVEN a report file whose `error_chain` is not an error of the Framework's error contract
- WHEN the main agent runs `report --file` with that file
- THEN the command refuses it with `invalid_issue`, naming the report file and the field `error_chain`
- AND the command exits with status 1
- BUT the command writes nothing

This illustrates [checked error chains](requirements.md#req.issues.report-error-chain).

### scenario.issues.command-report-check — Check a report without recording it

- GIVEN an initialized project and a report file that passes every check of `report`
- WHEN the main agent runs `report --file` with that file and `--check`
- THEN the command answers `valid` with the file
- AND the answer includes the file's report key
- AND the answer includes the file's reporting Module
- BUT no Issue is recorded

### scenario.issues.command-report-check-refused — Checking a failing report refuses it as recording would

- GIVEN an initialized project and a report file that fails a check of `report`
- AND that failure is, for example, a missing required field or an evidence path absent from the project
- WHEN the main agent runs `report --file` with that file and `--check`
- THEN the command refuses it exactly as `report` would, with the same code
- AND the refusal message names the file and field
- BUT no Issue is recorded

### scenario.issues.command-report-check-origin — A defect report is checked without the spec part

- GIVEN a project whose worktrees hold no registry `.concorde/specs.json`, with the spec part not installed
- AND a [defect report](../glossary.json#concept.defect-report) file has an owner of `null`
- AND the file has an `origin` naming the project it was seen in
- AND the file has evidence that exists there
- WHEN the main agent runs `report --file` with that file and `--check`
- THEN the command answers `valid` with the file
- AND the answer includes the file's report key
- AND the answer includes `null` as the file's reporting Module
- BUT no Issue is recorded

This illustrates [registered owners](requirements.md#req.issues.report-owner-registered).

### scenario.issues.command-report-unknown-owner — A report without an owner is filed under the root Module

- GIVEN a registry with one root Module and a report file whose owner is `null`
- WHEN the main agent runs `report --file` with that file
- THEN the Issue is recorded with the report's `owner_target_id` still `null`
- AND the Issue is recorded with the root Module as its reporting Module
- AND so the root Module is the Issue's owner
- AND the store check passes

### scenario.issues.command-report-provenance — An Operation records a report with its own provenance

- GIVEN a report file whose owner is a Module the primary worktree's registry does not list
- AND the report file's evidence path does not exist
- AND a provenance file names an [Operation](../glossary.json#concept.operation)'s run
- AND the provenance file names `operation` as agent
- AND the provenance file names that Module as reporting Module
- WHEN the Operation's host runs `report --file` with the report file and `--provenance` with the provenance file
- THEN the Issue is recorded with exactly that provenance
- AND the command prints the receipt and revision

### scenario.issues.command-report-provenance-usage — A provenance file given with --task or --check is refused

- GIVEN a valid report file and a valid provenance file
- WHEN the main agent runs `report --file` with that file
- AND the command receives `--provenance` with the provenance file
- AND the command also receives `--task` or `--check`
- THEN the command prints the error code `usage` and a message naming `--provenance`
- AND the command exits with status 2
- BUT the command writes nothing

### scenario.issues.command-report-provenance-invalid — A provenance file that breaks the provenance shape is refused

- GIVEN a valid report file and a provenance file with a field that breaks the provenance shape
- AND that field is, for example, a `context_id` that is no digest
- WHEN the Operation's host runs `report --file` with that file and `--provenance` with the provenance file
- THEN the command prints the error code `invalid_issue` and a message naming the provenance file and the field
- AND the command exits with status 1
- BUT the command writes nothing

### scenario.issues.command-without-spec-part — Without the spec part a Module is a plain label

- GIVEN a project whose worktrees hold no registry `.concorde/specs.json`, with the spec part not installed
- WHEN the main agent runs `report --file` with a report naming an owner no registry lists
- AND the main agent then runs `check`
- THEN the Issue is recorded with that owner as its reporting Module
- AND the Issue's context is the digest of no bytes
- AND `check` passes without judging any owner
- AND `check` gives one note saying the spec part is not installed

### scenario.issues.command-without-spec-part-null-owner — Without the spec part a report needs an owner

- GIVEN a project whose worktrees hold no registry `.concorde/specs.json`, with the spec part not installed
- AND a report file without an `origin` has an owner of `null`
- WHEN the main agent runs `report --file` with that file
- THEN the command prints the error code `no_reporting_module` and a message saying the spec part is not installed
- AND the command exits with status 1
- BUT the command writes nothing

This illustrates [registered owners](requirements.md#req.issues.report-owner-registered).

### scenario.issues.store-without-coordination — Without the coordination part no write waits for a merge

- GIVEN a primary worktree with no `.concorde/tasks/` and no unfinished-merge marker, with the coordination part not installed
- WHEN a session records a report
- THEN the store commits it without an unfinished merge refusing it

### scenario.issues.command-unreadable-merge-marker — A marker that cannot be read refuses the write

- GIVEN a primary worktree whose [unfinished-merge marker](../glossary.json#concept.unfinished-merge-marker) file does not read as a JSON object
- AND a valid report file exists
- WHEN the main agent runs `report --file` with that file
- THEN the command prints the error code `unreadable_merge_marker` with the reason `environment`, naming that file
- AND the command's options say to carry the error chain in the decision log, escalation or run result
- AND those options say never to report the error chain as an Issue
- AND the command exits with status 1
- BUT the command writes nothing

This illustrates [no Issue write while a merge is unfinished](requirements.md#req.issues.no-write-during-merge).

### scenario.issues.command-append — Append a later observation from a file

- GIVEN an open Issue and a report file naming it with its current revision
- AND the report file names another classification
- WHEN the main agent runs `report --file` with that file
- THEN the Issue holds both reports
- AND the command prints the new revision
- AND the Issue's status stays open
- AND the Issue's summary follows the latest report's title
- AND the summary follows the latest report's classification
- AND the summary follows the latest report's owner

### scenario.issues.command-append-stale — Appending at an old revision is refused

- GIVEN an open Issue that changed after the revision a report file names for it
- WHEN the main agent runs `report --file` with that file
- THEN the command refuses the report file with `stale_issue`
- AND the refusal names the Issue
- AND the refusal names the revision the file gives
- AND the refusal names the current revision
- AND the command exits with status 1
- BUT the Issue keeps only the reports it had

This illustrates [revision-checked writes](requirements.md#req.issues.revision-checked).

### scenario.issues.command-close — Close an Issue with evidence

- GIVEN an open Issue
- WHEN the main agent runs `close` with the reason `resolved`
- AND the command receives a note
- AND the command receives evidence items
- THEN the Issue is closed with a disposition of that reason
- AND the disposition's actor is `main-agent`
- AND the disposition's evidence is those items
- AND the command prints the Issue
- AND the command prints the Issue's status `closed`
- AND the command prints the Issue's new revision

This illustrates [command attribution](requirements.md#req.issues.main-agent-actor) and
[legal transitions](requirements.md#req.issues.legal-transitions).

### scenario.issues.command-close-duplicate — Close an Issue as a duplicate of another

- GIVEN two open Issues
- WHEN the main agent runs `close` on one with the reason `duplicate`
- AND the invocation includes `--duplicate-of` naming the other
- AND the invocation includes a note and evidence
- THEN the first Issue is closed with a disposition whose `duplicate_of` names the other
- AND the other Issue stays open

### scenario.issues.command-close-duplicate-of-closed — A duplicate of a closed Issue is refused

- GIVEN an open Issue and a closed one
- WHEN the main agent runs `close` on the open Issue with the reason `duplicate` and `--duplicate-of` naming the closed one
- THEN the command refuses it with `invalid_issue`, naming the closed Issue
- AND the command exits with status 1
- BUT the open Issue stays open

### scenario.issues.command-reopen — Reopen a closed Issue

- GIVEN a closed Issue
- WHEN the main agent runs `reopen` with a note and evidence items
- THEN the Issue is open again with every report unchanged
- AND the command prints its status and new revision

### scenario.issues.command-usage — An unusable argument exits with status 2

- GIVEN an argument that the command cannot use
- AND the argument is a missing argument, an unknown reason, a `duplicate` without `--duplicate-of`, a blank note or a repeated evidence item
- AND such an argument may also be a `list` status, tier, severity or sort that is none of the statuses, tiers, severities or sorts
- WHEN the command runs
- THEN it prints the error code `usage` and a message naming the argument
- AND it exits with status 2
- BUT it writes nothing

This illustrates [specific refusals](requirements.md#req.issues.specific-refusals) and
[refusals that write nothing](requirements.md#req.issues.refusal-writes-nothing).

### scenario.issues.command-unreadable-file — An unreadable report file exits with status 2

- GIVEN a report file path that does not exist or does not hold UTF-8 text
- WHEN the main agent runs `report --file` with it
- THEN the command prints the error code `unreadable_file` and a message naming the file
- AND the command exits with status 2
- BUT the command writes nothing

### scenario.issues.command-not-a-project — A directory that is not a Concorde project exits with status 2

- GIVEN a `--root` directory with neither `.concorde/config.json` nor `.concorde/install.json`
- WHEN any action of the command runs on it
- THEN the command prints the error code `not_a_project` and a message naming the directory
- AND the command exits with status 2
- BUT the command writes nothing

### scenario.issues.command-refused — A report file with an invalid field is refused

- GIVEN a report file with a malformed field, such as a blank title or an `issue_id` without an `expected_revision`
- WHEN the main agent runs `report --file` with that file
- THEN the command prints the error code `invalid_issue` and a message naming the report file and the field
- AND the command exits with status 1
- BUT the command writes nothing

### scenario.issues.command-report-unregistered-owner — A report naming an unregistered owner is refused

- GIVEN a project where the spec part is installed, and a report file whose `owner_target_id` is not a Module of its registry
- WHEN the main agent runs `report --file` with that file
- THEN the command prints the error code `unknown_owner` and a message naming the report file
- AND the message names the field `owner_target_id`
- AND the message names the owner
- AND the command exits with status 1
- BUT the command writes nothing

This illustrates [registered owners](requirements.md#req.issues.report-owner-registered).

### scenario.issues.command-report-missing-evidence — A report naming absent evidence is refused

- GIVEN a report file without an `origin` whose evidence path does not exist in the project
- WHEN the main agent runs `report --file` with that file
- THEN the command prints the error code `missing_evidence` and a message naming the report file
- AND the message names the field `evidence/<index>/path`
- AND the message names the path
- AND the command exits with status 1
- BUT the command writes nothing

This illustrates [present evidence](requirements.md#req.issues.report-evidence-present).

### scenario.issues.command-unknown-issue — Naming an absent Issue is refused

- GIVEN a well-formed Issue identity that names no record
- WHEN the main agent runs `show`, `close` or `reopen` with it, `close` with it as `--duplicate-of`, or `report --file` with a file appending to it
- THEN the command prints the error code `unknown_issue` and a message naming that identity
- AND it exits with status 1
- BUT it writes nothing

### scenario.issues.command-malformed-identity — A malformed Issue identity is refused

- GIVEN a string that is not `I-` followed by 32 lowercase hex digits
- WHEN the main agent runs `show` with it
- THEN the command prints the error code `invalid_issue` and a message naming that string
- AND the command exits with status 1

### scenario.issues.command-close-closed — Closing a closed Issue is refused

- GIVEN a closed Issue
- WHEN the main agent runs `close` on it
- THEN the command prints the error code `closed_issue` and a message naming the Issue
- AND the command exits with status 1
- BUT the Issue keeps only the disposition it had

### scenario.issues.command-append-closed — Appending to a closed Issue is refused

- GIVEN a closed Issue and a report file naming it with its current revision
- WHEN the main agent runs `report --file` with that file
- THEN the command prints the error code `closed_issue` and a message naming the Issue
- AND the command exits with status 1
- BUT the Issue keeps only the reports it had

### scenario.issues.command-reopen-open — Reopening an open Issue is refused

- GIVEN an open Issue
- WHEN the main agent runs `reopen` on it
- THEN the command prints the error code `open_issue` and a message naming the Issue
- AND the command exits with status 1
- BUT the Issue gets no disposition

### scenario.issues.command-close-self-duplicate — An Issue named as its own duplicate is refused

- GIVEN an open Issue
- WHEN the main agent runs `close` on it with the reason `duplicate` and `--duplicate-of` naming the same Issue
- THEN the command prints the error code `invalid_issue` and a message naming the Issue and saying it cannot be its own duplicate
- AND the command exits with status 1
- BUT the Issue stays open

### scenario.issues.command-write-failed — A failed write is an environment error

- GIVEN a valid report file and a project whose file system refuses to write the record
- WHEN the main agent runs `report --file` with that file
- THEN the command prints the error code `io_error` with the reason `environment`
- AND the command prints a message naming the file it could not write
- AND its options say to carry the error chain in the [decision log](../glossary.json#concept.decision-log), escalation or [run result](../glossary.json#concept.run-result) and never to report it as an Issue
- AND the command exits with status 1
- AND the file transaction's refusal comes below the command's link
- AND the operating system's error comes below the file transaction's refusal
- BUT no Issue is recorded

### scenario.issues.command-restore-refused — A record the file transaction could not restore is recovery_failed

- GIVEN a valid report file
- AND a file transaction publishes the record
- AND the file transaction fails
- AND the operating system refuses the file transaction's restoration of the record
- WHEN the main agent runs `report --file` with that file
- THEN the command prints the error code `recovery_failed` with the reason `environment`
- AND the command says that no read shows the uncommitted record
- AND the file transaction's refusal comes below the command's link
- AND each operating system error the file transaction received comes below the command's link
- AND `list` names no new Issue
- AND `recover` removes the record the write left

This illustrates [a refused request recording nothing](requirements.md#req.issues.refusal-writes-nothing)
and [the Issue system never reporting itself](requirements.md#req.issues.own-failures).

### scenario.issues.command-write-raced — A record changed during the write is refused as stale

- GIVEN an open Issue
- AND a report file specifies an append to it at its current revision
- AND another program changes the record after the command read it and before the file transaction checks it
- WHEN the main agent runs `report --file` with that file
- THEN the command prints the error code `stale_issue` and a message naming the Issue
- AND the command exits with status 1
- BUT the record keeps the other program's bytes

### scenario.issues.command-from-any-worktree — A linked worktree works on the primary worktree's Issues

- GIVEN an Issue recorded in the primary worktree, and a linked worktree holding a file its branch alone has
- WHEN a session runs `report --file` in the linked worktree with a report whose evidence is that file
- AND the session then runs `list`
- THEN the new Issue's record is in the primary worktree, not in the linked worktree
- AND `list` names both Issues

This illustrates [project-level records](requirements.md#req.issues.project-level).

### scenario.issues.command-list-filtered — List only the Issues of one Module, status, tier and severity

- GIVEN Issues owned by two Modules, one of them closed, with different tiers and severities
- WHEN the main agent runs `list --module <module> --status open`
- AND then `list --tier <tier>` with two tiers
- AND then `list` with the Module, status and tier filters together
- AND then `list` alone
- AND then `list --severity <severity>` with two severities
- AND then `list --status open --sort severity`
- THEN the first command lists only that Module's open Issues
- AND the second command lists only the Issues of either tier
- AND the third command lists only those passing all three filters
- AND `list` alone names every Issue, open and closed
- AND `--severity` lists only the Issues of either severity
- AND `--sort severity` lists the open Issues most severe first
- AND among those of equal severity, the command lists `decision-needed` before `obvious-fix`
- AND each row of that severity-sorted listing has its severity

This illustrates [filtered listing](requirements.md#req.issues.list-filtered) and
[listing by severity](requirements.md#req.issues.list-by-severity).

### scenario.issues.command-commit-failed — A failed commit is an Issue-system failure, never an Issue

- GIVEN a primary worktree whose `HEAD` is detached
- WHEN the main agent runs `report --file` with a valid report
- THEN the command prints the error code `commit_failed` with the reason `environment`, naming the detached `HEAD`
- AND the command's options say to carry the error chain in the decision log, escalation or run result
- AND the options say never to report the error chain as an Issue
- BUT the command writes nothing

This illustrates [the Issue system never reporting itself](requirements.md#req.issues.own-failures).

### scenario.issues.command-recover — Recover what a killed write left

- GIVEN a recorded Issue and a report whose command was killed after publishing its record and before committing it
- WHEN the main agent runs `list`
- AND the main agent then runs `recover`
- AND the main agent then runs `recover` again
- THEN `list` names only the recorded Issue
- AND the first `recover` exits with status 0
- AND the first recovery prints the killed report's record file as `removed`
- AND that record file is gone
- AND the first recovery prints no record `left`
- AND the second recovery prints that nothing was recovered or left
- BUT the primary branch gains no commit

This illustrates [recovering uncommitted records](requirements.md#req.issues.uncommitted-recovered).

### scenario.issues.command-recovery-failed — A record that could not be put back is an Issue-system failure

- GIVEN a valid report file
- AND Git refuses a commit
- AND putting the published record back in the primary worktree fails too
- WHEN the main agent runs `report --file` with that file
- THEN the command prints the error code `recovery_failed` with the reason `environment`
- AND the command says that no read shows the uncommitted record
- AND the command's options say to carry the error chain in the decision log, escalation or run result
- AND the options say never to report the error chain as an Issue
- BUT `list` names no Issue

This illustrates [the Issue system never reporting itself](requirements.md#req.issues.own-failures).

## Records

### scenario.issues.store-report — Save a report once

- GIVEN caller-supplied provenance and a classified report
- WHEN the store saves the report
- AND the store then saves the identical report again with the same provenance, so it uses the same `invocation_id`
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
- THEN the Issue holds both reports
- AND the Issue is listed with the new classification
- BUT the first report is unchanged

### scenario.issues.store-append-stale — An append at an old revision is refused

- GIVEN an open Issue that changed after a caller read its revision
- WHEN a report appends to it naming that old revision
- THEN the store refuses with `stale_issue`, naming the Issue
- AND the refusal names the old revision
- AND the refusal names the current revision
- BUT the record is unchanged

### scenario.issues.store-concurrency — Concurrent writers never lose a report

- GIVEN several reports, some of them repeated, submitted concurrently to the primary worktree
- WHEN the store accepts them
- THEN every distinct report is saved exactly once
- BUT no accepted report is lost or duplicated

### scenario.issues.project-level — Only the primary worktree writes the Issues

- GIVEN an Issue recorded in the primary worktree and a linked worktree of the same repository
- WHEN `project_root` is asked for either worktree
- THEN `project_root` names the primary worktree
- AND every worktree reads the primary worktree's records
- BUT a disposition written with the linked worktree as root is refused with `not_primary`
- AND the Issue stays open

This illustrates [project-level records](requirements.md#req.issues.project-level).

### scenario.issues.store-merge-lock — A write waits for the merge lock

- GIVEN another process holds the primary worktree's [merge lock](../glossary.json#concept.merge-lock)
- AND that process releases the lock before 300 seconds pass
- WHEN the store is asked to save a report with its default wait of 300 seconds
- THEN while the lock is held, the write waits without writing anything
- AND once the lock is released, the write saves the report

This illustrates [Issue writes under the merge lock](requirements.md#req.issues.merge-lock).

### scenario.issues.store-merge-busy — A write whose wait ends first is refused

- GIVEN another process holds the primary worktree's merge lock for longer than a write's wait
- WHEN the store is asked to save a report with that wait, such as none
- THEN once the wait passes, the write is refused with `merge_busy`
- AND the refusal names the lock file and the holder named by the lock file's holder line
- BUT no Issue is written

This illustrates [Issue writes under the merge lock](requirements.md#req.issues.merge-lock).

### scenario.issues.store-merge-incomplete — No write while a merge is unfinished

- GIVEN the [unfinished-merge marker](../glossary.json#concept.unfinished-merge-marker) of a task merge whose process ended
- WHEN the store is asked to save a report
- AND a caller that holds the merge lock itself then asks the store to save the report
- AND that caller asks the store to recover
- THEN each request is refused with `merge_incomplete`, naming the task, the process, the merge commit, where the primary branch is now and the `--resume` and `--abort` that finish the merge
- BUT no Issue is written

This illustrates [no Issue write while a merge is unfinished](requirements.md#req.issues.no-write-during-merge).

### scenario.issues.store-committed — Every write commits its record alone

- GIVEN a primary worktree with another change staged
- WHEN the store saves a report
- AND the store then closes its Issue
- THEN each write is a commit on the primary branch holding only the record
- AND each commit has the trailer `Concorde-Issue` naming the Issue
- AND the committed record equals the file
- AND Git reports the file unchanged
- BUT the other staged change stays staged and uncommitted

This illustrates [an Issue commit alone](requirements.md#req.issues.commit-alone) and
[committed receipts](requirements.md#req.issues.durable-receipt).

### scenario.issues.store-commit-failed — A write Git cannot commit is refused

- GIVEN a primary worktree whose `HEAD` is detached
- WHEN the store is asked to save a report
- THEN the store refuses with `commit_failed`, saying the `HEAD` is detached
- BUT no record is left in the directory
- AND no Issue is listed

### scenario.issues.store-tier — A report without a valid tier is refused

- GIVEN a report without a `tier`, or with a tier that is none of the four
- WHEN the store is asked to save it
- THEN the Kernel's typed-value check refuses it, naming the field `tier`
- BUT no Issue is written

This illustrates [required tiers](requirements.md#req.issues.tier-required).

### scenario.issues.store-tier-recorded — A tiered report creates a current record

- GIVEN a valid report of tier `suggestion`
- WHEN the store saves it
- THEN the store creates a record of `schema_version` 4
- AND the record is listed with the tier `suggestion`

### scenario.issues.store-tier-legacy — A record written before tiers stays valid

- GIVEN a committed record of `schema_version` 2 whose one report has no tier
- WHEN the Issues are listed
- AND the record is read
- THEN the record reads as valid
- AND the record is listed without a tier

### scenario.issues.store-tier-legacy-append — A record written before tiers takes a tiered report

- GIVEN a committed record of `schema_version` 2 whose one report has no tier, and its revision
- WHEN a report of tier `obvious-fix` appends to it at that revision
- THEN the Issue is listed with the tier `obvious-fix`
- AND its record keeps `schema_version` 2

### scenario.issues.store-tier-missing — A current record without a tier is refused

- GIVEN a record of `schema_version` 3 or 4 one of whose reports has no tier
- WHEN the store validates it
- THEN the store refuses the record with `invalid_issue`, naming the field `tier`

### scenario.issues.store-severity — A report without a valid severity is refused

- GIVEN a report without a `severity`, or with a severity that is none of the four
- WHEN the store is asked to save it
- THEN the Kernel's typed-value check refuses it, naming the field `severity`
- BUT no Issue is written

This illustrates [required severities](requirements.md#req.issues.severity-required).

### scenario.issues.store-severity-recorded — A report with a severity creates a current record

- GIVEN a valid report of severity `low`
- WHEN the store saves it
- THEN the store creates a record of `schema_version` 4
- AND the record is listed with the severity `low`

### scenario.issues.store-severity-legacy — A record written before severities stays valid

- GIVEN a committed record of `schema_version` 3 whose one report has no severity
- WHEN the Issues are listed unfiltered
- AND the Issues are listed filtered by every severity
- AND the record is read
- THEN the record reads as valid
- AND the record is listed without a severity
- BUT no severity filter keeps it

### scenario.issues.store-severity-legacy-append — A record written before severities takes a report with one

- GIVEN a committed record of `schema_version` 3 whose one report has no severity, and its revision
- WHEN a report of severity `critical` appends to it at that revision
- THEN the Issue is listed with the severity `critical`
- AND its record keeps `schema_version` 3

### scenario.issues.store-severity-missing — A current record without a severity is refused

- GIVEN a record of `schema_version` 4 one of whose reports has no severity
- WHEN the store validates it
- THEN the store refuses the record with `invalid_issue`, naming the field `severity`

### scenario.issues.store-severity-sort — Listing by severity puts the most severe Issues first

- GIVEN open Issues that include a `critical` Issue
- AND the `high` Issues include two of tier `decision-needed` and one of tier `obvious-fix`
- AND the open Issues include a `low` Issue
- AND an Issue written before severities has no severity in its latest report
- WHEN the store lists them sorted by severity
- AND the store then lists them sorted by severity and filtered to `high`
- THEN the first list starts with the `critical` Issue
- AND the two `high` `decision-needed` Issues follow in the order they were reported
- AND the `high` `obvious-fix` Issue follows them
- AND the `low` Issue follows that Issue
- AND the Issue without a severity is last
- AND the second lists only the three `high` Issues in that order
- BUT when listed without a sort, they come by identity

This illustrates [listing by severity](requirements.md#req.issues.list-by-severity).

### scenario.issues.store-disposition — Close with evidence

- GIVEN an open Issue and its current revision
- WHEN the store receives a closing disposition at that revision with a note
- AND the disposition includes evidence
- AND the disposition names an actor
- THEN the Issue gets the disposition
- AND its status is `closed`
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
- THEN the store refuses with `stale_issue`, naming the Issue
- AND the refusal names the old revision
- AND the refusal names the current revision
- BUT the record is unchanged

### scenario.issues.store-duplicate-stale — A duplicate of a changed Issue is refused

- GIVEN two open Issues, the second of which changed after a caller read its revision
- WHEN a `duplicate` disposition of the first names the second with that old revision as `duplicate_revision`
- THEN the store refuses with `stale_issue`, naming the second Issue
- AND the refusal names the second Issue's old revision
- AND the refusal names the second Issue's current revision
- BUT the first Issue stays open and unchanged

### scenario.issues.store-disposition-invalid — A disposition without evidence is refused

- GIVEN an open Issue and its current revision
- WHEN a disposition at that revision has an empty evidence list
- THEN the Kernel's [typed-value](../glossary.json#concept.typed-value) check refuses it with `invalid_field`, naming the disposition's `evidence` field
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
- THEN the Kernel's typed-value check refuses it with `invalid_field`, naming the field
- BUT no Issue is written

### scenario.issues.store-report-inconsistent — A report that breaks an Issue rule is refused

- GIVEN a report that satisfies the report schema
- AND the report has a subtype that does not match its type, only one of `issue_id` and `expected_revision`, or more than 64 KiB as canonical JSON
- WHEN the store is asked to save it
- THEN the store refuses it with `invalid_issue`, naming the rule it breaks
- BUT no Issue is written

### scenario.issues.store-unsafe-evidence-path — An evidence path outside the project is refused

- GIVEN a report whose evidence path is not a canonical project-relative POSIX path, such as `../outside`
- WHEN the store is asked to save it
- THEN the Kernel's typed-value check refuses it with `invalid_field`, naming the evidence path's field
- BUT no Issue is written

### scenario.issues.store-symlinked-directory — An Issue directory that is a symbolic link is refused

- GIVEN a project whose `.concorde/issues` is a symbolic link to another directory
- WHEN the store is asked to save a valid report
- THEN the Kernel's path check refuses it with `invalid_field`, because symbolic links are forbidden
- BUT nothing is written into the linked directory

### scenario.issues.store-corrupted-record — A record whose report no longer matches its digest is refused

- GIVEN a committed record whose report text was edited after the report was accepted
- AND the edit was committed
- AND the report's `id` no longer matches its content because the report text was edited and the edit was committed
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

- GIVEN another program that creates or changes an Issue's record file between the store's read and the file transaction's check
- WHEN the store creates that Issue, appends a report to it or disposes it
- THEN the store refuses with `stale_issue`, naming the Issue
- AND the refusal says whether the record was created or changed
- AND the refusal names the record file
- AND the file transaction's `stale_proposal` is the cause of the refusal
- BUT the record keeps the other program's bytes

This illustrates [revision-checked writes](requirements.md#req.issues.revision-checked).

## The closed folder

### scenario.issues.store-folders — Closing moves the record into closed/ and reopening moves it back

- GIVEN an open Issue and another change staged in the primary worktree
- WHEN the store closes the Issue
- AND the store then reopens the Issue
- AND the store then appends a report to the Issue
- THEN the close commits the record at `.concorde/issues/closed/<id>.md` and its removal from `.concorde/issues/<id>.md` in one commit
- AND that commit holds only those paths
- AND the commit's trailer names the Issue
- AND reads find the closed record in `closed/`
- AND `list` finds the closed record in `closed/`
- AND the located path finds the closed record in `closed/`
- AND the reopening moves the record back in one commit of both paths
- AND the append leaves the record there
- BUT the other staged change stays staged
- AND the Issue directory is clean

This illustrates [records in the folder of their status](requirements.md#req.issues.status-folder)
and [commits of the record alone](requirements.md#req.issues.commit-alone).

### scenario.issues.store-folders-locked — A close under a held merge lock moves the record too

- GIVEN an open Issue and a caller holding the merge lock, as a task merge closing the Issues its task resolves does
- WHEN that caller closes the Issue with `concorde issues close`, handing the merge lock on to that command's process
- THEN the answer gives the status `closed` and the path in `closed/`
- AND the record is moved in one commit of both paths
- AND this move leaves the Issue directory clean

This illustrates [records in the folder of their status](requirements.md#req.issues.status-folder).

### scenario.issues.store-interrupted-move — What a killed move left is put back whole

- GIVEN a close killed after publishing its record in `closed/` and removing it from `.concorde/issues/`, with or without staging
- AND a committed record's file was deleted by hand
- WHEN the store recovers or the next write of another Issue starts
- AND the close is repeated
- THEN the killed close's record is restored at `.concorde/issues/<id>.md`
- AND the copy in `closed/` is removed
- AND reads show the open committed record throughout
- AND the repeated close moves the record at the committed revision
- BUT the record deleted by hand, with no copy in the other folder, is left
- AND a write of its Issue is refused with `uncommitted_change`

This illustrates [recovering uncommitted records](requirements.md#req.issues.uncommitted-recovered)
and [kept foreign changes](requirements.md#req.issues.foreign-change-kept).

### scenario.issues.store-archive — Archive moves every misplaced record in one commit

- GIVEN a closed record committed in `.concorde/issues/`, as an earlier Concorde kept it
- AND an open record is committed in `closed/`
- AND other records are in their places
- AND another change is staged
- WHEN the store archives
- AND the store then archives again
- THEN the first archive moves both misplaced records into their places in one commit
- AND that commit holds exactly their four paths
- AND that commit has one trailer per Issue
- AND the first archive names each move
- AND each record's revision stays, since its bytes are unchanged
- BUT the records in their places stay
- AND the staged change stays staged
- AND the second archive moves nothing
- AND the second archive commits nothing

This illustrates [archiving misplaced records](requirements.md#req.issues.archive) and
[naming what was moved](requirements.md#req.issues.archive-reported).

### scenario.issues.store-archive-left — Archive leaves what it cannot move

- GIVEN an Issue committed in both folders
- AND a misplaced record edited by hand
- AND another misplaced record
- WHEN a session reads the doubled Issue or lists the Issues
- AND then the store archives
- THEN the read and the list are refused with `invalid_issue`, naming both paths
- AND the archive moves the other misplaced record
- AND the archive lists both paths of the doubled Issue as left
- AND the archive lists the edited record as left
- BUT the edited record keeps its edit

This illustrates [archiving misplaced records](requirements.md#req.issues.archive) and
[naming what was left](requirements.md#req.issues.archive-reported).

### scenario.issues.command-archive — Archive from any worktree

- GIVEN a closed record committed in `.concorde/issues/` of the primary worktree and a linked worktree of the repository
- WHEN the main agent runs `archive` in the linked worktree, then again
- THEN the first exits with status 0
- AND the first prints the move
- AND the primary worktree's record lies in `closed/`
- BUT the linked worktree's copy is unchanged
- AND the second prints that nothing was moved or left

This illustrates [archiving misplaced records](requirements.md#req.issues.archive) and
[project-level Issues](requirements.md#req.issues.project-level).

## Uncommitted records

### scenario.issues.store-uncommitted-hidden — Reads show only committed records

- GIVEN a committed Issue
- AND while a second report's record is published but not yet committed, another session reads
- WHEN that session lists the Issues and reads the second one
- AND later a report's write is killed after publishing its record
- THEN the session's list names only the committed Issue
- AND the read of the second is refused with `unknown_issue`
- AND once the second is committed both are listed
- BUT the killed report's record file is neither listed nor read

This illustrates [committed visibility](requirements.md#req.issues.committed-visible).

### scenario.issues.store-sync-failed — A write that fails after publication puts its record back

- GIVEN a committed Issue and a file system that fails to sync the Issue directory after the next record is published
- WHEN the store is asked to save another report
- THEN it fails with the operating system's error instead of returning a receipt
- AND the new record is removed
- AND because the new record is removed, the directory is as it was
- AND because the new record is removed, the index is as it was
- AND because the new record is removed, the primary branch is as it was
- BUT the committed Issue stays listed

This illustrates [durable receipts](requirements.md#req.issues.durable-receipt) and
[refusals that record nothing](requirements.md#req.issues.refusal-writes-nothing).

### scenario.issues.store-put-back-failed — A record that could not be put back is put back by the next write

- GIVEN a commit Git refuses, and a failure to put the published record back too
- WHEN the store is asked to save a report
- AND then the store is asked to save another report
- AND then the store is asked to save the first report again with the same invocation and report key
- THEN the first write is refused with `recovery_failed`
- AND the refusal names Git's refusal and the failure to put the published record back
- AND the refusal says no read shows the record
- AND the record stays in the directory
- AND the record is not listed
- AND the second write removes the record first
- AND then the second write commits only its own record
- AND the second write leaves the Issue directory clean
- AND the repeated report is recorded once and committed
- AND its receipt names the same record

This illustrates [recovering uncommitted records](requirements.md#req.issues.uncommitted-recovered).

### scenario.issues.store-interrupted — What a killed write left is put back before the next write acts

- GIVEN a committed Issue
- AND another change staged in the primary worktree
- AND an untracked file in the primary worktree
- AND a killed creation whose record is uncommitted
- AND a killed append to the Issue whose record is staged
- AND a file transaction's temporary file
- WHEN the store recovers
- AND when any later write, whether a report or disposition, starts
- THEN the appended record is restored to its committed version
- AND the created record is removed
- AND the temporary file is removed
- AND the reads show the committed Issue throughout
- AND the repeated append records at the committed revision, in a commit holding only its record
- BUT the other staged change stays staged
- AND the untracked file stays untracked

This illustrates [recovering uncommitted records](requirements.md#req.issues.uncommitted-recovered)
and [removing temporaries](requirements.md#req.issues.temporaries-removed).

### scenario.issues.store-foreign-change — A record change no write made is left alone

- GIVEN a committed Issue whose record file was edited by hand, so that it no longer reads as valid
- WHEN the store saves a report to another Issue
- AND then the store is asked to close or append to the edited Issue
- AND then the store recovers
- AND after the record file is deleted, the store recovers again
- THEN the other report is committed
- AND the edit stays as it was
- AND the close and the append are refused with `uncommitted_change`
- AND the refusals name the record file and why no write left the change
- AND the file keeps the edit
- AND recovery puts nothing back
- AND recovery lists the record as left
- AND the second recovery lists the record as left because the committed record was deleted
- BUT the Issue reads as committed, open

This illustrates [kept foreign changes](requirements.md#req.issues.foreign-change-kept).

### scenario.issues.store-recover — Recovery holds the merge lock

- GIVEN a killed report's uncommitted record and another process holding the merge lock
- WHEN the store is asked to recover without waiting
- AND then a caller that holds the lock asks the store to recover
- AND then the store is asked to recover again
- THEN the first recovery is refused with `merge_busy`
- AND the record stays
- AND the second recovery removes the record and says so
- BUT the third recovery has nothing to recover

This illustrates [Issue writes under the merge lock](requirements.md#req.issues.merge-lock).

## The store check

### scenario.issues.store-check-pass — Valid records pass the store check

- GIVEN a project where the spec part is installed
- AND the project has no Issue directory or its Issues are valid and owned by Modules of its registry
- WHEN the configured store check runs
- THEN it reports no errors and no notes
- AND it exits with status zero

### scenario.issues.store-check-invalid — The store check fails for an invalid record

- GIVEN a project whose Issue directory holds a malformed record, a stray file or a misnamed record
- WHEN the configured store check runs
- THEN it reports one error naming each of them
- AND it exits with a nonzero status

### scenario.issues.store-check-unknown-owner — The store check reports an unknown owner

- GIVEN a project where the spec part is installed, and an open Issue whose owner is not a Module of its registry
- WHEN the configured store check runs
- THEN it reports an error naming the Issue and the unknown owner
- AND it exits with a nonzero status

### scenario.issues.store-check-misplaced — The store check fails for a misplaced or doubled record

- GIVEN a closed record in `.concorde/issues/`
- AND an open record in `closed/`
- AND an Issue recorded in both folders
- WHEN the configured store check runs
- THEN it reports one error per misplaced record
- AND each misplaced record's error names its status and its place
- AND each misplaced record's error says that `concorde issues archive` moves it
- AND the store check reports one error naming both paths of the doubled Issue and its repair
- AND it exits with a nonzero status

This illustrates [records in the folder of their status](requirements.md#req.issues.status-folder).

### scenario.issues.store-check-closed-unknown-owner — A closed Issue of a removed Module does not fail

- GIVEN a project where the spec part is installed
- AND a closed Issue whose owner is not a Module of its registry
- AND no other problem exists
- WHEN the configured store check runs
- THEN it reports a note naming the Issue and the unknown owner
- BUT it exits with status zero
