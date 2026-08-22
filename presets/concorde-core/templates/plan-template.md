
## Concorde Architecture Gate

Before the plan is complete, review the providing module's responsibility and boundary, its current
features and I/O contracts, every immediate submodule and its I/O contracts, relevant externals, and
their current-level organization. Identify affected module Markdown, contract definitions, Archify
JSON views, adjacent child feature refinements, and evidence. Keep deeper implementation details
behind stable navigation references.

Evaluate feature-owned diagrams explicitly. Preserve any diagram already required by `spec.md`; add
one when component participation, ordered invocation, boundary crossings, state, or data flow would
be materially clearer visually. Plan the descriptive Archify JSON source under the feature's
`diagrams/` directory, its declaration in `spec.md`, complete textual counterpart, governing contract
references, automatic feature-page embedding, deterministic validation/delivery, and generated-output
freshness. A feature diagram is supplemental and must not overload the module's canonical
`architecture.json`.

Authority remains split by artifact meaning: `spec.md` owns feature behavior, module and contract
Markdown own architecture prose, Archify JSON owns view structure, code owns implementation, and tests
own executable evidence.

Keep durable feature intent (`spec.md`, `contracts/`, and `checklists/`) at the feature root. Write
this plan and its research, data model, runnable validation guide, and delivery evidence under the
feature's `implementation/` directory. That directory represents one temporal delivery attempt and
must not be mirrored by compatibility copies beside `spec.md`.
