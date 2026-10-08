# Kernel

## Purpose

The Kernel is the kernel [part](../glossary.json#concept.part). It holds the few contracts
Concorde's parts cooperate through without importing each other. Coordination writes a
[workspace binding](../glossary.json#concept.workspace-binding) for these readers:

- Execution
- Workflows
- Method

Method makes a [delivery commit](../glossary.json#concept.delivery-commit) that Coordination
recognizes. Coordination's Tasks and the issues part's Issues take the same
[merge lock](../glossary.json#concept.merge-lock). Tasks writes the
[unfinished-merge marker](../glossary.json#concept.unfinished-merge-marker) that Issues and Method's
project review read. Every level records the same
[trace node](../glossary.json#concept.trace-node). Every level reports with the same
[error chain](../glossary.json#concept.error-chain). Each of these agreements belongs to neither
side, so it lives here. Every part that cooperates through an agreement depends on the Kernel
instead of on the part at the other end.

The Kernel holds:

- Formats
- Conventions
- The small library that reads and writes them

It decides nothing about the work. It knows none of these:

- A task
- A run
- An [Operation](../glossary.json#concept.operation)
- A [Spec](../glossary.json#concept.spec)

A contract here may name an example of who uses it. It never relies on that user. The Kernel
depends on no part. Every part depends on it but two:

- The Spec tooling, the spec part, whose Spec core keeps its own copy of the data utilities it
  shares with the Kernel
- Distribution, which reaches the parts only through their registrations

The Kernel's code is a small library with these functions:

- Reading and checking a workspace binding
- Registering and checking typed values
- Applying a file transaction
- Finding and verifying the delivery commits of a workspace
- Taking the workspace lock and the merge lock
- Reading, writing and removing the unfinished-merge marker

Each function refuses with a stable code. Its caller turns that code into its own error link.
Tracing, the Kernel's child, adds the trace nodes and locks ([Library](contracts.md#library)).
The Kernel's precise obligations are its [requirements](requirements.md).
Its [scenarios](scenarios.md) show them at work.

For example, when its code loads, a part that keeps notes registers the type `example-note` at
version 1. Its schema requires a nonblank `text`. To record a note, the part makes the typed value
of the data `{"text": "Retry limit agreed."}`. It receives a checked copy,
`{"type_id": "example-note", "schema_version": 1, "data": {"text": "Retry limit agreed."}}`
([Typed values](contracts.md#typed-values)). While it holds the merge lock, the part applies a
file transaction below the primary worktree. The transaction creates `notes/n-1.json` holding
that value. Since the file must not exist yet, the transaction uses the `before_digest` `null`.
The part allows only that path ([File transactions](contracts.md#file-transactions)).
Once the file is renamed into place, the transaction returns `["notes/n-1.json"]`.
If another writer creates the file first, the transaction is refused with `stale_proposal` before
writing anything. The part then commits the file. It then releases the lock. The Kernel leaves
both actions to the part ([Library](contracts.md#library)).

## Core concepts

The Kernel's terms fall into three groups:

- The data parts exchange
- The workspace one part prepares and others work in
- The marks and locks by which they take turns

Its child [Tracing](tracing/module.md) explains:

- The trace node
- The [trace](../glossary.json#concept.trace)
- The error chain

### Data parts exchange

<a id="concept.typed-value"></a><a id="concept.file-transaction"></a>

When its owner's contract designates a value as a typed value, it is a
**[typed value](../glossary.json#concept.typed-value)** `{type_id, schema_version, data}`.
Its `data` is checked against the schema its owner registered for that type and version.
An example is a [trace node](../glossary.json#concept.trace-node)'s content, such as a run's steps
or a worker round's audit. When its code loads, the owner registers its own types.
A schema of one part may embed a value of another part's type by name, so neither imports the other.
Not every structured record is a typed value. Each of these keeps the representation its own
contract defines:

- A workspace binding
- A [run result](../glossary.json#concept.run-result)
- A grant
- An Issue record file

Each of these records is checked against its contract's schema without an envelope.
A **[file transaction](../glossary.json#concept.file-transaction)** writes a set of whole files,
each bound to the digest of the bytes it replaces. When a write or its final check fails while the
process runs, the transaction restores every file it wrote. The operating system may refuse that
restoration. When the operating system refuses restoration, the failure names every file still
holding its new content. A process killed in the middle restores nothing. Every writer that uses
a file transaction therefore says how its records are recovered from both cases. A transaction
protects nothing against another writer. Its caller holds whatever lock its records require for
the whole transaction. The [contracts](contracts.md#typed-values) give both formats exactly.

A killed process takes none of the paths below. It leaves every file renamed into place with its
new content. The [file transaction contract](contracts.md#file-transactions) gives the outcomes
of one transaction exactly:

```d2 illustrative
direction: right
check: "Check the list:\nform, allowed paths,\nbefore_digest"
writes: "Write each file:\ntemporary file, rename"
final: Final check
done: "Success:\nthe written paths"
refused: "Refused, nothing\nwritten"
restore: "Restore every\nwritten file"
restored: "The failure,\nevery file restored"
unrestored: "system_error naming\nthe files not restored"
check -> refused: "malformed, not allowed\nor stale"
check -> writes: valid
writes -> final: all written
final -> done: passes
writes -> restore: "a write fails, a file\nturned stale, interrupted"
final -> restore: "fails or\ninterrupted"
restore -> restored: every restoration done
restore -> unrestored: "the operating system\nrefuses one"
```

### The workspace

<a id="concept.workspace"></a><a id="concept.workspace-binding"></a>

A **[workspace](../glossary.json#concept.workspace)** is one worktree prepared for a bounded piece
of work. Once its **[workspace binding](../glossary.json#concept.workspace-binding)** exists, the
workspace exists. Whoever prepares the workspace writes `.concorde/workspace.json` at the
worktree's root, as the [binding contract](contracts.md#contract.kernel.workspace-binding) defines.
The binding names:

- The workspace
- The absolute root it lies in
- Its goal
- The [Modules](../glossary.json#concept.module) it works on
- The branch and base commit it works from
- The **workspace folder** where the work done in it is traced
- The `.concorde` directory whose `locks/` holds its locks

In Concorde, [`concorde task open`](../coordination/tasks/module.md) writes the binding into each
new task worktree. It names the workspace after the task. It places the workspace folder inside
the task's own folder, so that a task's [trace](../glossary.json#concept.trace) holds every run of
its workspace. The parts that work in the workspace read the binding. They never write it.
None of them learns that the folder belongs to a task, since another preparer may place it anywhere.
When a binding breaks its contract or names a root other than the worktree it lies in, it is
refused rather than trusted. The reason is that a copied binding would bind the wrong workspace.

The binding names the workspace folder rather than letting a reader derive it.
This lets whoever prepares the workspace decide where its traces belong.
The binding records only what the work needs to start. It never records:

- What was done there
- Which runs happened
- Whether the workspace was delivered

The reason is that those facts are the records themselves, read where they are.
There is no second copy that could disagree.

<a id="concept.workspace-lock"></a>

The **[workspace lock](../glossary.json#concept.workspace-lock)** keeps a workspace doing one thing
at a time. A run of the workspace holds it from before its admission until after its result is
written. This ensures that two runs never audit each other's writes as their own.
Whoever prepared the workspace takes the lock too, as Coordination does to merge or close a task.
This ensures that no run changes the worktree while it is merged or removed.
When a taker finds the lock held, the taker is refused naming the holder, or waits for it, as its
own Spec says. The lock is a file under `locks/workspaces/` of the binding's `.concorde`.
It is apart from every record and outside the workspace. Thus, a run that only reads the workspace
leaves the workspace untouched. The holder is read from the holder line
[Tracing keeps in every lock file](tracing/contracts.md#locks).
The holder is never assumed to be a run.

### Marks and locks of the primary branch

<a id="concept.delivery-commit"></a>

A **[delivery commit](../glossary.json#concept.delivery-commit)** is the one mark of a delivery.
It is a commit with these properties:

- It is on the workspace's branch, since its base commit.
- Its subject is exactly `concorde: deliver <workspace>`.
- Its body is the workspace's goal.

It is recognized by its subject alone, so no part keeps a list of deliveries.
Only when it has exactly one parent does it verify. Thus, a merge commit given the subject never
marks the workspace delivered. A reader judges a workspace delivered by its latest delivery commit verifying, as Coordination's Tasks does.
The Kernel defines the mark and how it is recognized and verified.
The Kernel never defines these delivering command rules:

- Who may make a delivery commit
- What the delivering command must check first
- Which changes the delivery commit holds

In Concorde, Method's `delivery` makes the delivery commit after it validates the whole workspace.
Where the method part is not installed, Coordination's `task deliver` makes it after the checks it
is given pass.
Whoever reads deliveries relies on this convention alone, not on the part that made the commit
([exact rule](contracts.md#delivery-commit)). Coordination deriving that a task is delivered is
one such reader.

<a id="concept.merge-lock"></a>

The **[merge lock](../glossary.json#concept.merge-lock)** of the primary worktree keeps Concorde's
changes to the primary branch from interleaving in its one checkout. Each of these changes is a
commit of its own:

- A task's merge
- A task's open
- A task's close
- Every write of an [Issue](../glossary.json#concept.issue)

The lock is a `flock` held by the process doing the change. Thus, no session has to release it or
announce that it is done. The reason is that, when the process ends, the operating system releases the lock,
even when the process is killed. As soon as the lock is free, a waiting process wakes.
When a process gives up waiting, it is refused with `merge_busy`. The refusal names these holder
details:

- The holder's command
- The holder's task
- The holder's process
- The holder's start time
- The holder's Claude Code session

While it holds the lock, the holder writes these details into the lock file.
A process may also be handed the lock by the process that started it.
When handed the lock, the process holds it from its start without waiting, exactly as long as it
runs ([Handing a lock on](tracing/contracts.md#handing-a-lock-on)). The lock keeps the name of its
first taker, the task merge. The reason is that every other taker takes it so as not to land a
commit between a merge commit and its checks.

<a id="concept.unfinished-merge-marker"></a>

The lock alone cannot keep that promise across a crash. The operating system releases the lock when
its holder ends, even in the middle of a merge. The **[unfinished-merge
marker](../glossary.json#concept.unfinished-merge-marker)** keeps what the lock forgets. It is the
file `.concorde/unfinished-merge.json` of the primary worktree, which Git ignores. A part that
merges into the primary branch in several steps writes the marker while it holds the merge lock,
before it changes anything. The part removes the marker once the merge is decided, kept or undone.
A crash between leaves the marker behind. The marker names:

- The part that wrote it, the only part that replaces or removes it.
- The command that merges, its process and its start.
- The branch, the commit before the merge, the commit merged in and the merge commit once it exists.
- The commands that finish the merge.

Every other part that commits on the primary branch reads the marker while it holds the merge lock.
While the marker is present, that part refuses and commits nothing. The part also refuses when the
marker cannot be read, since such a marker may describe a merge. The reader holds the lock, so the
writer has ended. The writer may still run only when it handed the lock on, and it removes the
marker before it does.

In Concorde, Tasks writes the marker for a task merge. The Issue store and project review's record
commit read it. The marker is Kernel state, not a task record. Thus, an Operation reads it without
reading any part's records ([req.concorde.halves-apart](../requirements.md#req.concorde.halves-apart)).

## Overview

The Kernel sits below every part that cooperates and above none. Each arrow says which agreement a
part relies on. No part reaches another through the Kernel. From both sides, parts reach only the
same convention through the Kernel.

```d2 illustrative
direction: up
kernel: Kernel {
  data: "Typed values,\nfile transactions"
  workspace: "Workspace binding,\nworkspace lock"
  primary: "Delivery commit, merge lock,\nunfinished-merge marker"
  tracing: "Tracing: trace nodes,\nlocks, error chain"
}
coordination: Coordination
execution: Execution
workflow: Workflows
method: Method
harness: Worker harness
issues: Issues
coordination -> kernel.workspace: "writes the binding,\ntakes the lock to merge or close"
coordination -> kernel.primary: "reads delivery commits, takes the\nmerge lock, writes the marker"
execution -> kernel.workspace: "reads the binding,\nholds the lock for a run"
workflow -> kernel.workspace: reads the binding
method -> kernel.workspace: reads the binding
method -> kernel.primary: makes delivery commits
issues -> kernel.primary: "takes the merge lock,\nreads the marker"
method -> kernel.primary: "reads the marker for\nthe review record"
issues -> kernel.data: records and writes
harness -> kernel.tracing: records worker runs
coordination -> kernel.tracing: "records task nodes,\nhands on and waits for locks"
execution -> kernel.tracing: "records runs,\ntakes run locks"
workflow -> kernel.tracing: records the workflow node
```

## How it is built

### Why a kernel at all

When two parts must agree on one of these, one of them could own the agreement:

- A file.
- A commit.
- A lock.

The other could import it.
Then the importer could not be installed without the owner. Coordination writes the binding
Execution reads. Each must work without the other because a project may use either of these arrangements:

- A project may run Execution in workspaces it prepares itself.
- A project may manage tasks without ever running Concorde's runs.

Putting the agreement in a part both depend on keeps both installable apart, since that part has no
behaviour of its own to drag in. The same reasoning places the merge lock here rather than in
Tasks, since Issues takes it without needing tasks. It places the delivery commit here rather than
in Method's Delivery, since Coordination recognizes deliveries without needing Method.

### What stays out

The Kernel holds only agreements more than one part needs. Since only parts that depend on
Execution read them, these stay Execution's:

- A run's result.
- Its [run store](../glossary.json#concept.run-store).
- Its [run lock](../glossary.json#concept.run-lock).

The [task record](../glossary.json#concept.task-record) stays Coordination's. The grant stays the
Spec tooling's. The worker harness receives the grant as data in the worker harness's own input
format. A convention one part alone uses belongs to that part, however general it looks. The Spec
tooling depends on no part, not even the Kernel. To keep that independence, the Spec tooling keeps
its own copy of these:

- Typed values.
- File transactions.
- Schema checking.
- Digests.

It accepts the duplication so that the Specs can be checked and published with nothing else
installed. The two copies agree on the formats in [the contracts](contracts.md), not on code.

### Installed through Distribution

<a id="uses-distribution"></a>

**Distribution** installs the kernel part as it installs every part, from its
[part registration](../glossary.json#concept.part-registration). The Kernel declares these entries
there:

- Its guidance.
- Its child Tracing's `trace` command.
- The `.concorde/locks/` entry Git ignores.

The Kernel declares the entries as the plain data the
[registration contract](../distribution/contracts.md#contract.distribution.part-registration)
defines. The Kernel meets the host promises that contract makes of each entry, such as a command
printing its own output. The Kernel relies on Distribution reading the registration without
importing the Kernel's code beyond those entries. The Kernel relies on nothing else of Distribution.
It imports nothing of Distribution. Thus, the dependency stays a format the Kernel meets.

### The children

<a id="contains-tracing"></a>

**Tracing** gives every level the place and shape of its records:

- The uniform [trace node](../glossary.json#concept.trace-node).
- The nesting by which a parent places its child.
- The trace roots the parts register.
- The locks under `.concorde/locks/` with their holder lines.
- How a lock is handed on and waited for.
- Retention.
- The `concorde trace` command that reads them.
- The [error chain](../glossary.json#concept.error-chain) through which a failure travels up.

The Kernel's own locks are the workspace lock and the merge lock. They are files of that place.
The Kernel's own locks are taken through Tracing's library. The unfinished-merge marker is no lock.
It lies outside `locks/`, which holds every lock and nothing else.

### Code

<a id="realization.kernel.library"></a>

The **Kernel library** is the package `src/concorde/kernel/`, besides Tracing's `tracing/` and the
error chain code's `errors.py`. Its files hold these:

- `refusal.py` holds the Kernel error every operation refuses with.
- `schema.py` holds these:
  - Typed values with their registration.
  - The registered dialect.
  - The checking of contract schemas, digests and project paths.
- `files.py` holds file transactions.
- `binding.py` holds the workspace binding's reader and writer.
- `delivery.py` holds the delivery commit's message and listing.
- `locking.py` holds the workspace lock and the merge lock, taken through Tracing's lock library.
- `marker.py` holds the unfinished-merge marker's reader, writer and account.

Except for the spec part and Distribution, every part imports the Kernel library for these formats
instead of keeping its own. The Spec tooling's copy lives in Spec core.

<a id="realization.kernel.tests"></a>

The **Kernel tests** exercise the library on the scenarios of the Kernel's
[scenarios](scenarios.md):

- Bindings read and refused.
- Delivery messages made.
- Deliveries listed and verified.
- Types registered.
- Typed values and contract records checked.
- Transactions refused.
- Transactions restored.
- Transactions unrestored.
- Locks refused.
- Locks retired.
- Locks taken.
- Markers read, written, refused and removed.

<a id="realization.kernel.guidance"></a>

The **Kernel guidance** is the part's sections of the [main-session
guidance](../glossary.json#concept.main-session-guidance). The sections are kept in
`prompts/guidance/kernel/`. They are registered under `guidance` in the part's registration.
Wherever the part is installed,
[Distribution](../distribution/module.md#guidance-composition) composes the sections after
Coordination's working method. The sections are the project skill's "Traces and error chains":
`concorde
trace show` and how to read an error chain. Where a part a section mentions is not installed, that
section says what happens.
