# Issues requirements

The Module-wide obligations of [Issues](module.md). Shapes, operations and error codes are in the
[Issue interface](interface.md); the [scenarios](scenarios.md) show the obligations in concrete
situations.

## Reporting

### req.issues.report-control — Reporting does not stop the reporter

Recording an [Issue report](../glossary.json#concept.issue-report) SHALL NOT stop the reporter.

The [main agent](../glossary.json#concept.main-agent) can record several problems and still complete
its task.

### req.issues.report-no-repair — Reporting does not start a repair

Recording an Issue report SHALL NOT start a repair of the problem it describes.

A repair is ordinary work the main agent starts later in a task of its own.

### req.issues.report-no-outcome — Reporting does not change the task outcome

Recording an Issue report SHALL NOT change the outcome of the task in which the problem was found.

Whether a problem stops the task is decided separately.

### req.issues.caller-provenance — Provenance comes from the command

The bookkeeping command SHALL supply every provenance field of a report itself, never take one from
the report file.

A report file with a provenance field is refused as malformed, because a report has no such field.

### req.issues.main-agent-actor — The command attributes Issue writes to the session

The bookkeeping command SHALL record as the source agent of each report and the actor of each
disposition it writes `main-agent`, or, called by the [project MCP server](../glossary.json#concept.project-mcp-server)'s Issue tools, the calling
session: `task-session` in a task worktree bound as a workspace and `main-agent` in any other.

This is attribution by the command and the tools, not authentication or a restriction on the
store's library callers. Workers never record or dispose Issues; an [Operation](../glossary.json#concept.operation)'s host may record
them through the store with the provenance it vouches for.

### req.issues.report-checked — A report names a registered owner and existing evidence

The bookkeeping command SHALL refuse a report whose `owner_target_id` is neither `null` nor a
[Module](../glossary.json#concept.module) of the primary worktree's registry, whose evidence path
does not exist in the worktree it reports from or, for a report with an origin, in the origin
project, or whose
[error chain](../glossary.json#concept.error-chain) is not an error of the Framework's error
contract.

A `null` owner is accepted: the report's reporting Module is then the registry's root Module, and
the command refuses the report with `no_reporting_module` when the registry has no single root
([provenance](interface.md#provenance)).

### req.issues.durable-receipt — A receipt means the report is committed

The [Issue](../glossary.json#concept.issue) store SHALL return a receipt, or a disposition's
revision, only after the record is durably published and committed on the primary branch.

### req.issues.tier-required — Every report carries a tier

The Issue store SHALL accept a report only when it carries one of the [tiers](module.md#tiers)
`suggestion`, `obvious-fix`, `preferred-fix` and `decision-needed`.

Every record it creates therefore holds only tiered reports; a record written before tiers existed
keeps its untiered reports unchanged and stays valid.

### req.issues.own-failures — The Issue system never reports itself

The bookkeeping command and the project MCP server's Issue tools SHALL say, in every refusal that is
a failure of the Issue system itself, that its error chain is carried in the [decision log](../glossary.json#concept.decision-log),
escalation or [run result](../glossary.json#concept.run-result) and never reported as an Issue.

An Issue system that failed cannot be trusted to record its own failure, so a session relying on it
to do so would wait for ever ([failures of the Issue system](module.md#failures-of-the-issue-system)).

### req.issues.specific-refusals — Refusals name what is wrong

The bookkeeping command SHALL answer every refusal with an error code and a message naming the
Issue, file, argument or field concerned.

The exit status is 2 for an unusable request (codes `usage`, `not_a_project` and
`unreadable_file`) and 1 for every other refusal, as the
[bookkeeping command](interface.md#bookkeeping-command) defines.

### req.issues.refusal-writes-nothing — A refused request writes no record

The bookkeeping command SHALL NOT write a record for a request it refuses.

## Records

### req.issues.store-writes — Only the store writes Issue records

Every program write that creates, appends to or disposes an Issue record SHALL go through
the Issue store.

Nobody edits a record by hand; Git operations that move committed record files, such as merging a
branch that still carries a record an earlier Concorde wrote there, are not store writes.

### req.issues.project-level — The primary worktree keeps the project's Issues

The Issue store SHALL write records only in the primary worktree of the project's repository.

The bookkeeping command and the project MCP server's Issue tools read and write that worktree's
records from any worktree of the repository, apart from `check`, which checks the worktree it runs
in.

Every session and run sees the same Issues at once, and every Issue has one project-wide identity
from the moment it is reported.

### req.issues.retention — Reports are never rewritten

The Issue store SHALL NOT modify or remove an accepted report, including when the Issue is closed or
reopened.

### req.issues.closed-kept — Closed Issues stay recorded

The Issue store SHALL NOT delete an Issue record file.

A closed Issue keeps its reports and dispositions, so it can be shown and reopened.

### req.issues.list-filtered — A listing reads only the Issues asked for

The bookkeeping command's `list` and the `issue_list` tool SHALL list only the Issues that pass
every filter given: a status keeps the Issues with that status, a Module those whose latest report
has it as owner or reporting Module, and tiers those whose latest report has one of them.

Given no filter, they list every Issue, open and closed.

A session checking for an Issue that already tracks its problem reads the open Issues of the Module
concerned, which fit its context however many Issues the project keeps.

### req.issues.revision-checked — Writes never overwrite a newer record

The Issue store SHALL write a record only over the exact revision its caller read.

A creation requires that the record does not exist; an append and a disposition name the revision
they replace, and a mismatch fails with `stale_issue`.

### req.issues.merge-lock — Issue writes take the merge lock

The Issue store SHALL perform every write while holding the primary worktree's
[merge lock](../glossary.json#concept.merge-lock), or while its caller holds it, and only while no
task's merge into the primary branch is unfinished.

A write so never commits between a merge commit and the checks that decide whether it stays.

### req.issues.commit-alone — An Issue commit commits its record alone

The Issue store SHALL commit each write as a commit of that record alone on the primary branch, or,
when Git does not commit it, put the record back as it was and refuse the write.

Other changes of the primary worktree, staged or not, stay as they were.

### req.issues.status-derived — Status agrees with disposition history

The Issue store SHALL accept a record only when its status is the result of applying its legal
disposition sequence to the initial `open` state.

An empty disposition history means `open`; `resolved`, `duplicate` and `not-actionable` close it,
and `reopened` opens it again. These reasons are not additional statuses. Reports do not change
status. A legal disposition sequence is one in which every disposition obeys
[legal transitions](#req.issues.legal-transitions); that requirement governs accepting a new
disposition, this one reading a whole record. See the [lifecycle](module.md#lifecycle) and
[record rules](interface.md#record-file).

### req.issues.legal-transitions — Dispositions alternate

The Issue store SHALL accept a closing disposition only for an open Issue and a reopening only for a
closed Issue.
