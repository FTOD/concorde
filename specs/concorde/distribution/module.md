# Distribution

## Purpose

Distribution is the distribution [part](../glossary.json#concept.part), the one present in every
installation. It turns the Concorde checkout into packages a developer can install. It installs
into a project the parts the developer chooses, with the parts they depend on. It records which
parts are installed. It updates them. From the installed parts, it composes these two things that
a project's sessions use:

- The one `concorde` command.
- The one [project MCP server](../glossary.json#concept.project-mcp-server).

It also builds the generated files. Where the spec part is installed, it writes the
[Protocol copy](../glossary.json#concept.protocol-copy) a project carries. It installs the
[main-session guidance](../glossary.json#concept.main-session-guidance) for Claude Code. The
[main agent](../glossary.json#concept.main-agent) and its
[task sessions](../glossary.json#concept.task-session) run on Claude Code for now. The main-session
guidance is composed from the guidance each installed part contributes.

Distribution reaches the parts only through their
[part registrations](../glossary.json#concept.part-registration). These are plain data each part
gives it. No part imports Distribution's code. Distribution does not decide any of these things:

- What a command or an MCP tool does.
- What the main agent is told.
- A project's Specs and configuration.

The installer writes no Spec but the realization that keeps its own installed files bound.

## Core concepts

### The build manifest

<a id="concept.build-manifest"></a>

The **[build manifest](../glossary.json#concept.build-manifest)**, `generated/build-manifest.json`,
is the build's record of the digest of every source it read and of every output it wrote.
Its [contract](contracts.md#contract.distribution.build-manifest) fixes its shape. It lets the
build tell what is stale. `build --check` reports what is stale. The installer refuses what is
stale. Only while a leftover output's bytes still match the previous manifest, the manifest lets
the build remove that output.

### The Protocol copy

<a id="concept.protocol-copy"></a>

The **[Protocol copy](../glossary.json#concept.protocol-copy)** is the rendered Spec Protocol
bundle the installer writes under `.concorde/protocol/`. It is built from the tracked manifest and
rendered assets so that a project receives exactly the Protocol the manifest names. The project's
configuration accepts it through its [Protocol binding](../glossary.json#concept.protocol-binding).
After a plain install, the developer updates the binding. `concorde update` rebinds it itself.

### Parts and their registrations

<a id="concept.part-registration"></a>

Every part of Concorde is a package of its own in the one repository. Each part carries the
repository's one version number. Each gives Distribution a
**[part registration](../glossary.json#concept.part-registration)**. This is plain data in the shape
the [registration contract](contracts.md#contract.distribution.part-registration) fixes. It names:

- The part.
- The parts it depends on.
- Its `concorde` commands.
- Its MCP tools.
- The [typed value](../glossary.json#concept.typed-value) types it registers.
- Its guidance.
- Its install contributions.
- Its idle check, which says whether work of the part currently runs in the project.

Its install contributions are:

- The files it ships beside its code.
- The `.gitignore` lines.
- The permission rules.
- The programs it needs, such as the worker harness's pi runtime.
- The Python dependencies its code imports, such as Method's LangGraph.

The registration is data, not an interface a part implements against Distribution's code.
So a part that depends on nothing, such as the spec part, registers without importing anything.
Distribution loads only the registrations of the installed parts. What a part does not register
does not exist in the project. These items of a part that is not installed are simply absent:

- A command.
- A tool.
- A guidance section.
- A file.

Each part keeps its registration as `registration.json` in its own directory of `src/concorde/`.
Every entry it names is an attribute of a module of that part's own package.
Examples of these entries are:

- A command.
- A tool.
- An install service.
- An idle check.

Distribution is the only code that imports a part by such a name. Because each entry belongs to
the part's own package, Distribution never reaches one part's code through another's registration.
A registration also names the part's modules that register what its code provides when they load.
Examples of what they register are:

- Typed value types.
- Trace roots.
- Operation definitions.
- Workflows.

For every installed part, Distribution loads those modules before it does any of these things:

- Routes a part's command.
- Answers a tool.
- Renders the build.

In a source checkout, the installed parts are every part the package builds. In a project, the
installed parts are the parts its receipt names. The build records what every part of the package
registers in the **parts index** `generated/parts.json` ([contract](contracts.md#part-registration)).
From this index, a project's `concorde` and project MCP server name the part of a command or tool
the project lacks. They do so without reading that part's registration.

| Part | Its [Module](../glossary.json#concept.module) | It registers, among others |
| --- | --- | --- |
| spec | [Spec tooling](../spec-tooling/module.md) | `spec-validation`, `registry`, `grant`, `init`, `docsite`, `spec-mcp`; its install services, which place the docsite template and bind the installed files; where it is installed Distribution places the Protocol copy |
| kernel | [Kernel](../kernel/module.md) | `trace`; the `.concorde/locks/` ignore rule |
| worker harness | [Worker harness](../worker-harness/module.md) | the pi runtime, the model discovery entry point |
| execution | [Execution](../execution/module.md) | `run`; the idle check over the [run locks](../glossary.json#concept.run-lock) |
| workflow | [Workflows](../workflows/module.md) | `workflow`; the `workflow_step` and `workflow_report` tools; the rendered workflows and their permission rules |
| issues | [Issues](../issues/module.md) | `issues`; the `issue_*` tools |
| coordination | [Coordination](../coordination/module.md) | `task`; the `task_*`, `task_merge`, `locks`, `register_wait` and `trace_show` tools, and `run_result` where the execution part is installed; the main-session guidance; the open tasks an update reports |
| method | [Method](../method/module.md) | its Operations and the execution commands `task-validation`, `delivery` and `scaffold`; the [brownfield workflow](../glossary.json#concept.brownfield-workflow)'s script; its guidance |
| distribution | this Module | `build`, `protocol-manifest`, `update`, `project-mcp` |

### Commands named by their owner

A command is named after the part that registers it, as the table above lists:

- `task` gives the coordination commands.
- The Spec tooling commands are:
  - `spec-validation`.
  - `registry`.
  - `docsite`.
  - `grant`.
  - `spec-mcp`.
  - `init`.
- `issues` gives the Issues commands.
- `trace` gives the Tracing commands.
- `run` gives an Operation.
- `workflow` gives a workflow step.
- The **distribution commands** are:
  - `build`.
  - `protocol-manifest`.
  - `update`.
  - `project-mcp`.

The distribution commands are the only ones Distribution owns itself. The
[execution commands](../glossary.json#concept.execution-command) are runs without a worker. The
part that provides them names them. That part registers them. Method's examples are:

- `task-validation`.
- `delivery`.
- `scaffold`.

Their entries run them through the Execution runner
([Commands](../execution/commands/module.md)).

### The project MCP server

<a id="concept.project-mcp-server"></a>

The **[project MCP server](../glossary.json#concept.project-mcp-server)** is the project's one stdio
MCP server. It is `concorde project-mcp`, registered as `concorde` in the project's `.mcp.json`.
Each Claude Code session runs its own process of the server. The server is a host. It presents the
MCP tools the installed parts register. It answers none of them itself. So the project's tools
depend on its installed parts:

- With the coordination part, a project has the task tools.
- With the [issues](../glossary.json#concept.issue) part, a project has the Issue tools.
- With the workflow part, a project has the `workflow_step` tool its workflows' step agents call.
- When a part is not installed, its tool is absent.

Each tool's part owns these aspects of the tool:

- Its behaviour.
- Its arguments.
- Its refusals.

Each call's process loads the installed parts' registering code. It passes the call, with the
session's provenance, to the entry the tool's registration names. That entry's answer or refusal
is the tool's. When the project has not installed a tool's part, the tool is refused with
`part_missing` naming the part, as a command is. When a tool's registration requires a part that
is not installed, the tool is not presented. Coordination's `run_result` without the execution
part is an example. [Serving a call](#serving-a-call) describes how the server does these things:

- Serves a call.
- Keeps it on the current code.
- Hands locks to long work.
- Wakes its session.

Its [contract](contracts.md#project-mcp-server) describes its exact session and call protocol.

## Overview

### From checkout to project

Distribution works in two stages. The build renders these items into `generated/`:

- Every part's prompts.
- The Protocol.
- The workflow scripts.

The build records the build manifest. The installer runs for a first install or by
`concorde update`. It refuses a stale build. It resolves the parts to install with the parts they
depend on. It places these items in the project:

- Each one's files.
- The environment.
- The command.
- The guidance of the installed parts.
- The workflows of the installed parts.

```d2 illustrative
direction: right
checkout: Concorde checkout {
  descriptor: "concorde.json"
  sources: "prompts/, protocol/,\nworkflow scripts"
  runtime: "Framework runtime,\ndocsite template, uv.lock"
}
build: Build renderer
generated: "generated/" {
  renders: "rendered prompts\nand skills"
  workflows: "Claude Code\nworkflows"
  manifest: "build manifest"
}
installer: "Installer\ninstall-concorde.py or\nconcorde update"
project: The project {
  concorde: ".concorde/" {
    grid-columns: 2
    protocol: "protocol/\nProtocol copy"
    framework: "framework/\nruntime, Python environment"
    tools: "tools/\nd2, pi runtime"
    bin: "bin/concorde"
    receipt: "install.json"
  }
  claude: "CLAUDE.md block, .claude/skills/,\n.claude/workflows/, settings rules,\n.mcp.json, .gitignore"
}
checkout.descriptor -> build: reads
checkout.sources -> build: reads
build -> generated: writes
generated -> installer: "checked fresh"
checkout -> installer: "copies from"
installer -> project: places
```

### An install, step by step

The installer makes its checks and the pinned download before its first write. So a refusal at
one of them leaves the project as it was. Not every refusal does. The steps drawn dashed run
programs. Like any write, these steps can fail after something was written.
[When an install fails halfway](#when-an-install-fails-halfway) explains this.

```d2 illustrative
direction: down
decide: "Decide, writing nothing" {
  grid-columns: 2
  direction: down
  checks: "1. Check the project, build, docsite\ntemplate, develop source, idle Concorde,\ndescriptor, settings, .mcp.json, uv, npm"
  fetch: "2. Fetch the pinned d2\nand check its SHA-256"
  checks -> fetch
}
refused: "Refused with an error link:\nthe project is unchanged" {shape: oval}
write: "Write" {
  direction: down
  tools: "2. Place d2 and the\npi runtime (npm ci)" {style.stroke-dash: 3}
  files: "3. Place the Protocol copy, defaults,\nFramework runtime and docsite template"
  env: "4. Create Concorde's Python\nenvironment (uv venv, dependencies)" {style.stroke-dash: 3}
  cmd: "5. Write .concorde/bin/concorde"
  guidance: "6. Install the guidance"
  workflows: "7. Install the workflows, their\npermission rules and the project MCP server"
  record: "8. Add ignore rules,\nwrite the receipt"
  bound: "9. Keep the installed\nfiles bound"
  tools -> files -> env -> cmd -> guidance -> workflows -> record -> bound
}
decide -> refused: "a check or\nthe download fails"
decide.fetch -> write.tools
```

### Its parts

How this Module's realizations call one another:

```d2
distribution: Distribution {
  descriptor: Package descriptor {
    "concorde.json"
  }
  build: Build renderer
  command: Command entry points
  server: Project MCP server host
  writer: Protocol copy writer
  installer: Installer program
  build -> descriptor: reads
  command -> build: runs
  command -> server: runs
  installer -> writer: places through
}
```

Python sources are under `src/concorde/distribution/` except `src/concorde/__main__.py` and the
`scripts/` entry points. Each realization's exact files are its metadata's `entries`.
The [build manifest](../glossary.json#concept.build-manifest) and
[Protocol copy](../glossary.json#concept.protocol-copy) are recorded. They are also written.
Neither binds a file of its own.

## Using Distribution

### The package

`concorde.json` is the package's identity. It names:

- The name.
- The version.
- The licence.
- The roots the installer ships.
- The install locations.
- The client `claude-code` the build renders workflows for.
- The pinned third-party programs under `tools` (today `d2`).
- The entry of [Dogfooding's](#uses-dogfooding) develop source check under `develop.check`.

The programs are pinned by:

- Release.
- URL.
- Per-platform SHA-256.

The build reads it too, so a changed descriptor makes every render stale.

### Building

`python3 scripts/concorde.py build` expands every prompt root into `generated/`
([requirements](requirements.md#req.distribution.build-reachable)). `{{name}}` becomes the literal
text `{name}` so that a prompt can show a placeholder such as a check's `{python}`.
Once every part's registering code is loaded, the build wraps every
[workflow script](../glossary.json#concept.workflow-script) the parts contribute to the workflow
catalog. It does this through the workflow part's `renders` entry. Each wrapped script becomes
`generated/workflows/claude/concorde-<name>.js`. Each wrapped script includes its `meta` block and
Claude Code step adapter.
The build writes the [parts index](contracts.md#part-registration) `generated/parts.json` from the
parts' registrations. It writes `generated/build-manifest.json` with every source's and output's
digest. It refuses a registration that breaks the [registration
contract](contracts.md#contract.distribution.part-registration). It also refuses a command or MCP
tool name two parts register ([requirements](requirements.md#req.distribution.unique-names)).
The prompt roots are:

- The Protocol's `prompts/protocol/principles.md`.
- The Protocol's `prompts/protocol/kinds/module.md`.
- Every file directly in `prompts/workers/`.
- Every file directly in `prompts/main-session/`.
- Every file directly in `prompts/dogfooding/`.
- Every file directly in `prompts/development/`.
- The prompt of every guidance section a part registers, `prompts/<path>` for its `generated/<path>`.

Each root renders to the same path under `generated/`. The build then
[composes the guidance](#guidance-composition) of every part of the package into:

- The `concorde` skill `generated/skills/concorde/SKILL.md`.
- The task-session prompt `generated/guidance/task-session.md`.

It renders the development skill from its prompt root
([skills](#realization.distribution.build)). `build --check` only reports what is stale.
It writes nothing ([requirements](requirements.md#req.distribution.build-check-read-only)).
`generated/` is Git-ignored, so a checkout always rebuilds.
`protocol-manifest --write --bind-project` does the following, as described next:

- Accepts a Protocol change's fresh digests.
- Binds the configuration.
- Refreshes this checkout's own copy.

### Reconciling the Protocol manifest

`protocol-manifest` compares the tracked manifest's digests for the rendered Protocol assets with
those of the current build. The tracked manifest is `protocol/manifest.json`.
[Spec core](../spec-tooling/spec/contracts.md#protocol-manifest) defines its shape.
`protocol-manifest` first requires:

- A fresh build.
- A readable tracked manifest of the manifest's shape.
- Every asset of that manifest to be held by the build.

When any precondition fails, it reports `invalid` with `CONCORDE-PROTOCOL-MANIFEST-001` naming the
problem. In that case, it writes nothing, whatever its flags
([requirements](requirements.md#req.distribution.protocol-manifest-precondition)).
Then each combination of its two flags does what the following table shows.
The result's `differences` names the assets whose digests differed from the build's.
Its `artifacts` names what it wrote:

| Flags | Writes | Status |
| --- | --- | --- |
| none | nothing | `success` when no digest differs, otherwise `invalid` with `CONCORDE-PROTOCOL-MANIFEST-001` naming the assets that differ |
| `--write` | the tracked manifest with the build's digests, only when one differs | `success` |
| `--bind-project` | the configuration's [Protocol binding](../glossary.json#concept.protocol-binding), set to the tracked manifest's version and the digest of its bytes, then this checkout's Protocol copy under `.concorde/protocol/` | `success` when no digest differs; otherwise the binding is written and the copy, which would no longer match the build, is refused with `protocol_mismatch` in a `failed` result, the copy left as it was |
| `--write --bind-project` | the tracked manifest when a digest differs, then the binding to it and the Protocol copy | `success` |

A Protocol change in this checkout is therefore accepted with both flags. For a checkout whose own
configuration is bound otherwise, `--write` alone suits, such as a package a project installs from.

### The command line

The following entry points take a global `--project-root` and one subcommand:

- `scripts/concorde.py`.
- The `concorde.sh` wrapper.
- The `concorde.ps1` wrapper.

In a source checkout that `uv sync` prepared, the entry point runs
itself again on the checkout's own `.venv` interpreter. That interpreter holds Concorde's Python
dependencies. An installed copy has no `.venv`. It runs on Concorde's own environment.

For each row's command to exist in a project, the part that registers it must be installed.
When a command's part is not installed, the command is refused
([requirements](requirements.md#req.distribution.absent-part-named)). This refusal:

- Names that part and how to install it.
- Prints `{"error": <link>}` whose code is `part_missing`.
- Exits with status 1.

This is the one refusal by which another part tells that a part is absent.
When a command line names no command of the package, it receives one `failed` envelope.
`concorde --help` lists the commands of the installed parts.

| Command | Does | Part, Module |
| --- | --- | --- |
| `spec-validation [target]` | runs the structural checks; Distribution adds the findings of [an update not yet validated](#updating-an-installed-concorde) and removes its mark | spec, [Spec core](../spec-tooling/spec/module.md), with Distribution's update findings |
| `registry --write` or `--check` | regenerates or checks the registry mirror | spec, [Spec core](../spec-tooling/spec/module.md) |
| `docsite --propose` or `--apply` | proposes or applies the docsite scaffold | spec, [Views](../spec-tooling/views/module.md) |
| `grant --modules <ids> --type <task type> [--root <worktree>]` | prints a [task type](../glossary.json#concept.task-type)'s grant | spec, [Spec core](../spec-tooling/spec/module.md) |
| `spec-mcp` | runs the stdio MCP server rooted at `CLAUDE_PROJECT_DIR` or the client's root; it prints no envelope | spec, [Spec MCP server](../spec-tooling/spec-mcp/module.md) |
| `project-mcp [--name <name>]` | runs the stdio [project MCP server](../glossary.json#concept.project-mcp-server) of the primary worktree, `<name>` being the name it is registered under, `concorde` by default, which a channel flag names as `server:<name>`; it prints no envelope | distribution, this Module, serving the tools the installed parts register |
| `init --propose --name <name>` or `--apply --proposal <file>` | proposes or applies a project's first [Spec](../glossary.json#concept.spec); after an apply Distribution adds the glossary import to the `CLAUDE.md` block | spec, [Spec core](../spec-tooling/spec/module.md) through the [`init` command](../spec-tooling/module.md#init-command), with Distribution's glossary import |
| `task open`, `list`, `show`, `close`, `merge`, `escalate` or `wait` | opens, lists, shows, closes, merges or escalates tasks, or waits for a task, run or lock; prints the task command's own JSON | coordination, [Tasks](../coordination/tasks/module.md) |
| `run <operation>` | runs one [Operation](../glossary.json#concept.operation) in the workspace of the current worktree or, when the Operation allows it, unbound; prints the [run result](../glossary.json#concept.run-result) | execution, [Execution](../execution/module.md), running the definitions the installed parts register with [Operations](../execution/operations/module.md) |
| `task-validation`, `delivery` or `scaffold` | runs one execution command in the workspace of the current worktree; prints the run result | method, the definitions of [Method](../method/module.md), run by [Execution](../execution/module.md) through [Commands](../execution/commands/module.md) |
| `workflow step` or `report` | runs one [workflow step](../glossary.json#concept.workflow-step), or reports a workflow's result; prints its own JSON | workflow, [Workflows](../workflows/module.md) |
| `issues list`, `show`, `check`, `report`, `close` or `reopen` | the Issues bookkeeping command `scripts/issues.py`; prints its own JSON | issues, [Issues](../issues/module.md) |
| `trace show`, `list` or `prune` | shows a [trace](../glossary.json#concept.trace) with its timing and cost rolled up, lists traces, or removes what retention allows; prints its own JSON | kernel, [Tracing](../kernel/tracing/module.md) |
| `build [--check]` | renders or checks the generated files | distribution |
| `protocol-manifest [--write] [--bind-project]` | [reconciles the Protocol manifest](#reconciling-the-protocol-manifest) | distribution |
| `update [--from <checkout>] [--parts <part>[,<part>…]]` | updates the installed Concorde, adding the parts `--parts` names, as described below; prints its [update result](contracts.md#contract.distribution.update-result) | distribution |

A command registered with `output` `envelope` prints exactly one JSON envelope, even when refused
([requirements](requirements.md#req.distribution.one-envelope)). It exits with the envelope's status.
Today this applies to every distribution and Spec tooling command except:

- `spec-mcp`.
- `project-mcp`.
- `update`.

A command registered with `own` prints what its owner defines. It uses its owner's exit codes.
Examples are:

- `task`.
- `run`.
- The execution commands.
- `workflow`.
- `issues`.
- `trace`.

`update` prints its [update result](contracts.md#contract.distribution.update-result) or its
[error link](requirements.md#req.distribution.installer-error-links).

The worker harness part's standalone Workers entry point is
`scripts/available_models.py --backend pi|claude [--json]`. As that part's install contribution, it
ships under `.concorde/framework/scripts/available_models.py` with the runtime. It resolves
its imports relative to itself. It works outside a Git worktree. It lists advisory configured
candidates without probing inference API access. Each candidate has the project model names the
user's [model map](../glossary.json#concept.model-map) gives it.
Configuration validation does not call it. The installer writes neither the worker configuration
nor the model map. The model map belongs to the user. It lies outside every project.

The command runs the Framework copy of the worktree it belongs to. Unless the task reinstalled
Concorde there, a task worktree has none of its own, since Git ignores the Framework copy. The task
worktree's command then runs the primary worktree's copy, found through Git's common directory.

### Serving a call

The [project MCP server](#the-project-mcp-server) is a host for the tools of the installed parts.
A call travels from the session through the server to a fresh process of the current Concorde.
That process calls the entry the tool's registration names and answers.
When a tool starts long work, the tool becomes that work.
The server watches what outlives the call.
When the watched process ends, the server wakes the session.
[The contract](contracts.md#project-mcp-server) fixes every message exactly.

```d2 illustrative
direction: right
session: Claude Code session
server: "Project MCP server\nconcorde project-mcp"
call: "Call process\nconcorde project-mcp --call\nof the current Concorde"
entry: "The tool's entry\nin its part's code"
work: "Long work, such as a merge:\nthe call process after exec"
wait: "Wait process,\nsuch as concorde task wait"
session -> server: "tools/call"
server -> call: "the call and provenance\non standard input"
call -> entry: "the call object"
entry -> call: "value or error, with\nwatch, handover or work"
call -> server: "one answer line,\nor reroute"
server -> session: "the tool's result"
call -> work: "handover: keeps\nthe locks it took" {style.stroke-dash: 3}
server -> wait: "watch"
wait -> server: "its answer"
work -> server: "its exit and output"
server -> session: "channel event"
```

The host's own promises are these:

- **Current code.** The server process lives as long as its Claude Code session, which may be hours.
  Meanwhile, Concorde itself changes under the server through a task merge in Concorde's own
  checkout or `concorde update` in an installed project.
  Code loaded once would then keep answering with the rules and record formats it started with.
  That code would refuse the records the new code writes.
  So the server runs none of its tools itself.
  Each call runs `concorde project-mcp --call <tool>` in a process of its own.
  Unless the tool's registration names the session's own worktree instead, the call uses the
  primary worktree's `concorde` as it is when the call arrives.
  That command is its `.concorde/bin/concorde` or, in Concorde's source checkout, its
  `scripts/concorde.py`.
  The `workflow_step` registration names the session's own worktree instead.
  The call's arguments and the session's provenance go to the call process as one JSON object.
  The call process's answer or refusal is the tool's.
  When a call's process gives no answer, or none within its time, the server refuses the call with
  its own `call_failed` link.
  The link names the command and what it printed.
  The following come from `concorde project-mcp --tools` of the current code:

  - The tools.
  - How each tool is served.
  - The server's instructions, its own followed by the sentence each installed part registers.

  The server routes a call as the last such listing says how the tool is served.
  That listing specifies:

  - In which worktree the tool's process runs.
  - Whether the tool hands on long work.
  - Whether the tool is answered on a thread of its own.

  The call's process, the current code, first checks that routing against its own registration
  of the tool.
  When the routing and registration differ, the call's process answers how it serves every tool
  instead of running anything.
  The server then routes the call again that way.
  So an update that changes only how a tool is served takes effect at the next call.
  Each answer also says which tools the current code has.
  When those tools differ from those the server last listed to the session, the server tells its
  session that its tools changed.
  Claude Code then lists the tools again.
  A listing the server fetches only to learn how a tool is served is not one the session was given.
  Until the next session, only these stay what the session started with:

  - The server's own session code.
  - Its few protocol messages.
  - Its instructions.

- **Locks handed to the work.** When a tool's registration says it starts long work, the tool never
  waits for a lock.
  Coordination's `task_merge` is such a tool.
  For such a tool, the call's process takes the locks the work needs at once or is refused at once naming the holder.
  When such a tool's call process gets the locks, it replaces itself with the command doing the work.
  That command keeps the locks, since a `flock` belongs to the open file description that survives
  the change of program ([Handing a lock on](../kernel/tracing/contracts.md#handing-a-lock-on)).
  The server never holds a lock, so a lock belongs to the work.
  Whenever the work ends, however it ends, the lock is released, even when the session and its
  server end first.
- **Watching and waking.** A tool may ask the server to watch a process.
  Examples are:

  - A wait for a task that Coordination's `register_wait` registers.
  - A wait for a run that Coordination's `register_wait` registers.
  - A wait for a lock that Coordination's `register_wait` registers.
  - The long work a tool started.

  When the watched process ends, the server wakes its session with a Claude Code channel event
  carrying that process's answer.
  A wait ends with the server.
  When the server ends, long work goes on and keeps its locks until the work ends.
  The server only ceases to watch the long work.
  Claude Code delivers a server's `notifications/claude/channel` only to an interactive session
  started with that server as a channel.
  This research preview needs:

  - `--dangerously-load-development-channels server:concorde`.
  - Anthropic authentication.
  - An organization that has not disabled channels.

  A background session is never woken by these notifications.
  A server cannot learn from Claude Code whether it is a channel.
  So, unless the environment variable `CONCORDE_CHANNEL` is `1` or `0`, the server identifies the interactive `claude` above it whose standard input is a terminal.
  It then reads its channel status from that process's command line.
  When the variable is `1` or `0`, the variable decides the server's channel status instead.
  The configuration a task session's server starts with sets the variable to `0`.
  When the server has no channel, the tool instead returns the equivalent blocking `concorde`
  command for the session's background Bash.
  When that command ends, it wakes the session.

The server answers calls that wait, each on a thread of its own, so the session's other calls are
not held up meanwhile. Using it is recommended, not enforced.
The reason is that the `concorde` command and the server take the same locks.
So both paths see each other's holders.
[Workers](../glossary.json#concept.worker) never receive the server.
They launch with an empty MCP configuration.

### Installing into a project

The developer runs, from a built Concorde checkout:

```text
python3 scripts/install-concorde.py <project> [--parts <part>[,<part>…]] [--develop]
    [--without-d2] [--without-pi-runtime] [--without-dependencies] [--update]
```

`--parts` names the parts to install, by the names of the
[parts table](#parts-and-their-registrations). The installer adds every part they depend on.
When the option is left out, the installer installs every part. Distribution itself is installed
with any part. `--develop` makes a [develop install](#uses-dogfooding).
As steps 2 and 4 below describe, these options leave out the corresponding components:

- `--without-d2` leaves out the pinned `d2`.
- `--without-pi-runtime` leaves out the [pi runtime](#the-pi-runtime).
- `--without-dependencies` leaves out Concorde's Python dependencies.

`--update` runs the installer in [update mode](#updating-an-installed-concorde), as `concorde update`
does. The installer first decides everything that could refuse the install and only then writes.
So a refusal among these checks leaves the project as it was. On a project where every check
passes, it goes through these steps in order:

1. **It checks, writing nothing.** It refuses these cases:
   - A directory is not a project (`invalid_project`).
   - A requested part name, or a name of a part it depends on, is not built by the package
     (`unknown_part`, [requirements](requirements.md#req.distribution.unknown-part-refused)).
   - A build is stale (`stale_build`). This includes a stale render of the
     [main-session guidance](../glossary.json#concept.main-session-guidance).
   - A docsite template fails [Views](../spec-tooling/views/module.md)' inventory rule
     (`invalid_docsite_template`,
     [checked first](requirements.md#req.distribution.installer-docsite-template-first)).
   - A render of the guidance is missing (`stale_build`,
     [requirements](requirements.md#req.distribution.installer-fresh-guidance)).
   - With `--develop`, a source fails Dogfooding's check.
   - In a project, an installed part reports work running (`concorde_busy`, described below).
   - In a project, an installed part's idle check fails (`part_failed`).
   - A `concorde.json` names no Python requirement (`invalid_descriptor`).
   - A `.claude/settings.json` is not a JSON object with an optional `permissions.allow` list
     (`settings_invalid`,
     [checked first](requirements.md#req.distribution.installer-settings-checked)).
   - A `.mcp.json` is not a JSON object with an optional `mcpServers` object
     (`mcp_config_invalid`,
     [checked as early](requirements.md#req.distribution.installer-mcp-checked)).
   - A machine lacks `uv` on `PATH` (`uv_missing`), since uv owns Concorde's Python.
   - When the pi runtime described below is still to be placed, a machine lacks `npm`
     (`npm_missing`) ([requirements](requirements.md#req.distribution.installer-programs-first)).
2. **It places the pinned programs** the installed parts' registrations name under
   `install.programs`. Where the spec part is installed, it performs these steps unless
   `--without-d2` skips them:
   - It fetches the `d2` release `concorde.json` pins.
   - Before anything else is written, it checks the release against its SHA-256.
   - It places the release at `.concorde/tools/d2`.

   On a later install with the same pin, it keeps the release
   ([requirements](requirements.md#req.distribution.installer-pinned-d2),
   [checked first](requirements.md#req.distribution.installer-d2-first)). Where the worker harness
   part is installed, it then places the pi runtime under `.concorde/tools/pi-runtime/`, as
   described below.
3. **It places Concorde's files.** It places the Framework runtime of the chosen parts under
   `.concorde/framework/`, replacing an earlier copy. It places these files and directories,
   and nothing else:
   - `concorde.json`.
   - Each chosen part's code directory `src/concorde/<directory>/`.
   - The files and directories its registration lists under `install.files`.

   Examples of the registered files and directories are:
   - Distribution's `scripts/concorde.py` and parts index.
   - The spec part's `protocol/` and rendered Protocol.
   - Method's rendered worker prompts.
   - The Issues command `scripts/issues.py`.
   - The worker harness's `scripts/available_models.py`.

   So the code of a part that is not installed is not in the project at all.
   For the same reason, Concorde's own development tooling, such as `scripts/e2e/`, never reaches
   the project. It writes the files each chosen part contributes. It writes Concorde-owned
   defaults only where absent. Except for Concorde-owned defaults, it removes every file an
   earlier install owned that this one no longer places. An example is the workflow of a part
   left out. A Concorde-owned default holds the project's own data. A default the replaced receipt
   names among its `defaults` stays. While the default is in place, it stays Concorde's, even when
   the installed parts or a newer Concorde no longer declare it.
   With the spec part, it places the Protocol copy under `.concorde/protocol/`.
   Where the spec part is installed, it also places the docsite template under `.concorde/framework/docsite/`.
   The template contains exactly the files Views' template inventory selects, `scaffold/`
   included. From that template, `concorde docsite --propose` scaffolds a project's site
   ([requirements](requirements.md#req.distribution.installer-docsite-template)).
4. **It creates Concorde's own Python environment.** `uv venv` creates a venv at
   `.concorde/framework/python/` for the Python requirement `concorde.json` names under
   `runtime.python`. Whatever interpreter runs the installer, uv chooses the venv's interpreter
   ([requirements](requirements.md#req.distribution.uv-owns-python)). It chooses one of the
   machine's interpreters or a uv-managed CPython. When none fits, uv downloads a uv-managed
   CPython. When uv cannot create the venv, the install is refused with `python_env_failed` and
   uv's output. Only where an installed part's registration names a dependency under
   `install.python_dependencies`, Concorde's Python dependencies go into that environment.
   An example is LangGraph, which Method's `spec_panel` runs on. The dependencies are exactly the
   runtime part of the checkout's `uv.lock`. Each package is checked against its locked hash
   ([requirements](requirements.md#req.distribution.locked-python-dependencies)). Then each
   dependency the installed parts name is checked by importing it. A failing step is refused with
   `python_dependencies_failed` and the failing command's output. `--without-dependencies` skips
   these steps. The Operations that need the dependencies then refuse.
5. **It writes the command.** `.concorde/bin/concorde` is composed from the registrations of the
   installed parts. It runs Concorde only in that environment. It leaves out these parts of the
   caller's environment:
   - `PYTHONPATH`.
   - `PYTHONHOME`.
   - User site-packages.

   So an activated project venv never becomes Concorde's interpreter
   ([requirements](requirements.md#req.distribution.own-python)).
6. **It installs the guidance.** The main-session guidance is [composed](#guidance-composition)
   of Coordination's working method followed by the guidance every other installed part
   contributes. Those contributions follow the order of the parts table. The build's renders of
   those parts are composed unchanged. The guidance becomes the project skill
   `.claude/skills/concorde/SKILL.md` and a block in the project's `CLAUDE.md`.
   The block lies between `<!-- concorde:start -->` and `<!-- concorde:end -->`.
   On a later install, the block is replaced in place. The rest of the file stays untouched.
   Where the spec part is installed, once a project glossary is declared, the block ends with an
   `@<path>` import of that glossary
   ([requirements](requirements.md#req.distribution.glossary-import)). The task-session prompt is
   composed of the same parts. It replaces the build's composition of every part in the Framework
   copy, `.concorde/framework/generated/guidance/task-session.md`, where Coordination reads it.
   When the coordination part is not installed, the prompt is removed there.
   After an `init --apply` that created the first glossary, Distribution's `init` entry point also
   adds that import. [The command entry points](#realization.distribution.command) describe this.
   The guidance is for Claude Code alone, since the main agent and its task sessions run on
   Claude Code for now. Nothing is placed for a pi session. A project's own `AGENTS.md` is left as
   it is.
7. **It installs the workflows and the project MCP server.** Where the workflow part is
   installed, it installs every rendered workflow of an installed part for Claude Code whose
   sources allow it. Every source of such a workflow in a part's code directory, as the build
   manifest records it, lies in an installed part's directory.

   Each such workflow becomes `.claude/workflows/concorde-<name>.js`.
   Claude Code offers the workflow as the command `/concorde-<name>`.
   Where the workflow part is installed, the `permissions.allow` of the project's `.claude/settings.json`
   gains the rules the workflow needs to run without a prompt per step. These are `Workflow(concorde-<name>)` for each workflow
   and the rules the installed parts register under `install.permissions`.
   The workflow part registers two rules for its [step agents](../glossary.json#concept.step-agent):
   - `mcp__concorde__workflow_step`, the project MCP server's tool through which they start every
     step.
   - `Bash(.concorde/bin/concorde workflow report:*)`.

   The installer adds only rules that are missing. The installer records them in the receipt.
   On a later install, the installer removes the recorded rules it no longer ships. It leaves every other
   setting untouched ([requirements](requirements.md#req.distribution.installer-own-permissions)).
   In every install, it registers the [project MCP server](../glossary.json#concept.project-mcp-server)
   in the project's `.mcp.json`. The server serves the tools of the installed parts.
   The entry is `"concorde": {"command": ".concorde/bin/concorde", "args": ["project-mcp"]}`.
   Claude Code starts the server from the directory a session starts in, the project root.
   The installer keeps every other server. When that entry is already there, the installer leaves
   the file as it is
   ([requirements](requirements.md#req.distribution.installer-project-mcp),
   [the rest kept](requirements.md#req.distribution.installer-mcp-kept)).
8. **It records the install.** It adds the ignore rules each installed part contributes.
   Examples are:
   - The Kernel's `.concorde/locks/`.
   - Execution's `.concorde/unbound/`.
   - Execution's `.concorde/lobby/`.
   - Execution's `.claude/worktrees/`, where its
     [unbound checkouts](../glossary.json#concept.unbound-checkout) go.
   - Coordination's `.concorde/tasks/`.
   - Coordination's `.concorde/history/`.
   - Coordination's [workspace binding](../glossary.json#concept.workspace-binding)
     `.concorde/workspace.json`, which each task worktree gets.
   - Coordination's `.claude/worktrees/`, where task worktrees go.
   - Distribution's own `.concorde/framework/`.
   - Distribution's own `.concorde/tools/`.
   - Distribution's own `.concorde/runs/`, where Dogfooding keeps
     [defect reports](../glossary.json#concept.defect-report) and End-to-end testing keeps its
     session logs.

   It writes the receipt `.concorde/install.json`, which names the installed parts.
9. **It keeps the installed files bound.** Where the spec part is installed, in an initialized
   project, it asks Spec core to update the root Module's Concorde installation realization.
   Spec core brings that realization in step with the receipt. A file becomes an exact entry
   when all these conditions hold:
   - The receipt names the file outside `.concorde/`.
   - The file is not one of the amended files.
   - The file exists.
   - No realization binds the file by its exact path.

   When an entry's file is gone, the entry is removed. So the files a newer Concorde adds are bound
   like those initialization bound
   ([requirements](requirements.md#req.distribution.installer-keeps-installation-bound)). Specs
   that cannot be read are left as they are for `spec-validation` to report.
   When Spec core refuses a binding, the result reports it, as
   [below](#when-an-install-fails-halfway).

The installer prints the receipt as its result.
[The install result](contracts.md#contract.distribution.install-result) defines that result
exactly. The receipt names Concorde's own environment under `python`, with these details:

- Its path.
- The requirement it was created for.
- The interpreter uv chose.
- That interpreter's version.

With installed dependencies, the receipt names them under `dependencies`, with these details:

- The requirements file.
- The digest of the `uv.lock` they came from.
- The number of packages.

Without the dependencies, `dependencies` is `null`. The receipt also names:

- `d2` and the pi runtime under `tools`.
- The checkout installed from as `source`.
- The commit the checkout was at as `source_commit` (`null` outside a Git checkout).
- The installed parts with the one version they carry
  ([requirements](requirements.md#req.distribution.parts-recorded)).
- The `mode`, `normal` or, for a [develop install](../glossary.json#concept.develop-install) made
  with `--develop`, `develop`.

Under `files`, it lists every file Concorde owns in the project. This includes a default an earlier
install wrote and this one found in place
([requirements](requirements.md#req.distribution.receipt-complete)). Under `defaults`, it lists
those files that are Concorde-owned defaults. This lets a later install know them without a
package that still declares them. Under `amended`, it lists the project's own files it only amends:

- `.gitignore`.
- `CLAUDE.md`.
- `.mcp.json`.
- Once written, `.claude/settings.json`
  ([requirements](requirements.md#req.distribution.receipt-amended)).

When work of an installed part still runs at the check, the installer refuses the project with
`concorde_busy`. This is because replacing the framework copy under that work would change its
code halfway ([requirements](requirements.md#req.distribution.idle-install)). The installer asks
the idle check each installed part registers. It names everything those checks report
([requirements](requirements.md#req.distribution.busy-named)). In Concorde, the execution part's
check is the one that reports anything. It reports every [run](../glossary.json#concept.run) of an
Operation or an [execution command](../glossary.json#concept.execution-command) whose runner holds
its [run lock](../glossary.json#concept.run-lock) at that moment. The check finds the run through its
[run progress file](../glossary.json#concept.run-progress-file) wherever the
[run store](../glossary.json#concept.run-store) keeps it. This includes the lobby while a bound run
waits for its workspace's lock. An Operation's worker's
[progress file](../glossary.json#concept.progress-file) lies beside the Operation's progress file.
The worker's progress file names the same runner. It is not a run of its own. A project without the
execution part has no run to report.

This check is all the protection there is. The installer makes it once, in step 1.
It takes no lock that keeps a run from starting afterwards, during these steps:

- It downloads.
- It places the pi runtime.
- It replaces the Framework copy.
- It creates Concorde's environment.

At the check, the installer does not see a runner that still starts. That runner takes its run lock
only once it has loaded its code. **While an install or update runs, the developer must not start
any of these in any worktree of the project**:

- A run.
- `task-validation`.
- `delivery`.
- Any other `concorde` command.

Such a command may find no interpreter or load code partly old and partly new.
As a result, the command may fail or misbehave. Long-lived processes the check never looks at keep
running the code they loaded until they restart. Examples are each session's
[project MCP server](../glossary.json#concept.project-mcp-server) and
[Spec MCP server](../spec-tooling/spec-mcp/module.md). The help of `concorde update` and of the
installer says so where the developer starts them.

#### When an install fails halfway

Only the refusals of step 1 and the download of step 2 are decided before the first write.
After the first write, a step that runs a program can still fail with these codes:

- `pi_runtime_failed`.
- `python_env_failed`.
- `python_dependencies_failed`.

A file operation of the installer itself can also fail, on a full disk or a path it may not
replace. The installer refuses that failure with `install_failed` and the operating system's error
([requirements](requirements.md#req.distribution.failed-write-reported)). An installer that is
killed reports nothing. Nothing is rolled back. What the steps before the failure wrote stays.
What the project holds depends on where the install stopped:

- **Before the receipt**, steps 2 to 8: the project may hold these new components:
  - The new tools.
  - The Protocol copy.
  - A new or partly copied Framework runtime.

  These may sit beside these previous components:
  - The command.
  - The guidance.
  - The workflows.
  - The settings.

  The receipt still describes the previous install. After a first install, the receipt is missing.
  Until the install completes, the installed command may not run. It then says that its own Python
  environment is missing.
- **At the receipt**: the receipt is replaced whole, so it is either the previous one or the new
  one. A killed installer may leave `.concorde/install.json.partial` behind.
- **After the receipt**, in step 9: every installed file and the new receipt are in place.
  Only the installation realization may lag behind the receipt. Spec core writes its metadata
  member as one [file transaction](../glossary.json#concept.file-transaction).
  When Spec core creates the realization, that same transaction includes the root entry's paragraph
  explaining it. When a write fails while the installer runs, Spec core restores the transaction.
  When Spec core refuses the binding, the install still succeeds. Its result carries Spec core's
  error under `binding_error`. The error names every file left with its new content by a restore
  the operating system refused. An installer can be killed between the two writes of a new
  realization. That interruption, or such a failed restore, can leave the metadata naming the
  realization without the paragraph that explains it. `spec-validation` reports that state.

Running the same install again repeats every step. It keeps the `d2` and pi runtime already in
place. It completes the install, with one exception: it does not write a missing paragraph of a
realization that already exists. The developer then removes that realization from the root Module's
metadata. After that removal, the next install creates the realization whole.

### The pi runtime

Unless the
[worker configuration](../glossary.json#concept.worker-configuration) chooses Claude Code for them,
workers run on pi. The main agent runs on Claude Code.
Since workers run on pi by default, every install of the worker harness part places the **pi runtime**
as that part's install contribution under `.concorde/tools/pi-runtime/`.
The pi runtime is the sandbox engine `@anthropic-ai/sandbox-runtime` that pi workers run their
commands in. The install places it through these steps:

- Copy the package's `src/concorde/distribution/pi_runtime/package.json` there.
- Copy `package-lock.json` there.
- Run `npm ci --ignore-scripts`.

After checking each npm package's integrity hash, that command installs exactly the locked versions
([requirements](requirements.md#req.distribution.installer-locked-pi-runtime)). A later install
with the same lockfile keeps the runtime it placed. When the runtime is still to be placed and npm
is not on `PATH`, the install refuses with `npm_missing` before writing anything
([requirements](requirements.md#req.distribution.installer-programs-first)).
For a machine where every worker runs on Claude Code, `--without-pi-runtime` leaves the runtime out.
The receipt records that choice (`pi_runtime`) so that an update keeps it.
A pi worker then fails with `pi_runtime_missing`, naming the command that installs the runtime.

### Updating an installed Concorde

<a id="concept.distribution.update"></a>

`concorde update` runs the installer in update mode.
It uses the Concorde checkout the receipt names as its `source` (or `--from <checkout>`).
`python3 <checkout>/scripts/install-concorde.py <project>
--update` does the same from the checkout. An update installs exactly the parts the receipt names.
When the receipt names none, the update installs every part, as with a receipt written before parts
were recorded. The update also installs any part the new Concorde makes one of those parts depend on
([requirements](requirements.md#req.distribution.update-installed-parts)). With an update,
`--parts` adds parts to that set, with the parts they depend on.
When the new Concorde no longer builds a part the receipt names, the update refuses with
`unknown_part`. It goes through three steps. The last two apply only where the spec part is installed:

1. **It installs as the first install did.** It does the following:
   - It keeps develop mode.
   - Where the previous install had a part needing `d2` and placed none, it keeps `d2` left out.
   - Where the previous install had a part needing Python dependencies and placed none, it keeps
     the Python dependencies left out.
   - Where the worker harness part is installed, it always places the pi runtime unless the first
     install left it out with `--without-pi-runtime`.
   - It creates Concorde's own environment again with uv for the new checkout's Python requirement.
   - When a run holds its run lock at the check, it refuses like an install.

   The `d2` and Python dependency rules let them come with a part added later when the earlier
   install had no use for them.
   The pi runtime rule therefore adds it to an install made before the runtime was placed by default.
   Until the update ends, nothing else in the project may be started, as
   [the busy check](#installing-into-a-project) explains.
2. Where the project is initialized, **it binds the new Protocol copy** in the project configuration
   itself. This is the one write of the project configuration an installer makes.
   A project not initialized yet has no configuration. The update does not create that configuration.
   In that case, the mark of step 3 records no rebinding unless an earlier mark did.
   Initialization binds the copy later.
3. **It marks the project Concorde unvalidated** by writing `.concorde/update.json`, which Git ignores.
   The mark records these values before and after:
   - The versions.
   - The installed commits.
   - The Protocol bindings.

   The validation findings `CONCORDE-UPDATE-001` and `CONCORDE-UPDATE-002` described next name the
   commits too. This is because, between two commits of a
   [Concorde repository](../glossary.json#concept.concorde-repository), the version seldom changes.
   The mark is replaced whole, so until this write an earlier mark stays as it was.
   When the project still carries an earlier update's mark without successful validation since that update,
   the new mark keeps these before-values from the earlier mark:
   - Its version.
   - Its commit.
   - Its Protocol binding.

   This is because everything installed since then is still to be validated.
   The new mark names this update's corresponding values as the ones after
   ([requirements](requirements.md#req.distribution.update-mark-kept)).

The mark then decides what validation says. While it is there, `concorde spec-validation` in the
primary worktree reports `CONCORDE-UPDATE-001` as an error. That error also stops a `task merge`.
A validation that finds other errors keeps the mark.
The first validation that finds none removes the mark and says so (`CONCORDE-UPDATE-002`).
Only an update sets the mark, so a project that stops validating because of its own changes is
never marked by it.

```d2 illustrative
direction: right
unmarked: "Not marked\n(no update.json)"
installing: "Installing, not yet\nrebound or marked"
unvalidated: "Concorde unvalidated\n(update.json)"
unmarked -> installing: "concorde update:\ninstall (step 1)"
installing -> unvalidated: "rebind, mark\n(steps 2 and 3)"
installing -> installing: "a failure or interruption:\nrun the update again"
unvalidated -> unvalidated: "spec-validation with\nerrors: CONCORDE-UPDATE-001"
unvalidated -> unmarked: "spec-validation without\nother errors: CONCORDE-UPDATE-002"
```

Where the spec part is not installed, the update ends after its install with these effects:

- It leaves the project configuration alone.
- It writes no mark.
- Its [result](contracts.md#contract.distribution.update-result) carries `update` `null`.
- Its result asks only for the updated files to be committed, never for a `spec-validation` the
  project does not have.

Open tasks are a separate matter. They are an
[optional integration](../glossary.json#concept.optional-integration) with the coordination part.
Where the coordination part is installed, its registration reports the tasks that have not ended.
The [update result](contracts.md#contract.distribution.update-result) lists those tasks.
When the coordination part is installed and the Protocol copy changed, the result asks for the primary
branch to be merged into each task.
This is because their worktrees keep the previous copy until then.
Validation does not wait for that merge. Without the coordination part the list is empty.

When an update fails or is interrupted before its install writes the new receipt, it ends before
it rebinds or marks anything. The previous receipt stays in place, so running the update again
updates from that install.
An update can stop after the new receipt at any of these points:

- In step 9 of the install.
- While it rebinds.
- While it writes the mark ([a failed write](requirements.md#req.distribution.failed-write-reported)).

Such an update leaves the new Concorde installed with the Protocol binding old or new and without
this update's mark.
For a project that was not marked before, the following holds:

- The project has no mark.
- Running the update again completes it.
- The completed update's mark then names the Concorde just installed as the one before.

For a project already marked, the earlier mark stays in place.
The completed update keeps that earlier mark's before-state too.
A killed update may leave `.concorde/update.json.partial` behind.
When the coordination part fails to report its open tasks, the update refuses with `part_failed`
after these steps:

- It installs.
- It rebinds.
- It marks.

The new Concorde is in place. The project is marked.
Only the result's list of open tasks is lost. `concorde task list` shows those open tasks.
When the installed command no longer runs because the failure left its Framework copy or environment
incomplete, the update is run again with `install-concorde.py --update` from the checkout.

### Refusals

Every refusal of the installer and of `concorde update` prints `{"error": <link>}`.
Every refusal exits with status 1. The output is one link of the Framework's
[error chain](../glossary.json#concept.error-chain), in the shape of its
[error contract](../kernel/tracing/contracts.md#contract.tracing.error). The link has these details:

- Its actor is `Installer (install-concorde)` or `concorde update`.
- Its code is the refusal's.
- Its detail names what is wrong and where.

When only a change from this list corrects the refusal, its reason is `input`:

- A different project.
- A different Concorde checkout.
- A different argument.

Otherwise, its reason is `environment`
([requirements](requirements.md#req.distribution.installer-error-links)). The caller can therefore
forward the emitted error-chain link as the cause of its own link like any other refusal.

The table lists these details for every refusal:

- When it happens.
- Its reason.
- Whether it can come after the installer wrote something.

| Code | Refused when | Reason | After a write |
| --- | --- | --- | --- |
| `invalid_arguments` | the installer's or `concorde update`'s command line is malformed, such as a missing project or an option without its value | `input` | no |
| `invalid_project` | the project is not a directory | `input` | no |
| `unknown_part` | `--parts`, or the receipt an update reads, names a part the package does not build, or a part depends on one | `input` | no |
| `stale_build` | the build is stale, or a render or file the install places, such as the guidance or a file an installed part ships, is missing | `input` | no |
| `invalid_docsite_template` | Views' inventory rule rejects the package's docsite template | `input` | no |
| `develop_source_not_repository`, `develop_source_not_primary`, `develop_source_detached`, `develop_source_dirty` | [Dogfooding's](#uses-dogfooding) source check refuses the checkout of a develop install | `input` | no |
| `develop_source_unreadable` | Git cannot run to check the checkout of a develop install | `environment` | no |
| `concorde_busy` | an installed part's idle check reports work running, in Concorde a run whose runner holds its run lock | `environment` | no |
| `part_failed` | an installed part's `idle_check` or `after_update` entry raises or answers what the [registration contract](contracts.md#contract.distribution.part-registration) does not allow, refused before any write for `idle_check` and after the update's install and mark for `after_update` | `environment` | for `after_update` |
| `invalid_descriptor` | `concorde.json` names no Python requirement or pins no `d2` release, or the pi runtime's lockfile pins no runtime | `input` | no |
| `settings_invalid` | `.claude/settings.json` is not a JSON object with an optional `permissions.allow` list | `input` | no |
| `mcp_config_invalid` | `.mcp.json` is not a JSON object with an optional `mcpServers` object | `input` | no |
| `uv_missing` | `uv` is not on `PATH` | `environment` | no |
| `npm_missing` | `npm` is not on `PATH` and the pi runtime is still to be placed | `environment` | no |
| `unsupported_platform` | `concorde.json` pins no `d2` archive for this platform | `environment` | no |
| `d2_unavailable`, `d2_digest_mismatch`, `d2_archive_invalid` | the pinned `d2` archive cannot be downloaded, does not match its SHA-256 or holds no readable program | `environment` | no |
| `pi_runtime_failed` | `npm ci` fails to place the pi runtime | `environment` | yes |
| `python_env_failed` | `uv venv` cannot create Concorde's own environment | `environment` | yes |
| `python_dependencies_failed` | a step installing the Python dependencies fails | `environment` | yes |
| `install_failed` | a file operation of the installer or of `concorde update` fails | `environment` | yes |
| `not_installed` | `concorde update` finds no readable receipt | `input` | no |
| `update_source_missing` | `concorde update` finds no checkout to update from | `input` | no |

### After installing

Except for the installation realization of step 9, the installer never writes Specs or the registry.
A plain install never writes the project configuration. Only update mode rewrites the
configuration's Protocol binding, as described above
([requirements](requirements.md#req.distribution.installer-no-specs)). Where the spec part is
installed, its install contribution then lets the developer describe the project.
When the spec part is installed, `concorde init --propose --name <name>` prints Spec core's initialization proposal.
`concorde init --apply --proposal <file>` applies a proposal read from a file outside the project
only when Spec core accepts all these properties of it:

- Its shape.
- Its integrity (the proposal digest matches the value).
- Its freshness (the project is still in the state it was computed from).

This acceptance shows the proposal intact and current, not that propose printed it
([Spec core](../spec-tooling/spec/requirements.md#req.spec.init-explicit-envelope)). After a plain
install that brought a new Protocol copy, the developer accepts the copy by updating the binding.
`concorde update` does that itself.

## How it is built

### Why the parts reach Distribution only through registrations

Distribution must compose any set of parts.
This includes a set that leaves out the very Modules Distribution would otherwise call.
In a project with only the spec part, the `concorde` command has no `task`.
In a project without the spec part, the command has no `spec-validation`.
If Distribution imported each part for these purposes, installing Distribution would install every part:

- To route its commands.
- To install its files.
- To check that it is idle.

Under those imports, a part missing from the project would fail at the first call that reached it.
Because of these import problems, each part describes itself as plain data.
For the same reason, Distribution loads only the registrations of the installed parts.
From those registrations, Distribution does the following:

- It routes a command to the part that registered it.
- It presents the MCP tools the installed parts registered.
- It places the files they contribute.
- It places the rules they contribute.
- It places the programs they contribute.
- It composes their guidance.
- It asks their idle checks.

No part imports Distribution either, so registering needs nothing installed.
The spec part depends on nothing. The spec part registers like any other.
The registration is Distribution's own contract because Distribution is the one that reads it.
Similarly, the worker harness owns the format of the grant it receives.

All parts are built from this one repository. They carry its one version number.
Because of this, a project never holds two parts of different Concorde versions.
For the same reason, an update moves every installed part together.

### Around it

<a id="uses-spec"></a>

**Spec core** is an [optional integration](../glossary.json#concept.optional-integration).
It matters only where the spec part is installed. There, Distribution relies on Spec core for
steps Distribution adds around the spec part's own commands. Spec core owns:

- `spec-validation` and `registry`.
- The [structural checks](../glossary.json#concept.structural-check) and
  [registry](../glossary.json#concept.registry) they work on.
- The [Protocol binding](../glossary.json#concept.protocol-binding) that
  `protocol-manifest --bind-project` and an update rewrite.

For commands that print Spec core's envelope, Distribution relies on that envelope.
These are the commands [listed above](#the-command-line) as not routed elsewhere.
Distribution never interprets a Spec itself. A Spec core refusal of such a command prints
unchanged in that envelope. Distribution writes and amends the envelope in its own code.
It meets the envelope's format without Spec core's code. The installer builds the
Protocol copy itself from the tracked manifest. Spec core defines the manifest's format.
Before any write, the installer refuses a stale build. The installer calls the spec part only
through the install services its registration names:

- The docsite template before any write.
- The binding of the installed files after the receipt.

A refusal of the binding has these effects:

- The Specs are left to `spec-validation`.
- The install remains successful.
- The install's result carries Spec core's [error](../spec-tooling/spec/errors.md#contract.spec.error).

The binding is one of Spec core's file transactions. The transaction's limits decide what an interrupted binding leaves, as
[When an install fails halfway](#when-an-install-fails-halfway) explains. Without the spec part,
none of these exist:

- A Protocol copy.
- A binding.
- Initialization.
- An update mark.

<a id="uses-views"></a>

**Views**, in the spec part too, owns the docsite scaffold. `docsite` only routes
`--propose`/`--apply` to Views. The scaffold proposal and every file Views writes are Views'
responsibility. Without `--proposal`, an `--apply` is refused first. Views also owns the template
inventory. This rule selects which files of the package's `docsite/` are the template.
Where the spec part is installed, the installer ships exactly those files, `scaffold/` included.
Where the spec part is installed, the installer calls the rule through the spec part's
`install.prepare` service rather than repeating it.
Where the spec part is installed and the rule rejects the package's template, the installer
refuses with `invalid_docsite_template`.
These shipping and rejection rules apply so that a project's scaffold always finds the template it
expects ([one inventory](../spec-tooling/views/requirements.md#req.views.template-inventory),
[the rule](../spec-tooling/views/contracts.md#contract.views.scaffold-proposal)).

<a id="uses-tracing"></a>

**Tracing** defines the [error contract](../kernel/tracing/contracts.md#contract.tracing.error).
These components print their own refusals in that contract's shape:

- The installer.
- `concorde update`.
- The `concorde` command.
- The project MCP server.

Because these refusals follow that shape, a caller forwards them like any other link.
Distribution follows that shape without importing the Kernel's code, since Distribution is
installed with any part, the spec part alone included.

<a id="uses-dogfooding"></a>

**Dogfooding** owns the [develop
install](../glossary.json#concept.develop-install): which checkouts may be
installed from in develop mode, and the guidance a develop install adds.
Dogfooding is no part, so the installer reaches it through the entry the package descriptor names
under `develop.check`. With `--develop`, and on every update of a develop install, the installer
performs these steps:

- Before writing anything, it calls Dogfooding's source check.
- When the check refuses, the installer refuses with the check's code and message.
- Then, where the coordination and issues parts are installed, it adds Dogfooding's rendered
  guidance to the skill and the `CLAUDE.md` block
  ([guidance composition](#guidance-composition)).
- It records the mode and the checked commit in the receipt.

<a id="uses-execution"></a>

**Execution**, in the execution part, is an
[optional integration](../glossary.json#concept.optional-integration) reached through that part's
idle check. Distribution never reads a run lock itself. Distribution relies on the check's report
meaning a run that still runs. Such a [run](../glossary.json#concept.run) has a runner that holds
its [run lock](../glossary.json#concept.run-lock). The run is found through its
[run progress file](../glossary.json#concept.run-progress-file) wherever the
[run store](../glossary.json#concept.run-store) keeps it, the lobby included.
This ensures that a busy refusal names exactly the runs whose code an install would replace under
them. Where the execution part is installed and such a run runs, an install is refused.
Without the execution part, no part reports a run. The installer then finds the project idle.

<a id="uses-tasks"></a>

**Tasks**, in the coordination part, is an optional integration too. Distribution relies on this
promise from Tasks. While an update's mark is in the primary worktree, every `task merge` runs
`concorde spec-validation` on the merged result
([requirements](../coordination/tasks/requirements.md#req.tasks.merge-update-validated)).
This is how the mark stops a merge until the project validates. After an update, Distribution
lists the open tasks only from what the coordination part's `after_update` entry reports.
Without the coordination part, there is no task to merge or list. The update result's `open_tasks`
is then empty.

Every other part reaches Distribution only through its registration. Distribution relies on
nothing of that part but what the registration says. Distribution routes each of these to the part
that registered it, handing that part the rest of the command line:

- `task`.
- `run`.
- The execution commands.
- `workflow`.
- `issues`.
- `trace`.

That part defines its own output. That part defines its own exit codes. Distribution names no
Operation's or command's meaning. Distribution passes no task. Distribution places the workflows the workflow part renders,
with the permission rules their step agents need. Like any other build output, Distribution refuses
stale renders. Distribution places the worker harness part's pi runtime and discovery entry point.
Distribution writes neither the
[worker configuration](../glossary.json#concept.worker-configuration) nor the
[model map](../glossary.json#concept.model-map).

### Inside

<a id="realization.distribution.descriptor"></a>

The **package descriptor** `concorde.json` is an input of the build. Therefore, a licence or
version change is never shipped with renders made before that change.

<a id="realization.distribution.build"></a>

The **build renderer** is a pure function of the source tree followed by a guarded write.
Includes must be:

- Safe.
- Acyclic.
- Audience-consistent.

An output is written only inside the build-owned `generated/` locations
([requirements](requirements.md#req.distribution.build-owned-outputs)). A prompt pulls in another
with an include line. The prompt declares the audience it is written for.
The include line and audience declaration work together so that a worker's instructions never take
in text meant for another reader. These are requirements:

- The [include line](requirements.md#req.distribution.prompt-includes).
- The [safe include](requirements.md#req.distribution.safe-includes).
- The [audience rules](requirements.md#req.distribution.include-audience).

A prompt is reached at most once within one root
([requirements](requirements.md#req.distribution.include-once)). A prompt is never deduplicated.
These rules make the order and the values of every text a root holds visible in its tree.
A text needed twice in one root is therefore kept in two prompts.
Unless its bytes still match the previous manifest, a leftover is not removed.
Any of these stops the build first:

- An edited leftover.
- A link.
- An unknown file.

The build also renders the **skills** agents load as Agent Skills, each as
`generated/skills/<name>/SKILL.md` ([requirements](requirements.md#req.distribution.skills-rendered)).
Each skill is under the front matter naming the skill and describing it. The `concorde` skill is
the main-session guidance [composed](#guidance-composition) of every part of the package.
The installer makes that composition for the installed parts. The description presents the session
as the main agent only where the coordination part is installed.
`concorde-development` is the render of the root Module's guidance for developing Concorde in its
own source checkout. That checkout loads the development skill beside `concorde`. No installation
places the development skill. The checkout and an installation of every part can load the very
same skill file.
This is because the build renders the skill rather than only the installer.

<a id="guidance-composition"></a>

The **guidance composition**, `guidance.py`, is the one code that composes the guidance from a set
of part registrations. The build and the installer both use it. Each part registers up to three
rendered sections under `guidance`:

- Its section of the project skill (`skill`).
- Its section of the task-session prompt (`task_session`).
- Its section of the `CLAUDE.md` block (`claude_md`).

A composition of one kind is the sections of that kind of the given parts, in this order:

- Coordination's section first.
- The other named parts' sections in the order of the [parts table](#parts-and-their-registrations).
- The sections of parts the table does not name, after the others, by name.

Each section is unchanged. One blank line separates the sections
([requirements](requirements.md#req.distribution.composed-guidance)). The skill carries its front
matter. Without the coordination part, the skill and the block are the installed parts' sections
alone. There is then no task-session prompt, since task sessions are Coordination's.
Coordination's sections live in [Main session](../coordination/main-session/module.md)'s
`prompts/main-session/`. Every other part's sections live in `prompts/guidance/<part directory>/`.
Each section is bound by its part's top Module. Each section says what happens where a part it
mentions is not installed. When a section may be composed without a part, a paragraph naming that
part's command or project MCP tool names that part. It does so as in "where the execution part is
installed" ([requirements](requirements.md#req.distribution.guidance-absent-parts)). Dogfooding's
develop section is no part's. In a develop install that installs the coordination and issues
parts, the installer appends Dogfooding's develop section to the composed skill and block.
Dogfooding's develop section relies on those parts. In any other develop install, the installer
leaves that section out. Such an install is still a develop install in its source check and receipt.

<a id="realization.distribution.command"></a>

The **command entry points** are thin. They take these steps:

- Load the registrations of the installed parts.
- Take the global `--project-root`.
- Load the installed parts' registering code.
- Call the entry the registering part names for the command with the rest of the command line.

For a command registered with `output` `envelope`, the entry points print the shared envelope the
entry answers. For such a command, they exit with the envelope's status.
This thin routing means a command's meaning changes
only in its owner.
The commands routed to other owners keep their owners' output unchanged. Two Spec core commands
are the exceptions, where Distribution adds a step of its own to its owner's work:

- `spec-validation`: Spec core still decides every structural finding. Distribution's entry
  point adds the findings of [an update not yet validated](#updating-an-installed-concorde) to its
  result. After a result with no other error, the entry point removes the update mark
  `.concorde/update.json`, as the [installer program](#realization.distribution.installer) describes.
- `init --apply`: Spec core's initialization writes only the project's Specs and configuration,
  never `CLAUDE.md`. Once initialization succeeds, the entry point brings the glossary import of
  the installed `CLAUDE.md` block up to date. As a result, the first glossary is imported
  ([requirements](requirements.md#req.distribution.glossary-import)). Without that block, a project
  is left as it is. When that write fails, the result is `failed` with `guidance_failed`.
  That error keeps the initialization's result. It has the operating system's error as its cause.
  When that write fails, the project is initialized, so the developer repairs the cause.
  After that failure, the developer runs `concorde update` or the installer again, which install
  the block with the import.
  After that failure, the developer never runs `init --apply` again, because it refuses an initialized project.

<a id="realization.distribution.project-mcp"></a>

The **project MCP server host**, `src/concorde/distribution/project_mcp/`, is the
[project MCP server](#the-project-mcp-server) without any tool of its own. Its files have these roles:

- `server.py` runs the stdio session. It finds the primary worktree through Git's common directory.
  It decides whether the session listens to it as a channel. It sends channel events from the
  threads that watch.
- `calls.py` runs each call in a fresh process of the current Concorde. It watches the waits and
  the long work the tools start.
- `tools.py` is what that process runs. It presents the tools of the installed parts' registrations.
  It calls the entry each registration names. It becomes the long work a `long_work` tool hands over.

It is a small hand-written JSON-RPC session with no MCP library, since its wire is the same few
messages plus one notification.

<a id="realization.distribution.protocol-copy-writer"></a>

After checking freshness and each digest, the **Protocol copy writer** builds the copy from the
tracked manifest and rendered assets ([requirements](requirements.md#req.distribution.no-stale-copy)).
This ensures that a project receives exactly the Protocol the manifest names.

<a id="realization.distribution.installer"></a>

The **installer program** resolves the parts to install with their dependencies. It reuses:

- The writer.
- The build's freshness check.
- Views' docsite template inventory.

It places each installed part's contributions. It installs the composed `concorde` skill and
main-session block. These are all the checks that can refuse an install before any program runs:

- The build's freshness.
- The docsite template.
- Dogfooding's develop source check.
- The running Concorde.
- The descriptor's Python requirement.
- The project's settings.
- `uv` on `PATH`.
- When the pi runtime is still to be placed, `npm`.

The installer decides all those checks and then the pinned download before the first write.
So a refusal at any of them leaves the project as it was.

In update mode the installer takes the choices to keep from the previous receipt. It installs as
before. It then rewrites the configuration's Protocol binding itself. The reason is that the
project would otherwise be bound to a Protocol copy it no longer carries. The installer writes
the Git-ignored mark `.concorde/update.json`. The mark holds because Distribution's own
`spec-validation` entry point does the following:

- While the mark is present, the entry point adds `CONCORDE-UPDATE-001` to Spec core's result.
- Unless a result is otherwise a success, the entry point does not remove the mark.

A `task merge` has that validation in the primary worktree as its default check.
It therefore stops until the project validates with the new Concorde
([requirements](requirements.md#req.distribution.update-unvalidated),
[reported](requirements.md#req.distribution.unvalidated-reported),
[cleared](requirements.md#req.distribution.unvalidated-cleared)).

<a id="realization.distribution.guidance"></a>

The **Distribution guidance** is the part's sections of the [main-session
guidance](../glossary.json#concept.main-session-guidance). The sections are kept in
`prompts/guidance/distribution/`. The part registers the sections under `guidance` in its
registration. Wherever the part is installed, [the composition below](#guidance-composition)
composes those sections after Coordination's working method. The sections cover:

- The project skill's "Installed parts and updates".
- What `concorde` is.
- `part_missing`.
- `concorde update`.
- The `CLAUDE.md` block's sentence on them, the one section every install holds.

Each section says what happens where a part it mentions is not installed.

<a id="realization.distribution.tests"></a>

The **Distribution tests**, under `tests/concorde/distribution/`, exercise these on a fresh project:

- The build.
- The Protocol manifest.
- The installed command.

They verify the [requirements](requirements.md) and [scenarios](scenarios.md).
