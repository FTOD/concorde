# SWE-bench cases

## Purpose

SWE-bench cases test Concorde's whole change flow on real issues: a
[case](../../glossary.json#concept.case) is prepared at its base commit, adopted, its Specs
repaired, its issue worked through Concorde as a [main
agent](../../glossary.json#concept.main-agent) would, and the merged change graded with the case's
own tests, the way SWE-bench grades it. This [Module](../../glossary.json#concept.module) holds the
two steps that exist only for cases, repairing the adopted Specs in one bounded round and grading a
delivered change, and the case itself. Preparing the project and running its workflows belong to
[End-to-end testing](../module.md). It serves the people developing Concorde only.

## Usage

```text
python3 scripts/e2e/e2e.py repair-specs <project> [--modules <ids>] [--task repair-specs]
python3 scripts/e2e/e2e.py grade <project> --instance <case.json> --python <interpreter> [--ref main] [--pythonpath <dir>]…
```

<a id="concept.case"></a>

**Working a case.** The developer builds the case's own Python environment outside the project (its
interpreter and pinned dependencies, never the project installed in it), prepares the case's
repository at its base commit under the case's name with `--python` naming that interpreter, which
`concorde init` records as the project's for its checks' `{python}`, adopts it with the brownfield
workflow, configures its checks, repairs the adopted Specs with `repair-specs`, and then works the
issue through Concorde as a main agent would, from `understand` to the merge. The case itself is one
SWE-bench instance, one row of SWE-bench's dataset saved as a JSON file and given to `grade` with
`--instance`: its `instance_id`, its `base_commit`, its `test_patch`, the case's own test changes,
and two lists of pytest test identities: `FAIL_TO_PASS`, the tests that fail before the issue is
resolved and must pass after it, and `PASS_TO_PASS`, the tests that must keep passing. Each list may
be a JSON list or a string holding one, as the dataset stores it.

**Repairing the adopted Specs.** In a case the Specs are the test's own addition, describing code
the test never changes, so the [review findings](../../glossary.json#concept.review-finding)
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

**Grading a case.** `grade` decides whether the merged change resolves the issue the way SWE-bench
does: in a throwaway worktree of `--ref` it puts every file the case's test patch touches back as
it was at the case's base commit, since the change may have edited the same test files, applies
the test patch, runs the test files it names with the given interpreter (`--pythonpath`
directories of that worktree first on `PYTHONPATH`), and reports how many of the FAIL_TO_PASS and
PASS_TO_PASS tests passed, each one that did not, and whether the case is resolved. The test patch
and the case's tests stay outside the project: no worker sees them, and the project is left as it
was ([requirements](requirements.md#req.swe-bench-cases.graded-apart)). The pytest output is kept
under `.concorde/runs/e2e/`. The case is resolved when every FAIL_TO_PASS and every PASS_TO_PASS
test passed. Failing tests are a verdict, not an error: each listed test that did not pass is named
with its status, `not run` for one pytest never reported, and pytest's exit code is kept. Grading
stops with an error instead when the instance lacks FAIL_TO_PASS tests, a test patch or a base
commit (`invalid_case`), or when the worktree cannot be made or the test patch does not apply
(`command_failed`, naming the command, its exit status and its output). The throwaway worktree is
removed however grading ends
([requirements](requirements.md#req.swe-bench-cases.grading-worktree-removed)).

## Design

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

<a id="realization.swe-bench-cases.steps"></a>

The **case steps** are `scripts/e2e/cases.py`: `repair_specs`, which runs the Operations and
execution commands of the repair round through the `concorde` command in the task's worktree, and
`grade` with its helpers. The
`repair-specs` and `grade` commands of `scripts/e2e/e2e.py` call it.

<a id="realization.swe-bench-cases.tests"></a>

The **case step tests**, `tests/concorde/e2e/test_cases.py`, clone a case at its base commit, grade
a toy case before and after its fix, and drive the repair round with stand-in runs, verifying
the [requirements](requirements.md) and [scenarios](scenarios.md).

### Around it

<a id="uses-distribution"></a>

**Distribution** provides the project's `concorde` command, through which the repair round opens its
task, runs its Operations and execution commands in the task's worktree and merges the task; the
case steps never write the project's Specs, [task records](../../glossary.json#concept.task-record)
or [workspace binding](../../glossary.json#concept.workspace-binding) themselves.

SWE-bench is external material, included by [End-to-end testing](../module.md): its instances
supply the base commit, test patch and test lists a case is graded with.
