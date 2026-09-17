# Installation service

### Configuration compatibility

The canonical Module template and Scenario fragment and the mandatory Spec document format are
authored under `protocol/` and distributed with the independent standard. The `templates/` entry
links to those sources. Plan and task starters remain Framework workflow assets; they
are not additional Protocol Spec kinds.

The Framework identifies its supported project configuration as Profile 14. Initialization writes
`.concorde/config.json` with `profile_version: 14`, the `registry` path, an accepted Protocol
`version` and manifest `digest` under `protocol`, and the typed `capability_configuration` for the
project's Pi worker model, thinking level, timeout and per-worker overrides; the `protocol` binding names the Protocol copy the installer placed
under `.concorde/protocol/`, which initialization never creates. Its registry uses JSON schema version 5. Profile 14 and registry
schema 5 are Framework compatibility and storage versions; Spec Protocol 8.0.0 identifies the
independent specification standard. Installation and initialization preserve these separate roles.

### Main routing view

Select `module.distribution` for manifest inventory, canonical Skill/role rendering, the build's
agent surface ownership, and managed Python or viewer provisioning. Select `module.spec` when the
requested behavior is project initialization or Protocol binding rather than installation
ownership. Installation distributes `scripts/run-ua-graph-viewer.py` and provisions its pinned official
viewer runtime; the launch interface and graph admission behavior are owned by `module.views` and
documented in [Understand Anything viewer](../views/viewer.md). Native package acquisition and
recovery remain on `module.distribution`; starting the viewer is a separate developer action.

## Precise specifications

The Distribution Module owns the exact obligations and interface details in [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
