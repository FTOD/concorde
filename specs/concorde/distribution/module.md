# Distribution

## Purpose

Distribution is the distribution [part](../glossary.json#concept.part), the one present in every
installation: it turns the Concorde checkout into packages a developer can install, installs into a
project the parts the developer chooses, with the parts they depend on, records which are installed
and updates them, and composes from the installed parts the one `concorde` command and the one
[project MCP server](../glossary.json#concept.project-mcp-server) a project's sessions use. It also
builds the generated files and writes the [Protocol copy](../glossary.json#concept.protocol-copy) a
project carries where the spec part is installed, and installs the
[main-session guidance](../glossary.json#concept.main-session-guidance) for Claude Code, on which the
[main agent](../glossary.json#concept.main-agent) and its
[task sessions](../glossary.json#concept.task-session) run for now, composed from the guidance each
installed part contributes.

Distribution reaches the parts only through their
[part registrations](../glossary.json#concept.part-registration), plain data each part gives it,
and no part imports Distribution's code. It does not decide what a command or an MCP tool does, what
the main agent is told, or a project's Specs and configuration — the installer writes no Spec but
the realization that keeps its own installed files bound.

## Core concepts

### The build manifest

<a id="concept.build-manifest"></a>

The **[build manifest](../glossary.json#concept.build-manifest)**, `generated/build-manifest.json`,
is the build's record of the digest of every source it read and of every output it wrote. It lets
the build tell what is stale, which `build --check` reports and the installer refuses, and remove a
leftover output only while its bytes still match the previous manifest.

### The Protocol copy

<a id="concept.protocol-copy"></a>

The **[Protocol copy](../glossary.json#concept.protocol-copy)** is the rendered Spec Protocol bundle
the installer writes under `.concorde/protocol/`, built from the tracked manifest and rendered
assets so that a project receives exactly the Protocol the manifest names. The project's
configuration accepts it through its [Protocol binding](../glossary.json#concept.protocol-binding):
after a plain install the developer updates the binding, while `concorde update` rebinds it itself.

### Parts and their registrations

<a id="concept.part-registration"></a>

Every part of Concorde is a package of its own in the one repository, carrying the repository's one
version number, and each gives Distribution a
**[part registration](../glossary.json#concept.part-registration)**: plain data, in the shape the
[registration contract](contracts.md#contract.distribution.part-registration) fixes, naming the
part, the parts it depends on, its `concorde` commands, its MCP tools, the
[typed value](../glossary.json#concept.typed-value) types it registers, its guidance, its install
contributions — the files it places, the `.gitignore` lines, the permission rules and the program it
needs, such as the worker harness's pi runtime — and its idle check, which says whether work of the
part is running in the project. The registration is data, not an interface a part implements against
Distribution's code, so a part that depends on nothing, such as the spec part, registers without
importing anything, and Distribution loads only the registrations of the installed parts. What a
part does not register does not exist in the project: a command, a tool, a guidance section or a
file of a part that is not installed is simply absent.

Each part keeps its registration as `registration.json` in its own directory of `src/concorde/`.
Every entry it names, a command, a tool, an install service, an idle check, is an attribute of a
module of that part's own package, so Distribution, the only code that imports a part by such a
name, never reaches one part's code through another's registration. A registration also names the
part's modules that register what its code provides when they load, such as typed value types,
trace roots, Operation definitions and workflows; Distribution loads them for every installed part
before it routes a part's command, answers a tool or renders the build. The installed parts are,
in a source checkout, every part the package builds, and in a project the parts its receipt names.
The build records what every part of the package registers in the **parts index**
`generated/parts.json` ([contract](contracts.md#part-registration)), from which a project's
`concorde` and project MCP server name the part of a command or tool the project lacks without
reading that part's registration.

| Part | Its [Module](../glossary.json#concept.module) | It registers, among others |
| --- | --- | --- |
| spec | [Spec tooling](../spec-tooling/module.md) | `spec-validation`, `registry`, `grant`, `init`, `docsite`, `spec-mcp`; its install services, which place the docsite template and bind the installed files; where it is installed Distribution places the Protocol copy |
| kernel | [Kernel](../kernel/module.md) | `trace`; the `.concorde/locks/` ignore rule |
| worker harness | [Worker harness](../worker-harness/module.md) | the pi runtime, the model discovery entry point |
| execution | [Execution](../execution/module.md) | `run` and every execution command a part registers; the idle check over the [run locks](../glossary.json#concept.run-lock) |
| workflow | [Workflows](../workflows/module.md) | `workflow`; the `workflow_step` and `workflow_report` tools; the rendered workflows and their permission rules |
| issues | [Issues](../issues/module.md) | `issues`; the `issue_*` tools |
| coordination | [Coordination](../coordination/module.md) | `task`; the `task_*`, `task_merge`, `locks`, `register_wait` and `trace_show` tools, and `run_result` where the execution part is installed; the main-session guidance; the open tasks an update reports |
| method | [Method](../method/module.md) | its Operations and the execution commands `task-validation`, `delivery` and `scaffold`; the [brownfield workflow](../glossary.json#concept.brownfield-workflow)'s script; its guidance |
| distribution | this Module | `build`, `protocol-manifest`, `update`, `project-mcp` |

### Commands named by their owner

A command is named after the part that registers it, as the table above lists: `task` gives the
coordination commands, `spec-validation`, `registry`, `docsite`, `grant`, `spec-mcp` and `init` the
Spec tooling commands, `issues` the Issues commands, `trace` the Tracing commands, `run` an
Operation and `workflow` a workflow step, and `build`, `protocol-manifest`, `update` and
`project-mcp` the **distribution commands**, the only ones Distribution owns itself. The
[execution commands](../glossary.json#concept.execution-command), runs without a worker, are named
by the part that provides them, such as Method's `task-validation`, `delivery` and `scaffold`, and
reach the Execution runner through the execution part's registration.

### The project MCP server

<a id="concept.project-mcp-server"></a>

The **[project MCP server](../glossary.json#concept.project-mcp-server)** is the project's one stdio
MCP server, `concorde project-mcp` registered as `concorde` in the project's `.mcp.json`, of which
each Claude Code session runs its own process. It is a host: it presents the MCP tools the installed
parts register, answering none of them itself, so a project with the coordination part has the task
tools, one with the [issues](../glossary.json#concept.issue) part the Issue tools, one with the workflow part the `workflow_step` tool
its workflows' step agents call, and a tool of a part that is not installed is absent. Each tool's
behaviour, arguments and refusals are its part's: each call's process loads the installed parts'
registering code and passes the call, with the session's provenance, to the entry the tool's
registration names, whose answer or refusal is the tool's. A tool of a part the project has not
installed is refused with `part_missing` naming the part, as a command is, and a tool whose
registration requires a part that is not installed, such as Coordination's `run_result` without the
execution part, is not presented. The host's own promises are these:

- **Current code.** The server process lives as long as its Claude Code session, which may be hours,
  while Concorde itself changes under it: a task merge in Concorde's own checkout, or
  `concorde update` in an installed project. Code loaded once would then keep answering with the
  rules and record formats it started with, and refuse the records the new code writes. So the
  server runs none of its tools itself. Each call runs `concorde project-mcp --call <tool>` with the
  `concorde` of the primary worktree as it is when the call arrives, its `.concorde/bin/concorde`
  or, in Concorde's source checkout, its `scripts/concorde.py`, as a process of its own, unless the
  tool's registration names the session's own worktree instead, as `workflow_step` does; the call's
  arguments and the session's provenance go to it as one JSON object, and its answer or refusal is
  the tool's. A call whose process gives no answer is refused with the server's own `call_failed`
  link, naming the command and what it printed. The tools, how each is served and the server's
  instructions, its own followed by the sentence each installed part registers, come from
  `concorde project-mcp --tools` of the current code. Each answer also says which tools the current
  code has; when they differ from those the session was given, the server tells its session that
  its tools changed, and Claude Code lists them again. Only the server's own session code, its few
  protocol messages and its instructions, stays what the session started with until the next
  session.
- **Locks handed to the work.** A tool whose registration says it starts long work, such as
  Coordination's `task_merge`, never waits for a lock: the call's process takes the locks the work
  needs at once or is refused at once naming the holder, and when it gets them it replaces itself
  with the command doing the work, which keeps them, since a `flock` belongs to the open file
  description that survives the change of program
  ([Handing a lock on](../kernel/tracing/contracts.md#handing-a-lock-on)). The server never holds a
  lock, so a lock belongs to the work and is released when the work ends, however it ends, even
  when the session and its server end first.
- **Watching and waking.** A tool may ask the server to watch a process, such as a wait for a task,
  a run or a lock that Coordination's `register_wait` registers, or the long work a tool started;
  the server wakes its session with a Claude Code channel event carrying that process's answer when
  it ends. The watched process ends with the server. Claude Code delivers a server's
  `notifications/claude/channel` only to an interactive session started with that server as a
  channel, a research preview that needs `--dangerously-load-development-channels server:concorde`,
  Anthropic authentication and an organization that has not disabled channels; a background session
  is never woken by them. A server cannot learn from Claude Code whether it is a channel, so it reads
  it from the command line of the interactive `claude` above it, one whose standard input is a
  terminal; when it has none, the tool returns the equivalent blocking `concorde` command for the
  session's background Bash instead, which wakes the session when it ends.

The server answers calls that wait, each on a thread of its own, so the session's other calls are
not held up meanwhile. Using it is recommended, not enforced: the `concorde` command and the server
take the same locks, so both paths see each other's holders. [Workers](../glossary.json#concept.worker)
never receive it: they launch with an empty MCP configuration.

## Overview

### From checkout to project

Distribution works in two stages. The build renders every part's prompts, the Protocol and the
workflow scripts into `generated/` and records the build manifest; the installer, run for a first
install or by `concorde update`, refuses a stale build, resolves the parts to install with the parts
they depend on, and places each one's files, the environment and the command, and the guidance and
workflows of the installed parts in the project.

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

The installer makes its checks and the pinned download before its first write, so a refusal at one
of them leaves the project as it was. Not every refusal does: the steps drawn dashed run programs
and can fail after something was written, as any write can, which [When an install fails
halfway](#when-an-install-fails-halfway) explains.

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
`scripts/` entry points; each realization's exact files are its metadata's `entries`. The
[build manifest](../glossary.json#concept.build-manifest) and
[Protocol copy](../glossary.json#concept.protocol-copy) are recorded and written but bind no file of
their own.

## Using Distribution

### The package

`concorde.json` is the package's identity: name, version, licence, the roots the
installer ships, install locations, the client `claude-code` the build renders workflows for, the
pinned third-party programs under `tools` (today `d2`, by release, URL and
per-platform SHA-256), and under `develop.check` the entry of [Dogfooding's](#uses-dogfooding)
develop source check. The build reads it too, so a changed descriptor makes every render stale.

### Building

`python3 scripts/concorde.py build` expands every prompt root into `generated/`
([requirements](requirements.md#req.distribution.build-reachable)), `{{name}}` becoming the literal
text `{name}` so that a prompt can show a placeholder such as a check's `{python}`, and wraps every
[workflow script](../glossary.json#concept.workflow-script) the parts contribute to the workflow
catalog as
`generated/workflows/claude/concorde-<name>.js` with its `meta` block and Claude Code step adapter,
through the workflow part's `renders` entry once every part's registering code is loaded, writes
the [parts index](contracts.md#part-registration) `generated/parts.json` from the parts'
registrations, and writes `generated/build-manifest.json` with every source's and output's digest.
It refuses a registration that breaks the [registration
contract](contracts.md#contract.distribution.part-registration) and a command or MCP tool name two
parts register ([requirements](requirements.md#req.distribution.unique-names)). The prompt
roots are the Protocol's `prompts/protocol/principles.md` and `prompts/protocol/kinds/module.md`
every file directly in `prompts/workers/`, `prompts/main-session/`, `prompts/dogfooding/` and
`prompts/development/`, and the prompt of every part's registered guidance, `prompts/<path>` for its
`generated/<path>`, each rendered to the same path under `generated/`; the two
[skills](#realization.distribution.build) are rendered from two of them. `build --check` only
reports what is stale, writing nothing
([requirements](requirements.md#req.distribution.build-check-read-only)). `generated/` is
Git-ignored, so a checkout always rebuilds. `protocol-manifest --write --bind-project` accepts a
Protocol change's fresh digests, binds the configuration and refreshes this checkout's own copy, as
described next.

### Reconciling the Protocol manifest

`protocol-manifest` compares the digests the tracked manifest `protocol/manifest.json`, whose shape
[Spec core](../spec-tooling/spec/contracts.md#protocol-manifest) defines, records for the rendered
Protocol assets with those of the current build. It first requires a fresh build and a readable
tracked manifest whose every asset the build holds; otherwise it reports `invalid` with
`CONCORDE-PROTOCOL-MANIFEST-001` naming the problem and writes nothing, whatever its flags. Then
each combination of its two flags does the following, its result's `differences` naming the assets
whose digests differed from the build's and its `artifacts` what it wrote:

| Flags | Writes | Status |
| --- | --- | --- |
| none | nothing | `success` when no digest differs, otherwise `invalid` with `CONCORDE-PROTOCOL-MANIFEST-001` naming the assets that differ |
| `--write` | the tracked manifest with the build's digests, only when one differs | `success` |
| `--bind-project` | the configuration's [Protocol binding](../glossary.json#concept.protocol-binding), set to the tracked manifest's version and the digest of its bytes, then this checkout's Protocol copy under `.concorde/protocol/` | `success` when no digest differs; otherwise the binding is written and the copy, which would no longer match the build, is refused with `protocol_mismatch` in a `failed` result, the copy left as it was |
| `--write --bind-project` | the tracked manifest when a digest differs, then the binding to it and the Protocol copy | `success` |

A Protocol change in this checkout is therefore accepted with both flags; `--write` alone suits a
checkout whose own configuration is bound otherwise, such as a package a project installs from.

### The command line

`scripts/concorde.py` (or the `concorde.sh`/`concorde.ps1` wrappers) takes a
global `--project-root` and one subcommand. In a source checkout that `uv sync` prepared, it runs
itself again on the checkout's own `.venv` interpreter, which holds Concorde's Python
dependencies; an installed copy has no `.venv` and runs on Concorde's own environment:

Each row's command exists in a project only when the part that registers it is installed; a command
of a part that is not installed is refused naming that part and how to install it, printing
`{"error": <link>}` whose code is `part_missing` and exiting with status 1, the one refusal by which
another part tells that a part is absent
([requirements](requirements.md#req.distribution.absent-part-named)). A command line naming no
command of the package is answered with one `failed` envelope, and `concorde --help` lists the
commands of the installed parts.

| Command | Does | Part, Module |
| --- | --- | --- |
| `spec-validation [target]` | runs the structural checks; Distribution adds the findings of [an update not yet validated](#updating-an-installed-concorde) and removes its mark | spec, [Spec core](../spec-tooling/spec/module.md), with Distribution's update findings |
| `registry --write` or `--check` | regenerates or checks the registry mirror | spec, [Spec core](../spec-tooling/spec/module.md) |
| `docsite --propose` or `--apply` | proposes or applies the docsite scaffold | spec, [Views](../spec-tooling/views/module.md) |
| `grant --modules <ids> --type <task type> [--root <worktree>]` | prints a [task type](../glossary.json#concept.task-type)'s grant | spec, [Spec core](../spec-tooling/spec/module.md) |
| `spec-mcp` | runs the stdio MCP server rooted at `CLAUDE_PROJECT_DIR` or the client's root; it prints no envelope | spec, [Spec MCP server](../spec-tooling/spec-mcp/module.md) |
| `project-mcp [--name <name>]` | runs the stdio [project MCP server](../glossary.json#concept.project-mcp-server) of the primary worktree; it prints no envelope | distribution, this Module, serving the tools the installed parts register |
| `init --propose --name <name>` or `--apply --proposal <file>` | proposes or applies a project's first [Spec](../glossary.json#concept.spec); after an apply Distribution adds the glossary import to the `CLAUDE.md` block | spec, [Spec core](../spec-tooling/spec/module.md), with Distribution's glossary import |
| `task open`, `list`, `show`, `close`, `merge`, `escalate` or `wait` | opens, lists, shows, closes, merges or escalates tasks, or waits for a task, run or lock; prints the task command's own JSON | coordination, [Tasks](../coordination/tasks/module.md) |
| `run <operation>` | runs one [Operation](../glossary.json#concept.operation) in the workspace of the current worktree or, when the Operation allows it, unbound; prints the [run result](../glossary.json#concept.run-result) | execution, [Execution](../execution/module.md), running the definitions the installed parts register with [Operations](../execution/operations/module.md) |
| `task-validation`, `delivery` or `scaffold` | runs one execution command in the workspace of the current worktree; prints the run result | method, the definitions of [Method](../method/module.md), run by [Execution](../execution/module.md) through [Commands](../execution/commands/module.md) |
| `workflow step` or `report` | runs one [workflow step](../glossary.json#concept.workflow-step), or reports a workflow's result; prints its own JSON | workflow, [Workflows](../workflows/module.md) |
| `issues list`, `show`, `check`, `report`, `close` or `reopen` | the Issues bookkeeping command `scripts/issues.py`; prints its own JSON | issues, [Issues](../issues/module.md) |
| `trace show`, `list` or `prune` | shows a [trace](../glossary.json#concept.trace) with its timing and cost rolled up, lists traces, or removes what retention allows; prints its own JSON | kernel, [Tracing](../kernel/tracing/module.md) |
| `build [--check]` | renders or checks the generated files | distribution |
| `protocol-manifest [--write] [--bind-project]` | [reconciles the Protocol manifest](#reconciling-the-protocol-manifest) | distribution |
| `update [--from <checkout>]` | updates the installed Concorde, as described below; prints its [update result](contracts.md#contract.distribution.update-result) | distribution |

Every command but `spec-mcp`, `project-mcp`, `task`, `run`, the execution commands, `workflow`, `issues`, `trace`
and `update` prints exactly one JSON envelope and exits with its
status, even when refused ([requirements](requirements.md#req.distribution.one-envelope)); those
route to their owners, which define their own output and exit codes, except `update`, which prints
its [update result](contracts.md#contract.distribution.update-result) or its
[error link](requirements.md#req.distribution.installer-error-links).

The worker harness part's standalone Workers entry point
`scripts/available_models.py --backend pi|claude [--json]` is shipped, as that part's install
contribution, under `.concorde/framework/scripts/available_models.py` with the runtime. It resolves
its imports relative to itself and works outside a Git worktree; it lists advisory configured
candidates, with the project model names the user's [model
map](../glossary.json#concept.model-map) gives each, without probing inference API access.
Configuration validation does not call it. The installer writes neither the worker configuration
nor the model map, which belongs to the user and lies outside every project.

The command runs the Framework copy of the worktree it belongs to; a task worktree has none of its
own, since Git ignores it, unless the task reinstalled Concorde there, so its command runs the
primary worktree's copy, found through Git's common directory.

### Installing into a project

The developer runs `python3 scripts/install-concorde.py <project> [--parts <part>[,<part>…]]`
from a built Concorde checkout. `--parts` names the parts to install, by the names of the
[parts table](#parts-and-their-registrations); the installer adds every part they depend on, and
installs every part when the option is left out. Distribution itself is installed with any part.
The installer first decides everything that could refuse the install and only then writes, so a refusal among these checks leaves the project as it was. On a
project where every check passes, it goes through these steps in order:

1. **It checks, writing nothing.** It refuses a directory that is not a project
   (`invalid_project`); a stale build (`stale_build`), which includes a stale render of the
   [main-session guidance](../glossary.json#concept.main-session-guidance); a docsite template
   that [Views](../spec-tooling/views/module.md)' inventory rule rejects
   (`invalid_docsite_template`,
   [checked first](requirements.md#req.distribution.installer-docsite-template-first)); a missing
   render of the guidance (`stale_build`,
   [requirements](requirements.md#req.distribution.installer-fresh-guidance)); with
   `--develop`, a source that Dogfooding's check refuses; a project in which an installed part reports
   work running (`concorde_busy`, described below); a `concorde.json` that names no Python requirement
   (`invalid_descriptor`); a `.claude/settings.json` that is not a JSON object with an optional
   `permissions.allow` list (`settings_invalid`,
   [checked first](requirements.md#req.distribution.installer-settings-checked)); a `.mcp.json`
   that is not a JSON object with an optional `mcpServers` object (`mcp_config_invalid`,
   [checked as early](requirements.md#req.distribution.installer-mcp-checked)); a machine
   without `uv` on `PATH` (`uv_missing`), since uv owns Concorde's Python; and, when the pi runtime described
   below is still to be placed, a machine without `npm` (`npm_missing`)
   ([requirements](requirements.md#req.distribution.installer-programs-first)).
2. **It places the pinned programs.** It fetches the `d2` release `concorde.json` pins, checks it
   against its SHA-256 before anything else is written and places it at `.concorde/tools/d2`,
   keeping it on a later install with the same pin
   ([requirements](requirements.md#req.distribution.installer-pinned-d2),
   [checked first](requirements.md#req.distribution.installer-d2-first); `--without-d2` skips
   it). It then places the pi runtime under `.concorde/tools/pi-runtime/`, as described below.
3. **It places Concorde's files.** It places the Framework runtime of the chosen parts under
   `.concorde/framework/`, replacing an earlier copy and leaving out `scripts/e2e/`, which only
   [End-to-end testing](../e2e/module.md) uses, and writes the files each chosen part contributes,
   Concorde-owned defaults only where absent. With the spec part go the Protocol copy under
   `.concorde/protocol/` and the docsite template under `.concorde/framework/docsite/`, exactly the
   files Views' template inventory selects, `scaffold/` included, from which
   `concorde docsite --propose` scaffolds a project's site
   ([requirements](requirements.md#req.distribution.installer-docsite-template)).
4. **It creates Concorde's own Python environment.** `uv venv` creates a venv at
   `.concorde/framework/python/` for the Python requirement `concorde.json` names under
   `runtime.python`, on an interpreter uv chooses — one of the machine's or a uv-managed CPython,
   which uv downloads when none fits — whatever interpreter runs the installer
   ([requirements](requirements.md#req.distribution.uv-owns-python)); when uv cannot create it,
   the install is refused with `python_env_failed` and uv's output. Into that environment go
   Concorde's Python dependencies, such as LangGraph, which `spec_panel` runs on: exactly the
   runtime part of the checkout's `uv.lock`, exported with `uv export` to
   `.concorde/framework/requirements.txt` and installed with `uv pip install --require-hashes`. A
   failing step is refused with `python_dependencies_failed` and the failing command's output;
   `--without-dependencies` skips them, and the Operations that need them then refuse.
5. **It writes the command.** `.concorde/bin/concorde`, composed from the registrations of the
   installed parts, runs Concorde only in that environment,
   with the caller's `PYTHONPATH`, `PYTHONHOME` and user site-packages left out, so an activated
   project venv never becomes Concorde's interpreter
   ([requirements](requirements.md#req.distribution.own-python)).
6. **It installs the guidance.** The main-session guidance, composed of Coordination's working
   method followed by the guidance every other installed part contributes, in the order of the parts
   table, becomes the project skill `.claude/skills/concorde/SKILL.md`, the build's renders of
   those parts composed unchanged, and a block between
   `<!-- concorde:start -->` and `<!-- concorde:end -->` in the project's `CLAUDE.md`, replaced in
   place on a later install, leaving the rest of the file untouched, and ending with an `@<path>`
   import of the project's glossary once one is declared
   ([requirements](requirements.md#req.distribution.glossary-import)). Distribution's `init` entry
   point also adds that import after an `init --apply` that created the first glossary, as
   [the command entry points](#realization.distribution.command) describe. The guidance is for Claude
   Code alone, since the main agent and its task sessions run on Claude Code for now; nothing is
   placed for a pi session, and a project's own `AGENTS.md` is left as it is.
7. **It installs the workflows and the project MCP server.** Where the workflow part is installed,
   every rendered workflow of an installed part for Claude Code becomes
   `.claude/workflows/concorde-<name>.js`, which Claude Code offers as the command
   `/concorde-<name>`, and the `permissions.allow` of the project's `.claude/settings.json` gains
   the rules the workflow needs to run without a prompt per step: `Workflow(concorde-<name>)` for
   each workflow and, for its [step agents](../glossary.json#concept.step-agent),
   `mcp__concorde__workflow_step`, the project MCP server's tool through which they start every
   step, and `Bash(.concorde/bin/concorde workflow report:*)`. It adds only rules that are missing,
   records them in the receipt, removes on a later install the recorded rules it no longer ships,
   and leaves every other setting untouched
   ([requirements](requirements.md#req.distribution.installer-own-permissions)). In every install
   it registers the [project MCP server](../glossary.json#concept.project-mcp-server), which serves
   the tools of the installed parts, in the project's `.mcp.json`
   as `"concorde": {"command": ".concorde/bin/concorde", "args": ["project-mcp"]}`, which Claude
   Code starts from the directory a session starts in, the project root, keeping every other
   server, and leaves the file as it is when that entry is already there
   ([requirements](requirements.md#req.distribution.installer-project-mcp),
   [the rest kept](requirements.md#req.distribution.installer-mcp-kept)).
8. **It records the install.** It adds the ignore rules each installed part contributes, such as
   the Kernel's `.concorde/locks/`, Execution's `.concorde/unbound/` and `.concorde/lobby/`,
   Coordination's `.concorde/tasks/` and `.concorde/history/`, the
   [workspace binding](../glossary.json#concept.workspace-binding) `.concorde/workspace.json` that
   each task worktree gets and `.claude/worktrees/`, where task worktrees go, and its own,
   `.concorde/framework/`, `.concorde/tools/` and `.concorde/runs/`, where Dogfooding keeps
   [defect reports](../glossary.json#concept.defect-report) and End-to-end testing its session
   logs, and writes the receipt `.concorde/install.json`, which names the installed parts.
9. **It keeps the installed files bound.** Where the spec part is installed, in an initialized
   project, it asks Spec core to bring the
   root Module's Concorde installation realization in step with the receipt: every file the receipt
   names outside `.concorde/`, other than the amended ones, that exists and that no realization
   binds by its exact path becomes an exact entry, and an entry whose file is gone is removed, so the files a newer Concorde adds are bound like those
   initialization bound
   ([requirements](requirements.md#req.distribution.installer-keeps-installation-bound)). Specs
   that cannot be read are left as they are for `spec-validation` to report, and a binding Spec
   core refuses is reported in the result, as [below](#when-an-install-fails-halfway).

The installer prints the receipt as its result, which
[the install result](contracts.md#contract.distribution.install-result) defines exactly. The
receipt names Concorde's own environment under `python` (its path, the requirement it was
created for, the interpreter uv chose and that interpreter's version), the installed dependencies
under `dependencies` (the requirements file, the digest of the `uv.lock` they came from and the
number of packages, or `null` without them), `d2` and the pi runtime under `tools`, the checkout
installed from as `source`, the commit it was at as `source_commit` (`null` outside a Git
checkout), the installed parts with the one version they carry
([requirements](requirements.md#req.distribution.parts-recorded)) and the `mode`, `normal` or, for a
[develop install](../glossary.json#concept.develop-install) made with `--develop`, `develop`. It
lists under `files` every file Concorde owns in the project, including a default an earlier
install wrote and this one found in place
([requirements](requirements.md#req.distribution.receipt-complete)), and under `amended` the
project's own files it only amends: `.gitignore`, `CLAUDE.md`, `.mcp.json` and, once written,
`.claude/settings.json` ([requirements](requirements.md#req.distribution.receipt-amended)).

A project in which work of an installed part is still running when the installer checks is refused
with `concorde_busy`, since replacing the framework copy under that work would change its code
halfway ([requirements](requirements.md#req.distribution.idle-install)). The installer asks the idle
check each installed part registers and names everything they report
([requirements](requirements.md#req.distribution.busy-named)). In Concorde the execution part's
check is the one that reports anything: every [run](../glossary.json#concept.run) of an Operation
or of an [execution command](../glossary.json#concept.execution-command) whose runner holds its
[run lock](../glossary.json#concept.run-lock) at that moment, found through its
[run progress file](../glossary.json#concept.run-progress-file) wherever the
[run store](../glossary.json#concept.run-store) keeps it, in the lobby too while a bound run waits
for its workspace's lock. The [progress file](../glossary.json#concept.progress-file) of an
Operation's worker, which lies beside the Operation's and names the same runner, is not a run of its
own. A project without the execution part has no run to report.

This check is all the protection there is. The installer makes it once, in step 1, and takes no
lock that keeps a run from starting afterwards, while it downloads, places the pi runtime,
replaces the Framework copy and creates Concorde's environment; nor does it see a runner still
starting at the check, which takes its run lock only once it has loaded its code. **The developer
must not start a run, `task-validation`, `delivery` or any other `concorde` command, in any
worktree of the project, while an install or update runs**: such a command may find no
interpreter or load code partly old and partly new, and fail or misbehave. Long-lived processes the
check never looks at, such as each session's
[project MCP server](../glossary.json#concept.project-mcp-server) and
[Spec MCP server](../spec-tooling/spec-mcp/module.md), keep running
the code they loaded until they restart. The help of `concorde update` and of the installer says
so where the developer starts them.

#### When an install fails halfway

Only the refusals of step 1 and the download of step 2 are decided before the first write. After
it, a step that runs a program can still fail (`pi_runtime_failed`, `python_env_failed`,
`python_dependencies_failed`), and so can a file operation of the installer itself, on a full disk
or a path it may not replace, which it refuses with `install_failed` and the operating system's
error ([requirements](requirements.md#req.distribution.failed-write-reported)); an installer
that is killed reports nothing. Nothing is rolled back. What the steps before the failure wrote
stays, and what the project holds depends on where the install stopped:

- **Before the receipt**, steps 2 to 8: the project may hold the new tools, Protocol copy and a new
  or partly copied Framework runtime beside the previous command, guidance, workflows and settings.
  The receipt still describes the previous install, or is missing after a first install, and the
  installed command may not run until the install completes: it then says that its own Python
  environment is missing.
- **At the receipt**: the receipt is replaced whole, so it is either the previous one or the new
  one; a killed installer may leave `.concorde/install.json.partial` behind.
- **After the receipt**, in step 9: every installed file and the new receipt are in place, and
  only the installation realization may lag behind the receipt. Spec core writes its metadata
  member, and the root entry's paragraph explaining it when it creates the realization, as one
  [file transaction](../glossary.json#concept.file-transaction), which it restores when a write
  fails while the installer runs. When Spec core refuses the binding, the install still succeeds and
  its result carries Spec core's error under `binding_error`, naming every file a restore the
  operating system refused left with its new content. An installer killed between the two writes
  of a new realization, or such a failed restore, can leave the metadata naming the realization
  without the paragraph that explains it, which `spec-validation` reports.

Running the same install again repeats every step, keeping the `d2` and pi runtime already in
place, and completes it, with one exception: it does not write a missing paragraph of a
realization that already exists. The developer then removes that realization from the root
Module's metadata, after which the next install creates it whole.

### The pi runtime

Workers run on pi unless the
[worker configuration](../glossary.json#concept.worker-configuration) chooses Claude
Code for them, although the main agent runs on Claude Code, so every install of the worker harness
part places, as that part's install contribution, the **pi runtime** — the sandbox engine
`@anthropic-ai/sandbox-runtime` that pi workers run their commands in — under
`.concorde/tools/pi-runtime/` by copying the package's
`src/concorde/distribution/pi_runtime/package.json` and `package-lock.json` there and running
`npm ci --ignore-scripts`, which installs exactly the locked versions after checking each npm
package's integrity hash
([requirements](requirements.md#req.distribution.installer-locked-pi-runtime)). A later install
with the same lockfile keeps the runtime it placed. When the runtime is still to be placed and npm
is not on `PATH`, the install refuses with `npm_missing` before writing anything
([requirements](requirements.md#req.distribution.installer-programs-first)).
`--without-pi-runtime` leaves the runtime out, for a machine where every worker runs on Claude
Code; the receipt records that choice (`pi_runtime`) so that an update keeps it, and a pi worker
then fails with `pi_runtime_missing`, naming the command that installs the runtime.

### Updating an installed Concorde

<a id="concept.distribution.update"></a>

`concorde update` runs, in update mode, the installer of the Concorde checkout the receipt names as
its `source` (or `--from <checkout>`); `python3 <checkout>/scripts/install-concorde.py <project>
--update` does the same from the checkout. An update installs exactly the parts the receipt names,
with any part the new Concorde makes one of them depend on
([requirements](requirements.md#req.distribution.update-installed-parts)); `--parts` with an update
adds parts to that set. It goes through three steps, the last two only where the spec part is
installed:

1. **It installs as the first install did.** It keeps `d2` and develop mode when they were
   installed, always places the pi runtime unless the first install left it out with
   `--without-pi-runtime` (so an update adds it to an install made before the runtime was placed by
   default), creates Concorde's own environment again with uv for the new checkout's Python
   requirement, and refuses like an install when a run holds its run lock at the check; nothing
   else in the project may be started until the update ends, as
   [the busy check](#installing-into-a-project) explains.
2. **It binds the new Protocol copy** in the project configuration itself, the one write of the
   project configuration an installer makes.
3. **It marks the project Concorde unvalidated** by writing `.concorde/update.json`, which Git
   ignores, with the versions, installed commits and Protocol bindings before and after. The
   validation findings `CONCORDE-UPDATE-001` and `CONCORDE-UPDATE-002` described next name the
   commits too, since between two commits of a
   [Concorde repository](../glossary.json#concept.concorde-repository) the version seldom changes.
   The mark is replaced whole, so until this write an earlier mark stays as it was. When the
   project is still marked by an earlier update it has not validated since, the new mark keeps that
   mark's version, commit and Protocol binding from before, since everything installed since then
   is still to be validated, and names this update's as the ones after
   ([requirements](requirements.md#req.distribution.update-mark-kept)).

The mark then decides what validation says. While it is there, `concorde spec-validation` in the
primary worktree reports `CONCORDE-UPDATE-001` as an error, which also stops a `task merge`; a
validation that finds other errors keeps the mark, and the first validation that finds none
removes it and says so (`CONCORDE-UPDATE-002`). Only an update sets the mark, so a project that
stops validating because of its own changes is never marked by it.

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

Open tasks are a separate matter, and an
[optional integration](../glossary.json#concept.optional-integration) with the coordination part.
Where it is installed, its registration reports the tasks that have not ended, and the
[update result](contracts.md#contract.distribution.update-result) lists them and, when the Protocol
copy changed, asks for the primary branch to be merged into each, since their worktrees keep the
previous copy until then; validation does not wait for that merge. Without the coordination part
the list is empty.

An update that fails or is interrupted before its install wrote the new receipt ends before it
rebinds or marks anything, with the previous receipt in place, so running it again updates from
that install. One that stops after the new receipt, in step 9 of the install or while it rebinds
or writes the mark ([a failed write](requirements.md#req.distribution.failed-write-reported)), leaves
the new Concorde installed with the Protocol binding old or new and without this update's mark:
a project that was not marked before has no mark, and running the update again completes it, but
its mark then names the Concorde just installed as the one before; a project already marked keeps
its earlier mark, whose before-state the completed update keeps too. A killed update may leave
`.concorde/update.json.partial` behind. When the
installed command no longer runs because the failure left its Framework copy or environment
incomplete, the update is run again with `install-concorde.py --update` from the checkout.

### Refusals

Every refusal of the installer and of `concorde update` prints `{"error": <link>}` and exits with
status 1: one link of the Framework's [error chain](../glossary.json#concept.error-chain), in the
shape of its [error contract](../kernel/tracing/contracts.md#contract.tracing.error),
whose actor is `Installer (install-concorde)` or `concorde update`, whose code is the refusal's,
whose detail names what is wrong and where, and whose reason is `input` when only a different
project, Concorde checkout or argument corrects it and `environment` otherwise
([requirements](requirements.md#req.distribution.installer-error-links)). The caller can therefore
forward it as the cause of its own link like any other refusal.

Every refusal, with when it happens, its reason and whether it can come after the installer wrote
something:

| Code | Refused when | Reason | After a write |
| --- | --- | --- | --- |
| `invalid_project` | the project is not a directory | `input` | no |
| `stale_build` | the build is stale, or a render the install places, such as the guidance, is missing | `input` | no |
| `invalid_docsite_template` | Views' inventory rule rejects the package's docsite template | `input` | no |
| `develop_source_not_repository`, `develop_source_not_primary`, `develop_source_detached`, `develop_source_dirty` | [Dogfooding's](#uses-dogfooding) source check refuses the checkout of a develop install | `input` | no |
| `develop_source_unreadable` | Git cannot run to check the checkout of a develop install | `environment` | no |
| `concorde_busy` | a run's runner holds its run lock | `environment` | no |
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

The installer never writes Specs or the registry, except the installation realization of step 9,
and a plain install never writes the project configuration; only update mode rewrites the
configuration's Protocol binding, as described above
([requirements](requirements.md#req.distribution.installer-no-specs)). Where the spec part is
installed, its install contribution then lets the developer describe the project:
`concorde init --propose --name <name>` prints Spec core's initialization proposal, and
`concorde init --apply --proposal <file>` applies a proposal read from a file outside the project
only when Spec core accepts its shape, its integrity (the proposal digest matches the value) and its
freshness (the project is still in the state it was computed from), which shows the proposal intact
and current, not that propose printed it
([Spec core](../spec-tooling/spec/requirements.md#req.spec.init-explicit-envelope)). After a plain install that brought a new Protocol copy, the developer accepts
it by updating the binding; `concorde update` does that itself.

## How it is built

### Why the parts reach Distribution only through registrations

Distribution must compose any set of parts, including one that leaves out the very Modules it would
otherwise call: the `concorde` command of a project with only the spec part has no `task`, and that
of a project without the spec part has no `spec-validation`. If Distribution imported each part to
route its commands, install its files and check that it is idle, installing Distribution would
install every part, and a part missing from the project would fail at the first call that reached
it. So each part describes itself as plain data, and Distribution loads only the registrations of
the installed parts: it routes a command to the part that registered it, presents the MCP tools the
installed parts registered, places the files, rules and programs they contribute, composes their
guidance and asks their idle checks. No part imports Distribution either, so registering needs
nothing installed, and the spec part, which depends on nothing, registers like any other. The
registration is Distribution's own contract because Distribution is the one that reads it, as the
worker harness owns the format of the grant it receives.

All parts are built from this one repository and carry its one version number, so a project never
holds two parts of different Concorde versions and an update moves every installed part together.

### Around it

<a id="uses-spec"></a>

**Spec core** is an [optional integration](../glossary.json#concept.optional-integration): it
matters only where the spec part is installed, and then Distribution relies on it for the steps it
adds around the spec part's own commands. It owns `spec-validation` and `registry`, the
[structural checks](../glossary.json#concept.structural-check) and
[registry](../glossary.json#concept.registry) they work on, and the
[Protocol binding](../glossary.json#concept.protocol-binding) that
`protocol-manifest --bind-project` and an update rewrite. Distribution relies on its envelope for
the commands that print it, those [listed above](#the-command-line) as not routed elsewhere, and
never interprets a Spec itself; a Spec core refusal of such a command prints unchanged in that
envelope, which Distribution writes and amends in its own code, meeting the envelope's format
without Spec core's. The installer builds the Protocol copy itself from the tracked manifest, whose
format Spec core defines, refusing a stale build before any write, and calls the spec part only
through the install services its registration names: the docsite template before any write and the
binding of the installed files after the receipt. A refusal of the binding leaves the Specs to
`spec-validation` and the install successful, its result carrying Spec core's
[error](../spec-tooling/spec/errors.md#contract.spec.error). The binding is one of Spec core's file
transactions, whose limits decide what an interrupted binding leaves, as
[When an install fails halfway](#when-an-install-fails-halfway) explains. Without the spec part
there is no Protocol copy, no binding, no initialization and no update mark.

<a id="uses-views"></a>

**Views**, in the spec part too, owns the docsite scaffold; `docsite` only routes
`--propose`/`--apply` to it. The scaffold proposal and every file it writes are Views'
responsibility, and an `--apply` without `--proposal` is refused first. Views also owns the template
inventory, the rule selecting which files of the package's `docsite/` are the template; where the
spec part is installed, the installer ships exactly those files, `scaffold/` included, by calling
that rule, through the spec part's `install.prepare` service, rather than repeating it, and refuses
with `invalid_docsite_template` when the rule rejects the package's template, so a project's
scaffold always finds the template it expects
([one inventory](../spec-tooling/views/requirements.md#req.views.template-inventory),
[the rule](../spec-tooling/views/contracts.md#contract.views.scaffold-proposal)).

<a id="uses-tracing"></a>

**Tracing** defines the [error contract](../kernel/tracing/contracts.md#contract.tracing.error) in
whose shape the installer, `concorde update`, the `concorde` command and the project MCP server
print their own refusals, so a caller forwards them like any other link. Distribution follows that shape without importing the Kernel's code, since it is
installed with any part, the spec part alone included.

<a id="uses-dogfooding"></a>

**Dogfooding** owns the [develop
install](../glossary.json#concept.develop-install): which checkouts may be
installed from in develop mode, and the guidance a develop install adds. Dogfooding is no part, so
the installer reaches it through the entry the package descriptor names under `develop.check`.
With `--develop`, and on every update of a develop install, the installer calls its source check
before writing anything
and refuses with its code and message when the check refuses, then adds its rendered guidance to
the skill and the `CLAUDE.md` block and records the mode and the checked commit in the receipt.

Every other part reaches Distribution only through its registration, and Distribution relies on
nothing of it but what the registration says. It routes `task`, `run`, the execution commands,
`workflow`, `issues` and `trace` to the part that registered each, handing it the rest of the
command line, and that part defines its own output and exit codes; it names no Operation's or
command's meaning and passes no task. It places the workflows the workflow part renders, with the
permission rules their step agents need, refusing stale renders like any other build output; it
places the worker harness part's pi runtime and discovery entry point, and writes neither the
[worker configuration](../glossary.json#concept.worker-configuration) nor the
[model map](../glossary.json#concept.model-map); it asks the execution part's idle check rather
than reading run locks itself; and it lists open tasks after an update only from what the
coordination part reports. A `task merge` runs `concorde spec-validation` in the primary worktree as
its default check where the spec part is installed, which is how an update's mark stops a merge
until the project validates.

### Inside

<a id="realization.distribution.descriptor"></a>

The **package descriptor** `concorde.json` is an input of the build, so a licence or version change
is never shipped with renders made before it.

<a id="realization.distribution.build"></a>

The **build renderer** is a pure function of the source tree followed by a guarded write: includes
must be safe, acyclic and audience-consistent, and an output is written only inside the build-owned
`generated/` locations ([requirements](requirements.md#req.distribution.build-owned-outputs)).
Every prompt under `prompts/` declares in its front matter an audience, `worker`, `ambient` or
`shared` (the Protocol's own chapters under `protocol/` are plain Markdown and count as `shared`),
and includes another with a line `@<path>.md [KEY=value ...]` starting at column one, whose values
fill the included prompt's `{KEY}` placeholders. An include is safe when its target is a Markdown
file at a repository-relative path without a symbolic link, never a Spec document, and a Protocol
prompt includes and is included only by Protocol prompts. A root must be `worker` or `shared` and is
resolved as instructions an agent reads, so it is audience-consistent when every prompt it includes
is `worker` or `shared`; text meant for another audience (`ambient`) is never pulled in. Within one
root a prompt is reached at most once, whatever values its include lines give: a second include line
reaching it, whether in the same prompt or through a diamond of two prompts that both include it,
stops the build with `CONCORDE-PROMPT-DIAMOND-001`, naming both include chains from the root, and
nothing is deduplicated. A text needed twice in one root is therefore kept in two prompts. A
leftover is removed only when its bytes still match the
previous manifest; an edited leftover, a link or an unknown file stops the build first.

The build also renders each **skill**, a prompt root that agents load as an Agent Skill, a second
time as `generated/skills/<name>/SKILL.md`: the root's render under the front matter naming the
skill and describing it ([requirements](requirements.md#req.distribution.skills-rendered)). The
`concorde` skill is the main-session guidance, composed of Coordination's working method and the
guidance each other part contributes: the build renders each part's guidance, and the installer
composes the renders of the installed parts in the order of the parts table without changing them, adding only
Dogfooding's section in a develop install; `concorde-development` is the root Module's guidance for
developing Concorde in its own source checkout, which that checkout loads beside `concorde` and no
installation places. Rendering the front matter in the build rather than in the installer lets the
checkout and every installed project load the very same file.

<a id="realization.distribution.command"></a>

The **command entry points** are thin: they load the registrations of the installed parts, take the
global `--project-root`, load the installed parts' registering code and call the entry the
registering part names for the command with the rest of the command line, and, for the distribution
and Spec tooling commands other than `spec-mcp` and `update`, print the shared envelope the entry
answers and exit with its status, so a command's meaning changes only in its owner.
The commands routed to other owners keep their owners' output unchanged. Two Spec core commands
are the exceptions, where Distribution adds a step of its own to its owner's work:

- `spec-validation`: Spec core still decides every structural finding, but Distribution's entry
  point adds the findings of [an update not yet validated](#updating-an-installed-concorde) to its
  result and removes the update mark `.concorde/update.json` after a result with no other error, as
  the [installer program](#realization.distribution.installer) describes.
- `init --apply`: Spec core's initialization writes only the project's Specs and configuration,
  never `CLAUDE.md`. Once it has succeeded, the entry point brings the glossary import of the
  installed `CLAUDE.md` block up to date, so that the first glossary is imported
  ([requirements](requirements.md#req.distribution.glossary-import)); a project without that block
  is left as it is. When that write fails, the result is `failed` with `guidance_failed`, which
  keeps the initialization's result and has the operating system's error as its cause. The project
  is initialized then, so the developer repairs the cause and runs `concorde update` or the
  installer again, which install the block with the import, and never `init --apply` again, which
  refuses an initialized project.

<a id="realization.distribution.project-mcp"></a>

The **project MCP server host**, `src/concorde/distribution/project_mcp/`, is the
[project MCP server](#the-project-mcp-server) without any tool of its own: `server.py` runs the
stdio session, finds the primary worktree through Git's common directory, decides whether the
session listens to it as a channel and sends channel events from the threads that watch;
`calls.py` runs each call in a fresh process of the current Concorde and watches the waits and the
long work the tools start; `tools.py` is what that process runs, presenting the tools of the
installed parts' registrations, calling the entry each names and becoming the long work a
`long_work` tool hands over. It is a small hand-written JSON-RPC session with no MCP library, since
its wire is the same few messages plus one notification.

<a id="realization.distribution.protocol-copy-writer"></a>

The **Protocol copy writer** builds the copy from the tracked manifest and rendered assets after
checking freshness and each digest
([requirements](requirements.md#req.distribution.no-stale-copy)), so a project receives exactly the
Protocol the manifest names.

<a id="realization.distribution.installer"></a>

The **installer program** resolves the parts to install with their dependencies, reuses the
writer, the build's freshness check and Views' docsite template inventory, places each installed
part's contributions and installs the composed `concorde` skill and main-session block. Everything that can refuse an
install before any program runs — the build's freshness, the docsite template, Dogfooding's develop
source check, the running Concorde, the descriptor's Python requirement, the project's settings,
`uv` on `PATH` and, when the pi runtime is still to be placed, `npm` — and then the pinned download
are decided before the first write, so such a refusal leaves the project as it was.

In update mode the installer takes the choices to keep from the previous receipt and installs as
before. It then rewrites the configuration's Protocol binding itself, since the project would
otherwise be bound to a Protocol copy it no longer carries, and writes the Git-ignored mark
`.concorde/update.json`. The mark holds because Distribution's own `spec-validation` entry point
adds `CONCORDE-UPDATE-001` to Spec core's result while the mark is present, and removes the mark
only on a result that is otherwise a success; a `task merge`, whose default check is that
validation in the primary worktree, therefore stops until the project validates with the new
Concorde ([requirements](requirements.md#req.distribution.update-unvalidated),
[reported](requirements.md#req.distribution.unvalidated-reported),
[cleared](requirements.md#req.distribution.unvalidated-cleared)).

<a id="realization.distribution.tests"></a>

The **Distribution tests**, under `tests/concorde/distribution/`, exercise the build, the Protocol
manifest and the installed command on a fresh project, verifying the
[requirements](requirements.md) and [scenarios](scenarios.md).
