# Distribution design notes

The reasons behind the design summarized in the [Distribution](module.md) entry: the renderer, the
build manifest, the package check, the launcher, installation and the managed runtime, and the
honest limits. Exact shapes are in the [interfaces](interfaces.md); installation step by step is in
[Installing and updating](installation.md).

## One renderer for two layouts

The **package** is described by `concorde.json`: its version, the package roots that ship, the
launcher and runtime lock, and the installation layout. The **build renderer** is a pure function
from the package's sources to a set of outputs, each with the exact list of sources that produced
it. The same function renders two layouts: the private layout of this checkout and the installed
layout, in which every generated path lies under `.concorde/framework/` and the session entry lies
under `.pi/extensions/`. Because both come from one renderer, an installed catalog cannot drift from
the one tested in the checkout.

The build renders each Agent's instructions once, under `generated/native/`, from the Agent's
[definition](../agents/module.md#concept.agents.definition) and the shared native rules. It renders
each [session entry](../session/module.md#concept.session.session-entry) with its
[capability catalog](../session/module.md#concept.session.catalog) from the Operation catalog, the
capability guidance and the registered request schemas, and it calls Pi session's projector for the
Task subagent files. It renders the Protocol assets from the Protocol text alone, so the Protocol
copy carries only the Protocol, and it exports the registered request and record schemas into a
separate file. The build evaluates schema sources in its own process without bytecode caches, so
the recorded source bytes are exactly what produced them, and it starts no process and uses no
network.

## The build manifest

The **build manifest** records the digest of every source the build read, including the Python
sources of Agents, capability modules and the Pi extension code that the outputs depend on, and the
digest of every output. It is the one agreement between the build and the parts of Concorde that
must not use stale outputs: Request admission refuses model-backed work, Task context refuses to
load an Agent's instructions and Pi session refuses to select a candidate, each when a recorded
source no longer matches. That check only recomputes source digests, so it is cheap enough to run
before every model-backed request. `build --check` re-renders everything in memory and compares
bytes, so it also catches a hand-edited output. The manifest's shape and the meaning of freshness
are the [build manifest contract](interfaces.md#contract.distribution.build-manifest).

Writing is guarded the same way. The build owns only its declared locations under `generated/` and
the `.pi/` files it renders. It removes an output it no longer produces only when the file's bytes
match the digest the previous manifest recorded, and it refuses to overwrite a `.pi/` file whose
bytes it did not write. Any unknown, modified or linked file stops the whole write before anything
changes, so old outputs disappear safely and a file the developer created is never deleted.

## Why the package check is a configured check

`validate` is Spec tooling's structural check of Specs; it must not reach into the package it was
shipped in. Whether the package builds and is current is Distribution's own promise, so it is a
configured check owned here: Check execution runs it in its read-only boundary, it reports findings
attributed to this Module, and a project that is not a Concorde source checkout simply does not
configure it. Declaration checks of Operations and Agents are not repeated here: the build renders
from the Operation catalog and the Agent definitions, and a declaration their owners' loaders refuse
fails the build.

## Running a capability

The **launcher** imports the Operation catalog and gives admission everything admission must not
import itself: the catalog's capability declarations, Operations' dispatcher that runs an admitted
request's declared entry point, the local installation service and, when a session selection is
active, the selection record that Pi session's selection service verified, as the run's session
provenance. This keeps Request admission free of Operations, Pi session and Distribution code while
it still sees the facts it checks. The launcher has two other entries: `--runtime-check`, an
offline probe the runtime provisioner runs for every capability, and `--native-context`, which runs
one native preparation or acceptance step of Agent execution for Pi session's tool and the native
workflow steps.

The launcher's re-entry into the managed runtime is why an installed project never runs a capability
with whatever happens to be installed globally. In this checkout the launcher keeps the interpreter
that started it, the checkout's own `.venv`.

The **command-line interface** is the one command surface of the package. Most subcommands only
route to the owning Module's service and add nothing but the envelope, so a behaviour always has one
owner. `status` options that change coordination are refused outside the primary checkout, and
`docsite` requires an isolated worktree unless the caller explicitly allows the primary one.

## Installing and running elsewhere

The **installer** installs one package into one **consumer project**. It decides every file by
comparing three things: the bytes it wants to write, the bytes on disk, and the bytes the
**installation receipt** says it wrote last time. Only a file whose current bytes are exactly what it
wrote is its to replace or remove; anything else is a conflict. The receipt is what makes an update
safe without a merge tool. Shared root files such as `AGENTS.md` are owned only within one marked
block, so the developer's own text around it is never rewritten. The installer also places the
**Protocol copy**, the Protocol text agents are given as project files; placing it never changes the
project's binding to a Protocol version, because receiving new software and agreeing to a new
specification language are separate decisions. Files that Pi session classifies as source-only
never ship.

The **runtime provisioner** creates and verifies the **managed runtime**: a virtual environment with
the one LangGraph version the runtime lock pins and the Pi dependencies the Pi package lock pins. It
marks the runtime as verified only after every public capability's runtime check passed inside that
environment and reported that environment as its own.

The **local installation service** lets the Host verify that a worktree carries a complete
installation of exactly the package it admitted and, only with an explicit bootstrap request,
install one first. The package identity is the version plus a digest over every file the installer
would write and a digest of the installed build manifest, so a version label alone proves nothing.
The service creates no worktree, starts no capability, grants nothing and records no candidate
status.

## Limits and honest gaps

A runtime rebuild removes the previous environment before creating the new one. If the rebuild
fails, the project has no managed runtime until the installer runs again successfully; nothing is
restored, and the installation's rollback of files and receipt does not bring it back. Callers must
not read the absence of a success record as a recovered runtime.

The installation lock excludes other installers only, not editors or running capabilities, so the
caller keeps a worktree quiet while installing and verifying it. The build, the installer and the
package check run with the developer's own privileges; Distribution sandboxes nothing and enforces
no Agent boundary.
