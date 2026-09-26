# Issues requirements

The Module-wide obligations of [Issues](module.md). Shapes, operations and error codes are in the
[Issue interface](interface.md); the [scenarios](scenarios.md) show the obligations in concrete
situations.

## Reporting

### req.issues.report-control — Reporting does not control execution

Recording an Issue report SHALL NOT stop the reporter, start a repair or change the outcome of the
task in which the problem was found.

The main agent can record several problems and still complete its task. Whether a problem stops the
task is decided separately.

### req.issues.caller-provenance — Provenance comes from the command

The bookkeeping command SHALL supply every provenance field of a report itself, never take one from
the report file.

A report file with a provenance field is refused as malformed, because a report has no such field.

### req.issues.main-agent-actor — The command attributes Issue writes to the main agent

The bookkeeping command SHALL record `main-agent` as the source agent of each report and the actor
of each disposition it writes.

This is attribution by the command, not authentication or a restriction on the store's library
callers. Workers and Operations do not record or dispose Issues automatically in this version;
the main agent decides what to record after reading their results.

### req.issues.report-checked — A report names a registered owner and existing evidence

The bookkeeping command SHALL refuse a report whose owner is not a registered Module, whose
evidence path does not exist in the project or, for a report with an origin, in the origin project,
or whose error chain is not an error of the Framework's error contract.

### req.issues.durable-receipt — A receipt means the report is on disk

The Issue store SHALL return a receipt only after the record holding the report is durably
published.

### req.issues.specific-refusals — Refusals name what is wrong

The bookkeeping command SHALL answer every refusal with an error code and a message naming the
Issue, file, argument or field concerned, without writing a record.

The exit status is 2 when the request is unusable and 1 when the Issue rules refuse it.

## Records

### req.issues.store-writes — Only the store writes Issue records

Every program write that creates, appends to or disposes an Issue record SHALL go through
the Issue store.

Git operations that move committed record files between branches, such as committing on a task
branch or merging it, are not store writes, and the store never runs Git.

### req.issues.retention — Reports are never rewritten

The Issue store SHALL NOT modify or remove an accepted report, including when the Issue is closed or
reopened.

### req.issues.closed-kept — Closed Issues stay recorded

The Issue store SHALL NOT delete an Issue record file.

A closed Issue keeps its reports and dispositions, so it can be shown and reopened.

### req.issues.revision-checked — Writes never overwrite a newer record

The Issue store SHALL write a record only over the exact revision its caller read.

A creation requires that the record does not exist; an append and a disposition name the revision
they replace, and a mismatch fails with `stale_issue`.

### req.issues.worktree-lock — One lock serializes the writes into a worktree

The Issue store SHALL perform every write into a worktree while holding that worktree's one
exclusive Issue lock.

### req.issues.status-derived — Status agrees with disposition history

The Issue store SHALL accept a record only when its status is the result of applying its legal
disposition sequence to the initial `open` state.

An empty disposition history means `open`; `resolved`, `duplicate` and `not-actionable` close it,
and `reopened` opens it again. These reasons are not additional statuses. Reports do not change
status. See the [lifecycle](module.md#lifecycle) and [record rules](interface.md#record-file).

### req.issues.legal-transitions — Dispositions alternate

The Issue store SHALL accept a closing disposition only for an open Issue and a reopening only for a
closed Issue.
