# Issues requirements

The Module-wide obligations of [Issues](module.md). The [Issue interface](interface.md) gives:

- Shapes.
- Operations.
- Error codes.

The [scenarios](scenarios.md) show the obligations in concrete situations.

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

The bookkeeping command SHALL supply every provenance field of a report itself, unless its caller gives the whole provenance in a provenance file of its own with `--provenance`, and never take one from the report file.

A report file with a provenance field is refused as malformed, because a report has no such field.
A caller that gives `--provenance` vouches for it, as a library caller of the store does.

### req.issues.main-agent-actor — The command attributes Issue writes to the session

The bookkeeping command SHALL record as the source agent of each report whose provenance it supplies and the actor of each disposition it writes `main-agent`, or, called by the [project MCP server](../glossary.json#concept.project-mcp-server)'s Issue tools, the calling session: `task-session` in a task worktree bound as a workspace and `main-agent` in any other.

This is attribution by the command and the tools, not authentication or a restriction on the
store's library callers. Workers never record or dispose Issues. An
[Operation](../glossary.json#concept.operation)'s host may record them with the provenance it
vouches for, through the store or through the command's `report --provenance`.
That command action records that provenance as given.

### req.issues.report-owner-registered — A report names a registered owner

The bookkeeping command SHALL refuse a report when all these conditions hold:

- The spec part is installed.
- The command supplies the report's provenance.
- The report's `owner_target_id` is neither `null` nor a
  [Module](../glossary.json#concept.module) of the primary worktree's registry.

A `null` owner is accepted. The report's reporting Module is then the registry's root Module.
When the registry has no single root, the command refuses the report with `no_reporting_module`
([provenance](interface.md#provenance)). Where the spec part is not installed, the owner is a plain
label the command takes as given. In that case, a `null` owner is refused with
`no_reporting_module`, since no registry names a root. The registry file `.concorde/specs.json`
tells which: the spec part counts as installed exactly where that file exists.
A report given with `--provenance` names the Module its caller vouches for. That Module may be one
its task adds, so the command checks no owner of that report.
When `report --check` only checks a report with an `origin`, that report resolves no reporting
Module, since the project that records it resolves one. Such a report can be a
[defect report](../glossary.json#concept.defect-report) about to be handed to the
[Concorde repository](../glossary.json#concept.concorde-repository).
Because the project that records such a report resolves its reporting Module, its `null` owner is
not refused even where the spec part is not installed.

### req.issues.report-evidence-present — A report's evidence exists

The bookkeeping command SHALL refuse a report whose provenance it supplies and one of whose evidence paths does not exist in the
worktree it reports from or, for a report with an origin, in the origin project.

### req.issues.report-error-chain — A report's error chain follows the error contract

The bookkeeping command SHALL refuse a report whose
[error chain](../glossary.json#concept.error-chain) is not an error of the Framework's error
contract.

### req.issues.durable-receipt — A receipt means the report is committed

The [Issue](../glossary.json#concept.issue) store SHALL return a receipt, or a disposition's revision, only after the record is durably published and committed on the primary branch.

A repeated report returns its earlier receipt only when the committed record holds that receipt.
Therefore, every receipt names a committed report.

### req.issues.tier-required — Every report carries a tier

The Issue store SHALL accept a report only when it carries one of these [tiers](module.md#tiers):

- `suggestion`.
- `obvious-fix`.
- `preferred-fix`.
- `decision-needed`.

Every record it creates therefore holds only tiered reports. A record written before tiers
existed keeps its untiered reports unchanged. That record stays valid.

### req.issues.severity-required — Every report carries a severity

The Issue store SHALL accept a report only when it carries one of these
[severities](module.md#severities):

- `critical`.
- `high`.
- `medium`.
- `low`.

Every record it creates therefore holds only reports with a severity. A record written before
severities existed keeps its reports without one unchanged. That record stays valid.

### req.issues.own-failures — The Issue system never reports itself

The bookkeeping command and the project MCP server's Issue tools SHALL say, in every refusal that is
a failure of the Issue system itself, that its error chain is carried in the [decision log](../glossary.json#concept.decision-log),
escalation or [run result](../glossary.json#concept.run-result) and never reported as an Issue.

An Issue system that failed cannot be trusted to record its own failure. Therefore, a session that
relies on it to do so would wait for ever
([failures of the Issue system](module.md#failures-of-the-issue-system)).

### req.issues.specific-refusals — Refusals name what is wrong

The bookkeeping command SHALL answer every refusal with an error code and a message naming the
concerned item from these kinds:

- Issue.
- File.
- Argument.
- Field.

For an unusable request, the exit status is 2. The codes for an unusable request are:

- `usage`.
- `not_a_project`.
- `unreadable_file`.

For every other refusal, the exit status is 1. The
[bookkeeping command](interface.md#bookkeeping-command) defines these exit statuses.

### req.issues.refusal-writes-nothing — A refused request records nothing

For a request it refuses, the bookkeeping command SHALL NOT commit a record or leave one a read
shows.

It writes nothing of its own either, with one exception. A write refused with `recovery_failed`
leaves its published record uncommitted until the next recovery puts it back. The reason is that
the record it published could not be put back.
Before a write checks its request, it runs [recovery](#req.issues.uncommitted-recovered).
That recovery puts back only what earlier writes published but did not commit. The recovery stays
done whatever the request's outcome.

## Records

### req.issues.store-writes — Only the store writes Issue records

Every program write of these kinds SHALL go through the Issue store:

- A write that creates an Issue record.
- A write that appends to an Issue record.
- A write that disposes an Issue record.

Nobody edits a record by hand. Git operations that move committed record files are not store
writes. One such operation merges a branch that still carries a record an earlier Concorde wrote
there.

### req.issues.project-level — The primary worktree keeps the project's Issues

The Issue store SHALL write records only in the primary worktree of the project's repository.

Apart from `check`, the bookkeeping command and the project MCP server's Issue tools read and
write that worktree's records from any worktree of the repository. That `check` action checks the
worktree it runs in.

Every session and run sees the same Issues at once. From the moment it is reported, every Issue
has one project-wide identity.

### req.issues.retention — Reports are never rewritten

The Issue store SHALL NOT modify or remove an accepted report, including when the Issue is closed or
reopened.

### req.issues.closed-kept — Closed Issues stay recorded

The Issue store SHALL NOT delete a committed Issue record, other than removing it from one folder
in the commit that adds it to the other.

Recovery removes only a record file no commit holds. No read ever showed that file.

A closed Issue keeps its reports and dispositions, so it can be shown and reopened.

### req.issues.status-folder — A record lies in the folder of its status

The Issue store SHALL write an open Issue's record at `.concorde/issues/<id>.md` and a closed
Issue's at `.concorde/issues/closed/<id>.md`, moving it there in the commit of the write that
changes its status or finds it in the other folder.

The records seen directly in `.concorde/issues/` are therefore the open Issues. Reads find a
record in either folder. When an Issue is committed in both folders, reads refuse it.
The store check reports each of these with its repair
([record file](interface.md#record-file)):

- A record whose folder does not match its status.
- An Issue recorded in both folders.

### req.issues.archive — Misplaced records are moved into their folder

The bookkeeping command's `archive` SHALL move every committed record of the primary worktree whose
folder does not match its status into the folder its status names, unchanged, in one commit under
the merge lock.

It leaves an Issue committed in both folders and a record holding a change no Issue write made.
The reason is that moving either would decide what only its inspection can.
With nothing to move, it commits nothing.

### req.issues.archive-reported — Archive names what it moved and left

The bookkeeping command's `archive` SHALL name each record it moved, with the path it moved from and
to, and each misplaced record it left, with the reason it left it.

Whoever runs it learns which records still need inspection without reading the commit.

### req.issues.list-filtered — A listing reads only the Issues asked for

The bookkeeping command's `list` and the `issue_list` tool SHALL list only the Issues that pass
every filter given, with each filter applied as follows:

- A status keeps the Issues with that status.
- A Module keeps the Issues whose latest report has it as owner or reporting Module.
- Tiers keep the Issues whose latest report has one of them.
- Severities keep the Issues whose latest report has one of them.

Given no filter, they list every Issue, open and closed.

A session checking for an Issue that already tracks its problem reads the open Issues of the
Module concerned. Those Issues fit its context however many Issues the project keeps.

### req.issues.list-by-severity — A listing can start from the most severe Issues

Asked to sort by severity, the bookkeeping command's `list` and the `issue_list` tool SHALL list
the Issues in this order:

- Most severe first.
- Among Issues of equal severity, by tier from `decision-needed` down to `suggestion`.
- Then, in the order they were first reported.
- Issues without a severity or tier after every one with it.

Without that request they list the Issues by identity. Every row shows the Issue's severity
beside its tier. When the Issue's latest report has no severity, the row shows none beside its
tier. This is so that whoever chooses what to fix next can start from the most severe problems.

### req.issues.committed-visible — Reads show only committed records

The Issue store's reads SHALL return only the records the primary worktree's last commit holds, never a record file that is not committed or differs from its committed version.

A record is visible exactly when its write is committed, which is before the write is acknowledged.
In these cases, a reader sees the records as they were committed:

- During a write.
- After a write that failed.
- After a write that was killed.

### req.issues.uncommitted-recovered — Uncommitted records are put back before any write

Before it reads the record it changes, every Issue write SHALL put back to its committed version,
or remove when no commit holds it, every record an earlier write published but did not commit,
under the [merge lock](../glossary.json#concept.merge-lock) and committing nothing.

A write that left such a record gave no receipt, so putting it back loses nothing acknowledged.
Its writer may repeat the write. When a write fails after publishing its record, it puts the
record back itself before it refuses. A move between the folders is put back whole. The record
is restored where it was committed. The record is removed from the folder it was published in.

### req.issues.temporaries-removed — An interrupted file transaction's temporaries are removed

Before it reads the record it changes, every Issue write SHALL remove the temporary files an
interrupted [file transaction](../glossary.json#concept.file-transaction) left in
`.concorde/issues/` and its `closed/` folder.

A killed write leaves them beside the records. They are never records. Nothing else removes them.

### req.issues.foreign-change-kept — A record change no write made is kept

Recovery SHALL leave as it is a record change that no Issue write leaves.

While such a change stands, the Issue store refuses every write of that Issue with
`uncommitted_change`. Writes of other Issues go on. Recovery touches only records an earlier
write left and temporary files. It never touches another change of the primary worktree.

### req.issues.revision-checked — Writes never overwrite a newer record

The Issue store SHALL write a record only over the exact revision its caller read.

A creation requires that the record does not exist. An append and a disposition name the revision
they replace. When the revision mismatches, the write fails with `stale_issue`.

### req.issues.merge-lock — Issue writes take the merge lock

The Issue store SHALL perform every write while holding the primary worktree's
[merge lock](../glossary.json#concept.merge-lock), or while its caller holds it.

As a result, writes never overlap any of these:

- One another.
- A task's merge.
- A task's open.
- A task's close.

### req.issues.no-write-during-merge — No Issue write while a merge is unfinished

Where the coordination part is installed, the Issue store SHALL refuse every write, whether it took the merge lock or its caller holds it, while a task's merge into the primary branch is unfinished.

As a result, a write
never commits between a merge commit and the checks that decide whether it stays. The store
learns of an unfinished merge from Tasks' [task records](../glossary.json#concept.task-record).
These use the format the coordination part publishes. The store never learns of an unfinished
merge from the coordination part's code. A task record the store cannot read may be the merging task's. For that
reason, the store refuses the write then too, rather than pass over the record. The refusal uses
`unreadable_task_record` and names the record. Without the coordination part there is no task
merge. In that case, the merge lock alone orders the writes.

### req.issues.tools-as-command — The Issue tools answer as the command

Each Issue tool the issues part registers with the [project MCP server](../glossary.json#concept.project-mcp-server) SHALL answer and refuse exactly as the bookkeeping command's action it names.

The tools are the issues part's own. The issues part registers them through its
[part registration](../glossary.json#concept.part-registration). Where the issues part is not
installed none of them exists ([MCP tools](interface.md#mcp-tools)). The calling session alone is
theirs, as reporter and actor ([attribution](#req.issues.main-agent-actor)).

### req.issues.tools-no-wait — The Issue tools never wait for the merge lock

While another process holds the merge lock, each Issue tool that writes SHALL refuse with
`merge_busy` at once, without waiting.

A tool call holds its session until it answers, so a busy lock is reported at once. The report
names the lock's holder. The session decides whether to wait for the lock's release and repeat
the call. The command's own writes wait instead, up to their wait.

### req.issues.own-check — Issues checks its own records

Issue records SHALL be validated as a project check only by the Issue store's check, `concorde issues check` and the tool `issue_check`, which this Module's [configured check](../glossary.json#concept.configured-check) runs.

The Spec tooling knows nothing of Issues, so `concorde spec-validation` never reads a record.
Whenever this Module's configured check runs, the records are still checked. Where the project
configures a merge's checks, they include this Module's configured check. The store's own reads
validate every record they return as well. This validation is no project check.

### req.issues.commit-alone — An Issue commit commits its record alone

The Issue store SHALL commit each report or disposition as a commit of that record alone on the
primary branch, with the path it left when the write moved it, and an archive as one commit of the
records it moves, with the paths they left, and only them.

Other changes of the primary worktree, staged or not, stay as they were. When Git refuses a
write's commit, the write puts its record back. The write then refuses, as the
[store operations](interface.md#store-operations) say.

### req.issues.status-derived — Status agrees with disposition history

The Issue store SHALL accept a record only when its status is the result of applying its legal
disposition sequence to the initial `open` state.

An empty disposition history means `open`. These reasons close it:

- `resolved`.
- `duplicate`.
- `not-actionable`.

The reason `reopened` opens it again. These reasons are not additional statuses. Reports do not
change status. A legal disposition sequence is one in which every disposition obeys
[legal transitions](#req.issues.legal-transitions). That requirement governs accepting a new
disposition. This requirement governs reading a whole record. See the
[lifecycle](module.md#lifecycle) and [record rules](interface.md#record-file).

### req.issues.legal-transitions — Dispositions alternate

The Issue store SHALL accept a closing disposition only for an open Issue and a reopening only for a closed Issue.
