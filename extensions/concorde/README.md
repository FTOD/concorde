# Concorde extension

The extension registers seven integration-neutral command surfaces:

- `speckit.concorde.init` proposes a root specification hierarchy and writes only after explicit
  acceptance of an exact proposal.
- `speckit.concorde.feature.create` proposes a module-owned feature or one immediate sub-feature and
  starts its one canonical specification only after approval; sub-features cannot nest further.
- `speckit.concorde.feature.select` atomically selects an existing feature/sub-feature for the normal
  Spec Kit phases.
- `speckit.concorde.feature.harden` verifies task completion, presents a digest-bound durable-design
  proposal, and only after explicit approval promotes it and removes the temporal attempt.
- `speckit.concorde.context` returns one bounded architectural level.
- `speckit.concorde.validate` deterministically validates the configured hierarchy.
- `speckit.concorde.ask` tells the coding agent how to answer a Concorde workflow or framework
  question from cited installed guidance and bounded project sources without changing the workspace.

The extension also provides the Protocol v3 selected-workspace adapter used by the preset's nine normal command
replacements. The six operational surfaces invoke the installed, standard-library Python runtime
through project-relative paths. `ask` is agent-followed Markdown and deliberately invokes no launcher
or runtime verb. Target projects need Python 3.11 or newer for operational surfaces; they do not need
`uv` or third-party Python packages.

A selected sub-feature uses its own durable/temporal paths and receives its parent's durable
`spec.md`/`design.md` only as read-only aggregate context plus concise sibling summaries. Feature
containment remains distinct from adjacent-module `refines` links.
