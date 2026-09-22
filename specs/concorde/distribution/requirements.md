# Distribution requirements

These are the Module-wide obligations of [Distribution](module.md). Each is stated once; the
[scenarios](scenarios.md) show them in concrete situations.

## Build

### req.distribution.build-idempotent — Identical sources give identical outputs

`build` and `build --check` SHALL produce byte-identical outputs and manifest from unchanged sources.

### req.distribution.build-no-io — The build performs no network or process I/O

Rendering the build SHALL NOT start a process or use the network.

Schema sources are evaluated inside the build's own process from the checkout's files, without
bytecode caches, so that the recorded source bytes are exactly what produced the schemas.

### req.distribution.one-worktree-build — A build writes only its own checkout

A build SHALL write only into the checkout that holds its sources.

There is no option to write another root; the installer uses the pure renderer and performs its
own writes under its receipt.

### req.distribution.fresh-instructions — Model work never uses a stale build

Starting a model-backed capability or loading an Agent's instructions SHALL fail when a recorded build source differs from the build manifest.

Both checks use `verify_fresh`, which fails with `stale_build`. Host capabilities load no generated
instructions and are not stopped by this check at admission.

### req.distribution.owned-retirement — Only owned outputs are removed

The build SHALL remove a file only when its bytes equal the digest the previous build manifest recorded for it.

### req.distribution.checkout-skills-user-invoked — The source session entry stays private

The build SHALL write this checkout's session entry only to `generated/session/pi/concorde-session.ts`, outside Pi's discovery directories.

### req.distribution.operation-guidance-fresh — The catalog matches its sources

Build checking and package validation SHALL report every difference between a session entry's catalog and the capability guidance, request schemas and capability inventory it was rendered from.

## Session integration

### req.distribution.pi-session-public-only — The tool offers only public capabilities

The `concorde` tool SHALL accept exactly the capabilities listed in its catalog, which are the eleven public capabilities.

### req.distribution.launcher-sigterm-cancels — SIGTERM cancels like an interrupt

The launcher SHALL handle SIGTERM as an interrupt and print its result envelope before exiting.

The Host decides what the interrupt cancels and records it; committed effects are not rolled back.

### req.distribution.private-selection — Selections name exact current bytes

Session selection SHALL refuse any entry, catalog, launcher or source path that is missing, aliased, outside the candidate or different from the candidate's current build.

### req.distribution.no-runtime-fallback — No substitute environment

Distribution SHALL NOT substitute another worktree's, the primary checkout's or a global environment for a missing or failed local installation, managed runtime or session selection.

### req.distribution.source-only-assets — Source-only files never ship

Installation SHALL NOT deploy the maintenance-worker definition, the source user session prompts, the coordinator extension, the brief lifecycle extension or the maintenance extension.

## Installation

### req.distribution.no-silent-protocol-rewrite — Installing never rebinds the Protocol

Installation and update SHALL NOT change a project's `protocol` binding in `.concorde/config.json`.

A project adopts a new Protocol copy only through `concorde-configure` with `accept_protocol`.

### req.distribution.receipt-ownership — Only unchanged owned files are replaced

Installation SHALL replace or remove a file only when its current bytes equal the bytes the installation receipt recorded for it.

### req.distribution.root-block-ownership — Root files are owned only within the block

Installation SHALL own a root instruction file only within its marked Concorde block.

### req.distribution.no-surrounding-text-rewrite — Text around the block stays

Installation SHALL NOT change any byte of a root instruction file outside its owned block.

The one whole-file effect is removing a file that the receipt records the installer created for its
block, when removing the block leaves it empty.

### req.distribution.rollback-on-failure — A failed apply restores what it changed

A failed installation apply SHALL return every file it touched, and the receipt, to its previous bytes and mode.

A runtime rebuild is outside this rollback: the previous runtime was deleted before rebuilding.

### req.distribution.stale-plan-refused — Plans apply only to the state they were made from

Applying SHALL refuse a plan when a recomputed plan, a root file or the package identity differs from what the preview saw.

### req.distribution.pi-only-install — Pi is the only client

Installation SHALL install the Pi session entry as Concorde's only client integration, without Skills or any other client's files.

### req.distribution.worktree-local-install — A verified installation is complete and exact

Local installation verification SHALL report a worktree as verified only when its Framework files, session entry, managed runtime and receipt all belong to the exact admitted package identity.

## Runtime

### req.distribution.runtime-verified-before-use — The runtime is marked only after it is checked

Provisioning SHALL write the managed runtime's owner marker only after every public capability's runtime check passed inside that runtime.

### req.distribution.launcher-managed-runtime — Installed capabilities run in the managed runtime

In a consumer project the launcher SHALL run capabilities with the managed runtime's interpreter, whatever interpreter started it.

## Configuration

### req.distribution.configure-atomic — Configuration changes are all or nothing

`concorde-configure` SHALL leave `.concorde/config.json` unchanged when the request is invalid, the project cannot be loaded or the write fails.

## Development

### req.distribution.test-evidence — Test runs record why and on what they ran

The pytest evidence plugin SHALL record each run's reason, scope, phase, attempt and input fingerprints in its JSON report.

Callers that pass none of these get `manual` and `unspecified`. The report keeps discovery,
queueing and execution times apart and never presents summed parallel test time as elapsed time.
