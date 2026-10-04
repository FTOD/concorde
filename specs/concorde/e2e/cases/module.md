# SWE-bench cases

## Purpose

SWE-bench cases test Concorde's whole change flow on real issues: a case is prepared at its base
commit, adopted, its [Specs](../../glossary.json#concept.spec) repaired, its issue worked through Concorde as a
[main agent](../../glossary.json#concept.main-agent) would, and the merged change graded with the
case's own tests, the way SWE-bench grades it. This [Module](../../glossary.json#concept.module) holds the
two steps that exist only for cases, repairing the adopted Specs in one bounded round and grading a
delivered change, and the case itself. Preparing the project and running its workflows belong to
[End-to-end testing](../module.md). It serves the people developing Concorde only.

## Core concepts

**A case.** A case is one SWE-bench instance, one row of SWE-bench's dataset saved as a JSON file
and given to `grade` with `--instance`: its `instance_id`, its `base_commit`, its `test_patch`, the
case's own test changes, and two lists of pytest test identities: `FAIL_TO_PASS`, the tests that
fail before the issue is resolved and must pass after it, and `PASS_TO_PASS`, the tests that must
keep passing. Each list may be a JSON list or a string holding one, as the dataset stores it.

**Working a case.** The developer builds the case's own Python environment outside the project (its
interpreter and pinned dependencies, never the project installed in it), prepares the case's
repository at its base commit under the case's name with `--python` naming that interpreter, which
`concorde init` records as the project's for its checks' `{python}`, adopts it with the
[brownfield workflow](../../glossary.json#concept.brownfield-workflow), configures its checks,
repairs the adopted Specs with `repair-specs`, and then works the issue through Concorde as a main
agent would, from `understand` to the merge. Finally `grade` grades the merged change.

## Overview

Working a case, with who carries each step: [End-to-end testing](../module.md) prepares the project
and runs its workflows, this Module repairs the adopted Specs and grades the result, and the issue
itself is worked through Concorde as a main agent would. Only `repair-specs` and `grade` belong to
this Module.

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

In a case the Specs are the test's own addition, describing code the test never changes, so the [review findings](../../glossary.json#concept.review-finding)
adoption leaves are repaired before the issue: `repair-specs` opens a task, named `repair-specs`
unless `--task` names another, over the Modules `--modules` names, every Module of the registry by
default, reviews them, runs `specify` once with that review as input and an intent to change only
what the Specs say, keeping every promise true to the code and turning a repair that needs a
decision about intent into an [open question](../../glossary.json#concept.open-question), reviews
them once more, runs `task-validation` and `delivery`, and merges the task
([requirements](requirements.md#req.swe-bench-cases.repair-specs-only)). Every run is started in the
task's worktree and names no task: the [Operations](../../glossary.json#concept.operation) with
`concorde run`, the [execution commands](../../glossary.json#concept.execution-command) as
`concorde task-validation` and `concorde delivery`, each working on the worktree's [workspace
binding](../../glossary.json#concept.workspace-binding). One round bounds it; what the second review
still finds is reported. A review whose [verdict](../../glossary.json#concept.review-verdict) is
`accepted` is followed by `task-validation` and `delivery` with no repair. A review ends `ok`
whether its verdict is `accepted` or `changes_required`, so the second review's remaining findings
do not stop the round. A step that does not end `ok` stops the repair with its result and leaves the
task open. The command prints the task, the Modules, every step with its run, status, summary, the
review's verdict and the error of a step that did not end `ok`, and the step the repair stopped at,
or none. A task of the same name that already exists fails the command with `task open`'s error.
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

`grade` decides whether the merged change resolves the issue the way SWE-bench
does: in a throwaway worktree of `--ref` it puts every file the case's test patch touches back as
it was at the case's base commit, since the change may have edited the same test files, applies
the test patch, runs the test files it names with the given interpreter (`--pythonpath`
directories of that worktree first on `PYTHONPATH`, and colour off whatever the caller's
environment asks for, since the statuses are read from pytest's summary lines), and reports how many
of the FAIL_TO_PASS and PASS_TO_PASS tests passed, each one that did not, and whether the case is
resolved. The test patch and the case's tests stay outside the project: no worker sees them, and
the project is left as it was ([requirements](requirements.md#req.swe-bench-cases.graded-apart)). The pytest output is kept
under `.concorde/runs/e2e/`. The case is resolved when every FAIL_TO_PASS and every PASS_TO_PASS
test passed. Failing tests are a verdict, not an error: each listed test that did not pass is named
with its status, `not run` for one pytest never reported, and pytest's exit code is kept. Grading
stops with an error instead when the instance lacks FAIL_TO_PASS tests, a test patch or a base
commit (`invalid_case`), when the worktree cannot be made or the test patch does not apply
(`command_failed`, naming the command, its exit status and its output), or when the test run
exceeds 30 minutes (`grade_timeout`, naming the case, the ref, the limit and the command, with the
output it had produced). The throwaway worktree is removed however grading ends
([requirements](requirements.md#req.swe-bench-cases.grading-worktree-removed)).

## Why it is built this way

Repairing a review's gaps automatically is otherwise a decision for a person. This exception holds
for cases only, because a case's Specs are the test's own description of code the test never
changes; that is why it lives here and not in the workflow users run, and why it is bounded to one
round that changes Specs and never code
([requirements](requirements.md#req.swe-bench-cases.specs-not-code)). What keeps the code unchanged
is the `specify` [task type](../../glossary.json#concept.task-type), not the intent: it may write
the bound Modules' documents and none of their code, and a specify run whose [write
audit](../../glossary.json#concept.write-audit) finds a changed code file ends `failed`, which stops
the repair before `delivery`. No second round is started: what the second review still finds is
reported and the task is merged, so a case never loops on a model's review.

Grading copies SWE-bench rather than inventing a verdict: the same test patch, the same two test
lists, the files it touches reset to the base commit first. Running it in a throwaway worktree
keeps the case's tests from ever reaching the project, where a worker could see them, and leaves
the project exactly as the merge left it.

## Files

<a id="realization.swe-bench-cases.steps"></a>

The **case steps** are `scripts/e2e/cases.py`: `repair_specs`, which runs the Operations and
execution commands of the repair round through the `concorde` command in the task's worktree, and
`grade` with its helpers. The
`repair-specs` and `grade` commands of `scripts/e2e/e2e.py` call it.

<a id="realization.swe-bench-cases.tests"></a>

The **case step tests**, `tests/concorde/e2e/test_cases.py`, clone a case at its base commit, grade
a toy case before and after its fix, and drive the repair round with stand-in runs, verifying
the [requirements](requirements.md) and [scenarios](scenarios.md).

## Around it

<a id="uses-distribution"></a>

**Distribution** provides the project's `concorde` command, through which the repair round opens its
task, runs its Operations and execution commands in the task's worktree and merges the task; the
case steps never write the project's Specs, [task records](../../glossary.json#concept.task-record)
or [workspace binding](../../glossary.json#concept.workspace-binding) themselves.

<a id="uses-specification"></a>

**Specification** provides the `specify` Operation, whose
[write audit](../../glossary.json#concept.write-audit) fails a run that changed code
([requirement](../../method/specification/requirements.md#req.specification.audit)),
which keeps the repair from changing code.

<a id="uses-spec-review"></a>

**Spec review** provides the `spec_review` Operation, whose
[verdict](../../glossary.json#concept.review-verdict) the round reads to decide whether to repair;
the run ends `ok` for `accepted` and `changes_required` alike.

SWE-bench is external material, included by [End-to-end testing](../module.md): its instances
supply the base commit, test patch and test lists a case is graded with.
