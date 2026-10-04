# Delivery

## Purpose

Delivery turns a workspace's new work into a delivered commit. It provides the execution command
`concorde delivery`. When the bound workspace has new work, Delivery validates the whole workspace
itself. It does so exactly as Validation decides a [readiness](../../glossary.json#concept.readiness).
New work means commits on its branch since the base commit, or uncommitted changes. When that
readiness is ready, Delivery commits the remaining changes on the bound branch. The
[delivery commit](../../glossary.json#concept.delivery-commit) is the only record of the delivery.
Whoever merges the workspace relies on it so that what it merges is exactly what was validated.
In Concorde, that actor is the [main agent](../../glossary.json#concept.main-agent). Workers never
touch Git. Whoever works in the workspace may commit verified steps on the branch. In Concorde,
that actor is the [task session](../../glossary.json#concept.task-session) of its task. Only Delivery
makes the commit that marks the work delivered. Delivery never does any of these things:

- Merges, pushes, amends or rebases a commit.
- Repairs a finding.
- Writes a task record.
- Delivers or reports as delivered anything it did not validate in the same run.

The one commit it ever takes off its branch is a delivery commit it created and rejected in the same
run.

## Core concepts

Delivery rests on one idea, the delivery commit. It is the one mark of a delivery, made only on top
of what the same run validated. It builds on Validation's
[readiness](../../glossary.json#concept.readiness) and on the Kernel's convention for the
[delivery commit](../../glossary.json#concept.delivery-commit). That convention says how any part
recognizes and verifies one ([Kernel](../../kernel/contracts.md#delivery-commit)). Delivery is the
one producer of delivery commits that validates the whole workspace first.

### The delivery commits it makes

A delivery commit Delivery makes has subject `concorde: deliver <workspace>`. That subject marks it
as a delivery. It has the goal as body, as the Kernel's convention requires. Its parent is the branch
head Delivery validated. It contains the cleared markers and every uncommitted change, with these
exceptions:

- What Git ignores.
- The untracked paths Validation's input measurement leaves out, such as a sandbox's `/dev/null`
  mounts and placeholder files.

When every step was already committed, the delivery commit contains only any cleared markers. It
may therefore contain nothing. A workspace may be delivered several times, with another `implement`
after a code review, say. Each delivery is a new commit on top, never amended. The delivery commits
are the only record of the deliveries. Delivery writes no
[task record](../../glossary.json#concept.task-record). It keeps no list of its own. It reads its
earlier deliveries back from the branch by their subject
([exact rule](contracts.md#delivery-commit)).

When the branch head already is a delivery commit of the workspace and nothing waits, running
`delivery` again reports that commit. It reports `ok` with `recovered` true. It commits nothing.
Before reporting it, Delivery verifies that the commit has exactly one parent. Every commit
Delivery creates has exactly one parent. Since the subject alone proves nothing about what the
commit holds, Delivery also validates the workspace again exactly as for a new delivery. When a head
with the subject has another number of parents, such as a merge commit, it is `commit_unverified`.
The error names the mismatch. A head whose workspace is not ready, or whose code change leaves a
scenario unverified, is `blocked` like any delivery.

The delivery run's own [trace node](../../glossary.json#concept.trace-node) references the delivery
commit. Thus, the trace leads to what was committed. The reference depends on what the run did:

- When the run created the commit, it references it as `commit`.
- When the run found its work already delivered, it references the existing commit as
  `found_commit`. The run reported that commit. An earlier run created that commit.

What the readiness examined and which runs led to it stay in local records: the run's trace node
and those of the workspace's other runs.
[Tracing](../../kernel/tracing/module.md)'s retention may remove those records. The task level
keeps what the task decided along the way in Git. In Concorde, Tasks commits the task's
[decision log](../../glossary.json#concept.decision-log) when the task ends.

## Overview

### Delivering a workspace

A run of `delivery` goes through eleven steps. Every step before 8 leaves the workspace as it was.
A blocked delivery, or one that reports a delivery commit it found, therefore changes nothing.
When step 9 fails, Delivery gives back the index step 8 recorded. When a commit does not verify in
step 10, Delivery takes it off the branch again. This leaves the index and the worktree as the
commit left them:

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

[The steps](#the-steps) gives each step's actor and stopping rule.
[The commit is the record](#the-commit-is-the-record) explains why the commit is all Delivery keeps.

## Running delivery

When the workspace's work is complete, the task level runs the command in the task worktree. Each
verified step may already be committed on the branch, so a clean worktree is the normal case:

```text
concorde delivery [--adoption] [--detach]
```

It is an [execution command](../../glossary.json#concept.execution-command). The
[Execution runner](../../execution/runner.md) runs it in the workspace whose
[binding](../../glossary.json#concept.workspace-binding) lies in the worktree it starts in. The
runner holds the [workspace lock](../../glossary.json#concept.workspace-lock). It records the command
in the [run store](../../glossary.json#concept.run-store). When a worktree has no binding, the runner
refuses the command with `binding_required`. The command commits nothing in that case. It requires
new work since the base commit. It then uses Validation's own steps to decide the
[readiness](../../glossary.json#concept.readiness) of the whole workspace. It requires that readiness
to be ready. These steps cover every commit since the base and every uncommitted change, as a
`task-validation` run does:

- The structural validation.
- The unbound-path check.
- The [configured checks](../../glossary.json#concept.configured-check).

An earlier `task-validation` run is only a preview. Delivery never trusts it or the checks of
single steps. When a changed path outside `specs/` and `.concorde/` is bound by a Module's
realization, the workspace **changed code**. Tests are included. When the workspace changed code, Delivery also
requires a test with a
[verification declaration](../../glossary.json#concept.verification-declaration). That declaration
names every scenario the workspace added or changed. When ready, Delivery commits every
uncommitted change on the bound branch as the
[delivery commit](../../glossary.json#concept.delivery-commit). The
[run result](../../glossary.json#concept.run-result) carries the commit
([contract](contracts.md#contract.delivery.output)). Its kind is `command`. It has no worker. The
task level then has the branch merged, in Concorde by the main agent. It then ends the task.

`--adoption` marks a delivery that describes code which already existed. The
[brownfield workflow](../../glossary.json#concept.brownfield-workflow) delivers such a delivery.
Such a delivery changes no behaviour. It adds no test. The scenarios it writes are therefore exempt from the
changed-code test rule. That rule requires changed code to ship with a test for each scenario it
added or changed. Delivery does not check this claim. The flag is the caller's declaration. Delivery
records it as `scenario-tests` evidence `exempt`. Every other rule applies unchanged.

### The result

| Status | Code | Reason | Detail |
| --- | --- | --- | --- |
| `blocked` | `nothing_to_deliver` | `decision` | no commit since the base commit and no uncommitted change (`git` evidence) |
| `blocked` | `not_ready` | `decision` | the whole workspace is not ready; Validation's `not_deliverable` link is the cause, with one cause per finding |
| `blocked` | `unverified_scenarios` | `decision` | the workspace changed code while a scenario it added or changed has no verifying test; names each with its document |
| `failed` | — | — | `wrong_branch`, Validation's `measurement_failed`, `checks_unavailable` or `inputs_changed`, an index Git cannot record (`index_unrecorded`), Git refusing (`stage_failed`, `commit_failed`) or a commit that does not verify, the one it made, which it takes off the branch again, one Git did not name, or the delivery commit it found at the head (`commit_unverified`) |

The error is the run's own link of level `command`, with the actor `Command delivery <run-id>
(workspace <workspace>)`. Every `blocked` code carries a host evidence `ref` of the same name.
It also carries an explanation of its own reason. A blocked delivery writes nothing in the
workspace. The fix is one of these actions:

- Do more work.
- End the task.
- Repair the findings and run `delivery` again.

A `failed` Git refusal, such as a hook or a missing author identity, carries the hook's output as
`git` evidence. It also carries a `component` cause with the Git command's exit status and output.
Delivery leaves the index as validated. Delivery keeps any worktree file a failing hook changed. It names
each such file. When an index has unmerged paths from an unfinished merge, the error is
`index_unrecorded`. Its reason is `decision`. It carries the paths as `git` evidence. Resolving or
aborting the merge is the task level's decision. When any other Git refusal prevents recording the
index, the error is `index_unrecorded` with the reason `environment`. Either way, its cause is one
of these links, with Git's output:

- The `git write-tree` link.
- The `git ls-tree` link.
- The `git ls-files` link.

Nothing has changed yet.

## How it is built

Delivery makes the delivery commit. Workers do not. A delivery makes a proposal part of the history
that is merged. It must match what was checked. Only deterministic code that checks it can prove
that match. Thus, immediately before committing, Delivery decides the readiness itself. It decides
the readiness over the whole workspace since its base. It does not trust an earlier
`task-validation` run or the checks each step passed. Steps are verified one at a time. Only the
whole can show that the steps still fit together. Validation's last step remeasures the inputs. When a change occurs while the checks run,
the run fails. The commit follows at once, so it is exactly what was validated, or nothing.

The commit carries no evidence file of its own. Its subject is the whole mark of a delivery. Run
identities and digests committed with it could never be checked later. The results they name are
local and removed by retention. Nothing ever read them. While the delivery run's trace node is
kept, it holds the readiness's record. Delivery changes no
[Spec](../../glossary.json#concept.spec) itself. When the readiness is decided, every realization
entry already exists. The task level binds a new file only once it has
created it. The commit therefore holds exactly what was validated.

Since delivery involves no model, it is an execution command rather than an
[Operation](../../glossary.json#concept.operation). It is a run nonetheless. Thus, a workflow can
take it as a step. Its evidence and
[error chain](../../glossary.json#concept.error-chain) reach its caller like any run's.

### The commit is the record

A delivery is recorded once, in the commit that makes it. Nothing else records it. A second record, such
as a list of deliveries in a task record, could disagree with the branch. A run that ends between
its commit and its bookkeeping leaves a delivered branch that the record says is not delivered.
That then needs a repair step. With the commit as the only record there is nothing to repair. The
next `delivery` sees the head is a delivery commit. It validates the workspace again. It then
reports the commit. Whoever needs to know whether a workspace is delivered reads the branch. When
both conditions hold, the task level counts a task as delivered in Concorde:

- Its branch head is a delivery commit of its workspace.
- Its worktree is clean.

It merges only such a head. Since the subject alone marks a delivery, Delivery keeps a rejected
commit from becoming such a record. It takes a commit it rejected off the branch in the same run.
Before reporting a delivery commit it finds at the head, it validates that commit again. The commit
as the record also keeps Delivery ignorant of tasks, as every part below the task level is. The
commit names the workspace, which the binding names, and nothing else.

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

Every step before 8 leaves the workspace as it was. Validation writes its check nodes and the
readiness only to the run's [trace node](../../glossary.json#concept.trace-node). Thus, a blocked
delivery changes nothing in the workspace. A delivery that reports a delivery commit it found also
changes nothing in the workspace.

By steps 3 to 6, Delivery validates a delivery commit found at the head exactly as it validates new
work. Its subject and its one parent show only that Delivery may have created it. They do not show
that what it holds is ready. Delivery reports either of these commits only once its workspace is
ready again:

- A commit a rejected run left behind.
- A commit another hand gave the subject.

When step 9 fails, Delivery gives back the index as step 8 recorded it. Step 9 fails with one of
these:

- `measurement_failed` while staging.
- `stage_failed`.
- `commit_failed`.

Delivery never undoes an edit of the worktree. A failing commit hook may leave edits the developer
wants. One example is a formatter that rewrites files then rejects the commit. So Delivery measures
the worktree again with Validation's input measurement. In the run's summary and detail, Delivery
names every path whose mode or content is not what the readiness examined. It keeps those paths.
When there is none, the workspace is again what the readiness describes. The next delivery
validates whatever the worktree then holds.

Step 8 records the index with Git's own means rather than a copy Delivery would keep:

- `git write-tree` records the index's entries.
- `git ls-files` lists the paths. Those the tree lacks are intent-to-add entries a tree cannot hold.
- `git ls-files -v` shows the skip-worktree and assume-unchanged flags.

Delivery restores the recorded parts with these commands:

- `git read-tree` restores the index's entries.
- `git add -N` marks the intent-to-add entries again.
- `git update-index` sets the flags again.

So changes staged before the delivery stay staged, including a staged version the worktree has
changed since. Even when another restoration fails, Delivery attempts to restore the intent-to-add
entries and each kind of flag. When Git refuses to read the recorded tree back into the index,
Delivery attempts none of those restorations. They apply only to an index that was read back. In
that case, the run's summary and detail say that they were not restored.

The run's summary and detail name each part that fails:

- The index.
- The intent-to-add entries.
- A kind of flag.

They then say the index is not as the readiness examined it. Each failed part is a `component`
cause of its error with Git's own account. When the worktree cannot be measured again, the run's
summary and detail say so. They include the measurement's account as a `component` cause.

A `commit_unverified` failure of step 10 comes after the commit exists. A commit Delivery rejected
must not stay where it would be read as a delivery. Delivery moves the bound branch back to the
validated head with `git update-ref` only while both conditions hold:

- The validated head is the commit's only parent.
- The branch still points at the commit.

Delivery leaves the index and the worktree as the commit left them. Thus, what a hook changed stays
there to be inspected. Its error says that Delivery took the commit off the branch. The error names it.
Since the run created it, the run's trace node still references it as `commit`.

When the head is not such a commit, Delivery moves nothing. One example is a hook that committed
again on top. When Git refuses the move, Delivery also moves nothing. Thus, it never takes off a
commit it did not create. The error says that the commit stays and why:

- The branch no longer points at it, naming the commit it points at.
- Git refused to move a branch that still points at it.

The error includes `git update-ref`'s account as a `component` cause. Repairing the branch is then
the task level's decision. See the [requirements](requirements.md) and
[scenarios](scenarios.md).

Delivery proves what it committed rather than assuming it. The repository's commit hooks run
normally. A pre-commit hook may change a file. The hook may then stage it again. In that case, the
commit Git creates can hold content the readiness never examined. This can happen while the
worktree is still clean. Just before `git commit`, step 9 therefore records the tree of the staged
index with `git write-tree`. Step 10 compares it with the new commit's tree. It names every path
that differs.

A commit message hook may likewise rewrite the message, such as by prefixing a ticket to the
subject. This would leave a commit without the subject that marks a delivery. Step 10 also compares
the commit's subject with the delivery subject. It names the subject the commit carries. Delivery
accepts a hook that only adds to the body, such as a `Change-Id` trailer.

Step 10 verifies the commit that `git commit` names on its standard output as the one it created.
The run's trace node references that same commit. Once its post-commit hook runs, Git prints the
commit it created. Git gives every hook's standard output to its standard error. Thus, a
post-commit hook that commits again on top cannot pass its commit off as the delivery commit.
The branch head would let it do so. Since a repository may switch off its reflog, the branch's
reflog would not do. The first commit on top of the validated head would not do either. A hook
amending the commit replaces it. When Git names no commit, the run fails `commit_unverified`. It
moves nothing.

In step 2, Delivery recognises a delivery commit by its subject alone, which any commit can carry.
Delivery reports the head as delivered only when both conditions hold:

- It also has exactly one parent, as every commit Delivery creates has.
- Steps 3 to 6 found its workspace ready.

Thus, Delivery does not take a merge commit reworded with the subject for a delivery. A head that
fails the parent check is `commit_unverified` with the reason `decision`. What to do with a commit
that does not hold what it claims is the task level's decision. Delivery does not distinguish a
cherry-picked or reworded commit with one parent from a delivery by its form. The subject is a mark
the task level relies on, not a proof. Before it reports the commit, Delivery therefore validates
what it holds.

### The command

<a id="realization.delivery.command"></a>

The **Delivery command** realization holds these parts and their tests:

- The steps.
- The commit message.
- The reader of earlier delivery commits.

## What Delivery relies on

- <a id="uses-execution"></a>**Execution**'s runner runs the command. It reads the workspace
  binding, which gives the steps these values:

  - The workspace's name.
  - The workspace's goal.
  - The workspace's Modules.
  - The bound branch.
  - The base commit.

  The runner holds the workspace lock for the whole run. Thus, no other run changes the workspace
  between the readiness and the commit. The runner records the run.
- <a id="uses-commands"></a>**Commands**, Execution's execution-command framework, is what
  `delivery` plugs into. Method registers its definition there. This is how the runner finds this
  [Module](../../glossary.json#concept.module)'s definition by the command's name.
- <a id="uses-kernel"></a>The **Kernel** gives Delivery these:

  - The format of the [workspace binding](../../glossary.json#concept.workspace-binding) it reads
    through the run context ([contract](../../kernel/contracts.md#contract.kernel.workspace-binding)).
  - The [workspace lock](../../glossary.json#concept.workspace-lock) the runner holds for it.
  - The [delivery commit](../../glossary.json#concept.delivery-commit) convention it makes its
    commits by.

  Thus, Coordination, which depends on the Kernel and not on Method, recognizes Delivery's commits.
- <a id="uses-validation"></a>**Validation** provides the readiness steps. Delivery runs those
  steps as its own. Thus, its readiness is decided exactly as a `task-validation` run's. Delivery
  relies on their final remeasurement to prove that the measured inputs at the end are those the
  readiness records. It never changes a finding. It treats a readiness that is not ready as
  blocking.
- <a id="uses-spec"></a>**Spec core** answers step 6 on the workspace's Specs as they read now.
  It answers which changed paths a Module's realization binds. Through its structural validation's
  coverage findings, it also answers which scenarios no test declares that it verifies. Delivery
  reads the base commit's text of each changed reading document itself, with read-only Git. This
  finds the scenarios the workspace added or changed. Delivery relies on Spec core loading the
  Specs completely or refusing. Delivery never changes them in this step.
