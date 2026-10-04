# Harness

## Purpose

The Harness is how the worker harness part applies a [worker](../../glossary.json#concept.worker)'s
[agent harness](../../glossary.json#concept.agent-harness): what the worker may read, write and run
and the environment it runs in, turned into the agent program's own configuration, on Claude Code or
on pi. It turns one [grant](../../glossary.json#concept.grant), received as data, into that
configuration; it does not compute grants, launch or resume workers, audit what a worker changed or
run checks, which its caller and [Workers](../workers/module.md) do. It serves only workers: a
[task session](../../glossary.json#concept.task-session)'s
[session boundary](../../glossary.json#concept.session-boundary) is Coordination's own, and the
[main agent](../../glossary.json#concept.main-agent)'s harness is its installed guidance alone. What
it enforces guards against scope drift and mistakes, not a malicious agent.

## Core concepts

A worker's agent harness has the three parts the root
[explains](../../module.md#the-people-and-agents) for every agent level: context, permission and
environment. For a worker, the context is only its [brief](../../glossary.json#concept.brief) and
the files the grant lets it read, and its tool set is its
[capability context](../../glossary.json#concept.capability-context); the permission is the grant,
`rw` writable, `ro` readable, `names` named only and everything else hidden, with no network and no
Git; the environment is its own configuration directory, a cleared environment, its own working
directory and limits. The permission and environment are what the Harness generates.

### A worker's harness

<a id="concept.worker-settings"></a><a id="concept.deny-rules"></a><a id="concept.write-hook"></a>

**A worker on Claude Code.** The **[worker settings](../../glossary.json#concept.worker-settings)** are the worker's only configuration (a fresh
`CLAUDE_CONFIG_DIR`) and hold three layers from the same grant.
**[Deny rules](../../glossary.json#concept.deny-rules)** cover the file tools. They deny Read and Edit
for every grant-omitted task-worktree path and every `names` path, Edit for every `ro` path, and
Read and Edit for each ungranted directory as a whole, the primary worktree but for the way to the
task worktree, every Git administrative path of the repository, `~/.claude` and the runtime
directory's `control/` and `config/`; the
[Claude Code mechanics](claude-code.md#deny-rules) list them exactly. They hold under
`bypassPermissions` and make Grep silently omit denied files. Since Claude Code applies `Read`
denials to Bash too, they never cover system directories or the **runtime paths**: the read-only
material outside the grant that every tool of the worker, Bash and the file tools alike, may read
and none may write, such as the toolchain, `.venv`, `node_modules` or the folder of the check logs a
caller admits for one run, which Workers passes with the run exactly as the caller lists them
([Reading beside the grant](../workers/launch.md#reading-beside-the-grant)) and the
Harness only receives.
The **[write hook](../../glossary.json#concept.write-hook)** makes `rw` the exact write allowlist,
judging a write by the file it would change, through any symbolic link, and denying any other Edit
or Write with a reason naming the path's level; for a path outside the
grant the reason says both that a file no Module declares needs a `specify` task first and that a
file another Module declares needs that Module bound. It says nothing about `rw` and never governs
reads. The Bash sandbox denies reading the worktree, `$HOME`, the primary worktree and every Git
administrative path, except `ro` and `rw` files and runtime paths outside those Git paths, allows writing only the `rw` files and the run's `work/`, `home/` and temporary
directory, allows no network, and ignores unsandboxed-command requests. `names` files are readable
by no tool, only named in the brief. The tool set of each [task type](../../glossary.json#concept.task-type) is chosen here too.
Exact shapes: [Claude Code mechanics](claude-code.md).

<a id="concept.permission-extension"></a>

**A worker on pi.** The **[permission extension](../../glossary.json#concept.permission-extension)** replaces the worker settings, generated from the
same grant by the same code:

| Surface | Claude Code | pi |
| --- | --- | --- |
| Reading files | deny rules on Read, Glob and Grep | the extension checks `read` and explains each denial |
| Writing files | deny rules plus the write hook | the extension checks `write` and `edit` with the write hook's table |
| Searching | Grep silently omits denied files | `grep`, `find` and `ls` run inside the sandbox, so denied files do not exist for them |
| Commands | Claude Code's Bash sandbox | `bash` through the same sandbox engine, sandbox-runtime |
| Network | none, strict allowlist | none, strict allowlist |
| [Worker result](../../glossary.json#concept.worker-result) | `--json-schema` | the `concorde_result` tool |
| Limits | `--max-turns`, `--max-budget-usd` | counted and enforced by the extension |
| Instructions and state | own `CLAUDE_CONFIG_DIR`, no `CLAUDE.md` | own `PI_CODING_AGENT_DIR`, no extensions, context files, skills or templates |

Exact tables: [pi mechanics](pi.md).

## Overview

### Where the Harness sits

The Harness sits in no call chain: no result or [error chain](../../glossary.json#concept.error-chain)
passes through it. It is used as a library by [Workers](../workers/module.md), which assembles the
inputs of one worker run — the frozen grant its caller handed over, the
[runtime directory](../../glossary.json#concept.runtime-directory) and the runtime paths — asks the
Harness for the configuration and launches the worker with it.

```d2 illustrative
direction: down
caller: "Caller\n(in Concorde, a Method step)"
workers: Workers
harness: Harness {
  worker: "worker settings or\npermission extension,\ntool set"
}
program: "worker\nClaude Code or pi"
caller -> workers: "grant as data,\ninstructions"
workers -> harness.worker: "the frozen grant,\nruntime directory,\nruntime paths"
harness.worker -> program: "Workers launches\nwith it and the brief"
```

### A worker's harness at work

**A worked example.** Take a project whose Module Checkout owns the Spec
`specs/shop/checkout/module.md` and binds `src/checkout/cart.py`, beside a Module Billing with the
Spec `specs/shop/billing/module.md` and the code `src/billing/invoice.py`, which Checkout does not
use. A task bound to Checkout runs the `implement` [Operation](../../glossary.json#concept.operation), whose step freezes this grant, among
others of the same kinds:

| Path | Level | Why |
| --- | --- | --- |
| `src/checkout/cart.py` | `rw` | Checkout's implementation scope |
| `specs/shop/checkout/module.md` | `ro` | Checkout's [Spec context](../../glossary.json#concept.spec-context) |
| `src/billing/invoice.py` | `ro` | the project's code, which an `implement` task reads whole |
| `specs/shop/billing/module.md` | none | outside every [boundary set](../../glossary.json#concept.boundary-set) of Checkout |

The step computes that grant through the Spec tooling and hands it to Workers as data, and Workers
hands the Harness that grant, the runtime directory and the runtime paths. For a Claude Code
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
its [worker result](../../glossary.json#concept.worker-result), and Workers audits the changes and
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
claude -> settings: generates
settings -> deny: carries
settings -> hook: carries
pi -> ext: provides
```

The [realizations](#the-realizations) below say which files carry each part.

## How it is built

### Around it

Workers uses the Harness; the Harness knows no caller and receives everything it needs as inputs.

**The grant** arrives as data in the worker harness's
[grant input](../workers/contracts.md#grant-input), which its caller fills: in Concorde, a step of
Method from the grant Spec core computes. The Harness depends on no Spec and on no Module that
computes grants. From Workers it also receives, besides the grant, the run's
runtime directory and runtime paths, the primary worktree of the task worktree's repository and
the repository's **Git administrative paths**: its common Git directory, the worktree's own Git
directory, every `.git` entry inside the worktree and the Git directories those point to, which
Workers finds once it has checked that the worktree lies directly in the primary worktree's
`.claude/worktrees/` ([placement](../workers/launch.md#placement)). The Harness hides
each of them, and the primary worktree as it hides the user's home, wherever the repository lies;
it never looks for Git paths itself beyond the `.git` entries it meets in the task worktree. The Harness relies on the grant listing every path's level (`rw`, `ro`,
`names`, ungranted omitted), and reads a path's level from the grant's most specific entry for it:
its exact entry, else the longest directory entry above it, so that a file the grant lists apart
from the directory around it, such as another Module's file below a writable directory, keeps its
own level in the deny rules, the write hook, the permission extension and Workers' audit alike; it
never computes or widens a grant, only receives it frozen from
Workers. It generates nothing from a malformed grant: one that has no `entries` list, or an entry
that is not an object with a non-empty path relative to the task worktree, never absolute, never
leaving it through `..` and in canonical form, with no empty or `.` segment, and a level that is one
of the strings `rw`, `ro` and `names`. Settings generation then raises a
`SettingsError` with the code `grant_malformed` naming the first such entry and what is wrong with
it, which Workers reports as its [refusal to launch](../workers/launch.md#errors).

**pi**, whose pinned copy under `references/pi/` is the version the pi harness was written against,
is relied on for its extension API: a tool an extension registers replaces pi's built-in of the
same name; pi validates a tool's arguments against the tool's parameter schema before running it;
`tool_call` handlers run in extension load order and may change a call's input or block it, and a
handler that throws blocks the tool; a tool whose result asks to terminate ends the run when every
other tool called in the same assistant message asks it too. The path decisions resolve a tool's
path argument exactly as pi resolves it.

### Why the Harness is separate

The Harness is separate from Workers because what it produces does not depend on who launches the
worker or why: a worker's harness on either program comes from the same grant by the same code.
Workers keeps what does: when a worker starts, how its rounds go, what is audited and recorded. So a
new backend needs a new compilation of the same grant here, not a new launch loop, and a new kind of
job needs only another grant from its caller.

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
[Spec](../../glossary.json#concept.spec); deny rules alone confine reads but can't stop a Write
creating an undeclared file, since a deny rule always beats an allow rule, so "only these files are
writable" cannot be expressed. The write hook closes exactly that gap, staying small.

### What a worker's harness enforces in v1

The table describes the Claude Code backend; the pi backend enforces the same surfaces with its
permission extension and sandbox-runtime, as the pi table under
[Core concepts](#core-concepts) compares. Workers sets the launch
flags and environment listed here; the Harness generates everything the settings hold.

| Surface | Mechanism | What it stops |
| --- | --- | --- |
| Read, Glob, Grep | `permissions.deny` for the grant's complement in the task worktree; the primary worktree and the user's home but for the way to the task worktree and the runtime paths; every Git administrative path; `~/.claude` with Claude Code's credential file | Ungranted/`names` reads; Grep silently omits them |
| Edit, Write | Same deny rules, plus a write-only PreToolUse hook denying non-`rw` paths, reason naming the level | `ro` edits or new files — deny alone can't, since deny beats allow |
| Bash | Sandbox: `denyRead` worktree/`$HOME`/primary worktree/Git paths, `allowRead` granted files + runtime paths, `allowWrite` `rw` files + the runtime directory's `work/`, `home/`, `tmp/`, `denyWrite` each `ro` or `names` path listed apart below a `rw` directory, no network, `allowUnsandboxedCommands: false` | Ungranted reads, `ro` writes, network, `dangerouslyDisableSandbox` |
| Permission mode | `bypassPermissions` via `--allow-dangerously-skip-permissions`; deny rules/hook/sandbox are the boundary | Nothing alone; `dontAsk` denies writes outside the working dir even when allowed |
| Working directory | The runtime directory's `work/`, never the task worktree | Claude Code adding the worktree to the Bash sandbox's read/write set |
| Tool set | `--tools` per task type, never WebFetch/WebSearch, no agent tool | Web access via tools, workers starting other agents |
| MCP | `--strict-mcp-config` with no servers | Any tool beyond the listed ones |
| Claude state/instructions | Own `CLAUDE_CONFIG_DIR`, cleared env, `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` | User settings, memory, skills, plugins, transcripts, project instructions |
| Git | No tool reads or writes a Git administrative path, inside or outside the user's home; diffs belong to Workers and commits to Delivery | A worker inspecting or rewriting history |
| Changes | Workers audits `git diff`/untracked files against the grant each round | Any remaining write outside `rw` counting as a result |
| Limits | Timeout, `--max-turns`, `--max-budget-usd`, kill of the process group at round end | Runaway runs and leftover processes |

### Known limits of v1

- The Claude or pi process, the write hooks and the extensions are not sandboxed. The file-tool
  boundary is only as good as the generated deny rules, hooks and extensions are complete and
  correct.
- Deny rules cover the task worktree, the primary worktree, the Git administrative paths and the
  home directory; system directories and other paths outside them stay readable to every tool,
  since Bash needs them to run anything. A primary worktree outside the home is therefore hidden
  like one inside it, and so is its Git metadata.
- A read denial's message is Claude Code's generic "denied by your permission settings", so the
  brief states the grant; write denials explain themselves via the hook.
- A path the grant lists apart at `ro` or `names` below a `rw` directory is in the Bash sandbox's
  `denyWrite`, which wins inside the wider `allowWrite` on both backends: Claude Code's
  `sandbox.filesystem.denyWrite` and sandbox-runtime's, which bind it read-only on Linux. A
  `denyWrite` entry covers everything below it, so a `rw` path the grant lists below such a `ro`
  or `names` directory is writable to the file tools but not to Bash.
- A single `rw` file granted to Bash is bind-mounted, so it can't be deleted or renamed from Bash,
  and a file created outside `rw` appears to succeed but lands on a throw-away filesystem, unseen by
  the audit — the brief warns of this.
- Writes to Git-ignored paths are not audited; Workers' audit is the last line of defense for a
  worker's write outside `rw`.
- On Claude Code a file created in the task worktree after the deny rules were generated has no
  rule of its own: the write hook still refuses to change it unless it is `rw`, and a directory rule
  hides it when its directory has no `ro` or `rw` path below it, but otherwise the file tools can
  read it. The worker itself cannot create such a file; pi's read check has no such gap, since it
  judges every path when it is read.

Future work: an outer sandbox-runtime (`srt`) sandbox around the agent process and proxied
credentials.

### The realizations

<a id="realization.harness.package"></a>

The **Harness package** is `concorde.worker_harness`'s Python package marker, the package of the
worker harness part in `src/concorde/worker_harness/`. The package also holds the code of Workers,
which binds its own files; a [Module](../../glossary.json#concept.module) need not match a package.

<a id="realization.harness.claude"></a>

The **Claude Code harness** is the worker settings generator (`settings.py`: the run's paths, the
deny rules, the Bash sandbox lists, the tool set of a task type and the complete settings file),
and the worker write hook (`write_hook.py`). Workers writes the settings and the hook, with the
grant's lists embedded, into the runtime directory's `control/`.

<a id="realization.harness.pi"></a>

The **pi harness** is the worker's permission extension (`pi_permission.ts`) with the pure path
decisions of its read and write tables (`pi_policy.ts`), which resolve paths exactly as pi does.
Workers embeds the policy into these sources and copies them into place.

### Where its promises are required

The Harness holds no requirements or scenarios of its own. What it generates is only observable
once Workers applies it to a worker, so each decidable promise is a requirement of Workers, and the
tests that verify those requirements exercise the Harness's files: one frozen grant for the whole run and every round
([req.workers.frozen-grant](../workers/launch.md#req.workers.frozen-grant),
[req.workers.unchanged-across-rounds](../workers/launch.md#req.workers.unchanged-across-rounds)),
no launch from a malformed grant
([req.workers.malformed-grant](../workers/launch.md#req.workers.malformed-grant)),
`rw` as the exact write allowlist
([req.workers.write-allowlist](../workers/launch.md#req.workers.write-allowlist)),
the deny rules
([req.workers.read-denials](../workers/launch.md#req.workers.read-denials)), the Bash
sandbox ([req.workers.bash-sandbox](../workers/launch.md#req.workers.bash-sandbox)),
no Git ([req.workers.no-git](../workers/launch.md#req.workers.no-git)) through every
Git administrative path
([req.workers.git-paths-denied](../workers/launch.md#req.workers.git-paths-denied)),
only in a worktree of `.claude/worktrees/`
([req.workers.placement](../workers/launch.md#req.workers.placement)), the same grant
on pi ([req.workers.pi-same-grant](../workers/pi.md#req.workers.pi-same-grant)), the
permission extension's file tools, sandbox, configuration and limits
([req.workers.pi-file-tools](../workers/pi.md#req.workers.pi-file-tools),
[req.workers.pi-sandbox](../workers/pi.md#req.workers.pi-sandbox),
[req.workers.pi-only-extension](../workers/pi.md#req.workers.pi-only-extension),
[req.workers.pi-limits](../workers/pi.md#req.workers.pi-limits)).

The Workers tests run fake and, on request, live workers and the pi path decisions under Node.
