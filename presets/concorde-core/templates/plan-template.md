
## Concorde Architecture Gate

Before the plan is complete, review the providing module's responsibility and boundary, its current
features and I/O contracts, every immediate submodule and its I/O contracts, relevant externals, and
their current-level organization. Identify affected module Markdown, contract definitions, Archify
JSON views, adjacent child feature refinements, and evidence. Keep deeper implementation details
behind stable navigation references.

Evaluate feature-owned diagrams explicitly. First preserve or plan at most one `role: core` Archify
`architecture` view when stable component participation and interaction would be materially clearer
visually. A sequence diagram cannot be the core view. Then preserve or plan `role: supplemental`
workflow, sequence, data-flow, or lifecycle views when narrower order, state, or movement questions
need them. Plan each descriptive Archify JSON source under the feature's
`diagrams/` directory, its declaration in `spec.md`, complete textual counterpart, governing contract
references, automatic feature-page embedding, deterministic validation/delivery, and generated-output
freshness. Feature diagrams remain explanatory and must not overload the module's canonical
`architecture.json` or become behavioral authority.

Authority remains split by artifact meaning: `tldr.md` orients (a self-contained summary that never
defines); `spec.md` owns feature behavior; the feature `design.md` records the accepted realization; module `module.md` (summary) and `design.md` (design reference) plus
contract Markdown own architecture prose; Archify JSON owns
view structure; code owns implementation; and tests own executable evidence.

Read the root `design.md` as the accepted baseline and identify the proposed realization delta;
when it still holds the placeholder, record "no accepted baseline" rather than inventing one. Read the
providing module's `module.md` as bounded context and open its `design.md` only for a specific
recorded detail, citing it. Never
update `tldr.md`, `spec.md`, the feature `design.md`, or a module `design.md` during planning or implementation; only the explicit Concorde hardening command may
promote a task-complete, user-approved milestone. Keep durable feature sources (`tldr.md`, `spec.md`,
`design.md`, `contracts/`, and feature-owned `diagrams/`) at the feature root. Keep every
requirements-quality checklist under `implementation/checklists/`. Write this plan and its research,
data model, runnable validation guide, and delivery evidence under the feature's `implementation/`
directory. That directory represents one temporal delivery attempt and must not be mirrored by
compatibility copies beside `spec.md`.

When the selected root is an immediate sub-feature, also read the Protocol v5 parent `tldr.md`,
`spec.md`, and `design.md` only as aggregate context. Plan and write exclusively beneath the selected child root.
Sibling summaries are navigation context; sibling bodies and all parent/sibling attempts are out of
scope unless the maintainer explicitly selects them in a separate lifecycle operation. Reject any
plan that creates a third feature level or duplicates a parent-owned invariant as child authority.
