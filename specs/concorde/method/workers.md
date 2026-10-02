# How an Operation runs its workers

What a [Method](module.md) [Operation](../glossary.json#concept.operation) adds to an ordinary run of the
[Execution runner](../execution/runner.md): how it admits its workers, how it settles each worker's
program and model, the [standard worker sequence](../glossary.json#concept.standard-worker-sequence)
its worker-backed steps follow, the round validation it gives the worker harness, and the error
links that sequence adds. The runner's own steps, refusals and errors are in
[How a run is executed](../execution/runner.md); what the worker harness does with what it is given
is in [Workers](../worker-harness/workers/module.md).

## Worker limits {#worker-limits}

The [worker configuration](../glossary.json#concept.worker-configuration)
`.concorde/workers.json`, read from the worktree the run works in, sets under `limits` the limits of
every worker launch: `timeout_seconds` per round (default 1800), `max_turns` (default 200),
`max_budget_usd` (default none) and `rounds` of resume (default 3); and under `runtime` the paths
Bash may read besides the grant, relative to the workspace or absolute (default `.venv` and
`node_modules`, each only when it exists). The worker harness reads and applies the limits. The
runtime paths are also what an unbound run's checkout needs: every Method Operation that may run
unbound names, in its definition, the configuration's runtime paths, and the runner links each
relative one Git ignores from the worktree the run started in into the checkout, as
[How a run is executed](../execution/runner.md#unbound-checkout) describes; the runner itself never
reads the worker configuration.

## Admitting the workers

So that a run never stops at a later worker after earlier ones ran, every Method Operation's run
begins, once the runner admitted it and before any other step of its provider, with the step
`check_worker_models`, which Method puts first in every definition it registers. It reads the worker
configuration of the worktree the run works in — for an
[unbound run](../glossary.json#concept.unbound-run), the
[unbound checkout](../glossary.json#concept.unbound-checkout) of the examined commit, so an unbound
run uses the committed file — and does two checks the worker harness cannot do, since it knows no
Operation:

- every Operation and [worker id](../glossary.json#concept.worker-id) the configuration names is one
  of the Operations Method registers and of their worker ids, so that an entry for a misspelled or
  removed worker is refused even when it is for another Operation;
- every worker the Operation may launch can be resolved: the step asks the worker harness's
  configuration reader to check the whole file's structure and limits and every one of those workers
  against the machine's [model map](../glossary.json#concept.model-map) at once
  ([Workers](../worker-harness/workers/module.md)).

When the configuration cannot be read or is not valid, names an unknown Operation or worker, or the
map is missing, unreadable or lacks the id of a model one of those workers would run on, the run
stops `failed` with `worker_model_unavailable` before its first worker launches, its cause the
configuration reader's refusal or Method's own `component` link naming each unknown name: for the
map, one `model_unmapped` naming every model and backend the map lacks with the workers that would
take each. A worker whose entries set no model, and a backend that is not installed, are left to
that worker's own launch. The admission does not discover models or require credentials;
custom or offline model names remain valid.

## Worker backend and model

Before each worker launch the step names the worker by the id its provider gives — or, when it
names none, the first id its definition lists — and the Operation by its name, both as labels the
worker harness uses to select the worker's entry of the configuration. The worker harness then
resolves the [worker backend](../glossary.json#concept.worker-backend), the model and the
reasoning level from the same worker configuration, pi unless the configuration chooses Claude
Code for that worker, its Operation or every worker, and the project model name's local id through
the model map, which the run reads from its own environment, bound or unbound alike.

Workers records the Operation, worker id, backend and where it came from, project model name, its
local id, the model map and the level in the run record, and the step adds `worker-model` evidence
naming the worker id, the backend and its source, the project model name with the local id and the
map it came from, and the level the worker ran with. When the worker's program is not installed, the
configuration file cannot be read or the model map is missing, unreadable or gives the model no id
for the backend, the step stops `failed` with `worker_model_unavailable` before that worker starts.

## Standard worker sequence

The worker-backed provider step computes and freezes the grant, composes the task instructions and
supplies the round validation; Workers, in the worker harness, which never computes a grant, reads
no Spec and runs no check of its own, performs the rest. The step hands Workers the frozen grant in
the worker harness's [grant input](../worker-harness/workers/contracts.md#grant-input) format, the
[task type](../glossary.json#concept.task-type), the Operation's name and the worker id, the
workspace and whether the worker may write there, the runtime paths, the run's
[trace node](../glossary.json#concept.trace-node) folder, the task instructions, the schema of the
provider's own output part, which Workers checks inside the fixed
[worker result](../glossary.json#concept.worker-result) schema, the round validation and the number
of [resume rounds](../glossary.json#concept.resume-round) (default 3).

| # | Step | Actor | Stops the step when |
| --- | --- | --- | --- |
| 1 | Compute the grant for the task type and Modules from the workspace's Specs through Spec core, lower every writable level to read when the provider withholds writes, freeze it with its [context identity](../glossary.json#concept.context-identity) and convert it into the grant input | the step, Spec core | the Specs cannot be loaded or a [Module](../glossary.json#concept.module) is unknown |
| 2 | Compose the task instructions: the provider's prompt, the plain definitions of the glossary terms the bound Modules' documents use, and the rules for a promise the Spec does not state (report it as a [Spec gap](../glossary.json#concept.spec-gap), never infer it) and a path outside the grant | the step, Spec core | — |
| 3 | Hand everything to Workers, which resolves the worker's backend, model and level and generates the [worker settings](../glossary.json#concept.worker-settings), the tool list and the [brief](../glossary.json#concept.brief) | Workers | the configuration cannot be read or is not valid, or the backend is not installed |
| 4 | Launch the worker with its own [run directory](../glossary.json#concept.run-directory) inside the run's trace node and wait for its worker result | Workers | launch error, timeout or a result that fails its schema |
| 5 | Audit the workspace's changes against the grant | Workers | any write outside the grant's writable paths |
| 6 | When the worker ended `ok` with a clean audit, call the step's round validation | Workers, the step | a worker result `blocked` or `failed`: the step ends with the worker's status, without validation or resume |
| 7 | While rounds remain and the round validation reports something to repair, resume the same worker with it and repeat steps 4 to 6 | Workers | the rounds are used up with a check still failing; a validation still reporting problems leaves the round's result for the step to judge |
| 8 | Write the [run record](../glossary.json#concept.run-record) | Workers | — |

The stop column ends the productive work, not the record: a round that ran is audited even when it
timed out or returned an invalid result, and Workers writes the run record for every worker run it
was asked to start, including one refused before launch.

### The round validation

The round validation is the step's, and Workers only calls it and acts on its answer. It checks, in
this order, what the worker's round left in the workspace:

1. **Glossary ownership.** When the grant makes the project glossary writable, every glossary entry
   the round changed, added or removed whose owner, before or after, is a Module outside the grant is
   reported as a violation named `<glossary>#<concept>`, which ends the run `failed` like an audit
   violation; the glossary is checked by entry because every Module's concepts share that one file.
2. **Configured checks**, when the step asks for them: the
   [configured checks](../glossary.json#concept.configured-check) of the bound Modules and of every
   Module that uses one of them, directly or through further uses, which the step computes from the
   workspace's Specs through Spec core, run outside the worker by Check execution; their
   [check results](../glossary.json#concept.check-result), with their logs in nodes the validation
   places in the round's folder, are the round's evidence, and every failing check is something to
   repair.
3. **The step's own validation**, when the provider has one and every check passed or none ran,
   such as the structural validation a Spec-writing step runs against its baseline instead of
   configured checks; what it reports is something to repair.

It returns the evidence to keep with the round and the text to repair, empty when nothing needs
repair. A Spec gap or a path outside the grant is never something to repair: the worker reports it
and ends `blocked`, and no round validation runs.

An [unbound run](../glossary.json#concept.unbound-run) whose provider asks for a worker of a
task type that may change files — `specify`, `implement` or `code-to-spec` — without withholding
every writable level is refused by the step with `unbound_write` before step 1, so no grant with a
writable path is ever computed for it, and the step tells Workers the worker may not write. The
runner already refuses unbound an Operation whose definition does not allow it; this check guards
the Operations that may run unbound, such as a survey, which withholds every writable level of its
`code-to-spec` grant.

The step's outcome maps to the result status as follows; the first matching row wins.

| Outcome | Status |
| --- | --- |
| Grant not computable, worker backend or model not settled, launch error, timeout, invalid worker result, audit or glossary ownership violation | `failed` |
| Worker result status `failed` | `failed` |
| Worker result status `blocked` | `blocked` |
| Checks still failing after the last round | `failed` |
| Worker result status `ok`, audit clean, every check passed | `ok`, unless a later provider step stops the run |

The steps and the statuses their exits give, as one flow:

```d2 illustrative
direction: down
step: Provider step {
  grant: 1 Compute, freeze and convert the grant
  instructions: 2 Compose the task instructions
  grant -> instructions
}
workers: Workers {
  prepare: "3 Backend and model; settings, tools and brief"
  launch: 4 Launch or resume the worker
  audit: 5 Audit against the grant
  record: 8 Write the run record
  prepare -> launch -> audit
}
validation: "6 Round validation (the step's):\nglossary ownership, configured checks\nwhen asked, the step's own validation"
ok: ok {shape: oval}
blocked: blocked {shape: oval}
failed: failed {shape: oval}
step.instructions -> workers.prepare
workers.audit -> validation: worker ok, audit clean
validation -> workers.launch: "7 something to repair; rounds left"
validation -> workers.record: "nothing to repair, or validation rounds used up"
validation -> workers.record: "a check still fails, rounds used up" {style.stroke-dash: 3}
workers.launch -> workers.record: launch error {style.stroke-dash: 3}
workers.audit -> workers.record: "violation, timeout, limit reached, invalid result, worker blocked or failed" {style.stroke-dash: 3}
step.grant -> failed: Specs not loaded, Module unknown {style.stroke-dash: 3}
workers.prepare -> failed: configuration invalid, backend missing {style.stroke-dash: 3}
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

The Operation's link is built as [How a run is executed](../execution/runner.md#errors) describes; the worker
sequence adds these codes.

| Error | Code | Reason | Causes |
| --- | --- | --- | --- |
| Grant not computable | `grant_unavailable` | `scope` | Spec core's error |
| An unbound run asked for a worker whose grant keeps a writable path | `unbound_write` | `scope` | none |
| Worker backend or model configuration not settled | `worker_model_unavailable` | `input` (`config_invalid` and the other refusals of the worker configuration) or `environment` (`backend_missing`, `model_map_missing`, `model_map_invalid`, `model_unmapped`) | the `component` link of Workers' model configuration, with its code and the file |
| Configured checks cannot run | `checks_unavailable` | `environment` | Check execution's error |
| Worker run ended with an audit violation, or the round validation found a glossary ownership violation | `audit_violation` | `permission` | the run record's error |
| Worker run ended with checks still failing | `checks_failed` | `decision` | the run record's error |
| Worker ended `blocked` or `failed` | `worker_blocked`, `worker_failed` | `decision` | the run record's error, whose cause is the worker's link |
| Worker round timed out, or its turn or budget limit was reached | `worker_timeout`, `worker_limit_reached` | `exhausted` | the run record's error |
| Worker result invalid | `worker_result_invalid` | `capability` | the run record's error |
| Any other failure of a worker run | the run record's code | `environment` | the run record's error |

For a worker run the Operation's options are the worker's own options, when it gave any, followed by
the Operation's; each provider's [Spec](../glossary.json#concept.spec) lists the links its own
steps add.
