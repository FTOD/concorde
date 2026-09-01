# Concorde extension

The extension registers five integration-neutral command surfaces:

- `speckit.concorde.init` exposes the Skills → Scripts → Workspace Files interaction model, proposes
  a minimal product-specific root without guessing product modules, writes only after explicit
  acceptance of an exact proposal, and reports an existing configured hierarchy as unchanged rather
  than comparing it with starter text.
- `speckit.concorde.impl.accept` verifies task completion, presents a digest-bound proposal for
  durable feature `implementation.md` (optionally amending the `design.md` of the module at which the
  feature is specified), presents attributed entries transiently while keeping `reflections.md` as
  their sole persisted authority, rejects copied `R-NNN` identifiers (`CONCORDE-ACCEPT-012`), and
  only after explicit approval promotes the proposal atomically and removes the temporal attempt;
  the reflection log is left byte-identical.
- `speckit.concorde.context` returns one bounded architectural level, including the module's
  `diagrams` list (every diagram beneath its `architecture/diagrams/`) and the project reflection
  log's path and the open entry count per feature when the log exists.
- `speckit.concorde.validate` deterministically validates the configured hierarchy, including the
  module `architecture/` layout (`CONCORDE-LAYOUT-010`/`-011`), module diagram references
  (`CONCORDE-VIEW-006`), hidden legends on maintained module and feature diagrams
  (`CONCORDE-VIEW-007`), and the shape of the project reflection log (`CONCORDE-REFLECT-001` to
  `-004`).
- `speckit.concorde.ask` tells the coding agent how to answer a Concorde workflow or framework
  question from cited installed guidance and bounded project sources without changing the workspace.

Features are created and selected through standard Spec Kit mechanisms rather than Concorde
commands. The normal `speckit.specify` phase creates a feature root at its canonical path inside the
hierarchy when `SPECIFY_FEATURE_DIRECTORY` names `<module directory>/features/NNN-<short-name>` or
`<parent feature root>/subfeatures/NNN-<short-name>`; Spec Kit persists that root in
`.specify/feature.json`, which is the only selection record. `speckit.concorde.validate` enforces
registration, canonical paths, and two-level containment afterwards.

The extension also provides the Protocol v8 selected-workspace adapter used by the preset's nine
normal command modifications. It resolves and validates the selected root before every
phase-sensitive step and reports its kind, durable and temporal paths, parent context, sibling
summaries, the `module.md` and `design.md` of the module at which the feature is specified
(`providing_module`) as navigation references, and `attempt_state`. The four operational
surfaces invoke the installed, standard-library Python runtime through project-relative paths.
`ask` is agent-followed Markdown and deliberately invokes no launcher or runtime verb. Target
projects need Python 3.11 or newer for operational surfaces; they do not need `uv` or third-party
Python packages.

A selected sub-feature uses its own durable/temporal paths and receives its parent's durable
`abstract.md`/`design.md`/`implementation.md` only as read-only aggregate context plus concise sibling summaries. Feature
containment remains distinct from adjacent-module `refines` links.

## Reflection triage agent assets

The extension also carries the canonical `reflection-triage/v1` orchestration body, model-neutral
investigator and implementer roles, a safe default configuration, thin Claude/Codex wrappers, and
the deterministic `scripts/python/reflections_queue.py` helper. These are support assets for Feature
005, not a sixth `speckit.concorde.*` command.

`concorde agent-assets preview|sync|verify|remove --integration <claude|codex>` renders and
reconciles the native project surfaces. Claude receives
`.claude/skills/reflections-triage/SKILL.md` and two `.claude/agents/*.md` roles; Codex receives
`.agents/skills/reflections-triage/SKILL.md` and two `.codex/agents/*.toml` roles. The generated
files share canonical bodies and contain no mandatory model or Concorde-checkout path.

Shared maintainer state lives under `.concorde/reflections/`: version-controlled `config.json`,
ignored plans, and ignored worktrees. The installer-owned
`.specify/concorde-agent-assets.json` receipt contains hashes only for generated projections.
Projection updates or removal touch a listed path only while its observed hash matches the receipt;
modified, legacy, inactive-integration, unrelated, and permission-policy files are preserved and
reported as conflicts when necessary.

Investigators are read-only and return complete plans to the parent. Implementers receive full plan
text and an explicit assigned worktree; the parent owns plan persistence, metadata, merge, and every
reflection status or note. Claude may also use native worktree isolation. Codex uses an explicit Git
worktree because its project custom-agent TOML has no per-agent worktree-isolation field.

Feature 005 owns these semantics and the deterministic operation. Feature 003 owns when installation
preview, apply, update, remove, release building, and self-hosting invoke and verify that operation.
