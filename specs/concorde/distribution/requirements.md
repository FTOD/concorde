# Distribution requirements

The Module-wide obligations of [Distribution](module.md). The [scenarios](scenarios.md) show them
in concrete situations.

## Build

### req.distribution.build-owned-outputs — The build writes only where it owns

The build SHALL write only inside `generated/protocol/`, `generated/workers/` and `generated/main-session/` and to `generated/build-manifest.json`.

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

Every invocation of the `concorde` command other than `spec-mcp`, `task` and `run` SHALL print exactly one JSON result envelope on standard output, except `--help`.

The exit status follows the envelope's status, so a caller that only checks the status and a caller
that reads the envelope reach the same conclusion.

## Installation

### req.distribution.installer-no-specs — The installer never writes Specs

The installer SHALL NOT create, modify or remove a registered Spec document, the registry or the
project configuration's Protocol binding.

### req.distribution.installer-fresh-guidance — Only current guidance is installed

The installer SHALL refuse to install main-session guidance whose rendered output is missing or
older than its sources.
