# Issues requirements

The Module-wide obligations of [Issues](module.md). Shapes, operations and error codes are in the
[Issue interface](interface.md); the [scenarios](scenarios.md) show the obligations in concrete
situations.

## Reporting

### req.issues.report-control — Reporting does not control execution

Accepting an Issue report SHALL NOT stop the reporter, start a repair or change the outcome of the
reporter's task.

A worker can report several problems and still complete its task. Whether a problem stops the task
is stated separately, by a Blocker in the worker's result.

### req.issues.report-limits — Reports stay within the reporter's limits

The reporting service SHALL refuse a report whose owner, evidence paths or appended Issue lie
outside the limits its caller admitted for that reporter.

### req.issues.host-provenance — Provenance comes from the caller

The reporting service SHALL take every provenance field of a report from its caller, never from the
report.

### req.issues.durable-receipt — A receipt means the report is on disk

The Issue store SHALL return a receipt only after the record holding the report is durably
published.

### req.issues.references — Results reference only known reports

A stage result SHALL reference only Issue reports made through the same reporting service or
explicitly admitted as that reporter's input.

## Records

### req.issues.host-writes — Only the store writes Issue records

Every Host write that creates, appends to, disposes or restores an Issue record SHALL go through the
Issue store.

Git operations that move committed record files between branches, such as creating a candidate,
delivering or merging, are not store writes, and the store never runs Git.

### req.issues.retention — Reports are never rewritten

The Issue store SHALL NOT modify or remove an accepted report, including when the Issue is closed or
reopened.

Restoring an unfinished close removes only the disposition that close added.

### req.issues.closed-kept — Closed Issues stay recorded

The Issue store SHALL NOT delete an Issue record file.

A closed Issue keeps its reports and dispositions, so it can be shown and reopened.

### req.issues.revision-checked — Writes never overwrite a newer record

The Issue store SHALL write a record only over the exact revision its caller read.

A creation requires that the record does not exist; an append, a disposition and a restoration name
the revision they replace, and a mismatch fails with `stale_issue`.

### req.issues.repository-lock — One lock serializes every store write

The Issue store SHALL perform every write while holding the one exclusive lock kept in the primary
worktree's run records.

### req.issues.legal-transitions — Dispositions alternate

The Issue store SHALL accept a closing disposition only for an open Issue and a reopening only for a
closed Issue.
