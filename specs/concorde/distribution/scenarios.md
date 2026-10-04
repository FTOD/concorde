# Distribution scenarios

Concrete situations that show the [requirements](requirements.md) at work.

## Build

### scenario.distribution.build-renders — Render the prompt roots and record them

- GIVEN a checkout whose prompt roots include other prompt files through include lines
- WHEN the developer runs `build`
- THEN each root is written to its path under `generated/` with every include expanded
- AND a `{{name}}` in a prompt is written as the literal `{name}`
- AND other braces stay as they are
- AND `generated/build-manifest.json` records the digest of every source and output
- AND a following `build --check` reports no differences

### scenario.distribution.build-skills — Render every skill with its front matter

- GIVEN a checkout whose parts register their guidance sections
- AND those sections include Coordination's skill section `prompts/main-session/skill.md`
- AND the checkout has the prompt root `prompts/development/skill.md`
- WHEN the developer runs `build`
- THEN `generated/skills/concorde/SKILL.md` and `generated/skills/concorde-development/SKILL.md` each start with front matter naming the skill and describing it in a double-quoted string
- AND the `concorde` skill continues with the render of Coordination's skill section followed by the render of every other part's skill section
- AND those renders follow the order of the parts table
- AND each render is byte for byte
- AND one blank line separates the renders
- AND the development skill continues with the render of its prompt root, byte for byte
- AND `generated/guidance/task-session.md` is the [task-session](../glossary.json#concept.task-session) sections of every part composed the same way
- AND the [build manifest](../glossary.json#concept.build-manifest) records them

### scenario.distribution.composed-guidance — Compose the guidance of a set of parts

- GIVEN the registrations of the coordination part
- AND the registrations of the spec part
- AND the registrations of the distribution part
- AND no registrations of other parts
- WHEN Distribution composes their guidance
- THEN the skill is Coordination's skill section followed by the spec part's and then Distribution's
- AND the task-session prompt is Coordination's followed by the spec part's
- AND the `CLAUDE.md` block is Coordination's section followed by the spec part's and Distribution's
- AND none holds a section of a part not given, such as the issues part's

### scenario.distribution.composed-guidance-without-coordination — Compose the guidance without the coordination part

- GIVEN the registrations of the spec and distribution parts alone
- WHEN Distribution composes their guidance
- THEN the skill is their sections alone under a description that does not present the session as the main agent
- AND the `CLAUDE.md` block is their sections alone
- AND there is no task-session prompt

### scenario.distribution.guidance-absent-parts — Every guidance section names the parts it may lack

- GIVEN every guidance section the package's parts register and Dogfooding's develop section
- WHEN a paragraph of one names a `concorde` command or a project MCP tool of a part that the section may be composed without, or a tool that requires such a part
- THEN that paragraph names that part as a part, as in "where the execution part is installed", saying what happens without it

This illustrates [a guidance section standing without the parts it may lack](requirements.md#req.distribution.guidance-absent-parts).

### scenario.distribution.build-workflows — Render every workflow for Claude Code

- GIVEN a workflow catalog whose only workflow is the [brownfield workflow](../glossary.json#concept.brownfield-workflow)
- WHEN the developer runs `build`
- THEN `generated/workflows/claude/concorde-brownfield.js` starts with a `meta` block naming `concorde-brownfield`
- AND the Claude Code step adapter follows that block
- AND the procedure follows the adapter
- AND `generated/workflows/claude/concorde-brownfield.js` is the only workflow render under `generated/workflows/`
- AND the [build manifest](../glossary.json#concept.build-manifest) records it

### scenario.distribution.build-check-stale — Report a stale build without writing

- GIVEN a checkout whose prompt source changed since the last build
- WHEN the developer runs `build --check`
- THEN the result is `invalid` and names every stale or missing output
- BUT no file under `generated/` changes

### scenario.distribution.build-refuses-unsafe — Refuse an unsafe prompt tree

- GIVEN a prompt file that no root includes, an include cycle, an include of a [Spec](../glossary.json#concept.spec) document or an owned output replaced by a link
- WHEN the developer runs `build`
- THEN the result is `invalid` with a finding naming the problem
- BUT no output is written or removed

### scenario.distribution.build-refuses-repeated-include — Refuse a prompt reached twice

- GIVEN a prompt root that includes two prompts, each of which includes the same third prompt with its own values
- WHEN the developer runs `build`
- THEN the build is refused, naming the third prompt and both include chains from the root that reach it
- BUT no output is written or removed

This illustrates [a prompt reached at most once within one root](requirements.md#req.distribution.include-once).

### scenario.distribution.build-removes-own-leftover — Remove an output the build no longer produces

- GIVEN an output the previous build wrote and whose prompt root was removed since
- WHEN the developer runs `build`
- THEN the leftover output is removed because its bytes match the previous manifest

### scenario.distribution.build-keeps-edited-leftover — Keep a leftover output edited by hand

- GIVEN an output the previous build wrote
- AND its prompt root was removed since that build
- AND its bytes were edited after that build
- WHEN the developer runs `build`
- THEN the build stops with an error naming the edited output
- BUT the edited output is kept as it is

### scenario.distribution.build-refuses-name-conflict — Refuse a name two parts register

- GIVEN a checkout in which two parts' [registrations](../glossary.json#concept.part-registration) register the same command
- WHEN the developer runs `build`
- THEN the build stops with an error naming the command and both parts
- AND nothing is resolved by the order of the parts

## Protocol manifest and copy

### scenario.distribution.protocol-manifest-bind — Accept a changed Protocol into this checkout

- GIVEN a Protocol chapter that changed and a fresh build
- WHEN the developer runs `protocol-manifest --write --bind-project`
- THEN the tracked manifest is rewritten with the new digests
- AND the configuration is bound to it
- AND `.concorde/protocol/` is refreshed

### scenario.distribution.protocol-manifest-report — Report a changed Protocol

- GIVEN a Protocol chapter that changed and a fresh build
- WHEN the developer runs `protocol-manifest` without flags
- THEN the result is `invalid` and names the assets whose digests differ

### scenario.distribution.protocol-manifest-single-flag — Write or bind alone

- GIVEN a Protocol chapter that changed and a fresh build
- WHEN the developer runs `protocol-manifest --bind-project`
- THEN the result is `failed` with `protocol_mismatch`
- AND the configuration is bound to the tracked manifest
- AND `.concorde/protocol/` is left as it was
- AND when the developer then runs `protocol-manifest --write`, the tracked manifest is rewritten with the new digests
- AND when the developer then runs `protocol-manifest --write`, the result of that command names the changed assets
- AND when the developer then runs `protocol-manifest --write`, the configuration's binding is unchanged

### scenario.distribution.protocol-manifest-refused — Write nothing without a fresh build and a readable manifest

- GIVEN a package whose Protocol source changed after its last build, or whose tracked Protocol manifest is not of the manifest's shape
- WHEN the developer runs `protocol-manifest --write --bind-project`
- THEN the result is `invalid` with `CONCORDE-PROTOCOL-MANIFEST-001` naming the problem
- BUT nothing is written
- AND the tracked manifest remains unchanged
- AND the configuration's binding remains unchanged
- AND `.concorde/protocol/` remains unchanged

This illustrates [the precondition of `protocol-manifest`](requirements.md#req.distribution.protocol-manifest-precondition).

### scenario.distribution.stale-copy-refused — Refuse to copy from a stale build

- GIVEN a package whose Protocol source changed after its last build
- WHEN the [Protocol copy](../glossary.json#concept.protocol-copy) is written into a project
- THEN the copy is refused as a stale build
- BUT the project's existing Protocol copy is unchanged

## Command line

### scenario.distribution.refused-command-line — A refused command line still answers with one envelope

- GIVEN a command line naming an unknown command, or giving a command that prints an envelope, such as `spec-validation` or `grant`, an unknown option, or leaving out one of its required arguments
- WHEN the developer runs `concorde` with it
- THEN exactly one `failed` result envelope is printed
- AND the exit status is nonzero

### scenario.distribution.composed-from-installed-parts — The command offers the installed parts

- GIVEN a project whose receipt names the parts installed, and one whose receipt names none
- WHEN the developer asks `concorde --help` for its commands, or the [project MCP server](../glossary.json#concept.project-mcp-server) lists its tools
- THEN the first offers exactly the distribution commands and the commands of the parts its receipt names
- AND the first offers exactly the tools those parts register whose required parts are installed
- AND the second offers the commands of every part of the package

### scenario.distribution.part-missing — A command or tool of a part not installed names the part

- GIVEN a project installed without the issues and execution parts
- WHEN the developer runs `concorde issues list` or `concorde run spec_review`, or a session calls the project MCP server's `issue_list`, `run_result` or `register_wait` for a run
- THEN each is refused with `{"error": <link>}` whose code is `part_missing`, naming the part the command or tool belongs to, or the part it needs, and how to install it
- AND the command exits with status 1
- AND the server lists neither the issues part's tools nor the coordination part's `run_result` and `task_resolve`, which need the execution and issues parts

## Installation

### scenario.distribution.install — Install Concorde into a project

- GIVEN a Git project that is not initialized, so that it has no Specs
- AND a fresh Concorde package is available
- WHEN the developer runs the installer on the project
- THEN the project has the Protocol copy under `.concorde/protocol/`
- AND the project has the `concorde` command
- AND the project has the [main-session guidance](../glossary.json#concept.main-session-guidance) as a project skill and a `CLAUDE.md` block
- AND the `d2` release pinned in `concorde.json` for this platform is at `.concorde/tools/d2`
- AND Git ignores that `d2` release
- AND the receipt names that `d2` release
- AND `.gitignore` ignores `.claude/worktrees/`, where task worktrees go
- AND `.gitignore` ignores `.concorde/workspace.json`, the task worktrees' [workspace binding](../glossary.json#concept.workspace-binding)
- AND every rendered Claude Code workflow is at `.claude/workflows/concorde-<name>.js`
- AND `.claude/settings.json` allows `Workflow(concorde-brownfield)`
- AND `.claude/settings.json` allows `mcp__concorde__workflow_step`
- AND `.claude/settings.json` allows `Bash(.concorde/bin/concorde workflow report:*)`
- AND `.claude/settings.json` keeps every setting it had
- AND the receipt records the added rules
- AND the installer prints the receipt as its [install result](contracts.md#contract.distribution.install-result)
- AND the installer exits with status 0
- AND the receipt records the package as `source`
- AND the receipt records mode `normal`
- AND for a package outside a Git checkout, the receipt records `source_commit` `null`
- AND nothing is placed under `.pi/`
- AND no `AGENTS.md` is created
- AND a project's own `AGENTS.md` is left as it is
- AND the project's own `AGENTS.md` is not listed under `amended`
- BUT no Spec document is created
- AND no registry is created
- AND no project configuration with its [Protocol binding](../glossary.json#concept.protocol-binding) is created
- AND only initialization creates these

### scenario.distribution.install-parts — Install a set of parts with their dependencies

- GIVEN a built Concorde package and a project
- WHEN the developer runs the installer with `--parts coordination`
- THEN the receipt names the coordination part under `parts` with the package's version
- AND the receipt names the kernel part under `parts` with the package's version
- AND the receipt names the distribution part under `parts` with the package's version
- AND the Framework copy holds the code of exactly those parts
- AND the Framework copy holds the guidance of no other part
- AND the Framework copy holds the ignore rules of no other part
- AND the Framework copy holds the programs of no other part
- AND the Framework copy holds the workflows of no other part
- AND for a command of a part left out, the installed `concorde` refuses with `part_missing`

### scenario.distribution.install-unknown-part — A part the package does not build installs nothing

- GIVEN a built Concorde package and a project
- WHEN the developer runs the installer with `--parts` naming a part the package does not build
- THEN the installer refuses with `unknown_part`, naming the part and the package's parts
- AND nothing is written into the project

This illustrates [refusing a part the package does not build](requirements.md#req.distribution.unknown-part-refused).

### scenario.distribution.update-installed-parts — An update keeps the installed parts and adds those asked for

- GIVEN a project in which only the spec part is installed
- WHEN the developer runs `concorde update`
- THEN the update installs the spec and distribution parts again and no other
- AND `concorde update --parts issues` then installs the issues part and the kernel it depends on beside them

### scenario.distribution.update-adds-programs — An update places what an added part needs

- GIVEN a project in which only the coordination part is installed, so that, needing neither, it has no `d2` and no Python dependencies
- WHEN the developer runs `concorde update --parts method`, which adds the method part and the spec part it depends on
- THEN the update places the pinned `d2` and the Python dependencies they need

### scenario.distribution.update-without-spec — An update without the spec part waits for no validation

- GIVEN a project in which the coordination part is installed without the spec part
- WHEN the developer runs `concorde update`
- THEN the update result carries `update` `null`
- AND no `.concorde/update.json` is written
- AND the update result's `next` asks only for the updated files to be committed

### scenario.distribution.install-repeat — Installing again repeats no download

- GIVEN a project in which Concorde was installed with the pinned `d2` and the locked pi runtime
- WHEN the developer runs the installer again with the same package
- THEN the `d2` release is not downloaded again
- AND `npm` does not run again
- AND the runtime placed first stays in place
- AND `CLAUDE.md` still holds exactly one Concorde block

### scenario.distribution.install-docsite-template — An installed Concorde can scaffold a docsite

- GIVEN a fresh Concorde package whose `docsite/` holds the template beside files the template inventory leaves out
- WHEN the developer installs it into a project
- AND the developer initializes the project's Specs
- AND the developer runs `concorde docsite --propose`
- THEN `.concorde/framework/docsite/` holds exactly the template files [Views](../spec-tooling/views/module.md)' inventory selects, `scaffold/` included
- AND the proposal succeeds
- AND the proposal lists the template files
- AND the proposal lists a new `docsite/site.json`
- AND with `--github-pages`, the proposal lists the deployment workflow

### scenario.distribution.install-docsite-template-refused — An unsafe docsite template installs nothing

- GIVEN a Concorde package whose `docsite/` template contains a symbolic link
- WHEN the developer installs it into a project
- THEN the install is refused with `invalid_docsite_template`
- AND the refusal names the link
- AND the link's reason is `input`
- BUT nothing is written into the project

### scenario.distribution.glossary-import — The CLAUDE.md block imports the project's glossary

- GIVEN a project in which Concorde is installed
- WHEN `concorde init --apply` creates the project's first glossary, or an install or update finds one declared
- THEN the Concorde block of `CLAUDE.md` imports that glossary with `@<path>`, once, so Claude Code loads every term at launch
- AND the rest of `CLAUDE.md` is kept

### scenario.distribution.glossary-import-failed — A glossary import that cannot be written after init

- GIVEN a project in which Concorde is installed
- AND the project's `CLAUDE.md` cannot be written
- WHEN `concorde init --apply` creates the project's first glossary
- THEN the result is `failed` with `guidance_failed`
- AND the result keeps the initialization's result
- AND the result names the operating system's error
- AND the project is initialized
- AND once `CLAUDE.md` can be written, `concorde update` adds the glossary import to the Concorde block

### scenario.distribution.glossary-import-none — The CLAUDE.md block imports nothing before a glossary

- GIVEN a project whose `CLAUDE.md` has content of its own
- AND the project declares no glossary yet
- WHEN the developer installs Concorde
- THEN the Concorde block of `CLAUDE.md` imports no glossary
- AND the rest of `CLAUDE.md` is kept

### scenario.distribution.install-defaults-kept — A Concorde-owned default stays the project's data

- GIVEN a project installed with the issues part
- AND its receipt names `.concorde/issues/.gitignore` under `files` and `defaults`
- AND the developer edited that file
- WHEN Concorde is installed again without the issues part
- AND Concorde is then installed from a Concorde that no longer declares that default
- THEN the file stays as the developer left it each time
- AND each receipt still names the file under `files` and `defaults`

### scenario.distribution.install-settings-kept — A developer's settings survive the installer

- GIVEN a project whose `.claude/settings.json` has its own permission rules
- AND a receipt records a rule the new package no longer ships
- WHEN the installer runs again
- THEN the developer's rules and other settings are unchanged
- AND the missing workflow rules are added
- AND the rule no longer shipped is removed

### scenario.distribution.install-settings-invalid — Unusable settings refuse the install

- GIVEN a project whose `.claude/settings.json` is not a JSON object
- WHEN the installer runs
- THEN the install is refused with `settings_invalid`
- BUT nothing is written, not even a workflow the project lacks

### scenario.distribution.mcp-reroute — A call is served as the current code registers its tool

- GIVEN a server that listed a tool as served in the primary worktree, without long work and on the session's thread
- WHEN the current code's registration serves it in the session's worktree, or as long work, or on a thread of its own, and the session calls it without listing its tools again
- THEN the call's process answers how the current code serves every tool, running nothing
- AND the server runs the call again in the session's worktree, or hands on its long work in that worktree, or answers it on a thread of its own
- AND a call routed twice otherwise is refused with `call_failed`

This illustrates [serving a call as the current code registers its tool](requirements.md#req.distribution.mcp-current-serving).

### scenario.distribution.mcp-call-failed — A call without an answer keeps what its process printed

- GIVEN a call whose process prints on standard output and standard error but no answer
- WHEN the process exits, exceeds its time and is stopped, or, as the process of a long-work tool, exits before answering
- THEN the server refuses the call with `call_failed`, naming the command
- AND the link's detail holds the end of what the process printed on each of the two streams

This illustrates [refusing a call without an answer](requirements.md#req.distribution.mcp-call-failed).

### scenario.distribution.mcp-tools-changed-after-refresh — Learning how a tool is served lists nothing to the session

- GIVEN a server that listed its tools to the session
- WHEN the session calls a tool the listing lacks, so that the server fetches the current code's listing to learn how it is served
- AND the answer says the current code's tools differ from those listed
- THEN the server tells its session that its tools changed

This illustrates [the session hearing that its tools changed](requirements.md#req.distribution.mcp-tools-changed).

### scenario.distribution.mcp-channel-override — `CONCORDE_CHANNEL` decides the channel

- GIVEN a server below an interactive `claude` started with `server:concorde` as a channel
- WHEN `CONCORDE_CHANNEL` is `0`
- THEN the server has no channel

This illustrates [the environment deciding the channel](requirements.md#req.distribution.mcp-channel-override).

### scenario.distribution.mcp-channel-forced — `CONCORDE_CHANNEL` gives a channel no `claude` asked for

- GIVEN a server below no `claude` started with `server:concorde` as a channel
- WHEN `CONCORDE_CHANNEL` is `1`
- THEN the server has a channel

This illustrates [the environment deciding the channel](requirements.md#req.distribution.mcp-channel-override).

### scenario.distribution.install-project-mcp — The installer registers the project MCP server

- GIVEN a project whose `.mcp.json` registers a server of its own
- WHEN the installer runs
- THEN `.mcp.json` also registers `concorde` as `.concorde/bin/concorde project-mcp`
- AND the project's own server is unchanged
- AND the receipt lists `.mcp.json` under `amended`
- AND installing again leaves the file as it is

### scenario.distribution.install-mcp-config-invalid — An unusable `.mcp.json` refuses the install

- GIVEN a project whose `.mcp.json` is not a JSON object
- WHEN the installer runs
- THEN it is refused with `mcp_config_invalid`
- BUT nothing is written, not even a workflow the project lacks

### scenario.distribution.update — Updating Concorde in a project

- GIVEN an initialized project with an open task, installed from a checkout whose Protocol has since changed
- WHEN the developer runs `concorde update`
- THEN the configuration binds the new Protocol copy, the [update result](contracts.md#contract.distribution.update-result) names the bindings, versions and installed commits before and after and the open task, and `.concorde/update.json` marks the project Concorde unvalidated
- AND the result asks for the primary branch to be merged into the open task

### scenario.distribution.update-marked-again — Updating again before a validation

- GIVEN a project that an update from an older Concorde marked Concorde unvalidated, rebinding its Protocol, and that has not validated since
- WHEN the developer runs `concorde update` again and it fails before writing its mark
- THEN the earlier mark is as it was
- AND once the developer runs `concorde update` again and it succeeds, the mark names the older Concorde's version, installed commit and Protocol binding as the ones before and this update's as the ones after

### scenario.distribution.update-unvalidated-reported — Validation reports an update not yet validated

- GIVEN a project that `concorde update` marked Concorde unvalidated
- AND one of its Specs is broken
- WHEN the developer runs `concorde spec-validation` in the primary worktree
- THEN the result is `invalid` and reports `CONCORDE-UPDATE-001` beside the Spec's own findings
- AND `.concorde/update.json` stays

### scenario.distribution.update-unvalidated-cleared — The first clean validation clears the mark

- GIVEN a project that `concorde update` marked Concorde unvalidated
- AND its Specs validate
- WHEN the developer runs `concorde spec-validation` in the primary worktree
- THEN the result is `success` and reports `CONCORDE-UPDATE-002`
- AND `.concorde/update.json` is removed

### scenario.distribution.install-busy — An install is refused while a run holds its run lock

- GIVEN an installed project in which the runner of an [Operation](../glossary.json#concept.operation) or [execution command](../glossary.json#concept.execution-command) run still holds its [run lock](../glossary.json#concept.run-lock)
- AND a bound run still waiting for its workspace's lock holds its run lock, with its [run progress file](../glossary.json#concept.run-progress-file) in the lobby
- AND its [run store](../glossary.json#concept.run-store) also holds the [progress file](../glossary.json#concept.progress-file) of the running Operation's worker and a run whose run lock nobody holds
- WHEN the developer installs Concorde again or runs `concorde update`
- THEN the install is refused with `concorde_busy`, naming each running run with its run lock, the process holding it and its progress file
- BUT neither the worker's progress file nor the run whose run lock nobody holds is named, whatever process its recorded identifier names
- AND nothing in the project changes

### scenario.distribution.install-after-runs-end — Concorde is replaced once no run holds its run lock

- GIVEN an installed project whose run store holds a finished run, a run whose run lock nobody holds although its recorded process identifier names a live process, and the progress file of an Operation's worker
- WHEN the developer installs Concorde again
- THEN the install succeeds

### scenario.distribution.install-idle-check-failed — An idle check that fails refuses the install unchanged

- GIVEN an installed project in which an installed part's idle check raises, or answers something other than a list of descriptions
- WHEN the developer installs Concorde again
- THEN the install is refused with `part_failed`, whose reason is `environment` and whose detail names the part and its entry
- BUT nothing in the project changes

### scenario.distribution.update-open-tasks-failed — An open-task report that fails loses only the report

- GIVEN a project installed with the spec and coordination parts, in which the coordination part's after-update entry raises
- WHEN the developer runs `concorde update`
- THEN the update is refused with `part_failed`, naming the coordination part and its entry
- AND the new receipt is written and `.concorde/update.json` marks the project Concorde unvalidated

### scenario.distribution.install-refusal-link — A refused install answers with an error link

- GIVEN an installer run on a directory that does not exist or without a project, or `concorde update` in a project whose receipt names no checkout or with `--from` lacking its value
- WHEN the command refuses
- THEN it prints `{"error": <link>}` with a link of the Framework's error contract, whose actor is the installer or `concorde update`, whose code is `invalid_project`, `update_source_missing` or `invalid_arguments`, and whose reason is `input`
- AND it exits with status 1

### scenario.distribution.install-write-failed — A write that fails after the first write is refused

- GIVEN a project in which the installer cannot write the project skill, because a file stands where its folder `.claude/skills/concorde/` goes
- WHEN the developer runs the installer
- THEN the install is refused with `install_failed`, naming the operating system's error, whose reason is `environment`
- AND the Protocol copy and Framework copy placed before stay in place, while no receipt is written
- AND once the file is moved away, running the installer again completes the install and writes the receipt

### scenario.distribution.update-mark-failed — An update that fails after its receipt is completed by running it again

- GIVEN an installed project in which `concorde update` cannot write its mark, because a directory stands at `.concorde/update.json`
- WHEN the developer runs `concorde update`
- THEN the update is refused with `install_failed`, naming the operating system's error
- AND the receipt already names the new install, while the project is not marked Concorde unvalidated
- AND once the directory is removed, running the update again marks the project Concorde unvalidated

### scenario.distribution.own-python — Concorde ignores the caller's Python

- GIVEN a project where Concorde is installed with the coordination part and that has no task, open or ended
- AND a caller whose `python3` on `PATH` fails and whose `PYTHONPATH` names a package called `concorde` that fails on import
- WHEN the caller runs `.concorde/bin/concorde task list`
- THEN it prints the project's empty task list `[]` and exits with status 0, run by the interpreter of `.concorde/framework/python/`
- AND uv created that environment for the Python requirement `concorde.json` names, and the receipt names the environment, the requirement, the interpreter uv chose and its version

### scenario.distribution.install-python-env-failed — No interpreter fits Concorde's Python requirement

- GIVEN a Concorde package whose Python requirement no interpreter on the machine satisfies
- AND uv may not download one
- WHEN the developer runs the installer
- THEN the install is refused with `python_env_failed`, carrying uv's output

### scenario.distribution.install-programs-missing — A missing program refuses the install before anything is written

- GIVEN a machine without `uv` on `PATH`, or without `npm` while the pi runtime is still to be placed
- WHEN the developer runs the installer on a project
- THEN the install is refused with `uv_missing` or `npm_missing`
- BUT nothing is written into the project, not even `d2`

### scenario.distribution.python-dependencies — Concorde's own environment gets its locked dependencies

- GIVEN a Concorde checkout whose `uv.lock` locks its runtime dependencies, and `uv` on `PATH`
- WHEN the installer runs
- THEN it exports the lock's runtime part, without the development group, to `.concorde/framework/requirements.txt`
- AND installs exactly those hashed versions into `.concorde/framework/python/` and checks that the environment imports LangGraph
- AND the receipt names the requirements file, the digest of the lock and the number of packages

### scenario.distribution.python-dependencies-failed — A failing dependency step refuses the install

- GIVEN a Concorde checkout and `uv` on `PATH`
- WHEN the installer runs and a step installing the Python dependencies fails
- THEN the install is refused with `python_dependencies_failed`, carrying the step's output

### scenario.distribution.python-dependencies-skipped — Install without the Python dependencies

- GIVEN a Concorde checkout and `uv` on `PATH`
- WHEN the developer runs the installer with `--without-dependencies`
- THEN the receipt's `dependencies` is `null`

### scenario.distribution.task-worktree-command — The command works in a task worktree

- GIVEN a project where Concorde is installed with the coordination part and committed, that has no task, open or ended, and a linked worktree of it, which has no Framework copy of its own
- WHEN `.concorde/bin/concorde task list` of the linked worktree runs
- THEN it runs the primary worktree's Framework copy, prints the empty task list `[]` and exits with status 0

### scenario.distribution.install-d2-refused — A d2 archive that cannot be trusted installs nothing

- GIVEN a fresh Concorde package whose `concorde.json` pins a `d2` release
- WHEN the installer runs and the downloaded archive does not match the pinned SHA-256, or the download fails
- THEN the installer refuses with `d2_digest_mismatch` or `d2_unavailable`, naming the URL and the reason
- AND nothing is written into the project

### scenario.distribution.install-without-d2 — Install without d2

- GIVEN a fresh Concorde package whose `concorde.json` pins a `d2` release
- WHEN the developer runs the installer with `--without-d2`
- THEN the install succeeds and the receipt names no `d2`
- BUT no `d2` is placed under `.concorde/tools/`, leaving it to the developer

### scenario.distribution.pi-runtime-default — Every install places the runtime pi workers run in

- GIVEN a project and a machine with npm
- WHEN the developer installs Concorde
- THEN the locked pi runtime is placed under `.concorde/tools/pi-runtime/`, since workers run on pi unless configured otherwise
- AND the receipt records `pi_runtime` true
- BUT no file of a pi main session is placed, since the [main agent](../glossary.json#concept.main-agent) runs on Claude Code

### scenario.distribution.install-without-pi-runtime — Install without the pi runtime

- GIVEN a project and a machine without npm
- WHEN the developer installs Concorde with `--without-pi-runtime`
- THEN the install succeeds without the runtime under `.concorde/tools/pi-runtime/`
- AND the receipt records `pi_runtime` false

### scenario.distribution.update-pi-runtime — An update adds the pi runtime

- GIVEN a project installed without the pi runtime by an installer that did not record the choice
- WHEN the developer runs `concorde update`
- THEN the pi runtime is placed
- AND the receipt records `pi_runtime` true
- AND the next `concorde update` keeps the runtime without installing it again

### scenario.distribution.install-later-files-bound — Files a later install adds stay bound

- GIVEN a project in which Concorde was installed and then initialized
- AND as a result, its installation realization binds the files installed then
- WHEN the developer installs Concorde again, or runs `concorde update`, with a Concorde that installs more files
- AND a workflow an older Concorde did not install is an example of such an additional file
- THEN for each added file listed under the receipt's `files` outside `.concorde/`, when no other realization binds that file's exact path, the installation realization has an exact entry for it
- BUT the files the receipt names as `amended` are not bound
- AND once the files are committed, `concorde spec-validation` reports no `CHK.binds.unbound` for them
- BUT a project that is not initialized gets no Spec
- AND installing again with nothing new leaves the Specs unchanged

### scenario.distribution.install-binding-failed — A failed binding is reported and the install kept

- GIVEN an initialized project in which Spec core refuses to bind the installation
- AND the refusal occurs, for instance, because writing the root [Module](../glossary.json#concept.module)'s metadata fails
- WHEN the developer installs Concorde
- THEN the install succeeds with the new receipt in place
- AND the install's result carries Spec core's error under `binding_error`, naming the file concerned
- BUT the receipt written to `.concorde/install.json` holds no `binding_error`

### scenario.distribution.update-keeps-pi-runtime-choice — An update keeps a runtime left out

- GIVEN a project installed with `--without-pi-runtime`, whose receipt records `pi_runtime` false
- WHEN the developer runs `concorde update`
- THEN even on a machine without npm, the update succeeds without the pi runtime
- AND the receipt still records `pi_runtime` false
