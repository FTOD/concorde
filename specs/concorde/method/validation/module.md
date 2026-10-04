# Validation

## Purpose

Validation decides whether a bound workspace is ready to deliver, with the execution command
`concorde task-validation`. It does the following:

- Checks the [Spec](../../glossary.json#concept.spec) structure.
- Finds the Modules the workspace changed.
- Runs their configured checks.
- Returns a readiness bound to the exact state of the workspace it examined.

The readiness says ready or not, with every blocking finding. Whoever works the workspace relies
on it to see whether the work is deliverable. In Concorde, this is the task level in a task
worktree. Delivery runs the same steps itself right before it commits. Validation launches no
worker. It changes no file of the workspace. It judges nothing a deterministic check cannot.
The reviews and the task level judge the following:

- Whether code keeps its promises beyond what the checks test.
- Whether a Spec explains enough.

## Core concepts

Validation rests on one idea, a readiness: a deterministic verdict on the whole workspace, bound to
the exact inputs it examined. It builds on the [configured checks](../../glossary.json#concept.configured-check)
of Check execution and the [structural checks](../../glossary.json#concept.structural-check) of
Spec core.

### Readiness

<a id="concept.readiness"></a>

A **readiness** is `ready` when all of these conditions hold:

- The Specs have no structural error.
- Every changed path is accounted for.
- Every check run passed.

Otherwise it lists every blocking finding the run established, not only the first. Each finding
has one kind:

| Kind | Blocking when |
| --- | --- |
| `load` | the Specs fail to load at all |
| `structural` | a [structural check](../../glossary.json#concept.structural-check) error, e.g. a broken link or stale registry mirror, or one of the run's [Modules](../../glossary.json#concept.module) that the workspace's registry no longer registers |
| `unbound` | a changed path is not a Spec document, the glossary, control record, generated/build output, external material (including a submodule a Module includes), or Module-bound |
| `check` | a [configured check](../../glossary.json#concept.configured-check) of a Module whose checks run failed or timed out, or Check execution could not run a Module's checks (see step 6) |

Warnings, such as missing scenario coverage, are reported but never block. Changed
Modules bind a changed file or own a changed Spec document. They are found through the
[impact indexes](../../glossary.json#concept.impact-index). A shared file runs
all its Modules' checks.

The readiness records its inputs as one input digest:

- The head.
- The base.
- Every changed path's Git file mode and digest.
- The configuration digest.

The input digest proves exactly which inputs a readiness describes. A later change of the
workspace alters it.

## Overview

### Deciding a readiness

A run decides a readiness in eight steps. Steps 1, 2, 6 and 7 can fail the run. In that case,
the run decides no readiness. Steps 3 to 6 collect every blocking finding rather than stopping at
the first. Step 8 saves what they found:

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
measure -> failed: "Git, a changed path or the\nconfiguration cannot be read" {style.stroke-dash: 3}
checks -> failed: "boundary unavailable,\nor a check input changed" {style.stroke-dash: 3}
remeasure -> failed: "digest changed" {style.stroke-dash: 3}
```

[The steps](#the-steps) gives each step's actor and stopping rule.

## Running task-validation

When the task level wants to know whether the workspace's work is complete, it runs the command
in the task worktree. It usually does this after `implement`, `test` and the reviews. `delivery`
decides the same readiness again itself. A `task-validation` run is therefore a preview, not a
precondition:

```text
concorde task-validation [--modules <id>[,<id>…]] [--input <run-id>]… [--detach]
```

It is an [execution command](../../glossary.json#concept.execution-command). The
[Execution runner](../../execution/runner.md) runs it like any
[Operation](../../glossary.json#concept.operation). It runs in the workspace whose
[binding](../../glossary.json#concept.workspace-binding) lies in the worktree it starts in.
The runner records it in the [run store](../../glossary.json#concept.run-store), so that a workflow
can find it. Without a binding in the worktree, the runner refuses the command with
`binding_required`, since readiness concerns a workspace's changes from its base commit. The
command takes no arguments of its own.
It accepts the runner's `--input` like any run, but no step reads an admitted input.
The **run's Modules** (`--modules`, the binding's by default) never narrow what is validated.
Readiness concerns the whole workspace. The run's Modules add their checks to the changed Modules'.
The checks of every Module that uses one of these, directly or through further uses, run too.
A change can therefore bring check results from Modules the workspace did not touch.
When a run decides a readiness, it returns a
[run result](../../glossary.json#concept.run-result) of kind `command`, with no worker.
Its `output` is the readiness ([contract](contracts.md#contract.validation.readiness)), one per run.
The run also saves it as `readiness.json` in its
[trace node](../../glossary.json#concept.trace-node).

### The result

| Status | Code | Reason | Detail |
| --- | --- | --- | --- |
| `ok` | — | — | the workspace is ready |
| `blocked` | `not_deliverable` | `decision` | one cause per finding: `check` (exit code, log tail) or `component` (rule, location, message) |
| `failed` | `wrong_branch` | `permission` | the workspace's head is not on the branch its binding names |
| `failed` | `measurement_failed` | `environment` | the measurement's error as cause: `git_failed` (Git cannot report the changes), `path_unreadable` (a changed path cannot be read) or `config_unreadable` (the configuration or a checks file cannot be read) |
| `failed` | `checks_unavailable` | `environment` | Check execution's error as cause |
| `failed` | `inputs_changed` | `environment` | the workspace changed mid-run; Check execution's `stale_evidence` as cause when a check noticed it |

The error is the run's own link of level `command`, with the actor
`Command task-validation <run-id> (workspace <workspace>)`. A blocked summary starts
`Not deliverable:` with the finding count. In both host evidence and the
[error chain](../../glossary.json#concept.error-chain)'s causes, each finding is named by kind,
location and message. Whoever reads the result therefore sees everything blocking delivery from
the result alone. Host evidence contains these entries:

- Each finding is an entry of kind `blocking` with its location as `ref` and its message as `detail`.
- Each check that ran is an entry of kind `check`.
- The structural validation and the decided readiness are summarized in entries of kind `readiness`.

An `ok` or `blocked` run always carries its readiness as the output. The usual fix of a blocked
run is one of these:

- Another `implement`.
- A `specify`.
- Regenerating a stale registry mirror.

A `failed` run and a refused one decide no readiness. Their `output` is null. They save no
`readiness.json`. Each `failed` run carries host evidence of its cause:

- For `wrong_branch` and `measurement_failed`, the kind is `git`.
- For `checks_unavailable`, the kind is `checks_unavailable`.
- For `inputs_changed`, the kind is `readiness`.

On an unchanged workspace, running `task-validation` again measures the same inputs. It reaches
the same structural and unbound findings and the same Modules. Its fresh check results, and with
them the readiness decision, can differ only when a configured check depends on something outside
the workspace.

## How it is built

Deterministic code alone decides readiness. Delivery can therefore run the same steps and trust
their outcome without asking. A model's opinion of completeness is not enough. That is also why
`task-validation` is an execution command and not an Operation. It involves no model, yet a workflow
must be able to take it as a step. Its caller must receive its evidence and error chain like any
run's. At the end, Validation remeasures the input digest to which the readiness is bound. This
proves that the measured inputs at the end of the run are those recorded at the start. It does not
trust a timestamp. In addition, Check execution refuses a check whose own inputs changed while it
ran. Changes the measurement leaves out, below, are not seen.

### What is measured and checked

The measurement covers everything Delivery will commit: tracked changes since the binding's base
commit and untracked files Git does not ignore. The measurement leaves out an untracked path Git
cannot version. Examples are the `/dev/null` mounts with which Claude Code's Bash sandbox hides
`.bashrc` or `.claude/settings.json`. It hides them from a sandboxed Claude Code session working
in the worktree. Such a session can be a [main agent](../../glossary.json#concept.main-agent) whose own session is
sandboxed. A [task session](../../glossary.json#concept.task-session) runs under no sandbox. The
measurement also leaves out the empty read-only placeholder file the sandbox creates on the host
at each such path. The sandbox keeps that file while any of the session's sandboxed commands still
runs. Readiness and delivery therefore come out the same inside and outside that sandbox.

A placeholder is recognised by the signature the sandbox runtime itself uses for its leftovers:

- It is empty.
- It is regular.
- It has no write bit.
- It has one link.

Recognition does not use a mount point in `/proc/self/mountinfo`. That mount point exists only
inside the sandbox that mounted it. A validation run on the host, or in another sandbox, must
leave the placeholder out as well.

Checks run for the changed Modules and for every Module that uses one of them, directly or through
further uses. Their code runs against the change (the Protocol's impact of a written file). The
rest of the project is not checked, which would be too slow. A full test suite is therefore best
checked by the Module that uses everything, such as the tests' Module. It then runs whichever
Module changes. Since a [Spec change](../../glossary.json#concept.spec-change) can break a link
anywhere, structural validation always covers the whole workspace.

### The steps

| # | Step | Actor | Stops when |
| --- | --- | --- | --- |
| 1 | Require the workspace's head to be on the branch its binding names | host | wrong or detached branch (`failed`) |
| 2 | Measure inputs: head, base, changed paths' modes and digests, config digest, combined | host, read-only Git | Git can't report the changes, or a changed path or the configuration can't be read (`failed`) |
| 3 | Validate the workspace's Spec structure: errors block, warnings are kept | Spec core | — (Specs that fail to load skip steps 4–6) |
| 4 | Require every changed path be accounted for, as the `unbound` kind lists | host, Spec core | — |
| 5 | Derive the changed Modules via the impact indexes | Spec core | — |
| 6 | Judge every checks file and declared input of the project, then run the configured checks of the changed Modules, the run's Modules and every Module using one of them | Check execution | check boundary unavailable (`failed`, `checks_unavailable`); a check input changed (`failed`, `inputs_changed`) |
| 7 | Remeasure inputs, compare the digest | host | digest changed (`failed`, `inputs_changed`) |
| 8 | Save the readiness and return it | host | — |

Steps 3–6 collect every blocking finding rather than stopping at the first. An unbound path is
reported once, at step 4. When the Specs fail to load, steps 4–6 are skipped. The load failure itself
blocks, naming the file and the loader's error. One of the run's Modules that the loaded registry
does not register is a structural blocking finding.

At step 6, Check execution's `check_sandbox_unavailable` fails the run with `checks_unavailable`.
Its `stale_evidence` fails the run with `inputs_changed`. Any other error it raises for a Module's
checks is a blocking `check` finding naming the Modules whose checks could not run. Examples are:

- A missing check input.
- An invalid check.
- An operating-system error, which Check execution's link names `system_error`.

The other Modules' checks still run. Each Module's own checks are run apart, reading only that
Module's checks file. Each of these keeps Check execution's own error link as its cause. The
checks such a failed call finished before the error keep their results. Since the call itself
returns none, Validation reads those results back from the checks' trace nodes.

Structural validation does not read checks files, which belong to Check execution. Step 6 is
therefore also where these problems with a checks file are found:

- Its input is missing.
- Its input escapes the worktree.
- Its check is malformed.

Before any check runs, Check execution's `validate_checks` judges every checks file and every
declared input of the project. Such a problem therefore blocks as one `check` finding, even in a
Module whose checks the run does not run. When a Module's own checks raise the same problem again,
it is not reported twice. Unlike an Operation, the command diagnoses the Specs itself. The runner
therefore does not load them before the steps. These diagnoses always reach the caller as findings
rather than as a refusal. Step 7 catches changes of the workspace during a check, which can take
minutes.

A `task-validation` run writes nothing in the workspace. Its checks' nodes with their logs and its
readiness go to its trace node in the run store. That node is under the binding's workspace folder.
Its locks go under the binding's `locks/`. Those are the only places it writes, even when they lie
inside the worktree. Delivery reuses the readiness steps. See the
[requirements](requirements.md) and [scenarios](scenarios.md).

### The command

<a id="realization.validation.command"></a>

The **[Task](../../glossary.json#concept.task) validation command** realization holds the steps,
the input measurement and their tests, with the
bound-workspace fixture Delivery's tests share.

## What Validation relies on

- <a id="uses-execution"></a>**Execution**'s runner runs the command. It reads the workspace
  binding, which gives the steps these values:

  - The workspace's name.
  - The branch.
  - The base commit.
  - The Modules.

  It holds the [workspace lock](../../glossary.json#concept.workspace-lock) for the whole run, so
  no other run changes the workspace during validation. It wraps the readiness in the
  [run result](../../glossary.json#concept.run-result). It records it in the run store. Validation
  relies on the runner refusing a run without a sound binding before any step. It also relies on
  the runner leaving the Specs to the command's own diagnosis. Validation never reads a
  [task record](../../glossary.json#concept.task-record).
- <a id="uses-commands"></a>**Commands**, Execution's execution-command framework, is what
  `task-validation` plugs into. Method registers its definition there. This is how the runner finds
  this Module's definition by the command's name.
- <a id="uses-kernel"></a>The **Kernel** defines the
  [workspace binding](../../glossary.json#concept.workspace-binding)
  ([contract](../../kernel/contracts.md#contract.kernel.workspace-binding)). Through the run
  context, the steps read these values from it:

  - The branch.
  - The base commit.
  - The Modules.

  The Kernel also defines the [workspace lock](../../glossary.json#concept.workspace-lock) the
  runner holds for the run. When a binding breaks the contract, the runner refuses it before any
  step.
- <a id="uses-spec"></a>**Spec core** validates the Specs. Through its impact indexes, it answers
  which Modules bind a path or own a document. Validation relies on the validator being
  deterministic. It also relies on loading refusing, not partially reading, a Spec that cannot
  support a boundary. Validation always roots Spec core at the workspace.
- <a id="uses-checks"></a>**Check execution** runs the
  [configured checks](../../glossary.json#concept.configured-check) of the Modules step 6 selects
  read-only, with the workspace as the project. It returns one
  [check result](../../glossary.json#concept.check-result) per check. The readiness keeps these
  values from each result:

  - Its check identity as `check`.
  - Its Module.
  - Its status.
  - Its exit code.
  - Its measured digest as `measured_digest`.
  - Its log path relative to the run's trace node, `checks/<check>/output.log`.

  For a timeout, the exit code becomes null. The readiness drops each result's log digest. When Check execution
  cannot establish a boundary, the run fails. When a call fails after some of its checks ran,
  Validation relies on each check's trace node
  ([contract](../../execution/checks/service.md#contract.checks.check-trace)) for the result of
  every check that finished.
- <a id="uses-workflows"></a>**Workflows** defines the
  [step output convention](../../workflows/contracts.md#contract.workflows.step-output), the
  `workflow` object of a run's output. In that object, every task-validation run that decided a
  readiness declares its `ready` as `data.ready`. When the workspace is not ready, it also declares
  a `blocking` item naming the blocking findings
  ([req.validation.step-output](requirements.md#req.validation.step-output)). This lets a workflow
  stop there without reading the readiness. Validation builds that object with Workflows'
  `step_output` helper. The helper checks it against the convention. Validation knows no workflow.
  What makes a workspace ready is Validation's. The envelope and what a blocking item does to a
  workflow's report are Workflows'.
