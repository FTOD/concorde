# Distribution scenarios

The concrete situations [Distribution](module.md) promises to handle. Module-wide obligations are
stated once in the [requirements](requirements.md) and linked from here; exact shapes are in the
[interfaces](interfaces.md).

## Build

### scenario.distribution.prompt-references — Resolve whole-line prompt references

- GIVEN prompt sources that reference other prompts with column-one `@path.md` lines, optionally followed by `KEY=value` bindings
- WHEN the resolver renders an Agent, Protocol or capability guidance root
- THEN each reference is replaced by the referenced prompt with its bindings substituted
- AND the result lists every source that contributed to it
- BUT ordinary mentions, email addresses, decorators, inline references and indented lines stay literal text

The exact grammar is in [Interfaces](interfaces.md#prompt-references).

### scenario.distribution.prompt-reference-invalid — A broken reference fails with its rule

- GIVEN a prompt root with a missing or unsafe target, a malformed binding, an unbound variable, an audience or layer violation, a cycle or a second inclusion of one file
- WHEN the resolver renders the root
- THEN it fails with the rule identity of that violation
- BUT it returns no partial result

### scenario.distribution.build-render — The build renders every output from sources

- GIVEN current Agent definitions, prompts, capability guidance, Protocol text and registered schemas
- WHEN the build renders the checkout
- THEN it produces one native instruction file for each of the seven Agents under `generated/native/`
- AND one session entry whose catalog lists the public capabilities of the Operation catalog
- AND the Task subagent files, the Protocol assets and the exported schemas
- AND rendering the same sources again yields byte-identical outputs and manifest

See [req.distribution.build-idempotent](requirements.md#req.distribution.build-idempotent),
[req.distribution.build-no-io](requirements.md#req.distribution.build-no-io) and
[req.distribution.single-instructions](requirements.md#req.distribution.single-instructions).

### scenario.distribution.build-protocol-assets — The Protocol assets hold only the Protocol

- GIVEN the Protocol text and its Module chapter and templates
- WHEN the build renders the Protocol assets
- THEN the principles bundle holds every Protocol chapter in order and the Module asset holds the Module chapter with its templates
- AND neither holds any Concorde configuration, profile or execution rule

See [req.distribution.protocol-only-bundle](requirements.md#req.distribution.protocol-only-bundle).

### scenario.distribution.build-write — Writing the build records sources and outputs

- GIVEN a successful render and owned output locations that hold only what the previous build wrote
- WHEN `build` writes it
- THEN every output is written
- AND the build manifest records the digest of every source and every output
- AND an output the new render no longer produces is removed together with directories it leaves empty
- BUT files of other tools under `generated/` are neither judged nor removed

See [req.distribution.owned-retirement](requirements.md#req.distribution.owned-retirement) and
[req.distribution.manifest-complete](requirements.md#req.distribution.manifest-complete).

### scenario.distribution.build-write-refused — An unowned or edited output stops the build

- GIVEN a modified or unrecorded file or a symbolic link among the owned output locations
- WHEN `build` writes
- THEN the build fails naming the file
- BUT nothing is written or removed

### scenario.distribution.build-check — Checking the build writes nothing

- GIVEN the generated outputs currently in the checkout
- WHEN `build --check` runs
- THEN it compares them with a fresh render in memory
- AND reports every missing, stale or extra owned output and every Protocol manifest digest that differs from the render
- BUT it writes nothing

### scenario.distribution.private-session-entry — The source session entry stays private

- GIVEN a build of this checkout
- WHEN it renders the session entry
- THEN the entry is `generated/session/pi/concorde-session.ts`, which Pi does not discover by itself
- AND its catalog is marked explicit-request-only and names the checkout's own launcher and `.venv` interpreters
- AND the installed layout renders the same capabilities under `.pi/extensions/concorde-session.ts` with the installed launcher and the managed runtime's interpreters

See [req.distribution.private-source-entry](requirements.md#req.distribution.private-source-entry).

### scenario.distribution.build-pi-session — The catalog embeds guidance, paths and request schemas

- GIVEN capability guidance for every public capability, the capability declarations and the registered request schemas
- WHEN the build renders a session entry
- THEN the entry imports the tracked session extension and embeds, for each public capability, its name, kind, native actions, description, resolved guidance, request schema and that schema's version

### scenario.distribution.build-guidance-invalid — Invalid guidance fails the build

- GIVEN guidance with wrong front matter or a reserved token left after resolution, or a public capability without a registered request schema
- WHEN the build renders a session entry
- THEN the build fails naming the capability
- BUT no output is written

## Package check

### scenario.distribution.package-check — A current package passes

- GIVEN a package whose prompts resolve, whose guidance and schemas are complete and whose build is fresh and matches a fresh render
- WHEN `check-package` runs
- THEN it reports success without findings

### scenario.distribution.package-check-drift — Drift is reported as findings

- GIVEN a package whose catalog, outputs or Protocol manifest differ from a fresh render, or whose build is not fresh
- WHEN `check-package` runs
- THEN it reports each difference as a finding attributed to Distribution
- BUT it repairs nothing

See [req.distribution.operation-guidance-fresh](requirements.md#req.distribution.operation-guidance-fresh).

## Launcher and command line

### scenario.distribution.launcher-dispatch — The launcher hands a catalog capability to admission

- GIVEN a public capability of the Operation catalog and a capability request on standard input
- WHEN `run-operation.py <capability>` runs
- THEN it hands the request, the catalog's declarations, Operations' dispatcher and the local installation service to Request admission
- AND prints the one result envelope admission returns

See [req.distribution.catalog-dispatch](requirements.md#req.distribution.catalog-dispatch).

### scenario.distribution.launcher-unknown — An unknown name is refused

- GIVEN a name that is not a public capability of the Operation catalog, or an unsupported argument list
- WHEN the launcher starts
- THEN it prints an `unknown_operation` failure envelope and exits with status 3
- BUT it reads no request and starts no capability

### scenario.distribution.launcher-selection — An active selection is verified before a run

- GIVEN a launcher started with a session selection in its environment
- WHEN it receives a capability request
- THEN it verifies the selection through Pi session before admission runs anything
- AND hands the verified selection record to Request admission as the run's session provenance

### scenario.distribution.launcher-selection-refused — A selection that does not verify stops the run

- GIVEN a launcher started with a session selection that no longer verifies
- WHEN it receives a capability request
- THEN it prints a failure envelope
- BUT admission runs nothing

### scenario.distribution.launcher-terminated — SIGTERM ends the launcher like Ctrl-C

- GIVEN a running launcher that has read its request
- WHEN the process receives SIGTERM
- THEN it takes the Ctrl-C path, so the Host cancels the running work and the launcher prints the result envelope before exiting

See [req.distribution.launcher-sigterm-cancels](requirements.md#req.distribution.launcher-sigterm-cancels).

### scenario.distribution.launcher-terminated-reading — SIGTERM before the request is read

- GIVEN a launcher still reading its request
- WHEN the process receives SIGTERM
- THEN it prints a failure envelope with `execution_cancelled`

### scenario.distribution.cli-envelope — Every subcommand prints one envelope

- GIVEN any `scripts/concorde.py` subcommand
- WHEN it finishes, succeeds or fails
- THEN it prints exactly one canonical JSON envelope and exits with the code of its status
- AND an unexpected exception becomes a `failed` envelope with `CONCORDE-RUN-001`

### scenario.distribution.protocol-manifest-bind — Accepting new Protocol assets in this checkout

- GIVEN a fresh build after a change to the Protocol text
- WHEN `protocol-manifest --write --bind-project` runs
- THEN the Protocol manifest records the rendered asset digests
- AND this checkout's Protocol binding and Protocol copy match that manifest

## Installation

### scenario.distribution.install-preview — Previewing writes nothing

- GIVEN a target project directory
- WHEN the installer runs without `--apply`
- THEN it prints the plan of actions for every Framework, Pi, Protocol, root guidance and runtime path
- AND it exits with the conflict status when any action is a conflict
- BUT it writes no file, and repeating it gives the same plan

### scenario.distribution.install-apply — Applying a current plan installs owned outputs

- GIVEN a previewed plan without conflicts that still matches the target
- WHEN the installer runs with `--apply`
- THEN it writes the Framework under `.concorde/framework/`, the session entry, observer and tester definition under `.pi/`, the Protocol copy under `.concorde/protocol/` and the `AGENTS.md` block
- AND it provisions the managed runtime and writes the installation receipt last
- AND it seeds `.concorde/issues/.gitignore` only when absent, without recording it in the receipt
- AND it leaves the project's Specs, configuration, Protocol binding and unrelated files unchanged
- BUT no source-only file is deployed, and `node_modules` below the package's `pi/` directory is neither deployed nor inspected

See [req.distribution.no-silent-protocol-rewrite](requirements.md#req.distribution.no-silent-protocol-rewrite)
and [req.distribution.source-only-assets](requirements.md#req.distribution.source-only-assets).

### scenario.distribution.install-conflict-rejected — Conflicting state blocks the apply

- GIVEN a modified owned file or block, an unowned file or marked block in the way, a symbolic link or a malformed root file
- WHEN `--apply` is requested
- THEN the installer refuses with the conflicts listed
- BUT it writes nothing

See [req.distribution.receipt-ownership](requirements.md#req.distribution.receipt-ownership) and
[req.distribution.root-block-ownership](requirements.md#req.distribution.root-block-ownership).

### scenario.distribution.install-stale-plan — A target that changed after the preview is refused

- GIVEN a target whose root files, recomputed plan or package identity differ from what the preview saw
- WHEN `--apply` is requested
- THEN the installer refuses the plan
- BUT it writes nothing

See [req.distribution.stale-plan-refused](requirements.md#req.distribution.stale-plan-refused).

### scenario.distribution.install-apply-rollback — A failed apply restores files and receipt

- GIVEN an apply that fails after it began writing files, other than by a failed runtime rebuild
- WHEN the installer handles the failure
- THEN every file it created is removed and every file it replaced or removed has its previous bytes and mode
- AND the previous receipt is restored, or deleted when there was none
- AND a runtime it created in this apply is removed
- BUT no partially applied state remains

See [req.distribution.rollback-on-failure](requirements.md#req.distribution.rollback-on-failure).

### scenario.distribution.install-unknown-option — An unknown option touches nothing

- GIVEN an installer command line with an unknown option
- WHEN it starts
- THEN it fails before reading or writing the target

### scenario.distribution.install-remove-guidance — Removing only the owned root blocks

- GIVEN an installation whose receipt owns root blocks
- WHEN `--remove-protocol-guidance --apply` runs
- THEN only the owned blocks are removed and their records dropped from the receipt
- AND a root file the receipt records the installer created is removed when nothing else remains in it, while a file the developer created stays even when empty
- AND the Framework, runtime and other receipt records stay

### scenario.distribution.install-remove-guidance-repeat — Removing the blocks again changes nothing

- GIVEN an installation whose owned root blocks were already removed
- WHEN `--remove-protocol-guidance --apply` runs again
- THEN no file and no receipt record changes

### scenario.distribution.install-upgrade — Updating replaces only unchanged owned outputs

- GIVEN a current receipt that owns files, including files and a root block the new package still ships and files it no longer ships
- WHEN the installer applies the newer package
- THEN it updates the owned files and the `AGENTS.md` block that are unchanged since they were written, and removes the unchanged owned files the package no longer ships
- AND surrounding text, modes and unrelated files stay

See [req.distribution.no-surrounding-text-rewrite](requirements.md#req.distribution.no-surrounding-text-rewrite).

### scenario.distribution.install-receipt-schema — A receipt of another schema is refused

- GIVEN a target whose installation receipt has a schema other than the current one, repeats a path or records a whole root file
- WHEN the installer plans
- THEN it fails without writing

### scenario.distribution.template-ownership — Templates ship inside their owners

- GIVEN the current package
- WHEN installation previews and applies it
- THEN the Module and Scenario starters ship under the Framework's `protocol/templates/`
- AND the package declares no separate templates root

### scenario.distribution.install-pi-session — The session entry is the only client integration

- GIVEN a target project
- WHEN installation is applied
- THEN `.pi/extensions/concorde-session.ts` is an owned output that imports the installed session extension and names the installed launcher and the managed runtime's interpreters
- AND the `AGENTS.md` block is installed for Pi to read as a context file
- BUT no other client's files are installed

See [req.distribution.pi-only-install](requirements.md#req.distribution.pi-only-install).

### scenario.distribution.install-preserve-project — Keeping inherited project files without owning them

- GIVEN a target with a complete committed Protocol copy and `AGENTS.md` block but no local receipt, or with arbitrary existing root instructions
- WHEN installation runs with `--preserve-project`
- THEN the existing Protocol copy, root files and their modes, configuration, registry, Specs and binding stay unchanged and are not adopted
- AND an entirely absent Protocol copy or `AGENTS.md` may be seeded as owned outputs, and repeating the installation keeps that ownership and changes nothing
- AND files a local receipt already owns must still match it and keep their ownership
- BUT a complete Protocol copy of another version is kept and not accepted for running

### scenario.distribution.install-preserve-protocol-invalid — A damaged inherited Protocol copy stops preservation

- GIVEN a target whose inherited Protocol copy is partial, aliased or does not match its manifest
- WHEN installation runs with `--preserve-project`
- THEN the installation fails without writing
- BUT the copy is never completed with files of the new package

### scenario.distribution.install-concurrent — A second installer fails at once

- GIVEN an applying installer holding a target
- WHEN a second applying installer, from the command line or the local installation service, starts on the same target
- THEN the second fails at once without waiting and without writing

See [req.distribution.single-installer](requirements.md#req.distribution.single-installer).

### scenario.distribution.install-target-refused — An aliased or source target is refused

- GIVEN a target path through a symbolic link, or a Concorde source checkout as target
- WHEN the installer or the local installation service is asked to install there
- THEN it refuses without writing

## Local installations

### scenario.distribution.install-local-worktree — Installing a worktree from an admitted package

- GIVEN an admitted source or installed package and a Git worktree without a runtime or receipt
- WHEN the Host explicitly bootstraps that worktree through the local installation service or its deployed installer
- THEN the worktree receives a complete Framework, session entry with catalog, managed runtime and receipt naming the exact package identity
- AND every runtime check uses the worktree's own interpreter, so the installation stays valid without the provider's environment
- BUT no candidate status or run record is created and no capability or model is started

See [req.distribution.worktree-local-install](requirements.md#req.distribution.worktree-local-install).

### scenario.distribution.install-local-reuse — A verified installation is reused

- GIVEN a worktree with a verified local installation of the admitted package
- WHEN the Host verifies or ensures it again
- THEN it is reported verified without reinstalling, acquiring dependencies or rewriting the marker or receipt

### scenario.distribution.install-local-failure — Missing or stale state fails without a fallback

- GIVEN a worktree whose local installation is missing, incomplete, conflicting or of another package
- WHEN local verification, or an ensure without bootstrap, is requested
- THEN it fails and returns no installation
- BUT no implicit bootstrap happens, and no other worktree's or global runtime takes its place

See [req.distribution.no-runtime-fallback](requirements.md#req.distribution.no-runtime-fallback).

### scenario.distribution.install-local-bootstrap-failure — A failed bootstrap restores the worktree

- GIVEN an explicit bootstrap whose dependency acquisition, installation or final verification fails, or whose provider bytes changed while it waited for the lock
- WHEN the local installation service handles the failure
- THEN the owned files and receipt are restored and unrelated project bytes are kept
- AND no verified installation is returned
- BUT a fresh plan can install once the cause is fixed

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
- AND every public capability's runtime check runs with the runtime's own interpreter and reports that runtime as its environment and the pinned LangGraph version
- AND only then is the owner marker written and the runtime record returned

See [req.distribution.runtime-verified-before-use](requirements.md#req.distribution.runtime-verified-before-use).

### scenario.distribution.runtime-provision-failure — A failed creation leaves nothing marked as verified

- GIVEN a `create` action whose dependency acquisition or verification fails, or whose directory appeared after planning
- WHEN the provisioner reports the failure
- THEN the directory it was creating is removed, or the pre-existing one is refused rather than adopted
- AND no marker claims a verified runtime and no runtime record is returned

### scenario.distribution.runtime-rebuild-failure — A failed rebuild leaves the project without a runtime

- GIVEN an owned runtime planned for `rebuild`, whose rebuild then fails
- WHEN the installer handles the failure
- THEN the previous runtime is gone and the directory being built is removed
- AND the apply's rollback restores files and receipt but not the runtime
- AND later local verification fails until an installation succeeds
- BUT no marker claims a verified runtime

### scenario.distribution.launcher-managed-runtime — The installed launcher enters the managed runtime

- GIVEN a consumer project whose Framework is at `.concorde/framework` and whose verified runtime, with Concorde's owner marker, is at `.concorde/.venv`
- WHEN the installed launcher is started with another interpreter, even an ambient `python3` without LangGraph
- THEN it re-executes itself with the runtime's interpreter before reading its request
- AND a launcher already running inside that runtime is not re-executed
- AND the source checkout, which has neither layout, keeps the interpreter that started it

See [req.distribution.launcher-managed-runtime](requirements.md#req.distribution.launcher-managed-runtime).

### scenario.distribution.launcher-missing-runtime — A runtime without LangGraph is reported

- GIVEN an interpreter that cannot import LangGraph
- WHEN the launcher's runtime check runs
- THEN it fails with `missing_runtime`
