# Workers

## Purpose

Workers runs one headless Claude Code worker for one task under one frozen grant, and turns what
happened into a run record the Operation host can trust. It does not compute the grant, choose the
task type or write the task-specific brief, and never commits or judges whether the worker's work
is correct. Its boundary guards against scope drift and mistakes, not a malicious worker, and it
supports only Claude Code. None of its code exists yet: everything here is the design its
implementation must follow.

## Terminology

| Term | Definition |
| --- | --- |
| Worker settings | The Claude Code settings file the host generates from a grant, carrying the Bash sandbox, the deny rules and the write hook of one worker run. |
| Deny rules | The `permissions.deny` entries of the worker settings that forbid the file tools every path the grant does not make readable or writable. |
| Write hook | A small PreToolUse hook on Edit and Write that denies every path outside the grant's `rw` list and explains the denial. |
| Brief | The prompt a worker receives: the Operation's task instructions followed by the grant's `rw`, `ro` and `names` lists as absolute paths and the rules of its boundary. |
| Worker result | The structured answer a worker ends with, validated against a fixed schema, reporting its status, a summary, its own error link when it could not finish, and the deletions it proposes. |
| Write audit | The host's comparison, after each round and outside the worker, of the task worktree's changes with the grant's `rw` list. |
| Resume round | One continuation of the same worker session with the failures of the configured checks, started by `claude -p --resume`. |
| Run record | The host's durable record of one worker run: its grant and context identity, settings, transcript path, audits, checks, rounds and result. |
| Run directory | The directory `.concorde/runs/<run-id>/` of the primary worktree that holds one run's record, generated configuration and the worker's private state and working directory. |
| [Worker](../../vocabulary.md#concept.concorde.worker) | |
| [Task type](../../vocabulary.md#concept.concorde.task-type) | |
| [Boundary](../../vocabulary.md#concept.concorde.boundary) | |
| [Evidence](../../vocabulary.md#concept.concorde.evidence) | |
| [Error chain](../../vocabulary.md#concept.concorde.error-chain) | |
| [Grant](../../spec-tooling/spec/module.md#concept.spec.grant) | |
| [Context identity](../../spec-tooling/spec/module.md#concept.spec.context-identity) | |
| [Configured check](../checks/module.md#concept.checks.configured-check) | |
| [Check result](../checks/module.md#concept.checks.check-result) | |

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

<a id="concept.workers.worker-settings"></a><a id="concept.workers.deny-rules"></a><a id="concept.workers.write-hook"></a>

The **worker settings** are the worker's only configuration (fresh `CLAUDE_CONFIG_DIR`) and hold
three layers from the same grant. **Deny rules** cover the file tools: every grant-omitted
task-worktree path (Read+Edit denied), every `ro`/`names` path (Edit denied, Read too for `names`),
one rule per ungranted directory, the primary worktree outside this run, `.git`, `~/.claude`, and
the run's `control/`/`config/`; they hold under `bypassPermissions`, make Grep silently omit denied
files, and — since Claude Code applies `Read` denials to Bash too — never cover system or runtime
paths Bash itself needs. The **write hook** makes `rw` the exact write allowlist, denying any other
Edit/Write with a reason naming the path's level (e.g. an undeclared file needing `specify` first);
it says nothing about `rw` and never governs reads. The Bash sandbox denies reading the
worktree/`$HOME` except `ro`/`rw` files and runtime paths, allows writing only the `rw` files and
the run's `work/`, `home/` and temporary directory, allows no network, and ignores
unsandboxed-command requests. `names` files are readable by no tool — only named in the brief.

<a id="concept.workers.brief"></a>

The **brief** is the worker's only instruction — `CLAUDE.md`, auto memory and user settings are
disabled — the Operation's task instructions plus the boundary Workers appends: `rw`/`ro`/`names` as
absolute paths (its working directory isn't the worktree); that it can't delete, only propose
deletions; that a Bash-created file outside `rw` is silently lost; and that a read denial means the
path is outside its grant.

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

A **resume round** happens only when the worker ended `ok`, the audit was clean, and a check failed:
the host sends each failure's identity, exit code and log tail to `claude -p --resume <session>`,
tracking the new session id returned. A `blocked`/`failed` result or an audit violation is never
resumed — those go to the main agent; when the rounds are used up and a check still fails, the run
ends `failed` with the last check results.

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
    "settings.py"
    "write_hook.py"
    "workers.py"
    "audit.py"
    "runs.py"
    "prompts/workers/common/"
  }
}
```

- <a id="realization.workers.runtime"></a>The **worker runtime** generates settings (deny rules,
  sandbox, hook registration), enforces the write hook, launches/resumes the worker while deciding
  rounds, runs the write audit, manages run directories/records, and supplies the worker prompt
  snippets every Operation includes, e.g. reporting an error. Tests fake `claude` for host behaviour
  and, with `CONCORDE_LIVE_CLAUDE=1`, run a real worker for what only Claude Code enforces.

Three layers exist since each alone failed in a spike against Claude Code 2.1.280: the Bash sandbox
governs only Bash and its children — alone it let Read return ungranted files and the credential,
and Edit change a read-only Spec; deny rules alone confine reads but can't stop a Write creating an
undeclared file, since a deny rule always beats an allow rule, so "only these files are writable"
cannot be expressed. The write hook closes exactly that gap, staying small.

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
is future work alongside the outer sandbox. Limits: the [Harness](../module.md).

Open questions: whether Bash needs read access to Claude Code's shell snapshots in
`CLAUDE_CONFIG_DIR` (deciding if `config/` stays unreadable) awaits the built runtime; per-task tool
lists are v1 defaults in [the run mechanics](launch.md#tool-sets) and may change.

## Relationships

```d2
workers: Workers
spec: Spec core
checks: Check execution
workers -> spec
workers -> checks
```

```d2
runtime: Worker runtime
settings: Worker settings
deny: Deny rules
hook: Write hook
brief: Brief
dir: Run directory
record: Run record
audit: Write audit
round: Resume round
result: Worker result
runtime -> settings: generates
runtime -> brief: generates
runtime -> record: writes
settings -> deny: carries
settings -> hook: carries
dir -> settings: holds
dir -> record: holds
record -> audit: records
record -> round: records
record -> result: keeps
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

<a id="uses-checks"></a>

**Check execution** runs the [configured checks](../checks/module.md#concept.checks.configured-check)
on the task worktree in its read-only boundary, returning a [check
result](../checks/module.md#concept.checks.check-result) per check with its log. Workers relies on
checks never changing the worktree; it runs them only after a clean audit, feeds failures into the
next round, and records every result. Checks that cannot run end the run `failed` with the error as
evidence and no round.
