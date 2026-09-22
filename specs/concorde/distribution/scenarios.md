# Distribution scenarios

These are the concrete situations [Distribution](module.md) promises to handle. Module-wide
obligations are stated once in the [requirements](requirements.md) and linked from here.

## Build

### scenario.distribution.prompt-references — Resolve whole-line prompt references

- GIVEN prompt sources that reference other prompts with column-one `@path.md` lines, optionally followed by `KEY=value` bindings
- WHEN the resolver renders a worker, Protocol or capability guidance root
- THEN each reference is replaced by the referenced prompt with its bindings substituted
- AND the result lists every source that contributed to it
- AND a missing or unsafe target, a malformed binding, an unbound variable, an audience or layer violation, a cycle, a second inclusion of one file within one root, or a column-one `@include` line fails with its rule identity and no partial result
- BUT ordinary mentions, email addresses, decorators, inline references and indented lines stay literal text

The exact grammar and rule identities are in [Interfaces](interfaces.md#prompt-references).

### scenario.distribution.build-render — The build renders every output from sources

- GIVEN current Agent definitions, prompts, capability guidance, Protocol text and request contracts
- WHEN the build renders the checkout
- THEN it produces native instructions for the seven domain Agents under `generated/native/` and the same bytes under `generated/agents/`
- AND one session entry whose catalog lists the eleven public capabilities
- AND the Task subagent files, the Studio configuration, the Protocol assets and the exported schemas
- AND rendering the same sources again yields byte-identical outputs and manifest

See [req.distribution.build-idempotent](requirements.md#req.distribution.build-idempotent) and
[req.distribution.build-no-io](requirements.md#req.distribution.build-no-io).

### scenario.distribution.build-write — Writing the build records sources and outputs

- GIVEN a successful render
- WHEN `build` writes it
- THEN every output is written
- AND `generated/build-manifest.json` records the digest of every source and every output
- AND an output the new render no longer produces is removed when its bytes match the previous manifest, together with directories it leaves empty
- BUT files of other tools under `generated/` are neither judged nor removed

### scenario.distribution.build-check — Checking the build writes nothing

- GIVEN the generated outputs currently in the checkout
- WHEN `build --check` runs
- THEN it compares them with a fresh render in memory
- AND reports every missing, stale or extra owned output and every asset digest in `protocol/manifest.json` that differs from the render
- BUT it writes nothing

### scenario.distribution.build-retired-skills — Removing outputs the build no longer produces

- GIVEN files from an earlier build remain, such as per-capability `SKILL.md` projections under `generated/session/codex`, `generated/session/claude`, `.agents/skills` or `.claude/skills`, an old `.pi/extensions/concorde-session.ts` or an old `.pi/APPEND_SYSTEM.md` in this checkout
- WHEN `build --check` or `build` runs
- THEN checking reports them without writing
- AND building removes each one only when its bytes match the previous build manifest
- AND a modified or unrecorded file, a symbolic link or unexpected content next to such a file stops the build before anything is written or removed
- BUT unrelated files in those directories and `skills-lock.json` are never touched

Only the exact names of the public capabilities and of five older capability names are inspected
in those directories; a name alone never proves ownership. See
[req.distribution.owned-retirement](requirements.md#req.distribution.owned-retirement).

### scenario.distribution.build-checkout-skills-user-invoked — The source session entry stays private

- GIVEN a build of this checkout
- WHEN it renders the session entry
- THEN the entry is `generated/session/pi/concorde-session.ts`, which Pi does not discover by itself
- AND its catalog is marked explicit-request-only and names the checkout's own launcher and `.venv` interpreters
- AND the installed layout renders the same capabilities under `.pi/extensions/concorde-session.ts` with the installed launcher and the managed runtime's interpreters

### scenario.distribution.build-pi-session — The catalog embeds guidance and request schemas

- GIVEN capability guidance under `prompts/operation-guidance/` and the exported request schemas
- WHEN the build renders a session entry
- THEN the entry imports the tracked session extension and embeds, for each public capability, its name, kind, description, resolved guidance, request schema and that schema's version
- AND guidance with wrong front matter, an unresolved `{SCRIPT}`, `{FRAMEWORK}` or `{OPERATION}` token, or no exported request schema fails the build
- AND `build --check`, package validation and the byte-exact test fixture detect any drift between the entry and its sources

### scenario.distribution.build-stale-blocks-execution — A stale build stops model-backed work

- GIVEN a recorded build source has changed or disappeared since the last build, or no build exists
- WHEN a model-backed capability is run or described, or an Agent's instructions are loaded
- THEN the freshness check fails with `stale_build`
- AND no instructions from the old build are used
- BUT `concorde-init`, `concorde-configure`, `concorde-validate` and `concorde-deliver`, which load no generated instructions, are not stopped by this check at admission

See [req.distribution.fresh-instructions](requirements.md#req.distribution.fresh-instructions).

### scenario.distribution.load-agent — Loading one Agent's current instructions

- GIVEN a fresh build
- WHEN the Host loads the instructions of a domain Agent by its bare, hyphenated or `concorde-` prefixed name
- THEN the build's freshness is checked first
- AND the result carries the Agent's external name, description, source path, rendered instructions, effects ceiling and complete worker binding
- AND an unknown Agent, an invalid binding or a stale build fails with the build error code `unknown_agent`, `invalid_agent_binding` or `stale_build`
- BUT a public capability name is not an Agent name and loads no instructions

### scenario.distribution.operation-determinism — Capability modules declare whether they call a model

- GIVEN capability modules in `operations/` that declare their kind, exposure, context selection, profile and the modules they use
- WHEN package validation checks them
- THEN each module must declare a boolean `DETERMINISTIC`
- AND that flag must be true exactly when neither its profile nor any module it uses, directly or transitively, can call a model
- AND a module that selects no Agent context must have no path to a model call
- AND the capability inventory in the Operations Spec's metadata must carry the same `deterministic` value for each capability
- BUT validation judges declared model-call paths only, not what arbitrary Python code does

Findings use `CONCORDE-OPERATION-CONSTANTS-001`, `CONCORDE-OPERATION-DETERMINISTIC-001` and
`CONCORDE-SPEC-OPERATIONS-001`.

## Session integration

### scenario.distribution.pi-session-prompt — A session learns the tool and the capabilities

- GIVEN a Pi session that loaded a session entry
- WHEN a turn starts
- THEN the entry appends a Concorde section to the system prompt naming the `concorde` tool and every capability with its description
- AND in the source checkout the section adds that a capability runs only when the developer asks for it by name
- AND the tool's `operation` parameter admits exactly the catalog's capabilities, its `action` is `run`, `describe` or `result`, and its optional `mode` is `execute` or `describe-policy`

### scenario.distribution.pi-session-describe — Describing a capability runs nothing

- GIVEN a Pi session that loaded a session entry
- WHEN the model calls `concorde` with action `describe`
- THEN the tool returns the capability's description, guidance and request schema from the catalog
- BUT it does not start the launcher

### scenario.distribution.pi-session-run — Running a Host capability goes through the launcher

- GIVEN a Pi session that loaded a session entry
- WHEN the model calls `concorde` with action `run` for a Host capability and the request data as `input`
- THEN the tool wraps `input` in a version 3 `concorde-operation-invocation` envelope with the capability's typed request, runs the launcher in the project root with the envelope on standard input, and returns the launcher's result with its usage summary
- AND a result the launcher reports as `blocked` or `failed`, a non-zero exit or unreadable output is returned as a tool error carrying the envelope
- AND a missing `input` or an unknown capability is refused without starting the launcher
- AND a result larger than 48 KiB is saved whole to a file that the returned text names

### scenario.distribution.pi-session-cancel — Aborting the turn cancels the run

- GIVEN a `run` in progress through the `concorde` tool
- WHEN the developer aborts the turn
- THEN the extension sends the launcher SIGTERM and reports the cancellation as a tool error carrying whatever result the launcher printed
- AND a launcher that has not exited within five seconds is killed together with its process group

### scenario.distribution.launcher-terminated — SIGTERM ends the launcher like Ctrl-C

- GIVEN a running `scripts/run-operation.py`
- WHEN the process receives SIGTERM
- THEN it takes the Ctrl-C path, so the Host cancels the running work and the launcher prints the result envelope before exiting
- AND SIGTERM while the launcher is still reading its invocation prints a failure envelope with `execution_cancelled`

See [req.distribution.launcher-sigterm-cancels](requirements.md#req.distribution.launcher-sigterm-cancels).

### scenario.distribution.private-selection — Selecting exact candidate inputs for a fresh session

- GIVEN a candidate with a fresh build and absolute paths to its private session entry and launcher
- WHEN `select-session --mode test` runs
- THEN the record names the build manifest digest, the launcher and session extension digests, the complete entry bytes, the exact embedded catalog and the Pi flags of a fresh session without discovered resources
- AND a missing, modified, aliased or out-of-candidate path, a symbolic link among the sources or a stale build fails without any fallback
- AND mode `maintenance` accepts no entry, and test and task modes require one
- AND a selection is saved only under the candidate's `.concorde/work/` and `--verify` accepts it only if a fresh selection is identical
- AND the private entry refuses to load without a selection, verifies it before registering the tool and before every call, and refuses a changed selection or a redirect to Studio
- BUT a selection is not evidence that Pi loaded the entry, that a tool was used or that a model ran

See [req.distribution.private-selection](requirements.md#req.distribution.private-selection).

## Installation

### scenario.distribution.install-preview — Previewing writes nothing

- GIVEN a target project directory
- WHEN the installer runs without `--apply`
- THEN it prints the plan of actions for every Framework, Pi, Protocol, root guidance and runtime path together with the notice about externally installed Skills
- AND it exits with status 2 when any action is a conflict
- BUT it writes no file, and repeating it gives the same plan

### scenario.distribution.install-apply — Applying a current plan installs owned outputs

- GIVEN a previewed plan without conflicts that still matches the target
- WHEN the installer runs with `--apply`
- THEN it writes the Framework under `.concorde/framework/`, the session entry, observer and tester definition under `.pi/`, the Protocol copy under `.concorde/protocol/` and the `AGENTS.md` block
- AND it provisions the managed runtime and writes the installation receipt last
- AND it seeds `.concorde/issues/.gitignore` only when absent, without recording it in the receipt
- AND it leaves the project's Specs, configuration, Protocol binding and unrelated files unchanged
- BUT `node_modules` below the package's `pi/` directory is neither deployed nor inspected

### scenario.distribution.install-conflict-rejected — Conflicting or stale state blocks the apply

- GIVEN a modified owned file or block, an unowned file or marked block in the way, a symbolic link or malformed root file, or a target that changed after the preview
- WHEN `--apply` is requested
- THEN the installer refuses before writing
- AND if a failure happens after writing began, every owned change is restored

See [req.distribution.receipt-ownership](requirements.md#req.distribution.receipt-ownership),
[req.distribution.root-block-ownership](requirements.md#req.distribution.root-block-ownership) and
[req.distribution.rollback-on-failure](requirements.md#req.distribution.rollback-on-failure).

### scenario.distribution.install-remove-guidance — Removing only the owned root blocks

- GIVEN an installation whose receipt owns root blocks
- WHEN `--remove-protocol-guidance --apply` runs
- THEN only the owned blocks are removed and their records dropped from the receipt
- AND a root file the receipt records the installer created is removed when nothing else remains in it, while a file the developer created stays even when empty
- AND the Framework, runtime and other receipt records stay
- AND repeating the removal changes nothing

### scenario.distribution.install-retired-clients — Upgrading an installation from an older receipt

- GIVEN a schema 1 receipt that also owns files and a `CLAUDE.md` block for other clients
- WHEN the current installer applies an upgrade
- THEN it installs the session entry and the `AGENTS.md` block, and removes only the unchanged owned files and the exact owned `CLAUDE.md` block
- AND edited owned content, unsafe links or inputs changed since the preview block before writing
- AND surrounding text, modes, unrelated files, externally installed Skills and `skills-lock.json` stay
- AND a failure restores the removed bytes, modes and the previous receipt, so a fresh plan can retry
- AND a receipt without root records can gain the Pi block without adopting existing marked content

### scenario.distribution.template-ownership — Templates ship only inside their owners

- GIVEN the current package and either a fresh target or a receipt that owns obsolete root template files
- WHEN installation previews and applies the package
- THEN the Framework has no root templates directory, the Module and Scenario starters ship under `protocol/templates/`, and the plan and task starters ship inside their Agents' packages
- AND an upgrade removes only unchanged owned obsolete template files, leaving other material, and possibly empty directories, in place
- AND modified owned files, symbolic links or changes after the preview block before writing, and a failed apply restores the removed bytes, modes and receipt
- AND repeating the installation changes nothing

### scenario.distribution.install-pi-session — The session entry is the only client integration

- GIVEN a target project
- WHEN installation is applied
- THEN `.pi/extensions/concorde-session.ts` is an owned output that imports the installed session extension and names the installed launcher and the managed runtime's interpreters
- AND the `AGENTS.md` block is installed for Pi to read as a context file
- BUT no Skills, Skills tool lock or other client's files are installed, and an unknown option such as `--integration` is refused before the target is touched

See [req.distribution.pi-only-install](requirements.md#req.distribution.pi-only-install).

### scenario.distribution.install-preserve-project — Keeping inherited project files without owning them

- GIVEN a target with a committed Protocol copy and `AGENTS.md` block but no local receipt, or with arbitrary existing root instructions
- WHEN installation runs with `--preserve-project`
- THEN the existing Protocol copy, root files and their modes, configuration, registry, Specs and binding stay unchanged and are not adopted
- AND an entirely absent Protocol copy or `AGENTS.md` may be seeded as owned outputs, and repeating the installation keeps that ownership and changes nothing
- AND files a local receipt already owns must still match it and keep their ownership
- AND a partial, aliased or changed Protocol copy stops the installation, and a complete copy of another version is kept but not accepted for running
- BUT without `--preserve-project` an unowned marked block is still a conflict

### scenario.distribution.install-local-worktree — Installing a worktree from an admitted package

- GIVEN an admitted source or installed package and a Git worktree without a runtime or receipt
- WHEN the Host explicitly bootstraps that worktree through the local installation service or its deployed installer
- THEN the worktree receives a complete Framework, session entry with catalog, managed runtime and receipt naming the exact package identity
- AND every runtime check uses the worktree's own interpreter, so the installation stays valid without the provider's environment
- AND a later call reuses the verified installation without reinstalling, acquiring dependencies or rewriting the marker or receipt
- BUT no candidate status or run record is created and no capability or model is started

See [req.distribution.worktree-local-install](requirements.md#req.distribution.worktree-local-install).

### scenario.distribution.install-local-failure — A failed local installation never supplies a fallback

- GIVEN missing or conflicting local state, changed provider bytes, a concurrent installer or a failed acquisition or check
- WHEN local verification or an explicit bootstrap is requested
- THEN missing or stale state fails without an implicit bootstrap, and conflicting ownership is preserved
- AND a failed creation restores the owned files and receipt, keeps unrelated project bytes, and allows a fresh plan once the cause is fixed
- AND an aliased target, a Concorde source checkout as target and a second concurrent installer are refused
- BUT no failure returns a verified installation, and no other worktree's or global runtime takes its place

See [req.distribution.no-runtime-fallback](requirements.md#req.distribution.no-runtime-fallback).

## Runtime

### scenario.distribution.runtime-plan — Planning the runtime changes nothing

- GIVEN a target, the package's runtime specification and the current receipt
- WHEN the runtime is planned
- THEN the plan holds one action of `create`, `unchanged`, `rebuild` or `conflict` with the runtime path, role and digest
- BUT planning replaces no file and acquires no package, although it may run local offline health probes

### scenario.distribution.runtime-provision — Provisioning builds and verifies the runtime

- GIVEN a current runtime action that is not `conflict`
- WHEN the runtime is provisioned
- THEN a created or rebuilt runtime receives the locked Python dependencies and the pinned Pi dependencies
- AND every public capability's runtime check runs with the runtime's own interpreter and must report that runtime as its prefix and the pinned LangGraph version
- AND only then is the owner marker written and the runtime record returned
- AND an `unchanged` runtime is not rebuilt but is checked again and may have its marker refreshed

See [req.distribution.runtime-verified-before-use](requirements.md#req.distribution.runtime-verified-before-use).

### scenario.distribution.runtime-provision-failure — A failed provisioning leaves nothing marked as verified

- GIVEN a provisioning attempt whose dependency acquisition or verification fails
- WHEN the provisioner reports the failure
- THEN the directory it was creating or rebuilding is removed and no marker claims a verified runtime
- AND a runtime directory that appeared after a `create` plan is refused rather than adopted
- AND no runtime record is returned, so a caller cannot mistake the failure for success
- BUT a failed rebuild does not bring back the previous runtime, and the installer must run again

### scenario.distribution.launcher-managed-runtime — The installed launcher enters the managed runtime

- GIVEN a consumer project whose Framework is at `.concorde/framework` and whose verified runtime, with Concorde's owner marker, is at `.concorde/.venv`
- WHEN `.concorde/framework/scripts/run-operation.py` is started with another interpreter, even an ambient `python3` without LangGraph
- THEN it re-executes itself with the runtime's interpreter before reading its invocation
- AND a launcher already running inside that runtime is not re-executed
- AND the source checkout, which has neither layout, keeps the interpreter that started it
- AND a runtime check that cannot import LangGraph reports `missing_runtime`

See [req.distribution.launcher-managed-runtime](requirements.md#req.distribution.launcher-managed-runtime).

## Configuration

### scenario.distribution.configure-apply — Configuring workers is all or nothing

- GIVEN an initialized project and a valid worker configuration
- WHEN `concorde-configure` is applied
- THEN the configuration is written to `.concorde/config.json` and the result is `status: applied`
- AND an invalid value, an uninitialized project or a failed write leaves the previous configuration in place
- BUT a `describe-policy` request is refused with `use_proposal`

See [req.distribution.configure-atomic](requirements.md#req.distribution.configure-atomic).

### scenario.distribution.accept-protocol — Accepting an installed Protocol is explicit

- GIVEN an initialized project whose Protocol binding no longer matches the Protocol copy under `.concorde/protocol/`
- WHEN `concorde-configure` is applied without `accept_protocol`
- THEN it fails with `protocol_mismatch` and the binding stays unchanged
- BUT with `accept_protocol: true` it binds the configuration to the copy's manifest and keeps the write only if the repository then loads

See [req.distribution.no-silent-protocol-rewrite](requirements.md#req.distribution.no-silent-protocol-rewrite).

## Development

### scenario.distribution.check-docsite-external — The docsite type check works on a disposable copy

- GIVEN this checkout with its docsite
- WHEN `scripts/development/check-docsite-types.py` runs
- THEN it copies the docsite to a temporary directory, derives the sidebar from the project registry there and runs the TypeScript compiler on the copy
- AND dependency installation and generated files stay inside that copy
- AND the checkout's installed dependencies are reused read-only only when their marker matches the package and lock bytes
- AND the command returns the compiler's exit status and removes the copy

### scenario.distribution.test-timing — Test runs record reasons and input identity

- GIVEN pytest arguments with or without `--reason`, `--scope`, `--phase`, `--attempt` and `--prior`
- WHEN the suite runs with `--json` reporting
- THEN the report records the reason, scope, phase, attempt, prior run and fingerprints of the tests, inputs, runtime, locks and environment
- AND a rerun with unchanged declared inputs is recognized as such
- AND discovery, queueing, execution and total elapsed times are reported separately, with setup time unknown unless measured
- AND callers that pass none of the options get `manual` and `unspecified` without new required flags
- BUT summed parallel test time is never reported as elapsed time

See [req.distribution.test-evidence](requirements.md#req.distribution.test-evidence).
