# How an Operation runs its workers

A [Method](module.md) [Operation](../glossary.json#concept.operation) adds these details to an ordinary
run of the [Execution runner](../execution/runner.md):

- How it admits its workers.
- How it settles each worker's program and model.
- The [standard worker sequence](../glossary.json#concept.standard-worker-sequence) its worker-backed
  steps follow.
- The round validation it gives the worker harness.
- The error links that sequence adds.

The runner's own steps, refusals and errors are in
[How a run is executed](../execution/runner.md). What the worker harness does with what it is given
is in [Workers](../worker-harness/workers/module.md).

## Worker limits {#worker-limits}

The [worker configuration](../glossary.json#concept.worker-configuration) `.concorde/workers.json`
is read from the worktree the run works in. Under `limits`, the configuration sets these limits for
every worker launch:

- `timeout_seconds` per round (default 1800).
- `max_turns` (default 200).
- `max_budget_usd` (default none).
- `rounds` of resume (default 3).

Under `runtime`, it sets the paths Bash may read besides the grant, relative to the workspace or
absolute. The defaults are `.venv` and `node_modules`, each only when it exists. The worker harness
reads and applies the limits. The runtime paths are also what an unbound run's checkout needs.
Every Method Operation that may run unbound gives the runner a **runtime-path resolver** in its
definition. The runner calls the resolver with the checkout's root at this point:

- After creating the [unbound checkout](../glossary.json#concept.unbound-checkout).
- Before linking anything into it.

The resolver reads the worker configuration committed in that checkout. It uses the worker
harness's configuration reader. When the file sets no paths, the resolver returns the defaults.
Otherwise, it returns the file's `runtime` paths. The runner links each relative path Git ignores
from the worktree the run started in into the checkout. It does so as
[How a run is executed](../execution/runner.md#unbound-checkout) describes. The runner itself never
reads the worker configuration. When the committed configuration cannot be read or is not valid,
the resolver returns no path. In that case, nothing is linked. The run's first step,
[admission](#admitting-the-workers), then refuses the run with `worker_model_unavailable` on the
same file.

## Admitting the workers

After the runner admits it, every Method Operation's run begins with the step `check_worker_models`.
This step precedes every other step of its provider. Method puts this step first in every definition
it registers. This way, a run never stops at a later worker for a configuration or model-map
problem that it could have found before its first worker started.

The step reads the worker configuration of the worktree the run works in. For an
[unbound run](../glossary.json#concept.unbound-run), this is the
[unbound checkout](../glossary.json#concept.unbound-checkout) of the examined commit. Thus, an unbound
run uses the committed file. The worker harness knows no Operation. Thus, the step does two checks
the worker harness cannot do:

- Every Operation and [worker id](../glossary.json#concept.worker-id) the configuration names belongs
  to the registered Operations and their worker ids. The installed parts register them. Execution's
  [Operation catalog](../glossary.json#concept.operation-catalog) lists them. Even for another
  Operation, Method's or another part's, the step refuses an entry for a misspelled or removed worker.
  An entry for an Operation another installed part registers stays valid.
- Every worker the Operation may launch can be resolved. The step asks the worker harness's
  configuration reader to check, at once, the whole file's structure and limits and every one of
  those workers against the machine's [model map](../glossary.json#concept.model-map)
  ([Workers](../worker-harness/workers/module.md)).

When any of these conditions holds, the run stops `failed` with `worker_model_unavailable` before
its first worker launches:

- The configuration cannot be read or is not valid.
- The configuration names an unknown Operation or worker.
- The map is missing or unreadable.
- The map lacks the id of a model one of those workers would run on.

The cause is the configuration reader's refusal or Method's own `component` link naming each
unknown name. For the map, the cause is one `model_unmapped` naming every model and backend the map
lacks with the workers that would take each.

Before the first worker starts, the admission thus guarantees exactly three things:

- The configuration is readable and valid.
- Every name it uses is registered.
- For every worker the Operation may launch, when the configuration gives it a model, the map has a
  local id for its backend.

It checks nothing else. As [Worker backend and model](#worker-backend-and-model) says, these failures
can still stop a later worker at its own launch:

- A worker's entries set no model, so its launch is refused with `worker_model_unavailable`.
- A backend is not installed.
- The agent program finds a problem itself, such as missing credentials or an unavailable model.

The admission does not discover models or require credentials. Custom or offline model names remain
valid.

## Worker backend and model

Before each worker launch, the step names the worker by the id its provider gives. When the provider
names none, the step uses the first id its definition lists. The step also names the Operation by
its name. The worker harness uses both labels to select the worker's entry of the configuration.

From the same worker configuration, the worker harness then resolves the
[worker backend](../glossary.json#concept.worker-backend), the model and the reasoning level. The
backend is pi unless the configuration chooses Claude Code at one of these levels:

- That worker.
- Its Operation.
- Every worker.

The worker harness resolves the project model name's local id through the model map. Bound or
unbound alike, the run reads the map from its own environment.

Workers records these details in the run record:

- The Operation.
- The worker id.
- The backend and where it came from.
- The project model name.
- Its local id.
- The model map.
- The level.

The step adds `worker-model` evidence naming these details:

- The worker id.
- The backend and its source.
- The project model name with the local id and the map it came from.
- The level the worker ran with.

When any of these conditions holds, the step stops `failed` with `worker_model_unavailable` before
that worker starts:

- The worker's program is not installed.
- The configuration file cannot be read.
- The model map is missing or unreadable.
- The model map gives the model no id for the backend.

## Standard worker sequence

The worker-backed provider step does the following:

- Computes the grant.
- Freezes the grant.
- Composes the task instructions.
- Supplies the round validation.

Workers, in the worker harness, performs the rest. Workers never computes a grant, reads a Spec or
runs a check of its own.

The step hands Workers these inputs:

- The frozen grant in the worker harness's
  [grant input](../worker-harness/workers/contracts.md#grant-input) format.
- The [task type](../glossary.json#concept.task-type).
- The Operation's name and the worker id.
- The workspace and whether the worker may write there.
- The runtime paths.
- The run's [trace node](../glossary.json#concept.trace-node) folder.
- The task instructions.
- The schema of the provider's own output part. Workers checks it inside the fixed
  [worker result](../glossary.json#concept.worker-result) schema.
- The round validation.
- The number of [resume rounds](../glossary.json#concept.resume-round) (default 3).

| # | Step | Actor | Stops the step when |
| --- | --- | --- | --- |
| 1 | Compute the grant for the task type and Modules from the workspace's Specs through Spec core, lower every writable level to read when the provider withholds writes, which gives the **effective grant**, freeze it with the [context identity](../glossary.json#concept.context-identity) of the computed grant and convert it into the grant input | the step, Spec core | the Specs cannot be loaded or a [Module](../glossary.json#concept.module) is unknown |
| 2 | Compose the task instructions: the provider's prompt, the plain definitions of the glossary terms the bound Modules' documents use, and the rules for a promise the Spec does not state (report it as a [Spec gap](../glossary.json#concept.spec-gap), never infer it) and a path outside the grant | the step, Spec core | — |
| 3 | Hand everything to Workers, which resolves the worker's backend, model and level and generates the [worker settings](../glossary.json#concept.worker-settings), the tool list and the [brief](../glossary.json#concept.brief) | Workers | the configuration cannot be read or is not valid, the worker's entries set no model, the backend is not installed, or the model map is missing, unreadable or gives the model no id for the backend: `worker_model_unavailable` |
| 4 | Launch the worker with its own [run directory](../glossary.json#concept.run-directory) inside the run's trace node and wait for its worker result | Workers | launch error, timeout or a result that fails its schema |
| 5 | Audit the workspace's changes against the grant | Workers | any write outside the grant's writable paths |
| 6 | When the worker ended `ok` with a clean audit, call the step's round validation | Workers, the step | a worker result `blocked` or `failed`: the step ends with the worker's status, without validation or resume |
| 7 | While rounds remain and the round validation reports something to repair, resume the same worker with it and repeat steps 4 to 6 | Workers | the rounds are used up with a check still failing; a validation still reporting problems leaves the round's result for the step to judge |
| 8 | Write the [run record](../glossary.json#concept.run-record), after carrying out the deletions the worker proposed | Workers | — |
| 9 | Check glossary ownership once more, against the workspace as Workers left it, whatever the worker's status | the step | an entry outside the grant added, changed or removed: `failed` with `audit_violation` |

The stop column ends the productive work, not the record. When a round ran, Workers audits it,
even when it times out or returns an invalid result. Workers writes the run record for every
worker run it was asked to start, including one refused before launch.

### The round validation

The round validation is the step's. Workers only calls it. Workers acts on its answer. The
validation checks what the worker's round left in the workspace. For a step that judges it, the
validation also checks the worker result the round returned. It checks in this order:

1. **Glossary ownership.** When the grant makes the project glossary writable, the validation checks
   every glossary entry the round changed, added or removed. When its owner before or after is a
   Module outside the grant, an entry violates ownership. The validation reports the violation as
   `<glossary>#<concept>`. Like an audit violation, this ends the run `failed`. The validation checks
   the glossary by entry because every Module's concepts share that one file.
2. **Configured checks.** When the step asks for them, the step computes the [configured
   checks](../glossary.json#concept.configured-check) from the workspace's Specs through Spec core,
   and Check execution runs them outside the worker. These checks belong to the bound Modules and
   every Module that uses one of them, directly or through further uses. The validation places their
   logs in nodes in the round's folder. Their [check
   results](../glossary.json#concept.check-result), with those logs, are the round's evidence. Every
   failing check is something to repair.
3. **The step's own validation**, when the provider has one and every check passed or none ran.
   Examples include:

   - The structural validation a Spec-writing step runs against its baseline instead of configured
     checks.
   - A review's check that every finding's citations hold, which reads the round's worker result.

   What it reports is something to repair.

It returns the evidence to keep with the round and the text to repair. When nothing needs repair,
the text is empty.

**Glossary ownership after the worker run.** The round validation runs only after a clean `ok`
round. It therefore does not see what a round left in these cases:

- The worker ended `blocked` or `failed`.
- The worker timed out.
- The worker returned an invalid result.

It also does not see the deletions Workers carries out after the last validation. Once Workers
returns, the step compares the glossary before the first round with the glossary as Workers left
the workspace. Whatever the worker's status, the step does so before either event:

- Any later step of its provider.
- The launch of another worker.

When an entry outside the grant was added, changed or removed, the run ends `failed` with
`audit_violation`. This includes a proposed deletion of such an entry. That violation takes
precedence over every other outcome of the worker run. When the worker run had its own error,
that error stays the violation's cause. Thus, the original failure is never lost. Only the round
validation decides whether a round may be resumed, never this check.

**Spec gaps and paths outside the grant are never repaired.** Neither is ever something to repair.
No round validation asks for one. No resume round supplies a promise the Spec does not state or a
path the grant does not give. What such a report means for the run is the Operation's, by its own
contract.

Where the missing meaning or access prevents the work the worker was given, the worker reports it.
In that case, the worker ends `blocked`, and no round validation runs. This happens, for example,
when an `implement` worker needs an unstated promise or a file outside its grant. Where finding and
reporting it is the work, the worker ends `ok` with it in its output. Examples include:

- An `understand` assessment that finds the Specs insufficient.
- A review that records a missing provider document as a finding and goes on.

A grant denial is a path the worker needed but could not read or write. The worker reports a grant
denial as such, never as missing Spec meaning. It never reports a Spec gap as a grant denial.

Before step 1, when both conditions hold, the step refuses an
[unbound run](../glossary.json#concept.unbound-run) with `unbound_write`:

- Its provider asks for a worker of a task type that may change files: `specify`, `implement` or
  `code-to-spec`.
- Its provider does not withhold every writable level.

Thus, the step never computes a grant with a writable path for it. The step tells Workers the
worker may not write. When an Operation's definition does not allow it to run unbound, the runner
already refuses it. This check guards the Operations that may run unbound, such as a survey.
A survey withholds every writable level of its `code-to-spec` grant.

The step's outcome maps to the result status as follows. The first matching row wins.

| Outcome | Status |
| --- | --- |
| Glossary ownership violation found after the worker run (step 9), whatever else happened | `failed` |
| Grant not computable, worker backend or model not settled, launch error, timeout, invalid worker result, audit or glossary ownership violation | `failed` |
| The worker run's record ended `failed` for any other reason, such as Workers' `deletion_failed` or `validation_unavailable` | `failed` |
| Worker result status `failed` | `failed` |
| Worker result status `blocked` | `blocked` |
| Checks still failing after the last round | `failed` |
| Worker result status `ok`, audit clean, every check passed, and the worker run's record ended `ok` | `ok`, unless a later provider step stops the run |

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
ownership: "9 Glossary ownership,\nafter the worker run"
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
workers.prepare -> failed: "configuration invalid, no model,\nbackend missing, model map missing,\nunreadable or without the model's id" {style.stroke-dash: 3}
workers.record -> ownership
ownership -> failed: "an entry outside the grant changed" {style.stroke-dash: 3}
ownership -> ok: "worker ok, audit clean, no check failing"
ownership -> blocked: worker blocked {style.stroke-dash: 3}
ownership -> failed: "checks still failing, audit violation, launch error, timeout,\nlimit reached, invalid result, worker failed" {style.stroke-dash: 3}
```

As the Protocol lets a harness give less than a type assigns, a provider may withhold every writable
level of a task type's grant. The frozen grant then has no writable path. The worker gets its
backend's read-only tool set. The `grant` evidence says the writes were withheld. Spec core always
computes the full grant of the type. Only the step lowers it.

That lowering is the one change between the computed grant and the effective grant the worker
harness receives. It turns `rw` into `ro`. It never does the following:

- Adds a path.
- Raises a level.
- Changes the context identity.

The context identity stays that of the computed grant. Thus, the evidence still names the Specs the
grant came from.

The run keeps the worker result unchanged in the result's `worker` field. It adds these items as its
own evidence:

- The grant.
- The context identity.
- The audit.
- Each check by its id. The id names the configured command. The evidence includes the check's
  status, exit code and log path.
- The rounds used.
- The transcript path.
- The worker's standard error.

Tracing is best-effort for the work, never silent. When the operating system refuses a write of a
trace node below the run, the run adds that write as `trace-write` evidence. The worker run's record
(its `trace_failures`) and each check result name these writes. The evidence identifies each write
by the worker run's or the check's identity. It includes these details:

- The node's file.
- The moment.
- The error.

Whatever the step makes of the worker run's outcome, the run adds this evidence. It does not change
the run's status for it. It never moves a statement of the worker into `summary` or `host_evidence`.
The summary of a worker-backed result states the status and what the run verified. The caller reads
the worker's own account in `worker`, as
[Execution requires](../execution/requirements.md#req.execution.claims-apart) of every run.

## Errors of the worker sequence

The Operation's link is built as [How a run is executed](../execution/runner.md#errors) describes.
The worker sequence adds these codes.

| Error | Code | Reason | Causes |
| --- | --- | --- | --- |
| Grant not computable | `grant_unavailable` | `scope` | Spec core's error |
| An unbound run asked for a worker whose grant keeps a writable path | `unbound_write` | `scope` | none |
| Worker backend or model configuration not settled | `worker_model_unavailable` | `input` (`config_invalid` and the other refusals of the worker configuration) or `environment` (`backend_missing`, `model_map_missing`, `model_map_invalid`, `model_unmapped`) | the `component` link of Workers' model configuration, with its code and the file |
| Configured checks cannot run | `checks_unavailable` | `environment` | Check execution's error |
| Worker run ended with an audit violation, or the round validation or the check after the worker run found a glossary ownership violation | `audit_violation` | `permission` | the run record's error, when the worker run ended with one |
| Worker run ended with checks still failing | `checks_failed` | `decision` | the run record's error |
| Worker ended `blocked` or `failed` | `worker_blocked`, `worker_failed` | `decision` | the run record's error, whose cause is the worker's link |
| Worker round timed out, or its turn or budget limit was reached | `worker_timeout`, `worker_limit_reached` | `exhausted` | the run record's error |
| Worker result invalid | `worker_result_invalid` | `capability` | the run record's error |
| Any other failure of a worker run | the run record's code | `environment` | the run record's error |

For a worker run, the Operation's options are the worker's own options, when it gave any, followed
by the Operation's. Each provider's [Spec](../glossary.json#concept.spec) lists the links
its own steps add.

Spec tooling reports with [its own error record](../spec-tooling/spec/errors.md#contract.spec.error),
never with a link. When a Spec tooling error causes a run's error, the Method step that read the
Specs translates it into a link. Examples of such a step include:

- Step 1 of the worker sequence.
- A step of `task-validation`.
- A step of `scaffold`.

The translation produces a `component` link. Its actor is `Spec core`, or names what the step
asked, such as `Spec core (grant)`. The record's message and location become the detail. Its reason
becomes the explanation of why Spec core could not handle it. The link's reason follows these rules:

- For a `system_error`, the reason is `environment`.
- For an `unexpected_error`, the reason is `capability`.
- Otherwise, the reason is `input`.

The record's remediation becomes the option and recommendation. Each of the record's causes becomes
a nested link the same way. That link is the cause the step keeps under the run's own link.
