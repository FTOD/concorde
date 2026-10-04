# Harness

## Purpose

The Harness is how the worker harness part applies a
[worker](../../glossary.json#concept.worker)'s
[agent harness](../../glossary.json#concept.agent-harness) on Claude Code or on pi. It turns the
worker's permissions and environment into the agent program's own configuration. The permissions
cover these actions:

- read
- write
- run

The Harness receives one [grant](../../glossary.json#concept.grant) as data and turns it into that
configuration. Its caller and [Workers](../workers/module.md) do the work that the Harness does
not do:

- compute grants
- launch or resume workers
- audit what a worker changed
- run checks

The Harness serves only workers. A [task session](../../glossary.json#concept.task-session)'s
[session boundary](../../glossary.json#concept.session-boundary) is Coordination's own. The
[main agent](../../glossary.json#concept.main-agent)'s harness is its installed guidance alone.
What the Harness enforces guards against scope drift and mistakes, not a malicious agent.

## Core concepts

A worker's agent harness has the three parts the root
[explains](../../module.md#the-people-and-agents) for every agent level:

- context
- permission
- environment

For a worker, the context is only its [brief](../../glossary.json#concept.brief) and the files the
grant lets it read. Its tool set is its [capability context](../../glossary.json#concept.capability-context).
The permission is the grant, with these levels:

- `rw` writable
- `ro` readable
- `names` named only
- everything else hidden

The permission allows no network and no Git. The environment has these parts:

- its own configuration directory
- a cleared environment
- its own working directory
- limits

The permission and environment are what the Harness generates.

### A worker's harness

<a id="concept.worker-settings"></a><a id="concept.deny-rules"></a><a id="concept.write-hook"></a>

**A worker on Claude Code.** The **[worker settings](../../glossary.json#concept.worker-settings)**
are the worker's only configuration (a fresh `CLAUDE_CONFIG_DIR`). They hold three layers from the
same grant. **[Deny rules](../../glossary.json#concept.deny-rules)** cover the file tools. They deny
these operations on these paths:

- Read and Edit for every grant-omitted task-worktree path and every `names` path
- Edit for every `ro` path
- Read and Edit for each ungranted directory as a whole
- Read and Edit for the primary worktree but for the way to the task worktree
- Read and Edit for every Git administrative path of the repository
- Read and Edit for `~/.claude`
- Read and Edit for the runtime directory's `control/` and `config/`

The [Claude Code mechanics](claude-code.md#deny-rules) list them exactly. Under `bypassPermissions`, the deny rules hold. They make Grep silently omit denied files. Since Claude
Code applies `Read` denials to Bash too, the deny rules never cover system directories or the
**runtime paths**. Runtime paths are read-only material outside the grant. Every tool of the worker,
Bash and the file tools alike, may read them. None may write them. Examples of runtime paths
are these:

- the toolchain
- `.venv`
- `node_modules`
- the folder of the check logs a caller admits for one run

Workers passes runtime paths with the run exactly as the caller lists them
([Reading beside the grant](../workers/launch.md#reading-beside-the-grant)). The Harness only
receives them.

The **[write hook](../../glossary.json#concept.write-hook)** makes `rw` the exact write allowlist.
It judges a write by the file it would change, through any symbolic link. It denies any other Edit
or Write with a reason naming the path's level. For a path outside the grant, the reason says that a
file no Module declares needs a `specify` task first. For that path, the reason also says that a
file another Module declares needs that Module bound.

The hook says nothing about `rw`. It never governs reads. Except for `ro` and `rw` files and runtime
paths outside those Git paths, the Bash sandbox denies reading these paths:

- the worktree
- `$HOME`
- the primary worktree
- every Git administrative path

The Bash sandbox allows writing only these paths:

- the `rw` files
- the run's `work/`
- the run's `home/`
- the run's temporary directory

The Bash sandbox allows no network. It ignores unsandboxed-command requests. No tool can read `names`
files. The brief only names them. The tool set of each
[task type](../../glossary.json#concept.task-type) is chosen here too.
The [Claude Code mechanics](claude-code.md) give the exact shapes.

<a id="concept.permission-extension"></a>

**A worker on pi.** The **[permission extension](../../glossary.json#concept.permission-extension)**
replaces the worker settings. The same code generates it from the same grant:

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

The [pi mechanics](pi.md) give the exact tables.

## Overview

### Where the Harness sits

The Harness sits in no call chain. No result or
[error chain](../../glossary.json#concept.error-chain) passes through it.
[Workers](../workers/module.md) uses it as a library. Workers assembles the inputs of one worker
run:

- the frozen grant its caller handed over
- the [runtime directory](../../glossary.json#concept.runtime-directory)
- the runtime paths

Workers asks the Harness for the configuration. Workers launches the worker with it.

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
`specs/shop/checkout/module.md` and binds `src/checkout/cart.py`. Beside Checkout is a Module Billing
with the Spec `specs/shop/billing/module.md` and the code `src/billing/invoice.py`. Checkout does not
use Billing. A task bound to Checkout runs the `implement`
[Operation](../../glossary.json#concept.operation). The Operation's step freezes this grant, among
others of the same kinds:

| Path | Level | Why |
| --- | --- | --- |
| `src/checkout/cart.py` | `rw` | Checkout's implementation scope |
| `specs/shop/checkout/module.md` | `ro` | Checkout's [Spec context](../../glossary.json#concept.spec-context) |
| `src/billing/invoice.py` | `ro` | the project's code, which an `implement` task reads whole |
| `specs/shop/billing/module.md` | none | outside every [boundary set](../../glossary.json#concept.boundary-set) of Checkout |

The step computes that grant through the Spec tooling. The step hands the grant to Workers as
data. Workers hands the Harness these inputs:

- that grant
- the runtime directory
- the runtime paths

For a Claude Code worker, the Harness returns the worker settings with these parts:

- The deny rules apply `Edit` on the Checkout Spec and on `invoice.py`.
- Since no granted path lies below `specs/shop/billing/**`, the deny rules apply `Read` and `Edit` on
  that path.
- The rules hide the rest of the home directory and the run's own configuration.
- The write hook has `cart.py` as its only writable path.
- The Bash sandbox reads the three granted files and writes only `cart.py` and the run's directories.
- The tool set is the `implement` tool set.

For a pi worker, the Harness returns the permission extension, generated from the same grant.
Workers launches the worker with that configuration and the brief. The brief lists the three
granted paths. The worker edits `cart.py`. No rule denies the edit. The write hook allows it.
The worker then tries to write a new file `src/checkout/discount.py`. Since the file does not exist
yet, no deny rule names it. The write hook refuses the write. The worker sees the hook's reason
with the prefix the hook adds to every denial:

`Concorde grant: src/checkout/discount.py is not in this task's grant; a new file outside the bound directories is created and bound to a Module by the task level before a worker fills it, and a file another Module binds needs that Module bound to the task`

A worker that needs that file says so in its [worker result](../../glossary.json#concept.worker-result).
Workers audits the changes. Workers records the run:

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

Since an `implement` task reads the project's code whole, a `names` path never appears in an
`implement` grant. A `names` path appears, for instance, in an `understand` grant. That grant's worker
may see an implementation file's name in its brief. No tool lets the worker read the file.

### Its parts

Each backend's realization produces the parts of a harness it is responsible for. The deny rules
and write hook must both be checked from the same generator to stay consistent. For that reason,
the Claude Code harness alone carries them together. It carries them inside one settings file.
Instead, pi checks the same decisions through a single extension:

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

Workers uses the Harness. The Harness knows no caller. It receives everything it needs as inputs.

**The grant** arrives as data in the worker harness's
[grant input](../workers/contracts.md#grant-input), which its caller fills. In Concorde, the caller
is a step of Method. Spec core computes the grant. The Harness depends on no Spec and on no Module
that computes grants. Besides the grant, the Harness receives these inputs from Workers:

- the run's runtime directory
- the runtime paths
- the primary worktree of the task worktree's repository
- the repository's **Git administrative paths**

The Git administrative paths comprise these paths:

- the repository's common Git directory
- the worktree's own Git directory
- every `.git` entry inside the worktree
- the Git directories those entries point to

Once Workers checks that the worktree lies directly in the primary worktree's `.claude/worktrees/`,
Workers finds those Git administrative paths ([placement](../workers/launch.md#placement)).
Wherever the repository lies, the Harness hides each of those paths. It hides the primary worktree
as it hides the user's home. Beyond the `.git` entries it meets in the task worktree, the Harness
never looks for Git paths itself.

The Harness relies on the grant listing every path's level:

- `rw`
- `ro`
- `names`
- ungranted omitted

The Harness reads a path's level from the grant's most specific entry for it. It uses the exact
entry, else the longest directory entry above it. A file the grant lists apart from the directory
around it therefore keeps its own level. Such a file can be another Module's file below a writable
directory. The file keeps its own level in these mechanisms alike:

- the deny rules
- the write hook
- the permission extension
- Workers' audit

The Harness never computes or widens a grant. It only receives the grant frozen from Workers.
From a malformed grant, the Harness generates nothing. A malformed grant has no `entries` list,
or has an entry that fails any of these conditions:

- The entry is an object.
- The entry has a non-empty path relative to the task worktree.
- The path is never absolute.
- The path never leaves the task worktree through `..`.
- The path is in canonical form, with no empty or `.` segment.
- The level is one of these strings:
  - `rw`
  - `ro`
  - `names`

Settings generation then raises a `SettingsError` with the code `grant_malformed`. The error names
the first such entry and what is wrong with it. Workers reports the error as its
[refusal to launch](../workers/launch.md#errors).

**pi** supplies the extension API the Harness relies on. Its pinned copy under `references/pi/`
is the version used to write the pi harness. The Harness relies on these API behaviors:

- A tool an extension registers replaces pi's built-in of the same name.
- Before running a tool, pi validates its arguments against the tool's parameter schema.
- `tool_call` handlers run in extension load order.
- A `tool_call` handler may change a call's input or block it.
- A handler that throws blocks the tool.
- When every other tool called in the same assistant message asks to terminate too, a tool whose
  result asks to terminate ends the run.

The path decisions resolve a tool's path argument exactly as pi resolves it.

### Why the Harness is separate

The Harness is separate from Workers because what it produces does not depend on who launches the
worker or why. A worker's harness on either program comes from the same grant by the same code.
Workers keeps the work that depends on who launches the worker or why:

- when a worker starts
- how its rounds go
- what is audited and recorded

So a new backend needs a new compilation of the same grant here. It does not need a new launch
loop. A new kind of job needs only another grant from its caller.

### One grant, compiled for each program

A worker's harness is compiled for each agent program. Neither program's harness is translated
into the other. Claude Code's permission-rule language is closed. It changes between versions. pi
has no permission system of its own. So the grant is the one source. Each program gets the mechanism
that fits it.

Since an extension sees every tool call before it runs and can explain a denial, it checks the file
tools on pi. Because only an OS boundary confines what a command or a search actually opens,
searching and commands go through the sandbox. The worker's tools are replaced rather than merely
intercepted, so the check sees the final arguments. Otherwise, a later `tool_call` handler could
still change those arguments.

### Three layers on Claude Code

Since each layer alone failed in a spike against Claude Code 2.1.280, a worker gets three layers on
Claude Code. The Bash sandbox governs only Bash and its children. Alone, it allowed these actions:

- Read returning ungranted files
- Read returning Claude Code's credential file
- Edit changing a read-only [Spec](../../glossary.json#concept.spec)

Deny rules alone confine reads. Since a deny rule always beats an allow rule, deny rules cannot
express "only these files are writable". Therefore, deny rules alone can't stop a Write creating
an undeclared file. The write hook closes exactly that gap. It stays small.

### What a worker's harness enforces in v1

The table describes the Claude Code backend. The pi backend enforces the same surfaces with its
permission extension and sandbox-runtime. The pi table under [Core concepts](#core-concepts)
compares the backends. Workers sets the launch flags and environment listed here. The Harness
generates everything the settings hold.

| Surface | Mechanism | What it stops |
| --- | --- | --- |
| Read, Glob, Grep | `permissions.deny` for the grant's complement in the task worktree; the primary worktree and the user's home but for the way to the task worktree and the runtime paths; every Git administrative path; `~/.claude` with Claude Code's credential file | Ungranted/`names` reads; Grep silently omits them |
| Edit, Write | Same deny rules, plus a write-only PreToolUse hook denying non-`rw` paths, reason naming the level | `ro` edits or new files — deny alone can't, since deny beats allow |
| Bash | Sandbox: `denyRead` worktree/`$HOME`/primary worktree/Git paths and each `names` path listed apart below a `ro` or `rw` directory, `allowRead` granted files + runtime paths, `allowWrite` `rw` files + the runtime directory's `work/`, `home/`, `tmp/`, `denyWrite` each `ro` or `names` path listed apart below a `rw` directory, no network, `allowUnsandboxedCommands: false` | Ungranted and `names` reads, `ro` writes, network, `dangerouslyDisableSandbox` |
| Permission mode | `bypassPermissions` via `--allow-dangerously-skip-permissions`; deny rules/hook/sandbox are the boundary | Nothing alone; `dontAsk` denies writes outside the working dir even when allowed |
| Working directory | The runtime directory's `work/`, never the task worktree | Claude Code adding the worktree to the Bash sandbox's read/write set |
| Tool set | `--tools` per task type, never WebFetch/WebSearch, no agent tool | Web access via tools, workers starting other agents |
| MCP | `--strict-mcp-config` with no servers | Any tool beyond the listed ones |
| Claude state/instructions | Own `CLAUDE_CONFIG_DIR`, cleared env, `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` | User settings, memory, skills, plugins, transcripts, project instructions |
| Git | No tool reads or writes a Git administrative path, inside or outside the user's home; diffs belong to Workers and commits to Delivery | A worker inspecting or rewriting history |
| Changes | Workers audits `git diff`/untracked files against the grant each round | Any remaining write outside `rw` counting as a result |
| Limits | Timeout, `--max-turns`, `--max-budget-usd`, kill of the process group at round end | Runaway runs and leftover processes |

### Known limits of v1

The v1 harness has these known limits:

- The Claude or pi process is not sandboxed. Neither are the write hooks and the extensions. The
  file-tool boundary is only as good as the completeness and correctness of these generated parts:
  - deny rules
  - hooks
  - extensions
- Deny rules cover these paths:
  - the task worktree
  - the primary worktree
  - the Git administrative paths
  - the home directory

  Since Bash needs them to run anything, system directories and other paths outside those covered
  paths stay readable to every tool. A primary worktree outside the home is therefore hidden like
  one inside it. So is its Git metadata.
- A read denial's message is Claude Code's generic "denied by your permission settings". The
  brief therefore states the grant. Write denials explain themselves via the hook.
- A path the grant lists apart at `ro` or `names` below a `rw` directory is in the Bash sandbox's
  `denyWrite`. On both backends, `denyWrite` wins inside the wider `allowWrite`. This applies to
  Claude Code's `sandbox.filesystem.denyWrite` and sandbox-runtime's. On Linux, both bind the path
  read-only. A `denyWrite` entry covers everything below it. Therefore, a `rw` path the grant lists
  below such a `ro` or `names` directory is writable to the file tools but not to Bash.
- A path the grant lists apart at `names` below a `ro` or `rw` directory is in the Bash sandbox's
  `denyRead`. On both backends, `denyRead` wins inside the wider `allowRead`. So Bash cannot read
  that path either. On pi, this is what hides that path from Bash. The pi permission extension
  receives only the sandbox lists. A `ro` or `rw` path the grant lists below such a `names` directory
  is in `allowRead`. The narrower entry wins again, so the `ro` or `rw` path stays readable.
- Since a single `rw` file granted to Bash is bind-mounted, it can't be deleted or renamed from
  Bash. A file created outside `rw` appears to succeed. But the file lands on a throw-away filesystem,
  unseen by the audit. The brief warns of this.
- Writes to Git-ignored paths are not audited. Workers' audit is the last line of defense for a
  worker's write outside `rw`.
- On Claude Code, a file created in the task worktree after the deny rules were generated has no
  rule of its own. Unless the file is `rw`, the write hook still refuses to change it. When the
  file's directory has no `ro` or `rw` path below it, a directory rule hides the file. Otherwise,
  the file tools can read it. The worker itself cannot create such a file. Since pi's read check
  judges every path when a tool reads it, pi has no such gap.

Future work: an outer sandbox-runtime (`srt`) sandbox around the agent process and proxied
credentials.

### The realizations

<a id="realization.harness.package"></a>

The **Harness package** is `concorde.worker_harness`'s Python package marker. This is the package
of the worker harness part in `src/concorde/worker_harness/`. The package also holds the code of
Workers, which binds its own files. A [Module](../../glossary.json#concept.module) need not match
a package.

<a id="realization.harness.claude"></a>

The **Claude Code harness** is the worker settings generator (`settings.py`) and the worker write
hook (`write_hook.py`). The generator produces these parts:

- the run's paths
- the deny rules
- the Bash sandbox lists
- the tool set of a task type
- the complete settings file

Workers writes the settings and the hook, with the grant's lists embedded, into the runtime
directory's `control/`.

<a id="realization.harness.pi"></a>

The **pi harness** is the worker's permission extension (`pi_permission.ts`) with the pure path
decisions of its read and write tables (`pi_policy.ts`). Those decisions resolve paths exactly as
pi does. Workers embeds the policy into these sources. Workers copies the sources into place.

### Where its promises are required

The Harness holds no requirements or scenarios of its own. Only once Workers applies the generated
configuration to a worker does what the Harness generates become observable. So each decidable
promise is a requirement of Workers. The tests that verify those requirements exercise the
Harness's files for these promises:

- one frozen grant for the whole run and every round
  ([req.workers.frozen-grant](../workers/launch.md#req.workers.frozen-grant),
  [req.workers.unchanged-across-rounds](../workers/launch.md#req.workers.unchanged-across-rounds))
- no launch from a malformed grant
  ([req.workers.malformed-grant](../workers/launch.md#req.workers.malformed-grant))
- `rw` as the exact write allowlist
  ([req.workers.write-allowlist](../workers/launch.md#req.workers.write-allowlist))
- the deny rules ([req.workers.read-denials](../workers/launch.md#req.workers.read-denials))
- the Bash sandbox ([req.workers.bash-sandbox](../workers/launch.md#req.workers.bash-sandbox))
- no Git ([req.workers.no-git](../workers/launch.md#req.workers.no-git)) through every Git
  administrative path
  ([req.workers.git-paths-denied](../workers/launch.md#req.workers.git-paths-denied))
- only in a worktree of `.claude/worktrees/`
  ([req.workers.placement](../workers/launch.md#req.workers.placement))
- the same grant on pi ([req.workers.pi-same-grant](../workers/pi.md#req.workers.pi-same-grant))
- the permission extension's file tools
  ([req.workers.pi-file-tools](../workers/pi.md#req.workers.pi-file-tools))
- the permission extension's sandbox
  ([req.workers.pi-sandbox](../workers/pi.md#req.workers.pi-sandbox))
- the permission extension's configuration
  ([req.workers.pi-only-extension](../workers/pi.md#req.workers.pi-only-extension))
- the permission extension's limits
  ([req.workers.pi-limits](../workers/pi.md#req.workers.pi-limits))

The Workers tests run fake workers and the pi path decisions under Node. On request, the tests also
run live workers.
