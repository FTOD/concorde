# Validation

## Purpose

Validation decides whether a bound workspace is ready to deliver, with the execution command
`concorde task-validation`: it checks the [Spec](../../glossary.json#concept.spec) structure,
finds the Modules the workspace changed, runs their configured checks, and returns a readiness —
ready or not, with every blocking finding — bound to the exact state of the workspace it examined.
Whoever works the workspace, in Concorde the task level in a task worktree, relies on it to see
whether the work is deliverable; Delivery runs the same steps itself right before it commits.
Validation launches no worker, changes no file of the workspace, and judges nothing a deterministic
check cannot: whether code keeps its promises beyond what the checks test, or whether a Spec
explains enough, is for the reviews and the task level.

## Core concepts

Validation rests on one idea, a readiness: a deterministic verdict on the whole workspace, bound to
the exact inputs it examined. It builds on the [configured checks](../../glossary.json#concept.configured-check)
of Check execution and the [structural checks](../../glossary.json#concept.structural-check) of
Spec core.

### Readiness

<a id="concept.readiness"></a>

A **readiness** is `ready` when the Specs have no structural error, every changed path is
accounted for, and every check run passed; otherwise it lists every blocking finding the run
established, not only the first, each of one kind:

| Kind | Blocking when |
| --- | --- |
| `load` | the Specs fail to load at all |
| `structural` | a [structural check](../../glossary.json#concept.structural-check) error, e.g. a broken link or stale registry mirror, or one of the run's [Modules](../../glossary.json#concept.module) that the workspace's registry no longer registers |
| `unbound` | a changed path is not a Spec document, the glossary, control record, generated/build output, external material (including a submodule a Module includes), or Module-bound |
| `check` | a [configured check](../../glossary.json#concept.configured-check) of a Module whose checks run failed or timed out, or Check execution could not run a Module's checks (see step 6) |

Warnings, such as missing scenario coverage, are reported but never block. Changed
Modules bind a changed file or own a changed Spec document, found through the
[impact indexes](../../glossary.json#concept.impact-index); a shared file runs
all its Modules' checks.

The readiness records its inputs — head, base, every changed path's Git file mode and digest and
the configuration digest — as one input digest, which proves exactly which inputs a readiness describes; a later
change of the workspace alters it.

## Overview

### Deciding a readiness

A run decides a readiness in eight steps. Steps 1, 2, 6 and 7 can fail the run, which then decides
no readiness; steps 3 to 6 collect every blocking finding rather than stopping at the first, and
step 8 saves what they found:

```d2 illustrative
direction: down
branch: "1. Head on the bound branch?"
measure: "2. Measure the inputs"
structure: "3. Validate the Spec structure"
paths: "4. Every changed path\naccounted for?"
modules: "5. Derive the changed Modules"
checks: "6. Run the configured checks"
remeasure: "7. Remeasure the inputs"
save: "8. Save the readiness"
ok: "ok: ready"
blocked: "blocked: not_deliverable,\none cause per finding"
failed: "failed: no readiness\n(wrong_branch, measurement_failed,\nchecks_unavailable, inputs_changed)"
branch -> measure: yes
measure -> structure -> paths -> modules -> checks -> remeasure
structure -> remeasure: "Specs fail to load:\nskip 4 to 6" {style.stroke-dash: 3}
remeasure -> save: "digest unchanged"
save -> ok: "no blocking finding"
save -> blocked: "blocking findings"
branch -> failed: no {style.stroke-dash: 3}
measure -> failed: "Git cannot report\nthe changes" {style.stroke-dash: 3}
checks -> failed: "boundary unavailable,\nor a check input changed" {style.stroke-dash: 3}
remeasure -> failed: "digest changed" {style.stroke-dash: 3}
```

[The steps](#the-steps) gives each step's actor and stopping rule.

## Running task-validation

The task level runs the command in the task worktree when it wants to know whether the workspace's
work is complete, usually after `implement`, `test` and the reviews. `delivery` decides the same
readiness again itself, so a `task-validation` run is a preview, not a precondition:

```text
concorde task-validation [--modules <id>[,<id>…]] [--input <run-id>]… [--detach]
```

It is an [execution command](../../glossary.json#concept.execution-command): the
[Execution runner](../../execution/runner.md) runs it like any
[Operation](../../glossary.json#concept.operation), in the workspace whose
[binding](../../glossary.json#concept.workspace-binding) lies in the worktree it starts in, and
records it in the [run store](../../glossary.json#concept.run-store), so that a workflow can
find it. In a worktree without a binding it is refused with `binding_required`, since readiness
concerns a workspace's changes from its base commit. The command takes no arguments of its own; it
accepts the runner's `--input` like any run, but no step reads an admitted input. The
**run's Modules** (`--modules`, the binding's by default) never narrow what is validated — readiness
concerns the whole workspace — but add their checks to the changed Modules'. The checks of every
Module that uses one of these, directly or through further uses, run too, so a change can bring
check results from Modules the workspace did not touch. A run that decides a readiness returns a
[run result](../../glossary.json#concept.run-result) of kind `command`, with no worker, whose
`output` is the readiness ([contract](contracts.md#contract.validation.readiness)), one per run,
which it also saves as `readiness.json` in its
[trace node](../../glossary.json#concept.trace-node).

### The result

| Status | Code | Reason | Detail |
| --- | --- | --- | --- |
| `ok` | — | — | the workspace is ready |
| `blocked` | `not_deliverable` | `decision` | one cause per finding: `check` (exit code, log tail) or `component` (rule, location, message) |
| `failed` | `wrong_branch` | `permission` | the workspace's head is not on the branch its binding names |
| `failed` | `measurement_failed` | `environment` | Git's or the configuration's error as cause |
| `failed` | `checks_unavailable` | `environment` | Check execution's error as cause |
| `failed` | `inputs_changed` | `environment` | the workspace changed mid-run; Check execution's `stale_evidence` as cause when a check noticed it |

The error is the run's own link of level `command`, with the actor
`Command task-validation <run-id> (workspace <workspace>)`. A blocked summary starts
`Not deliverable:` with the finding count; each finding is named by kind, location and message, as
host evidence and as the [error chain](../../glossary.json#concept.error-chain)'s causes — so
whoever reads the result sees everything blocking delivery from the result alone. As host evidence,
each finding is an entry of kind `blocking` with its location as `ref` and its message as `detail`,
each check that ran is an entry of kind `check`, and the structural validation and the decided
readiness are summarized in entries of kind `readiness`. An `ok` or `blocked` run always carries its
readiness as the output; the usual fix of a blocked one is another `implement`, a `specify`, or
regenerating a stale registry mirror. A `failed` run and a refused one decide no readiness: their
`output` is null and they save no `readiness.json`. Each `failed` run carries host evidence of its
cause: kind `git` for `wrong_branch` and `measurement_failed`, `checks_unavailable` for
`checks_unavailable` and `readiness` for `inputs_changed`. Running `task-validation` again on an
unchanged workspace measures the same inputs and reaches the same structural and unbound findings
and the same Modules; only its fresh check results, and with them the readiness decision, can
differ, when a configured check depends on something outside the workspace.

## How it is built

Readiness is decided by deterministic code alone, so Delivery can run the same steps and trust their
outcome without asking — a model's opinion of completeness is not enough. That is also why it is an
execution command and not an Operation: it involves no model, yet a workflow must be able to take
it as a step, and its caller must receive its evidence and error chain like any run's. Binding the
readiness to an input digest, remeasured at the end, proves that the measured inputs at the end of
the run are those it recorded at the start, rather than trusting a timestamp; Check execution in
addition refuses a check whose own inputs changed while it ran. Changes the measurement leaves out,
below, are not seen.

### What is measured and checked

The measurement covers everything Delivery will commit: tracked changes since the binding's base
commit and untracked files Git does not ignore. An untracked path Git cannot version, such as the
`/dev/null` mounts with which Claude Code's Bash sandbox hides `.bashrc` or `.claude/settings.json`
from a sandboxed Claude Code session working in the worktree, such as a
[main agent](../../glossary.json#concept.main-agent) whose own session is sandboxed (a
[task session](../../glossary.json#concept.task-session) runs under no sandbox), is left out, and so is the
empty read-only placeholder file the sandbox creates on the host at each such path and keeps while
any of the session's sandboxed commands still runs, so the readiness and delivery come out the same
inside and outside that sandbox. A placeholder is recognised by the signature the sandbox runtime
itself uses for its leftovers (empty, regular, no write bit, one link) rather than by a mount point
in `/proc/self/mountinfo`, which exists only inside the sandbox that mounted it: a validation run
on the host, or in another sandbox, must leave the placeholder out as well. Checks run for the changed Modules
and for every Module that uses one of them, directly or through further uses, since their code runs
against the change (the Protocol's impact of a written file); the rest of the project is not
checked, which would be too slow. A full test suite is therefore best checked by the Module that
uses everything, such as the tests' Module, so that it runs whichever Module changes. Structural
validation always covers the whole workspace, since a
[Spec change](../../glossary.json#concept.spec-change) can break a link anywhere.

### The steps

| # | Step | Actor | Stops when |
| --- | --- | --- | --- |
| 1 | Require the workspace's head to be on the branch its binding names | host | wrong or detached branch (`failed`) |
| 2 | Measure inputs: head, base, changed paths' modes and digests, config digest, combined | host, read-only Git | Git can't report the changes (`failed`) |
| 3 | Validate the workspace's Spec structure: errors block, warnings are kept | Spec core | — (Specs that fail to load skip steps 4–6) |
| 4 | Require every changed path be accounted for, as the `unbound` kind lists | host, Spec core | — |
| 5 | Derive the changed Modules via the impact indexes | Spec core | — |
| 6 | Run the configured checks of the changed Modules, the run's Modules and every Module using one of them | Check execution | check boundary unavailable (`failed`, `checks_unavailable`); a check input changed (`failed`, `inputs_changed`) |
| 7 | Remeasure inputs, compare the digest | host | digest changed (`failed`, `inputs_changed`) |
| 8 | Save the readiness and return it | host | — |

Steps 3–6 collect every blocking finding rather than stopping at the first; an unbound path is
reported once, at step 4. When the Specs fail to load, steps 4–6 are skipped and the load failure
itself blocks, naming the file and the loader's error. One of the run's Modules that the loaded
registry does not register is a structural blocking finding. At step 6, Check execution's
`check_sandbox_unavailable` fails the run with `checks_unavailable`, and its `stale_evidence` with
`inputs_changed`; any other error it raises for a Module's checks, such as a missing check input or
an invalid check, is a blocking `check` finding naming the Modules whose checks could not run, and
the other Modules' checks still run. Each of these keeps Check execution's own error link as its
cause. Since structural validation does not read checks files, which belong to Check execution,
step 6 is also where a checks file whose input is missing or whose check is malformed is found:
Check execution validates the checks files of the Modules it is asked to run before it runs them. Unlike an Operation, the command diagnoses the Specs itself, so
the runner does not load them before the steps and these diagnoses always reach the caller as
findings rather than as a refusal. Step 7 catches changes of the workspace during a check, which can
take minutes.

A `task-validation` run writes nothing in the workspace; its checks' nodes with their logs and its
readiness go to its trace node in the run store, under the binding's workspace folder, and its locks
under the binding's `locks/`; those are the only places it writes, even when they lie inside the
worktree. Delivery reuses the readiness steps. See the
[requirements](requirements.md) and [scenarios](scenarios.md).

### The command

<a id="realization.validation.command"></a>

The **[Task](../../glossary.json#concept.task) validation command** realization holds the steps,
the input measurement and their tests, with the
bound-workspace fixture Delivery's tests share.

## What Validation relies on

- <a id="uses-execution"></a>**Execution**'s runner runs the command: it reads the workspace
  binding, which gives the steps the workspace's name, branch, base commit and Modules, holds the
  [workspace lock](../../glossary.json#concept.workspace-lock) for the whole run, so no other run
  changes the workspace during validation, wraps the readiness in the
  [run result](../../glossary.json#concept.run-result) and records it in the run store.
  Validation relies on the runner refusing a run without a sound binding before any step and on it
  leaving the Specs to the command's own diagnosis; it never reads a
  [task record](../../glossary.json#concept.task-record).
- <a id="uses-commands"></a>**Commands**, Execution's execution-command framework, is what
  `task-validation` plugs into: Method registers its definition there, which is how the runner finds
  this Module's definition by the command's name.
- <a id="uses-kernel"></a>The **Kernel** defines the
  [workspace binding](../../glossary.json#concept.workspace-binding) whose branch, base commit and
  Modules the steps read through the run context
  ([contract](../../kernel/contracts.md#contract.kernel.workspace-binding)), and the
  [workspace lock](../../glossary.json#concept.workspace-lock) the runner holds for the run; a
  binding that breaks the contract is refused before any step.
- <a id="uses-spec"></a>**Spec core** validates the Specs, answers through its impact indexes which
  Modules bind a path or own a document.
  Validation relies on the validator being deterministic and on loading refusing, not partially
  reading, a Spec that cannot support a boundary; it always roots Spec core at the workspace.
- <a id="uses-checks"></a>**Check execution** runs the
  [configured checks](../../glossary.json#concept.configured-check) of the Modules step 6 selects
  read-only, with the workspace as the project, and returns one
  [check result](../../glossary.json#concept.check-result) per check. The readiness keeps
  each result's check identity as `check`, its Module, status and exit code, its measured
  digest as `measured_digest` and its log path relative to the run's trace node,
  `checks/<check>/output.log`; a timeout's exit code becomes null and the log digest is dropped. A boundary
  it cannot establish fails the run.
