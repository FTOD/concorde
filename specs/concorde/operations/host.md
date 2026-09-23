# How the host runs an Operation

The exact behaviour of the `concorde run` command and the Operation host of
[Operations](module.md): the runner, the standard worker sequence and how outcomes become a result
status. The envelope itself is the [result contract](contracts.md#contract.operations.result).

## Command line

```text
concorde run <operation> --task <task-id> [--modules <id>[,<id>…]] [--input <run-id>]… [operation arguments]
```

- The command runs in the primary worktree. `<operation>` is a name from the catalog; `--task`
  is required.
- `--modules` defaults to the task record's Modules. Every named Module must be registered in the
  task worktree.
- Each `--input` names a run of the same task whose status was `ok`; its saved `output` is
  admitted as task material. Any other run is refused with `input_not_admissible`.
- Operation arguments are defined by the provider and parsed by it. An unknown argument is a
  command-line error.
- Standard output receives exactly the result envelope as one JSON value. Diagnostics go to
  standard error.
- Exit status 0 means the result's status is `ok`, 1 means `blocked` or `failed`, and 2 means the
  command line was malformed or named no catalog Operation, in which case no result is written.

## Run identity and directory

The host creates the run identity `r-<YYYYMMDD>T<HHMMSS>-<operation>-<8 hex digits>` from the UTC
start time and random digits, and the run directory `.concorde/runs/<run-id>/` in the primary
worktree. The directory holds `result.json`, the envelope exactly as printed, and the host's own
logs. Workers keeps each worker launch's run record in the primary worktree's `.concorde/runs/`
as well, and the envelope lists their identities. `.concorde/runs/` is ignored by Git.

## Runner

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Parse the command line and look up the catalog entry; only then create the run identity and directory | host | malformed command line or unknown Operation (exit 2, no result, no directory) |
| 2 | Resolve the task and its worktree; check `--modules` and `--input` | host, Tasks, Spec core | unknown task or Module, missing worktree, inadmissible input (`failed`, not recorded in the task) |
| 3 | Begin the run in the task record with the catalog entry's `writes` flag | Tasks | `task_closed` or `task_busy` (`failed`, not recorded in the task) |
| 4 | Execute the provider's steps in order | provider, Workers, Check execution | a step stops the run with a status |
| 5 | Compose the envelope from the step outcomes and check it against the result contract and the provider's output contract | host | the envelope or output is invalid (`failed`, `invalid-output` evidence) |
| 6 | Write `result.json`, finish the run in the task record with the result's status, print the envelope and exit | host, Tasks | — |

- Each provider step returns either "continue", with any output and evidence it produced, or
  "stop", with a status, a summary and evidence. The runner never skips, repeats or reorders
  steps; any repetition, such as resume rounds, happens inside one step.
- An exception raised by a step becomes a `failed` result with `host-error` evidence naming the
  step, the error type and message, and the path of the traceback in the run directory.
- On `SIGINT` or `SIGTERM` the host stops its running step, ends every worker process it started
  through Workers and finishes with a `failed` result with `cancelled` evidence.
- Steps 5 and 6 run whatever happened in step 4. If step 6 cannot write the task record, the result
  is still written and printed, with `record` evidence naming the failure.
- A refusal in steps 2 or 3 still writes and prints a result, with the refusal code as `refused`
  evidence and an escalation from the host.

## Standard worker sequence

A worker-backed provider step hands Workers the task type, the Modules, the task worktree, the
brief material and the result schema of its task type, whether configured checks run, and the
number of resume rounds (default 3). Workers performs:

| # | Step | Stops the step when |
| --- | --- | --- |
| 1 | Compute the grant for the task type and Modules from the task worktree's Specs through Spec core and freeze it with its context identity | the Specs cannot be loaded or a Module is unknown |
| 2 | Pre-create the pending files that the grant makes writable | a pending file cannot be created |
| 3 | Generate the worker settings, the tool list and the brief from the frozen grant | — |
| 4 | Launch the worker in its own run directory and wait for its worker result | launch error, timeout or a result that fails its schema |
| 5 | Audit the task worktree's changes against the grant | any write outside the grant's writable paths |
| 6 | Run the bound Modules' configured checks outside the worker, when the step asks for checks | — |
| 7 | While a check fails and rounds remain, resume the same worker with the failures and repeat steps 5 and 6 | the rounds are used up with a check still failing |
| 8 | Write the run record | — |

The step's outcome maps to the result status as follows; the first matching row wins.

| Outcome | Status | Escalation source |
| --- | --- | --- |
| Grant not computable, launch error, timeout, invalid worker result, audit violation | `failed` | host |
| Checks still failing after the last round | `failed` | host |
| Worker result status `failed` | `failed` | worker |
| Worker result status `blocked` | `blocked` | worker |
| Worker result status `ok`, audit clean, every check passed | `ok`, unless a later provider step stops the run | none |

The host copies the worker result into the envelope's `worker` field unchanged and adds as host
evidence the grant, the context identity, the audit, each check with its command, exit code and
log path, the rounds used, the transcript path and the worker's standard error. It never moves a
statement of the worker into `summary` or `host_evidence`; the summary of a worker-backed result
states the status and what the host verified, and the main agent reads the worker's own account in
`worker`.
