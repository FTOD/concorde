# Workers

## Purpose

Workers runs the agent half of level 5, the bottom of Concorde's [levels of
work](../../module.md#the-levels-of-work): one headless worker for one job under one frozen grant,
on Claude Code or on pi, turning what happened into a run record the Operation that launched it can
trust. Each run is its own session, its own process and its own permissions, on the model the
worktree's worker model configuration chooses, and its run directory lies in the run store beside
the Operation run that launched it. Workers also owns that configuration and the command
`concorde configure-workers` that lists and changes it. Of each run it owns the whole
lifecycle: the run directory, the brief, the launch and resume rounds, the write audit, the checks
after each round and the record. The worker's permissions and environment are its [agent
harness](../../harness/module.md#concept.harness.harness), which the Harness generates from the
grant for the chosen program. Workers does not compute the grant, choose the task type or write the
task-specific brief, and never commits or judges whether the worker's work is correct. Its boundary
guards against scope drift and mistakes, not a malicious worker.

## Terminology

| Term | Definition |
| --- | --- |
| Worker backend | The agent program a worker runs on, Claude Code or pi: the one the worktree's worker model configuration chooses for the worker or its Operation, otherwise pi; both enforce the same grant. |
| Worker model configuration | A worktree's untracked `.concorde/worker-models.json`, which gives a backend, a model and a reasoning level for every worker, for an Operation's workers and for one worker by its id, the most specific entry winning field by field. |
| Worker id | The stable name an Operation gives one worker it may launch, such as `spec_panel`'s `reviewer2` or `chair`, used alike in the worker model configuration, the run record and the evidence. |
| Progress file | A worker run's `status.json`, which the host keeps current while the worker runs so the main session can show what it is doing. |
| Brief | The prompt a worker receives: the Operation's task instructions followed by the grant's `rw`, `ro` and `names` lists as absolute paths and the rules of its boundary. |
| Worker result | The structured answer a worker ends with, validated against a fixed schema, reporting its status, a summary, its own error link when it could not finish, and the deletions it proposes. |
| Write audit | The host's comparison, after each round and outside the worker, of the worktree's changes with the grant's `rw` list. |
| Resume round | One continuation of the same worker session with the failures of the configured checks. |
| Run record | The host's durable record of one worker run: its grant and context identity, settings, transcript path, audits, checks, rounds and result. |
| Run directory | The directory `runs/<run-id>/` of the run store that holds one worker run's record, generated configuration and the worker's private state and working directory. |
| configure-workers | The command `concorde configure-workers`, which lists the models the installed agent programs offer workers and changes the worker model configuration of the worktree it runs in, without launching a worker or recording a run. |
| [Worker](../../vocabulary.md#concept.concorde.worker) | |
| [Tool](../../vocabulary.md#concept.concorde.tool) | |
| [Agent harness](../../harness/module.md#concept.harness.harness) | |
| [Worker settings](../../harness/module.md#concept.harness.worker-settings) | |
| [Permission extension](../../harness/module.md#concept.harness.permission-extension) | |
| [Deny rules](../../harness/module.md#concept.harness.deny-rules) | |
| [Write hook](../../harness/module.md#concept.harness.write-hook) | |
| [Task type](../../vocabulary.md#concept.concorde.task-type) | |
| [Boundary](../../vocabulary.md#concept.concorde.boundary) | |
| [Evidence](../../vocabulary.md#concept.concorde.evidence) | |
| [Error chain](../../vocabulary.md#concept.concorde.error-chain) | |
| [Grant](../../spec-tooling/spec/module.md#concept.spec.grant) | |
| [Context identity](../../spec-tooling/spec/module.md#concept.spec.context-identity) | |
| [Configured check](../tools/checks/module.md#concept.checks.configured-check) | |
| [Check result](../tools/checks/module.md#concept.checks.check-result) | |
| [Run store](../module.md#concept.execution.run-store) | |
| [Run progress file](../module.md#concept.execution.progress-file) | |
| [Unbound run](../module.md#concept.execution.unbound-run) | |
| [Operation catalog](../operations/module.md#concept.operations.catalog) | |

## Usage

The caller is a worker-backed step of an Operation run, in the Execution runner's process, that
has chosen the worktree, task type and Modules and asked Spec core for the grant. For work that
changes files this is a bound workspace; an [unbound run](../module.md#concept.execution.unbound-run)
can launch only a reading worker over the worktree it runs in. The step calls Workers with the
worktree, the records directory of the run, the frozen grant and context identity, task
instructions for the brief, checks to run after the worker, and run limits — getting back a run
record (status `ok`/`blocked`/`failed`) with the worker result kept verbatim beside the host's own
evidence.

Workers is the deterministic management code, the **host** of a worker run; the worker it launches
is the AI process. An Operation's step calls Workers, which launches the worker and, after a clean
audit, calls the Check execution Tool when checks were requested. A check failure can lead to
another AI round within the same Operation. This is a host Tool call, not an AI worker calling Check
execution or starting another run. A workflow reaches workers through its Operations, never by
directly launching a Concorde worker. Task sessions have their own task-level lifecycle outside
Workers.

### A normal run

Take an `implement` run whose grant makes `src/shop/cart.py` and pending `src/shop/discounts.py`
writable (`rw`), the Module's Specs readable (`ro`), and another Module's `src/shop/pricing.py`
visible by name only (`names`):

```d2 illustrative
grant: Frozen grant
precreate: Pre-create pending files
generate: Generate settings, hook, tools and brief
launch: Launch or resume the worker
audit: Write audit
record: Write the run record
checks: Run configured checks
grant -> precreate -> generate -> launch -> audit
audit -> record: violation
audit -> checks: clean
checks -> launch: a check fails, rounds left
checks -> record: pass, or rounds used up
```

<a id="concept.workers.run-directory"></a>

The host creates the **run directory** `runs/<run-id>/` in the [run
store](../module.md#concept.execution.run-store) of the records directory the Operation names: the
records directory of its workspace binding for a bound run, so that a task's worker runs lie beside
its Operation runs in the primary worktree's `.concorde/runs/` however many task worktrees there
are, and the worktree's own `.concorde` for an unbound run. It holds host-only `control/`
(settings, hook, grant, brief), the worker's
`config/` (`CLAUDE_CONFIG_DIR` plus a credential copy), `home/` (`HOME`) and `work/` (its working
directory); the run directory is ignored by Git. `TMPDIR` is a short private directory under `/tmp`,
removed when the run ends. It pre-creates `src/shop/discounts.py` empty — a worker can write only
files that already exist — generates settings/tools/brief, launches `claude -p` in `work/` with
`bypassPermissions`, the result schema, no MCP servers and a cleared environment, audits every
change against `rw`, runs checks through Check execution, resumes the same session when a check
fails, up to three rounds by default, then performs proposed deletions and writes the run record.

<a id="concept.workers.progress-file"></a>

Throughout, the host keeps the worker run's **progress file** `status.json` current: the phase,
the round, the worker's latest tool call and the process identifier of the Execution runner it runs
in, which the Operation run's own [run progress file](../module.md#concept.execution.progress-file)
names too, so an observer pairs the two. The main session's run view reads it; the run record, not
the progress file, is the run's evidence. Every run ends both, however it ends: a run interrupted from
outside, such as by the cancellation of the Operation that launched it, is recorded as `failed`
with `interrupted` and its progress file as finished before the interruption travels on, so no
reader sees a worker that runs forever. The launching Operation learns the run's identity as soon
as the run exists, so it can name the run even when it is interrupted before the run returns.

### Two backends from one grant

<a id="concept.workers.backend"></a>

The **worker backend** is the agent program a worker runs on. The [worker model
configuration](#concept.workers.model-configuration) may choose it for one worker, for an
Operation's workers or for every worker; when no entry chooses it, the worker runs on **pi**,
whatever program the main session runs on. A Claude Code main session so runs pi workers unless it
chooses Claude Code for some of them, and a pi main session may do the same. A worker's backend
must be installed: when its command (`claude` or `pi`, or the path in `CONCORDE_CLAUDE` or
`CONCORDE_PI`) is missing, the worker is refused with `backend_missing`, naming the worker, the
program and what chose it, and how to choose the other program for it; it never falls back to the
other program. Everything but the agent process is shared: the grant, the brief, the run
directory, the progress file, the audit, the checks, the rounds and the run record, so workers of
one Operation on different backends exchange nothing but the structured results the host
validates.

Workers also reads the **main session's program** from the environment, for [Task
sessions](../../coordination/task-session/module.md), which run on it: `CONCORDE_CLIENT` when set (Concorde's pi
extension sets it to `pi`), otherwise `claude` when `CLAUDECODE=1`, which Claude Code sets for its
commands, otherwise `pi` when pi's `PI_SESSION_ID` or `PI_CODING_AGENT` is set. It refuses with
`client_unknown` when none names one and with `invalid_client` when `CONCORDE_CLIENT` names neither
program. No worker depends on it.

On Claude Code the worker's harness is applied by its [worker
settings](../../harness/module.md#concept.harness.worker-settings), on pi by the [permission
extension](../../harness/module.md#concept.harness.permission-extension); the
[Harness](../../harness/module.md#concept.harness.permission-extension) compares the two surface by
surface. The pi command line and environment are in [the pi run mechanics](pi.md).

### Choosing worker models

<a id="concept.workers.model-configuration"></a><a id="concept.workers.worker-id"></a>

The **worker model configuration** of a worktree is its `.concorde/worker-models.json`, ignored by
Git because it names models of this machine's installation. It is keyed by **worker id**: every
Operation declares the ids of the workers it may launch in the [Operation
catalog](../operations/module.md#concept.operations.catalog), such as `spec_panel`'s `reviewer1`
to `reviewer5` and `chair`, `spec_review`'s `reviewer` and `checker`, or `worker` for an Operation
with one worker, and the same id names the worker in its run record and in the Operation's
evidence. The file holds a `default`, and under `operations` an Operation's `default` and its
`workers`, one entry per worker id; each entry may set a `backend`, `pi` or `claude`, a `model` and
a `reasoning` level. For each field the most specific entry that sets it wins — the worker's, then
the Operation's default, then the default — with one exception: an entry that chooses a backend
starts that program afresh, so the model and level come only from that entry or a more specific
one, since a model named for one program means nothing to the other. A field no entry sets leaves
the program's own default, and a backend no entry sets is pi. An Operation's step asks for the
choice of one worker of its Operation by its id, in the worktree the run works on, and passes the
model with `--model` and the level with `--effort` to Claude Code or `--thinking` to pi:

```json
{
  "schema_version": 3,
  "default": {"model": "anthropic/claude-sonnet-5", "reasoning": "medium"},
  "operations": {
    "spec_panel": {
      "workers": {
        "reviewer1": {"model": "anthropic/claude-opus-5-5", "reasoning": "high"},
        "reviewer2": {"model": "local-openai/gpt-6", "reasoning": "high"},
        "reviewer3": {"model": "local-openai/gpt-6"},
        "chair": {"backend": "claude", "model": "opus"}
      }
    }
  }
}
```

Here every worker runs on pi, on `anthropic/claude-sonnet-5` at `medium`, except `spec_panel`'s:
`reviewer1` on `anthropic/claude-opus-5-5` at `high`, `reviewer2` on `local-openai/gpt-6` at
`high`, `reviewer3` on `local-openai/gpt-6` at the default's `medium`, and the `chair` on Claude
Code with its `opus` alias at Claude Code's own default level, since choosing Claude Code does not
carry the pi default's level over. The model configuration code knows no Operation or worker
names; the entries are whatever [`concorde configure-workers`](#concept.workers.configure-workers)
wrote after checking them against the catalog. A file of an earlier schema version, keyed by
backend and worker role, is refused with `config_invalid`, and never read.
[Tasks](../../coordination/tasks/module.md) copies the primary worktree's file into a task worktree when it
opens the task, so a task keeps the configuration it started with and a later change in the primary
worktree never reaches it.

Workers also lists the **candidates** the installed program offers: for pi every model
`pi --list-models` shows with credentials, as `provider/model` with the levels of `--thinking` or
only `off` for a model without reasoning; for Claude Code, which has no command listing an
account's models, its aliases, the models named by `model` and `availableModels` of the user's
Claude Code settings and those pinned by `ANTHROPIC_*MODEL` variables, marked incomplete, with the
levels of `--effort`. A change is refused with `unknown_model` for a model the listing does not show,
unless the caller admits unlisted models, and with `unknown_level` for a level the model does not
offer, each naming what is listed. A file that is not valid JSON or does not match the schema is
refused with `config_invalid`, naming the file and the problem, and never ignored.

The main session lets the developer choose: pi's run view has a picker for it and Claude Code's
main agent asks with its question tool ([Main session](../../coordination/main-session/module.md));
both change the file through `concorde configure-workers`.

### Changing worker models: configure-workers

<a id="concept.workers.configure-workers"></a>

**configure-workers** is how anyone lists and changes the worker model configuration:

```text
concorde configure-workers [--operation <op> [--worker <id>]]
    [--backend claude|pi] [--model <model>] [--reasoning <level>] [--allow-unlisted]
    [--unset] [--candidates claude|pi]
```

It works on the Git worktree it runs in, from any directory inside it: in the primary worktree it
changes the file that task worktrees opened from then on inherit, in a task worktree only that
worktree's copy. It is a plain command, not a run: it launches no worker, needs no workspace
binding, takes no workspace lock, records no run and never touches a task record, because the file
it writes is this machine's configuration and no part of any workspace's change.

Without a change it lists: the candidates of the program the named entry runs on (pi unless the
configuration chooses Claude Code, or the program `--candidates` names), the file as written, and
the effective backend, model and level of every worker of every Operation in the [Operation
catalog](../operations/module.md#concept.operations.catalog) that launches workers, by worker id.
`--backend`, `--model`, `--reasoning` or several of them set those fields on the default, on
`--operation <op>`'s default or on `--worker <id>` of it, and `--unset` removes that entry and every
section it leaves empty. A change is checked against the listing of the program the entry will run
on once it is applied: a model the listing does not show is refused unless `--allow-unlisted`
admits it, and a level the model does not offer is refused. The file is written atomically, and
only once every check passed; a refused request leaves it as it was.

The command prints one [command result](contracts.md#contract.workers.configure-workers-result):
`ok` with the [worker configuration](contracts.md#contract.workers.worker-configuration) as its
output and exit status 0, or `failed` with the command's own error link, level `command`, and exit
status 1: `invalid_request` for a request it cannot carry out, such as a `--worker` without its
`--operation`, an Operation that launches no worker or a worker id the Operation does not declare,
naming what is admitted; `configuration_refused` when the model configuration refused, whose cause
is that refusal's `component` link, such as `unknown_model` or `backend_missing`. A malformed
command line, or a directory outside every Git worktree, prints only an error link and exits with
status 2.

Before the first round Workers asks the Harness for the worker's configuration from the frozen
grant and the run's own paths: on Claude Code the [worker
settings](../../harness/module.md#concept.harness.worker-settings) with their [deny
rules](../../harness/module.md#concept.harness.deny-rules), [write
hook](../../harness/module.md#concept.harness.write-hook) and Bash sandbox, on pi the permission
extension, and the tool set of the task type. It places them in the run's `control/` directory and
never changes them during the run.

<a id="concept.workers.brief"></a>

The **brief** is the worker's only instruction — `CLAUDE.md`, auto memory and user settings are
disabled — the Operation's task instructions plus the boundary Workers appends: `rw`/`ro`/`names` as
absolute paths (its working directory isn't the worktree); that it can't delete, only propose
deletions; that a Bash-created file outside `rw` is silently lost; that a read denial means the
path is outside its grant; and, for every task type but `code-to-spec`, that a promise the Spec does
not state is never inferred from code but returned as `blocked`. A `code-to-spec` worker is told
instead that describing the code it reads is its task, and that doubtful intent is reported, never
promised.

<a id="concept.workers.worker-result"></a>

Every worker ends with a **worker result** validated by `--json-schema`: `status`
(`ok`/`blocked`/`failed`), a summary, proposed deletions and, when it could not finish, its
`error` — the first [error chain](../../vocabulary.md#concept.concorde.error-chain) link with its
code, detail, evidence, attempt, reason it couldn't handle the error, options and recommendation —
so the host and main agent can act without asking again. Contract: [the worker result
contract](contracts.md).

<a id="concept.workers.audit"></a>

The **write audit** runs read-only Git after every round, comparing tracked and untracked changes
since the pre-launch snapshot with `rw`. Any change outside `rw`, or a deletion, is a violation: the
run ends `failed` with every violating path as evidence, no resume follows, and the worktree is left
for the main agent — never reverted or committed by the host.

<a id="concept.workers.resume-round"></a>

A **resume round** happens only when the worker ended `ok`, the audit was clean, and a check failed
or, once the checks pass, the caller's own validation after the round reported something to
repair: the host sends each failure's identity, exit code and log tail, or the validation's text,
to `claude -p --resume <session>`, tracking the new session id returned. A Spec-writing Operation
uses the validation to have its worker repair the structural errors it introduced. A
`blocked`/`failed` result or an audit violation is never resumed — those go to the main agent;
when the rounds are used up and a check still fails, the run ends `failed` with the last check
results, while a validation still reporting problems leaves the round's result for its caller to
judge. Each round records its validation outcome.

<a id="concept.workers.run-record"></a>

The **run record**, written for every run including a refused launch, holds the grant/context
identity, settings/brief digests, the tool list, transcript path, session ids, each round's audit
and check results with logs, the worker's stderr tail, the worker result verbatim, deletions
performed, and the host's final status with its error link — evidence that never restates a
worker's claim as fact. Delivery later lists these records' identities in a workspace's evidence.

### Failures and repeat runs

Every non-`ok` run carries an error link: what failed, in which round, why Workers cannot handle it,
and its causes — the worker's own error, a Claude Code error such as a used-up turn limit, or every
still-failing check with its log's end. Host failures use the same shape with status `failed`: a
missing/unreadable grant, a run directory a deny rule would cover, a launch error, a timeout (the
process group is killed), a Claude Code error, a missing/invalid worker result, an audit violation,
or checks that can't run. Every call starts a fresh run; a failed one is never resumed later. Exact
codes/layout: [the run mechanics](launch.md); testable behaviour: [the scenarios](scenarios.md).

## Design

The worker is untrusted in that its claims are proposals: only the host reads Git, audits, runs
checks and records, after the worker ends — that is why the run record keeps the worker result
separate from host evidence.

### Its place in the levels of work

Workers carries the agent half of level 5, the bottom of Concorde's
[levels of work](../../module.md#the-levels-of-work). Its own code is not an agent: it runs in the
Execution runner's process, on behalf of the Operation run at level 4 that called it, and launches
the one process that is, the headless worker. Only a worker-backed step of an Operation calls it —
the standard worker sequence of [Operations](../operations/module.md) and the providers that run
workers, such as Understanding, Specification, Implementation, Code review, Adoption and Spec
review. No recorded command launches a worker, and nothing above level 4 does: a workflow reaches
workers through its Operations, and neither the main agent nor a task session ever starts one. Below it, the worker calls nothing of Concorde's: it never touches Git,
runs an Operation or starts an agent. Between rounds the Workers host code, not the worker, calls
its level-5 neighbour, the Check execution Tool, so that a failing check can drive another round
inside the same Operation.

Results travel up in one direction. The worker ends with its worker result; Workers keeps it
verbatim in the run record beside its own evidence and returns the record to the Operation's
step, which turns it into the Operation's run result. When the worker could not finish, its `error` is the
first link of the [error chain](../../vocabulary.md#concept.concorde.error-chain), and Workers adds
its own link above it saying why it cannot handle the failure — a Spec gap or grant violation is
not its to retry — before the Operation adds the next. Delivery later lists the run records'
identities in the workspace's evidence.

A run's collaborators: the Operation that calls it and the three providers it relies on.

```d2
operations: Operations
workers: Workers
spec: Spec core
harness: Harness
checks: Check execution
operations -> workers
workers -> spec
workers -> harness
workers -> checks
```

The Operation providers, Spec review and Delivery use this Module; the worker runtime knows none of
them. They rely on the run record and on the rule that a worker's result is kept apart from host
evidence. Only the configure-workers command looks at the Operation catalog, to check the names it
is given.

<a id="uses-spec"></a>

**Spec core** computes the [grant](../../spec-tooling/spec/module.md#concept.spec.grant) of a task
type for the bound Modules, and its [context
identity](../../spec-tooling/spec/module.md#concept.spec.context-identity). Workers relies on the
grant listing every path's level (`rw`/`ro`/`names`, ungranted omitted) and the identity naming
exactly what selected it; it never computes or widens a grant, only receives it frozen. A missing or
unreadable grant is a host failure before launch.

<a id="uses-harness"></a>

The **Harness** generates the worker's [agent harness](../../harness/module.md#concept.harness.harness)
from the frozen grant and the run's paths: the [worker
settings](../../harness/module.md#concept.harness.worker-settings) with their deny rules and write
hook on Claude Code, the [permission
extension](../../harness/module.md#concept.harness.permission-extension) on pi, and the tool set of
the task type. Workers relies on them confining the worker's tools to the grant, keeps them
unchanged for every round, and refuses to launch when a generated deny rule would cover the run's
own directories. It never edits what the Harness generated.

Which of the Harness's parts reaches a worker depends on its backend, and the run directory holds
what was generated:

```d2
backend: Worker backend
dir: Run directory
settings: Harness / Worker settings
extension: Harness / Permission extension
backend -> settings: Claude Code applies
backend -> extension: pi applies
dir -> settings: holds
```

<a id="uses-checks"></a>

**Check execution** is a Tool called by the Workers host code. It runs the
[configured checks](../tools/checks/module.md#concept.checks.configured-check)
on the worktree in its read-only boundary, returning a [check
result](../tools/checks/module.md#concept.checks.check-result) per check with its log. Workers relies on
checks never changing the worktree; it runs them only after a clean audit, feeds failures into the
next round, and records every result. Checks that cannot run end the run `failed` with the error as
evidence and no round.

<a id="uses-execution"></a>

**Execution** gives every worker run its place: the Operation's step passes the records directory
of its run, and Workers creates the run directory in that [run
store](../module.md#concept.execution.run-store), beside the Operation run, and records the
runner's process identifier in the progress file, as the runner's own [run progress
file](../module.md#concept.execution.progress-file) does. Workers relies on the runner refusing an
unbound run's writing worker before it reaches Workers, and never reads a workspace binding itself.

<a id="uses-operations"></a>

**Operations** declares, in its [catalog](../operations/module.md#concept.operations.catalog), which
Operations launch workers and the ids of their workers. `concorde configure-workers` checks every
`--operation` and `--worker` against it and lists the effective choice of each of those workers;
it relies on the catalog naming every worker an Operation may launch, since a worker it does not
name could not be configured.

Three Modules read Workers' definitions without launching a run: the
[Main session](../../coordination/main-session/module.md) shows the progress file and changes the worker model
configuration through `concorde configure-workers`, [Task sessions](../../coordination/task-session/module.md) reads the main
session's program the way the worker backend is read, and [Tasks](../../coordination/tasks/module.md) copies the
worker model configuration into a new task worktree.

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
  models: Model configuration {
    "models.py"
  }
  configure: Configure-workers command {
    "configure.py"
  }
  runtime -> claude: launches
  runtime -> pi: launches
  configure -> models: changes the file through
}
```

The runtime drives every run and hands the agent process to one of two backends; the model
configuration stands apart, because the Operation's step, not the runtime, asks it for a worker's
backend and model before calling Workers, and the configure-workers command changes the file only
through it.

- <a id="realization.workers.runtime"></a>The **worker runtime** writes the brief, decides rounds,
  runs the write audit, keeps the progress file, manages run directories/records, and supplies the
  worker prompt snippets every Operation includes, e.g. reporting an error. Its tests, under
  `tests/concorde/harness/workers/`, also exercise the Harness's worker settings, write hook and pi
  path decisions, since a worker run is where they apply.
- <a id="realization.workers.claude"></a>The **Claude Code backend** places the worker settings and
  write hook the Harness generates, launches and resumes `claude -p`, and reads its event stream.
  Tests fake `claude` for host behaviour and, with `CONCORDE_LIVE_CLAUDE=1`, run a real worker for
  what only Claude Code enforces.
- <a id="realization.workers.pi"></a>The **pi backend** checks its prerequisites, prepares the pi
  configuration directory, embeds the run's policy into the Harness's permission extension,
  launches and resumes `pi -p` and reads its event stream. Tests fake `pi` for host behaviour, run
  the path decisions under Node, and, with `CONCORDE_LIVE_PI=1`, run a real pi worker.

- <a id="realization.workers.models"></a>The **model configuration** validates, reads and writes
  `.concorde/worker-models.json`, resolves the backend, model and level of an Operation's worker by
  its id and checks that its program is installed, discovers the candidates by running the
  installed `claude` or `pi`, and detects the main session's program for Task sessions. Tests fake
  both programs.
- <a id="realization.workers.configure"></a>The **configure-workers command** parses the request,
  checks it against the Operation catalog, lists the candidates, applies a checked change through
  the model configuration and prints the command result. Its tests run the command in a primary
  and a task worktree with both programs faked.

What one run leaves behind. The runtime generates the brief, keeps the progress file and writes the
run record; both files sit in the run directory, and the record is the run's evidence:

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

### Why the run is built this way

`bypassPermissions` is used since `-p` mode's `dontAsk` denies every Edit/Write outside the working
directory even when allowed, and that directory can't be the worktree — Claude Code adds it (and
every `--add-dir`) to the Bash sandbox's read/write set, defeating per-file confinement — so the
brief uses absolute paths. The run directory must also avoid any deny-rule path, or the host refuses
to launch.

Pending files are pre-created since a worker must never create an undeclared file, and Bash can only
grant writes to existing files; for the same reason it can't delete — only propose deletions,
performed by the host inside `rw` after a clean audit. An untouched pre-created file is removed
again, staying pending.

Resume rounds reuse the worker's context — the spike confirmed this fixes a failing check — and
each resume returns a session id the host continues from. Rounds are only for check failures; a
Spec gap or grant violation is a decision for the main agent or developer, not to retry.

`--safe-mode`/`--bare` are unused since they'd disable the write hook too. Credentials are a copy of
the user's file in `config/`; an env-var token was untested, and keeping credentials from the worker
is future work alongside the outer sandbox. Limits: the [Harness](../../harness/module.md).

Open questions: whether Bash needs read access to Claude Code's shell snapshots in
`CLAUDE_CONFIG_DIR` (deciding if `config/` stays unreadable) awaits the built runtime; per-task tool
lists are v1 defaults in [the Harness](../../harness/claude-code.md#tool-sets) and may change.
