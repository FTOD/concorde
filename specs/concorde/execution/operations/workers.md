# How an Operation runs its workers

What an [Operation](../../glossary.json#concept.operation) adds to an ordinary run of the
[Execution runner](../runner.md): the limits of its worker launches, how it settles each worker's
program and model, the
[standard worker sequence](../../glossary.json#concept.standard-worker-sequence) its steps follow,
and the error links that sequence adds. The runner's own steps, refusals and errors are in
[How a run is executed](../runner.md).

## Worker limits {#worker-limits}

The [worker configuration](../../glossary.json#concept.worker-configuration)
`.concorde/workers.json`, read from the worktree the run works in, sets under `limits` the limits of
every worker launch: `timeout_seconds` per round (default 1800), `max_turns` (default 200),
`max_budget_usd` (default none) and `rounds` of resume (default 3); and under `runtime` the paths
Bash may read besides the grant, relative to the workspace or absolute (default `.venv` and
`node_modules`, each only when it exists). An unbound run's checkout links each relative runtime
path Git ignores from the worktree the run started in, as
[How a run is executed](../runner.md#unbound-checkout) describes.

## Worker backend and model

Before each worker launch the step resolves, for the worker the provider names by its id — or, when
it names none, the first id its catalog entry lists — the
[worker backend](../../glossary.json#concept.worker-backend), the model and the reasoning level from
the same worker configuration of the worktree the run works in, which for an
[unbound run](../../glossary.json#concept.unbound-run) is the
[unbound checkout](../../glossary.json#concept.unbound-checkout) of the examined commit, so an
unbound run uses the committed file; the backend is pi unless the configuration chooses Claude Code
for that worker, its Operation or every worker. The validator checks the whole file's structure,
limits and every configured Operation and worker name against the catalog before resolving any
worker. It does not discover models or require credentials; custom/offline model names remain
valid. A malformed or unknown-name entry fails even when it is for a different Operation.

Workers records the Operation, [worker id](../../glossary.json#concept.worker-id), backend and where
it came from, model and level in the run record, and the step adds `worker-model` evidence naming
the worker id, the backend and its source, the model and the level the worker ran with. When the
worker's program is not installed or the configuration file cannot be read, the step stops `failed`
with `worker_model_unavailable` before any worker starts.

## Standard worker sequence

The worker-backed provider step itself computes and freezes the grant and settles the worker's
backend and model; Workers, which never computes a grant, performs the rest. The step hands Workers
the frozen grant, the [task type](../../glossary.json#concept.task-type), the workspace, the records
directory, the brief material, the schema of the provider's own output part, which Workers checks
inside the fixed [worker result](../../glossary.json#concept.worker-result) schema, whether
[configured checks](../../glossary.json#concept.configured-check) run, and the number of
[resume rounds](../../glossary.json#concept.resume-round) (default 3).

| # | Step | Actor | Stops the step when |
| --- | --- | --- | --- |
| 1 | Compute the grant for the task type and Modules from the workspace's Specs through Spec core, lower every writable level to read when the provider withholds writes, and freeze it with its [context identity](../../glossary.json#concept.context-identity) | the step, Spec core | the Specs cannot be loaded or a [Module](../../glossary.json#concept.module) is unknown |
| 2 | Resolve the worker's backend, model and level | the step | the configuration cannot be read or is not valid, or the backend is not installed |
| 3 | Generate the [worker settings](../../glossary.json#concept.worker-settings), the tool list and the brief from the frozen grant | Workers | — |
| 4 | Launch the worker with its own [run directory](../../glossary.json#concept.run-directory) inside the run's [trace node](../../glossary.json#concept.trace-node) and wait for its worker result | Workers | launch error, timeout or a result that fails its schema |
| 5 | Audit the workspace's changes against the grant | Workers | any write outside the grant's writable paths |
| 6 | When the step asks for checks and the worker ended `ok` with a clean audit, run the configured checks of the bound Modules and of every Module that uses one of them outside the worker | Workers | a worker result `blocked` or `failed`: the step ends with the worker's status, without checks or resume |
| 7 | While rounds remain and a check fails, or every check passed or none ran but the step's own validation after the round reports something to repair, resume the same worker with the failures and repeat steps 4 to 6 | Workers | the rounds are used up with a check still failing; a validation still reporting problems leaves the round's result for the step to judge |
| 8 | Write the [run record](../../glossary.json#concept.run-record) | Workers | — |

The stop column ends the productive work, not the record: a round that ran is audited even when it
timed out or returned an invalid result, and Workers writes the run record for every worker run it
was asked to start, including one refused before launch.

An [unbound run](../../glossary.json#concept.unbound-run) whose provider asks for a worker of a
task type that may change files — `specify`, `implement` or `code-to-spec` — without withholding
every writable level is refused by the step with `unbound_write` before step 1, so no grant with a
writable path is ever computed for it. The runner already refuses an unbound run of an Operation
the catalog marks as not unbound; this check guards the Operations that may run unbound, such as a
survey, which withholds every writable level of its `code-to-spec` grant.

The step's outcome maps to the result status as follows; the first matching row wins.

| Outcome | Status |
| --- | --- |
| Grant not computable, worker backend or model not settled, launch error, timeout, invalid worker result, audit violation | `failed` |
| Worker result status `failed` | `failed` |
| Worker result status `blocked` | `blocked` |
| Checks still failing after the last round | `failed` |
| Worker result status `ok`, audit clean, every check passed | `ok`, unless a later provider step stops the run |

The steps and the statuses their exits give, as one flow:

```d2 illustrative
direction: down
step: Provider step {
  grant: 1 Compute and freeze the grant
  model: 2 Resolve backend, model and level
  grant -> model
}
workers: Workers {
  prepare: 3 Settings, tools and brief
  launch: 4 Launch or resume the worker
  audit: 5 Audit against the grant
  checks: "6 Configured checks, when asked; then the step's own validation, when it has one"
  record: 8 Write the run record
  prepare -> launch -> audit
  audit -> checks: worker ok, audit clean
  checks -> launch: "7 a check fails, or validation reports a repair; rounds left"
  checks -> record: "checks pass or none ran; nothing to repair, or validation rounds used up"
  checks -> record: "a check still fails, rounds used up" {style.stroke-dash: 3}
  launch -> record: launch error {style.stroke-dash: 3}
  audit -> record: "violation, timeout, limit reached, invalid result, worker blocked or failed" {style.stroke-dash: 3}
}
ok: ok {shape: oval}
blocked: blocked {shape: oval}
failed: failed {shape: oval}
step.model -> workers.prepare
step.grant -> failed: Specs not loaded, Module unknown {style.stroke-dash: 3}
step.model -> failed: configuration invalid, backend missing {style.stroke-dash: 3}
workers.record -> ok: "worker ok, audit clean, no check failing"
workers.record -> blocked: worker blocked {style.stroke-dash: 3}
workers.record -> failed: "checks still failing, audit violation, launch error, timeout,\nlimit reached, invalid result, worker failed" {style.stroke-dash: 3}
```

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
| Worker backend or model configuration not settled | `worker_model_unavailable` | `input` (`config_invalid`) or `environment` (`backend_missing`) | the `component` link of Workers' model configuration, with its code (`config_invalid` or `backend_missing`) and the file |
| Configured checks cannot run | `checks_unavailable` | `environment` | Check execution's error |
| Worker run ended with an audit violation | `audit_violation` | `permission` | the run record's error |
| Worker run ended with checks still failing | `checks_failed` | `decision` | the run record's error |
| Worker ended `blocked` or `failed` | `worker_blocked`, `worker_failed` | `decision` | the run record's error, whose cause is the worker's link |
| Worker round timed out, or its turn or budget limit was reached | `worker_timeout`, `worker_limit_reached` | `exhausted` | the run record's error |
| Worker result invalid | `worker_result_invalid` | `capability` | the run record's error |
| Any other failure of a worker run | the run record's code | `environment` | the run record's error |

For a worker run the Operation's options are the worker's own options, when it gave any, followed by
the Operation's; each provider's [Spec](../../glossary.json#concept.spec) lists the links its own
steps add.
