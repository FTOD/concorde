# Delivery

## Purpose

Delivery turns a validated task worktree into a commit. It provides the deterministic `delivery`
Operation: when the task's latest readiness is ready and still current, it commits every worktree
change on the task branch with an evidence bundle recording what was validated and which runs
produced it, and records the delivery in the task record. The main agent relies on it so what it
merges is exactly what was validated. Delivery is the only part of Concorde that commits — workers
never touch Git — and it never merges, pushes, rewrites history, validates on its own, or delivers
a worktree that changed after validation.

## Terminology

| Term | Definition |
| --- | --- |
| Delivery commit | The commit Delivery creates on a task branch, holding every change the task's current readiness examined and the evidence bundle for it. |
| Evidence bundle | The JSON file committed with a delivery that records the task, the readiness the delivery consumed and the Operation runs that led to it. |
| [Main agent](../../vocabulary.md#concept.concorde.main-agent) | |
| [Worker](../../vocabulary.md#concept.concorde.worker) | |
| [Evidence](../../vocabulary.md#concept.concorde.evidence) | |
| [Task](../../tasks/module.md#concept.tasks.task) | |
| [Task record](../../tasks/module.md#concept.tasks.task-record) | |
| [Task state](../../tasks/module.md#concept.tasks.task-state) | |
| [Readiness](../validation/module.md#concept.validation.readiness) | |
| [Run record](../../harness/workers/module.md#concept.workers.run-record) | |
| [Operation](../module.md#concept.operations.operation) | |
| [Operation result](../module.md#concept.operations.result) | |

## Usage

The main agent runs the Operation right after a `validate` run whose readiness was ready:

```text
concorde run delivery --task severity
```

The Operation takes no arguments of its own. It loads the task's latest `validate`
[readiness](../validation/module.md#concept.validation.readiness), requires it ready, and
remeasures the worktree as Validation did. Unchanged, it clears the confirmed pending markers,
writes the evidence bundle, commits everything on the task branch, and records the delivery in the
[task record](../../tasks/module.md#concept.tasks.task-record), making the
[task state](../../tasks/module.md#concept.tasks.task-state) delivered. The
[Operation result](../module.md#concept.operations.result) carries the commit
([contract](contracts.md#contract.delivery.output)). The main agent then merges the branch with
Git, unasked, and closes the task.

```d2
op: Delivery Operation
commit: Delivery commit
bundle: Evidence bundle
op -> commit: creates
commit -> bundle: carries
```

<a id="concept.delivery.delivery-commit"></a>

A **delivery commit** has subject `concorde: deliver <task-id>`, the goal as body, and three
trailers: `Concorde-Task`, `Concorde-Evidence` (bundle path) and `Concorde-Readiness` (the
`validate` run consumed). Its parent is the validated branch head; it contains every uncommitted
change except what Git ignores. A task may be delivered several times — another `implement` after
a code review, say — each a new commit on top, never amended.

<a id="concept.delivery.evidence-bundle"></a>

The **evidence bundle** is committed at `.concorde/evidence/<task-id>/<n>.json` (`n` counts
deliveries from 1): the task, goal, Modules, base/parent commits, the consumed readiness (input
digest, check results), applied confirmations, and each run since the previous delivery (operation,
status, summary, worker run identities, result digest). Full results,
[run records](../../harness/workers/module.md#concept.workers.run-record) and worker transcripts
stay in the Git-ignored `.concorde/runs/`; the bundle carries only identities and digests
([exact shape](contracts.md#contract.delivery.evidence-bundle)).

| Status | Code | Reason | Detail |
| --- | --- | --- | --- |
| `blocked` | `no_readiness` | `decision` | no validate run yet, or the latest run produced no readiness (then its error chain is the cause) |
| `blocked` | `not_ready` | `decision` | latest readiness not ready (its error chain is the cause) |
| `blocked` | `stale_readiness` | `decision` | worktree changed since validation |
| `blocked` | `nothing_to_deliver` | `decision` | nothing to commit (`git` evidence) |
| `failed` | — | — | wrong branch, confirmations fail, or Git refuses |

Every `blocked` code carries a `readiness` host evidence `ref` (`git` for `nothing_to_deliver`);
Delivery writes nothing, and the fix is usually to address the findings or rerun `validate`. A
`failed` Git refusal — a hook, a missing author identity — carries the hook's output as `git`
evidence and a `component` cause with the Git command's exit status and output; the worktree is
left as validated. An unrecorded delivery commit found at the next run is recorded, not repeated.

## Design

Delivery commits, workers do not: a commit makes a proposal part of history and must match what was
checked, which only the host can prove — by repeating, immediately before committing, the same
input-digest measurement Validation bound the readiness to; any change since makes it stale, so the
commit is exactly what was validated, or nothing. The evidence travels with the branch inside the
commit rather than staying local, kept small — identities and digests, since it lives in the
repository forever. Clearing the pending markers happens last, before the commit, since until then
a filled pending file is still a proposal; doing it in the same commit keeps the Spec and its files
consistent.

| # | Step | Actor | Stops when |
| --- | --- | --- | --- |
| 1 | Resolve the worktree; require its head is the task branch | host | wrong/detached branch (`failed`) |
| 2 | Record an unrecorded delivery commit at the head, if any | host, Tasks | recovered (`ok`) |
| 3 | Load the latest `validate` readiness; require ready | host, Tasks | none (`blocked`, `no_readiness`); not ready (`blocked`, `not_ready`) |
| 4 | Remeasure via Validation, compare the digest | Validation | differs (`blocked`, `stale_readiness`) |
| 5 | Require ≥1 uncommitted change | host, read-only Git | none (`blocked`, `nothing_to_deliver`) |
| 6 | Apply confirmations via Validation | Validation | refused (`failed`) |
| 7 | Write the evidence bundle | host | — |
| 8 | Stage every change and the bundle; commit | host, Git | Git refuses (`failed`; undone, index reset) |
| 9 | Verify the commit is head, parent validated, worktree clean | host, read-only Git | mismatch (`failed`) |
| 10 | Record the delivery | Tasks | can't write (`failed`; recovered next run) |
| 11 | Return the commit as the output | host | — |

Every step before 6 only reads, so a blocked delivery leaves no trace. Steps 6–8 are undone
together when the commit fails: confirmed metadata is restored from the bytes read before, the
bundle removed and the index reset, so the worktree is again what the readiness describes. Checks
are not repeated after
confirmations, since clearing a marker changes no code and Validation revalidates the Spec
structure when it applies them. See the [requirements](requirements.md) and
[scenarios](scenarios.md).

Delivery is built as one realization:

```d2
delivery: Delivery {
  op: Delivery Operation {
    "src/concorde/delivery/"
    "tests/concorde/delivery/"
  }
}
```

<a id="realization.delivery.operation"></a>

The **Delivery Operation** realization holds the steps and the evidence bundle writer, and their
tests. The bundle is staged even where Git would ignore its path, so every commit carries it.

## Relationships

```d2
delivery: Delivery
tasks: Tasks
validation: Validation
operations: Operations
workers: Workers
delivery -> tasks
delivery -> validation
delivery -> operations
delivery -> workers
```

- <a id="uses-tasks"></a>**Tasks** resolves the task to its worktree, branch and base commit, lists
  its runs and deliveries, and records the new delivery, moving the task to delivered. Delivery
  relies on Tasks' one-run-per-task rule, and on Tasks checking a merged close against the
  delivery commits it records.
- <a id="uses-validation"></a>**Validation** provides the readiness, the input measurement and the
  confirmations. Delivery relies on the measurement matching the one the readiness was bound to —
  an equal digest proves an unchanged worktree — and on confirmations applying exactly or not at
  all; it never decides readiness, treating a missing, not ready or stale one as blocking.
- <a id="uses-operations"></a>**Operations** lists `delivery`, runs these steps through its host,
  wraps the output in the [Operation result](../module.md#concept.operations.result) and saves each
  run's result, which Delivery reads to write the bundle's run entries.
- <a id="uses-workers"></a>**Workers** keeps a
  [run record](../../harness/workers/module.md#concept.workers.run-record) for every launch.
  Delivery lists each run's record identity in the bundle so evidence can be matched locally,
  relying on those identities being unique and stable; it never reads a transcript.
