# Delivery

## Purpose

Delivery turns a workspace's new work into a delivered commit. It provides the execution command
`concorde delivery`: when the bound workspace has new work — commits on its branch since the base
commit, or uncommitted changes — it validates the whole workspace itself, exactly as Validation
decides a [readiness](../../../glossary.json#concept.readiness), and when that is ready it commits
the remaining changes on the bound branch. The
[delivery commit](../../../glossary.json#concept.delivery-commit) is the only record of the
delivery. Whoever merges the workspace relies on it, in Concorde the
[main agent](../../../glossary.json#concept.main-agent), so that what it merges is exactly what was
validated. Workers never touch Git; the task level — whoever works the task, the main agent itself
or a [task session](../../../glossary.json#concept.task-session) — may commit verified steps on the
branch, and only Delivery makes the commit that marks the work delivered. Delivery never merges, pushes,
rewrites history, repairs a finding, writes a task record, or delivers anything it did not validate
in the same run.

## Core concepts

Delivery rests on one idea, the delivery commit: the one mark of a delivery, made only on top of
what the same run validated. It builds on Validation's
[readiness](../../../glossary.json#concept.readiness).

### The delivery commit

<a id="concept.delivery-commit"></a>

A **[delivery commit](../../../glossary.json#concept.delivery-commit)** has subject
`concorde: deliver <workspace>`, which marks it as a delivery, and the goal as body. Its parent is
the branch head Delivery validated; it contains the cleared markers and every uncommitted change
except what Git ignores and untracked paths Git cannot version, such as a sandbox's `/dev/null`
mounts — only any cleared markers, and so possibly nothing, when every step was already committed.
A workspace may be delivered several times — another `implement` after a code review, say — each a
new commit on top, never amended. The delivery commits are the only record of the deliveries:
Delivery writes no [task record](../../../glossary.json#concept.task-record) and keeps no list of
its own, and reads its earlier deliveries back from the branch by their subject
([exact rule](contracts.md#delivery-commit)). Running `delivery` again when the branch head already
is a delivery commit of the workspace and nothing waits reports that commit, `ok` with `recovered`
true, and commits nothing — once it has verified that the commit has exactly one parent, as every
commit Delivery creates has; a head with the subject that fails this, such as a merge commit, is
`commit_unverified`, naming the mismatch. The delivery run's own
[trace node](../../../glossary.json#concept.trace-node) references the delivery commit, so the trace
leads to what was committed: as `commit` when the run created it, and as `found_commit` when it
found its work already delivered and reported the existing commit, which an earlier run created.
What the readiness examined and which runs led to it stay in the run's trace node and those of the
workspace's other runs, local records that [Tracing](../../../tracing/module.md)'s retention may
remove; what the task decided along the way is kept in Git by the task level, in Concorde as the
task's [decision log](../../../glossary.json#concept.decision-log) Tasks commits when the task ends.

## Overview

### Delivering a workspace

A run of `delivery` goes through ten steps. Every step before 7 leaves the workspace as it was, so a
blocked delivery changes nothing; steps 7 and 8 are undone together when step 8 fails, and a commit
that does not verify in step 9 stays for the task level to decide on:

```d2 illustrative
direction: down
branch: "1. Head on the bound branch?"
found: "2. Head already a delivery commit\nof the workspace, nothing waiting?"
work: "3. A commit since the base\nor an uncommitted change?"
readiness: "4. Decide the whole workspace's\nreadiness with Validation's steps"
ready: "5. Ready?"
tests: "6. Changed code: every added or\nchanged scenario has a verifying test?\n(skipped with --adoption)"
index: "7. Record the index,\napply the confirmations"
commit: "8. Stage every change, record\nthe staged tree, commit"
verify: "9. Verify the commit"
output: "10. Return the commit"
ok: "ok"
blocked: "blocked\nthe workspace unchanged"
failed: "failed"
branch -> found: yes
found -> work: no
work -> readiness: yes
readiness -> ready
ready -> tests: yes
tests -> index: yes
index -> commit -> verify -> output -> ok
found -> ok: "yes, one parent:\nrecovered"
found -> failed: "yes, but not one parent:\ncommit_unverified" {style.stroke-dash: 3}
branch -> failed: "no: wrong_branch" {style.stroke-dash: 3}
work -> blocked: "no: nothing_to_deliver" {style.stroke-dash: 3}
readiness -> failed: "measurement, checks\nor inputs fail" {style.stroke-dash: 3}
ready -> blocked: "no: not_ready" {style.stroke-dash: 3}
tests -> blocked: "no: unverified_scenarios" {style.stroke-dash: 3}
index -> failed: "index_unrecorded,\nconfirmations refused" {style.stroke-dash: 3}
commit -> failed: "Git refuses: 7 and 8 undone" {style.stroke-dash: 3}
verify -> failed: "mismatch: commit_unverified,\nthe commit stays" {style.stroke-dash: 3}
```

[The steps](#the-steps) gives each step's actor and stopping rule, and
[The commit is the record](#the-commit-is-the-record) why the commit is all Delivery keeps.

## Running delivery

The task level runs the command in the task worktree when the workspace's work is complete. Each
verified step may already be committed on the branch, so a clean worktree is the normal case:

```text
concorde delivery [--adoption] [--detach]
```

It is an [execution command](../../../glossary.json#concept.execution-command): the
[Execution runner](../../runner.md) runs it in the workspace whose
[binding](../../../glossary.json#concept.workspace-binding) lies in the worktree it starts in, under
the [workspace lock](../../../glossary.json#concept.workspace-lock), and records it in the run
store. In a worktree without a binding it is refused with `binding_required` and commits nothing. It
requires new work since the base commit, then decides the
[readiness](../../../glossary.json#concept.readiness) of the whole workspace with Validation's own
steps — the structural validation, the unbound-path check and the
[configured checks](../../../glossary.json#concept.configured-check) a `task-validation` run
performs, over every commit since the base and every uncommitted change — and requires it ready. An
earlier `task-validation` run is only a preview; Delivery never trusts it or the checks of single
steps. When the workspace **changed code** — a changed path outside `specs/` and `.concorde/` that a
Module's realization binds, tests included — Delivery also requires a test whose
[verification declaration](../../../glossary.json#concept.verification-declaration) names every
scenario the workspace added or changed. Ready, it clears the pending markers of the realization
entries whose files now exist (the readiness's confirmations) and commits them with any uncommitted
change on the bound branch. The
[run result](../../../glossary.json#concept.run-result), of kind `command` with no worker, carries
the commit ([contract](contracts.md#contract.delivery.output)). The task level then has the branch
merged, in Concorde by the main agent, and ends the task.

`--adoption` marks a delivery that describes code which already existed, as the
[brownfield workflow](../../../glossary.json#concept.brownfield-workflow) delivers: such a delivery
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
| `failed` | — | — | `wrong_branch`, Validation's `measurement_failed`, `checks_unavailable` or `inputs_changed`, an index Git cannot record (`index_unrecorded`), `confirmations_refused`, Git refusing (`stage_failed`, `commit_failed`) or a commit that does not verify, the one it made or the delivery commit it found at the head (`commit_unverified`) |

The error is the run's own link of level `command`, with the actor `Command delivery <run-id>
(workspace <workspace>)`. Every `blocked` code carries a host evidence `ref` of the same name and
an explanation of its own reason; a blocked delivery writes nothing in the workspace, and the fix is
to do more work or end the task, or to repair the findings and run `delivery` again. A `failed` Git
refusal — a hook, a missing author identity — carries the hook's output as `git` evidence and a
`component` cause with the Git command's exit status and output; the workspace is left as
validated. An index with unmerged paths, from a merge not finished, is `index_unrecorded` with the
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
run's trace node for as long as it is kept. Clearing the pending markers happens last,
before the commit, since until then a filled pending file is still a proposal; doing it in the same
commit keeps the [Spec](../../../glossary.json#concept.spec) and its files consistent.

Delivery is an execution command rather than an
[Operation](../../../glossary.json#concept.operation) because it involves no model; it is a run
nonetheless, so that a workflow can take it as a step, and its evidence and
[error chain](../../../glossary.json#concept.error-chain) reach its caller like any run's.

### The commit is the record

A delivery is recorded once, in the commit that makes it, and nowhere else. A second record, such
as a list of deliveries in a task record, could disagree with the branch: a run that ends between
its commit and its bookkeeping leaves a delivered branch that the record says is not delivered,
which then needs a repair step. With the commit as the only record there is nothing to repair: the
next `delivery` sees the head is a delivery commit and reports it, and whoever needs to know whether
a workspace is delivered reads the branch. In Concorde the task level does exactly that: it counts
a task as delivered when its branch head is a delivery commit of its workspace and its worktree is
clean, and merges only such a head. It also keeps Delivery ignorant of tasks, as all of Execution
is: the commit names the workspace, which the binding names, and nothing else.

### The steps

| # | Step | Actor | Stops when |
| --- | --- | --- | --- |
| 1 | Require the workspace's head to be on the branch its binding names | host | wrong or detached branch (`failed`) |
| 2 | Report the head when it already is a delivery commit of the workspace and nothing waits, after verifying that it has exactly one parent | host, read-only Git | already delivered (`ok`, `recovered`) or the head does not verify (`failed`, `commit_unverified`) |
| 3 | Require a commit since the base commit or an uncommitted change | host, read-only Git | neither (`blocked`, `nothing_to_deliver`) |
| 4 | Decide the whole workspace's readiness with Validation's steps | Validation | measurement, checks or inputs fail (`failed`) |
| 5 | Require the readiness ready | host | not ready (`blocked`, `not_ready`) |
| 6 | When the workspace changed code, require a test declaring that it verifies every scenario it added or changed since its base commit, unless `--adoption` | host, Spec core, read-only Git | an unverified scenario (`blocked`, `unverified_scenarios`, naming each with its document) |
| 7 | Record the index with Git; apply confirmations via Validation | host, Git, Validation | the index cannot be recorded (`failed`, `index_unrecorded`) or confirmations refused (`failed`) |
| 8 | Stage every change; record the staged tree; commit | host, Git | Git refuses (`failed`; undone, index restored) |
| 9 | Verify the commit is head, its tree the staged tree, parent validated, worktree clean | host, read-only Git | mismatch (`failed`, `commit_unverified`; the commit stays) |
| 10 | Return the commit as the output, numbered after the delivery commits on the branch | host | — |

Every step before 7 leaves the workspace as it was — Validation writes its check nodes and the
readiness only to the run's [trace node](../../../glossary.json#concept.trace-node) — so a blocked
delivery changes nothing in the workspace. Steps 7 and 8 are undone together when step 8 fails
(`measurement_failed` while staging, `stage_failed`, `commit_failed`): confirmed metadata is
restored from the bytes read before and the index given back as step 7 recorded it, so the
workspace is again what the readiness describes. Step 7 records the index with Git's own means rather than a copy Delivery
would keep: `git write-tree` for its entries, which `git read-tree` restores; the paths `git
ls-files` lists that the tree lacks, which are intent-to-add entries a tree cannot hold and
`git add -N` marks again; and the skip-worktree and assume-unchanged flags `git ls-files -v`
shows, which `git update-index` sets again. So changes staged before the delivery, including a
staged version the worktree has changed since, stay staged. Every part of the undo is attempted
even when another fails; each part that fails — a metadata file, the index, the intent-to-add
entries or a kind of flag — is named in the run's summary and detail, which then say the
workspace is not as the readiness examined it, and is a `component` cause of its error with the
file system's or Git's own account. A
`commit_unverified` failure comes after the commit exists: Delivery leaves it in place, since it
never rewrites history, and repairing the branch is the task level's decision. Checks are not
repeated after confirmations, since clearing a marker changes no code and Validation revalidates the
Spec structure when it applies them. See the [requirements](requirements.md) and
[scenarios](scenarios.md).

Delivery proves what it committed rather than assuming it. The repository's commit hooks run
normally, and a pre-commit hook may change a file and stage it again, so the commit Git creates can
hold content the readiness never examined while the worktree is still clean. Step 8 therefore
records the tree of the staged index with `git write-tree` just before `git commit`, and step 9
compares it with the new commit's tree, naming every path that differs. A delivery commit is
recognised in step 2 by its subject alone, which any commit can carry; Delivery reports the head as
delivered only when it also has exactly one parent, as every commit it creates has, so that a merge
commit reworded with the subject is not taken for a delivery. A head that fails this is
`commit_unverified` with the reason `decision`, since what to do with a commit that does not hold
what it claims is the task level's decision. A cherry-picked or reworded commit with one parent is
not told from a delivery: the subject is a mark the task level relies on, not a proof.

### The command

<a id="realization.delivery.command"></a>

The **Delivery command** realization holds the steps, the commit message and the reader of earlier
delivery commits, and their tests.

## What Delivery relies on

- <a id="uses-execution"></a>**Execution**'s runner runs the command: it reads the workspace
  binding, which gives the steps the workspace's name, goal, Modules, bound branch and base commit,
  holds the workspace lock for the whole run, so no other run changes the workspace between the
  readiness and the commit, and records the run.
- <a id="uses-commands"></a>**Commands** lists `delivery` in its catalog, which is how the runner
  finds this [Module](../../../glossary.json#concept.module)'s definition by the command's name.
- <a id="uses-validation"></a>**Validation** provides the readiness steps and the confirmations.
  Delivery runs those steps as its own, so its readiness is decided exactly as a `task-validation`
  run's, relies on their final remeasurement to prove that the measured inputs at the end are
  those the readiness records, and on confirmations applying exactly or not at all; it never
  changes a finding, treating a readiness that is not ready as blocking.
- <a id="uses-spec"></a>**Spec core** answers step 6 on the workspace's Specs as they read now:
  which changed paths a Module's realization binds and, through its structural validation's
  coverage findings, which scenarios no test declares that it verifies. Delivery reads the base
  commit's text of each changed reading document itself, with read-only Git, to find the scenarios
  the workspace added or changed; it relies on Spec core loading the Specs completely or refusing,
  and never changes them in this step.
