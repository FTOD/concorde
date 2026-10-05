# Workers

## Purpose

Workers runs the agent half of level 5, the bottom of Concorde's
[levels of work](../../module.md#the-levels-of-work). It runs one headless worker for one job under
one frozen [grant](../../glossary.json#concept.grant). Its caller hands over the grant as data. The
worker runs on Claude Code or on pi. Workers turns what happened into a
[run record](../../glossary.json#concept.run-record) its caller can trust.

In Concorde, that caller is a step of one of Method's
[Operations](../../glossary.json#concept.operation). Any program may call Workers by handing over
these inputs:

- a grant
- its instructions
- a trace node folder

Each run has its own resources:

- session
- process
- permissions

The run uses the model the worktree's
[worker configuration](../../glossary.json#concept.worker-configuration) chooses. Its
[run directory](../../glossary.json#concept.run-directory) is a
[trace node](../../glossary.json#concept.trace-node) inside the folder its caller gives. Workers
also owns that configuration. The project tracks and edits the configuration directly. Workers
reads the user's [model map](../../glossary.json#concept.model-map).

Workers owns the whole lifecycle of each run:

- the run directory
- the brief
- the launch and [resume rounds](../../glossary.json#concept.resume-round)
- the [write audit](../../glossary.json#concept.write-audit)
- the call of its caller's round validation after each round
- the record

The worker's permissions and environment are its
[agent harness](../../glossary.json#concept.agent-harness). The [Harness](../harness/module.md)
generates the agent harness from the grant for the chosen program.

Workers does none of these things:

- compute the grant
- choose the [task type](../../glossary.json#concept.task-type)
- write the task-specific instructions
- judge whether the worker's work is correct

Workers reads none of these sources:

- a [Spec](../../glossary.json#concept.spec)
- a glossary
- an Operation catalog

Workers runs no check of its own. Its caller's round validation says what needs repair after a
round. Workers never commits. Its boundary guards against scope drift and mistakes, not a
malicious worker.

## Core concepts

A worker run pairs deterministic code with one AI process. The host performs these steps:

- prepare what the worker gets
- launch the worker
- check what the worker did
- keep the record

The run builds on the [grant](../../glossary.json#concept.grant) and its
[context identity](../../glossary.json#concept.context-identity). Both arrive as data in the run's
own [grant input](contracts.md#grant-input). The run also builds on the
[agent harness](../../glossary.json#concept.agent-harness) the Harness generates.

### The host and its worker

Workers is the deterministic management code. It is the **host** of a worker run. The worker it
launches is the AI process. The worker is untrusted in that its claims are proposals. After the
worker ends, only the host performs these actions:

- read Git
- audit
- call its caller's round validation
- record

That is why the run record keeps the worker result separate from host evidence.

### Where a run lives

<a id="concept.run-directory"></a><a id="concept.runtime-directory"></a>

The host creates the **[run directory](../../glossary.json#concept.run-directory)**
`workers/<run-id>/` inside the trace node folder its caller gives. In Concorde, that folder is the
node of the Operation run that launched the worker. The host keeps what analysis needs of the run
there.

The **[runtime directory](../../glossary.json#concept.runtime-directory)** holds what the worker
needs only while it runs. This is a short private directory under `/tmp`. It holds these items:

- The generated configuration of the worker.
- The copies of the credentials.
- The home directory of the worker.
- Its temporary directory.
- Its working directory.

When the run ends, the host removes the runtime directory.

<a id="concept.progress-file"></a>

Throughout, the host keeps the worker run's
**[progress file](../../glossary.json#concept.progress-file)** `status.json` current. The file
shows these details so that an observer sees what the run is doing:

- its phase
- its round
- the worker's latest tool call

The run record, not the progress file, is the run's evidence.

### What the worker gets

A worker runs only in a worktree that lies directly in `.claude/worktrees/` of its repository's
primary worktree. In Concorde, this is a task worktree or an
[unbound checkout](../../glossary.json#concept.unbound-checkout). That one placement tells Workers
where all of the repository's Git metadata is. This holds wherever the repository lies, inside or
outside the user's home.

Before it generates anything, Workers refuses a worker in any other placement. Otherwise, Workers
finds these repository Git administrative paths with read-only Git:

- its common Git directory
- the worktree's own Git directory
- every `.git` entry inside the worktree

[The run mechanics](launch.md#placement) list these paths.

Before the first round, Workers asks the Harness for the worker's configuration from these inputs:

- the frozen grant
- the run's own paths
- the primary worktree
- those Git paths

On Claude Code, this configuration is the
[worker settings](../../glossary.json#concept.worker-settings) with these controls:

- [deny rules](../../glossary.json#concept.deny-rules)
- a [write hook](../../glossary.json#concept.write-hook)
- a Bash sandbox

On pi, this configuration is the permission extension. The Harness also supplies the tool set of
the task type. Workers places the configuration and tool set in the runtime directory's `control/`.
Workers never changes them during the run.

<a id="concept.brief"></a>

The **[brief](../../glossary.json#concept.brief)** is the worker's only instruction. It consists of
its caller's task instructions followed by the boundary Workers appends, as [the brief](#the-brief)
details.

<a id="concept.worker-result"></a>

Every worker ends with a **[worker result](../../glossary.json#concept.worker-result)**.
Whichever the backend, the host validates the worker result against one schema. The result holds
these fields:

- its `status` (`ok`/`blocked`/`failed`)
- a summary
- proposed deletions
- when the worker could not finish, its `error`, the first
  [error chain](../../glossary.json#concept.error-chain) link

Contract: [the worker result contract](contracts.md).

### What the host checks and keeps

<a id="concept.write-audit"></a>

After every round, the **[write audit](../../glossary.json#concept.write-audit)** runs read-only
Git. The audit compares the worktree's changes since the pre-launch snapshot with `rw`. Any change
outside `rw`, or a deletion, is a violation. A violation ends the run `failed`.

<a id="concept.resume-round"></a>

A **[resume round](../../glossary.json#concept.resume-round)** continues the worker's own session
with what its caller's **round validation** reports to repair, so that the worker repairs it within
the same run. The round validation is a callback the caller passes with the request. After every round
whose worker ended `ok` with a clean audit, the host calls the round validation. The callback
answers with the evidence to keep and what to repair
([Round validation](launch.md#round-validation)).
Such evidence includes Concorde's [check results](../../glossary.json#concept.check-result).

<a id="concept.run-record"></a>

The **[run record](../../glossary.json#concept.run-record)** is the worker run's `trace.json`. It
holds these details:

- what the run was given
- the worker result verbatim
- each round's host-observed audit
- each round's host-observed round validation
- each round's host-observed usage

### Two backends from one grant

<a id="concept.worker-backend"></a>

The **[worker backend](../../glossary.json#concept.worker-backend)** is the agent program a worker
runs on, Claude Code or pi. Unless the
[worker configuration](../../glossary.json#concept.worker-configuration) chooses Claude Code for
the worker, the backend is pi. Everything but the agent process is shared:

- the grant
- the brief
- the run directory
- the progress file
- the audit
- the round validation
- the rounds
- the run record

Workers of one Operation on different backends therefore exchange nothing but the structured
results the host validates. On Claude Code, the
[worker settings](../../glossary.json#concept.worker-settings) apply the worker's harness. On pi,
the [permission extension](../../glossary.json#concept.permission-extension) applies it. The
[Harness](../harness/module.md) compares the two surface by surface.

### The worker configuration

<a id="concept.worker-configuration"></a><a id="concept.worker-id"></a>

The **[worker configuration](../../glossary.json#concept.worker-configuration)** of a worktree is
its tracked `.concorde/workers.json`. This is the only source of a worker's model and reasoning
level. It names every model by a **project model name**, such as `gpt-6-astra` or `claude-opus-5-5`.
A project model name depends on no installation. Every worker launch requires the file. A worktree
without it runs no worker. The configuration holds these entries:

- The enabled models, each named by a project model name and each with an optional reasoning level
  of its own.
- A backend, a model and a reasoning level for every worker.
- A backend, a model and a reasoning level for the workers of one Operation.
- A backend, a model and a reasoning level for one worker, by its worker id.
- The limits of every worker launch.
- The runtime paths that workers may read.

For each field, the most specific entry that sets it wins.

The configuration keys its entries by Operation and by
**[worker id](../../glossary.json#concept.worker-id)**. The worker id is the stable name a caller
gives each worker it may launch. To Workers, both the Operation and worker id are labels. When the
caller asks for a worker, it declares both labels. In Concorde, the Operation labels are the names
of the Operations in the [Operation catalog](../../glossary.json#concept.operation-catalog).
The worker ids are the ids each Operation lists.

<a id="concept.model-map"></a>

The **[model map](../../glossary.json#concept.model-map)** is how one machine reaches those models.
It is a JSON file of the user, outside every repository. The map is never committed. The map gives
each project model name its local model id on pi, on Claude Code or on both. Its path is
`~/.config/concorde/models.json`, unless `CONCORDE_MODEL_MAP` or `XDG_CONFIG_HOME` places it
elsewhere. When the map gives a worker's model no id for the worker's backend, the worker is
refused.

## Overview

Three pictures show Workers:

- where it sits between its caller and the providers it relies on
- how one run progresses
- what a run leaves behind

### Its place in the levels of work

Workers carries the agent half of level 5, the bottom of Concorde's
[levels of work](../../module.md#the-levels-of-work). Its own code is not an agent. Workers runs in
its caller's process. Workers launches the one process that is an agent, the headless worker. In
Concorde, the caller's process is the Execution runner's. That process acts on behalf of the
Operation run at level 4.

In Concorde's own flows, only a worker-backed step of one of Method's Operations calls Workers.
The step follows the
[standard worker sequence](../../glossary.json#concept.standard-worker-sequence).
No [execution command](../../glossary.json#concept.execution-command) launches a worker. Nothing
above level 4 launches one. A workflow reaches workers through its Operations. Neither the main
agent nor a [task session](../../glossary.json#concept.task-session) ever starts one.

Below Workers, the worker calls nothing of Concorde's. The worker never performs these actions:

- touch Git
- run an Operation
- start an agent

Between rounds, the Workers host code, not the worker, calls its caller's round validation. What a
program found, such as a failing check, can therefore drive another round inside the same run.

A program that runs no Operation can also call the host. Workers' own tests call it with a request
they build. Such a run names no launching run, so its progress file's `operation_run_id` is null.
The run lies in whatever trace node folder the request names. No Concorde command launches a worker
that way.

Results travel up in one direction. The worker ends with its worker result. Workers keeps the
result verbatim in the run record beside its own evidence. Workers returns the record to its
caller. In Concorde, the caller is the Operation's step. The step turns the record into the
Operation's [run result](../../glossary.json#concept.run-result).

When the worker could not finish, its `error` is the first link of the
[error chain](../../glossary.json#concept.error-chain). Workers adds its own link above that error,
saying why it cannot handle the failure. A [Spec gap](../../glossary.json#concept.spec-gap) or grant
violation is not Workers' to retry. Before the caller adds the next link, Workers adds its link.

A run has these collaborators:

- Method, whose steps call it in Concorde
- Harness, which it relies on
- Tracing, which it relies on

```d2
method: Method
workers: Workers
harness: Harness
tracing: Tracing
method -> workers
workers -> harness
workers -> tracing
```

Workers knows none of its callers. They rely on these properties:

- the run record
- the rule that a worker's result is kept apart from host evidence
- their round validation being called after every clean round

### A normal run

In Concorde, the caller is a worker-backed step of an Operation run. The step runs in the Execution
runner's process. The step chooses these inputs:

- the worktree
- the task type
- the Modules

The step computes the grant through Spec core. For work that changes files, the worktree is a bound
workspace. An [unbound run](../../glossary.json#concept.unbound-run) hands over a grant with no
writable path over the worktree it runs in. That worktree is its
[unbound checkout](../../glossary.json#concept.unbound-checkout), which Workers audits like any
worktree. The step calls Workers with these inputs:

- the worktree
- the trace node folder of its run
- the frozen grant as data
- task instructions for the brief
- its round validation
- the run limits

Workers returns a run record (status `ok`/`blocked`/`failed`). The record keeps the worker result
verbatim beside the host's own evidence.

Take an `implement` run whose grant makes `src/shop/cart.py` and `src/shop/discounts.py` writable
(`rw`). The task level created and bound both files for the run to fill. The grant makes the
[Module](../../glossary.json#concept.module)'s Specs and another Module's `src/shop/pricing.py`
readable (`ro`). This is because a task type that reads code reads the project's whole code. A path
visible by name only (`names`) appears in the grants of the task types that do not read code.
One such task type is `understand`, whose worker sees the bound Modules' implementation files by
name only:

```d2 illustrative
grant: Frozen grant
generate: Generate settings, hook, tools and brief
launch: Launch or resume the worker
audit: Write audit
record: Write the run record
validation: "Caller's round validation\n(in Concorde: configured checks,\nthe step's own validation)"
grant -> generate -> launch -> audit
audit -> record: "violation, timeout, limit, process failure,\ninvalid result, blocked or failed"
audit -> validation: "valid ok result, clean audit"
validation -> launch: "a repair, rounds left"
validation -> record: "nothing to repair,\nor rounds used up"
```

The host performs these steps:

- Generate the worker's harness and brief.
- Launch the worker's program headless in `work/` with a cleared environment.
- Audit every change against `rw`.
- Call the round validation. In an `implement` run, the round validation runs the
  [configured checks](../../glossary.json#concept.configured-check).
- Resume the same session with what the round validation reports to repair, up to three resume
  rounds by default.
- Then perform proposed deletions.
- Write the run record.

The cleared environment passes on only the proxy its model calls go through
([the proxy](launch.md#proxy)). On pi, the default, the host uses `pi -p` with the permission
extension as its only extension ([the pi run mechanics](pi.md#launch)). On Claude Code, the host
uses `claude -p` with these controls ([the run mechanics](launch.md#launch)):

- `bypassPermissions`
- the result schema
- no MCP servers

### What one run leaves behind

The runtime generates the brief. It keeps the progress file. It writes the run record. Both files
sit in the run directory. The record is the run's evidence:

```d2
dir: Run directory
progress: Progress file
record: Run record
audit: Write audit
round: Resume round
result: Worker result
dir -> progress: holds
dir -> record: holds
record -> audit: records
record -> round: records
record -> result: keeps
```

## Details

### Where a run's files live

The run directory lies inside the trace node folder its caller gives, wherever that lies. In
Concorde, that folder is the node of the Operation run that launched the worker. A task's worker
runs are therefore below its runs in the task's [trace](../../glossary.json#concept.trace). An
unbound run's worker runs are never in its throwaway checkout. They are below that run in the
`.concorde` of the worktree it started in. The run directory keeps what analysis needs:

- the run record
- the frozen grant
- the brief
- each round's node with its standard error and checks
- the transcript

The runtime directory holds these directories:

- the host-only `control/`
- the worker's `config/` (`CLAUDE_CONFIG_DIR` or pi's configuration, with the credential copies and
  the session)
- `home/` (`HOME`)
- `tmp/` (`TMPDIR`)
- `work/` (its working directory)

The host-only `control/` holds these parts:

- settings
- hook
- result schema

Before the runtime directory is removed, the transcript moves from `config/` into the run
directory. No credential copy is ever retained. If a transcript cannot be kept or a runtime
directory cannot be removed, the run fails with `cleanup_failed`, never silently.

The progress file also names the process identifier of the process the run runs in. It also names
the identity of the run that launched it. The caller gives that identity. By that identity, an
observer pairs the worker's progress file with the launching run's own progress. In Concorde, this
is Execution's [run progress file](../../glossary.json#concept.run-progress-file). Process
identifiers are not unique across PID namespaces, so they never pair the two.

However a run ends while its host can act, the run ends both its progress file and its run record.
Before an external interruption travels on, the host records the run as `failed` with
`interrupted`. Before that interruption travels on, the host also records the progress file as
finished. Such interruptions include a termination signal or the cancellation of the run that
launched it. No reader therefore sees a worker that runs forever. As soon as the run exists, the
caller learns its identity. The caller can therefore name the run even when it is interrupted
before the run returns.

When `SIGKILL` kills a host outside its control, the host finishes nothing. Its worker run's record
stays `running`. Once the run that launched it is known to have ended,
[Tracing](../../kernel/tracing/module.md) shows the worker run as `lost`. In Concorde, once no
process holds the launching run's [run lock](../../glossary.json#concept.run-lock), Tracing shows
the worker run as `lost`. The runtime directory, with the credential copies, is left to the
system's temporary-file cleaning.

### The brief

The worker has these sources disabled:

- `CLAUDE.md`
- auto memory
- user settings

The brief is therefore all the worker is told.

Workers appends the boundary to its caller's task instructions. The boundary gives
`rw`/`ro`/`names` as absolute paths because the worker's working directory isn't the worktree. The
boundary states these rules:

- The worker's tools take absolute paths. Every path the worker writes in its result is relative
  to the worktree. This is the form every caller's output uses.
- The worker can't delete, only propose deletions.
- A Bash-created file outside `rw` is silently lost.
- A read denial means the path is outside the worker's grant.

When the caller gives the project's own interpreter, the brief also names it as the `python`
first on the worker's `PATH`. This interpreter runs the project's code and tests.

Everything about the job itself is the caller's instructions. In Concorde, Method's
[standard worker sequence](../../glossary.json#concept.standard-worker-sequence) puts these details
there:

- the definitions of the glossary terms the grant carries
- when the glossary is writable, the rule that only the bound Modules' entries may change
- the rule that a promise the [Spec](../../glossary.json#concept.spec) does not state is never
  inferred from code
- what the worker does instead for its task type

The task types have these responses:

- A `review-code` worker reports such behaviour as a `spec-gap` finding.
- An `understand` worker reports the missing promise as a
  [Spec gap](../../glossary.json#concept.spec-gap). The worker ends `ok`.
- A `code-to-spec` worker is told that describing the code it reads is its task. Doubtful intent is
  reported, never promised.
- A `review-spec` or `review-architecture` worker reports a missing promise or a document it lacks
  as a finding. The worker goes on.
- Every other worker returns `blocked`.

On Claude Code, a worker returns its worker result through `--json-schema`. On pi, a worker returns
its worker result as the argument of its `concorde_result` tool. Its `error` carries these details
so the host and [main agent](../../glossary.json#concept.main-agent) can act without asking again:

- the link's code
- detail
- evidence
- attempt
- the reason the worker couldn't handle the error
- options
- recommendation

### Audit, rounds and record

When the write audit finds a violation, the run ends `failed` with every violating path as evidence.
No resume follows. The worktree is left for the main agent, never reverted or committed by the
host. The audit judges whole files against `rw`. A finer judgement of what a writable file may
hold belongs to its caller's round validation. This includes which entries of the shared glossary
a Spec-writing worker may change. In Concorde, the round validation reports every glossary entry a
Module outside the grant owns as a violation. That violation ends the run `failed`
([Method's round validation](../../method/workers.md#the-round-validation)).

A resume round happens only when all these conditions hold:

- The worker ended `ok`.
- The audit was clean.
- The caller's round validation reported something to repair.

For a resume round, the host sends the validation's repair text to the worker's latest session.
In Concorde, the repair text gives the structural errors a Spec-writing worker introduced, or these
details for each failing check:

- the check's identity
- the check's exit code
- the check's log tail

On Claude Code, the host uses `claude -p --resume <session>`. The host tracks the new session id
returned. On pi, the host uses the run's fixed session id. A `blocked`/`failed` result or an audit
violation is never resumed. Those go to the main agent.

When the rounds are used up and the round validation still reports a repair, the outcome depends
on whether the validation asks for failure. If the validation asks for failure, the run ends
`failed` with the code and causes the validation names. In Concorde, this is `checks_failed` with
the last check results. Otherwise, the run leaves the round's result for its caller to judge. Each
round records the round validation's evidence and outcome.

For every run including a refused launch, the host writes the run record at these times:

- when the run directory is created
- after every round
- at the end

The record's metadata hold these details:

- the grant's context identity
- the grant digest
- the settings digest
- the brief digest
- the task type
- the worker id
- the backend
- the model
- the reasoning level

Its content holds these details:

- the tool list
- the transcript path
- the worker result verbatim
- the deletions performed

The record also holds the host's final status with its error link. Each round is a node of its own
below the record. The round's node holds these details:

- its session
- its prompt kind
- its audit
- the round validation's evidence and outcome
- its standard error
- the tokens the agent program reported for it
- the cost the agent program reported for it
- the turns the agent program reported for it

This evidence never restates a worker's claim as fact.

### Resolving the backend

When no entry of the worker configuration chooses a worker's backend, the worker runs on pi. The
main agent and its task sessions run on Claude Code only for now. A Claude Code main agent therefore
runs pi workers, except those the configuration puts on Claude Code.

A worker's backend must be installed. When its command is missing, the worker is refused with
`backend_missing`. The command has one of these forms:

- `claude`
- `pi`
- the path in `CONCORDE_CLAUDE` or `CONCORDE_PI`

The refusal names these details:

- the worker
- the program
- what chose the program
- how to choose the other program for the worker

The worker never falls back to the other program. This refusal comes from resolving the worker's
backend, which the caller does before it calls the host. No worker run and no run record therefore
exists. The caller reports the refusal in its own error, with `backend_missing` as the cause. The
pi command line and environment are in [the pi run mechanics](pi.md).

### Choosing worker models

The worker configuration is tracked by Git like the project's code. Workers never reads these
choices from the developer's own pi or Claude Code settings:

- a worker's model
- a worker's level
- which models may be used

Every developer's workers of a commit therefore run alike. A project model name depends on no
installation. The ids a program takes, such as pi's `local-openai/gpt-6-astra`, are defined by one
machine's own pi or Claude Code configuration. Every worker needs the file. A worktree without one
runs no worker.

When a caller asks for a worker, it declares the Operations and the ids of the workers it may
launch. In Concorde, every Operation lists them in the Operation catalog. Examples are:

- `spec_panel`'s workers, whose ids are listed below
- `spec_review`'s `reviewer` and `checker`
- `worker` for an Operation with one worker

The `spec_panel` worker ids are:

- `reviewer1` to `reviewer5`
- `architect1`
- `architect2`
- `chair`

The same id names the worker in its run record and in the Operation's evidence.

Like pi's and Claude Code's own configuration, one model map serves these places of its user:

- the primary worktree
- every task worktree
- every unbound checkout
- every [test project](../../glossary.json#concept.test-project)

The map says how to reach a model, never which model a worker uses. Like the map, credentials and
pi's provider definitions come from the developer's installation
([the pi run mechanics](pi.md#run-directory)). They never go into Git. When a worker's model has no
id for its program in the map, that worker runs no more than one without a model. Workers never
takes the project model name for the local id.

The worker configuration holds the required `enabled_models`, the models any worker may run on.
Each model is keyed by its project model name. Each model optionally carries the model's own
`reasoning` level. A project model name starts with a letter or digit and uses these characters:

- letters
- digits
- `.`
- `_`
- `-`

No program's own id can therefore stand in for a project model name. One such id is pi's
`provider/model`. The configuration holds these entries:

- a `default`
- an Operation's `default` under `operations`
- an Operation's `workers` under `operations`, one entry per worker id

Each entry may set these fields:

- a `backend`, `pi` or `claude`
- a `model`
- a `reasoning` level

Every model an entry names must be one of `enabled_models`. For each field, the most specific entry
that sets it wins. The entries have this order, including for the backend:

1. the worker's entry
2. the Operation's default
3. the default

An entry that only chooses Claude Code for a worker keeps the model and level it inherits. A
project model name means the same model on either program. The level comes from the first
applicable source in this order:

1. the entry that chose the model or a more specific entry
2. the model's own level in `enabled_models`
3. a less specific entry that sets a level
4. none, which leaves the program's built-in default level

When a worker's entries set no model, the worker is refused. It never runs on its program's
default model. A backend no entry sets is pi. The same file holds the `limits` of every worker
launch and the `runtime` paths. The
[worker configuration contract](contracts.md#contract.workers.worker-configuration) defines the
limits and runtime paths with their defaults. The caller reads them for each launch:

```json
{
  "schema_version": 2,
  "enabled_models": {
    "claude-sonnet-5": {"reasoning": "medium"},
    "claude-opus-5-5": {"reasoning": "high"},
    "gpt-6-astra": {},
    "opus": {}
  },
  "default": {"model": "claude-sonnet-5"},
  "operations": {
    "spec_panel": {
      "workers": {
        "reviewer1": {"model": "claude-opus-5-5"},
        "reviewer2": {"model": "gpt-6-astra", "reasoning": "high"},
        "reviewer3": {"model": "gpt-6-astra"},
        "chair": {"backend": "claude", "model": "opus"}
      }
    }
  },
  "limits": {"timeout_seconds": 1800, "rounds": 3},
  "runtime": [".venv", "node_modules"]
}
```

Except for `spec_panel`'s workers, every worker here runs on pi, on `claude-sonnet-5` at that
model's own `medium`. The `spec_panel` workers run as follows:

- `reviewer1` runs on `claude-opus-5-5` at that model's own `high`.
- `reviewer2` runs on `gpt-6-astra` at `high` from its entry.
- Since neither its entries nor that model set a level, `reviewer3` runs on `gpt-6-astra` at pi's
  built-in default level.
- The `chair` runs on Claude Code with the model the project calls `opus` at Claude Code's own
  default level.

The machine's model map then gives each of those models its local id for the program that runs it:

```json
{
  "schema_version": 1,
  "models": {
    "claude-sonnet-5": {"pi": "anthropic/claude-sonnet-5", "claude": "claude-sonnet-5"},
    "claude-opus-5-5": {"pi": "anthropic/claude-opus-5-5", "claude": "claude-opus-5-5"},
    "gpt-6-astra": {"pi": "local-openai/gpt-6-astra"},
    "opus": {"claude": "opus"}
  }
}
```

When `CONCORDE_MODEL_MAP` names a file by its absolute path, that file is the map. Otherwise, the
map is `concorde/models.json` of the user's XDG configuration directory. When `$XDG_CONFIG_HOME` is
an absolute path, it is that directory. Otherwise, the directory is `~/.config`. The variable lets
a test or a test harness give its workers a map of its own. The map may name models no project
enables. A model may have an id on one program only, as `gpt-6-astra` and `opus` have here. When a
worker runs that model on the other program, the worker is refused.

A caller asks for the choice of one worker of an Operation by its id, in the worktree the run works
on. Workers performs these steps in order:

- Resolve these choices from the worker configuration:
  - the backend
  - the project model name
  - the level
- Check that the backend is installed.
- Read the model map. Take the model's id for that backend.
- Pass the id with `--model` and the level with `--effort` to Claude Code or `--thinking` to pi.

The run record and, in Concorde, the Operation's evidence name these details:

- the project model name
- the local id
- the map the local id came from

The JSON files are the source of truth. A human or an AI edits them directly. There is no editor.
Whenever a worker launches, the validator checks the whole worker configuration. The validator
checks these details:

- structure
- duplicate keys
- Operation and worker names against those the caller declares
- that `enabled_models` is present and not empty and names project model names
- that every model an entry names is enabled
- the limits
- the effective backend's reasoning vocabulary, including a model's own level wherever it applies

That vocabulary is fixed. Claude Code accepts these levels:

- `low`
- `medium`
- `high`
- `xhigh`
- `max`

On pi, the levels are these:

- `off`
- `minimal`
- `low`
- `medium`
- `high`
- `xhigh`
- `max`

An omitted level is always valid. The validator accepts custom model names without requiring any
of these:

- discovery
- installed backends
- credentials

These refusals each say how to repair the file:

- When a worktree lacks the file, the refusal is `config_missing`.
- When an entry names a model outside `enabled_models`, the refusal is `model_not_enabled`, naming
  the entry.
- When a worker's entries set no model, the refusal is `model_unresolved`, naming the worker and
  the entries its model may come from.

Any other malformed file is refused with `config_invalid`, naming the file and problem. Earlier
schema versions are not migrated or ignored. A file of schema version 1, whose models were one
program's local ids, is refused saying how to rename them and map them. A worktree may still have
the untracked `.concorde/worker-models.json` of earlier versions but no `.concorde/workers.json`.
In that case, the worktree is refused with `config_invalid` saying how to move it, rather than
silently run on defaults.

When a worker launches, the map is read whole. The map is never written. When the map is missing,
the refusal is `model_map_missing`, showing what the map holds. When any of these conditions holds,
the refusal is `model_map_invalid`:

- The map is not valid JSON.
- The map has duplicate keys.
- The map has unknown fields.
- The map has a model without an id.
- The map has a name that is not a project model name.
- `CONCORDE_MODEL_MAP` names the map by a relative path.

When a worker's project model name has no id for its backend there, the refusal is `model_unmapped`.
The refusal names these details:

- the worker
- its backend and where the backend came from
- its model and where the model came from
- the map
- the exact entry to add

Each refusal comes before the worker launches. None falls back. The project model name is never
taken as the local id. Nothing else of the user's environment chooses a model.

The configuration reader also checks every worker one Operation may launch against the map at
once. This prevents a run from stopping after its first workers run. Before its first worker
launches, the caller asks for this check. In Concorde, the caller asks when the Operation's run is
admitted. The reader resolves each worker's backend and model. It refuses with one
`model_unmapped`. That refusal names every model and backend the map lacks, with the workers that
would take each. A worker whose entries set no model is left to its own resolution. When those
entries set no model, that resolution refuses the worker with `model_unresolved`. Every refusal
before a run, with its code and reason, is listed in
[the run mechanics](launch.md#refusals-before-a-run).

Because the file is tracked, a [task](../../glossary.json#concept.task) carries the configuration of
its base commit. The tracked file has these consequences:

- A later change on the primary branch never reaches a task already open.
- A change the task makes to its own copy is part of its branch. When the task merges, that change
  reaches the primary branch.
- A change of this file alone may be committed directly on the primary branch for the tasks opened
  after it.

Discovery is separate and advisory. `python3 scripts/available_models.py --backend pi|claude`
(optionally `--json`) works outside Git. On pi, it lists configured credentialed candidates with
`pi --no-extensions --list-models`. Because Claude Code cannot list account entitlements, it offers
an incomplete list of aliases and names from user settings and environment. Discovery makes no
inference API calls. It does not verify access. Custom/offline edits remain possible in these
cases:

- an empty listing
- a missing program
- failed discovery

The candidate output names these details:

- the source
- reasoning levels, with pi's non-reasoning models listing only `off`
- the project model names the model map already gives each candidate as their id on that program

The complete pi listing also names the map's pi ids it does not list, such as one a changed pi
configuration renamed. A missing or unreadable map is reported in the output, never refused.
These are suggestions for the model map and for `enabled_models`, which alone admits a model.

### Failures and repeat runs

Every non-`ok` run carries an error link. The link carries these details:

- what failed
- in which round it failed
- why Workers cannot handle it
- its causes

The causes are one of these sources:

- the worker's own error
- a Claude Code error such as a used-up turn limit
- the links the round validation names, in Concorde every still-failing check with its log's end

Host failures use the same shape with status `failed`. These are host failures:

- a missing/unreadable grant
- a runtime directory a deny rule would cover
- a launch error
- a timeout (the process group is killed)
- a Claude Code error
- a missing/invalid worker result
- an audit violation
- a round validation that could not validate
- a proposed deletion that failed
- a cleanup that failed

Every call starts a fresh run. A failed run is never resumed later. Exact codes/layout are in
[the run mechanics](launch.md). Testable behaviour is in [the scenarios](scenarios.md).

### Inside

```d2
workers: Workers {
  runtime: Worker runtime {
    "workers.py"
    "progress.py"
    "audit.py"
    "runs.py"
    "prompts/workers/common/"
  }
  claude: Claude Code backend {
    "claude_backend.py"
  }
  pi: pi backend {
    "pi_backend.py"
  }
  models: Configuration reader {
    "models.py"
  }
  runtime -> claude: launches
  runtime -> pi: launches
}
```

The runtime drives every run. It hands the agent process to one of two backends. The worker
configuration stands apart because the caller, not the runtime, asks it for the choices.
Before calling the host, the caller asks for these choices:

- a worker's backend
- a worker's model
- a worker's limits

<a id="realization.workers.runtime"></a>The **worker runtime** performs these actions:

- check a worker's placement and find the Git administrative paths
- write the brief
- decide rounds
- call the round validation
- run the write audit
- keep the progress file
- manage run directories/records
- supply the worker prompt snippets every Operation includes, e.g. reporting an error

Since a worker run is where they apply, the runtime's tests under `tests/concorde/harness/workers/`
also exercise these parts:

- the Harness's [worker settings](../../glossary.json#concept.worker-settings)
- the Harness's [write hook](../../glossary.json#concept.write-hook)
- pi path decisions

<a id="realization.workers.claude"></a>The **Claude Code backend** performs these actions:

- place the worker settings and write hook the Harness generates
- launch and resume `claude -p`
- read its event stream

Tests fake `claude` for host behaviour. With `CONCORDE_LIVE_CLAUDE=1`, tests run a real worker for
what only Claude Code enforces.

<a id="realization.workers.pi"></a>The **pi backend** performs these actions:

- check its prerequisites
- prepare the pi configuration directory
- embed the run's policy into the Harness's permission extension
- launch and resume `pi -p`
- read its event stream

The pi backend's tests perform these actions:

- fake `pi` for host behaviour
- run the path decisions under Node
- with `CONCORDE_LIVE_PI=1`, run a real pi worker

<a id="realization.workers.models"></a>The **configuration reader** validates and reads
`.concorde/workers.json` against the Operations and worker ids its caller declares. By its id, the
reader resolves these choices for an Operation's worker:

- the backend
- the project model name
- the level

The reader also resolves the limits and runtime paths of every launch. The reader refuses these
cases:

- a missing file
- a model outside `enabled_models`
- a worker without a model

At launch, the reader checks that the worker's program is installed. It resolves the model's local
id through the model map. The reader refuses these cases:

- a missing map
- a malformed map
- a model the map does not map for the backend

The reader never writes either file. It never reads the developer's own agent settings. The
separate `available_models.py` module and `scripts/available_models.py` entry point discover
advisory candidates, with the project model names the map gives each. Discovery uses neither Git
nor inference probes.

### Why the run is built this way

`bypassPermissions` is used because, even when allowed, `-p` mode's `dontAsk` denies every
Edit/Write outside the working directory. That directory can't be the worktree. Claude Code adds the
working directory and every `--add-dir` to the Bash sandbox's read/write set, defeating per-file
confinement. The brief therefore uses absolute paths. The runtime directory must also avoid any
deny-rule path. Otherwise, the host refuses to launch.

A worker creates a new file only below a `rw` directory. Every exact `rw` path already exists
because a realization binds only files that exist. Before the run, the task level creates and binds
any other new file. The host creates no file for the worker. A worker cannot delete either. It
only proposes deletions. After a clean last round, the host performs the proposed deletions inside
`rw`, judged with their directories' symbolic links resolved.

Resume rounds reuse the worker's context. The spike confirmed this fixes a failing check. On
Claude Code, each resume returns a session id the host continues from. Rounds are only for what
the caller's round validation reports, such as failing checks. A Spec gap or grant violation is a
decision for the main agent or developer, not to retry. The judgement stays with the caller because
it is the job's, not the worker's. That judgement covers these questions:

- which checks prove an `implement` change
- whether a Spec still validates
- which glossary entries a Spec-writing worker may change

Keeping the loop here and the judgement there lets Workers resume any job without knowing these
sources:

- checks
- Specs
- the glossary

On Claude Code, the deny rules withhold only the worktree paths that exist when the host generates
them. A file created later has no rule of its own. Unless a directory rule hides it, the file tools
can read it, a [limit of the Harness](../harness/claude-code.md#deny-rules). The worker cannot use
that file to reach more than its grant. The worker's own writes outside `rw` are refused. Any other
file outside `rw` that appears in the worktree during the run and that Git does not ignore fails
the run through the write audit. What remains is a Git-ignored file another process creates in the
worktree while the run lasts. A Claude Code worker may read that file without anything failing.
On pi, there is no such gap because the permission extension checks every file tool call against
the grant itself.

`--safe-mode`/`--bare` are unused because they'd disable the write hook too. Credentials are a copy
of the user's file in the runtime directory's `config/`. When the run ends, that copy is removed
with the runtime directory. The traces therefore never retain one. An env-var token was untested.
Keeping credentials from the worker itself is future work alongside the outer sandbox. The
[Harness](../harness/module.md) describes the limits.

[Open questions](../../glossary.json#concept.open-question) include whether Bash needs read access
to Claude Code's shell snapshots in `CLAUDE_CONFIG_DIR`. The answer decides if `config/` stays
unreadable. The question awaits the built runtime. Per-task tool lists are v1 defaults in
[the Harness](../harness/claude-code.md#tool-sets) and may change.

## What Workers relies on

Workers relies on two Modules: the Harness beside it in the worker harness part and Tracing in the
kernel part. Everything else Workers needs arrives in the request. In particular, the
[grant](../../glossary.json#concept.grant) arrives frozen as data in its
[grant input](contracts.md#grant-input). The grant arrives with the
[context identity](../../glossary.json#concept.context-identity) its caller computed. Workers relies
on the caller listing every path's level (`rw`/`ro`/`names`, ungranted omitted). Workers never
computes or widens a grant. Before launch, a missing or malformed grant is a host failure. In
Concorde, Method fills the grant input by projecting Spec core's grant onto these fields:

- `task_type`
- `entries`
- `context_identity`

A contract test keeps the projection's shape equal.

<a id="uses-harness"></a>

The **Harness** generates the worker's [agent harness](../../glossary.json#concept.agent-harness)
from these inputs:

- the frozen grant
- the run's paths
- the primary worktree
- the Git administrative paths Workers found

The generated agent harness has these parts:

- on Claude Code, the [worker settings](../../glossary.json#concept.worker-settings) with their
  [deny rules](../../glossary.json#concept.deny-rules) and write hook
- on pi, the [permission extension](../../glossary.json#concept.permission-extension)
- the tool set of the task type

Workers relies on those parts confining the worker's tools to the grant. Workers keeps them
unchanged for every round. When a generated deny rule would cover the run's own directories,
Workers refuses to launch. Through every tool, Workers relies on the Harness hiding every Git
administrative path Workers hands over. Through every tool, Workers also relies on the Harness
hiding the primary worktree but for the way to the worktree. Together with the placement, this
hiding keeps a worker from Git metadata wherever the repository lies. Workers never edits what the
Harness generated.

Depending on the backend, different parts of the Harness reach a worker. The runtime directory
holds what the Harness generated:

```d2
backend: Worker backend
dir: Runtime directory
settings: Harness / Worker settings
extension: Harness / Permission extension
backend -> settings: Claude Code applies
backend -> extension: pi applies
dir -> settings: holds
```

<a id="uses-distribution"></a>

**Distribution** installs the worker harness from the
[part registration](../../glossary.json#concept.part-registration) Workers keeps,
`src/concorde/worker_harness/registration.json`. Workers relies on that file meeting Distribution's
[registration contract](../../distribution/contracts.md#contract.distribution.part-registration).
Workers imports nothing of Distribution.

<a id="uses-tracing"></a>

**Tracing** gives the worker run and each round the shape and place of a
[trace node](../../glossary.json#concept.trace-node). Workers writes both through Tracing's library
at these times:

- at their start
- after each round
- at their end

In their usage, Workers records only what the agent program reported for each round. Workers
reports its failures in the error contract. Workers relies on the
[node contract](../../kernel/tracing/contracts.md#contract.tracing.node). Of its caller's node,
Workers relies on nothing but the folder it is given.

Without launching a run, the [Main session](../../coordination/main-session/module.md) reads
Workers' definitions. The Main session changes the worker configuration by editing it directly.
Through Git, a task worktree carries the worker configuration of its base commit, with nothing
copied.
