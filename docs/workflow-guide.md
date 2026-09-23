# Concorde workflow guide

This guide follows one change from an idea to a merge, the way a developer and the Claude Code
main agent carry it out with Concorde. It uses **Spec Protocol 12.0.0** and **Claude Code** only;
Pi is not supported in this version. `concorde` below means the project's `.concorde/bin/concorde`
(in Concorde's own checkout, `python3 scripts/concorde.py`).

## The actors

- **The developer** decides the direction and answers questions of major impact.
- **The main agent** is the developer's Claude Code session in the primary worktree. The installed
  skill makes it split work into tasks, run Operations, read their results, keep decision logs and
  merge delivered work. It normally does not edit the project itself.
- **Workers** are headless `claude -p` processes that one Operation starts for one bounded task of
  one task type. Their boundary is a **grant** computed from the task worktree's Specs.
- **The Operation host** is the deterministic part of every Operation: it computes the grant,
  launches the worker, audits what it changed, runs the checks and writes the result.

## 1. Understand the project

The main agent answers questions from the Specs. Two commands help it without running a worker:

```bash
concorde validate                                   # structural checks of every Spec
concorde grant --modules module.payments --type implement
```

The grant lists every path an `implement` worker for `module.payments` could know by name
(`names`), read (`ro`) or write (`rw`); every other path is denied. The main agent may also
register `concorde spec-mcp` in the project's `.mcp.json` to ask the same questions over MCP.

## 2. Open a task

Agreed work becomes a task: a branch `concorde/<task>` with its own worktree next to the primary
checkout, a record and a decision log in `.concorde/tasks/`.

```bash
concorde task open retry --goal "limit payment retries" --modules module.payments
concorde task show retry          # the record and the decision log's path
```

Tasks whose Modules and shared files do not overlap may run at the same time; each has its own
worktree, and one task runs at most one Operation at a time.

## 3. Run Operations

The main agent runs every Operation with `concorde run` in background Bash and reads the JSON
result when the command exits (status 0 `ok`, 1 `blocked` or `failed`, 2 a bad command line).

| Operation | Task type | What it does |
| --- | --- | --- |
| `understand` | `understand` | Assesses what the Modules promise and whether the Spec suffices; plans when asked. Writes nothing. |
| `specify` | `specify` | Changes the bound Modules' own Spec documents, including declaring pending files. |
| `implement` | `implement` | Changes the bound Modules' code; the host runs the configured checks and resumes the worker on failures. |
| `test` | `test` | The host runs the configured checks; the worker reads the code and interprets the results. |
| `spec_review` | `review-spec` | Reviews the bound Modules' Specs and reports every blocking finding. |
| `code_review` | `review-code` | Reviews the task's code changes against the Specs. |
| `validate` | — | Deterministic: structural validation and the configured checks of the changed Modules; decides readiness. |
| `delivery` | — | Deterministic: commits the task's change with an evidence bundle on the task branch. |

`--input <run-id>` admits the output of an earlier `ok` run of the same task, such as a plan from
`understand`, into the next worker's brief.

### What a worker can and cannot do

A worker runs in its own run directory under `.concorde/runs/`, never in the worktree, with a
cleared environment and its own Claude Code configuration. Its settings deny the file tools every
path outside its grant, allow Edit and Write only on `rw` paths through a hook, and run Bash in a
sandbox without network. It never sees Git. A file it may not write yet must first be declared as a
pending file of its Module through `specify`. After each round the host audits the worktree: any
write outside `rw` fails the run.

### Reading a result

- `host_evidence`: facts the host produced — the grant, the audit, each check with its exit code and
  log, the rounds, the worker's transcript path.
- `worker`: the worker's own result, a claim, never evidence.
- `escalation`: for any result that is not `ok`, the problem, what was tried, the options and a
  recommendation, with its source (`host` or `worker`).

Automatic resume rounds repair failing checks only. A Spec gap, a path outside the grant or a
structural Spec error stops the Operation and comes back as an escalation.

## 4. Decide and record

The main agent decides ordinary questions itself — names, internal structure, the order of tasks,
re-running an Operation with a clearer brief — writes each decision and every result that was not
`ok` into the task's decision log, and reports them at the end. It asks the developer first only
when a decision changes what a Module promises, the project's direction or an earlier decision of
the developer, discards work, cannot be reverted, touches security, or needs more resources.

## 5. Validate, deliver and merge

```bash
concorde run validate --task retry
concorde run delivery --task retry
git merge concorde/retry
concorde task close retry --merged
```

`delivery` refuses without current readiness from `validate`. It commits the change with an
evidence bundle under `.concorde/evidence/` on the task branch. The main agent merges the branch
without asking for authorization and closes the task. A task that will not be merged is closed
with `--abandoned`.

## Issues

A problem the current task will not fix is recorded as an Issue under `.concorde/issues/`;
`python3 scripts/issues.py list` shows what is open. Solving an Issue is ordinary work: a task for
its Module, the Operations that fix it, and the Issue closed on that task's branch.

## Development

Concorde is developed in this checkout as direct developer-authorized maintenance: change sources,
run `python3 scripts/concorde.py build`, `build --check`, `validate` and the tests, and commit each
verified step. See [AGENTS.md](../AGENTS.md) and the [refactor design](design/concorde-refactor.md).
