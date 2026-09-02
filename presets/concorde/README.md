# Concorde preset

This preset composes the normal Spec Kit lifecycle with Concorde's module-centered specification
profile.

At priority 10 it contributes four templates: the appended feature-design, plan, and tasks layers,
plus the project-wide reflection-log template. It replaces the installed instructions for nine
normal lifecycle commands and adds `speckit.fast-loop`. Complete command layers resolve Protocol 12
before any path-sensitive work.

Every module recursively owns one `architecture.md`. It defines that level's responsibility,
boundary, immediate module/feature inventory, typed architecture entities, directed relationships,
representative interactions, and optional architecture-owned diagrams. Child modules live directly
under `modules/<name>/` and repeat the same shape.

Every level-local feature is one direct `features/<NNN-name>.md` file. That file is the complete
capability specification: outcome, scope, usage, scenarios,
requirements, embedded provided/required interfaces, failures, related-feature semantics, and an
Architecture Zoom over entity IDs from the providing module or its ancestry. Features relate by
stable IDs; they never contain other features. Existing `contract.*` IDs may remain interface
identities, but no separate interface document is created.

Source code is implementation authority. Tests and deterministic checks are evidence. Planning,
research, tasks, checklists, and validation evidence live only in the project-control workspace
`.concorde/attempts/<stable-feature-id>/`. The tracked process-memory authority is
`.concorde/reflections/log.md`; reflection-triage configuration shares that directory while its plans
and worktrees remain disposable. New reflection IDs are allocated atomically from the log's
high-water marker. Reflection-triage/v3 removes only validated merged `small` `fast-loop` entries;
all other entries retain maintainer disposition. Implementation tasks may reconcile architecture/feature intent alongside code/tests when the
task explicitly owns and traces that change. Successful Concorde delivery validates the completed
state and removes exactly the selected attempt; it authors no durable narrative.

Maintained diagram sources belong to modules under `diagrams/`, have complete textual counterparts
in `architecture.md`, and remain explanatory. Every source uses `meta.legend.mode: hidden`; declared
outputs resolve uniquely below `generated/`. Generated pages and diagram outputs are reproducible
projections, never specification authority.

The installed Concorde extension supplies the Protocol 12 workspace adapter and five
framework-specific commands for initialization, context, validation, delivery, and grounded
questions. Normal Spec Kit selection remains the only feature-selection record.
