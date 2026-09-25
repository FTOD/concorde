# How the host runs an Operation

The exact behaviour of the `concorde run` command and the Operation host of
[Operations](module.md): the runner, the standard worker sequence and how outcomes become a result
status. The envelope itself is the [result contract](contracts.md#contract.operations.result).

## Command line

```text
concorde run <operation> [--task <task-id>] [--modules <id>[,<id>…]] [--input <run-id>]… [operation arguments]
```

- `<operation>` is a name from the catalog. `--task` is required unless the catalog entry makes the
  task optional; leaving out a required `--task` is a command-line error.
- With a task, `--modules` defaults to the task record's Modules and every named Module must be
  registered in the task worktree. Without a task the run works on the worktree the command runs
  in, `--modules` defaults to none, and every named Module must be registered there.
- Each `--input` names a run whose status was `ok` and that belongs to the same task, or, for a run
  without a task, that had no task either; its saved `output` is admitted as task material. Any
  other run is refused with `input_not_admissible`.
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
| 1 | Parse the command line and look up the catalog entry; only then create the run identity and directory | host | malformed command line, unknown Operation or a directory outside Git (exit 2, the reason on standard error, no result, no directory) |
| 2 | Resolve the task and its worktree, or without a task the primary worktree; check `--modules` and `--input` | host, Tasks, Spec core | unknown task or Module, missing worktree, inadmissible input, a run without a task started in a task's worktree (`failed`, not recorded in the task) |
| 3 | Begin the run in the task record with the catalog entry's `writes` flag; the task worktree's Specs are loaded to check the Modules unless the provider diagnoses them itself (`validate`). A run without a task skips this step | Tasks | `task_closed` or `task_busy` (`failed`, not recorded in the task) |
| 4 | Execute the provider's steps in order | provider, Workers, Check execution | a step stops the run with a status |
| 5 | Compose the envelope from the step outcomes and check it against the result contract and the provider's output contract | host | the envelope or output is invalid (`failed`, `invalid-output` evidence) |
| 6 | Write `result.json`, finish the run in the task record with the result's status, print the envelope and exit | host, Tasks | — |

- Each provider step returns either "continue", with any output and evidence it produced, or
  "stop", with a status, a summary and evidence. Steps of one run share the run context: the task record, the task
  worktree, the Modules, the admitted inputs, the output so far, a `state` dictionary the provider
  owns, and the run record of the latest worker launch. The runner never skips, repeats or reorders
  steps; any repetition, such as resume rounds, happens inside one step.
- An exception raised by a step becomes a `failed` result with `host-error` evidence naming the
  step, the error type and message; the cause of its error is a `component` link with the
  exception's type, message and command output, where it was raised and the path of the full
  traceback in the run directory.
- On `SIGINT` or `SIGTERM` the host stops its running step, ends every worker process it started
  through Workers and finishes with a `failed` result with `cancelled` evidence naming the signal.
- Steps 5 and 6 run whatever happened in step 4. If step 6 cannot write the task record, the result
  is still written and printed, with `record` evidence naming the failure.
- A refusal in steps 2 or 3 still writes and prints a result, with the refusal code as `refused`
  evidence and an error whose cause is the Tasks refusal with its message, such as the known tasks
  for an unknown one or the running Operation for a busy one.
- Whenever the status is not `ok`, the host also writes the error chain, rendered as indented
  text, to standard error.

## Progress file

The host writes `.concorde/runs/<run-id>/status.json` atomically when the run directory is
created, before each provider step and when the result is written:

| Field | Content |
| --- | --- |
| `kind` | `operation` |
| `run_id`, `operation`, `task`, `modules` | the run's identity, Operation, task and Modules |
| `phase` | `running`, then `finished` once `result.json` is written |
| `step` | the provider step running now, or null |
| `status`, `summary` | null while running; the result's status and summary once finished |
| `host_pid` | the host's process identifier, which every worker run it launches records too |
| `started_at`, `updated_at` | UTC times |

A failed write never changes the run.

## Worker settings in the project configuration

The optional `workers` object of `.concorde/config.json`, read from the task worktree, sets the
limits of every worker launch: `timeout_seconds` per round (default 1800), `max_turns` (default 200), `max_budget_usd` (default none), `rounds` of resume
(default 3) and `runtime`, the paths Bash may read besides the grant, relative to the task
worktree or absolute (default `.venv` and `node_modules`, each only when it exists). A refusal of the task before the run begins (`unknown_task`,
`missing_worktree`, `input_not_admissible`, `task_closed`, `task_busy`, `unknown_module`) is
reported as `refused` evidence.

## Worker backend and model

No project setting chooses the agent program or the model of a worker. Before each worker launch
the host takes the [worker backend](../harness/workers/module.md#concept.workers.backend) from its
own environment, which the main session that started the run passed on, and the model and
reasoning level of the Operation's worker role — the role the provider names for the launch, or
its first role — from the run worktree's [worker model
configuration](../harness/workers/module.md#concept.workers.model-configuration). Workers records
the Operation, role, model and level in the run record, and the host adds `worker-model` host
evidence naming the backend, the role, the model and the level the worker ran with. When no main
session program can be found, or the configuration file cannot be read, the step stops `failed`
with `worker_model_unavailable` before any worker starts.

## Runs without a task

A run without a task uses the same runner and envelope with `task` null, and records nothing in any
task record: no task is begun, made busy or reopened. Its worker launches follow the standard worker
sequence with the grant computed from the primary worktree's Specs, and the host refuses, with
`project_scope_write` and before any worker starts, every launch whose grant would keep a writable
path, whatever the provider asks, since only a task's worktree may change. A `specify`,
`implement` or `code-to-spec` launch is therefore refused unless its provider withholds every
writable level, as a survey does. Its results and run
records live in the primary worktree's `.concorde/runs/` like every other run's.

A run without a task is accepted only when the command runs in the primary worktree. Started in a
linked worktree, it is refused before the run begins with `task_worktree_without_task`: its
detail names the worktree and, when a task record names that worktree, the task, and its
recommendation is to run again with `--task <that task>`. In a task's worktree the run must hold
the task's lock, or a writing run of the same task would change files under its audit.

## configure_workers

<a id="configure-workers"></a>

`configure_workers` has one host step, `configure`, and launches no worker:

```text
concorde run configure_workers [--task <task-id>] [--backend claude|pi]
    [--operation <op> [--role <role>]] [--model <model>] [--reasoning <level>] [--allow-unlisted] [--unset]
```

| # | Step | Stops the run when |
| --- | --- | --- |
| 1 | Check the request: `--role` only with `--operation`; `--operation` a catalog Operation with a task type; `--role` one of its roles; `--unset` without `--model` or `--reasoning`; `--allow-unlisted` only with `--model` | the request is impossible (`invalid_request`) |
| 2 | Take the backend from `--backend`, or from the main session that started the run | no main session program is known (`configuration_refused`) |
| 3 | Read the run worktree's configuration file | it cannot be read (`configuration_refused`) |
| 4 | Unless `--unset`, list the candidates of the installed program | the program is missing or does not answer (`configuration_refused`) |
| 5 | With `--model` or `--reasoning`, refuse a model the listing does not show (unless `--allow-unlisted`) or a level the model does not offer, then set the fields on the default, the Operation's entry or the role's entry; with `--unset`, remove that entry; write the file atomically | the value is not offered (`configuration_refused`) |
| 6 | Output the [worker configuration](contracts.md#contract.operations.worker-configuration) | — |

The worktree is the task's with `--task` and otherwise the one the command runs in. The file is
changed only in step 5, and a refused run leaves it as it was. With a task, the run is recorded in
the task record like any run of it but never changes the task's delivered state, since the file is
not part of the task's change.

## Standard worker sequence

A worker-backed provider step hands Workers the task type, the Modules, the task worktree, the
brief material and the result schema of its task type, whether configured checks run, and the
number of resume rounds (default 3). Workers performs:

| # | Step | Stops the step when |
| --- | --- | --- |
| 1 | Compute the grant for the task type and Modules from the task worktree's Specs through Spec core, lower every writable level to read when the provider withholds writes, and freeze it with its context identity | the Specs cannot be loaded or a Module is unknown |
| 2 | Pre-create the pending files that the grant makes writable | a pending file cannot be created |
| 3 | Generate the worker settings, the tool list and the brief from the frozen grant | — |
| 4 | Launch the worker in its own run directory and wait for its worker result | launch error, timeout or a result that fails its schema |
| 5 | Audit the task worktree's changes against the grant | any write outside the grant's writable paths |
| 6 | Run the bound Modules' configured checks outside the worker, when the step asks for checks | — |
| 7 | While a check fails and rounds remain, resume the same worker with the failures and repeat steps 5 and 6 | the rounds are used up with a check still failing |
| 8 | Write the run record | — |

The step's outcome maps to the result status as follows; the first matching row wins.

| Outcome | Status |
| --- | --- |
| Grant not computable, worker backend or model not settled, launch error, timeout, invalid worker result, audit violation | `failed` |
| Checks still failing after the last round | `failed` |
| Worker result status `failed` | `failed` |
| Worker result status `blocked` | `blocked` |
| Worker result status `ok`, audit clean, every check passed | `ok`, unless a later provider step stops the run |

A provider may withhold every writable level of a task type's grant, as the Protocol lets a harness
give less than a type assigns; the frozen grant then has no writable path, the worker gets its
backend's read-only tool set, and the `grant` host evidence says the writes were withheld. Spec core
always computes the full grant of the type; only the host lowers it.

The host copies the worker result into the envelope's `worker` field unchanged and adds as host
evidence the grant, the context identity, the audit, each check with its command, exit code and
log path, the rounds used, the transcript path and the worker's standard error. It never moves a
statement of the worker into `summary` or `host_evidence`; the summary of a worker-backed result
states the status and what the host verified, and the main agent reads the worker's own account in
`worker`.

## Errors

When a run does not end `ok`, the result's `error` is the Operation's own link of the
[error chain](../contracts.md#contract.concorde.error): the level `operation`, the actor
`Operation <name> <run-id> (task <task>)`, a code, a detail naming the task, the Modules, the run,
the paths and the messages concerned, the reason the Operation cannot handle the error, the options
it offers the main agent with a recommendation, and as causes the errors it received, unchanged.
A step that stops the run builds that link itself; the runner and the standard worker sequence
build it as follows.

| Error | Code | Reason | Causes |
| --- | --- | --- | --- |
| Refusal before the run began | `refused` | `decision` for `task_busy`, `scope` for `specs_unloadable`, `input` otherwise | the Tasks refusal |
| Grant not computable | `grant_unavailable` | `scope` | Spec core's error |
| A run without a task asked for a `specify` or `implement` worker | `project_scope_write` | `scope` | none |
| `configure_workers` request impossible | `invalid_request` | `input` | none |
| `configure_workers` refused by the model configuration | `configuration_refused` | the Workers link's reason | the `component` link of Workers' model configuration, with its code (`client_unknown`, `invalid_client`, `config_invalid`, `backend_missing`, `discovery_failed`, `unknown_model` or `unknown_level`), its detail and options |
| Worker backend or model configuration not settled | `worker_model_unavailable` | `input` | the `component` link of Workers' model configuration, with its code (`client_unknown`, `invalid_client` or `config_invalid`) and the file |
| Configured checks cannot run | `checks_unavailable` | `environment` | Check execution's error |
| Worker run ended with an audit violation | `audit_violation` | `permission` | the run record's error |
| Worker run ended with checks still failing | `checks_failed` | `decision` | the run record's error |
| Worker ended `blocked` or `failed` | `worker_blocked`, `worker_failed` | `decision` | the run record's error, whose cause is the worker's link |
| Worker round timed out, or its turn or budget limit was reached | `worker_timeout`, `worker_limit_reached` | `exhausted` | the run record's error |
| Worker result invalid | `worker_result_invalid` | `capability` | the run record's error |
| Any other failure of a worker run | the run record's code | `environment` | the run record's error |
| A step raised | `host_error` | `capability` | the exception's `component` link |
| Cancelled | `cancelled` | `environment` | none |
| Invalid envelope or output | `invalid_result` | `capability` | the error the run had, if any |

For a worker run the Operation's options are the worker's own options, when it gave any, followed by
the Operation's; each provider's Spec lists the links its own steps add.

Spec tooling reports with [its own error record](../spec-tooling/spec/errors.md), never with a link.
When a Spec tooling error causes an Operation's error, the host translates it into a `component`
link of the actor `Spec core`: the record's message and location become the detail, its reason
becomes the explanation of why Spec core could not handle it (reason `input`, or `environment` for a
`system_error`), its remediation becomes the option and recommendation, and each of its causes
becomes a nested link the same way. A Check execution or Issue error, which are subclasses of the
Spec tooling error type registered by their own Modules, is translated the same way.
