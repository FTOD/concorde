# SWE-bench cases

## Purpose

SWE-bench cases test Concorde's whole change flow on real issues: a case is prepared at its base
commit, adopted, its Specs repaired, its issue worked through Concorde as a main agent would, and
the merged change graded with the case's own tests, the way SWE-bench grades it. This Module holds
the two steps that exist only for cases, repairing the adopted Specs in one bounded round and
grading a delivered change, and the case itself. Preparing the project and running its workflows
belong to [End-to-end testing](../module.md). It serves the people developing Concorde only.

## Terminology

| Term | Definition |
| --- | --- |
| Case | A SWE-bench task instance: an issue of one repository at its base commit, with a test patch and the tests that must pass once the issue is resolved. |
| [Test project](../module.md#concept.e2e.test-project) | |
| [Developer](../../vocabulary.md#concept.concorde.developer) | |

A case is worked in a test project prepared at the case's base commit and named after it.

## Usage

```text
python3 scripts/e2e/e2e.py repair-specs <project> [--modules <ids>] [--task repair-specs]
python3 scripts/e2e/e2e.py grade <project> --instance <case.json> --python <interpreter> [--ref main] [--pythonpath <dir>]…
```

<a id="concept.swe-bench-cases.case"></a>

**Working a case.** The developer builds the case's own Python environment outside the project (its
interpreter and pinned dependencies, never the project installed in it), prepares the case's
repository at its base commit under the case's name with `--python` naming that interpreter, which
`concorde init` records as the project's for its checks' `{python}`, adopts it with the brownfield
workflow, configures its checks, repairs the adopted Specs with `repair-specs`, and then works the
issue through Concorde as a main agent would, from `understand` to the merge.

**Repairing the adopted Specs.** In a case the Specs are the test's own addition, describing code
the test never changes, so the review findings adoption leaves are repaired before the issue:
`repair-specs` opens a task over the adopted Modules, reviews them, runs `specify` once with that
review as input and an intent to change only what the Specs say, keeping every promise true to
the code and turning a repair that needs a decision about intent into an open question, reviews
them once more, and validates, delivers and merges the task
([requirements](requirements.md#req.swe-bench-cases.repair-specs-only)). One round bounds it; what
the second review still finds is reported. A review that accepts the Specs is followed by
`validate` and `delivery` with no repair, and a step that does not end `ok` stops the repair with
its result and leaves the task open.

**Grading a case.** `grade` decides whether the merged change resolves the issue the way SWE-bench
does: in a throwaway worktree of `--ref` it puts every file the case's test patch touches back as
it was at the case's base commit, since the change may have edited the same test files, applies
the test patch, runs the test files it names with the given interpreter (`--pythonpath`
directories of that worktree first on `PYTHONPATH`), and reports how many of the FAIL_TO_PASS and
PASS_TO_PASS tests passed, each one that did not, and whether the case is resolved. The test patch
and the case's tests stay outside the project: no worker sees them, and the project is left as it
was ([requirements](requirements.md#req.swe-bench-cases.graded-apart)). The pytest output is kept
under `.concorde/runs/e2e/`.

## Design

Repairing a review's gaps automatically is otherwise a decision for a person. This exception holds
for cases only, because a case's Specs are the test's own description of code the test never
changes; that is why it lives here and not in the workflow users run, and why it is bounded to one
round that changes Specs and never code.

Grading copies SWE-bench rather than inventing a verdict: the same test patch, the same two test
lists, the files it touches reset to the base commit first. Running it in a throwaway worktree
keeps the case's tests from ever reaching the project, where a worker could see them, and leaves
the project exactly as the merge left it.

<a id="realization.swe-bench-cases.steps"></a>

The **case steps** are `scripts/e2e/cases.py`: `repair_specs`, which runs the Operations of the
repair round through the project's `concorde` command, and `grade` with its helpers. The
`repair-specs` and `grade` commands of `scripts/e2e/e2e.py` call it.

<a id="realization.swe-bench-cases.tests"></a>

The **case step tests**, `tests/concorde/e2e/test_cases.py`, clone a case at its base commit, grade
a toy case before and after its fix, and drive the repair round with stand-in Operations, verifying
the [requirements](requirements.md) and [scenarios](scenarios.md).

### Around it

<a id="uses-distribution"></a>

**Distribution** provides the project's `concorde` command, through which the repair round opens,
runs, delivers and merges its task; the case steps never write the project's Specs or task
records themselves.

SWE-bench is external material, included by [End-to-end testing](../module.md): its instances
supply the base commit, test patch and test lists a case is graded with.
