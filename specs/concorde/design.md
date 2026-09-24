# Framework design

This topic explains the reasons behind the Framework's significant choices, which the
[Framework entry](module.md#design) states briefly, and follows one task through the Modules. It
is written for a reader who wants to understand why Concorde is shaped as it is; a reader who only
needs to use a Module can stop at that Module's entry.

## The Spec is the shared truth

Concorde is built around one idea: the Spec, not the code, is the shared source of truth between
the developer and the agents. Specs are written under the Spec Protocol, so both humans and tools
can read them. Every other choice follows from making that safe and practical: what a worker may
read and write is computed from the Specs, a worker's answer is checked by the host rather than
trusted, and a missing promise stops work instead of being inferred from code.

## Main agent, task sessions and workers

The main agent is the developer's Claude Code or pi session. It has the global view and the developer's
trust, so Concorde does not restrict it. Workers are the opposite: each has one bounded task, no
human to ask, and a boundary derived from the Specs. Keeping the two apart is what lets a large
change be split into small, checkable steps without the developer supervising each one.

Between them sits an optional **task session**, a per-task session the main agent starts only
when it splits work into several tasks. Earlier versions deferred this tier: with Operations run
from the main agent, the main agent already had everything such a session adds, and one fewer
layer of messaging meant one fewer place for an error to be lost. Two things changed that. A
session can be inside only one task worktree at a time, and the task's Concorde commands must run
with that worktree's own copy, so parallel tasks need parallel sessions. And the error that
motivated the deferral is contained structurally: a task session escalates through
`concorde task escalate --by task-session`, which records its link with the failed runs' chains
unchanged as causes, and the main agent adds its own link on top, so no level summarizes another.
A task session's writes are confined to its task by generated settings, while the main agent
stays unrestricted and alone merges.

## Working inside the task

Whoever carries out a task, the main agent or a task session, works inside the task worktree and
runs every Concorde command there with the worktree's own copy. The primary worktree's copy is
the code of the primary branch: it cannot know the Specs, Protocol or checks a task changes, and
in Concorde's own checkout it would judge a change to Concorde with the code the change replaces.
Running the branch's copy is self-validation, so after merging the main agent runs `validate` once
more on the primary branch. Task worktrees live under `.claude/worktrees/` of the primary worktree,
where Claude Code can move a session into an existing worktree and back.

## Tasks are branches

A task is a branch with its own worktree. Parallel work happens only between worktrees, so two
tasks never write the same checkout. Each task keeps a record and a decision log in the primary
worktree, so the main agent can resume, report and merge without relying on its own memory.

## Operations are host steps plus workers

An Operation is a small, fixed sequence of deterministic host steps around zero or more workers.
The host computes the grant, prepares the worker, audits the worker's writes, runs the checks
itself and records the run. The control flow is plain Python with a step table in the owning
Module's Spec; neither LangGraph nor an agent-side workflow engine is used, because the sequences
are short and must be readable and testable as code.

When a check fails, the host resumes the same worker with the failure, up to a fixed number of
rounds. These automatic rounds repair code only. A Spec gap, a boundary the worker needs to cross,
or a failed deterministic Spec check stops the Operation and returns its error chain, because
deciding what the Spec should promise belongs to the developer and the main agent.

## Errors travel as a chain

Every level of Concorde handles some errors and must pass the others up: Workers resumes a worker
for a failing check but not for a Spec gap, an Operation reruns nothing, the main agent decides
ordinary questions but not the project's direction. An error that is passed up as a bare code or
a one-line summary loses exactly what the next level needs to decide, and an error that each level
re-describes in its own words drifts from what actually happened. So every level that cannot
handle an error adds one link and keeps the rest: its own detailed account, the specific reason it
cannot handle the error, the options it sees, and the errors it received as causes, unchanged. The
reasons come from a small fixed set, such as a missing permission, a decision reserved to a higher
level or used-up rounds, so a reader can see at a glance which level could act with more authority.

The chain is structured data with one [contract](contracts.md#contract.concorde.error), not a
convention of prose. Workers fill in their part of it in their result, the host checks it against
its schema, and the main agent adds its own link with a command rather than paraphrasing, so the
developer receives the whole path from the failing check or the worker's missing promise up to the
question they are asked.

## Grants come from the task's own Specs

A grant is computed from the Specs in the task's worktree, never from the primary's. A task that
changes a Spec therefore gives the next step of the same task a boundary that matches the changed
Spec. The grant is frozen when a worker starts, so a concurrent Spec change cannot widen a running
worker. A worker never requests its own grant.

## Enforcement and its limits

A worker is a separate `claude -p` process with its own settings, its own configuration directory
and the run directory as its working directory. Three layers derived from one grant confine it:
deny rules keep the file tools away from everything outside the grant, a small write hook makes the
writable paths the only ones Edit and Write may touch, and the Bash sandbox confines shell
commands, including their reads, writes and network. After the worker stops, the host compares the
worktree's changes with the grant, so any write that slipped through is caught.

These layers were chosen after testing what Claude Code actually enforces: its sandbox confines
only Bash, its permission rules cannot express "only these files are writable", and a hook alone
covers only the tools it governs. They guard against a worker drifting out of its scope or making a
mistake. They do not stop a malicious actor: the Claude process and the hook are not themselves
sandboxed. Wrapping the whole worker in an outer OS sandbox is future work.

## One task through the Modules

The sequence below is an illustration, not a declaration; each arrow in it is declared by the
calling Module's own `uses`.

```d2 illustrative
shape: sequence_diagram
m: Main agent
t: Tasks
o: Operation host
s: Spec core
w: Worker
c: Check execution
m -> t: open a task (branch and worktree)
m -> o: concorde run implement --task
o -> s: grant for the task type and Modules
o -> w: launch with settings, brief and grant
w -> o: worker result {style.stroke-dash: 3}
o -> o: audit writes against the grant
o -> c: run configured checks
o -> m: Operation result with evidence {style.stroke-dash: 3}
m -> o: concorde run validate, then delivery
m -> t: merge the task branch
```
