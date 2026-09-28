# How a run is executed

The exact behaviour of the [Execution runner](../glossary.json#concept.execution-runner): the
command lines, the [workspace binding](../glossary.json#concept.workspace-binding) it reads, the
runner's steps, the [run progress file](../glossary.json#concept.run-progress-file) and how refusals
and failures become a result. The Operation or execution command a command line names is the run's
definition: its steps, its arguments, whether it may run unbound and its output contract. The
envelope is the [run result contract](contracts.md#contract.execution.run-result) and the binding
the [workspace binding contract](contracts.md#contract.execution.workspace-binding). What an
[Operation](../glossary.json#concept.operation) adds, its worker sequence, is in
[How an Operation runs its workers](operations/workers.md).

## Command lines

```text
concorde run <operation> [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [--wait <seconds>] [operation arguments]
concorde <command>       [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [--wait <seconds>] [command arguments]
```

- `<operation>` is a name from the [Operation catalog](../glossary.json#concept.operation-catalog);
  `<command>` is one of the [execution commands](../glossary.json#concept.execution-command)
  `task-validation`, `delivery` and `scaffold`. `concorde run` naming an execution command is a
  command-line error that names the command to use instead.
- The run works on the worktree the command starts in: the Git worktree containing the current
  directory, or for an [unbound run](../glossary.json#concept.unbound-run) its
  [unbound checkout](#unbound-checkout). A directory outside every Git worktree is a command-line
  error.
- `--modules` names the Modules the run works on. Without it a bound run works on the binding's
  Modules that the workspace still registers, and an
  [unbound run](../glossary.json#concept.unbound-run) on none. Every named
  [Module](../glossary.json#concept.module) must be registered in the worktree.
- Each `--input` names a run whose result is `ok` and whose workspace is this run's workspace, or,
  for an unbound run, a run without a workspace; its saved `output` is admitted, with its name, as
  material of the run. Any other run is refused with `input_not_admissible`.
- `--wait <seconds>` (default 0) is how long a bound run waits for a busy workspace's lock before
  it is refused with `workspace_busy`; a negative value is a command-line error. An unbound run
  takes no lock and ignores it.
- Operation and command arguments are defined by the definition and parsed with the rest; an
  unknown argument is a command-line error.
- Without `--detach`, standard output receives exactly the
  [run result](../glossary.json#concept.run-result) as one JSON value; with it, the announcement
  described in [Detached runs](#detached-runs). Diagnostics go to standard error.
- Exit status 0 means the result's status is `ok`, 1 means `blocked` or `failed`, and 2 means the
  command line was malformed or named no known Operation or command, in which case no run is
  created and no result is written.

## Workspace binding

The runner reads `.concorde/workspace.json` at the root of the worktree it starts in:

- When the file is absent, the run is **unbound**: its records directory is that worktree's own
  `.concorde`, its workspace is null, it takes no lock, and it is admitted only when its
  definition allows unbound runs; otherwise it is refused with `binding_required`. An admitted
  unbound run works in its [unbound checkout](#unbound-checkout).
- When the file is present, it must satisfy the binding contract and name as `root` the worktree
  it lies in; otherwise the run is refused with `binding_unreadable`, `binding_invalid` or
  `binding_misplaced`, and its result is written in the worktree's own `.concorde`.
- A bound run's records directory is the binding's `records`, and its run context gives every step
  the workspace's name, goal, Modules, branch and base commit.

The runner never writes the binding.

## Run identity and directory

The runner creates the run identity `r-<YYYYMMDD>T<HHMMSS>-<name>-<8 hex digits>` from the UTC start
time, the definition's name with `-` written as `_`, and random digits, and the run's directory
`<records>/runs/<run-id>/`. The directory holds `result.json`, the run result exactly as printed,
the run progress file, the logs of the checks the run ran, and for a
[detached run](../glossary.json#concept.detached-run) the runner's output `host.out`. Workers keeps
each worker launch's [run record](../glossary.json#concept.run-record) beside it, in the same
[run store](../glossary.json#concept.run-store), and the result lists their identities.

## Runner

| # | Step | Stops the run when |
| --- | --- | --- |
| 1 | Parse the command line, look up the definition and read the workspace binding, which selects the records directory (the worktree's own `.concorde` when the binding is absent or cannot be trusted); only then create the run identity, the run's directory and its run progress file | malformed command line, unknown Operation or command, a directory outside Git (exit 2, the reason on standard error, no result, no directory) |
| 2 | Refuse a binding that could not be read, breaks the binding contract or names another root | an unreadable, invalid or misplaced binding (`failed`) |
| 3 | For a bound run, take the [workspace lock](../glossary.json#concept.workspace-lock), waiting for it up to `--wait` seconds (none by default); for an unbound run, refuse a definition that needs a binding, then create the [unbound checkout](#unbound-checkout) and work in it from here on | `workspace_busy`, `binding_required`, `checkout_unavailable` (`failed`) |
| 4 | Admit the run: settle the Modules, leaving out with `removed-module` evidence each binding Module the workspace no longer registers; check the named Modules against the workspace's registry unless the definition diagnoses the Specs itself; admit the inputs | `modules_removed`, `unknown_module`, `specs_unloadable`, `input_not_admissible` (`failed`) |
| 5 | Execute the definition's steps in order | a step stops the run with a status |
| 6 | Remove an unbound run's checkout, then compose the run result from the step outcomes and check it against the run result contract and, for an `ok` result, the definition's output contract | the result or output is invalid (`failed`, `invalid-output` evidence) |
| 7 | Write `result.json`, mark the run progress file finished, release the lock, print the result and exit | — |

- Each step returns either "continue", with any output and evidence it produced, or "stop", with a
  status, a summary and evidence. Steps of one run share the run context: the workspace binding, the
  worktree the run works in, for an unbound run also the worktree it started in and the commit it
  examines, the records directory, the Modules, the admitted inputs, the output so far, a state the
  definition owns, and the run record of the latest worker launch. The runner never skips, repeats
  or reorders steps; any repetition, such as [resume rounds](../glossary.json#concept.resume-round),
  happens inside one step.
- An exception raised by a step becomes a `failed` result with `host-error` evidence naming the
  step, the error type and message; the cause of its error is a `component` link with the
  exception's type, message and command output, where it was raised and the path of the full
  traceback in the run's directory.
- On `SIGINT` or `SIGTERM` the runner stops its running step, ends every worker process the run
  started through Workers and finishes with a `failed` result with `cancelled` evidence naming the
  signal. Its `cancelled` link names every worker run the run started, with evidence of kind
  `worker-run` pointing at each run's record and
  [progress file](../glossary.json#concept.progress-file), and `worker_runs` lists them: the
  runner learns each worker run's identity when the worker run starts, not when it returns.
- Steps 6 and 7 run whatever happened before them. A refusal in steps 2 to 4 still writes and
  prints a result, with the refusal code as `refused` evidence and an error whose cause is the
  refusal of the workspace binding, the unbound checkout or the run store with its message, such
  as Git's output for a checkout it refused, the run holding the lock of a busy workspace or the
  registered Modules for an unknown one.
- The result is written before the lock is released, so a result always means a workspace free
  for its next run.
- Whenever the status is not `ok`, the runner also writes the
  [error chain](../glossary.json#concept.error-chain), rendered as indented text, to standard error.

## Unbound checkout

An admitted [unbound run](../glossary.json#concept.unbound-run) works in its
[unbound checkout](../glossary.json#concept.unbound-checkout), never in the worktree it started in,
here called its origin:

1. The runner resolves the origin's `HEAD` to a commit and creates a new private directory in the
   system's temporary directory, named `concorde-unbound-…`, holding the checkout
   `<directory>/<run-id>`, made with `git worktree add --detach` of that commit from the origin's
   repository, with none of the repository's Git hooks run. Only Git's administrative files of the
   repository change; no file of the origin and not its index.
2. Each submodule the commit records that the origin has checked out, and whose repository holds
   the recorded commit, is checked out in the checkout the same way, `git worktree add --detach` of
   that commit from the submodule's repository, with the origin's sparse-checkout patterns when
   the origin's checkout is sparse; `submodule` evidence names each. A submodule the origin has not
   checked out, or that Git cannot check out, stays empty, as in a fresh clone, with
   `submodule-absent` evidence naming why.
3. Each relative path of the checked-out project configuration's `workers.runtime` (default
   `.venv` and `node_modules`) that exists in the origin and that Git ignores is linked into the
   checkout as a symbolic link to the origin's, with `environment` evidence; the run's checks and
   workers only read it, the checks inside their read-only boundary. A runtime path Git does not
   ignore is not linked, with `environment-not-linked` evidence, since the commit holds it.
4. From here on the run context's worktree is the checkout: the Specs, the grant, the workers,
   Workers' audit and the steps all work there. The run context keeps the origin, whose `.concorde`
   remains the records directory and whose
   [worker model configuration](../glossary.json#concept.worker-model-configuration) chooses the
   workers' backends and models, and the commit, which the result names as `commit` and the run's
   error link as `… (unbound, <origin> at <commit>)`. `checkout` evidence names the commit and the
   checkout's path.
5. Before the result is composed, however the steps ended, including a refusal, a raised error or
   a cancellation, the runner removes the links, the submodule checkouts and the checkout with
   `git worktree remove --force`, then the temporary directory. A removal Git refuses is done
   directly, deleting the directory and pruning Git's worktree list, and reported with
   `checkout-not-removed` evidence; it never changes the result's status. A runner killed outside
   its control, by `SIGKILL`, leaves the directory to the system's temporary-file cleaning and its
   worktree entry to Git's own pruning.

When the origin's `HEAD` names no commit, or Git refuses the checkout, the run is refused at step 3
with `checkout_unavailable`, whose cause is the `Execution (unbound checkout)` link with Git's
output, and nothing is left behind; the runner never falls back to working in the origin.

## Detached runs

With `--detach` the command checks the command line (a malformed one starts nothing, with exit
status 2), reads the workspace binding to select the records directory as step 1 does, chooses the
run identity, creates the run's directory and starts the runner as a process of its own, in a new
session, handing it the identity, so that the runner records in the directory the command
announces. It then waits until the run progress file exists and prints
`{run_id, kind, name, host_pid, progress, result}` with exit status 0. A runner that ends or has
not written its run progress file within the announcement wait, 60 seconds from its start, is
killed, with its process group, and the command prints the same fields with an `error` link
`detach_failed` naming the end of the runner's output, with exit status 1, so an unannounced runner
never starts its run later.

## Run progress file

The runner writes `<records>/runs/<run-id>/status.json` atomically when the run's directory is
created, before each step and when the result is written:

| Field | Content |
| --- | --- |
| `kind` | `operation` or `command` |
| `run_id`, `name`, `workspace`, `worktree`, `modules` | the run's identity, definition, workspace (null when unbound), the worktree it works in (an unbound run's checkout once it exists) and Modules |
| `commit` | the commit an unbound run examines once its checkout exists; null otherwise |
| `phase` | `running`, then `finished` once `result.json` is written |
| `step` | the step running now, `workspace-lock` while the run waits for the workspace lock, or null |
| `waiting_for` | the run holding the workspace lock while this run waits for it; null otherwise |
| `status`, `summary` | null while running; the result's status and summary once finished |
| `host_pid` | the runner's process identifier, which every worker run it launches records too |
| `started_at`, `updated_at` | UTC times |

A failed write never changes the run.

## Errors

When a run does not end `ok`, the result's `error` is the run's own link of the
[error chain](../contracts.md#contract.concorde.error): the level `operation` for an Operation and
`command` for an execution command, the actor `Operation <name> <run-id> (workspace <workspace>)`,
`Command <name> <run-id> (workspace <workspace>)` or, unbound, `… (unbound, <worktree> at <commit>)`,
without ` at <commit>` when the run was refused before its checkout existed, a code, a
detail naming the workspace, the Modules, the run, the paths and the messages concerned, the reason
the run cannot handle the error, the options it offers with a recommendation, and as causes the
errors it received, unchanged. A step that stops the run builds that link itself; the runner builds
it as follows.

| Error | Code | Reason | Causes |
| --- | --- | --- | --- |
| Refusal before the steps began | `refused` | `decision` for `workspace_busy`; `scope` for `binding_required` and `specs_unloadable`; `environment` for `binding_unreadable` and `checkout_unavailable`; `input` otherwise | the `component` link of `Execution (workspace binding)`, `Execution (unbound checkout)` or `Execution (run store)` with the refusal's code and message |
| A step raised | `host_error` | `capability` | the exception's `component` link |
| Cancelled | `cancelled` | `environment` | none |
| Invalid result or output | `invalid_result` | `capability` | the error the run had, if any |
| A step stopped without an error | `missing_error` | `capability` | none |

Spec tooling reports with [its own error record](../spec-tooling/spec/errors.md), never with a link.
When a Spec tooling error causes a run's error, the step translates it into a `component` link of
the actor `Spec core`: the record's message and location become the detail, its reason becomes the
explanation of why Spec core could not handle it (reason `input`, or `environment` for a
`system_error`), its remediation becomes the option and recommendation, and each of its causes
becomes a nested link the same way. A Check execution or [Issue](../glossary.json#concept.issue)
error, which are subclasses of the Spec tooling error type registered by their own Modules, is
translated the same way.
