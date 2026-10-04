# SWE-bench cases

## Purpose

SWE-bench cases test Concorde's whole change flow on real issues. The flow follows these steps:

- Prepare a case at its base commit.
- Adopt it.
- Repair its [Specs](../../glossary.json#concept.spec).
- Work its issue through Concorde as a [main agent](../../glossary.json#concept.main-agent) would.
- Grade the merged change with the case's own tests, the way SWE-bench grades it.

This [Module](../../glossary.json#concept.module) holds the case itself and the two steps that exist
only for cases:

- Repairing the adopted Specs in one bounded round.
- Grading a delivered change.

Preparing the project and running its workflows belong to [End-to-end testing](../module.md).
It serves the people developing Concorde only.

## Core concepts

**A case.** A case is one SWE-bench instance: one row of SWE-bench's dataset.
The row is saved as a JSON file.
The caller gives it to `grade` with `--instance`. It contains these values:

- `instance_id`.
- `base_commit`.
- `test_patch`, the case's own test changes.
- `FAIL_TO_PASS`, a list of pytest test identities that fail before the issue is resolved.
  These tests must pass after the issue is resolved.
- `PASS_TO_PASS`, a list of pytest test identities that must keep passing.

Each list may be a JSON list or a string holding one, as the dataset stores it.

**Working a case.** The developer follows these steps:

- Build the case's own Python environment outside the project, with its interpreter and pinned
  dependencies. Never install the project in it.
- Prepare the case's repository at its base commit under the case's name, with `--python` naming
  that interpreter. `concorde init` records that interpreter as the project's for its checks'
  `{python}`.
- Adopt it with the [brownfield workflow](../../glossary.json#concept.brownfield-workflow).
- Configure its checks.
- Repair the adopted Specs with `repair-specs`.
- Then work the issue through Concorde as a main agent would, from `understand` to the merge.

Finally `grade` grades the merged change.

## Overview

Working a case assigns each step as follows:

- [End-to-end testing](../module.md) prepares the project and runs its workflows.
- This Module repairs the adopted Specs.
- This Module grades the result.
- The issue itself is worked through Concorde as a main agent would.

Only `repair-specs` and `grade` belong to this Module.

```d2 illustrative
direction: right
developer: "Developer" {
  env: "Build the case's Python\nenvironment outside the project"
  checks: "Configure the\nproject's checks"
}
e2e: "End-to-end testing" {
  prepare: "prepare the repository\nat the base commit, --python"
  adopt: "run the brownfield\nworkflow: adoption"
}
cases: "SWE-bench cases" {
  repair: "repair-specs:\none bounded round"
  grade: "grade: the case's tests\nin a throwaway worktree"
  verdict: "resolved or not" {shape: oval}
}
concorde: "Concorde, as a main agent would" {
  work: "Work the issue:\nunderstand to the merge"
}
developer.env -> e2e.prepare -> e2e.adopt -> developer.checks -> cases.repair -> concorde.work -> cases.grade -> cases.verdict
```

## The commands

```text
python3 scripts/e2e/e2e.py repair-specs <project> [--modules <ids>] [--task repair-specs]
python3 scripts/e2e/e2e.py grade <project> --instance <case.json> --python <interpreter> [--ref main] [--pythonpath <dir>]…
```

### Repairing the adopted Specs

In a case the Specs are the test's own addition. They describe code the test never changes.
For this reason, the [review findings](../../glossary.json#concept.review-finding) adoption leaves
are repaired before the issue. `repair-specs` opens a task over the Modules `--modules` names.
By default, it selects every Module of the registry. Unless `--task` names another, the task is
named `repair-specs`. The command follows these steps
([requirements](requirements.md#req.swe-bench-cases.repair-specs-only)):

- Review the Modules.
- Run `specify` once with that review as input and an intent to change only what the Specs say.
  The run keeps every promise true to the code. It turns a repair that needs a decision about
  intent into an [open question](../../glossary.json#concept.open-question).
- Review the Modules once more.
- Run `task-validation`.
- Run `delivery`.
- Merge the task.

Every run starts in the task's worktree. It names no task. The
[Operations](../../glossary.json#concept.operation) start with `concorde run`. The
[execution commands](../../glossary.json#concept.execution-command) start as
`concorde task-validation` and `concorde delivery`. Each works on the worktree's [workspace
binding](../../glossary.json#concept.workspace-binding). One round bounds the repair.
What the second review still finds is reported. When a review's
[verdict](../../glossary.json#concept.review-verdict) is `accepted`, `task-validation` and
`delivery` follow with no repair. Whether its verdict is `accepted` or `changes_required`, a
review ends `ok`. Because the second review ends `ok`, its remaining findings do not stop the round.
When a step does not end `ok`, the repair stops with its result. It leaves the task open.
The command prints the following:

- The task.
- The Modules.
- Every step with these details:
  - Its run.
  - Its status.
  - Its summary.
  - The review's verdict, for a review.
  - The error, for a step that did not end `ok`.
- The step the repair stopped at, or none.

When a task of the same name already exists, the command fails with `task open`'s error.
The round, with its one branch and the exit every step shares:

```d2 illustrative
direction: down
open: "task open, in the project"
review: "spec_review"
accepted: "Verdict accepted?" {shape: diamond}
specify: "specify, with the review as input"
again: "spec_review again, findings reported"
validate: "task-validation"
delivery: "delivery"
merge: "task merge" {shape: oval}
stop: "Stopped at that step, the task left open" {shape: oval}
open -> review
review -> accepted
accepted -> validate: yes
accepted -> specify: no
specify -> again -> validate
validate -> delivery -> merge
review -> stop: "not ok" {style.stroke-dash: 3}
specify -> stop: "not ok" {style.stroke-dash: 3}
again -> stop: "not ok" {style.stroke-dash: 3}
validate -> stop: "not ok" {style.stroke-dash: 3}
delivery -> stop: "not ok" {style.stroke-dash: 3}
```

### Grading a case

`grade` decides whether the merged change resolves the issue the way SWE-bench does.
In a throwaway worktree of `--ref`, it follows these steps:

- Since the change may edit these test files, restore every file the case's test patch touches
  to the case's base-commit state.
- Apply the test patch.
- Run the test files it names with the given interpreter.
- Report how many of the FAIL_TO_PASS and PASS_TO_PASS tests passed.
- Report each one that did not.
- Report whether the case is resolved.

The test run puts `--pythonpath` directories of that worktree first on `PYTHONPATH`.
Since pytest's summary lines supply the statuses, whatever the caller's environment asks for,
colour is off. The test patch and the case's tests stay outside the project.
No worker sees them. The project is left as it was
([requirements](requirements.md#req.swe-bench-cases.graded-apart)). The pytest output is kept
under `.concorde/runs/e2e/`. When every FAIL_TO_PASS and every PASS_TO_PASS test passed, the case
is resolved. Failing tests are a verdict, not an error. For each listed test that did not pass,
grading names the test with its status. For a test pytest never reports, the status is `not run`.
Pytest's exit code is kept. In the following cases, grading stops with an error instead:

- When the instance lacks any of the following, the error is `invalid_case`:
  - FAIL_TO_PASS tests.
  - A test patch.
  - A base commit.
- When the worktree cannot be made or the test patch does not apply, the error is
  `command_failed`. It names the following:
  - The command.
  - Its exit status.
  - Its output.
- When the test run exceeds 30 minutes, the error is `grade_timeout`. It names the following:
  - The case.
  - The ref.
  - The limit.
  - The command.
  It includes the output the test run produced.

However grading ends, the throwaway worktree is removed
([requirements](requirements.md#req.swe-bench-cases.grading-worktree-removed)).

## Why it is built this way

Repairing a review's gaps automatically is otherwise a decision for a person.
Because a case's Specs are the test's own description of code the test never changes, this
exception holds for cases only.
That is why the exception lives here and not in the workflow users run.
That is also why it is bounded to one round that changes Specs and never code
([requirements](requirements.md#req.swe-bench-cases.specs-not-code)).
The `specify` [task type](../../glossary.json#concept.task-type), not the intent, keeps the code
unchanged. It may write the bound Modules' documents and none of their code.
When a specify run's [write
audit](../../glossary.json#concept.write-audit) finds a changed code file, the run ends `failed`.
This stops the repair before `delivery`.
No second round is started.
What the second review still finds is reported.
The task is merged, so a case never loops on a model's review.

Grading copies SWE-bench rather than inventing a verdict:

- It uses the same test patch.
- It uses the same two test lists.
- It resets the files the patch touches to the base commit first.

Grading uses a throwaway worktree to keep the case's tests from ever reaching the project,
where a worker could see them.
It leaves the project exactly as the merge left it.

## Files

<a id="realization.swe-bench-cases.steps"></a>

The **case steps** are `scripts/e2e/cases.py`:

- `repair_specs` runs the Operations and execution commands of the repair round through the
  `concorde` command in the task's worktree.
- `grade` has its helpers.

The `repair-specs` and `grade` commands of `scripts/e2e/e2e.py` call it.

<a id="realization.swe-bench-cases.tests"></a>

The **case step tests**, `tests/concorde/e2e/test_cases.py`, do the following:

- Clone a case at its base commit.
- Grade a toy case before and after its fix.
- Drive the repair round with stand-in runs.

These tests verify the [requirements](requirements.md) and [scenarios](scenarios.md).

## Around it

<a id="uses-distribution"></a>

**Distribution** provides the project's `concorde` command.
Through that command, the repair round does the following:

- Opens its task.
- Runs its Operations and execution commands in the task's worktree.
- Merges the task.

The case steps never write the following themselves:

- The project's Specs.
- The project's [task records](../../glossary.json#concept.task-record).
- The project's [workspace binding](../../glossary.json#concept.workspace-binding).

<a id="uses-specification"></a>

**Specification** provides the `specify` Operation.
When a run changes code, its [write audit](../../glossary.json#concept.write-audit) fails it
([requirement](../../method/specification/requirements.md#req.specification.audit)).
This keeps the repair from changing code.

<a id="uses-spec-review"></a>

**Spec review** provides the `spec_review` Operation.
The round reads its [verdict](../../glossary.json#concept.review-verdict) to decide whether to repair.
The run ends `ok` for `accepted` and `changes_required` alike.

SWE-bench is external material, included by [End-to-end testing](../module.md).
Its instances supply the following for grading a case:

- The base commit.
- The test patch.
- The test lists.
