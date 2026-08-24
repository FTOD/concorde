
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

Authority remains split by artifact meaning: `spec.md` owns feature behavior; `design.md` records the
accepted feature realization; module and contract Markdown own architecture prose; Archify JSON owns
view structure; code owns implementation; and tests own executable evidence.

Read the root `design.md` as the accepted baseline and identify the proposed realization delta. Never
update it during planning or implementation; only the explicit Concorde hardening command may
promote a task-complete, user-approved milestone. Keep durable feature sources (`spec.md`,
`design.md`, `contracts/`, and `checklists/`) at the feature root. Write
this plan and its research, data model, runnable validation guide, and delivery evidence under the
feature's `implementation/` directory. That directory represents one temporal delivery attempt and
must not be mirrored by compatibility copies beside `spec.md`.
