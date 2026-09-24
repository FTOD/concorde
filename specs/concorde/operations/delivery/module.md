# Delivery

## Purpose

Delivery turns a task's new work into a delivered commit. It provides the deterministic `delivery`
Operation: when the task has new work — commits on its branch since the previous delivery (or its
base), or uncommitted changes — it validates the whole task itself, exactly as Validation decides a
readiness, and when that is ready it commits the remaining changes on the task branch with an
evidence bundle recording what was validated and which runs produced it, and records the delivery
in the task record. The main agent relies on it so what it merges is exactly what was validated.
Workers never touch Git; the main agent may commit verified steps on the task branch, and only
Delivery makes the commit that carries the evidence. Delivery never merges, pushes, rewrites
history, repairs a finding, or delivers anything it did not validate in the same run.

## Terminology

| Term | Definition |
| --- | --- |
| Delivery commit | The commit Delivery creates on top of a task branch it validated, holding the evidence bundle, the metadata its confirmations changed and every change not yet committed. |
| Evidence bundle | The JSON file committed with a delivery that records the task, the readiness the delivery decided and the Operation runs that led to it. |
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

The main agent runs the Operation when the task's work is complete. Each verified step may
already be committed on the task branch, so a clean worktree is the normal case:

```text
concorde run delivery --task severity
```

The Operation takes no arguments of its own. It requires new work since the previous delivery (or
the base), then decides the [readiness](../validation/module.md#concept.validation.readiness) of
the whole task with Validation's own steps — the structural validation, the unbound-path check and
the configured checks a `validate` run performs, over every commit since the base and every
uncommitted change — and requires it ready. An earlier `validate` run is only a preview; Delivery
never trusts it or the checks of single steps. Ready, it clears the confirmed pending markers,
writes the evidence bundle, commits it with any uncommitted change on the task branch, and records
the delivery in the [task record](../../tasks/module.md#concept.tasks.task-record), making the
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
delivery run, which decided the readiness). Its parent is the branch head Delivery validated; it
contains the bundle, the cleared markers and every uncommitted change except what Git ignores —
only the bundle when every step was already committed. A task may be delivered several times —
another `implement` after a code review, say — each a new commit on top, never amended.

<a id="concept.delivery.evidence-bundle"></a>

The **evidence bundle** is committed at `.concorde/evidence/<task-id>/<n>.json` (`n` counts
deliveries from 1): the task, goal, Modules, base/parent commits, the readiness the delivery
decided (input digest, check results), applied confirmations, and each run since the previous
delivery (operation, status, summary, worker run identities, result digest). Full results,
[run records](../../harness/workers/module.md#concept.workers.run-record) and worker transcripts
stay in the Git-ignored `.concorde/runs/`; the bundle carries only identities and digests
([exact shape](contracts.md#contract.delivery.evidence-bundle)).

| Status | Code | Reason | Detail |
| --- | --- | --- | --- |
| `blocked` | `nothing_to_deliver` | `decision` | no commit since the previous delivery (or the base) and no uncommitted change; names which (`git` evidence) |
| `blocked` | `not_ready` | `decision` | the whole task is not ready; Validation's `not_deliverable` link is the cause, with one cause per finding |
| `failed` | — | — | wrong branch, Validation's `measurement_failed`, `checks_unavailable` or `inputs_changed`, confirmations fail, or Git refuses |

Every `blocked` code carries a host evidence `ref` of the same name (`git` for
`nothing_to_deliver`, `readiness` for `not_ready`) and an explanation of its own reason; Delivery
writes nothing in the task worktree, and the fix is to do more work or close the task, or to
repair the findings and run `delivery` again. A
`failed` Git refusal — a hook, a missing author identity — carries the hook's output as `git`
evidence and a `component` cause with the Git command's exit status and output; the worktree is
left as validated. An unrecorded delivery commit found at the next run is recorded, not repeated.

## Design

Delivery commits the evidence, workers do not: a delivery makes a proposal part of the history the
main agent merges and must match what was checked, which only the host can prove. So Delivery
decides the readiness itself, over the whole task since its base, immediately before committing,
rather than trusting an earlier `validate` run or the checks each step passed — steps are verified
one at a time, and only the whole can show that they still fit together. Validation's last step
remeasures the inputs, so a change while the checks ran fails the run; the commit follows at once,
so it is exactly what was validated, or nothing. The evidence travels with the branch inside the
commit rather than staying local, kept small — identities and digests, since it lives in the
repository forever. Clearing the pending markers happens last, before the commit, since until then
a filled pending file is still a proposal; doing it in the same commit keeps the Spec and its files
consistent.

| # | Step | Actor | Stops when |
| --- | --- | --- | --- |
| 1 | Resolve the worktree; require its head is the task branch | host | wrong/detached branch (`failed`) |
| 2 | Record an unrecorded delivery commit at the head, if any | host, Tasks | recovered (`ok`) |
| 3 | Require a commit since the previous delivery (or the base) or an uncommitted change | host, Tasks, read-only Git | neither (`blocked`, `nothing_to_deliver`) |
| 4 | Decide the whole task's readiness with Validation's steps | Validation | measurement, checks or inputs fail (`failed`) |
| 5 | Require the readiness ready | host | not ready (`blocked`, `not_ready`) |
| 6 | Apply confirmations via Validation | Validation | refused (`failed`) |
| 7 | Write the evidence bundle | host | — |
| 8 | Stage every change and the bundle; commit | host, Git | Git refuses (`failed`; undone, index reset) |
| 9 | Verify the commit is head, parent validated, worktree clean | host, read-only Git | mismatch (`failed`) |
| 10 | Record the delivery | Tasks | can't write (`failed`; recovered next run) |
| 11 | Return the commit as the output | host | — |

Every step before 6 leaves the task worktree as it was — Validation writes its check logs and the
readiness only to the run directory — so a blocked delivery changes nothing in the task. Steps
6–8 are undone together when the commit fails: confirmed metadata is restored from the bytes read
before, the bundle removed and the index reset, so the worktree is again what the readiness
describes. Checks are not repeated after confirmations, since clearing a marker changes no code
and Validation revalidates the Spec structure when it applies them. See the
[requirements](requirements.md) and [scenarios](scenarios.md).

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
- <a id="uses-validation"></a>**Validation** provides the readiness steps and the confirmations.
  Delivery runs those steps as its own, so its readiness is decided exactly as a `validate` run's,
  relies on their final remeasurement to prove the worktree did not change while checks ran, and
  on confirmations applying exactly or not at all; it never changes a finding, treating a
  readiness that is not ready as blocking.
- <a id="uses-operations"></a>**Operations** lists `delivery`, runs these steps through its host,
  wraps the output in the [Operation result](../module.md#concept.operations.result) and saves each
  run's result, which Delivery reads to write the bundle's run entries.
- <a id="uses-workers"></a>**Workers** keeps a
  [run record](../../harness/workers/module.md#concept.workers.run-record) for every launch.
  Delivery lists each run's record identity in the bundle so evidence can be matched locally,
  relying on those identities being unique and stable; it never reads a transcript.
