# Method requirements

These requirements hold for every [Operation](../glossary.json#concept.operation) and [execution command](../glossary.json#concept.execution-command) [Method](module.md) provides; each
child [Module](../glossary.json#concept.module) states the precise behaviour of its own.

## The standard worker sequence

### req.method.workspace-specs — Grants come from the workspace

Every worker-backed step of a Method Operation SHALL compute the grant of a bound run from the Specs of the workspace the run works on, never from the primary worktree's, and the grant of an [unbound run](../glossary.json#concept.unbound-run) from the Specs of its [unbound checkout](../glossary.json#concept.unbound-checkout).

### req.method.models-placed-first — Every worker is placed before the first launches

Every run of a Method Operation SHALL check every worker its Operation may launch against the [worker configuration](../glossary.json#concept.worker-configuration) and the [model map](../glossary.json#concept.model-map) before it launches its first worker, launching none when the configuration names an Operation or [worker id](../glossary.json#concept.worker-id) that no installed part registers or the map gives no local id to a model one of those workers is configured to run on.

The names are checked against every Operation the installed parts register, as Execution's
[Operation catalog](../glossary.json#concept.operation-catalog) lists them, not only Method's, so a
project's own Operations keep their entries. What the admission does not check — a worker the
configuration gives no model, a backend that is not installed, credentials and model availability —
stops only that worker's own launch ([Admitting the workers](workers.md#admitting-the-workers)).

### req.method.grant-as-data — The worker harness receives the grant as data

Every worker-backed step of a Method Operation SHALL hand the worker harness its effective grant, converted into the worker harness's grant input unchanged in its paths and levels, together with the [context identity](../glossary.json#concept.context-identity) of the grant it computed through Spec core.

The effective grant is the computed grant, or, for a provider that withholds writes, the computed
grant with every writable level lowered to read; that narrowing is the only change allowed between
them, never adds a path or raises a level, and keeps the context identity
([Standard worker sequence](workers.md#standard-worker-sequence)).

### req.method.trace-writes-reported — A refused trace write below the run is in its result

A Method run SHALL report, as `trace-write` evidence of its result, every write of the
[trace node](../glossary.json#concept.trace-node) of a worker run it launched, of one of that run's rounds or of a check it ran that the operating
system refused, as Workers and Check execution report it, without changing the run's status for it.

Workers and Check execution report such a failure in their own results
([req.tracing.written-at-start](../kernel/tracing/requirements.md#req.tracing.written-at-start)),
which only the run that called them reads; the run's result is where whoever started it learns that
a node of its trace is missing or stale.

### req.method.glossary-by-entry — The glossary is audited by entry

When a worker's grant names a writable glossary, a Method Operation SHALL end the run `failed` with `audit_violation` for every glossary entry the worker run added, changed or removed, including by a deletion it proposed, whose owner, before or after, is not one of the grant's Modules, whatever status the worker ended with.

The worker harness audits the worktree's files against the grant's `rw` list, which makes the whole
glossary writable or not; which entries of it a worker may change is a question of the Specs, so it
is asked by Method: in the [round validation](workers.md#the-round-validation) after every clean
round, which ends the run without another round, and once more against the workspace as the worker
harness left it, after every worker run, so that neither a round that ended `blocked` or `failed`
nor a deletion carried out after the last validation escapes it.

### req.method.gaps-never-repaired — Spec gaps and grant denials are never repaired

No round validation of a Method Operation SHALL report a [Spec gap](../glossary.json#concept.spec-gap) or a path outside the grant as something to repair.

What the report means for the run is the Operation's own: `blocked` where it prevents the work the
worker was given, `ok` where reporting it is that work, as for an assessment that finds the Specs
insufficient or a review's finding
([Spec gaps and paths outside the grant](workers.md#the-round-validation)).

## The brownfield workflow

These obligations fix the procedure [The brownfield workflow](brownfield.md) explains; the machinery
they run on, [step keys](../glossary.json#concept.step-key), modes, answers and the report, is
[Workflows](../workflows/requirements.md)'.

### req.method.brownfield-order — The steps run in their fixed order

The [brownfield workflow](../glossary.json#concept.brownfield-workflow) SHALL run, one run at a time in its bound workspace, `survey` of its Module, then `scaffold` of that survey, then one `code_to_spec` per created Module and last of its Module, then `spec_review` of its Module and the created Modules, then `task-validation`, then `delivery --adoption`, starting each only when the rules of req.method.brownfield-stops let the procedure go on.

### req.method.brownfield-providers-first — Providers are described before their consumers

The brownfield workflow SHALL describe the created Modules in the order of the `uses` among them that the scaffold hands it, condensed into strongly connected groups: each time, of the groups whose used groups are all described, the one whose first Module the scaffold lists first, and the Modules of one group in the order the scaffold lists them.

Without a cycle among the created Modules every group is one Module, so each is described after
every created Module it uses. Modules that use each other form one group: one of them is described
before a Module it uses, and its worker reads that Module's stub or description as it stands then.
Every created Module is still described once, and the surveyed Module last.

### req.method.brownfield-stops — The procedure stops where its mode says

The brownfield workflow SHALL end, going straight to its report, after a survey or scaffold that did not end `ok`, after a task validation that did not end `ok` or declared its workspace not ready, after a survey whose [decision points](../glossary.json#concept.decision-point) its answers do not settle in interactive mode, and, in interactive mode only, after a `code_to_spec` that did not end `ok` or left [open questions](../glossary.json#concept.open-question) its answers do not settle and after a `spec_review` that did not end `ok`.

In no-ask mode a `code_to_spec` or `spec_review` that did not end `ok` does not end the procedure:
the Module keeps its stub or partial description, task validation decides whether the workspace can
still be delivered, and the report names the problem
([Workflows](../workflows/requirements.md#req.workflows.no-ask-describe-continues)).

### req.method.brownfield-last-step — Delivery is the procedure's last step

The brownfield workflow's script SHALL name `delivery` as its procedure's last step, so that its [workflow result](../glossary.json#concept.workflow-result) is `ok` only when a delivery ended `ok`.

## Optional integrations

The review Operations whose findings may become Issues are `spec_review`, `spec_panel` and
`code_review`. `plan_review` judges a plan the task level wrote, with findings identified within its
run and judged blocking or advisory rather than by [Issue tier](../glossary.json#concept.issue-tier); its findings stay in its report and
never become Issues, whatever parts are installed.

### req.method.issues-optional — Review verdicts do not need the issues part

`spec_review`, `spec_panel` and `code_review` SHALL derive their verdict whether or not the issues part is installed.

### req.method.findings-kept — Every review finding stays in the run result

`spec_review`, `spec_panel` and `code_review` SHALL return every finding they report in their [run result](../glossary.json#concept.run-result), whether or not the issues part is installed.

### req.method.issues-where-installed — Findings become Issues only where Issues are installed

`spec_review`, `spec_panel` and `code_review` SHALL report their findings as [Issues](../glossary.json#concept.issue) where the issues part is installed.

Each review's own [Spec](../glossary.json#concept.spec) gives the shape.

### req.method.issues-absent-stated — Findings not recorded as Issues are said to be so

`spec_review`, `spec_panel` and `code_review` SHALL state in their result, where the issues part is not installed, that the findings were not recorded as Issues.

That statement is how the [optional integration](../glossary.json#concept.optional-integration)
rule of the root ([req.concorde.absent-part-stated](../requirements.md#req.concorde.absent-part-stated))
applies to them; the findings stay in the run result with their tiers.
