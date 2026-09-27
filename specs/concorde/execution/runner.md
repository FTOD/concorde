# How a run is executed

The exact behaviour of the [Execution runner](module.md#concept.execution.runner): the command
lines, the workspace binding it reads, the runner's steps, the progress file and how refusals and
failures become a result. The envelope is the [run result contract](contracts.md#contract.execution.run-result)
and the binding the [workspace binding contract](contracts.md#contract.execution.workspace-binding).
What an Operation adds, its worker sequence, is in
[How an Operation runs its workers](operations/workers.md).

## Command lines

```text
concorde run <operation> [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [operation arguments]
concorde <command>       [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [command arguments]
```

- `<operation>` is a name from the [Operation catalog](operations/module.md#concept.operations.catalog);
  `<command>` is one of the execution commands `task-validation`, `delivery` and `scaffold`.
  `concorde run` naming an execution command is a command-line error that names the command to use
  instead.
- The run works on the worktree the command starts in: the Git worktree containing the current
  directory. A directory outside every Git worktree is a command-line error.
- `--modules` names the Modules the run works on. Without it a bound run works on the binding's
  Modules that the workspace still registers, and an unbound run on none. Every named Module must
  be registered in the worktree.
- Each `--input` names a run whose result is `ok` and whose workspace is this run's workspace, or,
  for an unbound run, a run without a workspace; its saved `output` is admitted, with its name, as
  material of the run. Any other run is refused with `input_not_admissible`.
- Operation and command arguments are defined by the definition and parsed with the rest; an
  unknown argument is a command-line error.
- Standard output receives exactly the run result as one JSON value. Diagnostics go to standard
  error.
- Exit status 0 means the result's status is `ok`, 1 means `blocked` or `failed`, and 2 means the
  command line was malformed or named no known Operation or command, in which case no run is
  created and no result is written.

## Workspace binding

The runner reads `.concorde/workspace.json` at the root of the worktree it starts in:

- When the file is absent, the run is **unbound**: its records directory is that worktree's own
  `.concorde`, its workspace is null, it takes no lock, and it is admitted only when its
  definition allows unbound runs; otherwise it is refused with `binding_required`.
- When the file is present, it must satisfy the binding contract and name as `root` the worktree
  it lies in; otherwise the run is refused with `binding_unreadable`, `binding_invalid` or
  `binding_misplaced`, and its result is written in the worktree's own `.concorde`.
- A bound run's records directory is the binding's `records`, and its run context gives every step
  the workspace's name, goal, Modules, branch and base commit.

The runner never writes the binding.

## Run identity and directory

The runner creates the run identity `r-<YYYYMMDD>T<HHMMSS>-<name>-<8 hex digits>` from the UTC start
time, the definition's name with `-` written as `_`, and random digits, and the run directory
`<records>/runs/<run-id>/`. The directory holds `result.json`, the run result exactly as printed,
the progress file, the logs of the checks the run ran, and for a detached run the runner's output
`host.out`. Workers keeps each worker launch's run record beside it, in the same run store, and the
result lists their identities.

## Runner

| # | Step | Stops the run when |
| --- | --- | --- |
| 1 | Parse the command line and look up the definition; only then create the run identity and directory | malformed command line, unknown Operation or command, a directory outside Git (exit 2, the reason on standard error, no result, no directory) |
| 2 | Read the workspace binding | an unreadable, invalid or misplaced binding (`failed`) |
| 3 | For a bound run, take the workspace lock | `workspace_busy` (`failed`) |
| 4 | Admit the run: refuse an unbound run of a definition that needs a binding; settle the Modules, leaving out with `removed-module` evidence each binding Module the workspace no longer registers; check the named Modules against the workspace's registry unless the definition diagnoses the Specs itself; admit the inputs | `binding_required`, `modules_removed`, `unknown_module`, `specs_unloadable`, `input_not_admissible` (`failed`) |
| 5 | Execute the definition's steps in order | a step stops the run with a status |
| 6 | Compose the run result from the step outcomes and check it against the run result contract and the definition's output contract | the result or output is invalid (`failed`, `invalid-output` evidence) |
| 7 | Write `result.json`, mark the progress file finished, release the lock, print the result and exit | — |

- Each step returns either "continue", with any output and evidence it produced, or "stop", with a
  status, a summary and evidence. Steps of one run share the run context: the workspace binding,
  the worktree, the records directory, the Modules, the admitted inputs, the output so far, a
  state the definition owns, and the run record of the latest worker launch. The runner never
  skips, repeats or reorders steps; any repetition, such as resume rounds, happens inside one step.
- An exception raised by a step becomes a `failed` result with `host-error` evidence naming the
  step, the error type and message; the cause of its error is a `component` link with the
  exception's type, message and command output, where it was raised and the path of the full
  traceback in the run directory.
- On `SIGINT` or `SIGTERM` the runner stops its running step, ends every worker process the run
  started through Workers and finishes with a `failed` result with `cancelled` evidence naming the
  signal. Its `cancelled` link names every worker run the run started, with evidence of kind
  `worker-run` pointing at each run's record and progress file, and `worker_runs` lists them: the
  runner learns each worker run's identity when the worker run starts, not when it returns.
- Steps 6 and 7 run whatever happened before them. A refusal in steps 2 to 4 still writes and
  prints a result, with the refusal code as `refused` evidence and an error whose cause is the
  refusal of the workspace binding or the run store with its message, such as the run holding the
  lock of a busy workspace or the registered Modules for an unknown one.
- The result is written before the lock is released, so a result always means a workspace free
  for its next run.
- Whenever the status is not `ok`, the runner also writes the error chain, rendered as indented
  text, to standard error.

## Detached runs

With `--detach` the command checks the command line (a malformed one starts nothing, with exit
status 2), chooses the run identity, creates the run directory and starts the runner as a process of
its own, in a new session, handing it the identity. It then waits until the run's progress file
exists and prints `{run_id, kind, name, host_pid, progress, result}` with exit status 0. A runner
that ends or has not written its progress file within the announcement wait is killed, with its
process group, and the command prints the same fields with an `error` link `detach_failed` naming
the end of the runner's output, with exit status 1, so an unannounced runner never starts its run
later.

## Progress file

The runner writes `<records>/runs/<run-id>/status.json` atomically when the run directory is
created, before each step and when the result is written:

| Field | Content |
| --- | --- |
| `kind` | `operation` or `command` |
| `run_id`, `name`, `workspace`, `worktree`, `modules` | the run's identity, definition, workspace (null when unbound), worktree and Modules |
| `phase` | `running`, then `finished` once `result.json` is written |
| `step` | the step running now, or null |
| `status`, `summary` | null while running; the result's status and summary once finished |
| `host_pid` | the runner's process identifier, which every worker run it launches records too |
| `started_at`, `updated_at` | UTC times |

A failed write never changes the run.

## Errors

When a run does not end `ok`, the result's `error` is the run's own link of the
[error chain](../contracts.md#contract.concorde.error): the level `operation` for an Operation and
`command` for an execution command, the actor `Operation <name> <run-id> (workspace <workspace>)`,
`Command <name> <run-id> (workspace <workspace>)` or, unbound, `… (unbound, <worktree>)`, a code, a
detail naming the workspace, the Modules, the run, the paths and the messages concerned, the reason
the run cannot handle the error, the options it offers with a recommendation, and as causes the
errors it received, unchanged. A step that stops the run builds that link itself; the runner builds
it as follows.

| Error | Code | Reason | Causes |
| --- | --- | --- | --- |
| Refusal before the steps began | `refused` | `decision` for `workspace_busy`; `scope` for `binding_required` and `specs_unloadable`; `environment` for `binding_unreadable`; `input` otherwise | the `component` link of `Execution (workspace binding)` or `Execution (run store)` with the refusal's code and message |
| A step raised | `host_error` | `capability` | the exception's `component` link |
| Cancelled | `cancelled` | `environment` | none |
| Invalid result or output | `invalid_result` | `capability` | the error the run had, if any |
| A step stopped without an error | `missing_error` | `capability` | none |

Spec tooling reports with [its own error record](../spec-tooling/spec/errors.md), never with a link.
When a Spec tooling error causes a run's error, the step translates it into a `component` link of
the actor `Spec core`: the record's message and location become the detail, its reason becomes the
explanation of why Spec core could not handle it (reason `input`, or `environment` for a
`system_error`), its remediation becomes the option and recommendation, and each of its causes
becomes a nested link the same way. A Check execution or Issue error, which are subclasses of the
Spec tooling error type registered by their own Modules, is translated the same way.
