# Kernel

## Purpose

The Kernel is the kernel [part](../glossary.json#concept.part): the few contracts Concorde's parts
cooperate through without importing each other. Coordination writes a
[workspace binding](../glossary.json#concept.workspace-binding) that Execution, Workflows and Method
read; Method makes a [delivery commit](../glossary.json#concept.delivery-commit) that Coordination
recognizes; Tasks and Issues take the same [merge lock](../glossary.json#concept.merge-lock); every
level records the same [trace node](../glossary.json#concept.trace-node) and reports with the same
[error chain](../glossary.json#concept.error-chain). Each of these agreements belongs to neither
side, so it lives here, and every part that cooperates through it depends on the Kernel instead of
on the part at the other end.

The Kernel holds formats, conventions and the small library that reads and writes them; it decides
nothing about the work. It knows no task, no run, no [Operation](../glossary.json#concept.operation) and no [Spec](../glossary.json#concept.spec): a contract here may name
an example of who uses it, never rely on that user. It depends on no part, and every part but the
Spec tooling, which keeps its own copy of the data utilities it shares with the Kernel, and
Distribution, which reaches the parts only through their registrations, depends on it.

## Core concepts

The Kernel's terms fall into three groups: the data parts exchange, the workspace one part prepares
and others work in, and the marks and locks by which they take turns. Its child
[Tracing](tracing/module.md) explains the trace node, the [trace](../glossary.json#concept.trace)
and the error chain.

### Data parts exchange

<a id="concept.typed-value"></a><a id="concept.file-transaction"></a>

Every structured value parts exchange or record is a
**[typed value](../glossary.json#concept.typed-value)** `{type_id, schema_version, data}`, whose
`data` is checked against the schema its owner registered for that type and version: a [run result](../glossary.json#concept.run-result),
a trace node's content, an Issue record. The owner registers its own types when its code loads, and
a record of one part may embed a value of another part's type by name, so neither imports the other.
A **[file transaction](../glossary.json#concept.file-transaction)** writes a set of whole files,
each bound to the digest of the bytes it replaces, completely or, when a write or its final check
fails, not at all; a process killed in the middle can leave it partly applied, which is why every
writer that uses one also says how its records are recovered. The
[contracts](contracts.md#typed-values) give both formats exactly.

### The workspace

<a id="concept.workspace"></a><a id="concept.workspace-binding"></a>

A **[workspace](../glossary.json#concept.workspace)** is one worktree prepared for a bounded piece
of work. It exists once its **[workspace binding](../glossary.json#concept.workspace-binding)**
does: whoever prepares it writes `.concorde/workspace.json` at the worktree's root, as the
[binding contract](contracts.md#contract.kernel.workspace-binding) defines, naming the workspace,
the absolute root it lies in, its goal, the [Modules](../glossary.json#concept.module) it works on,
the branch and base commit it works from, the **workspace folder** where the work done in it is
traced and the `.concorde` directory whose `locks/` holds its locks. In Concorde,
[`concorde task open`](../coordination/tasks/module.md) writes it into each new task worktree,
naming the workspace after the task and placing the workspace folder inside the task's own folder,
so that a task's [trace](../glossary.json#concept.trace) holds every run of its workspace. The parts
that work in the workspace read the binding and never write it, and none of them learns that the
folder belongs to a task: another preparer may place it anywhere. A binding that breaks its
contract, or that names a root other than the worktree it lies in, is refused rather than trusted,
since a copied binding would bind the wrong workspace.

The binding names the workspace folder rather than letting a reader derive it, so that whoever
prepares the workspace decides where its traces belong. It records only what the work needs to
start: never what was done there, which runs happened or whether the workspace was delivered, since
those facts are the records themselves, read where they are, with no second copy that could
disagree.

<a id="concept.workspace-lock"></a>

The **[workspace lock](../glossary.json#concept.workspace-lock)** keeps a workspace doing one thing
at a time. A run of the workspace holds it from before its admission until after its result is
written, so that two runs never audit each other's writes as their own; whoever prepared the
workspace takes it too, as Coordination does to merge or close a task, so that no run changes the
worktree while it is merged or removed. A taker that finds it held is refused naming the holder, or
waits for it, as its own Spec says. The lock is a file under `locks/workspaces/` of the binding's
`.concorde`, apart from every record and outside the workspace, so a run that only reads the
workspace leaves it untouched; who holds it is read from the holder line
[Tracing keeps in every lock file](tracing/contracts.md#locks), never assumed to be a run.

### Marks and locks of the primary branch

<a id="concept.delivery-commit"></a>

A **[delivery commit](../glossary.json#concept.delivery-commit)** is the one mark of a delivery: a
commit on the workspace's branch, since its base commit, whose subject is exactly
`concorde: deliver <workspace>`, with the workspace's goal as body. It is recognized by its subject
alone, so no part keeps a list of deliveries, and it verifies only when it has exactly one parent,
so that a merge commit carrying the subject is never taken for one. Only a delivering command makes
it: Method's `delivery`, which validates the whole workspace first and commits only when it is
ready, or, where the method part is not installed, Coordination's `task deliver`, which runs the
checks it is given. Whoever reads deliveries, such as Coordination deriving that a task is
delivered, relies on this convention alone and not on the part that made the commit
([exact rule](contracts.md#delivery-commit)).

<a id="concept.merge-lock"></a>

The **[merge lock](../glossary.json#concept.merge-lock)** of the primary worktree keeps the changes
Concorde makes to the primary branch from interleaving in its one checkout: a task's merge, open and
close, and every write of an [Issue](../glossary.json#concept.issue), each a commit of its own. It
is a `flock` held by the process doing the change, so no session has to release it or announce that
it is done: the operating system releases it when the process ends, even when it is killed, and a
waiting process wakes as soon as it is free. A process that gives up waiting is refused with
`merge_busy`, naming the holder's command, task, process, start time and Claude Code session, which
the holder writes into the lock file while it holds it. A process may also be handed the lock by the
process that started it, and then holds it from its start without waiting, exactly as long as it
runs ([Handing a lock on](tracing/contracts.md#handing-a-lock-on)). It keeps the name of its first
taker, the task merge, because every other taker takes it so as not to land a commit between a
merge commit and its checks.

## Overview

The Kernel sits below every part that cooperates and above none. Each arrow says which agreement a
part relies on; no part reaches another through the Kernel, only the same convention from both
sides.

```d2 illustrative
direction: up
kernel: Kernel {
  data: "Typed values,\nfile transactions"
  workspace: "Workspace binding,\nworkspace lock"
  primary: "Delivery commit,\nmerge lock"
  tracing: "Tracing: trace nodes,\nlocks, error chain"
}
coordination: Coordination
execution: Execution
workflow: Workflows
method: Method
harness: Worker harness
issues: Issues
coordination -> kernel.workspace: "writes the binding,\ntakes the lock to merge or close"
coordination -> kernel.primary: "reads delivery commits,\ntakes the merge lock"
execution -> kernel.workspace: "reads the binding,\nholds the lock for a run"
workflow -> kernel.workspace: reads the binding
method -> kernel.primary: makes delivery commits
issues -> kernel.primary: takes the merge lock
issues -> kernel.data: records and writes
harness -> kernel.tracing: records worker runs
coordination -> kernel.tracing
execution -> kernel.tracing
workflow -> kernel.tracing
```

## How it is built

### Why a kernel at all

When two parts must agree on a file, a commit or a lock, one of them could own the agreement and
the other import it, but then the importer could not be installed without the owner. Coordination
writes the binding Execution reads, and each must work without the other: a project may run
Execution in workspaces it prepares itself, or manage tasks without ever running Concorde's runs.
Putting the agreement in a part both depend on, which has no behaviour of its own to drag in, keeps
both installable apart. The same reasoning places the merge lock here rather than in Tasks, since
Issues takes it without needing tasks, and the delivery commit here rather than in Method's
Delivery, since Coordination recognizes deliveries without needing Method.

### What stays out

The Kernel holds only agreements more than one part needs. A run's result, its [run store](../glossary.json#concept.run-store) and its
[run lock](../glossary.json#concept.run-lock) stay Execution's, since only parts that depend on Execution read them; the [task record](../glossary.json#concept.task-record) stays
Coordination's; the grant stays the Spec tooling's, handed to the worker harness as data in the
worker harness's own input format. A convention one part alone uses belongs to that part, however
general it looks. The Spec tooling depends on no part, not even the Kernel, so it keeps its own copy
of typed values, file transactions, schema checking and digests, accepting the duplication so that
the Specs can be checked and published with nothing else installed; the two copies agree on the
formats in [the contracts](contracts.md), not on code.

### The children

<a id="contains-tracing"></a>

**Tracing** gives every level the place and shape of its records: the uniform
[trace node](../glossary.json#concept.trace-node), the nesting by which a parent places its child,
the trace roots the parts register, the locks under `.concorde/locks/` with their holder lines, how
a lock is handed on and waited for, retention, the `concorde trace` command that reads them, and
the [error chain](../glossary.json#concept.error-chain) through which a failure travels up. The
Kernel's own locks, the workspace lock and the merge lock, are files of that place, taken through
its library.

### Code

The Kernel binds no code of its own yet: today its formats are implemented where they were first
needed, the workspace binding in Execution's runner, the delivery commit in Delivery and Tasks, the
merge lock in Tasks, typed values and file transactions in Spec core, and each of those Modules'
realizations binds that code. The code tasks that follow this Spec move them into the kernel's own
package, which Tracing's code joins, and bind it here.
