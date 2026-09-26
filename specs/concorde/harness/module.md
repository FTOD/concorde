# Harness

## Purpose

The Harness is how Concorde derives an agent's harness and applies it to the agent: what the agent
is given to know, what it may touch and the environment it runs in, turned into the agent
program's own configuration on Claude Code or on pi. It is independent of which agent it serves.
Each [agent](../agents/module.md) level asks for the harness it needs: Workers for a worker, from
the frozen grant of its task; Task sessions for a task session, from its task's worktree and
decision log; the main session's harness is its installed guidance alone, since Concorde places no
permission limits on the main agent. The Harness generates the configuration that applies a
harness; it does not launch or resume agents, compute grants, audit what an agent changed or run
checks, which the agent Modules and [Check execution](../checks/module.md) do. What it enforces
guards against scope drift and mistakes, not a malicious agent.

## Terminology

| Term | Definition |
| --- | --- |
| Agent harness | The context, permission and environment Concorde gives one agent, derived from the Specs and the agent's task and applied through the agent program's own configuration. |
| Worker settings | The Claude Code settings file the Harness generates from a grant, carrying the Bash sandbox, the deny rules and the write hook of one worker run. |
| Deny rules | The `permissions.deny` entries of the worker settings that forbid the file tools every path the grant does not make readable or writable. |
| Write hook | A small PreToolUse hook on Edit and Write that denies every path outside the grant's `rw` list and explains the denial. |
| Permission extension | The pi extension the Harness generates from a grant, which checks every file tool against it, runs every command in the sandbox and receives the worker result. |
| Session boundary | The settings and write hook on Claude Code, or the boundary extension on pi, that confine a task session's file tools and shell to its task, leaving reads and the network open. |
| [Main agent](../vocabulary.md#concept.concorde.main-agent) | |
| [Task session](../vocabulary.md#concept.concorde.task-session) | |
| [Worker](../vocabulary.md#concept.concorde.worker) | |
| [Context](../vocabulary.md#concept.concorde.context) | |
| [Boundary](../vocabulary.md#concept.concorde.boundary) | |
| [Grant](../spec-tooling/spec/module.md#concept.spec.grant) | |

The worker settings, deny rules and write hook apply a worker's harness on Claude Code, the
permission extension on pi; the session boundary applies a task session's harness on both.

## Usage

<a id="concept.harness.harness"></a>

An **agent harness** has three parts, and the three agent levels need very different amounts of
each:

| | Main session | Task session | Worker |
| --- | --- | --- | --- |
| Context | the installed [guidance](../agents/main-session/module.md#concept.main-session.guidance) and whatever the developer's own configuration adds | the developer's configuration, the task-session guidance and the task's goal, Modules and decision log | only its brief: the Operation's instructions and the grant's `rw`, `ro` and `names` lists, from which it reads its Spec, implementation and task context; its tool set is its capability context |
| Permission | none | file tools and shell write only the task worktree, its decision log and what commits and runs need; reads and the network open | the grant: `rw` writable, `ro` readable, `names` named only, everything else hidden; no network, no Git |
| Environment | the developer's | the developer's configuration and program | its own configuration directory, a cleared environment, its own working directory and limits |
| Applied by | Distribution, which installs the guidance | the session boundary, for Task sessions | worker settings or the permission extension, for Workers |

The context of a worker, its four kinds and how each is computed are defined in the
[shared vocabulary](../vocabulary.md#concept.concorde.context); the Harness decides how that context
reaches the agent, which for a worker is the brief and the files the grant lets it read. The
permission and environment are what the Harness generates. It is used as a library: an agent
Module assembles the inputs of its level — a frozen grant and run directory, or a task's paths —
and asks the Harness for the configuration, which it then hands to the program it launches.

<a id="concept.harness.worker-settings"></a><a id="concept.harness.deny-rules"></a><a id="concept.harness.write-hook"></a>

**A worker on Claude Code.** The **worker settings** are the worker's only configuration (a fresh
`CLAUDE_CONFIG_DIR`) and hold three layers from the same grant. **Deny rules** cover the file
tools: every grant-omitted task-worktree path (Read and Edit denied), every `ro` or `names` path
(Edit denied, Read too for `names`), one rule per ungranted directory, the primary worktree outside
the run, `.git`, `~/.claude`, and the run's `control/` and `config/`; they hold under
`bypassPermissions`, make Grep silently omit denied files, and — since Claude Code applies `Read`
denials to Bash too — never cover system or runtime paths Bash itself needs. The **write hook**
makes `rw` the exact write allowlist, denying any other Edit or Write with a reason naming the
path's level (e.g. an undeclared file needing `specify` first); it says nothing about `rw` and never
governs reads. The Bash sandbox denies reading the worktree and `$HOME` except `ro` and `rw` files
and runtime paths, allows writing only the `rw` files and the run's `work/`, `home/` and temporary
directory, allows no network, and ignores unsandboxed-command requests. `names` files are readable
by no tool, only named in the brief. The tool set of each task type is chosen here too. Exact
shapes: [Claude Code mechanics](claude-code.md).

<a id="concept.harness.permission-extension"></a>

**A worker on pi.** The **permission extension** replaces the worker settings, generated from the
same grant by the same code:

| Surface | Claude Code | pi |
| --- | --- | --- |
| Reading files | deny rules on Read, Glob and Grep | the extension checks `read` and explains each denial |
| Writing files | deny rules plus the write hook | the extension checks `write` and `edit` with the write hook's table |
| Searching | Grep silently omits denied files | `grep`, `find` and `ls` run inside the sandbox, so denied files do not exist for them |
| Commands | Claude Code's Bash sandbox | `bash` through the same sandbox engine, sandbox-runtime |
| Network | none, strict allowlist | none, strict allowlist |
| Worker result | `--json-schema` | the `concorde_result` tool |
| Limits | `--max-turns`, `--max-budget-usd` | counted and enforced by the extension |
| Instructions and state | own `CLAUDE_CONFIG_DIR`, no `CLAUDE.md` | own `PI_CODING_AGENT_DIR`, no extensions, context files, skills or templates |

Exact tables: [pi mechanics](pi.md).

<a id="concept.harness.session-boundary"></a>

**A task session.** The **session boundary** confines what a task session writes and nothing else.
On Claude Code it is a settings file with a write hook that lets Edit and Write change only the
task worktree and its decision log, and a Bash sandbox that writes only the task worktree, the
repository's Git directory (for commits on the task branch), `.concorde/runs/` and
`.concorde/tasks/` (for Operation runs and records) and the user's package caches, with every
network host allowed. On pi it is the boundary extension, loaded on top of the developer's own
configuration, which blocks a `write` or `edit` outside the same two places, naming the task
worktree, rewrites every `bash` command to run inside sandbox-runtime with the same writable paths
and open network plus a private temporary directory, and gives the session its `concorde_report`
tool. Exact shapes: [Claude Code mechanics](claude-code.md#task-session-settings) and
[pi mechanics](pi.md#session-boundary-extension).

## Design

The Harness serves every [agent level](../module.md#the-five-levels) of Concorde's five-level
hierarchy without being a level itself: it sits in no call chain from the main session down to a
worker, and no result or error chain passes through it. Workers asks it for a worker's harness
from a frozen grant, Task sessions for a task session's harness from a task's paths, and
Distribution installs the main session's guidance directly since Concorde places no permission
limits there. Each level differs only in what it asks for; the Harness holds the one place that
turns those inputs into a program's own configuration.

### Around it

The agent Modules use the Harness; it knows none of them and receives everything it needs as
inputs.

<a id="uses-spec"></a>

**Spec core** computes the [grant](../spec-tooling/spec/module.md#concept.spec.grant) a worker's
harness is generated from. The Harness relies on the grant listing every path's level (`rw`, `ro`,
`names`, ungranted omitted); it never computes or widens a grant, only receives it frozen from
Workers, and generates nothing for a grant it cannot read.

### Inside

The Harness is separate from the agents because what it produces does not depend on who runs the
agent or why: the same deny-rule generator, write-hook table, pi path resolution and sandbox engine
serve a worker and a task session, and the pi task session's path decisions import the worker's.
The agent Modules keep what does: when an agent starts, how its rounds go, what is audited and
recorded. So a new kind of agent, or a new level, needs a new set of inputs for the Harness, not a
new enforcement mechanism.

A harness is compiled for each agent program rather than one being translated into the other:
Claude Code's permission-rule language is closed and changes between versions, and pi has no
permission system of its own, so the inputs — a grant, or a task's paths — are the one source and
each program gets the mechanism that fits it. On pi the file tools are checked by an extension
because an extension sees every tool call before it runs and can explain a denial; searching and
commands go through the sandbox because only an OS boundary confines what a command or a search
actually opens. A worker's tools are replaced rather than merely intercepted, so the check sees the
final arguments, which a later `tool_call` handler could otherwise still change; a task session's
are intercepted, so the developer's own extensions keep theirs.

A worker gets three layers on Claude Code since each alone failed in a spike against Claude Code
2.1.280: the Bash sandbox governs only Bash and its children — alone it let Read return ungranted
files and the credential, and Edit change a read-only Spec; deny rules alone confine reads but
can't stop a Write creating an undeclared file, since a deny rule always beats an allow rule, so
"only these files are writable" cannot be expressed. The write hook closes exactly that gap,
staying small. A task session needs only the write side, because its reads and network are open
by design, so it gets the hook and the sandbox without deny rules.

### What a worker's harness enforces in v1

The table describes the Claude Code backend; the pi backend enforces the same surfaces with its
permission extension and sandbox-runtime, as the table above compares. Workers sets the launch
flags and environment listed here; the Harness generates everything the settings hold.

| Surface | Mechanism | What it stops |
| --- | --- | --- |
| Read, Glob, Grep | `permissions.deny` for the grant's complement in the task worktree; the primary worktree outside the run dir; `.git`, `~/.claude`, the credential | Ungranted/`names` reads; Grep silently omits them |
| Edit, Write | Same deny rules, plus a write-only PreToolUse hook denying non-`rw` paths, reason naming the level | `ro` edits or new files — deny alone can't, since deny beats allow |
| Bash | Sandbox: `denyRead` worktree/`$HOME`, `allowRead` granted files + runtime paths, `allowWrite` `rw` files + run dirs, no network, `allowUnsandboxedCommands: false` | Ungranted reads, `ro` writes, network, `dangerouslyDisableSandbox` |
| Permission mode | `bypassPermissions` via `--allow-dangerously-skip-permissions`; deny rules/hook/sandbox are the boundary | Nothing alone; `dontAsk` denies writes outside the working dir even when allowed |
| Working directory | The run's own directory, never the task worktree | Claude Code adding the worktree to the Bash sandbox's read/write set |
| Tool set | `--tools` per task type, never WebFetch/WebSearch, no agent tool | Web access via tools, workers starting other agents |
| MCP | `--strict-mcp-config` with no servers | Any tool beyond the listed ones |
| Claude state/instructions | Own `CLAUDE_CONFIG_DIR`, cleared env, `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` | User settings, memory, skills, plugins, transcripts, project instructions |
| Git | No tool reads `.git`; diffs/commits belong to the host | A worker inspecting or rewriting history |
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
- Writes to Git-ignored paths are not audited; the host audit is the last line of defense for a
  worker's write outside `rw`.
- A task session's boundary does not cover tools other extensions or MCP servers add, such as a
  formatter that writes files.

Future work: an outer `srt` sandbox around the agent process and proxied credentials.

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
pi -> session: provides the extension of
```

<a id="realization.harness.package"></a>

The **Harness package** is `concorde.harness`'s Python package marker. The package also holds the
code of Workers and Check execution, which bind their own files; a Module need not match a package.

<a id="realization.harness.claude"></a>

The **Claude Code harness** is the worker settings generator (`settings.py`: the run's paths, the
deny rules, the Bash sandbox lists, the tool set of a task type and the complete settings file),
the worker write hook (`write_hook.py`) and the task-session write hook (`session_hook.py`). Task
session assembles the rest of a task session's settings around its hook.

<a id="realization.harness.pi"></a>

The **pi harness** is the worker's permission extension (`pi_permission.ts`) with the pure path
decisions of its read and write tables (`pi_policy.ts`), and the task session's boundary extension
(`pi_session.ts`) with its write decision and report check (`pi_session_policy.ts`), which imports
`pi_policy.ts` to resolve paths exactly as pi does. Workers and Task sessions embed the policy into
these sources and copy them into place.

The Harness has no tests of its own yet: its files are exercised by the Workers tests, which run
fake and, on request, live workers and the pi path decisions under Node, and by the Task session
tests, which run the task-session hook and boundary decisions.
