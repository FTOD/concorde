# Code review

## Purpose

Code review gives the main agent an independent judgement of a task's code changes against the
Specs. It provides the `code_review` Operation: a worker reads the bound Modules' Specs, code and
tests, changes nothing, and reports every problem it can establish in one pass, tied to the promise
it judges the code against; the host derives the verdict, and the main agent decides whether to run
`implement` again, repair the Spec first or move to validation. Code review never edits a file,
never runs a command and judges code only against the Specs in the bound Modules' context; a clean
review is evidence about the reviewed inputs only, not proof of no other defect.

## Terminology

| Term | Definition |
| --- | --- |
| Code review report | The result of one code review run: the reviewer's findings about the task's code changes, the verdict the host derived from them and the inputs the review examined. |
| Code review finding | One problem the reviewer established in the reviewed code, judged blocking or advisory and tied to the Spec promise or passage it violates or leaves unanswered. |
| [Main agent](../../vocabulary.md#concept.concorde.main-agent) | |
| [Worker](../../vocabulary.md#concept.concorde.worker) | |
| [Task type](../../vocabulary.md#concept.concorde.task-type) | |
| [Spec context](../../vocabulary.md#concept.concorde.spec-context) | |
| [Task context](../../vocabulary.md#concept.concorde.task-context) | |
| [Evidence](../../vocabulary.md#concept.concorde.evidence) | |
| [Operation](../module.md#concept.operations.operation) | |
| [Operation host](../module.md#concept.operations.host) | |
| [Operation result](../module.md#concept.operations.result) | |
| [Grant](../../spec-tooling/spec/module.md#concept.spec.grant) | |
| [Brief](../../agents/workers/module.md#concept.workers.brief) | |
| [Worker result](../../agents/workers/module.md#concept.workers.worker-result) | |
| [Write audit](../../agents/workers/module.md#concept.workers.audit) | |
| [Configured check](../../checks/module.md#concept.checks.configured-check) | |
| [Check result](../../checks/module.md#concept.checks.check-result) | |

## Usage

```text
concorde run code_review [--task <task-id>] --modules <module-id>[,<module-id>…] [--base <ref>] [--focus "<text>"]
```

`--modules` names the judged Modules (task Modules by default), `--base` the diff's start commit
(the task branch's start by default; required [without a task](../module.md#concept.operations.no-task),
when the review judges the primary worktree since that commit), and `--focus` a concern to look at first, never narrowing
what may be reported. For example, `code_review --modules module.issues` gives the reviewer the
Issues Spec, code and tests, the branch diff and the Issues checks.

```d2
op: Code review Operation
review: Code review report
finding: Code review finding
op -> review: produces
review -> finding: holds
```

<a id="concept.code-review.review"></a>

The Operation returns an [Operation result](../module.md#concept.operations.result) whose `output`
is a **code review report** ([contract](contracts.md#contract.code-review.review)), with verdict
`changes_required` when any finding is blocking, else `clean`.

| Status | Code | Reason | Detail |
| --- | --- | --- | --- |
| `ok` | — | — | review completed, any verdict |
| `blocked` | — | — | reviewer could not judge the change at all, e.g. an all-unbound-files diff |
| `failed` | — | — | host could not run the reviewer, or the audit found a change |
| `failed` | `unresolved_basis` | `capability` | a finding cites a nonexistent promise, or a blocking finding names no basis; names every finding with the basis it cites |
| `failed` | `unresolved_base` | — | Git's message as cause |

Only an `ok` run carries a report; other runs still name the base, diff paths and check results as
host evidence.

<a id="concept.code-review.finding"></a>

Each **code review finding** is blocking (undeliverable unfixed) or advisory, and names its kind: a
violation of a stated promise, a defect the Spec's promises imply, a missing test for a touched
scenario, a change outside the bound Modules' code, or a Spec gap, where the code does something
the Spec neither requires nor forbids. A blocking finding always names its basis — a stable
identity
(requirement, scenario, contract or concept) or a Spec passage — from the bound Modules'
[Spec context](../../vocabulary.md#concept.concorde.spec-context). The main agent usually answers
blocking Spec gaps with `specify`, other blocking findings with `implement`.

## Design

The Operation is worker-backed, run by the [Operation host](../module.md#concept.operations.host)
with task type `review-code`: the reviewer reads the bound Modules' Spec context, external material
and their realizations' files, sees others by name only, and writes nothing. The diff is
[task context](../../vocabulary.md#concept.concorde.task-context): it adds no source, and the host
cuts it to what the grant already makes readable.

| # | Step | Actor | Stops when |
| --- | --- | --- | --- |
| 1 | Freeze the bound Modules' `review-code` [grant](../../spec-tooling/spec/module.md#concept.spec.grant) | Workers, Spec core | Specs won't load / Module unknown (`failed`) |
| 2 | Diff base→worktree, untracked included; keep readable paths' contents, list rest by name | host, Spec core | base unresolved (`failed`) |
| 3 | Run bound Modules' [configured checks](../../checks/module.md#concept.checks.configured-check) outside the worker | host, Check execution | a check won't start (`failed`) |
| 4 | Build worker settings, tools and [brief](../../agents/workers/module.md#concept.workers.brief): focus, diff, named-only paths, [check results](../../checks/module.md#concept.checks.check-result) with the last part of every log that did not pass, grant's read/names | Workers | — |
| 5 | Launch reviewer, await its [worker result](../../agents/workers/module.md#concept.workers.worker-result) | Workers, worker | launch error/timeout (`failed`); `blocked` passed on |
| 6 | [Audit](../../agents/workers/module.md#concept.workers.audit) the worktree (no writable path, so any change is a violation); write run record | Workers | any change (`failed`) |
| 7 | Resolve every finding's basis, derive the verdict | host, Spec core | unresolved/missing basis (`failed`) |
| 8 | Return the Operation result | host | — |

The reviewer gets Read, Glob and Grep only — no Edit, Write, Bash, web or MCP — so the host runs
checks first and hands over the results; a failing check is for the reviewer to interpret. A very
large diff is cut short in the brief, and the reviewer reads the rest through its grant. There is
no resume round: it reports every blocking finding in one pass, since another round re-reads
everything and lets one fix hide the next — also why a review is not repeated automatically after
`implement`.

The reviewer judges only against the Specs in its context, never against taste or another Module's
code, so a disputed finding traces to a written promise. The host verifies only what it can
decide — that every cited basis exists and which verdict follows — and otherwise keeps findings as
claims. See the [requirements](requirements.md) and [scenarios](scenarios.md) for the precise
obligations.

```d2
codereview: Code review {
  op: Code review Operation {
    "src/concorde/code_review/"
    "prompts/workers/review-code.md"
    "tests/concorde/code_review/"
  }
}
```

<a id="realization.code-review.operation"></a>

The **Code review Operation** realization holds the host steps, the `review-code` worker
instructions, the result schema and its tests: the reviewer returns only findings and a summary;
the host adds the base, paths, check results and verdict.

## Relationships

```d2
codereview: Code review
operations: Operations
workers: Workers
checks: Check execution
spec: Spec core
codereview -> operations
codereview -> workers
codereview -> checks
codereview -> spec
```

- <a id="uses-operations"></a>**Operations** lists `code_review`, dispatches to this Module and
  provides the host runner and the [Operation result](../module.md#concept.operations.result)
  envelope. Code review relies on the host to record the run and calls no other Operation.
- <a id="uses-workers"></a>**Workers** turns the frozen grant into worker settings, launches the
  reviewer with this Module's brief, collects its
  [worker result](../../agents/workers/module.md#concept.workers.worker-result), audits the
  worktree and writes the run record.
- <a id="uses-checks"></a>**Check execution** runs the bound Modules'
  [configured checks](../../checks/module.md#concept.checks.configured-check) read-only
  and returns a [check result](../../checks/module.md#concept.checks.check-result) for
  each, passed to the reviewer and included in the report unchanged.
- <a id="uses-spec"></a>**Spec core** computes the `review-code`
  [grant](../../spec-tooling/spec/module.md#concept.spec.grant), decides which changed paths the
  diff may show in full, and resolves findings' basis identities. Code review never computes a
  boundary itself.
