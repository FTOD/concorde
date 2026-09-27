# Validation

## Purpose

Validation decides whether a bound workspace is ready to deliver, with the recorded command
`concorde task-validation`: it checks the Spec structure, finds the Modules the workspace changed,
runs their configured checks, and returns a readiness — ready or not, with every blocking finding —
bound to the exact state of the workspace it examined. Whoever works the workspace, in Concorde the
task level in a task worktree, relies on it to see whether the work is deliverable; Delivery runs
the same steps itself right before it commits. Validation launches no worker, changes no file of
the workspace, and judges nothing a deterministic check cannot: whether code keeps its promises
beyond what the checks test, or whether a Spec explains enough, is for the reviews and the task
level.

## Terminology

| Term | Definition |
| --- | --- |
| Readiness | The outcome of Validation's readiness steps in one `task-validation` or `delivery` run: whether the workspace may be delivered, with its blocking findings, the checks run and the pending entries to confirm, bound to a digest of the exact inputs examined. |
| [Module](../../vocabulary.md#concept.concorde.module) | |
| [Evidence](../../vocabulary.md#concept.concorde.evidence) | |
| [Error chain](../../vocabulary.md#concept.concorde.error-chain) | |
| [Workspace](../module.md#concept.execution.workspace) | |
| [Workspace binding](../module.md#concept.execution.workspace-binding) | |
| [Recorded command](../module.md#concept.execution.recorded-command) | |
| [Run result](../module.md#concept.execution.run-result) | |
| [Workspace lock](../module.md#concept.execution.workspace-lock) | |
| [Structural check](../../spec-tooling/spec/module.md#concept.spec.structural-check) | |
| [Impact index](../../spec-tooling/spec/module.md#concept.spec.impact-index) | |
| [File transaction](../../spec-tooling/spec/module.md#concept.spec.file-transaction) | |
| [Configured check](../tools/checks/module.md#concept.checks.configured-check) | |
| [Check result](../tools/checks/module.md#concept.checks.check-result) | |

## Usage

The task level runs the command in the task worktree when it wants to know whether the workspace's
work is complete, usually after `implement`, `test` and the reviews. `delivery` decides the same
readiness again itself, so a `task-validation` run is a preview, not a precondition:

```text
concorde task-validation [--modules <id>[,<id>…]] [--detach]
```

It is a [recorded command](../module.md#concept.execution.recorded-command): the
[Execution runner](../runner.md) runs it like any Operation, in the workspace whose
[binding](../module.md#concept.execution.workspace-binding) lies in the worktree it starts in, and
records it in the run store, so that Delivery and a workflow can find it. In a worktree without a
binding it is refused with `binding_required`, since readiness concerns a workspace's changes from
its base commit. The command takes no arguments of its own. Its Modules (`--modules`, the
binding's by default) never narrow what is validated — readiness concerns the whole workspace — but
add their checks to the changed Modules'. It returns a [run result](../module.md#concept.execution.run-result)
of kind `command`, with no worker, whose `output` is the readiness
([contract](contracts.md#contract.validation.readiness)), one per run, which it also saves as
`readiness.json` in its run directory.

<a id="concept.validation.readiness"></a>

A **readiness** is `ready` when the Specs have no structural error, every changed path is
accounted for, and every check run passed; otherwise it lists every blocking finding the run
established, not only the first, each of one kind:

| Kind | Blocking when |
| --- | --- |
| `load` | the Specs fail to load at all |
| `structural` | a [structural check](../../spec-tooling/spec/module.md#concept.spec.structural-check) error, e.g. a broken link or stale registry mirror, or a run Module the workspace's registry no longer registers |
| `unbound` | a changed path is not a Spec document, control record, generated/build output, external material (including a submodule a Module includes), or Module-bound |
| `check` | a changed or run Module's [configured check](../tools/checks/module.md#concept.checks.configured-check) failed, timed out or couldn't run |

Warnings, such as missing scenario coverage, are reported but never block. A pending entry whose
file now exists is not an error but a **confirmation**, cleared by Delivery on commit. Changed
Modules bind a changed file or own a changed Spec document, found through the
[impact indexes](../../spec-tooling/spec/module.md#concept.spec.impact-index); a shared file runs
all its Modules' checks.

The readiness records its inputs — head, base, every changed path's digest and the configuration
digest — as one input digest, which proves exactly which inputs a readiness describes; a later
change of the workspace alters it.

| Status | Code | Reason | Detail |
| --- | --- | --- | --- |
| `ok` | — | — | the workspace is ready |
| `blocked` | `not_deliverable` | `decision` | one cause per finding: `check` (exit code, log tail) or `component` (rule, location, message) |
| `failed` | `wrong_branch` | `permission` | the workspace's head is not on the branch its binding names |
| `failed` | `measurement_failed` | `environment` | Git's or the configuration's error as cause |
| `failed` | `checks_unavailable` | `environment` | Check execution's error as cause |
| `failed` | `inputs_changed` | `environment` | the workspace changed mid-run |

The error is the run's own link of level `command`, with the actor `Command task-validation
<run-id> (workspace <workspace>)`. A blocked summary starts `Not deliverable:` with the finding
count; each finding is named by kind, location and message, as host evidence and as the
[error chain](../../vocabulary.md#concept.concorde.error-chain)'s causes — so whoever reads the
result sees everything blocking delivery from the result alone. The readiness is always the output;
the usual fix is another `implement`, a `specify`, or regenerating a stale registry mirror. Each
`failed` code carries a host evidence entry with the same code. Running `task-validation` again on
an unchanged workspace gives the same readiness with fresh check results.

## Design

Readiness is decided by deterministic code alone, so Delivery can run the same steps and trust
their outcome without asking — a model's opinion of completeness is not enough. That is also why it
is a recorded command and not an Operation: it involves no model, yet delivery must cite the run
that decided a readiness, a workflow must be able to take it as a step, and its caller must receive
its evidence and error chain like any run's. Binding the readiness to an input digest, remeasured
at the end, proves the inputs did not change while the checks ran, rather than trusting a
timestamp.

The measurement covers everything Delivery will commit: tracked changes since the binding's base
commit and untracked files Git does not ignore. An untracked path Git cannot version, such as the
`/dev/null` mounts with which Claude Code's Bash sandbox hides `.bashrc` or
`.claude/settings.json` from a task session, is left out, so the readiness and delivery come out
the same inside and outside that sandbox. Checks run for the changed Modules and for every Module
that uses one of them, directly or through further uses, since their code runs against the change
(the Protocol's impact of a written file); the rest of the project is not checked, which would be
too slow. A full test suite is therefore best checked by the Module that uses everything, such as
the tests' Module, so that it runs whichever Module changes. Structural validation always covers
the whole workspace, since a Spec change can break a link anywhere.

| # | Step | Actor | Stops when |
| --- | --- | --- | --- |
| 1 | Require the workspace's head to be on the branch its binding names | host | wrong or detached branch (`failed`) |
| 2 | Measure inputs: head, base, changed paths' digests, config digest, combined | host, read-only Git | Git can't report the changes (`failed`) |
| 3 | Validate the workspace's Spec structure | Spec core | — |
| 4 | Sort findings: errors block, filled pending entries become confirmations, warnings kept | host | — |
| 5 | Require every changed path be a Spec document, control record or Module-bound | host, Spec core | — |
| 6 | Derive the changed Modules via the impact indexes | Spec core | — |
| 7 | Run the changed and run Modules' configured checks | Check execution | check boundary unavailable (`failed`) |
| 8 | Remeasure inputs, compare the digest | host | digest changed (`failed`, `inputs_changed`) |
| 9 | Save the readiness and return it | host | — |

Steps 3–7 collect every blocking finding rather than stopping at the first: step 3 reads the Specs
as they will look once confirmed, so a filled pending entry is no error, and an unbound path is
reported once, at step 5. When the Specs fail to load, steps 5–7 are skipped and the load failure
itself blocks, naming the file and the loader's error. A run Module the loaded registry does not
register is a structural blocking finding. Unlike an Operation, the command diagnoses the Specs
itself, so the runner does not load them before the steps and these diagnoses always reach the
caller as findings rather than as a refusal. Step 8 catches changes of the workspace during a
check, which can take minutes.

A `task-validation` run writes nothing in the workspace; its logs and readiness go to its run
directory in the run store. Delivery reuses the readiness steps and a confirmation service that
clears exactly the listed pending markers in one
[file transaction](../../spec-tooling/spec/module.md#concept.spec.file-transaction), bound to the
measured metadata digests, then revalidates and rolls back on any remaining error. See the
[requirements](requirements.md) and [scenarios](scenarios.md).

<a id="realization.validation.command"></a>

The **Task validation command** realization holds the steps, the input measurement, the
confirmation service Delivery calls, and their tests, with the bound-workspace fixture Delivery's
tests share.

### Outside

- <a id="uses-execution"></a>**Execution**'s runner runs the command: it reads the workspace
  binding, which gives the steps the workspace's name, branch, base commit and Modules, holds the
  [workspace lock](../module.md#concept.execution.workspace-lock) for the whole run, so no other
  run changes the workspace during validation, wraps the readiness in the
  [run result](../module.md#concept.execution.run-result) and records it in the run store.
  Validation relies on the runner refusing a run without a sound binding before any step and on it
  leaving the Specs to the command's own diagnosis; it never reads a task record.
- <a id="uses-spec"></a>**Spec core** validates the Specs, answers through its impact indexes which
  Modules bind a path or own a document, and applies confirmations as a file transaction.
  Validation relies on the validator being deterministic and on loading refusing, not partially
  reading, a Spec that cannot support a boundary; it always roots Spec core at the workspace.
- <a id="uses-checks"></a>**Check execution** runs each changed Module's
  [configured checks](../tools/checks/module.md#concept.checks.configured-check) read-only,
  with the workspace as the project, and returns one
  [check result](../tools/checks/module.md#concept.checks.check-result) per check, copied into
  the readiness unchanged; a boundary it cannot establish fails the run.
