# Distribution requirements

The Module-wide obligations of [Distribution](module.md). Each is stated once; the
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

### req.distribution.owned-retirement — Only owned outputs are removed

The build SHALL remove a file only when its bytes equal the digest the previous build manifest recorded for it.

### req.distribution.manifest-complete — Every output is recorded

A successful build SHALL record in its build manifest every output it wrote and every source any output was rendered from.

### req.distribution.private-source-entry — The source session entry stays private

The build SHALL write this checkout's session entry only to `generated/session/pi/concorde-session.ts`, outside Pi's discovery directories.

### req.distribution.operation-guidance-fresh — The catalog matches its sources

Build checking and the package check SHALL report every difference between a session entry's catalog and the capability guidance, request schemas and Operation catalog it was rendered from.

### req.distribution.protocol-only-bundle — The Protocol copy holds only the Protocol

The build SHALL render the Protocol assets from the Protocol text alone.

### req.distribution.single-instructions — One rendered copy of each Agent's instructions

The build SHALL render each Agent's instructions to exactly one output.

## Launcher

### req.distribution.catalog-dispatch — The launcher runs only catalog capabilities

The launcher SHALL run a capability request only for a name that the Operation catalog declares as a public capability.

### req.distribution.launcher-sigterm-cancels — SIGTERM cancels like an interrupt

The launcher SHALL handle SIGTERM as an interrupt and print its result envelope before exiting.

The Host decides what the interrupt cancels and records it; committed effects are not rolled back.

### req.distribution.launcher-managed-runtime — Installed capabilities run in the managed runtime

In a consumer project the launcher SHALL run capabilities with the managed runtime's interpreter, whatever interpreter started it.

## Installation

### req.distribution.no-silent-protocol-rewrite — Installing never rebinds the Protocol

Installation and update SHALL NOT change a project's Protocol binding.

A project adopts a new Protocol copy only through `concorde-configure`, which Request admission
provides.

### req.distribution.source-only-assets — Source-only files never ship

The installed layout SHALL NOT contain any file that Pi session classifies as source-only.

### req.distribution.receipt-ownership — Only unchanged owned files are replaced

Installation SHALL replace or remove a file only when its current bytes equal the bytes the installation receipt recorded for it.

### req.distribution.root-block-ownership — Root files are owned only within the block

Installation SHALL own a root instruction file only within its marked Concorde block.

### req.distribution.no-surrounding-text-rewrite — Text around the block stays

Installation SHALL NOT change any byte of a root instruction file outside its owned block.

The one whole-file effect is removing a file that the receipt records the installer created for its
block, when removing the block leaves it empty.

### req.distribution.rollback-on-failure — A failed apply restores the files it changed

A failed installation apply SHALL return every file it touched, and the receipt, to its previous bytes and mode.

A managed runtime is not a file in this sense: a runtime the apply created is removed, and a runtime
it was rebuilding is lost, as [runtime-rebuild-failure](scenarios.md#scenario.distribution.runtime-rebuild-failure)
states.

### req.distribution.stale-plan-refused — Plans apply only to the state they were made from

Applying SHALL refuse a plan when a recomputed plan, a root file or the package identity differs from what the preview saw.

### req.distribution.pi-only-install — Pi is the only client

Installation SHALL install the Pi session entry as Concorde's only client integration, without Skills or any other client's files.

### req.distribution.worktree-local-install — A verified installation is complete and exact

Local installation verification SHALL report a worktree as verified only when its Framework files, session entry, managed runtime and receipt all belong to the exact admitted package identity.

### req.distribution.no-runtime-fallback — No substitute environment

Distribution SHALL NOT substitute another worktree's, the primary checkout's or a global environment for a missing or failed local installation or managed runtime.

### req.distribution.single-installer — One installer per target at a time

An applying installer SHALL refuse to start while another applying installer holds the same target.

## Runtime

### req.distribution.runtime-verified-before-use — The runtime is marked only after it is checked

Provisioning SHALL write the managed runtime's owner marker only after every public capability's runtime check passed inside that runtime.
