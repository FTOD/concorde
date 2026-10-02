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

### req.issues.report-owner-registered — A report names a registered owner

The bookkeeping command SHALL refuse a report whose `owner_target_id` is neither `null` nor a
[Module](../glossary.json#concept.module) of the primary worktree's registry.

A `null` owner is accepted: the report's reporting Module is then the registry's root Module, and
the command refuses the report with `no_reporting_module` when the registry has no single root
([provenance](interface.md#provenance)).

### req.issues.report-evidence-present — A report's evidence exists

The bookkeeping command SHALL refuse a report one of whose evidence paths does not exist in the
worktree it reports from or, for a report with an origin, in the origin project.

### req.issues.report-error-chain — A report's error chain follows the error contract

The bookkeeping command SHALL refuse a report whose
[error chain](../glossary.json#concept.error-chain) is not an error of the Framework's error
contract.

### req.issues.durable-receipt — A receipt means the report is committed

The [Issue](../glossary.json#concept.issue) store SHALL return a receipt, or a disposition's
revision, only after the record is durably published and committed on the primary branch.

A repeated report returns its earlier receipt only when the committed record holds it, so every
receipt names a committed report.

### req.issues.tier-required — Every report carries a tier

The Issue store SHALL accept a report only when it carries one of the [tiers](module.md#tiers)
`suggestion`, `obvious-fix`, `preferred-fix` and `decision-needed`.

Every record it creates therefore holds only tiered reports; a record written before tiers existed
keeps its untiered reports unchanged and stays valid.

### req.issues.severity-required — Every report carries a severity

The Issue store SHALL accept a report only when it carries one of the
[severities](module.md#severities) `critical`, `high`, `medium` and `low`.

Every record it creates therefore holds only reports with a severity; a record written before
severities existed keeps its reports without one unchanged and stays valid.

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

### req.issues.refusal-writes-nothing — A refused request records nothing

The bookkeeping command SHALL NOT commit a record, or leave one a read shows, for a request it
refuses.

It writes none either, except that a write refused with `recovery_failed`, because the record it
had published could not be put back, leaves that record uncommitted until the next recovery puts
it back ([recovery](#req.issues.uncommitted-recovered)).

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

The Issue store SHALL NOT delete a committed Issue record, other than removing it from one folder
in the commit that adds it to the other.

Recovery removes only a record file no commit holds, which no read ever showed.

A closed Issue keeps its reports and dispositions, so it can be shown and reopened.

### req.issues.status-folder — A record lies in the folder of its status

The Issue store SHALL write an open Issue's record at `.concorde/issues/<id>.md` and a closed
Issue's at `.concorde/issues/closed/<id>.md`, moving it there in the commit of the write that
changes its status or finds it in the other folder.

The records seen directly in `.concorde/issues/` are so the open Issues. Reads find a record in
either folder, and refuse an Issue committed in both; the store check reports a record whose folder
does not match its status and an Issue recorded in both folders, each with its repair
([record file](interface.md#record-file)).

### req.issues.archive — Misplaced records are moved into their folder

The bookkeeping command's `archive` SHALL move every committed record of the primary worktree whose
folder does not match its status into the folder its status names, unchanged, in one commit under
the merge lock, and name each record it moved and each misplaced record it left.

It leaves an Issue committed in both folders and a record holding a change no Issue write made,
since moving either would decide what only its inspection can; with nothing to move it commits
nothing.

### req.issues.list-filtered — A listing reads only the Issues asked for

The bookkeeping command's `list` and the `issue_list` tool SHALL list only the Issues that pass
every filter given: a status keeps the Issues with that status, a Module those whose latest report
has it as owner or reporting Module, tiers those whose latest report has one of them, and
severities those whose latest report has one of them.

Given no filter, they list every Issue, open and closed.

A session checking for an Issue that already tracks its problem reads the open Issues of the Module
concerned, which fit its context however many Issues the project keeps.

### req.issues.list-by-severity — A listing can start from the most severe Issues

Asked to sort by severity, the bookkeeping command's `list` and the `issue_list` tool SHALL list
the Issues most severe first, those of equal severity by tier from `decision-needed` down to
`suggestion`, then in the order they were first reported, and the Issues without a severity or
tier after every one with it.

Without that request they list the Issues by identity. Every row shows the Issue's severity, or
none when its latest report has none, beside its tier, so that whoever chooses what to fix next can
start from the most severe problems.

### req.issues.committed-visible — Reads show only committed records

The Issue store's reads SHALL return only the records the primary worktree's last commit holds,
never a record file that is not committed or differs from its committed version.

A record is visible exactly when its write is acknowledged, and a reader during a write, or after
one that failed or was killed, sees the records as they were committed.

### req.issues.uncommitted-recovered — Uncommitted records are put back before any write

Before it reads the record it changes, every Issue write SHALL put back to its committed version,
or remove when no commit holds it, every record an earlier write published but did not commit,
and remove the temporary files of an interrupted
[file transaction](../glossary.json#concept.file-transaction) there, under the
[merge lock](../glossary.json#concept.merge-lock) and committing nothing.

A write that left such a record gave no receipt, so putting it back loses nothing acknowledged,
and its writer may repeat it. A write that fails after publishing its record puts it back itself
before it refuses. A move between the folders is put back whole: the record is restored where it
was committed and removed from the folder it was published in.

### req.issues.foreign-change-kept — A record change no write made is kept

Recovery SHALL leave as it is a record change that no Issue write leaves.

While such a change stands, the Issue store refuses every write of that Issue with
`uncommitted_change`, and writes of other Issues go on. Recovery touches only records an earlier
write left and temporary files, never another change of the primary worktree.

### req.issues.revision-checked — Writes never overwrite a newer record

The Issue store SHALL write a record only over the exact revision its caller read.

A creation requires that the record does not exist; an append and a disposition name the revision
they replace, and a mismatch fails with `stale_issue`.

### req.issues.merge-lock — Issue writes take the merge lock

The Issue store SHALL perform every write while holding the primary worktree's
[merge lock](../glossary.json#concept.merge-lock), or while its caller holds it.

Writes so never overlap one another, or a task's merge, open or close.

### req.issues.no-write-during-merge — No Issue write while a merge is unfinished

The Issue store SHALL refuse every write, whether it took the merge lock or its caller holds it,
while a task's merge into the primary branch is unfinished.

A write so never commits between a merge commit and the checks that decide whether it stays.

### req.issues.commit-alone — An Issue commit commits its record alone

The Issue store SHALL commit each write as a commit of that record alone on the primary branch,
with the path it left when the write moved it.

Other changes of the primary worktree, staged or not, stay as they were. A write whose commit Git
refuses puts its record back and refuses, as the [store operations](interface.md#store-operations)
say.

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
