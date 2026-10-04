# Distribution requirements

The Module-wide obligations of [Distribution](module.md). The [scenarios](scenarios.md) show them
in concrete situations.

## Build

### req.distribution.build-owned-outputs — The build writes only where it owns

The build SHALL write only in these locations:

- Inside `generated/protocol/`.
- Inside `generated/workers/`.
- Inside `generated/main-session/`.
- Inside `generated/dogfooding/`.
- Inside `generated/development/`.
- Inside `generated/guidance/`.
- Inside `generated/skills/`.
- Inside `generated/workflows/`.
- In `generated/build-manifest.json`.
- In the parts index `generated/parts.json`.

Other locations under `generated/` belong to other producers. The build never judges or removes
those locations. Each new prompt root adds its own owned location in the same change.

### req.distribution.skills-rendered — Every skill is rendered with its front matter

The build SHALL render each skill as `generated/skills/<name>/SKILL.md` with these contents in order:

- Front matter with the skill's `name` and a double-quoted `description`.
- The skill's composition or the render of its prompt root.

The skill `concorde` is composed of every part's skill section.
The skill `concorde-development` comes from `prompts/development/skill.md`.

The installer places the `concorde` skill from its rendered file, so an installed project and Concorde's
own source checkout load the same text.

### req.distribution.build-check-read-only — Checking the build writes nothing

`build --check` SHALL NOT perform any of these actions on any file:

- Write it.
- Create it.
- Remove it.

### req.distribution.build-reachable — Every prompt file is rendered

When a Markdown file under `prompts/` is neither a prompt root nor reached through the includes of
one, the build SHALL fail.

### req.distribution.prompt-includes — A prompt includes another by a line of its own

When a line `@<path>.md [KEY=value ...]` starts at column one of a prompt, the build SHALL expand
it as follows:

- Use the prompt at that repository-relative path.
- Fill each `{KEY}` placeholder of the included prompt with the line's value for it.

Every Markdown file under `prompts/` is a prompt. The Protocol's own chapters under `protocol/` are
prompts too. Together with the prompts under `prompts/protocol/`, those chapters are its Protocol
prompts.

### req.distribution.safe-includes — Only a safe include is expanded

The build SHALL refuse an include when any of these conditions holds:

