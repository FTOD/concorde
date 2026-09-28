# Distribution

## Purpose

Distribution turns the Concorde checkout into something a developer can run and install: describes
the [package](../glossary.json#concept.package), builds the generated files, routes each `concorde`
command to its owning [Module](../glossary.json#concept.module), writes the
[Protocol copy](../glossary.json#concept.protocol-copy) a project carries, and installs Concorde
with the [main-session guidance](../glossary.json#concept.main-session-guidance), for Claude Code
and, on request, for pi. It does not decide what a command does, what the
[main agent](../glossary.json#concept.main-agent) is told, or a project's Specs and configuration —
the [installer](../glossary.json#concept.installer) never writes Specs.

## Usage

<a id="concept.package"></a>

**The package.** `concorde.json` is the package's identity: name, version, licence, the roots the
installer ships, install locations, the supported clients `claude-code` and `pi`, and the pinned
third-party programs under `tools` (today `d2`, by release, URL and per-platform SHA-256). The build
reads it too, so a changed descriptor makes every render stale.

<a id="concept.build"></a><a id="concept.build-manifest"></a>

**Building.** `python3 scripts/concorde.py build` expands every prompt root into `generated/`
([requirements](requirements.md#req.distribution.build-reachable)), `{{name}}` becoming the literal
text `{name}` so that a prompt can show a placeholder such as a check's `{python}`, and wraps every
[workflow script](../glossary.json#concept.workflow-script) of the workflow catalog for each client:
`generated/workflows/claude/concorde-<name>.js` with its `meta` block and Claude Code step adapter,
`generated/workflows/pi/<name>.js` with the pi step adapter, and the pi command-runner agents
`generated/workflows/pi/agents/concorde-step.md` and `concorde-report.md`, and writes
`generated/build-manifest.json` with every source's and output's digest. The prompt roots are the
Protocol's `prompts/protocol/principles.md` and `prompts/protocol/kinds/module.md` and every file
directly in `prompts/workers/`, `prompts/main-session/` and `prompts/dogfooding/`, each rendered
to the same path under `generated/`; `build --check` only reports what is stale, writing
nothing ([requirements](requirements.md#req.distribution.build-check-read-only)). `generated/` is
Git-ignored, so a checkout always rebuilds. `protocol-manifest --write --bind-project` accepts a
Protocol change's fresh digests, binds the configuration and refreshes this checkout's own copy.

<a id="concept.command-line-interface"></a>

**The command line.** `scripts/concorde.py` (or the `concorde.sh`/`concorde.ps1` wrappers) takes a
global `--project-root` and one subcommand. In a source checkout that `uv sync` prepared, it runs
itself again on the checkout's own `.venv` interpreter, which holds Concorde's Python
dependencies; an installed copy has no `.venv` and runs on Concorde's own environment:

| Command | Does | Owned by |
| --- | --- | --- |
| `spec-validation [target]` | runs the structural checks | [Spec core](../spec-tooling/spec/module.md) |
| `registry --write` or `--check` | regenerates or checks the registry mirror | [Spec core](../spec-tooling/spec/module.md) |
| `docsite --propose` or `--apply` | proposes or applies the docsite scaffold | [Views](../spec-tooling/views/module.md) |
| `grant --modules <ids> --type <task type> [--root <worktree>]` | prints a [task type](../glossary.json#concept.task-type)'s grant | [Spec core](../spec-tooling/spec/module.md) |
| `spec-mcp` | runs the stdio MCP server rooted at `CLAUDE_PROJECT_DIR` or the client's root; it prints no envelope | [Spec MCP server](../spec-tooling/spec-mcp/module.md) |
| `init --propose --name <name>` or `--apply --proposal <file>` | proposes or applies a project's first [Spec](../glossary.json#concept.spec) | [Spec core](../spec-tooling/spec/module.md) |
| `task open`, `list`, `show` or `close` | opens, lists, shows or closes tasks; prints the task command's own JSON | [Tasks](../coordination/tasks/module.md) |
| `run <operation>` | runs one [Operation](../glossary.json#concept.operation) in the workspace of the current worktree or, when the Operation allows it, unbound; prints the [run result](../glossary.json#concept.run-result) | [Execution](../execution/module.md), with the catalog of [Operations](../execution/operations/module.md) |
| `task-validation`, `delivery` or `scaffold` | runs one execution command in the workspace of the current worktree; prints the run result | [Execution](../execution/module.md), with the catalog of [Commands](../execution/commands/module.md) |
| `workflow step` or `report` | runs one [workflow step](../glossary.json#concept.workflow-step), or reports a workflow's result; prints its own JSON | [Workflows](../execution/workflows/module.md) |
| `configure-workers [--show [--json] \| --check [--json]]` | opens the terminal draft editor by default; read-only options inspect or validate without discovery | [Workers](../execution/workers/module.md) |
| `issues list`, `show`, `check`, `report`, `close` or `reopen` | the Issues bookkeeping command `scripts/issues.py`; prints its own JSON | [Issues](../issues/module.md) |
| `build [--check]` | renders or checks the generated files | Distribution |
| `protocol-manifest [--write] [--bind-project]` | reconciles the Protocol manifest | Distribution |
| `update [--from <checkout>] [--pi]` | updates the installed Concorde, as described below; prints the installer's own JSON | Distribution |

<a id="concept.distribution-command"></a>

A command is named after the part of Concorde that owns it: `task` gives the coordination
commands, `spec-validation`, `registry`, `docsite`, `grant`, `spec-mcp` and `init` the Spec tooling
commands, `issues` the Issues commands, and `build`, `protocol-manifest` and `update` the
**[distribution commands](../glossary.json#concept.distribution-command)**, the only ones
Distribution owns itself. Of Execution's, `task-validation`, `delivery` and `scaffold` are the
[execution commands](../glossary.json#concept.execution-command), runs without a worker; `run`
starts an Operation, `workflow` a workflow step and `configure-workers` changes the worker
configuration.

Every command but `spec-mcp`, `task`, `run`, the execution commands, `workflow`,
`configure-workers`, `issues` and `update` prints exactly one JSON envelope and exits with its
status, even when refused ([requirements](requirements.md#req.distribution.one-envelope)); those
route to their owners, which define their own output and exit codes, except `update`, which prints
the installer's result or its
[error link](requirements.md#req.distribution.installer-error-links). Worker configuration defaults
to a human terminal editor; only its explicit read-only JSON options print a configuration envelope.

The standalone Workers entry point `scripts/available_models.py --backend pi|claude [--json]`
is shipped under `.concorde/framework/scripts/available_models.py` with the runtime. It resolves
its imports relative to itself and works outside a Git worktree; it lists advisory configured
candidates without probing inference API access. Configuration validation does not call it.

<a id="concept.protocol-copy"></a><a id="concept.installer"></a>

**Installing into a project.** `python3 scripts/install-concorde.py <project>` refuses a stale build,
a machine without `uv` on `PATH` (`uv_missing`), since uv owns Concorde's Python, and a project in
which Concorde is still running — a [run](../glossary.json#concept.run) of an
Operation or of an [execution command](../glossary.json#concept.execution-command) whose runner
process lives, as its [run progress file](../glossary.json#concept.run-progress-file) says, or a pi
[task-session](../glossary.json#concept.task-session) round whose supervisor lives, each named in
the refusal `concorde_busy` ([requirements](requirements.md#req.distribution.idle-install),
[naming](requirements.md#req.distribution.busy-named)), since
replacing the framework copy under them would change their code halfway; the
[progress file](../glossary.json#concept.progress-file) of an Operation's worker, which lies beside
the Operation's and names the same runner, is not a run of its own — then places the Framework
runtime under `.concorde/framework/` (replacing an earlier copy, and leaving out `scripts/e2e/`,
which only [End-to-end testing](../e2e/module.md) uses) with the docsite template under
`.concorde/framework/docsite/`, exactly the files [Views](../spec-tooling/views/module.md)' template
inventory selects, `scaffold/` included, from which `concorde docsite --propose` scaffolds a
project's site ([requirements](requirements.md#req.distribution.installer-docsite-template),
[checked first](requirements.md#req.distribution.installer-docsite-template-first)),
Concorde's own Python environment, a venv
at `.concorde/framework/python/` that `uv venv` creates for the Python requirement `concorde.json`
names under `runtime.python`, on an interpreter uv chooses — one of the machine's or a uv-managed
CPython, which uv downloads when none fits — whatever interpreter runs the installer
([requirements](requirements.md#req.distribution.uv-owns-python)), refused with
`python_env_failed` and uv's output when uv cannot create it, Concorde's Python dependencies in that
environment, such as LangGraph, which `spec_panel` runs on — exactly the runtime part of the
checkout's `uv.lock`, exported with `uv export` to `.concorde/framework/requirements.txt` and
installed with `uv pip install --require-hashes`, and refused with `python_dependencies_failed` with
the failing command's output when a step fails (`--without-dependencies` skips them, and the
Operations that need them then refuse) — the
`concorde` command as `.concorde/bin/concorde`, which runs Concorde only in that environment, with
the caller's `PYTHONPATH`, `PYTHONHOME` and user site-packages left out, so an activated project
venv never becomes Concorde's interpreter, the Protocol copy under `.concorde/protocol/` and
Concorde-owned defaults only where absent, the
[main-session guidance](../glossary.json#concept.main-session-guidance) as the project skill
`.claude/skills/concorde/SKILL.md` and a block between `<!-- concorde:start -->` and
`<!-- concorde:end -->` in the project's `CLAUDE.md` — replaced in place on a later install, leaving
the rest of the file untouched, and ending with an `@<path>` import of the project's glossary once
one is declared, which `concorde init --apply` also adds when it creates the first glossary — and
the `d2` release `concorde.json` pins, placed at
`.concorde/tools/d2`, checked against its SHA-256 before anything else is written and kept on a
later install with the same pin
([requirements](requirements.md#req.distribution.installer-pinned-d2),
[checked first](requirements.md#req.distribution.installer-d2-first), `--without-d2` skips it);
plus ignore rules for `.concorde/runs/`, `.concorde/tasks/`, the
[workspace binding](../glossary.json#concept.workspace-binding) `.concorde/workspace.json` that each
task worktree gets, `.concorde/worker-models.json`, `.concorde/framework/`, `.concorde/tools/` and
`.claude/worktrees/`, where task worktrees go, and a receipt `.concorde/install.json`. The receipt
names Concorde's own environment under `python` (its path, the requirement it was created for, the
interpreter uv chose and that interpreter's version), the installed dependencies under
`dependencies` (the requirements file, the digest of the `uv.lock` they came from and the number
of packages, or `null` without them), the checkout installed from as `source`, the commit it was at
as `source_commit` (`null` outside a Git checkout) and the `mode`, `normal` or, for a
[develop install](../glossary.json#concept.develop-install) made with `--develop`, `develop`. It lists under `files` every file Concorde owns in the project, including a
default an earlier install wrote and this one found in place, and under `amended` the project's own
files it only amends: `.gitignore`, `CLAUDE.md` and, once written, `.claude/settings.json`. It also
installs every rendered workflow for Claude Code as `.claude/workflows/concorde-<name>.js`, which
Claude Code offers as the command `/concorde-<name>`, and adds to the `permissions.allow` of the
project's `.claude/settings.json` the rules the workflow needs to run without a prompt per step:
`Workflow(concorde-<name>)` for each workflow and `Bash(.concorde/bin/concorde workflow step:*)` and
`Bash(.concorde/bin/concorde workflow report:*)` for its
[step agents](../glossary.json#concept.step-agent). It adds only rules that are missing, records
them in the receipt, removes on a later install the recorded rules it no longer ships, and leaves
every other setting untouched. The command runs the Framework copy of the worktree it belongs to; a
task worktree has none of its own, since Git ignores it, unless the task reinstalled Concorde there,
so its command runs the primary worktree's copy, found through Git's common directory.

<a id="concept.distribution.update"></a><a id="concept.concorde-unvalidated"></a>

**Updating an installed Concorde.** `concorde update` runs, in update mode, the installer of the
Concorde checkout the receipt names as its `source` (or `--from <checkout>`): it installs as the
first install did, keeping `d2`, the pi main session's files and develop mode when they were
installed (`--pi` adds the pi main session's files to an install that has none), always placing the
pi runtime unless the first install left it out with `--without-pi-runtime` (so an update adds it to
an install made before the runtime was placed by default), creating Concorde's own environment
again with uv for the new checkout's Python requirement, and refusing like an install while
Concorde runs in the project; binds the new Protocol copy in the configuration itself, the one
write of the project configuration an installer makes; and marks the project
**[Concorde unvalidated](../glossary.json#concept.concorde-unvalidated)** by writing
`.concorde/update.json`, which Git ignores, with the versions, installed commits and Protocol
bindings before and after; the validation findings `CONCORDE-UPDATE-001` and `CONCORDE-UPDATE-002`
described next name the commits too, since between two commits of a
[Concorde repository](../glossary.json#concept.concorde-repository) the version seldom changes.
While that state is there, `concorde spec-validation` in the primary worktree reports
`CONCORDE-UPDATE-001` as an error, which also stops a `task merge`; the first validation that passes
removes it and says so (`CONCORDE-UPDATE-002`). Only an update sets the state, so a project that
stops validating because of its own changes is never marked by it. The result lists the open tasks
and, when the Protocol copy changed, asks for the primary branch to be merged into each, since their
worktrees keep the previous copy until then.

<a id="concept.pi-runtime"></a>Workers run on pi unless the
[worker model configuration](../glossary.json#concept.worker-model-configuration) chooses Claude
Code for them, whatever program the main session is, so every install places the
**[pi runtime](../glossary.json#concept.pi-runtime)** — the sandbox engine
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

With `--pi` the installer also prepares the project for a pi main session: it places the
[run view](../glossary.json#concept.run-view), with its
[model picker](../glossary.json#concept.model-picker), as `.pi/extensions/concorde/`; the skill a
second time as `.pi/skills/concorde/SKILL.md`; every rendered pi workflow script under
`.concorde/workflows/pi/`; and the command-runner agents `concorde-step` and `concorde-report` under
`.pi/agents/`, where pi-subagents finds the project's agents. The receipt records the choice (`pi`),
which an update keeps. Both skills carry the same frontmatter, whose values are bare names or
double-quoted strings, because pi parses it as strict YAML and drops a skill it cannot parse. pi
loads the project's extension and skill only once the developer trusts the project, which its
interactive start asks for and a headless `pi -p` or RPC run grants with `--approve`.

Every refusal of the installer and of `concorde update` prints `{"error": <link>}` and exits with
status 1: one link of the Framework's [error chain](../glossary.json#concept.error-chain), in the
shape of its [error contract](../contracts.md#contract.concorde.error),
whose actor is `Installer (install-concorde)` or `concorde update`, whose code is the refusal's,
whose detail names what is wrong and where, and whose reason is `input` when only a different
project, Concorde checkout or argument corrects it and `environment` otherwise
([requirements](requirements.md#req.distribution.installer-error-links)). The caller can therefore
forward it as the cause of its own link like any other refusal.

The installer never writes Specs or the registry, and a plain install never writes the project
configuration; only update mode rewrites the configuration's Protocol binding, as described above
([requirements](requirements.md#req.distribution.installer-no-specs)). Afterwards,
`concorde init --propose --name <name>` prints Spec core's initialization proposal, and
`concorde init --apply --proposal <file>` applies exactly the proposal it printed, from a file
outside the project. After a plain install that brought a new Protocol copy, the developer accepts
it by updating the binding; `concorde update` does that itself.

## Design

### Around it

<a id="uses-spec"></a>

**Spec core** owns `spec-validation` and `registry`, the
[structural checks](../glossary.json#concept.structural-check) and
[registry](../glossary.json#concept.registry) they work on, and the
[Protocol binding](../glossary.json#concept.protocol-binding) that
`protocol-manifest --bind-project` rewrites. Distribution relies on its envelope for every command
and never interprets a Spec itself; a Spec core refusal prints unchanged.

<a id="uses-views"></a>

**Views** owns the docsite scaffold; `docsite` only routes `--propose`/`--apply` to it. The
[scaffold proposal](../glossary.json#concept.scaffold-proposal) and every file
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
refuses to install it missing or stale rather than fall back to an old copy.

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
reads the [run store](../glossary.json#concept.run-store)'s
[run progress files](../glossary.json#concept.run-progress-file) to refuse while a run of either
kind lives, relying on each naming its kind, its runner's process and its phase.

<a id="uses-task-session"></a>

**Task session** owns the pi task session's
[session rounds](../glossary.json#concept.session-round) and the progress file `status.json` its
supervisor keeps for each round under `.concorde/tasks/<task>.session/`. The installer reads those
files to refuse while a round runs, relying on each naming its task, its round, its phase and its
supervisor's process, and never starts, stops or answers a task session.

<a id="uses-commands"></a>

**Commands** lists the [execution commands](../glossary.json#concept.execution-command)
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
`generated/` locations ([requirements](requirements.md#req.distribution.build-owned-outputs)).
Every prompt under `prompts/` declares in its front matter an audience, `worker`, `ambient` or
`shared` (the Protocol's own chapters under `protocol/` are plain Markdown and count as `shared`),
and includes another with a line `@<path>.md [KEY=value ...]` starting at column one, whose values
fill the included prompt's `{KEY}` placeholders. An include is safe when its target is a Markdown
file at a repository-relative path without a symbolic link, never a Spec document, and a Protocol
prompt includes and is included only by Protocol prompts. A root must be `worker` or `shared` and is
resolved as instructions an agent reads, so it is audience-consistent when every prompt it includes
is `worker` or `shared`; text meant for another audience (`ambient`) is never pulled in. Within one
root a prompt is reached at most once. A leftover is removed only when its bytes still match the
previous manifest; an edited leftover, a link or an unknown file stops the build first.

<a id="realization.distribution.command"></a>

The **command entry points** are thin: they parse the command line, call the owning Module's
function, and, for the distribution and Spec tooling commands other than `spec-mcp` and `update`,
wrap the outcome in Spec core's shared envelope, so a command's meaning changes only in its owner.
The commands routed to other owners keep their owners' output unchanged.

<a id="realization.distribution.protocol-copy-writer"></a>

The **Protocol copy writer** builds the copy from the tracked manifest and rendered assets after
checking freshness and each digest
([requirements](requirements.md#req.distribution.no-stale-copy)), so a project receives exactly the
Protocol the manifest names.

<a id="realization.distribution.installer"></a>

The **installer program** reuses the writer, the build's freshness check and Views' docsite
template inventory, and installs the rendered main-session guidance. Everything that can refuse an
install before any program runs — the build's freshness, the docsite template, Dogfooding's develop
source check, the running Concorde, the project's settings, the descriptor's Python requirement,
`uv` on `PATH` and, when the pi runtime is still to be placed, `npm` — and then the pinned download
are decided before the first write, so such a refusal leaves the project as it was. Only the steps
that run those programs, `npm ci`, `uv venv` and the installation of the Python dependencies, can
fail after something was written; an install run again repeats them.

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

<a id="realization.distribution.tests"></a>

The **Distribution tests**, under `tests/concorde/distribution/`, exercise the build, the Protocol
manifest and the installed command on a fresh project, verifying the
[requirements](requirements.md) and [scenarios](scenarios.md).
