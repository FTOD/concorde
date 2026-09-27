# How an Operation runs its workers

What an [Operation](module.md#concept.operations.operation) adds to an ordinary run of the
[Execution runner](../runner.md): the limits of its worker launches, how it settles each worker's
program and model, the standard worker sequence its steps follow, and the error links that
sequence adds. The runner's own steps, refusals and errors are in
[How a run is executed](../runner.md).

## Worker settings in the project configuration

The optional `workers` object of `.concorde/config.json`, read from the workspace, sets the limits
of every worker launch: `timeout_seconds` per round (default 1800), `max_turns` (default 200),
`max_budget_usd` (default none), `rounds` of resume (default 3) and `runtime`, the paths Bash may
read besides the grant, relative to the workspace or absolute (default `.venv` and
`node_modules`, each only when it exists).

## Worker backend and model

No tracked project setting chooses the agent program or the model of a worker. Before each worker
launch the step resolves, for the worker the provider names by its id — or its first worker — the
[worker backend](../workers/module.md#concept.workers.backend), the model and the reasoning level
from the run worktree's [worker model
configuration](../workers/module.md#concept.workers.model-configuration); the backend is pi unless
the configuration chooses Claude Code for that worker, its Operation or every worker. Workers
records the Operation, worker id, backend and where it came from, model and level in the run
record, and the step adds `worker-model` evidence naming the worker id, the backend and its source,
the model and the level the worker ran with. When the worker's program is not installed or the
configuration file cannot be read, the step stops `failed` with `worker_model_unavailable` before
any worker starts.

## Standard worker sequence

A worker-backed provider step hands Workers the task type, the Modules, the workspace, the records
directory, the brief material and the result schema of its task type, whether configured checks
run, and the number of resume rounds (default 3). Workers performs:

| # | Step | Stops the step when |
| --- | --- | --- |
| 1 | Compute the grant for the task type and Modules from the workspace's Specs through Spec core, lower every writable level to read when the provider withholds writes, and freeze it with its context identity | the Specs cannot be loaded or a Module is unknown |
| 2 | Pre-create the pending files that the grant makes writable | a pending file cannot be created |
| 3 | Generate the worker settings, the tool list and the brief from the frozen grant | — |
| 4 | Launch the worker in its own run directory of the run store and wait for its worker result | launch error, timeout or a result that fails its schema |
| 5 | Audit the workspace's changes against the grant | any write outside the grant's writable paths |
| 6 | Run the bound Modules' configured checks outside the worker, when the step asks for checks | — |
| 7 | While a check fails and rounds remain, resume the same worker with the failures and repeat steps 5 and 6 | the rounds are used up with a check still failing |
| 8 | Write the run record | — |

An unbound run never reaches step 1 with a grant that would keep a writable path: the step refuses
it first with `unbound_write`, whatever the provider asks. A `specify`, `implement` or
`code-to-spec` launch of an unbound run is therefore refused unless its provider withholds every
writable level, as a survey does.

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
backend's read-only tool set, and the `grant` evidence says the writes were withheld. Spec core
always computes the full grant of the type; only the step lowers it.

The run keeps the worker result in the result's `worker` field unchanged and adds as its own
evidence the grant, the context identity, the audit, each check with its command, exit code and log
path, the rounds used, the transcript path and the worker's standard error. It never moves a
statement of the worker into `summary` or `host_evidence`; the summary of a worker-backed result
states the status and what the run verified, and the caller reads the worker's own account in
`worker`.

## Errors of the worker sequence

The Operation's link is built as [How a run is executed](../runner.md#errors) describes; the worker
sequence adds these codes.

| Error | Code | Reason | Causes |
| --- | --- | --- | --- |
| Grant not computable | `grant_unavailable` | `scope` | Spec core's error |
| An unbound run asked for a worker whose grant keeps a writable path | `unbound_write` | `scope` | none |
| Worker backend or model configuration not settled | `worker_model_unavailable` | `input` | the `component` link of Workers' model configuration, with its code (`client_unknown`, `invalid_client`, `config_invalid` or `backend_missing`) and the file |
| Configured checks cannot run | `checks_unavailable` | `environment` | Check execution's error |
| Worker run ended with an audit violation | `audit_violation` | `permission` | the run record's error |
| Worker run ended with checks still failing | `checks_failed` | `decision` | the run record's error |
| Worker ended `blocked` or `failed` | `worker_blocked`, `worker_failed` | `decision` | the run record's error, whose cause is the worker's link |
| Worker round timed out, or its turn or budget limit was reached | `worker_timeout`, `worker_limit_reached` | `exhausted` | the run record's error |
| Worker result invalid | `worker_result_invalid` | `capability` | the run record's error |
| Any other failure of a worker run | the run record's code | `environment` | the run record's error |

For a worker run the Operation's options are the worker's own options, when it gave any, followed
by the Operation's; each provider's Spec lists the links its own steps add.