- Its target is not a Markdown file at a repository-relative path.
- Its target is reached through a symbolic link.
- Its target is a [Spec](../glossary.json#concept.spec) document.
- The include is from a Protocol prompt to another prompt.
- The include is from another prompt to a Protocol prompt.

### req.distribution.include-audience — A root takes in only text meant for its audience

The build SHALL refuse any of these:

- A prompt under `prompts/` whose front matter declares no audience among `worker`, `ambient` and
  `shared`.
- A root whose audience is not `worker` or `shared`.
- A root that reaches through its includes a prompt whose audience is neither `shared` nor the
  root's own.

A root is resolved as instructions an agent reads. For this reason, text meant for another audience,
such as an `ambient` prompt, is never pulled into the root.
The Protocol's own chapters are plain Markdown. They count as `shared`.

### req.distribution.include-once — A prompt is reached at most once within one root

When a root reaches one prompt by a second include line, the build SHALL refuse the root with
`CONCORDE-PROMPT-DIAMOND-001`, naming:

- The prompt.
- Both include chains from the root that reach the prompt.

This applies whatever values the lines give. It applies whether the lines are in the same prompt
or in two prompts that both include the reached prompt.

An include cycle is refused as well. Nothing is deduplicated.
A text needed twice in one root is kept in two prompts.

### req.distribution.no-stale-copy — A stale build is never copied

The [Protocol copy](../glossary.json#concept.protocol-copy) writer SHALL refuse to copy the Protocol
from a package when any of these conditions holds:

- Its [build manifest](../glossary.json#concept.build-manifest) records a source that is missing.
- Its build manifest records a source that is changed.
- Its rendered asset differs from the tracked manifest.

### req.distribution.protocol-manifest-precondition — protocol-manifest acts only on a fresh build and a readable manifest

`protocol-manifest` SHALL write nothing and report `invalid` with `CONCORDE-PROTOCOL-MANIFEST-001`, whatever its flags, when any of these conditions holds:

- The build is stale.
- The tracked Protocol manifest is unreadable.
- The tracked Protocol manifest is not of the [manifest's shape](../spec-tooling/spec/contracts.md#protocol-manifest).
- The tracked Protocol manifest names an asset the build lacks.

What each combination of its flags writes once this holds is
[explained with the command](module.md#reconciling-the-protocol-manifest).

## Command line

### req.distribution.one-envelope — One envelope per command

An invocation of the `concorde` command SHALL print exactly one JSON result envelope on standard output when all these conditions hold:

- It names a command registered with `output` `envelope`, or no command of the package.
- It is not `--help`.
- It is not a command of a part that is not installed.

The [registration](contracts.md#contract.distribution.part-registration) of each command decides.
Today the distribution and Spec tooling commands are registered with `envelope`, except these:

- `spec-mcp`
- `project-mcp`
- `update`

Every other command is registered with `own` and prints what its owner defines. Such commands
include:

- `task`
- `run`
- `workflow`
- `issues`
- `trace`
- the execution commands

The exit status is the one Spec core's shared envelope assigns to the envelope's status. So the
exit status follows from this requirement rather than being a separate one: a caller that only
checks the status and a caller that reads the envelope reach the same conclusion. `update` prints
the installer's result or [error link](#req.distribution.installer-error-links) instead.

## Parts

### req.distribution.parts-installable — Any set of parts installs with its dependencies

The installer SHALL install exactly the [parts](../glossary.json#concept.part) it is asked for
together with every part they depend on, transitively, and no other part.

Distribution itself is installed with any part. Left without a choice, the installer installs every
part.

### req.distribution.unknown-part-refused — A part the package does not build is refused first

When a requested part or a dependency has a name the package does not build, the installer SHALL
refuse that name before writing anything.

The refusal is `unknown_part`. It names the part and the parts the package builds.

### req.distribution.parts-recorded — The receipt names the installed parts

The installer's receipt SHALL name every installed part, each with the version it carries.

### req.distribution.update-installed-parts — An update keeps the installed parts

`concorde update` SHALL install exactly these parts:

- The parts the receipt names.
- Every part the new Concorde makes one of those parts depend on.
- Every part the update is asked to add.

### req.distribution.one-version — Every part carries the package's version

The build SHALL give every part the version `concorde.json` names, so that every installed part of a project carries the same version.

### req.distribution.registration-only — Distribution reaches a part only through its registration

Only through an installed part's [part registration](../glossary.json#concept.part-registration),
Distribution SHALL perform these actions for that part:

- Route commands to it.
- Present its MCP tools.
- Place its files.
- Compose guidance from it.
- Ask its idle state.

It loads no registration of a part that is not installed.

No part imports Distribution's code. Distribution imports a part's code only through the entries
its registration names.

### req.distribution.composed-from-registrations — The command and the server offer only installed parts

Each of these SHALL offer exactly what is listed for it:

- The installed `concorde` command offers the distribution commands and the commands the installed
  parts register.
- The [project MCP server](../glossary.json#concept.project-mcp-server) offers the MCP tools the
  installed parts register whose required parts are all installed.

### req.distribution.absent-part-named — A command of an absent part names the part

When a part of the package registers a command but the project has not installed that part, the
`concorde` command SHALL refuse the command, naming:

- That part.
- How to install it.

The command prints the refusal as `{"error": <link>}` with the code `part_missing`.
The command exits with status 1. The printed refusal is the one refusal by which another part tells that a part
is absent. The project MCP server refuses a tool of such a part with the same link.

### req.distribution.unique-names — No two parts register one name

When two parts register the same command or the same MCP tool name, the build SHALL fail.

### req.distribution.composed-guidance — The guidance is composed of the installed parts

The installed [main-session guidance](../glossary.json#concept.main-session-guidance) SHALL have these contents in order and no section of a part that is not installed:

- Coordination's working method.
- The rendered guidance section of every other installed part, in the order of the parts.

This holds for each of its three compositions:

- The project skill.
- The [task-session](../glossary.json#concept.task-session) prompt.
- The `CLAUDE.md` block.

Without the coordination part, there is no main-session guidance to compose.
For this reason, the installer places the sections of the installed parts as the project skill
and the `CLAUDE.md` block alone. There is no task-session prompt in this case.

## Installation


### req.distribution.guidance-absent-parts — A guidance section stands without the parts it may lack

Each of these sections SHALL say what happens where a part it may be composed without is not installed, wherever it names a command or project MCP tool of that part:

- Every guidance section a part registers.
- Dogfooding's develop section.

A section may be composed without every part that neither its own part depends on nor, for a
task-session section, Coordination does. The develop section may be composed without every part
that the coordination and issues parts do not depend on. A section that names such a command or tool plainly would send the agent to
something the project lacks.

### req.distribution.glossary-import — The CLAUDE.md block imports the glossary

Where the spec part is installed, the installed `CLAUDE.md` block SHALL import as follows:

- When the project's registry declares a glossary, import that glossary.
- When the project's registry declares none, import nothing.

### req.distribution.receipt-complete — The receipt names every owned file

The installer's receipt SHALL list these files:

- Under `files`, every file Concorde owns in the project, whether or not this install wrote it.
- Under `defaults`, those of them that are Concorde-owned defaults, including a default an earlier
  receipt named that is still in place.

No install removes a default its earlier receipt names, since a default holds the project's own
data ([Installing into a project](module.md#installing-into-a-project)).

### req.distribution.receipt-amended — The receipt names every amended project file

The installer's receipt SHALL list under `amended` the project's own files that the installer only amends.

### req.distribution.installer-own-permissions — The installer adds only its own permission rules

The installer SHALL change the project's `.claude/settings.json` only by:

- Adding the missing permission rules its workflows need.
- Removing the rules it recorded in its receipt and no longer ships.

Every other setting, including rules the developer wrote that equal one of Concorde's, stays as
it was.

### req.distribution.installer-settings-checked — Unusable settings are refused first

When a project's `.claude/settings.json` is not a JSON object with an optional `permissions.allow` list, the installer SHALL refuse the project before writing anything.

The refusal is `settings_invalid`.

### req.distribution.installer-project-mcp — The installer registers the project MCP server

The installer SHALL register the [project MCP server](../glossary.json#concept.project-mcp-server)
in the project's `.mcp.json` with these details:

- The server name is `concorde`.
- The server runs as `.concorde/bin/concorde
project-mcp`.

### req.distribution.installer-mcp-kept — The installer keeps the rest of `.mcp.json`

The installer SHALL change the project's `.mcp.json` only in its server `concorde`.

Every other server and setting stays as it was. When a file's `concorde` entry is already the one
above, the installer does not write the file.

### req.distribution.installer-mcp-checked — An unusable `.mcp.json` is refused first

When a project's `.mcp.json` is not a JSON object with an optional `mcpServers` object, the installer SHALL refuse the project before writing anything.

The refusal is `mcp_config_invalid`.

### req.distribution.own-python — Concorde runs in its own Python environment

The installed `concorde` command SHALL run Concorde with these restrictions:

- It uses only the interpreter of its own environment under `.concorde/framework/python/`.
- It ignores the caller's Python path settings.
- It ignores user site-packages.

### req.distribution.idle-install — An install is refused while an installed part reports work running

When an installed part's registered idle check reports work of that part running at the installer's check, the installer SHALL refuse installation before writing anything.

In Concorde, only the execution part's check reports anything. It reports the runner of an
[Operation](../glossary.json#concept.operation) or
[execution command](../glossary.json#concept.execution-command) run that holds its
[run lock](../glossary.json#concept.run-lock). The update runs the installer, so the same holds for
`concorde update`. The installer checks once, before the first write. The installer does not keep
work from starting after the check.

### req.distribution.busy-named — A busy refusal names what runs

The installer's `concorde_busy` refusal SHALL name each piece of work the idle checks reported, in Concorde each run found running.

### req.distribution.installer-error-links — Installer refusals are error links

Every refusal of the installer and of `concorde update` SHALL be printed as one error link of the
Framework's [error contract](../kernel/tracing/contracts.md#contract.tracing.error), naming the refusal's code and what is wrong.

### req.distribution.installer-no-specs — The installer writes no Spec but its installation realization

The installer SHALL NOT create, modify or remove any of these items:

- The registry.
- A registered [Spec](../glossary.json#concept.spec) document except in the Concorde installation
  realization that keeps the installed files bound.
- Any part of the project configuration except, in update mode, its
  [Protocol binding](../glossary.json#concept.protocol-binding).

That realization exists only because Concorde is installed. For that reason, it is the installer's
like the files it binds. Everything else in the project's Specs stays the project's. A plain install
leaves the project configuration as it is. An update changes only the Protocol binding in the project
configuration.

### req.distribution.installer-keeps-installation-bound — Installed files stay bound

Where the spec part is installed in an initialized project, the installer SHALL do the following after it writes the receipt:

- It brings the Concorde installation realization in step with the receipt through Spec core.
- It thereby binds every file the receipt names outside `.concorde/`, other than the amended ones,
  whether the file was installed before or after initialization.

The binding is [Spec core's](../spec-tooling/spec/requirements.md#req.spec.installation-follows-record).
When an installed file exists and no realization binds it by its exact path, the file is added.
When an entry's file no longer exists, the entry is removed. When the project's Specs
cannot be read, the installer binds nothing and does not fail, since everything else was already
written.
`spec-validation` reports why the project's Specs cannot be read. When Spec core refuses the
binding, the installer does not fail either. In that case, the installer's result carries Spec
core's error under `binding_error`.

### req.distribution.update-unvalidated — An update marks the project Concorde unvalidated

When the spec part is installed in a project, `concorde update` SHALL mark the project Concorde unvalidated.

The mark is the file `.concorde/update.json`. The project ignores the file. Only an update writes
it. `concorde spec-validation` clears the mark. For that reason, a project without the spec part,
which has no such validation, is never marked.

### req.distribution.update-mark-kept — An earlier mark is kept until replaced

When an earlier update still marks a project, `concorde update` SHALL write its own mark with these values from the earlier mark:

- The version from before.
- The installed commit from before.
- The Protocol binding from before.

What has not been validated then reaches back to the earlier update. Therefore, a second update
before a validation never hides what has not been validated.

### req.distribution.update-mark-whole — The mark is replaced whole

`concorde update` SHALL replace the update mark whole, so that an earlier mark stays as it was until the update's own mark is written.

When an update fails before its mark, it therefore leaves any earlier update's mark exactly as
before ([a failed write](#req.distribution.failed-write-reported)).

### req.distribution.unvalidated-reported — Validation reports an unvalidated update

While the project is Concorde unvalidated, when `concorde spec-validation` in its primary worktree finds an error, the command SHALL also report `CONCORDE-UPDATE-001` as an error.

When a validation finds no error, it instead produces these results:

- It clears the mark ([below](#req.distribution.unvalidated-cleared)).
- It reports no `CONCORDE-UPDATE-001`.

Nothing merges before the update is validated. This is because, while the mark exists, a `task
merge` runs that validation on the merged result
([Tasks](../coordination/tasks/requirements.md#req.tasks.merge-update-validated)). This holds regardless
of the checks given to that merge.

### req.distribution.unvalidated-cleared — The first clean validation clears the mark

When a Concorde-unvalidated project's `concorde spec-validation` finds no error other than `CONCORDE-UPDATE-001`, the command SHALL remove the mark.

It reports the removal as `CONCORDE-UPDATE-002`.

### req.distribution.installer-fresh-guidance — Only a fresh build is installed

When either condition holds, the installer SHALL refuse the package with `stale_build` before writing anything:

- The package's [build manifest](../glossary.json#concept.build-manifest) records a missing or
  changed source or output.
- The package lacks a render or file the installed parts place.

Freshness is judged by the digests the build manifest records, never by file times. The rendered
[main-session guidance](../glossary.json#concept.main-session-guidance) is one such render, so stale
or missing guidance is never installed.

### req.distribution.installer-locked-pi-runtime — Only the locked pi runtime is installed

The installer SHALL install the pi runtime only with `npm ci --ignore-scripts` from the `package-lock.json` the package ships.

`npm ci` installs exactly the versions the lockfile names. When a package's integrity hash differs,
`npm ci` refuses the package. No install script of a dependency runs on the developer's machine.

### req.distribution.installer-pinned-d2 — Only the pinned d2 is installed

The installer SHALL place a `d2` program only from an archive whose SHA-256 equals the one `concorde.json` pins for the platform.

The docsite renders the Specs' diagrams with it.

### req.distribution.installer-d2-first — The d2 archive is checked before anything is written

When it installs `d2`, the installer SHALL perform these steps before it writes anything else into the project:

- Fetch the pinned archive.
- Check the pinned archive.

A failed or tampered download therefore leaves the project untouched.

### req.distribution.installer-programs-first — Missing programs refuse before anything is written

When either condition holds, the installer SHALL refuse before writing anything into the project:

- `uv` is not on `PATH`.
- All these conditions hold:
  - `npm` is not on `PATH`.
  - The pi runtime is to be installed.
  - The pi runtime is not already in place.

The refusals are `uv_missing` and `npm_missing`. The steps that run those programs can still fail
after the first write. A write itself can also fail
([a failed write](#req.distribution.failed-write-reported)).

### req.distribution.failed-write-reported — A failed write is refused as `install_failed`

When a file operation of the installer or of `concorde update` fails after the first write, that command SHALL refuse with `install_failed`, naming the operating system's error.

Nothing is rolled back: what the earlier steps wrote stays. The receipt is replaced whole after
every other installed file. Therefore, when a failure occurs before the receipt's replacement, the
previous receipt stays. A failure after the replacement happens while one of these steps runs:

- The installer binds the installed files.
- An update rebinds the Protocol.
- An update writes its mark.

Such a failure leaves the new receipt without this update's mark. An earlier mark stays as it was. Running the same command again repeats every
step.

### req.distribution.uv-owns-python — uv creates Concorde's own environment

The installer SHALL create Concorde's own environment under `.concorde/framework/python/` only with `uv venv`, for the Python requirement `concorde.json` names under `runtime.python`.

uv chooses an interpreter that satisfies the requirement. When the machine has none, uv downloads
a uv-managed CPython. Because uv chooses the interpreter, the interpreter that runs the installer
never decides Concorde's.

### req.distribution.locked-python-dependencies — Only the locked Python dependencies are installed

Where an installed part names a Python dependency, the installer SHALL install exactly the runtime part of the package's `uv.lock` with these details:

- The installation is into Concorde's own environment.
- The runtime part is exported with `uv export` to `.concorde/framework/requirements.txt`.
- The runtime part is installed with `uv pip install --require-hashes`.

A package whose hash differs from the lock is therefore never installed. The
[install result](contracts.md#contract.distribution.install-result) names the requirements file and
the lock's digest.

### req.distribution.installer-docsite-template — The installer ships the docsite template

Where the spec part is installed, the installer SHALL place exactly the docsite template files selected by [Views](../spec-tooling/views/module.md)' template inventory from the package, including `scaffold/`, under `.concorde/framework/docsite/`.

A project's `concorde docsite --propose` reads its template there,
so an install without the template could not scaffold a site.

### req.distribution.installer-docsite-template-first — An unsafe docsite template installs nothing

Where both conditions hold, the installer SHALL refuse with `invalid_docsite_template` before it writes anything into the project:

- The spec part is installed.
- Views' template inventory rejects the package's docsite template as missing or unsafe.

## The project MCP server

### req.distribution.mcp-current-code — Every call answers with the current Concorde

The project MCP server SHALL answer every call of a registered tool with a process of the Concorde described below, never with Concorde code the server loaded before that call:

- It is the Concorde that the `concorde` command of the worktree the tool's current registration
  names ([serving](#req.distribution.mcp-current-serving)) runs when the call arrives.

So, while a session runs, a merge or a `concorde update` changes the code that answers the session's
next call in these respects ([Serving a call](module.md#serving-a-call)):

- Its rules.
- Its record formats.
- Its refusals.

The same holds for the waiting and long-running processes a tool starts, such as Coordination's
`concorde task wait` and `concorde task merge`. These processes run the primary worktree's
`concorde`. As Workflows requires, `workflow_step`, registered with `worktree` `session`, runs the
`concorde` of the session's own worktree.

### req.distribution.mcp-current-serving — A call is served as the current code registers its tool

The project MCP server SHALL run every call of a registered tool as the registration of the Concorde that answers the call says, even when the server's last listing of the tools said otherwise:

- The call runs in the worktree the registration names.
- The call runs with or without the hand-over of long work, as the registration says.
- The call runs on or off a thread of the server's own, as the registration says.
- For a tool registered with `worktree` `session`, the call runs the session's own worktree's `concorde`, long work included.

How a tool is served is part of the current code as much as its answer. When an update changes how
a tool is served, that change takes effect at the next call. The session does not need to list its
tools again.

### req.distribution.mcp-tools-changed — The session hears that its tools changed

When the tools of the Concorde that answered a call differ from those the server last listed to its session, the server SHALL tell the session that its tools changed.

A listing the server fetched without giving it to the session does not count as listed.

A part installed or removed by an update thereby adds or removes its tools in a running session,
since the session then lists them again ([listed](#req.distribution.mcp-tools-listed-current)).

### req.distribution.mcp-tools-listed-current — The server lists the current code's tools

When a `tools/list` request from its session arrives, the project MCP server SHALL answer it with the tools of the Concorde that the primary worktree's `concorde` command runs at that arrival.

### req.distribution.mcp-channel-override — The environment may decide the channel

Before and instead of reading the command lines of the processes above it, the project MCP server SHALL judge its session as follows:

- When `CONCORDE_CHANNEL` is `1`, the session is a channel.
- When `CONCORDE_CHANNEL` is `0`, the session is not a channel.

A background task session's server is started with `CONCORDE_CHANNEL=0`. Claude Code never wakes a
background session with channel events, so the waits it registers must name their commands.

### req.distribution.mcp-call-failed — A call without an answer is refused

When a call's process ends without an answer or exceeds its time without an answer, the project MCP server SHALL refuse the call with its own `call_failed` link, which names these:

- The command.
- The end of what the process printed.

What the process printed is the end of each of its two streams, standard output and standard error.
This includes the streams of a process stopped at its time limit.
