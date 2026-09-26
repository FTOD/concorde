# Workers

## Purpose

Workers runs the lowest level of Concorde's agents: one headless worker for one task under one
frozen grant, on Claude Code or on pi, turning what happened into a run record the Operation host
can trust. Each run is its own session, its own process and its own permissions, on the model the
task worktree's configuration chooses. Workers owns the run's lifecycle: the run directory, the
brief, the launch and resume rounds, the write audit, the checks after each round and the record.
The worker's permissions and environment are its [agent
harness](../../harness/module.md#concept.harness.harness), which the Harness generates from the
grant for the chosen program. Workers does not compute the grant, choose the task type or write
the task-specific brief, and never commits or judges whether the worker's work is correct. Its
boundary guards against scope drift and mistakes, not a malicious worker.

## Terminology

| Term | Definition |
| --- | --- |
| Worker backend | The agent program a worker runs on, Claude Code or pi: the one the worktree's worker model configuration chooses for the worker's Operation and role, otherwise the program of the main session that started the run; both enforce the same grant. |
| Worker model configuration | A worktree's untracked `.concorde/worker-models.json`, which may choose the backend of every worker, of an Operation's workers or of one worker role, and gives for each backend a default model and reasoning level and optional entries per Operation and per worker role of an Operation. |
| Progress file | The run's `status.json`, which the host keeps current while the run goes on so the main session can show what it is doing. |
| Brief | The prompt a worker receives: the Operation's task instructions followed by the grant's `rw`, `ro` and `names` lists as absolute paths and the rules of its boundary. |
| Worker result | The structured answer a worker ends with, validated against a fixed schema, reporting its status, a summary, its own error link when it could not finish, and the deletions it proposes. |
| Write audit | The host's comparison, after each round and outside the worker, of the task worktree's changes with the grant's `rw` list. |
| Resume round | One continuation of the same worker session with the failures of the configured checks. |
| Run record | The host's durable record of one worker run: its grant and context identity, settings, transcript path, audits, checks, rounds and result. |
| Run directory | The directory `.concorde/runs/<run-id>/` of the primary worktree that holds one run's record, generated configuration and the worker's private state and working directory. |
| [Worker](../../vocabulary.md#concept.concorde.worker) | |
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
| [Configured check](../../checks/module.md#concept.checks.configured-check) | |
| [Check result](../../checks/module.md#concept.checks.check-result) | |

## Usage

The caller is an Operation host that has opened a task worktree, chosen the task type and the
Modules, and asked the Spec core for the grant. It calls Workers with the worktree, frozen grant and
context identity, task instructions for the brief, checks to run after the worker, and run limits —
getting back a run record (status `ok`/`blocked`/`failed`) with the worker result kept verbatim
beside the host's own evidence.

### A normal run

Take an `implement` task whose grant makes `src/shop/cart.py` and pending `src/shop/discounts.py`
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

The host creates the **run directory** `.concorde/runs/<run-id>/` in the primary worktree, even when
the task worktree is elsewhere: host-only `control/` (settings, hook, grant, brief), the worker's
`config/` (`CLAUDE_CONFIG_DIR` plus a credential copy), `home/` (`HOME`) and `work/` (its working
directory); the run directory is ignored by Git. `TMPDIR` is a short private directory under `/tmp`,
removed when the run ends. It pre-creates `src/shop/discounts.py` empty — a worker can write only
files that already exist — generates settings/tools/brief, launches `claude -p` in `work/` with
`bypassPermissions`, the result schema, no MCP servers and a cleared environment, audits every
change against `rw`, runs checks through Check execution, resumes the same session when a check
fails, up to three rounds by default, then performs proposed deletions and writes the run record.

<a id="concept.workers.progress-file"></a>

Throughout, the host keeps the run's **progress file** `status.json` current: the phase, the round
and the worker's latest tool call. The main session's run view reads it; the run record, not the
progress file, is the run's evidence.

### Two backends from one grant

<a id="concept.workers.backend"></a>

The **worker backend** is the agent program a worker runs on. The `backend` section of the
[worker model configuration](#concept.workers.model-configuration) may choose it for one worker
role of an Operation, for an Operation's workers or for every worker; when no entry chooses it, it
is the agent program of the main session that started the run, which the Operation host reads from
its environment — `CONCORDE_CLIENT` when set (Concorde's pi extension sets it to `pi`), otherwise
`claude` when `CLAUDECODE=1`, which Claude Code sets for its commands, otherwise `pi` when pi's
`PI_SESSION_ID` or `PI_CODING_AGENT` is set — and the run is refused with `client_unknown` when none
names one. A Claude Code main session may so run pi workers and a pi main session Claude Code
workers. A backend the configuration chooses must be installed: when its command (`claude` or `pi`,
or the path in `CONCORDE_CLAUDE` or `CONCORDE_PI`) is missing, the choice is refused with
`backend_missing`, naming the entry that chose it, and the worker never falls back to the other
program. Everything but the agent process is shared: the grant, the brief, the run directory, the
progress file, the audit, the checks, the rounds and the run record, so workers of one Operation on
different backends exchange nothing but the structured results the host validates.

On Claude Code the worker's harness is applied by its [worker
settings](../../harness/module.md#concept.harness.worker-settings), on pi by the [permission
extension](../../harness/module.md#concept.harness.permission-extension); the
[Harness](../../harness/module.md#concept.harness.permission-extension) compares the two surface by
surface. The pi command line and environment are in [the pi run mechanics](pi.md).

### Choosing worker models

<a id="concept.workers.model-configuration"></a>

The **worker model configuration** of a worktree is its `.concorde/worker-models.json`, ignored by
Git because it names models of this machine's installation. Its `backend` section chooses the
[worker backend](#concept.workers.backend): a `default` for every worker, and under `operations` an
Operation's `default` and its `roles`, each naming `claude` or `pi`; the most specific entry wins —
the role's, then the Operation's, then the section's default — and without one the worker runs on
the main session's program. The section is written by hand: no Operation changes it. The model and
level are then resolved in the section of the chosen backend. For each backend it holds a `default`,
entries under `operations` for an Operation's workers, and under an Operation's `roles` entries for
one worker role of it, each with a `model` and a `reasoning` level. For each field the most specific
entry that sets it wins — the role's, then the Operation's, then the default — and a field no entry
sets leaves the program's own default. The Operation host asks for the choice of one worker role of
its Operation, in the worktree the run works on, and passes the model with `--model` and the level
with `--effort` to Claude Code or `--thinking` to pi:

```json
{
  "schema_version": 2,
  "backend": {
    "operations": {"implement": {"default": "pi"}}
  },
  "pi": {
    "default": {"model": "anthropic/claude-sonnet-5", "reasoning": "medium"},
    "operations": {
      "implement": {"model": "local-openai/gpt-6"},
      "spec_review": {"roles": {"checker": {"reasoning": "low"}}}
    }
  }
}
```

Here an `implement` worker runs on pi whatever the main session's program, on
`local-openai/gpt-6` at `medium`. From a pi main session `spec_review`'s checker runs on
`anthropic/claude-sonnet-5` at `low` and every other worker on `anthropic/claude-sonnet-5` at
`medium`; from a Claude Code main session they run on Claude Code with its own default model, since
the file has no `claude` section. Workers knows no Operation names; the entries are whatever the
[`configure_workers`](../../operations/module.md#concept.operations.configure-workers) Operation
wrote after checking them against the catalog. [Tasks](../../tasks/module.md) copies the primary
worktree's file into a task worktree when it opens the task, so a task keeps the configuration it
started with and a later change in the primary worktree never reaches it.

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
main agent asks with its question tool ([Main session](../main-session/module.md)).

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
worker's claim as fact. Delivery later collects these into a task's evidence.

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
  runtime -> claude: launches
  runtime -> pi: launches
}
```

- <a id="realization.workers.runtime"></a>The **worker runtime** writes the brief, decides rounds,
  runs the write audit, keeps the progress file, manages run directories/records, and supplies the
  worker prompt snippets every Operation includes, e.g. reporting an error. Its tests also exercise
  the Harness's worker settings, write hook and pi path decisions, since a worker run is where they
  apply.
- <a id="realization.workers.claude"></a>The **Claude Code backend** places the worker settings and
  write hook the Harness generates, launches and resumes `claude -p`, and reads its event stream.
  Tests fake `claude` for host behaviour and, with `CONCORDE_LIVE_CLAUDE=1`, run a real worker for
  what only Claude Code enforces.
- <a id="realization.workers.pi"></a>The **pi backend** checks its prerequisites, prepares the pi
  configuration directory, embeds the run's policy into the Harness's permission extension,
  launches and resumes `pi -p` and reads its event stream. Tests fake `pi` for host behaviour, run
  the path decisions under Node, and, with `CONCORDE_LIVE_PI=1`, run a real pi worker.

- <a id="realization.workers.models"></a>The **model configuration** detects the main
  session's program, resolves a worker's backend and checks that its program is installed,
  discovers the candidates by running the installed `claude` or `pi`, validates, reads and writes
  `.concorde/worker-models.json`, and resolves the choice of an Operation's worker role. Tests fake
  both programs.

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

## Relationships

```d2
workers: Workers
spec: Spec core
harness: Harness
checks: Check execution
workers -> spec
workers -> harness
workers -> checks
```

```d2
runtime: Worker runtime
brief: Brief
dir: Run directory
record: Run record
audit: Write audit
round: Resume round
result: Worker result
runtime -> brief: generates
runtime -> record: writes
dir -> record: holds
record -> audit: records
record -> round: records
record -> result: keeps
runtime -> progress: keeps
dir -> progress: holds
progress: Progress file
backend: Worker backend
```

The Operation providers, Spec review and Delivery use this Module; it knows none of them. They rely
on the run record and on the rule that a worker's result is kept apart from host evidence.

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

<a id="uses-checks"></a>

**Check execution** runs the [configured checks](../../checks/module.md#concept.checks.configured-check)
on the task worktree in its read-only boundary, returning a [check
result](../../checks/module.md#concept.checks.check-result) per check with its log. Workers relies on
checks never changing the worktree; it runs them only after a clean audit, feeds failures into the
next round, and records every result. Checks that cannot run end the run `failed` with the error as
evidence and no round.
