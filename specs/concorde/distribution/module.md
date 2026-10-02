# Distribution

## Purpose

Distribution turns the Concorde checkout into something a developer can run and install: describes
the package, builds the generated files, routes each `concorde`
command to its owning [Module](../glossary.json#concept.module), writes the
[Protocol copy](../glossary.json#concept.protocol-copy) a project carries, and installs Concorde
with the [main-session guidance](../glossary.json#concept.main-session-guidance) for Claude Code,
on which the [main agent](../glossary.json#concept.main-agent) and its
[task sessions](../glossary.json#concept.task-session) run for now,
and with the runtime its workers need on pi. It does not decide what a command does, what the main
agent is told, or a project's Specs and configuration — the installer writes no Spec but the
realization that keeps its own installed files bound.

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

### Commands named by their owner

A command is named after the part of Concorde that owns it: `task` gives the coordination
commands and `project-mcp` the Main session's server, `spec-validation`, `registry`, `docsite`, `grant`, `spec-mcp` and `init` the Spec tooling
commands, `issues` the Issues commands, `trace` the Tracing commands, and `build`, `protocol-manifest` and `update` the
**distribution commands**, the only ones
Distribution owns itself. Of Execution's, `task-validation`, `delivery` and `scaffold` are the
[execution commands](../glossary.json#concept.execution-command), runs without a worker; `run`
starts an Operation and `workflow` a workflow step.

## Overview

### From checkout to project

Distribution works in two stages. The build renders the checkout's prompts, Protocol and workflow
scripts into `generated/` and records the build manifest; the installer, run for a first install or
by `concorde update`, refuses a stale build and places Concorde's own files, its environment and
command, and the guidance and workflows in the project.

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
  writer: Protocol copy writer
  installer: Installer program
  build -> descriptor: reads
  command -> build: runs
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
installer ships, install locations, the client `claude-code` the build renders workflows for, and
the pinned third-party programs under `tools` (today `d2`, by release, URL and
per-platform SHA-256). The build reads it too, so a changed descriptor makes every render stale.

### Building

`python3 scripts/concorde.py build` expands every prompt root into `generated/`
([requirements](requirements.md#req.distribution.build-reachable)), `{{name}}` becoming the literal
text `{name}` so that a prompt can show a placeholder such as a check's `{python}`, and wraps every
[workflow script](../glossary.json#concept.workflow-script) of the workflow catalog as
`generated/workflows/claude/concorde-<name>.js` with its `meta` block and Claude Code step adapter,
and writes `generated/build-manifest.json` with every source's and output's digest. The prompt
roots are the Protocol's `prompts/protocol/principles.md` and `prompts/protocol/kinds/module.md`
and every file directly in `prompts/workers/`, `prompts/main-session/`, `prompts/dogfooding/` and
`prompts/development/`, each rendered to the same path under `generated/`; the two
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

| Command | Does | Owned by |
| --- | --- | --- |
| `spec-validation [target]` | runs the structural checks; Distribution adds the findings of [an update not yet validated](#updating-an-installed-concorde) and removes its mark | [Spec core](../spec-tooling/spec/module.md), with Distribution's update findings |
| `registry --write` or `--check` | regenerates or checks the registry mirror | [Spec core](../spec-tooling/spec/module.md) |
| `docsite --propose` or `--apply` | proposes or applies the docsite scaffold | [Views](../spec-tooling/views/module.md) |
| `grant --modules <ids> --type <task type> [--root <worktree>]` | prints a [task type](../glossary.json#concept.task-type)'s grant | [Spec core](../spec-tooling/spec/module.md) |
| `spec-mcp` | runs the stdio MCP server rooted at `CLAUDE_PROJECT_DIR` or the client's root; it prints no envelope | [Spec MCP server](../spec-tooling/spec-mcp/module.md) |
| `project-mcp [--name <name>]` | runs the stdio [project MCP server](../glossary.json#concept.project-mcp-server) of the primary worktree; it prints no envelope | [Main session](../coordination/main-session/module.md) |
| `init --propose --name <name>` or `--apply --proposal <file>` | proposes or applies a project's first [Spec](../glossary.json#concept.spec); after an apply Distribution adds the glossary import to the `CLAUDE.md` block | [Spec core](../spec-tooling/spec/module.md), with Distribution's glossary import |
| `task open`, `list`, `show`, `close`, `merge`, `escalate` or `wait` | opens, lists, shows, closes, merges or escalates tasks, or waits for a task, run or lock; prints the task command's own JSON | [Tasks](../coordination/tasks/module.md) |
| `run <operation>` | runs one [Operation](../glossary.json#concept.operation) in the workspace of the current worktree or, when the Operation allows it, unbound; prints the [run result](../glossary.json#concept.run-result) | [Execution](../execution/module.md), with the catalog of [Operations](../execution/operations/module.md) |
| `task-validation`, `delivery` or `scaffold` | runs one execution command in the workspace of the current worktree; prints the run result | [Execution](../execution/module.md), with the catalog of [Commands](../execution/commands/module.md) |
| `workflow step` or `report` | runs one [workflow step](../glossary.json#concept.workflow-step), or reports a workflow's result; prints its own JSON | [Workflows](../execution/workflows/module.md) |
| `issues list`, `show`, `check`, `report`, `close` or `reopen` | the Issues bookkeeping command `scripts/issues.py`; prints its own JSON | [Issues](../issues/module.md) |
| `trace show`, `list` or `prune` | shows a [trace](../glossary.json#concept.trace) with its timing and cost rolled up, lists traces, or removes what retention allows; prints its own JSON | [Tracing](../tracing/module.md) |
| `build [--check]` | renders or checks the generated files | Distribution |
| `protocol-manifest [--write] [--bind-project]` | [reconciles the Protocol manifest](#reconciling-the-protocol-manifest) | Distribution |
| `update [--from <checkout>]` | updates the installed Concorde, as described below; prints its [update result](contracts.md#contract.distribution.update-result) | Distribution |

Every command but `spec-mcp`, `project-mcp`, `task`, `run`, the execution commands, `workflow`, `issues`, `trace`
and `update` prints exactly one JSON envelope and exits with its
status, even when refused ([requirements](requirements.md#req.distribution.one-envelope)); those
route to their owners, which define their own output and exit codes, except `update`, which prints
its [update result](contracts.md#contract.distribution.update-result) or its
[error link](requirements.md#req.distribution.installer-error-links).

The standalone Workers entry point `scripts/available_models.py --backend pi|claude [--json]`
is shipped under `.concorde/framework/scripts/available_models.py` with the runtime. It resolves
its imports relative to itself and works outside a Git worktree; it lists advisory configured
candidates, with the project model names the user's [model
map](../glossary.json#concept.model-map) gives each, without probing inference API access.
Configuration validation does not call it. The installer writes neither the worker configuration
nor the model map, which belongs to the user and lies outside every project.

The command runs the Framework copy of the worktree it belongs to; a task worktree has none of its
own, since Git ignores it, unless the task reinstalled Concorde there, so its command runs the
primary worktree's copy, found through Git's common directory.

### Installing into a project

The developer runs `python3 scripts/install-concorde.py <project>`
from a built Concorde checkout. The installer first decides everything that could refuse the
install and only then writes, so a refusal among these checks leaves the project as it was. On a
project where every check passes, it goes through these steps in order:

1. **It checks, writing nothing.** It refuses a directory that is not a project
   (`invalid_project`); a stale build (`stale_build`), which includes a stale render of the
   [main-session guidance](../glossary.json#concept.main-session-guidance); a docsite template
   that [Views](../spec-tooling/views/module.md)' inventory rule rejects
   (`invalid_docsite_template`,
   [checked first](requirements.md#req.distribution.installer-docsite-template-first)); a missing
   render of the guidance (`stale_build`,
   [requirements](requirements.md#req.distribution.installer-fresh-guidance)); with
   `--develop`, a source that Dogfooding's check refuses; a project in which a run's runner holds
   its run lock (`concorde_busy`, described below); a `concorde.json` that names no Python requirement
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
3. **It places Concorde's files.** It writes the Protocol copy under `.concorde/protocol/` and
   Concorde-owned defaults only where absent, and places the Framework runtime under
   `.concorde/framework/`, replacing an earlier copy and leaving out `scripts/e2e/`, which only
   [End-to-end testing](../e2e/module.md) uses. With it goes the docsite template under
   `.concorde/framework/docsite/`, exactly the files Views' template inventory selects,
   `scaffold/` included, from which `concorde docsite --propose` scaffolds a project's site
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
5. **It writes the command.** `.concorde/bin/concorde` runs Concorde only in that environment,
   with the caller's `PYTHONPATH`, `PYTHONHOME` and user site-packages left out, so an activated
   project venv never becomes Concorde's interpreter
   ([requirements](requirements.md#req.distribution.own-python)).
6. **It installs the guidance.** The main-session guidance becomes the project skill
   `.claude/skills/concorde/SKILL.md`, the build's rendered skill as it is, and a block between
   `<!-- concorde:start -->` and `<!-- concorde:end -->` in the project's `CLAUDE.md`, replaced in
   place on a later install, leaving the rest of the file untouched, and ending with an `@<path>`
   import of the project's glossary once one is declared
   ([requirements](requirements.md#req.distribution.glossary-import)). Distribution's `init` entry
   point also adds that import after an `init --apply` that created the first glossary, as
   [the command entry points](#realization.distribution.command) describe. The guidance is for Claude
   Code alone, since the main agent and its task sessions run on Claude Code for now; nothing is
   placed for a pi session, and a project's own `AGENTS.md` is left as it is.
7. **It installs the workflows.** Every rendered workflow for Claude Code becomes
   `.claude/workflows/concorde-<name>.js`, which Claude Code offers as the command
   `/concorde-<name>`, and the `permissions.allow` of the project's `.claude/settings.json` gains
   the rules the workflow needs to run without a prompt per step: `Workflow(concorde-<name>)` for
   each workflow and, for its [step agents](../glossary.json#concept.step-agent),
   `mcp__concorde__workflow_step`, the project MCP server's tool through which they start every
   step, and `Bash(.concorde/bin/concorde workflow report:*)`. It adds only rules that are missing,
   records them in the receipt, removes on a later install the recorded rules it no longer ships,
   and leaves every other setting untouched
   ([requirements](requirements.md#req.distribution.installer-own-permissions)). It registers the
   [project MCP server](../glossary.json#concept.project-mcp-server) in the project's `.mcp.json`
   as `"concorde": {"command": ".concorde/bin/concorde", "args": ["project-mcp"]}`, which Claude
   Code starts from the directory a session starts in, the project root, keeping every other
   server, and leaves the file as it is when that entry is already there
   ([requirements](requirements.md#req.distribution.installer-project-mcp),
   [the rest kept](requirements.md#req.distribution.installer-mcp-kept)).
8. **It records the install.** It adds ignore rules for the folders [Tracing](../tracing/module.md)
   keeps, `.concorde/tasks/`, `.concorde/history/`, `.concorde/unbound/` and `.concorde/locks/`,
   for `.concorde/runs/`, where Dogfooding keeps [defect reports](../glossary.json#concept.defect-report) and End-to-end testing its session
   logs,
   the [workspace binding](../glossary.json#concept.workspace-binding) `.concorde/workspace.json`
   that each task worktree gets, `.concorde/framework/`, `.concorde/tools/` and
   `.claude/worktrees/`, where task worktrees go, and writes the receipt `.concorde/install.json`.
9. **It keeps the installed files bound.** In an initialized project it asks Spec core to bring the
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
checkout) and the `mode`, `normal` or, for a
[develop install](../glossary.json#concept.develop-install) made with `--develop`, `develop`. It
lists under `files` every file Concorde owns in the project, including a default an earlier
install wrote and this one found in place
([requirements](requirements.md#req.distribution.receipt-complete)), and under `amended` the
project's own files it only amends: `.gitignore`, `CLAUDE.md`, `.mcp.json` and, once written,
`.claude/settings.json` ([requirements](requirements.md#req.distribution.receipt-amended)).

A project in which a run is still running when the installer checks is refused with
`concorde_busy`, since replacing the framework copy under that run would change its code halfway
([requirements](requirements.md#req.distribution.idle-install)). What counts is a
[run](../glossary.json#concept.run) of an Operation or of an
[execution command](../glossary.json#concept.execution-command) whose runner holds its
[run lock](../glossary.json#concept.run-lock) at that moment, found through its
[run progress file](../glossary.json#concept.run-progress-file) wherever the
[run store](../glossary.json#concept.run-store) keeps it, in the lobby too while a bound run waits
for its workspace's lock; the refusal names each
([requirements](requirements.md#req.distribution.busy-named)). The
[progress file](../glossary.json#concept.progress-file) of an Operation's worker, which lies beside
the Operation's and names the same runner, is not a run of its own.

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
Code for them, although the main agent runs on Claude Code, so every install places the
**pi runtime** — the sandbox engine
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
--update` does the same from the checkout. An update goes through three steps:

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

Open tasks are a separate matter. The
[update result](contracts.md#contract.distribution.update-result) lists them and, when the Protocol
copy changed, asks
for the primary branch to be merged into each, since their worktrees keep the previous copy until
then; validation does not wait for that merge.

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
shape of its [error contract](../tracing/contracts.md#contract.tracing.error),
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
([requirements](requirements.md#req.distribution.installer-no-specs)). Afterwards,
`concorde init --propose --name <name>` prints Spec core's initialization proposal, and
`concorde init --apply --proposal <file>` applies a proposal read from a file outside the project
only when Spec core accepts its shape, its integrity (the proposal digest matches the value) and its
freshness (the project is still in the state it was computed from), which shows the proposal intact
and current, not that propose printed it
([Spec core](../spec-tooling/spec/requirements.md#req.spec.init-explicit-envelope)). After a plain install that brought a new Protocol copy, the developer accepts
it by updating the binding; `concorde update` does that itself.

## How it is built

### Around it

<a id="uses-spec"></a>

**Spec core** owns `spec-validation` and `registry`, the
[structural checks](../glossary.json#concept.structural-check) and
[registry](../glossary.json#concept.registry) they work on, and the
[Protocol binding](../glossary.json#concept.protocol-binding) that
`protocol-manifest --bind-project` rewrites. Distribution relies on its envelope for the commands that print it, those
[listed above](#the-command-line) as not routed elsewhere, and never interprets a Spec itself; a
Spec core refusal of such a command prints unchanged in that envelope. The installer calls Spec
core only to read the Protocol copy and to bind the installed files: the first refuses as a stale
build before any write, and a Spec core refusal of the second leaves the Specs to `spec-validation`
and the install successful, its result carrying Spec core's
[error](../spec-tooling/spec/errors.md#contract.spec.error). The binding is one
[file transaction](../glossary.json#concept.file-transaction), whose limits decide what an
interrupted binding leaves, as [When an install fails halfway](#when-an-install-fails-halfway)
explains.

<a id="uses-views"></a>

**Views** owns the docsite scaffold; `docsite` only routes `--propose`/`--apply` to it. The
scaffold proposal and every file
it writes are Views' responsibility, and an `--apply` without `--proposal` is refused first. Views
also owns the template inventory, the rule selecting which files of the package's `docsite/` are
the template; the installer ships exactly those files, `scaffold/` included, by calling that rule
rather than repeating it, and refuses with `invalid_docsite_template` when the rule rejects the
package's template, so a project's scaffold always finds the template it expects
([one inventory](../spec-tooling/views/requirements.md#req.views.template-inventory),
[the rule](../spec-tooling/views/contracts.md#contract.views.scaffold-proposal)).

<a id="uses-main-session"></a>

**Main session** owns the guidance the main agent receives. Distribution renders it as a prompt
root and the installer places the rendered
[main-session guidance](../glossary.json#concept.main-session-guidance) unchanged, and
refuses to install it missing or stale rather than fall back to an old copy. Main session also owns
the [project MCP server](../glossary.json#concept.project-mcp-server): `project-mcp` only starts it,
and the installer registers it in the project's `.mcp.json`, as step 7 of
[the install](#installing-into-a-project) says, so that Claude Code starts one process of it for
each session from the project root; Distribution answers none of its calls.

<a id="uses-dogfooding"></a>

**Dogfooding** owns the [develop
install](../glossary.json#concept.develop-install): which checkouts may be
installed from in develop mode, and the guidance a develop install adds. With `--develop`, and on
every update of a develop install, the installer calls its source check before writing anything
and refuses with its code and message when the check refuses, then adds its rendered guidance to
the skill and the `CLAUDE.md` block and records the mode and the checked commit in the receipt.

<a id="uses-execution"></a>

**Execution** owns what `run` and the execution commands `task-validation`, `delivery` and
`scaffold` do: the entry point hands each the rest of its command line and the Execution runner
parses it, reads the workspace binding, runs the steps and prints the run result, with its own exit
codes. Distribution names no Operation or command's meaning and passes no task. The installer also
reads the [run locks](../glossary.json#concept.run-lock) under `.concorde/locks/runs/` to refuse
when a run of either kind holds one at its check; it asks nothing of Execution to keep a run from
starting after that.

<a id="uses-tracing"></a>

**Tracing** owns `trace`: the entry point hands it the rest of the command line, and Tracing's
trace command prints its own output. The installer takes from Tracing's
[layout](../tracing/contracts.md#layout) the folders it has Git ignore and the run locks it reads,
relying on a runner holding its run lock for as long as it runs.

<a id="uses-commands"></a>

**Commands** lists the [execution commands](../glossary.json#concept.execution-command)
in its catalog. The entry point routes each name the catalog lists to the Execution runner, so a
new execution command is one more catalog entry and no change here.

<a id="uses-workflows"></a>

**Workflows** owns each workflow's script, its catalog entry with name and description, the step
adapter, and the `concorde workflow` command that `workflow` routes to. Distribution only wraps and
places them: the build renders each script for Claude Code unchanged in its steps, and the installer places the Claude Code renders and the permission rules
their step agents need, refusing stale renders like any other build output.

<a id="uses-tasks"></a>

**Tasks** owns `task`: the entry point hands it the rest of the command line, and the task command
prints its own JSON and sets its own exit status. `concorde update` reads the
[task records](../glossary.json#concept.task-record) under `.concorde/tasks/`, in the shape of their
[contract](../coordination/tasks/contracts.md#contract.tasks.record), to
list each [task](../glossary.json#concept.task) that has not ended, by its identity, branch and
worktree, skipping a record it cannot read, and asks for the primary branch to be merged into each
when the Protocol copy changed; it writes no task record. A `task merge` runs `concorde
spec-validation` in the primary worktree as its default check, which is how an update's mark stops
a merge until the project validates.

<a id="uses-issues"></a>

**Issues** owns `issues`: the entry point runs Issues' bookkeeping command `scripts/issues.py` with
the rest of the command line, and its output, such as the
[receipt](../issues/interface.md#contract.issues.receipt) of a report, and its exit status reach the
caller unchanged. Distribution itself neither reads nor writes an
[Issue](../glossary.json#concept.issue).

<a id="uses-spec-mcp"></a>

**Spec MCP server** owns `spec-mcp`: the entry point starts its server, which answers from
[one root](../spec-tooling/spec-mcp/requirements.md#req.spec-mcp.one-root) and speaks
[only on standard input and output](../spec-tooling/spec-mcp/requirements.md#req.spec-mcp.stdio-only),
so the entry point prints no envelope; Distribution resolves no root and answers no query itself.

<a id="uses-workers"></a>

**Workers** owns how a worker runs on its [backend](../glossary.json#concept.worker-backend), the
[worker configuration](../glossary.json#concept.worker-configuration) and the
[model map](../glossary.json#concept.model-map). Distribution ships what Workers needs from an
install: the pi runtime, the sandbox engine in which
[pi commands run](../execution/workers/pi.md#req.workers.pi-sandbox), whose absence Workers
refuses with `pi_runtime_missing`, and Workers' discovery entry point
`scripts/available_models.py` with the Framework runtime. It writes neither the configuration nor
the map, and its busy check leaves out a worker's [progress
file](../glossary.json#concept.progress-file), which is not a run of its own.

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
`concorde` skill is the main-session guidance, which the installer places as it is, adding only
Dogfooding's section in a develop install; `concorde-development` is the root Module's guidance for
developing Concorde in its own source checkout, which that checkout loads beside `concorde` and no
installation places. Rendering the front matter in the build rather than in the installer lets the
checkout and every installed project load the very same file.

<a id="realization.distribution.command"></a>

The **command entry points** are thin: they parse the command line, call the owning Module's
function, and, for the distribution and Spec tooling commands other than `spec-mcp` and `update`,
wrap the outcome in Spec core's shared envelope, so a command's meaning changes only in its owner.
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

<a id="realization.distribution.protocol-copy-writer"></a>

The **Protocol copy writer** builds the copy from the tracked manifest and rendered assets after
checking freshness and each digest
([requirements](requirements.md#req.distribution.no-stale-copy)), so a project receives exactly the
Protocol the manifest names.

<a id="realization.distribution.installer"></a>

The **installer program** reuses the writer, the build's freshness check and Views' docsite
template inventory, and installs the rendered `concorde` skill and main-session block. Everything that can refuse an
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
