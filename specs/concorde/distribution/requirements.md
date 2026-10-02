# Distribution requirements

The Module-wide obligations of [Distribution](module.md). The [scenarios](scenarios.md) show them
in concrete situations.

## Build

### req.distribution.build-owned-outputs — The build writes only where it owns

The build SHALL write only inside `generated/protocol/`, `generated/workers/`, `generated/main-session/`, `generated/dogfooding/`, `generated/development/`, `generated/skills/` and `generated/workflows/` and to `generated/build-manifest.json`.

Other locations under `generated/` belong to other producers, and the build never judges or removes
them. Each new prompt root adds its own owned location in the same change.

### req.distribution.skills-rendered — Every skill is rendered with its front matter

The build SHALL render each skill, `concorde` from `prompts/main-session/skill.md` and `concorde-development` from `prompts/development/skill.md`, as `generated/skills/<name>/SKILL.md`: front matter with the skill's `name` and a double-quoted `description`, followed by the render of its prompt root.

The installer places the `concorde` skill from that file, so an installed project and Concorde's
own source checkout load the same text.

### req.distribution.build-check-read-only — Checking the build writes nothing

`build --check` SHALL NOT write, create or remove any file.

### req.distribution.build-reachable — Every prompt file is rendered

The build SHALL fail when a Markdown file under `prompts/` is neither a prompt root nor reached
through the includes of one.

### req.distribution.no-stale-copy — A stale build is never copied

