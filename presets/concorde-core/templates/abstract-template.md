# Feature Abstract: [FEATURE NAME]

`[feature.stable.id]` · specified at `[module.id]` · about [N] minutes. This page is enough to
understand what the feature does, how it is built, and how it works; the links at the end only
redirect you when you want more.

<!--
  Write this file together with design.md and keep it self-contained: a programmer or coding agent must
  get the purpose, functionality, basic structure, and logic from this page alone, in under 15
  minutes (at most 3,000 body words). Exactly these five H2 sections, in this order. Summarize
  design.md; never state a requirement, scope boundary, or success criterion design.md does not state.
  Links redirect; they are never required reading. Clarification updates this page whenever an
  accepted answer changes something it summarizes. Acceptance never writes it.
-->

## Purpose

[One or two short paragraphs: the outcome the feature achieves and for whom.]

## Functionality

[What the feature does and does not do: its operations, surfaces, parts, and boundaries. Use a
Markdown table for an inventory. End with a "**Not part of this feature**" sentence.]

## Structure

[The participating parts and how they collaborate. Link the feature's declared core diagram as
<a href="/architecture/<output-basename>.html">…</a> (name its maintained source under diagrams/),
or the parent's core view or the level view when this feature declares none; a fenced ```text sketch
is welcome.]

## Logic

[First the main flow as an ordered list. Then:]

**Rules the implementation must keep**

- [One rule per bullet, ending with the design.md requirement IDs it summarizes, e.g. (FR-001, FR-004).]

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md)
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md)
- **Contracts** — [contracts/](contracts/) [when the directory exists]
- **The level this feature belongs to** — the module summary `module.md` [relative link]
- **Parent or sub-features** — [links when applicable]
