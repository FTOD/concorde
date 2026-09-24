# Validation

## Purpose

Validation decides whether a task worktree is ready to deliver, with the deterministic `validate`
Operation: it checks the Spec structure, finds the Modules the task changed, runs their configured
checks, and returns a readiness — ready or not, with every blocking finding — bound to the exact
worktree state examined. The main agent relies on it to see whether a task is deliverable;
Delivery runs the same steps itself right before it commits. Validation launches no worker,
changes no file of the task worktree, and judges nothing a deterministic check cannot: whether code keeps its promises beyond
what the checks test, or whether a Spec explains enough, is for the reviews and the main agent.

## Terminology

| Term | Definition |
| --- | --- |
| Readiness | The outcome of Validation's readiness steps in one `validate` or `delivery` run: whether the task worktree may be delivered, with its blocking findings, the checks run and the pending entries to confirm, bound to a digest of the exact inputs examined. |
| [Main agent](../../vocabulary.md#concept.concorde.main-agent) | |
| [Module](../../vocabulary.md#concept.concorde.module) | |
| [Evidence](../../vocabulary.md#concept.concorde.evidence) | |
| [Structural check](../../spec-tooling/spec/module.md#concept.spec.structural-check) | |
| [Impact index](../../spec-tooling/spec/module.md#concept.spec.impact-index) | |
| [File transaction](../../spec-tooling/spec/module.md#concept.spec.file-transaction) | |
| [Configured check](../../harness/checks/module.md#concept.checks.configured-check) | |
| [Check result](../../harness/checks/module.md#concept.checks.check-result) | |
| [Task](../../tasks/module.md#concept.tasks.task) | |
| [Operation](../module.md#concept.operations.operation) | |
| [Operation result](../module.md#concept.operations.result) | |

## Usage

The main agent runs the Operation when it wants to know whether a task's work is complete, usually
after `implement`, `test` and the reviews. `delivery` decides the same readiness again itself, so a
`validate` run is a preview, not a precondition:

```text
concorde run validate --task severity
```

The Operation takes no arguments of its own. Its bound Modules (`--modules`, the task's by default)
never narrow what is validated — readiness concerns the whole worktree — but add their checks to
the changed Modules'. It returns an [Operation result](../module.md#concept.operations.result)
whose `output` is the readiness ([contract](contracts.md#contract.validation.readiness)), one per
run.

<a id="concept.validation.readiness"></a>

A **readiness** is `ready` when the Specs have no structural error, every changed path is
accounted for, and every check run passed; otherwise it lists every blocking finding the run
established, not only the first, each of one kind:

| Kind | Blocking when |
| --- | --- |
| `load` | the Specs fail to load at all |
| `structural` | a [structural check](../../spec-tooling/spec/module.md#concept.spec.structural-check) error, e.g. a broken link or stale registry mirror |
| `unbound` | a changed path is not a Spec document, control record, generated/build output, external material (including a submodule a Module includes), or Module-bound |
| `check` | a changed or bound Module's [configured check](../../harness/checks/module.md#concept.checks.configured-check) failed, timed out or couldn't run |

Warnings, such as missing scenario coverage, are reported but never block. A pending entry whose
file now exists is not an error but a **confirmation**, cleared by Delivery on commit. Changed
Modules bind a changed file or own a changed Spec document, found through the
[impact indexes](../../spec-tooling/spec/module.md#concept.spec.impact-index); a shared file runs
all its Modules' checks.

The readiness records its inputs — head, base, every changed path's digest and the configuration
digest — as one input digest, which proves exactly which inputs a readiness describes; a later
worktree change alters it.

| Status | Code | Reason | Detail |
| --- | --- | --- | --- |
| `ok` | — | — | task is ready |
| `blocked` | `not_deliverable` | `decision` | one cause per finding: `check` (exit code, log tail) or `component` (rule, location, message) |
| `failed` | `wrong_branch` | `permission` | not on the task branch |
| `failed` | `measurement_failed` | — | Git's error as cause |
| `failed` | `checks_unavailable` | — | Check execution's error as cause |
| `failed` | `inputs_changed` | — | worktree changed mid-run |

A blocked summary starts `Not deliverable:` with the finding count; each finding is named by kind,
location and message, as host evidence and as the
[error chain](../../vocabulary.md#concept.concorde.error-chain)'s causes — so the main agent sees
everything blocking delivery from the result alone. The readiness is always the output; the usual
fix is another `implement`, a `specify`, or regenerating a stale registry mirror. Each `failed`
code carries a host evidence entry with the same code. Running `validate` again on an unchanged
worktree gives the same readiness with fresh check results.

## Design

Readiness is decided by deterministic code alone, so Delivery can run the same steps and trust
their outcome without asking — a model's opinion of completeness is not enough. Binding it to an
input digest, remeasured at the end, proves the inputs did not change while the checks ran, rather
than trusting a timestamp.

The measurement covers everything Delivery will commit: tracked changes since the base commit and
untracked files Git does not ignore. An untracked path Git cannot version, such as the `/dev/null`
mounts with which Claude Code's Bash sandbox hides `.bashrc` or `.claude/settings.json` from a task
session, is left out, so the readiness and delivery come out the same inside and outside that
sandbox. Checks run only for the changed Modules — checking a whole
project every run would be too slow — so a Module broken only through one it uses is caught only
when bound or named with `--modules`. Structural validation always covers the whole worktree, since
a Spec change can break a link anywhere.

| # | Step | Actor | Stops when |
| --- | --- | --- | --- |
| 1 | Resolve the task worktree; require its head is the task branch | host | wrong or detached branch (`failed`) |
| 2 | Measure inputs: head, base, changed paths' digests, config digest, combined | host, read-only Git | Git can't report the changes (`failed`) |
| 3 | Validate the task worktree's Spec structure | Spec core | — |
| 4 | Sort findings: errors block, filled pending entries become confirmations, warnings kept | host | — |
| 5 | Require every changed path be a Spec document, control record or Module-bound | host, Spec core | — |
| 6 | Derive the changed Modules via the impact indexes | Spec core | — |
| 7 | Run the changed and bound Modules' configured checks | Check execution | check boundary unavailable (`failed`) |
| 8 | Remeasure inputs, compare the digest | host | digest changed (`failed`, `inputs_changed`) |
| 9 | Save the readiness and return it | host | — |

Steps 3–7 collect every blocking finding rather than stopping at the first: step 3 reads the Specs
as they will look once confirmed, so a filled pending entry is no error, and an unbound path is
reported once, at step 5. When the Specs fail to load, steps 5–7 are skipped and the load failure
itself blocks, naming the file and the loader's error. A bound Module the loaded registry does not
register is a structural blocking finding. Unlike other Operations, the host does not load the
Specs before the run, so these diagnoses always reach the main agent. Step 8 catches worktree
changes during a check, which can take minutes.

A `validate` run writes nothing in the task worktree; its logs and readiness go to the run
directory in the primary worktree. Delivery reuses the readiness steps and a confirmation service
that clears exactly the listed pending markers in one
[file transaction](../../spec-tooling/spec/module.md#concept.spec.file-transaction), bound to the
measured metadata digests, then revalidates and rolls back on any remaining error. See the
[requirements](requirements.md) and [scenarios](scenarios.md).

Validation is built as one realization:

```d2
validation: Validation {
  op: Validate Operation {
    "src/concorde/validation/"
    "tests/concorde/validation/"
  }
}
```

<a id="realization.validation.operation"></a>

The **Validate Operation** realization holds the steps, the input measurement, the confirmation
service Delivery calls, and their tests, with the task fixture Delivery's tests share.

## Relationships

```d2
validation: Validation
spec: Spec core
checks: Check execution
tasks: Tasks
operations: Operations
validation -> spec
validation -> checks
validation -> tasks
validation -> operations
```

- <a id="uses-spec"></a>**Spec core** validates the Specs, answers through its impact indexes which
  Modules bind a path or own a document, and applies confirmations as a file transaction.
  Validation relies on the validator being deterministic and on loading refusing, not partially
  reading, a Spec that cannot support a boundary; it always roots Spec core at the task worktree.
- <a id="uses-checks"></a>**Check execution** runs each changed Module's
  [configured checks](../../harness/checks/module.md#concept.checks.configured-check) read-only,
  with the task worktree as the project, and returns one
  [check result](../../harness/checks/module.md#concept.checks.check-result) per check, copied into
  the readiness unchanged; a boundary it cannot establish fails the run.
- <a id="uses-tasks"></a>**Tasks** resolves the task to its worktree, branch and base commit.
  Validation reads the record and changes nothing in it; the Operation host records the run.
- <a id="uses-operations"></a>**Operations** lists `validate`, runs these steps through its host,
  wraps the readiness in the [Operation result](../module.md#concept.operations.result), and
  allows no other run of the task meanwhile, so no worker changes the worktree during validation.
