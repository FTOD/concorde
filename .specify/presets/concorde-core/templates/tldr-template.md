# TL;DR: [FEATURE NAME]

`[feature.stable.id]` · specified at `[module.id]` · about [N] minutes. This page is enough to
understand what the feature does, how it is built, and how it works; the links at the end only
redirect you when you want more.

<!--
  Write this file together with spec.md and keep it self-contained: a programmer or coding agent must
  get the purpose, functionality, basic structure, and logic from this page alone, in under 15
  minutes (at most 3,000 body words). Exactly these five H2 sections, in this order. Summarize
  spec.md; never state a requirement, scope boundary, or success criterion spec.md does not state.
  Links redirect; they are never required reading. Clarification updates this page whenever an
  accepted answer changes something it summarizes. Hardening never writes it.
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

- [One rule per bullet, ending with the spec.md requirement IDs it summarizes, e.g. (FR-001, FR-004).]

## Read Next

- **Exact requirements, scenarios, and success criteria** — [spec.md](spec.md)
- **How the accepted implementation realizes this feature** — [design.md](design.md)
- **Contracts** — [contracts/](contracts/) [when the directory exists]
- **The level this feature belongs to** — the module summary `module.md` [relative link]
- **Parent or sub-features** — [links when applicable]
