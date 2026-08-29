
## Concorde Architecture Gate

Before the plan is complete, review the providing module's responsibility and boundary, its current
features and I/O contracts, every immediate submodule and its I/O contracts, relevant externals, and
their current-level organization. Identify affected module Markdown, contract definitions under
`architecture/contracts/`, the level's diagrams under `architecture/diagrams/`, adjacent child
feature refinements, and evidence. Keep deeper implementation details
behind stable navigation references.

Evaluate feature-owned diagrams explicitly. First preserve or plan at most one `role: core` Archify
`architecture` view when stable component participation and interaction would be materially clearer
visually. A sequence diagram cannot be the core view. Then preserve or plan `role: supplemental`
workflow, sequence, data-flow, or lifecycle views when narrower order, state, or movement questions
need them. Plan each descriptive Archify JSON source under the feature's
`diagrams/` directory, its declaration in `design.md`, complete textual counterpart, governing contract
references, automatic feature-page embedding, deterministic validation/delivery, and generated-output
freshness. Feature diagrams remain explanatory and must not overload the module's level views
under `architecture/diagrams/` or become behavioral authority.

Authority remains split by artifact meaning: `abstract.md` orients (a self-contained summary that never
defines); feature `design.md` owns behavior; feature `implementation.md` records the accepted realization; module `module.md` (summary) and `design.md` (design reference) plus
contract Markdown own architecture prose; Archify JSON owns
view structure; code owns implementation; and tests own executable evidence.

Record every specification, architecture, cross-feature, or guidance problem planning cannot resolve
as an entry in the project reflection log (`workspace.reflections`, the one maintained file a phase
may append to) and list those entries in this gate; never resolve them by editing a durable document
or another feature's sources.

Read root `implementation.md` as the accepted baseline and identify the proposed realization delta;
when it still holds the placeholder, record "no accepted baseline" rather than inventing one. Read the
providing module's `module.md` as bounded context and open its `design.md` only for a specific
recorded detail, citing it. Never
update `abstract.md`, feature `design.md`, feature `implementation.md`, or a module `design.md` during
planning or implementation; only the explicit Concorde acceptance command may promote a task-complete,
user-approved milestone. Keep durable feature sources (`abstract.md`, `design.md`,
`implementation.md`, `contracts/`, and feature-owned `diagrams/`) at the feature root. Keep every
requirements-quality checklist under `attempt/checklists/`. Write this plan and its research,
data model, runnable validation guide, and delivery evidence under the feature's `attempt/`
directory. That directory represents one temporal delivery attempt and must not be mirrored by
compatibility copies beside `design.md`.

When the selected root is an immediate sub-feature, also read the Protocol v7 parent `abstract.md`,
`design.md`, and `implementation.md` only as aggregate context. Plan and write exclusively beneath the selected child root.
Sibling summaries are navigation context; sibling bodies and all parent/sibling attempts are out of
scope unless the maintainer explicitly selects them in a separate lifecycle operation. Reject any
plan that creates a third feature level or duplicates a parent-owned invariant as child authority.
