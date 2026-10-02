# Workers

## Purpose

Workers runs the agent half of level 5, the bottom of Concorde's [levels of
work](../../module.md#the-levels-of-work): one headless worker for one job under one frozen
[grant](../../glossary.json#concept.grant), on Claude Code or on pi, turning what happened into a
[run record](../../glossary.json#concept.run-record) the
[Operation](../../glossary.json#concept.operation) that launched it can trust. Each run is its own
session, its own process and its own permissions, on the model the worktree's [worker
configuration](../../glossary.json#concept.worker-configuration) chooses, and its [run
directory](../../glossary.json#concept.run-directory) is a [trace
node](../../glossary.json#concept.trace-node) inside the node of the Operation run that launched it. Workers
also owns that configuration, which the project tracks and edits directly. Of each run it owns the whole lifecycle: the run directory, the
brief, the launch and [resume rounds](../../glossary.json#concept.resume-round), the [write
audit](../../glossary.json#concept.write-audit), the checks after each round and the record. The
worker's permissions and environment are its [agent
harness](../../glossary.json#concept.agent-harness), which the [Harness](../../harness/module.md)
generates from the grant for the chosen program. Workers does not compute the grant, choose the
[task type](../../glossary.json#concept.task-type) or write the task-specific brief, and never
commits or judges whether the worker's work is correct. Its boundary guards against scope drift and
mistakes, not a malicious worker.

## Core concepts

A worker run pairs deterministic code with one AI process: the host prepares what the worker gets,
launches it, checks what it did and keeps the record. It builds on the
[grant](../../glossary.json#concept.grant) and [context
identity](../../glossary.json#concept.context-identity) of Spec core and on the
[agent harness](../../glossary.json#concept.agent-harness) of the Harness.

### The host and its worker

Workers is the deterministic management code, the **host** of a worker run; the worker it launches
is the AI process. The worker is untrusted in that its claims are proposals: only the host reads
Git, audits, runs checks and records, after the worker ends — that is why the run record keeps the
worker result separate from host evidence.

### Where a run lives

<a id="concept.run-directory"></a><a id="concept.runtime-directory"></a>

The host creates the **[run directory](../../glossary.json#concept.run-directory)**
`workers/<run-id>/` inside the trace node of the Operation run that launched it, and keeps there
what analysis needs of the run. What the worker needs only while it runs is in its **[runtime
directory](../../glossary.json#concept.runtime-directory)**, a short private directory under `/tmp`
that the host removes when the run ends.

<a id="concept.progress-file"></a>

Throughout, the host keeps the worker run's
**[progress file](../../glossary.json#concept.progress-file)** `status.json` current with its phase,
its round and the worker's latest tool call, so that an observer sees what the run is doing. The run
record, not the progress file, is the run's evidence.

### What the worker gets

A worker runs only in a worktree that lies directly in `.claude/worktrees/` of its repository's
primary worktree, a task worktree or an
[unbound checkout](../../glossary.json#concept.unbound-checkout): that one placement tells Workers
where all of the repository's Git metadata is, wherever the repository lies, inside or outside the
user's home. Workers refuses a worker in any other placement before it generates anything, and
otherwise finds the repository's Git administrative paths with read-only Git, its common Git
directory, the worktree's own and every `.git` entry inside it, as
[the run mechanics](launch.md#placement) list them.

Before the first round Workers asks the Harness for the worker's configuration from the frozen
grant, the run's own paths, the primary worktree and those Git paths: on Claude Code the [worker
settings](../../glossary.json#concept.worker-settings) with their [deny
rules](../../glossary.json#concept.deny-rules), [write
hook](../../glossary.json#concept.write-hook) and Bash sandbox, on pi the permission
extension, and the tool set of the task type. It places them in the runtime directory's `control/`
and never changes them during the run.

<a id="concept.brief"></a>

The **[brief](../../glossary.json#concept.brief)** is the worker's only instruction: the
Operation's task instructions followed by the boundary Workers appends, as [the
brief](#the-brief) details.

<a id="concept.worker-result"></a>

Every worker ends with a **[worker result](../../glossary.json#concept.worker-result)** that the
host validates against one schema, whichever the backend: its `status` (`ok`/`blocked`/`failed`), a
summary, proposed deletions and, when it could not finish, its `error`, the first [error
chain](../../glossary.json#concept.error-chain) link. Contract: [the worker result
contract](contracts.md).

### What the host checks and keeps

<a id="concept.write-audit"></a>

The **[write audit](../../glossary.json#concept.write-audit)** runs read-only Git after every round,
comparing the worktree's changes since the pre-launch snapshot with `rw`. Any change outside `rw`,
or a deletion, is a violation, which ends the run `failed`.

<a id="concept.resume-round"></a>

A **[resume round](../../glossary.json#concept.resume-round)** continues the worker's own session
with what still needs repair, a failing configured check or what the caller's own validation
reports, so that the worker repairs it within the same run.

<a id="concept.run-record"></a>

The **[run record](../../glossary.json#concept.run-record)** is the worker run's `trace.json`: what
the run was given, the worker result verbatim, and each round's audit, checks and usage, which the
host observed itself.

### Two backends from one grant

<a id="concept.worker-backend"></a>

The **[worker backend](../../glossary.json#concept.worker-backend)** is the agent program a worker
runs on, Claude Code or pi: pi unless the [worker
configuration](../../glossary.json#concept.worker-configuration) chooses Claude Code for the worker.
Everything but the agent process is shared: the grant, the brief, the run directory, the progress
file, the audit, the checks, the rounds and the run record, so workers of one Operation on different
backends exchange nothing but the structured results the host validates. On Claude Code the
worker's harness is applied by its [worker settings](../../glossary.json#concept.worker-settings),
on pi by the [permission extension](../../glossary.json#concept.permission-extension); the
[Harness](../../harness/module.md) compares the two surface by surface.

### The worker configuration

<a id="concept.worker-configuration"></a><a id="concept.worker-id"></a>

The **[worker configuration](../../glossary.json#concept.worker-configuration)** of a worktree is
its tracked `.concorde/workers.json`, the only source of a worker's model and reasoning level. It
names every model by a **project model name**, such as `gpt-6-astra` or `claude-opus-5-5`, that
depends on no installation, and keys its entries by **[worker
id](../../glossary.json#concept.worker-id)**, the stable name the [Operation
catalog](../../glossary.json#concept.operation-catalog) gives each worker an Operation may launch.

<a id="concept.model-map"></a>

The **[model map](../../glossary.json#concept.model-map)** is how one machine reaches those models:
a JSON file of the user, outside every repository and never committed, that gives each project
model name its local model id on pi, on Claude Code or on both.

## Overview

Three pictures show Workers: where it sits between the Operation that calls it and the providers it
relies on, how one run progresses, and what a run leaves behind.

### Its place in the levels of work

Workers carries the agent half of level 5, the bottom of Concorde's
[levels of work](../../module.md#the-levels-of-work). Its own code is not an agent: it runs in the
Execution runner's process, on behalf of the Operation run at level 4 that called it, and launches
the one process that is, the headless worker. Only a worker-backed step of an Operation calls it in
Concorde's own flows —
the [standard worker sequence](../../glossary.json#concept.standard-worker-sequence) of
[Operations](../operations/module.md) and the providers that run workers, such as Understanding,
Specification, Implementation, Code review, Adoption and Spec review. No
[execution command](../../glossary.json#concept.execution-command) launches a worker, and nothing
above level 4 does: a workflow reaches workers through its Operations, and neither the main agent
nor a [task session](../../glossary.json#concept.task-session) ever starts one. Below it, the worker
calls nothing of Concorde's: it never touches Git, runs an Operation or starts an agent. Between
rounds the Workers host code, not the worker, calls Check execution, so that a failing check can
drive another round inside the same Operation.

The host can also be called directly, without an Operation run, as Workers' own tests call it with
a request they build: such a run has no Operation run to name, so its progress file's
`operation_run_id` is null, and when the request names no trace node folder its run directory lies
in the unbound runs of the worktree's `.concorde`. No Concorde command launches a worker that way.

Results travel up in one direction. The worker ends with its worker result; Workers keeps it
verbatim in the run record beside its own evidence and returns the record to the Operation's step,
which turns it into the Operation's [run result](../../glossary.json#concept.run-result). When the
worker could not finish, its `error` is the first link of the
[error chain](../../glossary.json#concept.error-chain), and Workers adds its own link above it
saying why it cannot handle the failure — a [Spec gap](../../glossary.json#concept.spec-gap) or
grant violation is not its to retry — before the Operation adds the next.

A run's collaborators: the Operations that call it and the providers it relies on, among them
Operations itself for its catalog.

```d2
operations: Operations
workers: Workers
spec: Spec core
harness: Harness
checks: Check execution
execution: Execution
tracing: Tracing
operations -> workers
workers -> spec
workers -> harness
workers -> checks
workers -> execution
workers -> tracing
workers -> operations
```

The Operation providers and Spec review use this Module; the worker runtime knows none of
them. They rely on the run record and on the rule that a worker's result is kept apart from host
evidence. The configuration validator looks at the Operation catalog when a worker launches.

### A normal run

The caller is a worker-backed step of an Operation run, in the Execution runner's process, that has
chosen the worktree, task type and Modules and asked Spec core for the grant. For work that changes
files this is a bound workspace; an [unbound run](../../glossary.json#concept.unbound-run) can
launch only a reading worker over the worktree it runs in, its
[unbound checkout](../../glossary.json#concept.unbound-checkout), which Workers audits like any
worktree. The step calls Workers with the worktree,
the trace node folder of its run, the frozen grant and context identity, task instructions for the
brief, checks to run after the worker, and run limits — getting back a run record (status
`ok`/`blocked`/`failed`) with the worker result kept verbatim beside the host's own evidence.

Take an `implement` run whose grant makes `src/shop/cart.py` and `src/shop/discounts.py`, which the
task level created and bound for the run to fill, writable (`rw`), and the
[Module](../../glossary.json#concept.module)'s Specs and another Module's `src/shop/pricing.py`
readable (`ro`), since a task type that reads code reads the project's whole code. A path visible by
name only (`names`) appears in the grants of the task types that do not read code, such as
`understand`, whose worker sees the bound Modules' implementation files by name only:

```d2 illustrative
grant: Frozen grant
generate: Generate settings, hook, tools and brief
launch: Launch or resume the worker
audit: Write audit
record: Write the run record
checks: Run configured checks
grant -> generate -> launch -> audit
audit -> record: "violation, timeout, limit, process failure,\ninvalid result, blocked or failed"
audit -> checks: "valid ok result, clean audit"
checks -> launch: "a check fails or validation\nreports a repair, rounds left"
checks -> record: "checks pass and nothing to repair,\nor rounds used up"
```

The host generates the worker's harness and brief, launches the worker's program headless in
`work/` with a cleared environment, which passes on only the proxy its model calls go through
([the proxy](launch.md#proxy)) — on pi, the default, `pi -p` with the permission extension as
its only extension ([the pi run mechanics](pi.md#launch)); on Claude Code `claude -p` with
`bypassPermissions`, the result schema and no MCP servers ([the run mechanics](launch.md#launch)) —
audits every change against `rw`, runs checks through Check execution, resumes the same session when
a check fails, up to three resume rounds by default, then performs proposed deletions and writes the
run record.

### What one run leaves behind

The runtime generates the brief, keeps the progress file and writes the run record; both files sit
in the run directory, and the record is the run's evidence:

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

The run directory lies inside the trace node of the Operation run that launched it, wherever that
run's node lies, so a task's worker runs are found below its runs in the task's
[trace](../../glossary.json#concept.trace), and an unbound run's below it in the `.concorde` of the
worktree it started in, never in its throwaway checkout. It keeps what analysis needs: the run
record, the frozen grant, the brief, each round's node with its standard error and checks, and the
transcript. The runtime directory holds the host-only `control/` (settings, hook, result schema),
the worker's `config/` (`CLAUDE_CONFIG_DIR` or pi's configuration, with the credential copies and
the session), `home/` (`HOME`), `tmp/` (`TMPDIR`) and `work/` (its working directory). The
transcript is moved from `config/` into the run directory before the runtime directory is removed,
so no credential copy is ever retained.

The progress file also names the process identifier of the Execution runner the run runs in and the
identity of the Operation run that launched it, by which an observer pairs it with that run's own
[run progress file](../../glossary.json#concept.run-progress-file); process identifiers are not
unique across PID namespaces, so they never pair the two. Every run ends both its progress file and
its run record, however it ends while its host can act: a run interrupted from outside, such as by
a termination signal or the cancellation of the Operation that launched it, is recorded as `failed`
with `interrupted` and its progress file as finished before the interruption travels on, so no
reader sees a worker that runs forever. The launching Operation learns the run's identity as soon
as the run exists, so it can name the run even when it is interrupted before the run returns. A
host killed outside its control, by `SIGKILL`, finishes nothing: its worker run's record stays
`running`, which [Tracing](../../tracing/module.md) shows as `lost` once no process holds the
[run lock](../../glossary.json#concept.run-lock) of the run that launched it, and its runtime
directory, with the credential copies, is left to the system's temporary-file cleaning.

### The brief

`CLAUDE.md`, auto memory and user settings are disabled, so the brief is all the worker is told. To
the Operation's task instructions Workers appends the boundary: `rw`/`ro`/`names` as absolute paths
(its working directory isn't the worktree), with the rule that its tools take absolute paths while
every path it writes in its result is relative to the worktree, the form every Operation's output
uses; the definitions of the terms its grant carries, and,
when the glossary is writable, that only the bound Modules' entries may change; that it can't
delete, only propose deletions; that a Bash-created file outside `rw` is silently lost; that a read
denial means the path is outside its grant; and that a promise the
[Spec](../../glossary.json#concept.spec) does not state is never inferred from code. What the worker
does instead depends on its task type: a `review-code` worker reports such behaviour as a
`spec-gap` finding, an `understand` worker reports the missing promise as a [Spec
gap](../../glossary.json#concept.spec-gap) and ends `ok`, a `code-to-spec` worker is told that
describing the code it reads is its task and that doubtful intent is reported, never promised, and
a `review-spec` or `review-architecture` worker reports a missing promise or a document it lacks as
a finding and goes on, ending `blocked` only when it cannot review at all, since the review's own
instructions say how it reports such a gap; every other worker returns `blocked`. When the caller
gives the project's own interpreter, the brief also names it as the `python` first on the worker's
`PATH`, to run the project's code and tests with.

A worker returns its worker result through `--json-schema` on Claude Code and as the argument of its
`concorde_result` tool on pi. Its `error` carries the link's code, detail, evidence, attempt, the
reason it couldn't handle the error, options and recommendation, so the host and [main
agent](../../glossary.json#concept.main-agent) can act without asking again.

### Audit, rounds and record

A violation of the write audit ends the run `failed` with every violating path as evidence, no
resume follows, and the worktree is left for the main agent — never reverted or committed by the
host. The project glossary is audited by entry, because every Module's concepts share that one
file: the snapshot keeps its bytes, and each entry a round added, changed or removed although a
Module outside the grant owns it, before or after, is a violation named `<glossary>#<concept>` with
both owners.

A resume round happens only when the worker ended `ok`, the audit was clean, and a check failed or,
once the checks pass, the caller's own validation after the round reported something to repair: the
host sends each failure's identity, exit code and log tail, or the validation's text, to the
worker's latest session — on Claude Code with `claude -p --resume <session>`, tracking the new
session id returned, on pi with the run's fixed session id. A Spec-writing Operation uses the
validation to have its worker repair the structural errors it introduced. A `blocked`/`failed`
result or an audit violation is never resumed — those go to the main agent; when the rounds are used
up and a check still fails, the run ends `failed` with the last check results, while a validation
still reporting problems leaves the round's result for its caller to judge. Each round records its
validation outcome.

The run record is written when the run directory is created, after every round and at the end, for
every run including a refused launch. Its metadata hold the grant's context identity, the grant,
settings and brief digests, the task type, worker id, backend, model and reasoning level; its
content the tool list, transcript path, the worker result verbatim and the deletions performed; and
the host's final status with its error link. Each round is a node of its own below it, with its
session, prompt kind, audit and [check results](../../glossary.json#concept.check-result), its
standard error, and the tokens, cost and turns the agent program reported for it — evidence that
never restates a worker's claim as fact.

### Resolving the backend

When no entry of the worker configuration chooses a worker's backend, the worker runs on pi,
although the main agent and its task sessions run on Claude Code only for now: a Claude Code main
agent so runs pi workers unless the configuration chooses Claude Code for some of them. A worker's
backend must be installed: when its command (`claude` or `pi`, or the path in `CONCORDE_CLAUDE` or
`CONCORDE_PI`) is missing, the worker is refused with `backend_missing`, naming the worker, the
program and what chose it, and how to choose the other program for it; it never falls back to the
other program. This refusal comes from resolving the worker's backend, which the Operation's step
does before it calls Workers, so no worker run and no run record exists; the step reports it in its
own error, with `backend_missing` as the cause. The pi command line and environment are in [the pi
run mechanics](pi.md).

### Choosing worker models

The worker configuration is tracked by Git like the project's code: Workers never reads a worker's
model or level, or which models may be used, from the developer's own pi or Claude Code settings,
so every developer's workers of a commit run alike. A project model name depends on no installation,
since the ids a program takes, such as pi's `local-openai/gpt-6-astra`, are defined by one machine's
own pi or Claude Code configuration. Every worker needs the file: a worktree without one runs no
worker. Every Operation declares the ids of the workers it may launch in the Operation catalog, such
as `spec_panel`'s `reviewer1` to `reviewer5`, `architect1`, `architect2` and `chair`,
`spec_review`'s `reviewer` and `checker`, or `worker` for an Operation with one worker, and the
same id names the worker in its run record and in the Operation's evidence.

One model map serves the primary worktree, every task worktree, every unbound checkout and every
[test project](../../glossary.json#concept.test-project) of its user, as pi's and Claude Code's own
configuration does. It says how to reach a model, never which model a worker uses, like the
credentials and pi's provider definitions, which also come from the developer's installation ([the
pi run mechanics](pi.md#run-directory)) and never go into Git. A worker whose model has no id for
its program in the map runs no more than one without a model: Workers never takes the project model
name for the local id.


The worker configuration holds the required `enabled_models`, the models any worker may run on,
each keyed by its project model name and optionally carrying the model's own `reasoning` level. A
project model name is letters, digits, `.`, `_` and `-`, starting with a letter or digit, so no
program's own id, such as pi's `provider/model`, can stand in for one. The configuration holds a
`default`, and under `operations` an Operation's `default` and its `workers`, one entry per worker
id; each entry may set a `backend`, `pi` or `claude`, a `model` and a `reasoning` level, and every
model an entry names must be one of `enabled_models`. For each field the most specific entry that
sets it wins — the worker's, then the Operation's default, then the default — the backend like any
other field: an entry that only chooses Claude Code for a worker keeps the model and level it
inherits, since a project model name means the same model on either program. The level is the one
set by the entry that chose the model or by a more specific entry; otherwise the model's own level
in `enabled_models`; otherwise one a less specific entry sets; otherwise none, which leaves the
program's built-in default level. A worker whose entries set no model is refused: it never runs on
its program's default model. A backend no entry sets is pi. The same file holds the `limits` of
every worker launch and the `runtime` paths, which [the worker configuration
contract](contracts.md#contract.workers.worker-configuration) defines with their defaults and the
Operation's step reads for each launch:

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

Here every worker runs on pi, on `claude-sonnet-5` at that model's own `medium`, except
`spec_panel`'s: `reviewer1` on `claude-opus-5-5` at that model's own `high`, `reviewer2` on
`gpt-6-astra` at `high` from its entry, `reviewer3` on `gpt-6-astra` at pi's built-in default level,
since neither its entries nor that model set one, and the `chair` on Claude Code with the model the
project calls `opus` at Claude Code's own default level. The model map of the machine the workers
run on then gives each of those models its local id for the program that runs it:

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

The map is the file `CONCORDE_MODEL_MAP` names by its absolute path, else `concorde/models.json` of
the user's XDG configuration directory: `$XDG_CONFIG_HOME` when it is an absolute path, otherwise
`~/.config`. The variable lets a test or a test harness give its workers a map of its own. The map
may name models no project enables, and a model may have an id on one program only, as `gpt-6-astra`
and `opus` have here: a worker that runs it on the other program is refused.

An Operation's step asks for the choice of one worker of its Operation by its id, in the worktree the
run works on. Workers resolves the backend, the project model name and the level from the worker
configuration, checks that the backend is installed, then reads the model map and takes the model's
id for that backend, and passes the id with `--model` and the level with `--effort` to Claude Code
or `--thinking` to pi. The run record and the Operation's evidence name the project model name, the
local id and the map it came from.

The JSON files are the source of truth, and a human or an AI edits them directly; there is no
editor. The validator checks the whole worker configuration whenever a worker launches: structure,
duplicate keys, Operation and worker names against the catalog, that `enabled_models` is present and
not empty and names project model names, that every model an entry names is enabled, the limits and
the effective backend's reasoning vocabulary, including a model's own level wherever it applies.
That vocabulary is fixed: `low`, `medium`, `high`, `xhigh` and `max` on Claude Code, and `off`,
`minimal`, `low`, `medium`, `high`, `xhigh` and `max` on pi; an omitted level is always valid. It
accepts custom model names without discovery, installed backends or credentials. A worktree without
the file is refused with `config_missing`, a model an entry names outside `enabled_models` with
`model_not_enabled`, naming the entry, and a worker whose entries set no model with
`model_unresolved`, naming the worker and the entries its model may come from; each says how to
repair the file. Any other malformed file is refused with `config_invalid`, naming the file and
problem; earlier schema versions are not migrated or ignored: a file of schema version 1, whose
models were one program's local ids, is refused saying how to rename them and map them, and a
worktree that still has the untracked `.concorde/worker-models.json` of earlier versions but no
`.concorde/workers.json` is refused with `config_invalid` saying how to move it, rather than
silently run on defaults.

The map is read whole when a worker launches, and never written. A missing map is refused with
`model_map_missing`, showing what it holds; one that is not valid JSON, has duplicate keys, unknown
fields, a model without an id or a name that is not a project model name, or that
`CONCORDE_MODEL_MAP` names by a relative path, with `model_map_invalid`; and a worker whose project
model name has no id for its backend there with `model_unmapped`, naming the worker, its backend and
model and where each came from, the map and the exact entry to add. Each refusal comes before the
worker launches, and none falls back: the project model name is never taken as the local id, and
nothing else of the user's environment chooses a model.

So that a run does not stop after its first workers have run, the configuration reader also checks
every worker one Operation may launch against the map at once, which the Operation's run asks for
when it is admitted, before its first worker launches: it resolves each worker's backend and model
and refuses with one `model_unmapped` naming every model and backend the map lacks, with the
workers that would take each. A worker whose entries set no model is left to its own resolution,
which refuses it with `model_unresolved`. Every refusal before a run, with its code and reason, is
listed in [the run mechanics](launch.md#refusals-before-a-run).

Because the file is tracked, a [task](../../glossary.json#concept.task) carries the configuration of
its base commit: a later change on the primary branch never reaches a task already open, a change
the task makes to its own copy is part of its branch and reaches the primary branch when the task
merges, and a change of this file alone may be committed directly on the primary branch for the
tasks opened after it.

Discovery is separate and advisory. `python3 scripts/available_models.py --backend pi|claude`
(optionally `--json`) works outside Git. pi lists configured credentialed candidates with
`pi --no-extensions --list-models`; Claude Code offers an incomplete list of aliases and names from
user settings and environment because it cannot list account entitlements. Discovery makes no
inference API calls and does not verify access. An empty listing, a missing program or failed
discovery does not prevent custom/offline edits. The candidate output names the source and
reasoning levels, with pi's non-reasoning models listing only `off`, and the project model names the
model map already gives each candidate as their id on that program; pi's complete listing also
names the map's pi ids it does not list, such as one a changed pi configuration renamed. A missing
or unreadable map is reported in the output, never refused. These are suggestions for the model map
and for `enabled_models`, which alone admits a model.

### Failures and repeat runs

Every non-`ok` run carries an error link: what failed, in which round, why Workers cannot handle it,
and its causes — the worker's own error, a Claude Code error such as a used-up turn limit, or every
still-failing check with its log's end. Host failures use the same shape with status `failed`: a
missing/unreadable grant, a runtime directory a deny rule would cover, a launch error, a timeout (the
process group is killed), a Claude Code error, a missing/invalid worker result, an audit violation,
or checks that can't run. Every call starts a fresh run; a failed one is never resumed later. Exact
codes/layout: [the run mechanics](launch.md); testable behaviour: [the scenarios](scenarios.md).

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

The runtime drives every run and hands the agent process to one of two backends; the worker
configuration stands apart, because the Operation's step, not the runtime, asks it for a worker's
backend, model and limits before calling Workers.

- <a id="realization.workers.runtime"></a>The **worker runtime** checks a worker's placement and
  finds the Git administrative paths, writes the brief, decides rounds,
  runs the write audit, keeps the progress file, manages run directories/records, and supplies the
  worker prompt snippets every Operation includes, e.g. reporting an error. Its tests, under
  `tests/concorde/harness/workers/`, also exercise the Harness's
  [worker settings](../../glossary.json#concept.worker-settings),
  [write hook](../../glossary.json#concept.write-hook) and pi path decisions, since a worker run is
  where they apply.
- <a id="realization.workers.claude"></a>The **Claude Code backend** places the worker settings and
  write hook the Harness generates, launches and resumes `claude -p`, and reads its event stream.
  Tests fake `claude` for host behaviour and, with `CONCORDE_LIVE_CLAUDE=1`, run a real worker for
  what only Claude Code enforces.
- <a id="realization.workers.pi"></a>The **pi backend** checks its prerequisites, prepares the pi
  configuration directory, embeds the run's policy into the Harness's permission extension,
  launches and resumes `pi -p` and reads its event stream. Tests fake `pi` for host behaviour, run
  the path decisions under Node, and, with `CONCORDE_LIVE_PI=1`, run a real pi worker.

- <a id="realization.workers.models"></a>The **configuration reader** validates and reads
  `.concorde/workers.json`, resolves the backend, project model name and level of an Operation's
  worker by its id and the limits and runtime paths of every launch, refuses a missing file, a model
  outside `enabled_models` and a worker without a model, checks that the worker's program is
  installed at launch and resolves the model's local id through the model map, refusing a missing or
  malformed map and a model it does not map for the backend; it never writes either file and never
  reads the developer's own agent settings. The separate `available_models.py` module and
  `scripts/available_models.py` entry point discover advisory candidates, with the project model
  names the map gives each, without Git or inference probes.

### Why the run is built this way

`bypassPermissions` is used since `-p` mode's `dontAsk` denies every Edit/Write outside the working
directory even when allowed, and that directory can't be the worktree — Claude Code adds it (and
every `--add-dir`) to the Bash sandbox's read/write set, defeating per-file confinement — so the
brief uses absolute paths. The runtime directory must also avoid any deny-rule path, or the host
refuses to launch.

A worker creates a new file only below a `rw` directory: every exact `rw` path already exists,
since a realization binds only files that exist and the task level creates and binds any other new
file before the run. The host creates no file for the worker. A worker cannot delete either — it
only proposes deletions, performed by the host inside `rw` after a clean audit.

Resume rounds reuse the worker's context — the spike confirmed this fixes a failing check — and
on Claude Code each resume returns a session id the host continues from. Rounds are only for
failing checks and what the caller's validation reports; a Spec gap or grant violation is a
decision for the main agent or developer, not to retry.

On Claude Code the deny rules withhold only the worktree paths that exist when the host generates
them: a file created later has no rule of its own, and unless a directory rule hides it the file
tools can read it, a [limit of the Harness](../../harness/claude-code.md#deny-rules). The worker
cannot use it to reach more than its grant: its own writes outside `rw` are refused, and any other
file outside `rw` that appears in the worktree during the run and that Git does not ignore fails the
run through the write audit. What remains is a Git-ignored file another process creates in the
worktree while the run lasts, which a Claude Code worker may read without anything failing. On pi
there is no such gap, since the permission extension checks every file tool call against the grant
itself.

`--safe-mode`/`--bare` are unused since they'd disable the write hook too. Credentials are a copy of
the user's file in the runtime directory's `config/`, removed with it when the run ends, so the
traces never retain one; an env-var token was untested, and keeping credentials from the worker
itself is future work alongside the outer sandbox. Limits: the [Harness](../../harness/module.md).

[Open questions](../../glossary.json#concept.open-question): whether Bash needs read access to
Claude Code's shell snapshots in `CLAUDE_CONFIG_DIR` (deciding if `config/` stays unreadable) awaits
the built runtime; per-task tool lists are v1 defaults in
[the Harness](../../harness/claude-code.md#tool-sets) and may change.

## What Workers relies on

<a id="uses-spec"></a>

**Spec core** computes the [grant](../../glossary.json#concept.grant) of a task
type for the bound Modules, and its [context
identity](../../glossary.json#concept.context-identity). Workers relies on the
grant listing every path's level (`rw`/`ro`/`names`, ungranted omitted) and the identity naming
exactly what selected it; it never computes or widens a grant, only receives it frozen. A missing or
unreadable grant is a host failure before launch.

<a id="uses-harness"></a>

The **Harness** generates the worker's [agent harness](../../glossary.json#concept.agent-harness)
from the frozen grant, the run's paths, the primary worktree and the Git administrative paths
Workers found: the
[worker settings](../../glossary.json#concept.worker-settings) with their
[deny rules](../../glossary.json#concept.deny-rules) and write hook on Claude Code, the
[permission extension](../../glossary.json#concept.permission-extension) on pi, and the tool set of
the task type. Workers relies on them confining the worker's tools to the grant, keeps them
unchanged for every round, and refuses to launch when a generated deny rule would cover the run's
own directories. It relies on the Harness hiding every Git administrative path it hands over, and
the primary worktree but for the way to the worktree, through every tool, which together with the
placement is what keeps a worker from Git metadata wherever the repository lies. It never edits
what the Harness generated.

Which of the Harness's parts reaches a worker depends on its backend, and the runtime directory holds
what was generated:

```d2
backend: Worker backend
dir: Runtime directory
settings: Harness / Worker settings
extension: Harness / Permission extension
backend -> settings: Claude Code applies
backend -> extension: pi applies
dir -> settings: holds
```

<a id="uses-checks"></a>

**Check execution** is a service the Workers host code calls. It runs the
[configured checks](../../glossary.json#concept.configured-check)
on the worktree in its read-only boundary, returning a [check
result](../../glossary.json#concept.check-result) per check with its log, in the shape its
[service](../checks/service.md#check-result) defines, which each round keeps as its `checks`;
a failure of the service reaches Workers as Check execution's own link
([req.checks.service-link](../checks/service.md#req.checks.service-link)), and a check that did not
pass as the link [req.checks.failure-link](../checks/service.md#req.checks.failure-link) promises. Workers relies on
Check execution keeping checks from writing the worktree's files directly and refusing a result
whose inputs changed while it ran; it runs them only after a clean audit, feeds failures into the
next round, and records every result. Checks that cannot run, or whose result Check execution
refuses as `stale_evidence`, end the run `failed` with `checks_unavailable`, Check execution's error
as its cause, and no further round.

<a id="uses-execution"></a>

**Execution** gives every worker run its place: the Operation's step passes the trace node folder
of its run in the [run store](../../glossary.json#concept.run-store), and Workers creates the run
directory inside it, and records the
Operation run's identity, which the step passes, and the runner's process identifier in the
progress file, beside the runner's own [run progress
file](../../glossary.json#concept.run-progress-file). Workers relies on the runner refusing an
unbound run's writing worker before it reaches Workers, and never reads a [workspace binding](../../glossary.json#concept.workspace-binding) itself.
For an unbound run the step passes the run's checkout as the worktree and reads the backend,
model and limits from the worker configuration committed in that checkout, as every other input of
the run, so Workers never learns that the worktree it audits is a checkout. Workers relies on the
runner placing that checkout in `.claude/worktrees/` of the primary worktree, where a worker may
run; a task worktree opened anywhere else runs no worker.

<a id="uses-tracing"></a>

**Tracing** gives the worker run and each round the shape and place of a
[trace node](../../glossary.json#concept.trace-node): Workers writes both through Tracing's library,
at their start, after each round and at their end, records in their usage only what the agent
program reported for each round, and reports its failures in the error contract. It relies on the
[node contract](../../tracing/contracts.md#contract.tracing.node) and on nothing of the Operation's
node but the folder it is given.

<a id="uses-operations"></a>

**Operations** declares, in its [catalog](../../glossary.json#concept.operation-catalog), which
Operations launch workers and the ids of their workers. The shared validator checks all configured
Operation and worker names against it. It relies on the catalog naming every worker an Operation may
launch.

The [Main session](../../coordination/main-session/module.md) reads Workers' definitions without
launching a run: it changes the worker configuration by editing it directly. A task
worktree carries the worker configuration of its base commit through Git, with nothing copied.
