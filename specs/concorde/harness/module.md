# Harness

## Purpose

The Harness is how Concorde derives an agent's harness and applies it to the agent: what the agent
is given to know, what it may touch and the environment it runs in, turned into the agent program's
own configuration: on Claude Code for every agent, and on pi for a worker, since the main agent and
task sessions run on Claude Code only for now while a worker may run on pi. It is independent of
which agent it serves. The Harness generates the configuration that applies a harness; it does not
launch or resume agents, compute grants, audit what an agent changed or run checks, which the agent
Modules and [Check execution](../execution/checks/module.md) do. What it enforces guards against
scope drift and mistakes, not a malicious agent.

## Core concepts

### The agent harness

<a id="concept.agent-harness"></a>

An **[agent harness](../glossary.json#concept.agent-harness)** has three parts, and the three agent
levels need very different amounts of each:

| | Main session | Task session | Worker |
| --- | --- | --- | --- |
| Context | the installed [guidance](../glossary.json#concept.main-session-guidance) and whatever the developer's own configuration adds | the developer's configuration, the task-session guidance and the task's goal, Modules and decision log | only its brief: the [Operation](../glossary.json#concept.operation)'s instructions and the grant's `rw`, `ro` and `names` lists, from which it reads its [Spec context](../glossary.json#concept.spec-context), [external context](../glossary.json#concept.external-context), [implementation context](../glossary.json#concept.implementation-context) and [task context](../glossary.json#concept.task-context); its tool set is its [capability context](../glossary.json#concept.capability-context) |
| Permission | none | file tools and shell write only the task worktree, its decision log and what commits and runs need; reads and the network open | the grant: `rw` writable, `ro` readable, `names` named only, everything else hidden; no network, no Git |
| Environment | the developer's | the developer's Claude Code configuration | its own configuration directory, a cleared environment, its own working directory and limits |
| Applied by | Distribution, which installs the guidance | the [session boundary](../glossary.json#concept.session-boundary), for Task sessions | [worker settings](../glossary.json#concept.worker-settings) or the [permission extension](../glossary.json#concept.permission-extension), for Workers |

The context of a worker, its five kinds and how each is computed are defined in the
[shared vocabulary](../glossary.json#concept.context); the Harness decides how that context reaches
the agent, which for a worker is the brief and the files the grant lets it read. The permission and
environment are what the Harness generates.

### A worker's harness

<a id="concept.worker-settings"></a><a id="concept.deny-rules"></a><a id="concept.write-hook"></a>

**A worker on Claude Code.** The **worker settings** are the worker's only configuration (a fresh
`CLAUDE_CONFIG_DIR`) and hold three layers from the same grant.
**[Deny rules](../glossary.json#concept.deny-rules)** cover the file tools. They deny Read and Edit
for every grant-omitted task-worktree path and every `names` path, Edit for every `ro` path, and
Read and Edit for each ungranted directory as a whole, the primary worktree, `.git`,
`~/.claude` and the runtime directory's `control/` and `config/`; the
[Claude Code mechanics](claude-code.md#deny-rules) list them exactly. They hold under
`bypassPermissions` and make Grep silently omit denied files. Since Claude Code applies `Read`
denials to Bash too, they never cover system directories or the **runtime paths**: the paths Bash
itself needs to read, such as the toolchain, `.venv` or `node_modules`, which Workers passes with
the run as [one of its inputs](../execution/workers/launch.md#inputs) and the Harness only receives.
The **[write hook](../glossary.json#concept.write-hook)** makes `rw` the exact write allowlist,
denying any other Edit or Write with a reason naming the path's level; for a path outside the
grant the reason says both that a file no Module declares needs a `specify` task first and that a
file another Module declares needs that Module bound. It says nothing about `rw` and never governs
reads. The Bash sandbox denies reading the worktree and `$HOME` except `ro` and `rw` files and
runtime paths, allows writing only the `rw` files and the run's `work/`, `home/` and temporary
directory, allows no network, and ignores unsandboxed-command requests. `names` files are readable
by no tool, only named in the brief. The tool set of each [task type](../glossary.json#concept.task-type) is chosen here too.
Exact shapes: [Claude Code mechanics](claude-code.md).

<a id="concept.permission-extension"></a>

**A worker on pi.** The **permission extension** replaces the worker settings, generated from the
same grant by the same code:

| Surface | Claude Code | pi |
| --- | --- | --- |
| Reading files | deny rules on Read, Glob and Grep | the extension checks `read` and explains each denial |
| Writing files | deny rules plus the write hook | the extension checks `write` and `edit` with the write hook's table |
| Searching | Grep silently omits denied files | `grep`, `find` and `ls` run inside the sandbox, so denied files do not exist for them |
| Commands | Claude Code's Bash sandbox | `bash` through the same sandbox engine, sandbox-runtime |
| Network | none, strict allowlist | none, strict allowlist |
| [Worker result](../glossary.json#concept.worker-result) | `--json-schema` | the `concorde_result` tool |
| Limits | `--max-turns`, `--max-budget-usd` | counted and enforced by the extension |
| Instructions and state | own `CLAUDE_CONFIG_DIR`, no `CLAUDE.md` | own `PI_CODING_AGENT_DIR`, no extensions, context files, skills or templates |

Exact tables: [pi mechanics](pi.md).

### The session boundary

<a id="concept.session-boundary"></a>

The **session boundary** confines what a task session writes and nothing else.
A task session runs on Claude Code, so its boundary is a settings file with a write hook of its own, which lets Edit and Write change
only the task worktree and its decision log instead of a grant's `rw` list, and a Bash sandbox that
writes only the task worktree, the repository's Git directory (for commits on the task branch), the
task's own folder `.concorde/tasks/<task>/` of the primary worktree (which holds the workspace
folder that the task worktree's [workspace binding](../glossary.json#concept.workspace-binding)
names for every run started there, and the [task record](../glossary.json#concept.task-record) in which escalations are recorded), the
primary worktree's `.concorde/locks/` (where those runs take their locks) and `.concorde/issues/`
(where those runs write the project's [Issues](../glossary.json#concept.issue), each write taking
the [merge lock](../glossary.json#concept.merge-lock) and committing its record through the Git
directory) and the user's package caches, with every network host allowed. The write hook still
refuses an Issue record, so the session's own Edit and Write never write one. Once the task is closed its folder has moved to the
[history](../glossary.json#concept.history), and the write hook refuses every write to the decision
log, whose folder no longer exists, rather than recreate it. The open network is reached through the sandbox's
proxy on `localhost`, because the sandboxed commands have a network namespace of their own; a worker
those commands start passes that proxy on to its own process (Workers'
[proxy rule](../execution/workers/launch.md#proxy)), never to its tools, whose sandbox stays without
network. The session's MCP servers are not inside the boundary: Claude Code runs them outside the
Bash sandbox, and the [project MCP server](../glossary.json#concept.project-mcp-server) that every
task session receives can change task records and take locks for any task. The developer chose not
to confine it: it is a management tool, the task-session guidance says what a task session may do
with it, and the boundary stays a guard against a session's mistakes in its files and shell.
Exact shapes: [Claude Code mechanics](claude-code.md#task-session-settings).

## Overview

### Where the Harness sits

The Harness serves every agent level of Concorde's [levels of work](../module.md#the-levels-of-work)
without being a level itself: it sits in no call chain from the main session down to a worker, and
no result or [error chain](../glossary.json#concept.error-chain) passes through it. Each
[agent](../coordination/module.md) level asks for the harness it needs: Workers for a worker, from
the frozen [grant](../glossary.json#concept.grant) of its task; Task sessions for a
[task session](../glossary.json#concept.task-session), from its task's worktree and
[decision log](../glossary.json#concept.decision-log); the main session's harness is its installed
guidance alone, which Distribution installs directly, since Concorde places no permission limits on
the [main agent](../glossary.json#concept.main-agent).

```d2 illustrative
direction: down
modules: Agent Modules {
  workers: Workers
  sessions: Task sessions
  distribution: Distribution
}
harness: Harness {
  worker: "worker settings or\npermission extension,\ntool set"
  session: "task-session\nwrite hook"
}
programs: Agent programs {
  worker: "worker\nClaude Code or pi"
  session: "task session\nClaude Code"
  main: "main agent\nClaude Code"
}
modules.workers -> harness.worker: "from a frozen grant,\nruntime directory,\nruntime paths"
modules.sessions -> harness.session: "from a task worktree\nand decision log"
harness.worker -> programs.worker: "Workers launches\nwith it and the brief"
harness.session -> programs.session: "Task sessions starts it\nwith settings around the hook"
modules.distribution -> programs.main: "installs the guidance;\nno permission limits"
```

It is used as a library: an agent Module assembles the inputs of its level — a frozen grant and
[runtime directory](../glossary.json#concept.runtime-directory), or a task's paths — and asks the
Harness for the configuration, which it then hands to the program it launches. Each level differs
only in what it asks for; the Harness holds the one place that turns those inputs into a program's
own configuration.

### A worker's harness at work

**A worked example.** Take a project whose Module Checkout owns the Spec
`specs/shop/checkout/module.md` and binds `src/checkout/cart.py`, beside a Module Billing with the
Spec `specs/shop/billing/module.md` and the code `src/billing/invoice.py`, which Checkout does not
use. A task bound to Checkout runs the `implement` Operation, whose step freezes this grant, among
others of the same kinds:

| Path | Level | Why |
| --- | --- | --- |
| `src/checkout/cart.py` | `rw` | Checkout's implementation scope |
| `specs/shop/checkout/module.md` | `ro` | Checkout's Spec context |
| `src/billing/invoice.py` | `ro` | the project's code, which an `implement` task reads whole |
| `specs/shop/billing/module.md` | none | outside every [boundary set](../glossary.json#concept.boundary-set) of Checkout |

Workers hands the Harness that grant, the runtime directory and the runtime paths. For a Claude Code
worker the Harness returns the worker settings: deny rules `Edit` on the Checkout Spec and on
`invoice.py`, `Read` and `Edit` on `specs/shop/billing/**`, since no granted path lies below it,
and the rules that hide the rest of the home directory and the run's own configuration; the write
hook with `cart.py` as its only writable path; a Bash sandbox that reads the three granted files and
writes only `cart.py` and the run's directories; and the `implement` tool set. For a pi worker it
returns the permission extension, generated from the same grant. Workers launches the worker with
that configuration and the brief, which lists the three granted paths. The worker edits `cart.py`:
no rule denies it and the write hook allows it. It then tries to write a new file
`src/checkout/discount.py`: no deny rule names a file that does not exist yet, but the write hook
refuses it, and the worker sees the reason "Concorde grant: src/checkout/discount.py is not in
this task's grant; a new file outside the bound directories is created and bound to a Module by the
task level before a worker fills it, and a file another Module binds needs that Module bound to the
task",
the hook's reason with the prefix it adds to every denial. A worker that needs that file says so in
its [worker result](../glossary.json#concept.worker-result), and Workers audits the changes and
records the run:

```d2 illustrative
direction: right
workers: Workers (agent Module) {
  direction: down
  hand: "1. Hand over the frozen grant,\nruntime directory, runtime paths"
  launch: "3. Launch the worker with\nthe configuration and the brief"
  audit: "7. Write audit, checks,\nrun record"
}
harness: Harness {
  generate: "2. Generate the worker settings\nor the permission extension,\nand the tool set"
}
program: "Claude Code or pi (agent program)" {
  direction: down
  edit: "4. Edit src/checkout/cart.py:\nrw, allowed"
  write: "5. Write src/checkout/discount.py:\ndenied, not in the grant"
  result: "6. Return the worker result"
  edit -> write -> result
}
workers.hand -> harness.generate
harness.generate -> workers.launch: configuration
workers.launch -> program.edit
program.result -> workers.audit
```

A `names` path never appears in an `implement` grant, since such a task reads the project's code
whole; it appears, for instance, in an `understand` grant, whose worker may see an implementation
file's name in its brief but read it with no tool.

### Its parts

Each backend's realization produces the parts of a harness it is responsible for; the Claude Code
harness alone carries a worker's deny rules and write hook inside one settings file, since both
must be checked from the same generator to stay consistent, while pi checks the same decisions
through a single extension instead:

```d2
claude: Claude Code harness
pi: pi harness
settings: Worker settings
deny: Deny rules
hook: Write hook
ext: Permission extension
session: Session boundary
claude -> settings: generates
settings -> deny: carries
settings -> hook: carries
pi -> ext: provides
claude -> session: provides the write hook of
```

The [realizations](#the-realizations) below say which files carry each part.

## How it is built

### Around it

The agent Modules use the Harness; it knows none of them and receives everything it needs as
inputs, including a worker's runtime directory and runtime paths from Workers.

<a id="uses-spec"></a>

**Spec core** computes the [grant](../glossary.json#concept.grant) a worker's
harness is generated from. The Harness relies on the grant listing every path's level (`rw`, `ro`,
`names`, ungranted omitted); it never computes or widens a grant, only receives it frozen from
Workers. It generates nothing from a malformed grant: one that has no `entries` list, or an entry
that is not an object with a non-empty path relative to the task worktree, never absolute and never
leaving it through `..`, and a level of `rw`, `ro` or `names`. Settings generation then raises a
`SettingsError` with the code `grant_malformed` naming the first such entry and what is wrong with
it, which Workers reports as its [refusal to launch](../execution/workers/launch.md#errors).

**pi**, whose pinned copy under `references/pi/` is the version the pi harness was written against,
is relied on for its extension API: a tool an extension registers replaces pi's built-in of the
same name; pi validates a tool's arguments against the tool's parameter schema before running it;
`tool_call` handlers run in extension load order and may change a call's input or block it, and a
handler that throws blocks the tool; a tool whose result asks to terminate ends the run when every
other tool called in the same assistant message asks it too. The path decisions resolve a tool's
path argument exactly as pi resolves it.

### Why the Harness is separate

The Harness is separate from the agents because what it produces does not depend on who runs the
agent or why: the same write-hook table and sandbox settings serve a worker and a task session, and
a worker's harness on either program comes from the same grant by the same code. The agent Modules keep what does: when an agent starts, how its rounds go, what is audited and
recorded. So a new kind of agent, or a new level, needs a new set of inputs for the Harness, not a
new enforcement mechanism.

### One grant, compiled for each program

A worker's harness is compiled for each agent program rather than one being translated into the
other: Claude Code's permission-rule language is closed and changes between versions, and pi has no
permission system of its own, so the grant is the one source and each program gets the mechanism
that fits it. On pi the file tools are checked by an extension because an extension sees every tool
call before it runs and can explain a denial; searching and commands go through the sandbox because
only an OS boundary confines what a command or a search actually opens. The worker's tools are
replaced rather than merely intercepted, so the check sees the final arguments, which a later
`tool_call` handler could otherwise still change.

### Three layers on Claude Code

A worker gets three layers on Claude Code since each alone failed in a spike against Claude Code
2.1.280: the Bash sandbox governs only Bash and its children — alone it let Read return ungranted
files and Claude Code's credential file, and Edit change a read-only
[Spec](../glossary.json#concept.spec); deny rules alone confine reads but can't stop a Write
creating an undeclared file, since a deny rule always beats an allow rule, so "only these files are
writable" cannot be expressed. The write hook closes exactly that gap, staying small. A task
session needs only the write side, because its reads and network are open by design, so it gets
the hook and the sandbox without deny rules.

### What a worker's harness enforces in v1

The table describes the Claude Code backend; the pi backend enforces the same surfaces with its
permission extension and sandbox-runtime, as the pi table under
[Core concepts](#core-concepts) compares. Workers sets the launch
flags and environment listed here; the Harness generates everything the settings hold.

| Surface | Mechanism | What it stops |
| --- | --- | --- |
| Read, Glob, Grep | `permissions.deny` for the grant's complement in the task worktree; the primary worktree; `.git`, `~/.claude` with Claude Code's credential file | Ungranted/`names` reads; Grep silently omits them |
| Edit, Write | Same deny rules, plus a write-only PreToolUse hook denying non-`rw` paths, reason naming the level | `ro` edits or new files — deny alone can't, since deny beats allow |
| Bash | Sandbox: `denyRead` worktree/`$HOME`, `allowRead` granted files + runtime paths, `allowWrite` `rw` files + the runtime directory's `work/`, `home/`, `tmp/`, no network, `allowUnsandboxedCommands: false` | Ungranted reads, `ro` writes, network, `dangerouslyDisableSandbox` |
| Permission mode | `bypassPermissions` via `--allow-dangerously-skip-permissions`; deny rules/hook/sandbox are the boundary | Nothing alone; `dontAsk` denies writes outside the working dir even when allowed |
| Working directory | The runtime directory's `work/`, never the task worktree | Claude Code adding the worktree to the Bash sandbox's read/write set |
| Tool set | `--tools` per task type, never WebFetch/WebSearch, no agent tool | Web access via tools, workers starting other agents |
| MCP | `--strict-mcp-config` with no servers | Any tool beyond the listed ones |
| Claude state/instructions | Own `CLAUDE_CONFIG_DIR`, cleared env, `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` | User settings, memory, skills, plugins, transcripts, project instructions |
| Git | No tool reads `.git`; diffs belong to Workers and commits to Delivery | A worker inspecting or rewriting history |
| Changes | Workers audits `git diff`/untracked files against the grant each round | Any remaining write outside `rw` counting as a result |
| Limits | Timeout, `--max-turns`, `--max-budget-usd`, kill of the process group at round end | Runaway runs and leftover processes |

### Known limits of v1

- The Claude or pi process, the write hooks and the extensions are not sandboxed. The file-tool
  boundary is only as good as the generated deny rules, hooks and extensions are complete and
  correct.
- Deny rules cover the task worktree and home directory; system directories and other paths outside
  the home stay readable to every tool, since Bash needs them to run anything.
- A read denial's message is Claude Code's generic "denied by your permission settings", so the
  brief states the grant; write denials explain themselves via the hook.
- A single `rw` file granted to Bash is bind-mounted, so it can't be deleted or renamed from Bash,
  and a file created outside `rw` appears to succeed but lands on a throw-away filesystem, unseen by
  the audit — the brief warns of this.
- Writes to Git-ignored paths are not audited; Workers' audit is the last line of defense for a
  worker's write outside `rw`.
- A task session's boundary does not cover tools that plugins or MCP servers add, such as a
  formatter that writes files.
- On Claude Code a file created in the task worktree after the deny rules were generated has no
  rule of its own: the write hook still refuses to change it unless it is `rw`, and a directory rule
  hides it when its directory has no `ro` or `rw` path below it, but otherwise the file tools can
  read it. The worker itself cannot create such a file; pi's read check has no such gap, since it
  judges every path when it is read.

Future work: an outer sandbox-runtime (`srt`) sandbox around the agent process and proxied
credentials.

### The realizations

<a id="realization.harness.package"></a>

The **Harness package** is `concorde.harness`'s Python package marker. The package also holds the
code of Workers and Check execution, which bind their own files; a
[Module](../glossary.json#concept.module) need not match a package.

<a id="realization.harness.claude"></a>

The **Claude Code harness** is the worker settings generator (`settings.py`: the run's paths, the
deny rules, the Bash sandbox lists, the tool set of a task type and the complete settings file),
the worker write hook (`write_hook.py`) and the task-session write hook (`session_hook.py`). Workers
writes the settings and the hook, with the grant's lists embedded, into the runtime directory's `control/`, and
Task sessions assembles the rest of a task session's settings around its hook.

<a id="realization.harness.pi"></a>

The **pi harness** is the worker's permission extension (`pi_permission.ts`) with the pure path
decisions of its read and write tables (`pi_policy.ts`), which resolve paths exactly as pi does.
Workers embeds the policy into these sources and copies them into place.

### Where its promises are required

The Harness holds no requirements or scenarios of its own. What it generates is only observable
once an agent Module applies it to an agent, so each decidable promise is a requirement of the
Module that applies it, and the tests that verify those requirements exercise the Harness's files:

- A worker's harness, in Workers: one frozen grant for the whole run and every round
  ([req.workers.frozen-grant](../execution/workers/launch.md#req.workers.frozen-grant),
  [req.workers.unchanged-across-rounds](../execution/workers/launch.md#req.workers.unchanged-across-rounds)),
  no launch from a malformed grant
  ([req.workers.malformed-grant](../execution/workers/launch.md#req.workers.malformed-grant)),
  `rw` as the exact write allowlist
  ([req.workers.write-allowlist](../execution/workers/launch.md#req.workers.write-allowlist)),
  the deny rules
  ([req.workers.read-denials](../execution/workers/launch.md#req.workers.read-denials)), the Bash
  sandbox ([req.workers.bash-sandbox](../execution/workers/launch.md#req.workers.bash-sandbox)),
  no Git ([req.workers.no-git](../execution/workers/launch.md#req.workers.no-git)), the same grant
  on pi ([req.workers.pi-same-grant](../execution/workers/pi.md#req.workers.pi-same-grant)), the
  permission extension's file tools, sandbox, configuration and limits
  ([req.workers.pi-file-tools](../execution/workers/pi.md#req.workers.pi-file-tools),
  [req.workers.pi-sandbox](../execution/workers/pi.md#req.workers.pi-sandbox),
  [req.workers.pi-only-extension](../execution/workers/pi.md#req.workers.pi-only-extension),
  [req.workers.pi-limits](../execution/workers/pi.md#req.workers.pi-limits)).
- A task session's harness, in Task sessions: the session boundary's file tools and shell
  ([req.task-session.boundary](../coordination/task-session/requirements.md#req.task-session.boundary),
  [req.task-session.shell-boundary](../coordination/task-session/requirements.md#req.task-session.shell-boundary))
  and the boundary written before the session starts
  ([req.task-session.boundary-first](../coordination/task-session/requirements.md#req.task-session.boundary-first)).

The Workers tests run fake and, on request, live workers and the pi path decisions under Node; the
Task session tests run the task-session hook and settings.