The [Protocol copy](../glossary.json#concept.protocol-copy) writer SHALL refuse to copy the Protocol
from a package whose [build manifest](../glossary.json#concept.build-manifest) records a source that
is missing or changed, or whose rendered asset differs from the tracked manifest.

## Command line

### req.distribution.one-envelope — One envelope per command

Every invocation of the `concorde` command other than `spec-mcp`, `project-mcp`, `task`, `run`, `task-validation`, `delivery`, `scaffold`, `workflow`, `issues`, `trace` and `update` SHALL print exactly one JSON result envelope on standard output, except `--help`.

The exit status is the one Spec core's shared envelope assigns to the envelope's status, so it
follows from this requirement rather than being a separate one: a caller that only checks the status
and a caller that reads the envelope reach the same conclusion. `update` prints the installer's
result or [error link](#req.distribution.installer-error-links) instead, and the other commands
excepted print what their owners define.

## Installation

### req.distribution.glossary-import — The CLAUDE.md block imports the glossary

The installed `CLAUDE.md` block SHALL import the glossary the project's registry declares, and nothing when none is declared.

### req.distribution.receipt-complete — The receipt names every owned file

The installer's receipt SHALL list under `files` every file Concorde owns in the project, whether or not this install wrote it.

### req.distribution.receipt-amended — The receipt names every amended project file

The installer's receipt SHALL list under `amended` the project's own files that the installer only amends.

### req.distribution.installer-own-permissions — The installer adds only its own permission rules

The installer SHALL change the project's `.claude/settings.json` only by adding the missing permission rules its workflows need and removing the rules it recorded in its receipt and no longer ships.

Every other setting, including rules the developer wrote that equal one of Concorde's, stays as
it was.

### req.distribution.installer-settings-checked — Unusable settings are refused first

The installer SHALL refuse, before writing anything, a project whose `.claude/settings.json` is not a JSON object with an optional `permissions.allow` list.

The refusal is `settings_invalid`.

### req.distribution.installer-project-mcp — The installer registers the project MCP server

The installer SHALL register the [project MCP server](../glossary.json#concept.project-mcp-server)
in the project's `.mcp.json` as the server `concorde`, run as `.concorde/bin/concorde
project-mcp`.

### req.distribution.installer-mcp-kept — The installer keeps the rest of `.mcp.json`

The installer SHALL change the project's `.mcp.json` only in its server `concorde`.

Every other server and setting stays as it was, and a file whose `concorde` entry is already the
one above is not written.

### req.distribution.installer-mcp-checked — An unusable `.mcp.json` is refused first

The installer SHALL refuse, before writing anything, a project whose `.mcp.json` is not a JSON object with an optional `mcpServers` object.

The refusal is `mcp_config_invalid`.

### req.distribution.own-python — Concorde runs in its own Python environment

The installed `concorde` command SHALL run Concorde only with the interpreter of its own environment under `.concorde/framework/python/`, ignoring the caller's Python path settings and user site-packages.

### req.distribution.idle-install — An install is refused while a run holds its run lock

The installer SHALL refuse, before writing anything, to install into a project in which the runner
of an [Operation](../glossary.json#concept.operation) or
[execution command](../glossary.json#concept.execution-command) run holds its
[run lock](../glossary.json#concept.run-lock) when the installer checks.

The update runs the installer, so the same holds for `concorde update`. The check is made once,
before the first write; the installer does not keep a run from starting after it.

### req.distribution.busy-named — A busy refusal names what runs

The installer's `concorde_busy` refusal SHALL name each run it found running.

### req.distribution.installer-error-links — Installer refusals are error links

Every refusal of the installer and of `concorde update` SHALL be printed as one error link of the
Framework's [error contract](../tracing/contracts.md#contract.tracing.error), naming the refusal's code and
what is wrong.

### req.distribution.installer-no-specs — The installer writes no Spec but its installation realization

The installer SHALL NOT create, modify or remove the registry, a registered
[Spec](../glossary.json#concept.spec) document except in the Concorde installation realization that
keeps the installed files bound, or any part of the project configuration except, in update mode,
its [Protocol binding](../glossary.json#concept.protocol-binding).

That realization exists only because Concorde is installed, so it is the installer's like the files
it binds; everything else in the project's Specs stays the project's. A plain install leaves the
project configuration as it is, and an update changes in it only the Protocol binding.

### req.distribution.installer-keeps-installation-bound — Installed files stay bound

In an initialized project, the installer SHALL, after writing the receipt, bring the Concorde
installation realization in step with the receipt through Spec core, so that every file the
receipt names outside `.concorde/`, other than the amended ones, is bound whether it was installed
before or after initialization.

The binding is [Spec core's](../spec-tooling/spec/requirements.md#req.spec.installation-follows-record):
an installed file that exists and that no realization binds by its exact path is added, and an entry
whose file no longer exists is removed. When the project's Specs cannot be read, the installer binds
nothing and does not fail, since everything else was already written; `spec-validation` reports why.
When Spec core refuses the binding, the installer does not fail either, and its result carries Spec
core's error under `binding_error`.

### req.distribution.update-unvalidated — An update marks the project Concorde unvalidated

`concorde update` SHALL mark the project Concorde unvalidated.

The mark is the file `.concorde/update.json`, which the project ignores; only an update writes it.

### req.distribution.update-mark-kept — An earlier mark is kept until replaced

`concorde update` of a project still marked by an earlier update SHALL write its own mark with the earlier mark's version, installed commit and Protocol binding from before, and leave the earlier mark as it was until then.

What has not been validated then reaches back to the earlier update, so a second update before a
validation never hides it.

### req.distribution.unvalidated-reported — Validation reports an unvalidated update

While the project is Concorde unvalidated, a `concorde spec-validation` in its primary worktree that finds an error SHALL also report `CONCORDE-UPDATE-001` as an error.

A validation that finds no error instead clears the mark ([below](#req.distribution.unvalidated-cleared))
and reports no `CONCORDE-UPDATE-001`. Nothing merges before the update is validated, since a `task
merge` runs that validation on the merged result while the mark exists, whatever checks it is given
([Tasks](../coordination/tasks/requirements.md#req.tasks.merge-update-validated)).

### req.distribution.unvalidated-cleared — The first clean validation clears the mark

A `concorde spec-validation` of a Concorde-unvalidated project that finds no error other than `CONCORDE-UPDATE-001` SHALL remove the mark.

It reports the removal as `CONCORDE-UPDATE-002`.

### req.distribution.installer-fresh-guidance — Only current guidance is installed

The installer SHALL refuse to install
[main-session guidance](../glossary.json#concept.main-session-guidance) whose rendered output is
missing or older than its sources.

### req.distribution.installer-locked-pi-runtime — Only the locked pi runtime is installed

The installer SHALL install the pi runtime only with `npm ci --ignore-scripts` from the `package-lock.json` the package ships.

`npm ci` installs exactly the versions the lockfile names and refuses a package whose integrity
hash differs, and no install script of a dependency runs on the developer's machine.

### req.distribution.installer-pinned-d2 — Only the pinned d2 is installed

The installer SHALL place a `d2` program only from an archive whose SHA-256 equals the one `concorde.json` pins for the platform.

The docsite renders the Specs' diagrams with it.

### req.distribution.installer-d2-first — The d2 archive is checked before anything is written

When it installs `d2`, the installer SHALL fetch and check the pinned archive before it writes anything else into the project.

A failed or tampered download therefore leaves the project untouched.

### req.distribution.installer-programs-first — Missing programs refuse before anything is written

The installer SHALL refuse, before writing anything into the project, when `uv` is not on `PATH`, or when `npm` is not on `PATH` and the pi runtime is to be installed and not already in place.

The refusals are `uv_missing` and `npm_missing`. The steps that run those programs can still fail
after the first write, as can a write itself ([a failed write](#req.distribution.failed-write-reported)).

### req.distribution.failed-write-reported — A failed write is refused as `install_failed`

When a file operation of the installer or of `concorde update` fails after the first write, it SHALL refuse with `install_failed`, naming the operating system's error.

Nothing is rolled back: what the earlier steps wrote stays. The receipt is replaced whole after
every other installed file, so a failure before it leaves the previous receipt, and a failure
after it, while the installed files are bound or an update rebinds the Protocol and writes its
mark, leaves the new receipt without this update's mark, an earlier mark staying as it was. Running the same command again repeats
every step.

### req.distribution.uv-owns-python — uv creates Concorde's own environment

The installer SHALL create Concorde's own environment under `.concorde/framework/python/` only with `uv venv`, for the Python requirement `concorde.json` names under `runtime.python`.

uv chooses an interpreter that satisfies the requirement, downloading a uv-managed CPython when the
machine has none, so the interpreter that runs the installer never decides Concorde's.

### req.distribution.installer-docsite-template — The installer ships the docsite template

The installer SHALL place under `.concorde/framework/docsite/` exactly the docsite template files that [Views](../spec-tooling/views/module.md)' template inventory selects from the package, including `scaffold/`.

A project's `concorde docsite --propose` reads its template there, so an install without it could
not scaffold a site.

### req.distribution.installer-docsite-template-first — An unsafe docsite template installs nothing

When Views' template inventory rejects the package's docsite template as missing or unsafe, the installer SHALL refuse with `invalid_docsite_template` before it writes anything into the project.
