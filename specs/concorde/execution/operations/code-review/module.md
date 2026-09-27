# Code review

## Purpose

Code review gives the [main agent](../../../glossary.json#concept.main-agent) an independent
judgement of a workspace's [code changes](../../../glossary.json#concept.code-change) against the
Specs. It provides the `code_review` [Operation](../../../glossary.json#concept.operation): a worker
reads the bound Modules' Specs, code and tests, changes nothing, and reports every problem it can
establish in one pass, tied to the promise it judges the code against; the Operation derives the
verdict, and the main agent decides whether to run `implement` again, repair the
[Spec](../../../glossary.json#concept.spec) first or move to validation. Code review never edits a
file, never runs a command and judges code only against the Specs in the bound Modules' context; a
clean review is evidence about the reviewed inputs only, not proof of no other defect.

## Usage

```text
concorde run code_review [--modules <module-id>[,<module-id>…]] [--base <ref>] [--focus "<text>"]
```

The run judges the [workspace](../../../glossary.json#concept.workspace) whose binding lies in
the worktree it starts in. `--modules` names the judged Modules (the binding's by default),
`--base` the diff's start commit (the binding's base commit by default; required for an
[unbound run](../../../glossary.json#concept.unbound-run), which judges the worktree it starts
in, such as the primary worktree, since that commit), and `--focus` a concern to look at first,
never narrowing what may be reported. For example, `code_review --modules module.issues` gives the
reviewer the Issues Spec, code and tests, the workspace's diff since its base and the Issues
checks.

<a id="concept.code-review-report"></a>

The Operation returns a [run result](../../../glossary.json#concept.run-result) whose `output` is a
**[code review report](../../../glossary.json#concept.code-review-report)**
([contract](contracts.md#contract.code-review.review)), with verdict `changes_required` when any
finding is blocking, else `clean`.

| Status | Code | Reason | Detail |
| --- | --- | --- | --- |
| `ok` | — | — | review completed, any verdict |
| `blocked` | — | — | reviewer could not judge the change at all, e.g. an all-unbound-files diff |
| `failed` | — | — | the reviewer could not be run, or the audit found a change |
| `failed` | `no_base` | `input` | an unbound run without `--base`, or a binding without a base commit |
| `failed` | `unresolved_basis` | `capability` | a finding cites a nonexistent promise, or a blocking finding names no basis; names every finding with the basis it cites |
| `failed` | `unresolved_base` | — | Git's message as cause |

Only an `ok` run carries a report; other runs still name the base, diff paths and check results as
host evidence.

<a id="concept.code-review-finding"></a>

Each **[code review finding](../../../glossary.json#concept.code-review-finding)** is blocking
(undeliverable unfixed) or advisory, and names its kind: a violation of a stated promise, a defect
the Spec's promises imply, a missing test for a touched scenario, a change outside the bound
Modules' code, or a [Spec gap](../../../glossary.json#concept.spec-gap), where the code does
something the Spec neither requires nor forbids. A blocking finding always names its basis — a
stable identity (requirement, scenario, contract or concept) or a Spec passage — from the bound
Modules' [Spec context](../../../glossary.json#concept.spec-context). The main agent usually answers
blocking Spec gaps with `specify`, other blocking findings with `implement`.

## Design

The Operation is worker-backed, run by the
[Execution runner](../../../glossary.json#concept.execution-runner) with
[task type](../../../glossary.json#concept.task-type) `review-code`: the reviewer reads the bound
Modules' Spec context, external material and their realizations' files, sees others by name only,
and writes nothing. The diff is [task context](../../../glossary.json#concept.task-context): it adds
no source, and the Operation cuts it to what the grant already makes readable.

| # | Step | Actor | Stops when |
| --- | --- | --- | --- |
| 1 | Freeze the bound Modules' `review-code` [grant](../../../glossary.json#concept.grant) | Workers, Spec core | Specs won't load / [Module](../../../glossary.json#concept.module) unknown (`failed`) |
| 2 | Diff base→worktree, untracked included; keep readable paths' contents, list rest by name | Operation, Spec core | base unresolved (`failed`) |
| 3 | Run bound Modules' [configured checks](../../../glossary.json#concept.configured-check) outside the worker | Operation, Check execution | a check won't start (`failed`) |
| 4 | Build [worker settings](../../../glossary.json#concept.worker-settings), tools and [brief](../../../glossary.json#concept.brief): focus, diff, named-only paths, [check results](../../../glossary.json#concept.check-result) with the last part of every log that did not pass, grant's read/names | Workers | — |
| 5 | Launch reviewer, await its [worker result](../../../glossary.json#concept.worker-result) | Workers, worker | launch error/timeout (`failed`); `blocked` passed on |
| 6 | [Audit](../../../glossary.json#concept.write-audit) the worktree (no writable path, so any change is a violation); write [run record](../../../glossary.json#concept.run-record) | Workers | any change (`failed`) |
| 7 | Resolve every finding's basis, derive the verdict | Operation, Spec core | unresolved/missing basis (`failed`) |
| 8 | Return the run's output | Operation, Execution runner | — |

The reviewer gets Read, Glob and Grep only — no Edit, Write, Bash, web or MCP — so the Operation
runs checks first and hands over the results; a failing check is for the reviewer to interpret. A
very large diff is cut short in the brief, and the reviewer reads the rest through its grant. There
is no [resume round](../../../glossary.json#concept.resume-round): it reports every blocking finding
in one pass, since another round re-reads everything and lets one fix hide the next — also why a
review is not repeated automatically after `implement`.

The reviewer judges only against the Specs in its context, never against taste or another Module's
code, so a disputed finding traces to a written promise. The Operation verifies only what it can
decide — that every cited basis exists and which verdict follows — and otherwise keeps findings as
claims. See the [requirements](requirements.md) and [scenarios](scenarios.md) for the precise
obligations.

<a id="realization.code-review.operation"></a>

The **Code review Operation** realization holds the Operation steps, the `review-code` worker
instructions, the result schema and its tests: the reviewer returns only findings and a summary;
the Operation adds the base, paths, check results and verdict.

### Outside

- <a id="uses-operations"></a>**Operations** lists `code_review` in its catalog as an Operation
  that writes nothing and may run unbound with `--base`, and names this Module as its provider.
  Code review calls no other Operation.
- <a id="uses-execution"></a>**Execution**'s
  [runner](../../../glossary.json#concept.execution-runner) runs the Operation's steps: it reads the
  [workspace binding](../../../glossary.json#concept.workspace-binding), settles the Modules,
  records the run and wraps the report in the
  [run result](../../../glossary.json#concept.run-result). Code review relies on it for the
  binding's base commit, the default of `--base`, and for recording the run.
- <a id="uses-workers"></a>**Workers** turns the frozen grant into worker settings, launches the
  reviewer with this Module's brief, collects its
  [worker result](../../../glossary.json#concept.worker-result), audits the
  worktree and writes the run record.
- <a id="uses-checks"></a>**Check execution** runs the bound Modules'
  [configured checks](../../../glossary.json#concept.configured-check) read-only
  and returns a [check result](../../../glossary.json#concept.check-result) for
  each, passed to the reviewer and included in the report unchanged.
- <a id="uses-spec"></a>**Spec core** computes the `review-code`
  [grant](../../../glossary.json#concept.grant), decides which changed paths the
  diff may show in full, and resolves findings' basis identities. Code review never computes a
  boundary itself.
