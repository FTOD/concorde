# Distribution

## Purpose

Distribution turns the Concorde checkout into something a developer can run and install: describes
the package, builds the generated files, routes each `concorde` command to its owning Module,
writes the Protocol copy a project carries, and installs Concorde with the main-session guidance, for Claude Code and, on request, for pi.
It does not decide what a command does, what the main agent is told, or a project's Specs and
configuration — the installer never writes Specs.

## Terminology

| Term | Definition |
| --- | --- |
| Package | The set of Concorde files, described by `concorde.json`, that is built, checked and installed as one unit. |
| Build | The deterministic rendering of every registered prompt root under `prompts/` into plain files under `generated/`. |
| Build manifest | The generated record of the digest of every source the build read and of every output it wrote. |
| Command-line interface | The `concorde` command, whose subcommands each print exactly one JSON result envelope and exit with a status derived from it. |
| Protocol copy | The rendered Spec Protocol bundle placed in a project under `.concorde/protocol/`, whose manifest digest the project configuration binds. |
| Distribution command | A `concorde` command Distribution owns itself rather than routing to another Module: `build` and `protocol-manifest`. |
| Installer | The program that places the Protocol copy, the `concorde` command and the main-session guidance into a project without writing its Specs. |
| [Developer](../vocabulary.md#concept.concorde.developer) | |
| [Main agent](../vocabulary.md#concept.concorde.main-agent) | |
| [Protocol binding](../spec-tooling/spec/module.md#concept.spec.protocol-binding) | |
| [Registry](../spec-tooling/spec/module.md#concept.spec.registry) | |
| [Structural check](../spec-tooling/spec/module.md#concept.spec.structural-check) | |
| [Scaffold proposal](../spec-tooling/views/module.md#concept.views.scaffold-proposal) | |
| [Main-session guidance](../coordination/main-session/module.md#concept.main-session.guidance) | |
| [Develop install](../dogfooding/module.md#concept.dogfooding.develop-install) | |
| [Run](../execution/module.md#concept.execution.run) | |
| [Execution command](../execution/commands/module.md#concept.commands.execution-command) | |
| [Run progress file](../execution/module.md#concept.execution.progress-file) | |

## Usage

<a id="concept.distribution.package"></a>

**The package.** `concorde.json` is the package's identity: name, version, licence, the roots the
installer ships, install locations, the supported clients `claude-code` and `pi`, and the pinned third-party
programs under `tools` (today `d2`, by release, URL and per-platform SHA-256). The build reads it
too, so a changed descriptor makes every render stale.

<a id="concept.distribution.build"></a><a id="concept.distribution.build-manifest"></a>

**Building.** `python3 scripts/concorde.py build` expands every prompt root into `generated/`
([requirements](requirements.md#req.distribution.build-reachable)), `{{name}}` becoming the literal
text `{name}` so that a prompt can show a placeholder such as a check's `{python}`, and wraps every
[workflow script](../execution/workflows/module.md#concept.workflows.script) of the workflow catalog for each
client: `generated/workflows/claude/concorde-<name>.js` with its `meta` block and Claude Code step
adapter, `generated/workflows/pi/<name>.js` with the pi step adapter, and the pi command-runner agents
`generated/workflows/pi/agents/concorde-step.md` and `concorde-report.md`, and writes
`generated/build-manifest.json` with every source's and output's digest. Every file directly in
`prompts/workers/`, `prompts/main-session/` and `prompts/dogfooding/` is a prompt root of its own,
rendered to the same path under `generated/`; `build --check` only
reports what is stale, writing nothing
([requirements](requirements.md#req.distribution.build-check-read-only)). `generated/` is
Git-ignored, so a checkout always rebuilds. `protocol-manifest --write --bind-project` accepts a
Protocol change's fresh digests, binds the configuration and refreshes this checkout's own copy.

<a id="concept.distribution.cli"></a>

**The command line.** `scripts/concorde.py` (or the `concorde.sh`/`concorde.ps1` wrappers) takes a
global `--project-root` and one subcommand. In a source checkout that `uv sync` prepared, it runs
itself again on the checkout's own `.venv` interpreter, which holds Concorde's Python
dependencies; an installed copy has no `.venv` and runs on Concorde's own environment:

| Command | Does | Owned by |
| --- | --- | --- |
| `spec-validation [target]` | runs the structural checks | [Spec core](../spec-tooling/spec/module.md) |
| `registry --write` or `--check` | regenerates or checks the registry mirror | [Spec core](../spec-tooling/spec/module.md) |
| `docsite --propose` or `--apply` | proposes or applies the docsite scaffold | [Views](../spec-tooling/views/module.md) |
| `grant --modules <ids> --type <task type> [--root <worktree>]` | prints a task type's grant | [Spec core](../spec-tooling/spec/module.md) |
| `spec-mcp` | runs the stdio MCP server rooted at `CLAUDE_PROJECT_DIR` or the client's root; it prints no envelope | [Spec MCP server](../spec-tooling/spec-mcp/module.md) |
| `init --propose --name <name>` or `--apply --proposal <file>` | proposes or applies a project's first Spec | [Spec core](../spec-tooling/spec/module.md) |
| `task open`, `list`, `show` or `close` | opens, lists, shows or closes tasks; prints the task command's own JSON | [Tasks](../coordination/tasks/module.md) |
| `run <operation>` | runs one Operation in the workspace of the current worktree or, when the Operation allows it, unbound; prints the run result | [Execution](../execution/module.md), with the catalog of [Operations](../execution/operations/module.md) |
| `task-validation`, `delivery` or `scaffold` | runs one execution command in the workspace of the current worktree; prints the run result | [Execution](../execution/module.md), with the catalog of [Commands](../execution/commands/module.md) |
| `workflow step` or `report` | runs one workflow step, or reports a workflow's result; prints its own JSON | [Workflows](../execution/workflows/module.md) |
| `configure-workers` | lists or changes the worker model configuration of the current worktree; prints its own JSON | [Workers](../execution/workers/module.md) |
| `issues list`, `show`, `check`, `report`, `close` or `reopen` | the Issues bookkeeping command `scripts/issues.py`; prints its own JSON | [Issues](../issues/module.md) |
| `build [--check]` | renders or checks the generated files | Distribution |
| `protocol-manifest [--write] [--bind-project]` | reconciles the Protocol manifest | Distribution |

<a id="concept.distribution.distribution-command"></a>

A command is named after the part of Concorde that owns it: `task` gives the coordination
commands, `spec-validation`, `registry`, `docsite`, `grant`, `spec-mcp` and `init` the Spec tooling
commands, `issues` the Issues commands, and `build` and `protocol-manifest` the **distribution
commands**, the only ones Distribution owns itself. Of Execution's, `task-validation`, `delivery`
and `scaffold` are the [execution commands](../execution/commands/module.md#concept.commands.execution-command),
runs without a worker; `run` starts an Operation, `workflow` a workflow step and
`configure-workers` changes the worker configuration.

Every command but `spec-mcp`, `task`, `run`, the execution commands, `workflow`,
`configure-workers` and `issues` prints exactly one JSON envelope and exits with its status, even
when refused ([requirements](requirements.md#req.distribution.one-envelope)); those route to their
owners, which define their own JSON and exit codes.

<a id="concept.distribution.protocol-copy"></a><a id="concept.distribution.installer"></a>

**Installing into a project.** `python3 scripts/install-concorde.py <project>` refuses a stale
build and a project in which Concorde is still running — a [run](../execution/module.md#concept.execution.run)
of an Operation or of an [execution command](../execution/commands/module.md#concept.commands.execution-command)
whose runner process lives, as its [run progress file](../execution/module.md#concept.execution.progress-file)
says, or a pi task-session round whose supervisor lives, each named in the refusal
`concorde_busy` ([requirements](requirements.md#req.distribution.idle-install)), since replacing
the framework copy under them would change their code halfway; the progress file of an
Operation's worker, which lies beside the Operation's and names the same runner, is not a run of
its own — then places the Framework runtime under `.concorde/framework/` (replacing an earlier copy,
and leaving out `scripts/e2e/`, which only [End-to-end testing](../e2e/module.md) uses),
Concorde's own Python environment, a venv at `.concorde/framework/python/` made from the
installer's interpreter or `--python` (Python 3.11 or newer, else nothing more is written),
Concorde's Python dependencies in that environment, such as LangGraph, which `spec_panel` runs
on — exactly the runtime part of the checkout's `uv.lock`, exported with `uv export` to
`.concorde/framework/requirements.txt` and installed with `uv pip install --require-hashes`, and
refused with `uv_missing` when `uv` is not on `PATH` or `python_dependencies_failed` with the
failing command's output when a step fails (`--without-dependencies` skips them, and the
Operations that need them then refuse) — the `concorde` command as `.concorde/bin/concorde`, which
runs Concorde only in that environment, with the caller's `PYTHONPATH`, `PYTHONHOME` and user
site-packages left out, so an activated project venv never becomes Concorde's interpreter,
the Protocol copy under `.concorde/protocol/` and Concorde-owned defaults only where absent, the
[main-session guidance](../coordination/main-session/module.md#concept.main-session.guidance) as the project
skill `.claude/skills/concorde/SKILL.md` and a block between `<!-- concorde:start -->` and
`<!-- concorde:end -->` in the project's `CLAUDE.md` — replaced in place on a later install,
leaving the rest of the file untouched — and the `d2` release `concorde.json` pins, placed at
`.concorde/tools/d2`, checked against its SHA-256 before anything else is written and kept on a
later install with the same pin
([requirements](requirements.md#req.distribution.installer-pinned-d2), `--without-d2` skips it);
plus ignore rules for `.concorde/runs/`, `.concorde/tasks/`, the workspace binding
`.concorde/workspace.json` that each task worktree gets, `.concorde/worker-models.json`,
`.concorde/framework/`, `.concorde/tools/` and `.claude/worktrees/`, where task worktrees go, and a receipt
`.concorde/install.json`. The receipt names the installed dependencies under `dependencies`
(the requirements file, the digest of the `uv.lock` they came from and the number of packages, or
`null` without them), the checkout installed from as `source`, the commit
it was at as `source_commit` (`null` outside a Git checkout) and the `mode`, `normal` or, for a
[develop install](../dogfooding/module.md#concept.dogfooding.develop-install) made with
`--develop`, `develop`. It lists under `files` every file Concorde owns in the project,
including a default an earlier install wrote and this one found in place, and under `amended` the
project's own files it only amends: `.gitignore`, `CLAUDE.md` and, once written, `.claude/settings.json`. It also installs every rendered workflow for Claude Code as
`.claude/workflows/concorde-<name>.js`, which Claude Code offers as the command `/concorde-<name>`,
and adds to the `permissions.allow` of the project's `.claude/settings.json` the rules the workflow
needs to run without a prompt per step: `Workflow(concorde-<name>)` for each workflow and
`Bash(.concorde/bin/concorde workflow step:*)` and `Bash(.concorde/bin/concorde workflow report:*)`
for its step agents. It adds only rules that are missing, records them in the receipt, removes on a
later install the recorded rules it no longer ships, and leaves every other setting untouched. The command runs the Framework copy of the worktree it belongs to; a
task worktree has none of its own, since Git ignores it, unless the task reinstalled Concorde
there, so its command runs the primary worktree's copy, found through Git's common directory.

<a id="concept.distribution.update"></a>

**Updating an installed Concorde.** `concorde update` runs, in update mode, the installer of the
Concorde checkout the receipt names as its `source` (or `--from <checkout>`): it installs as the
first install did, keeping `d2`, the pi main session's files and develop mode when they were
installed (`--pi` adds the pi main session's files to an install that has none), always placing
the pi runtime unless the first install left it out with `--without-pi-runtime` (so an update
adds it to an install made before the runtime was placed by default), keeping Concorde's own
environment's interpreter unless `--python` names another, and refusing like an install while
Concorde runs in the project; binds the new Protocol copy in the
configuration itself, the one write of the project configuration an installer makes; and marks
the project **Concorde unvalidated** by writing `.concorde/update.json`, which Git ignores, with
the versions, installed commits and Protocol bindings before and after; the findings below name
the commits too, since between two commits of a Concorde repository the version seldom changes. While that state is there, `concorde
spec-validation` in the primary worktree reports `CONCORDE-UPDATE-001` as an error, which also stops a
`task merge`; the first validation that passes removes it and says so (`CONCORDE-UPDATE-002`).
Only an update sets the state, so a project that stops validating because of its own changes is
never marked by it. The result lists the open tasks and, when the Protocol copy changed, asks for
the primary branch to be merged into each, since their worktrees keep the previous copy until then.

Workers run on pi unless the worker model configuration chooses Claude Code for them, whatever
program the main session is, so every install places the **pi runtime** — the sandbox engine
`@anthropic-ai/sandbox-runtime` that pi workers run their commands in — under
`.concorde/tools/pi-runtime/` by copying the package's
`src/concorde/distribution/pi_runtime/package.json` and `package-lock.json` there and running
`npm ci --ignore-scripts`, which installs exactly the locked versions after checking each
package's integrity hash ([requirements](requirements.md#req.distribution.installer-locked-pi-runtime)).
A later install with the same lockfile keeps the runtime it placed. Without npm the install
refuses before writing anything else. `--without-pi-runtime` leaves the runtime out, for a
machine where every worker runs on Claude Code; the receipt records that choice (`pi_runtime`)
so that an update keeps it, and a pi worker then fails with `pi_runtime_missing`, naming the
command that installs the runtime.

With `--pi` the installer also prepares the project for a pi main session: it places the
[run view](../coordination/main-session/module.md#concept.main-session.run-view), with its model picker, as
`.pi/extensions/concorde/`; the skill a second time as `.pi/skills/concorde/SKILL.md`; every
rendered pi workflow script under `.concorde/workflows/pi/`; and the command-runner agents
`concorde-step` and `concorde-report` under `.pi/agents/`, where pi-subagents finds the project's
agents. The receipt records the choice (`pi`), which an update keeps. Both skills carry the same frontmatter, whose values are bare names or
double-quoted strings, because pi parses it as strict YAML and drops a skill it cannot parse. pi
loads the project's extension and skill only once the developer trusts the project, which its
interactive start asks for and a headless `pi -p` or RPC run grants with `--approve`.

Every refusal of the installer and of `concorde update` prints `{"error": <link>}` and exits with
status 1: one link of the Framework's [error chain](../vocabulary.md#concept.concorde.error-chain),
whose actor is `Installer (install-concorde)` or `concorde update`, whose code is the refusal's,
whose detail names what is wrong and where, and whose reason is `input` when only a different
project, Concorde checkout or argument corrects it and `environment` otherwise
([requirements](requirements.md#req.distribution.installer-error-links)). The caller can therefore
forward it as the cause of its own link like any other refusal.

It never writes Specs, the registry or the project configuration
([requirements](requirements.md#req.distribution.installer-no-specs)). Afterwards,
`concorde init --propose --name <name>` prints Spec core's initialization proposal, and
`concorde init --apply --proposal <file>` applies exactly the proposal it printed, from a file
outside the project; the developer accepts a new Protocol copy later by updating the binding.

## Design

### Around it

<a id="uses-spec"></a>

**Spec core** owns `spec-validation` and `registry`, the
[structural checks](../spec-tooling/spec/module.md#concept.spec.structural-check) and
[registry](../spec-tooling/spec/module.md#concept.spec.registry) they work on, and the
[Protocol binding](../spec-tooling/spec/module.md#concept.spec.protocol-binding) that
`protocol-manifest --bind-project` rewrites. Distribution relies on its envelope for every command
and never interprets a Spec itself; a Spec core refusal prints unchanged.

<a id="uses-views"></a>

**Views** owns the docsite scaffold; `docsite` only routes `--propose`/`--apply` to it. The
[scaffold proposal](../spec-tooling/views/module.md#concept.views.scaffold-proposal) and every file
it writes are Views' responsibility, and an `--apply` without `--proposal` is refused first.

<a id="uses-main-session"></a>

**Main session** owns the guidance the main agent receives. Distribution renders it as a prompt
root and the installer places the rendered
[main-session guidance](../coordination/main-session/module.md#concept.main-session.guidance) unchanged, and
refuses to install it missing or stale rather than fall back to an old copy.

<a id="uses-dogfooding"></a>

**Dogfooding** owns the [develop
install](../dogfooding/module.md#concept.dogfooding.develop-install): which checkouts may be
installed from in develop mode, and the guidance a develop install adds. With `--develop`, and on
every update of a develop install, the installer calls its source check before writing anything
and refuses with its code and message when the check refuses, then adds its rendered guidance to
the skill and the `CLAUDE.md` block and records the mode and the checked commit in the receipt.

<a id="uses-execution"></a>

**Execution** owns what `run` and the execution commands `task-validation`, `delivery` and
`scaffold` do: the entry point hands each the rest of its command line and the Execution runner
parses it, reads the workspace binding, runs the steps and prints the run result, with its own
exit codes. Distribution names no Operation or command's meaning and passes no task. The
installer also reads the run store's [run progress files](../execution/module.md#concept.execution.progress-file) to refuse while a run
of either kind lives, relying on each naming its kind, its runner's process and its phase.

<a id="uses-commands"></a>

**Commands** lists the [execution commands](../execution/commands/module.md#concept.commands.execution-command)
in its catalog. The entry point routes each name the catalog lists to the Execution runner, so a
new execution command is one more catalog entry and no change here.

The same entry point hands `configure-workers` to [Workers](../execution/workers/module.md), which
owns the worker model configuration and prints the command's own result.

<a id="uses-workflows"></a>

**Workflows** owns each workflow's script, its catalog entry with name and description, the step
adapters and the pi command-runner agent, and the `concorde workflow` command that `workflow` routes
to. Distribution only wraps and places them: the build renders each script for both clients
unchanged in its steps, and the installer places the renders and the permission rules their step
agents need, refusing stale renders like any other build output.

### Inside

<a id="realization.distribution.descriptor"></a>

The **package descriptor** `concorde.json` is an input of the build, so a licence or version change
is never shipped with renders made before it.

<a id="realization.distribution.build"></a>

The **build renderer** is a pure function of the source tree followed by a guarded write: includes
must be safe, acyclic and audience-consistent, and an output is written only inside the build-owned
`generated/` locations ([requirements](requirements.md#req.distribution.build-owned-outputs)). A
leftover is removed only when its bytes still match the previous manifest; an edited leftover, a
link or an unknown file stops the build first.

<a id="realization.distribution.command"></a>

The **command entry points** are thin: they parse the command line, call the owning Module's
function, and wrap the outcome in Spec core's shared envelope, so a command's meaning changes only
in its owner.

<a id="realization.distribution.protocol-copy-writer"></a>

The **Protocol copy writer** builds the copy from the tracked manifest and rendered assets after
checking freshness and each digest
([requirements](requirements.md#req.distribution.no-stale-copy)), so a project receives exactly the
Protocol the manifest names.

<a id="realization.distribution.installer"></a>

The **installer program** reuses the writer and the build's freshness check, and installs the
rendered main-session guidance. Everything that can refuse an install, the build's freshness,
Dogfooding's develop source check, the running Concorde and the pinned downloads, is decided before
the first write, so a refused install leaves the project as it was.

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
[build manifest](#concept.distribution.build-manifest) and
[Protocol copy](#concept.distribution.protocol-copy) are recorded and written but bind no file of
their own.

<a id="realization.distribution.tests"></a>

The **Distribution tests**, under `tests/concorde/distribution/`, exercise the build, the Protocol
manifest and the installed command on a fresh project, verifying the
[requirements](requirements.md) and [scenarios](scenarios.md).
