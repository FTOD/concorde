# Distribution requirements

The Module-wide obligations of [Distribution](module.md). The [scenarios](scenarios.md) show them
in concrete situations.

## Build

### req.distribution.build-owned-outputs — The build writes only where it owns

The build SHALL write only inside `generated/protocol/`, `generated/workers/`, `generated/main-session/` and `generated/workflows/` and to `generated/build-manifest.json`.

Other locations under `generated/` belong to other producers, and the build never judges or removes
them. Each new prompt root adds its own owned location in the same change.

### req.distribution.build-check-read-only — Checking the build writes nothing

`build --check` SHALL NOT write, create or remove any file.

### req.distribution.build-reachable — Every prompt file is rendered

The build SHALL fail when a Markdown file under `prompts/` is included by no prompt root.

### req.distribution.no-stale-copy — A stale build is never copied

The Protocol copy writer SHALL refuse to copy the Protocol from a package whose build manifest
records a source that is missing or changed, or whose rendered asset differs from the tracked
manifest.

## Command line

### req.distribution.one-envelope — One envelope per command

Every invocation of the `concorde` command other than `spec-mcp`, `task`, `run`, `workflow` and `issues` SHALL print exactly one JSON result envelope on standard output, except `--help`.

The exit status follows the envelope's status, so a caller that only checks the status and a caller
that reads the envelope reach the same conclusion.

## Installation

### req.distribution.receipt-complete — The receipt names every owned file

The installer's receipt SHALL list every file Concorde owns in the project, whether or not this install wrote it, and apart from them the project files it only amends.

### req.distribution.installer-own-permissions — The installer adds only its own permission rules

The installer SHALL change the project's `.claude/settings.json` only by adding the missing permission rules its workflows need and removing the rules it recorded in its receipt and no longer ships.

Every other setting, including rules the developer wrote that equal one of Concorde's, stays as
it was; a file that is not a JSON object is refused before anything is written.

### req.distribution.own-python — Concorde runs in its own Python environment

The installed `concorde` command SHALL run Concorde only with the interpreter of its own environment under `.concorde/framework/python/`, ignoring the caller's Python path settings and user site-packages.

### req.distribution.installer-no-specs — The installer never writes Specs

The installer SHALL NOT create, modify or remove a registered Spec document, the registry or,
except in update mode, the project configuration's Protocol binding.

### req.distribution.update-unvalidated — An update is validated before anything merges

`concorde update` SHALL leave the project Concorde unvalidated, reported as an error by every validation in the primary worktree, until a validation passes.

### req.distribution.installer-fresh-guidance — Only current guidance is installed

The installer SHALL refuse to install main-session guidance whose rendered output is missing or
older than its sources.

### req.distribution.installer-locked-pi-runtime — Only the locked pi runtime is installed

The installer SHALL install the pi runtime only with `npm ci --ignore-scripts` from the `package-lock.json` the package ships.

`npm ci` installs exactly the versions the lockfile names and refuses a package whose integrity
hash differs, and no install script of a dependency runs on the developer's machine.

### req.distribution.installer-pinned-d2 — Only the pinned d2 is installed

The installer SHALL place a `d2` program only from an archive whose SHA-256 equals the one `concorde.json` pins for the platform.

The docsite renders the Specs' diagrams with it. The installer fetches and checks it before writing
anything else, so a failed or tampered download leaves the project untouched.
