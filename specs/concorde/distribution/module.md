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
| Installer | The program that places the Protocol copy, the `concorde` command and the main-session guidance into a project without writing its Specs. |
| [Developer](../vocabulary.md#concept.concorde.developer) | |
| [Main agent](../vocabulary.md#concept.concorde.main-agent) | |
| [Protocol binding](../spec-tooling/spec/module.md#concept.spec.protocol-binding) | |
| [Registry](../spec-tooling/spec/module.md#concept.spec.registry) | |
| [Structural check](../spec-tooling/spec/module.md#concept.spec.structural-check) | |
| [Scaffold proposal](../spec-tooling/views/module.md#concept.views.scaffold-proposal) | |
| [Main-session guidance](../main-session/module.md#concept.main-session.guidance) | |

## Usage

<a id="concept.distribution.package"></a>

**The package.** `concorde.json` is the package's identity: name, version, licence, the roots the
installer ships, install locations, the supported clients `claude-code` and `pi`, and the pinned third-party
programs under `tools` (today `d2`, by release, URL and per-platform SHA-256). The build reads it
too, so a changed descriptor makes every render stale.

<a id="concept.distribution.build"></a><a id="concept.distribution.build-manifest"></a>

**Building.** `python3 scripts/concorde.py build` expands every prompt root into `generated/`
([requirements](requirements.md#req.distribution.build-reachable)) and writes
`generated/build-manifest.json` with every source's and output's digest; `build --check` only
reports what is stale, writing nothing
([requirements](requirements.md#req.distribution.build-check-read-only)). `generated/` is
Git-ignored, so a checkout always rebuilds. `protocol-manifest --write --bind-project` accepts a
Protocol change's fresh digests, binds the configuration and refreshes this checkout's own copy.

<a id="concept.distribution.cli"></a>

**The command line.** `scripts/concorde.py` (or the `concorde.sh`/`concorde.ps1` wrappers) takes a
global `--project-root` and one subcommand:

| Command | Does | Owned by |
| --- | --- | --- |
| `validate [target]` | runs the structural checks | [Spec core](../spec-tooling/spec/module.md) |
| `registry --write` or `--check` | regenerates or checks the registry mirror | [Spec core](../spec-tooling/spec/module.md) |
| `docsite --propose` or `--apply` | proposes or applies the docsite scaffold | [Views](../spec-tooling/views/module.md) |
| `grant --modules <ids> --type <task type> [--root <worktree>]` | prints a task type's grant | [Spec core](../spec-tooling/spec/module.md) |
| `spec-mcp` | runs the stdio MCP server rooted at `CLAUDE_PROJECT_DIR` or the client's root; it prints no envelope | [Spec MCP server](../spec-tooling/spec-mcp/module.md) |
| `init --propose --name <name>` or `--apply --proposal <file>` | proposes or applies a project's first Spec | [Spec core](../spec-tooling/spec/module.md) |
| `task open`, `list`, `show` or `close` | opens, lists, shows or closes tasks; prints the task command's own JSON | [Tasks](../tasks/module.md) |
| `run <operation> [--task <task>]` | runs one Operation, for a task or, when the Operation allows it, for none; prints the Operation result | [Operations](../operations/module.md) |
| `issues list`, `show`, `check`, `report`, `close` or `reopen` | the Issues bookkeeping command `scripts/issues.py`; prints its own JSON | [Issues](../issues/module.md) |
| `build [--check]` | renders or checks the generated files | Distribution |
| `protocol-manifest [--write] [--bind-project]` | reconciles the Protocol manifest | Distribution |

Every command but `spec-mcp`, `task`, `run` and `issues` prints exactly one JSON envelope and exits
with its status, even when refused
([requirements](requirements.md#req.distribution.one-envelope)); those four route to their owners,
which define their own JSON and exit codes.

<a id="concept.distribution.protocol-copy"></a><a id="concept.distribution.installer"></a>

**Installing into a project.** `python3 scripts/install-concorde.py <project>` refuses a stale
build, then places the Framework runtime under `.concorde/framework/` (replacing an earlier copy;
it needs only the Python standard library), the `concorde` command as `.concorde/bin/concorde`,
the Protocol copy under `.concorde/protocol/` and Concorde-owned defaults only where absent, the
[main-session guidance](../main-session/module.md#concept.main-session.guidance) as the project
skill `.claude/skills/concorde/SKILL.md` and a block between `<!-- concorde:start -->` and
`<!-- concorde:end -->` in the project's `CLAUDE.md` — replaced in place on a later install,
leaving the rest of the file untouched — and the `d2` release `concorde.json` pins, placed at
`.concorde/tools/d2`, checked against its SHA-256 before anything else is written and kept on a
later install with the same pin
([requirements](requirements.md#req.distribution.installer-pinned-d2), `--without-d2` skips it);
plus ignore rules for `.concorde/runs/`, `.concorde/tasks/`, `.concorde/worker-models.json`,
`.concorde/framework/`, `.concorde/tools/` and `.claude/worktrees/`, where task worktrees go, and a receipt
`.concorde/install.json`. The command runs the Framework copy of the worktree it belongs to; a
task worktree has none of its own, since Git ignores it, unless the task reinstalled Concorde
there, so its command runs the primary worktree's copy, found through Git's common directory.

With `--pi` the installer also prepares the project for a pi main session and pi workers: it
places the pi runtime — the sandbox engine `@anthropic-ai/sandbox-runtime` that pi workers run
their commands in — under `.concorde/tools/pi-runtime/` by copying the package's
`src/concorde/distribution/pi_runtime/package.json` and `package-lock.json` there and running
`npm ci --ignore-scripts`, which installs exactly the locked versions after checking each
package's integrity hash ([requirements](requirements.md#req.distribution.installer-locked-pi-runtime));
the [run view](../main-session/module.md#concept.main-session.run-view), with its model picker, as
`.pi/extensions/concorde/`; and the skill a second time as `.pi/skills/concorde/SKILL.md`. A later
install with the same lockfile keeps the runtime it placed. Without npm it refuses before writing
anything else.

It never writes Specs, the registry or the project configuration
([requirements](requirements.md#req.distribution.installer-no-specs)). Afterwards,
`concorde init --propose --name <name>` prints Spec core's initialization proposal, and
`concorde init --apply --proposal <file>` applies exactly the proposal it printed, from a file
outside the project; the developer accepts a new Protocol copy later by updating the binding.

## Design

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
rendered main-session guidance.

How this Module is built:

```d2
distribution: Distribution {
  descriptor: Package descriptor {
    "concorde.json"
  }
  build: Build renderer {
    "build.py"
    "prompt_resolver.py"
  }
  command: Command entry points {
    "__main__.py"
    "cli.py"
    "concorde.py"
    "concorde.sh"
    "concorde.ps1"
  }
  writer: Protocol copy writer {
    "project_defaults.py"
  }
  installer: Installer program {
    "install-concorde.py"
    "install.py"
    "tools.py"
    "pi_runtime/"
  }
  build -> descriptor: reads
  command -> build: runs
  installer -> writer: places through
}
```

Python sources are under `src/concorde/distribution/` except `src/concorde/__main__.py` and the
`scripts/` entry points. The [build manifest](#concept.distribution.build-manifest) and
[Protocol copy](#concept.distribution.protocol-copy) are recorded and written but bind no file of
their own.

<a id="realization.distribution.tests"></a>

The **Distribution tests**, under `tests/concorde/distribution/`, exercise the build, the Protocol
manifest and the installed command on a fresh project, verifying the
[requirements](requirements.md) and [scenarios](scenarios.md).

## Relationships

```d2
distribution: Distribution
tooling: Spec tooling {
  spec: Spec core
  views: Views
}
mainsession: Main session
distribution -> tooling.spec
distribution -> tooling.views
distribution -> mainsession
```

<a id="uses-spec"></a>

**Spec core** owns `validate` and `registry`, the
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
[main-session guidance](../main-session/module.md#concept.main-session.guidance) unchanged, and
refuses to install it missing or stale rather than fall back to an old copy.
