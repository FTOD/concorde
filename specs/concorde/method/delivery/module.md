# Delivery

## Purpose

Delivery turns a workspace's new work into a delivered commit. It provides the execution command
`concorde delivery`: when the bound workspace has new work — commits on its branch since the base
commit, or uncommitted changes — it validates the whole workspace itself, exactly as Validation
decides a [readiness](../../glossary.json#concept.readiness), and when that is ready it commits
the remaining changes on the bound branch. The
[delivery commit](../../glossary.json#concept.delivery-commit) is the only record of the
delivery. Whoever merges the workspace relies on it, in Concorde the
[main agent](../../glossary.json#concept.main-agent), so that what it merges is exactly what was
validated. Workers never touch Git; whoever works in the workspace, in Concorde the
[task session](../../glossary.json#concept.task-session) of its task, may commit verified steps
on the branch, and only Delivery makes the commit that marks the work delivered. Delivery never merges, pushes,
amends or rebases a commit, repairs a finding, writes a task record, or delivers or reports as
delivered anything it did not validate in the same run; the one commit it ever takes off its branch
is a delivery commit it created in the same run and then rejected.

## Core concepts

Delivery rests on one idea, the delivery commit: the one mark of a delivery, made only on top of
what the same run validated. It builds on Validation's
[readiness](../../glossary.json#concept.readiness) and on the Kernel's convention for the
[delivery commit](../../glossary.json#concept.delivery-commit), which says how any part recognizes
and verifies one ([Kernel](../../kernel/contracts.md#delivery-commit)); Delivery is the one producer
of delivery commits that validates the whole workspace first.

### The delivery commits it makes

A delivery commit Delivery makes has subject `concorde: deliver <workspace>`, which marks it as a
delivery, and the goal as body, as the Kernel's convention requires. Its parent is the branch head
Delivery validated; it contains the cleared markers and every uncommitted change
except what Git ignores and the untracked paths Validation's input measurement leaves out, such as
a sandbox's `/dev/null` mounts and placeholder files — only any cleared markers, and so possibly nothing, when every step was already committed.
A workspace may be delivered several times — another `implement` after a code review, say — each a
new commit on top, never amended. The delivery commits are the only record of the deliveries:
Delivery writes no [task record](../../glossary.json#concept.task-record) and keeps no list of
its own, and reads its earlier deliveries back from the branch by their subject
([exact rule](contracts.md#delivery-commit)). Running `delivery` again when the branch head already
is a delivery commit of the workspace and nothing waits reports that commit, `ok` with `recovered`
true, and commits nothing — once it has verified that the commit has exactly one parent, as every
commit Delivery creates has, and has validated the workspace again exactly as for a new delivery,
since the subject alone proves nothing about what the commit holds. A head with the subject that
has another number of parents, such as a merge commit, is `commit_unverified`, naming the mismatch;
one whose workspace is not ready, or whose code change leaves a scenario unverified, is `blocked`
like any delivery. The delivery run's own
[trace node](../../glossary.json#concept.trace-node) references the delivery commit, so the trace
leads to what was committed: as `commit` when the run created it, and as `found_commit` when it
found its work already delivered and reported the existing commit, which an earlier run created.
What the readiness examined and which runs led to it stay in the run's trace node and those of the
workspace's other runs, local records that [Tracing](../../kernel/tracing/module.md)'s retention may
remove; what the task decided along the way is kept in Git by the task level, in Concorde as the
task's [decision log](../../glossary.json#concept.decision-log) Tasks commits when the task ends.

## Overview

### Delivering a workspace

A run of `delivery` goes through eleven steps. Every step before 8 leaves the workspace as it was,
so a blocked delivery, or one that reports a delivery commit it found, changes nothing; the index
step 8 recorded is given back when step 9 fails, and a commit that does not verify in step 10 is
taken off the branch again, leaving the index and the worktree as the commit left them:

```d2 illustrative
direction: down
branch: "1. Head on the bound branch?"
found: "2. Head already a delivery commit\nof the workspace, nothing waiting?"
work: "3. A commit since the base\nor an uncommitted change?"
readiness: "4. Decide the whole workspace's\nreadiness with Validation's steps"
ready: "5. Ready?"
tests: "6. Changed code: every added or\nchanged scenario has a verifying test?\n(skipped with --adoption)"
reported: "7. Found in step 2?"
index: "8. Record the index"
commit: "9. Stage every change, record\nthe staged tree, commit"
verify: "10. Verify the commit"
output: "11. Return the commit"
ok: "ok"
blocked: "blocked\nthe workspace unchanged"
failed: "failed"
branch -> found: yes
found -> work: "no, or yes with one parent:\nvalidate it again"
work -> readiness: yes
readiness -> ready
ready -> tests: yes
tests -> reported: yes
reported -> index: no
index -> commit -> verify -> output -> ok
reported -> ok: "yes: recovered"
found -> failed: "yes, but not one parent:\ncommit_unverified" {style.stroke-dash: 3}
branch -> failed: "no: wrong_branch" {style.stroke-dash: 3}
work -> blocked: "no: nothing_to_deliver" {style.stroke-dash: 3}
readiness -> failed: "measurement, checks\nor inputs fail" {style.stroke-dash: 3}
ready -> blocked: "no: not_ready" {style.stroke-dash: 3}
tests -> blocked: "no: unverified_scenarios" {style.stroke-dash: 3}
index -> failed: "index_unrecorded" {style.stroke-dash: 3}
commit -> failed: "Git refuses: the index given back" {style.stroke-dash: 3}
verify -> failed: "mismatch: commit_unverified,\nthe commit taken off the branch" {style.stroke-dash: 3}
```

[The steps](#the-steps) gives each step's actor and stopping rule, and
[The commit is the record](#the-commit-is-the-record) why the commit is all Delivery keeps.

## Running delivery

The task level runs the command in the task worktree when the workspace's work is complete. Each
verified step may already be committed on the branch, so a clean worktree is the normal case:

```text
concorde delivery [--adoption] [--detach]
```

It is an [execution command](../../glossary.json#concept.execution-command): the
[Execution runner](../../execution/runner.md) runs it in the workspace whose
[binding](../../glossary.json#concept.workspace-binding) lies in the worktree it starts in, under
the [workspace lock](../../glossary.json#concept.workspace-lock), and records it in the
[run store](../../glossary.json#concept.run-store). In a worktree without a binding it is refused
with `binding_required` and commits nothing. It requires new work since the base commit, then
decides the [readiness](../../glossary.json#concept.readiness) of the whole workspace with
Validation's own steps — the structural validation, the unbound-path check and the
[configured checks](../../glossary.json#concept.configured-check) a `task-validation` run
performs, over every commit since the base and every uncommitted change — and requires it ready. An
earlier `task-validation` run is only a preview; Delivery never trusts it or the checks of single
steps. When the workspace **changed code** — a changed path outside `specs/` and `.concorde/` that a
Module's realization binds, tests included — Delivery also requires a test whose
[verification declaration](../../glossary.json#concept.verification-declaration) names every
scenario the workspace added or changed. Ready, it commits every uncommitted change on the bound
branch as the [delivery commit](../../glossary.json#concept.delivery-commit). The
[run result](../../glossary.json#concept.run-result), of kind `command` with no worker, carries
the commit ([contract](contracts.md#contract.delivery.output)). The task level then has the branch
merged, in Concorde by the main agent, and ends the task.

`--adoption` marks a delivery that describes code which already existed, as the
[brownfield workflow](../../glossary.json#concept.brownfield-workflow) delivers: such a delivery
changes no behaviour and adds no test, so the scenarios it writes are exempt from the rule that
changed code ships only with a test for each scenario it added or changed. Delivery does not check
this claim: the flag is the caller's declaration, recorded as `scenario-tests` evidence `exempt`.
Every other rule applies unchanged.

### The result

| Status | Code | Reason | Detail |
| --- | --- | --- | --- |
| `blocked` | `nothing_to_deliver` | `decision` | no commit since the base commit and no uncommitted change (`git` evidence) |
| `blocked` | `not_ready` | `decision` | the whole workspace is not ready; Validation's `not_deliverable` link is the cause, with one cause per finding |
| `blocked` | `unverified_scenarios` | `decision` | the workspace changed code while a scenario it added or changed has no verifying test; names each with its document |
| `failed` | — | — | `wrong_branch`, Validation's `measurement_failed`, `checks_unavailable` or `inputs_changed`, an index Git cannot record (`index_unrecorded`), Git refusing (`stage_failed`, `commit_failed`) or a commit that does not verify, the one it made, which it takes off the branch again, one Git did not name, or the delivery commit it found at the head (`commit_unverified`) |

The error is the run's own link of level `command`, with the actor `Command delivery <run-id>
(workspace <workspace>)`. Every `blocked` code carries a host evidence `ref` of the same name and
an explanation of its own reason; a blocked delivery writes nothing in the workspace, and the fix is
to do more work or end the task, or to repair the findings and run `delivery` again. A `failed` Git
refusal — a hook, a missing author identity — carries the hook's output as `git` evidence and a
`component` cause with the Git command's exit status and output; the index is left as validated,
and any worktree file a failing hook changed is kept and named. An index with unmerged paths, from a merge not finished, is `index_unrecorded` with the
reason `decision` and the paths as `git` evidence, since resolving or aborting the merge is the
task level's decision; any other Git refusal to record the index is `index_unrecorded` with the
reason `environment`. Either way its cause is the `git write-tree`, `git ls-tree` or
`git ls-files` link with Git's output, and nothing has changed yet.

## How it is built

Delivery makes the delivery commit, workers do not: a delivery makes a proposal part of the history
that is merged and must match what was checked, which only deterministic code that checks it can
prove.
So Delivery decides the readiness itself, over the whole workspace since its base, immediately
before committing, rather than trusting an earlier `task-validation` run or the checks each step
passed — steps are verified one at a time, and only the whole can show that they still fit
together. Validation's last step remeasures the inputs, so a change while the checks ran fails the
run; the commit follows at once, so it is exactly what was validated, or nothing. The commit
carries no evidence file of its own: its subject is the whole mark of a delivery. Run identities
and digests committed with it could never be checked later, since the results they name are local
and removed by retention, and nothing ever read them; the readiness's record stays in the delivery
run's trace node for as long as it is kept. Delivery changes no [Spec](../../glossary.json#concept.spec)
itself: every realization entry already exists when the readiness is decided, since the task level
binds a new file only once it has created it, so the commit holds exactly what was validated.

Delivery is an execution command rather than an
[Operation](../../glossary.json#concept.operation) because it involves no model; it is a run
nonetheless, so that a workflow can take it as a step, and its evidence and
[error chain](../../glossary.json#concept.error-chain) reach its caller like any run's.

### The commit is the record

A delivery is recorded once, in the commit that makes it, and nowhere else. A second record, such
as a list of deliveries in a task record, could disagree with the branch: a run that ends between
its commit and its bookkeeping leaves a delivered branch that the record says is not delivered,
which then needs a repair step. With the commit as the only record there is nothing to repair: the
next `delivery` sees the head is a delivery commit, validates the workspace again and reports it,
and whoever needs to know whether a workspace is delivered reads the branch. In Concorde the task
level does exactly that: it counts a task as delivered when its branch head is a delivery commit of
its workspace and its worktree is clean, and merges only such a head. Since the subject alone marks
a delivery, Delivery keeps a rejected commit from becoming such a record: it takes a commit it
rejected off the branch in the same run, and validates a delivery commit it finds at the head again
before it reports it. The commit as the record also keeps Delivery ignorant of tasks, as every part below the task
level is: the commit names the workspace, which the binding names, and nothing else.

### The steps

| # | Step | Actor | Stops when |
| --- | --- | --- | --- |
| 1 | Require the workspace's head to be on the branch its binding names | host | wrong or detached branch (`failed`) |
| 2 | Note the head when it already is a delivery commit of the workspace and nothing waits, after verifying that it has exactly one parent | host, read-only Git | the head does not verify (`failed`, `commit_unverified`) |
| 3 | Require a commit since the base commit or an uncommitted change | host, read-only Git | neither (`blocked`, `nothing_to_deliver`) |
| 4 | Decide the whole workspace's readiness with Validation's steps | Validation | measurement, checks or inputs fail (`failed`) |
| 5 | Require the readiness ready | host | not ready (`blocked`, `not_ready`) |
| 6 | When the workspace changed code, require a test declaring that it verifies every scenario it added or changed since its base commit, unless `--adoption` | host, Spec core, read-only Git | an unverified scenario (`blocked`, `unverified_scenarios`, naming each with its document) |
| 7 | Report the delivery commit step 2 noted, numbered among the delivery commits on the branch | host | it noted one (`ok`, `recovered`) |
| 8 | Record the index with Git | host, Git | the index cannot be recorded (`failed`, `index_unrecorded`) |
| 9 | Stage every change; record the staged tree; commit, taking the commit Git names | host, Git | Git refuses (`failed`; the index restored, a hook's worktree edits kept and named) |
| 10 | Verify the commit is head, its tree the staged tree, its subject the delivery subject, parent validated, worktree clean | host, read-only Git | mismatch (`failed`, `commit_unverified`; the commit taken off the branch) |
| 11 | Return the commit as the output, numbered after the delivery commits on the branch | host | — |

Every step before 8 leaves the workspace as it was — Validation writes its check nodes and the
readiness only to the run's [trace node](../../glossary.json#concept.trace-node) — so a blocked
delivery, and one that reports a delivery commit it found, changes nothing in the workspace. A
delivery commit found at the head is validated exactly as new work would be, by steps 3 to 6: its
subject and its one parent show only that Delivery may have created it, not that what it holds is
ready, so a commit a rejected run left behind, or one another hand gave the subject, is reported
only once its workspace is ready again. When step 9 fails (`measurement_failed` while staging,
`stage_failed`, `commit_failed`), the index is given back as step 8 recorded it. Delivery never
undoes an edit of the worktree: a failing commit hook, such as a formatter that rewrites files and
then rejects the commit, may leave edits the developer wants. So Delivery measures the worktree
again with Validation's input measurement and names, in the run's summary and detail, every path
whose mode or content is not what the readiness examined, which it keeps; when there is none, the
workspace is again what the readiness describes. The next delivery validates whatever the worktree
then holds. Step 8 records the index with Git's own means rather than a copy Delivery
would keep: `git write-tree` for its entries, which `git read-tree` restores; the paths `git
ls-files` lists that the tree lacks, which are intent-to-add entries a tree cannot hold and
`git add -N` marks again; and the skip-worktree and assume-unchanged flags `git ls-files -v`
shows, which `git update-index` sets again. So changes staged before the delivery, including a
staged version the worktree has changed since, stay staged. Restoring the intent-to-add entries
and each kind of flag is attempted even when another of them fails; when Git refuses to read the
recorded tree back into the index, none of them is attempted, since they apply only to an index
that was read back, and the run's summary and detail say that they were not restored. Each part
that fails — the index, the intent-to-add entries or a kind of flag — is named in the run's summary
and detail, which then say the index is not as the readiness examined it, and is a `component`
cause of its error with Git's own account; when the worktree cannot be measured again, they say so,
with the measurement's account as a `component` cause. A
`commit_unverified` failure of step 10 comes after the commit exists, and a commit Delivery rejected
must not stay where it would be read as a delivery: Delivery moves the bound branch back to the
validated head with `git update-ref`, only while the validated head is the commit's only parent and
the branch still points at the commit, and leaves the index and the worktree as the commit left
them, so that what a hook changed stays there to be inspected. Its error says that the commit was
taken off the branch and names it, and the run's trace node still references it as `commit`, since
the run created it. When the head is not such a commit, such as after a hook committed again on
top, or Git refuses the move, Delivery moves nothing, so that it never takes off a commit it did not
create, and the error says that the commit stays and why — the branch no longer points at it,
naming the commit it points at, or Git refused to move a branch that still points at it — with
`git update-ref`'s account as a `component` cause; repairing the branch is then the task level's
decision. See the [requirements](requirements.md) and
[scenarios](scenarios.md).

Delivery proves what it committed rather than assuming it. The repository's commit hooks run
normally, and a pre-commit hook may change a file and stage it again, so the commit Git creates can
hold content the readiness never examined while the worktree is still clean. Step 9 therefore
records the tree of the staged index with `git write-tree` just before `git commit`, and step 10
compares it with the new commit's tree, naming every path that differs. A commit message hook may
likewise rewrite the message, such as by prefixing a ticket to the subject, which would leave a
commit without the subject that marks a delivery; step 10 also compares the commit's subject with
the delivery subject, naming the subject the commit carries, while a hook that only adds to the
body, such as a `Change-Id` trailer, is accepted. The commit step 10 verifies, and the
run's trace node references, is the one `git commit` names on its standard output as the one it
created: Git prints it once its post-commit hook has run and gives every hook's standard output to
its standard error, so a post-commit hook that commits again on top cannot pass its commit off as
the delivery commit, as the branch head would. The branch's reflog would not do, since a repository
may switch it off, nor the first commit on top of the validated head, which a hook amending the
commit replaces. When Git names no commit, the run fails `commit_unverified` and moves nothing. A delivery commit is
recognised in step 2 by its subject alone, which any commit can carry; Delivery reports the head as
delivered only when it also has exactly one parent, as every commit it creates has, so that a merge
commit reworded with the subject is not taken for a delivery, and only once steps 3 to 6 found its
workspace ready. A head that fails the parent check is `commit_unverified` with the reason
`decision`, since what to do with a commit that does not hold what it claims is the task level's
decision. A cherry-picked or reworded commit with one parent is not told from a delivery by its
form: the subject is a mark the task level relies on, not a proof, which is why Delivery validates
what it holds before it reports it.

### The command

<a id="realization.delivery.command"></a>

The **Delivery command** realization holds the steps, the commit message and the reader of earlier
delivery commits, and their tests.

## What Delivery relies on

- <a id="uses-execution"></a>**Execution**'s runner runs the command: it reads the workspace
  binding, which gives the steps the workspace's name, goal, Modules, bound branch and base commit,
  holds the workspace lock for the whole run, so no other run changes the workspace between the
  readiness and the commit, and records the run.
- <a id="uses-commands"></a>**Commands**, Execution's execution-command framework, is what
  `delivery` plugs into: Method registers its definition there, which is how the runner finds this
  [Module](../../glossary.json#concept.module)'s definition by the command's name.
- <a id="uses-kernel"></a>The **Kernel** gives Delivery the format of the
  [workspace binding](../../glossary.json#concept.workspace-binding) it reads through the run
  context ([contract](../../kernel/contracts.md#contract.kernel.workspace-binding)), the
  [workspace lock](../../glossary.json#concept.workspace-lock) the runner holds for it, and the
  [delivery commit](../../glossary.json#concept.delivery-commit) convention it makes its commits
  by, so that Coordination, which depends on the Kernel and not on Method, recognizes them.
- <a id="uses-validation"></a>**Validation** provides the readiness steps. Delivery runs those
  steps as its own, so its readiness is decided exactly as a `task-validation` run's, and relies on
  their final remeasurement to prove that the measured inputs at the end are those the readiness
  records; it never
  changes a finding, treating a readiness that is not ready as blocking.
- <a id="uses-spec"></a>**Spec core** answers step 6 on the workspace's Specs as they read now:
  which changed paths a Module's realization binds and, through its structural validation's
  coverage findings, which scenarios no test declares that it verifies. Delivery reads the base
  commit's text of each changed reading document itself, with read-only Git, to find the scenarios
  the workspace added or changed; it relies on Spec core loading the Specs completely or refusing,
  and never changes them in this step.
