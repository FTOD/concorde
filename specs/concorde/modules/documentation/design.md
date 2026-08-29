# Design Reference: Documentation

This reference explains and justifies the Documentation module. Responsibility, boundary, the level
view, and the five boundary contracts remain owned by `module.md`, `architecture.json`, and the
contract documents under `contracts/`.

## Implementation Notes

### Docsite realization

The module is realized by the private TypeScript Docusaurus project under `docsite/`. It publishes a
read-only project model from two maintained source roots without creating a second content
authority: `specs/` supplies architecture sources plus durable feature specifications and accepted
realizations, and `docs/` supplies project-authored guidance. A shared registry
(`docsite/plugins/concorde-content/registry.ts`) classifies those inputs into source collections and
presents them through three navigation families: Architecture, Documentation, and Features. The
Documentation collection reads `docs/**/*.md` directly; Architecture and Features use ignored
projections under `docsite/.generated/content/` because separate Docusaurus content-plugin instances
cannot safely share the same physical `specs/` loader root.

Within the plugin, `diagrams.ts` owns Archify declaration discovery and safe normalized mappings,
`links.ts` owns strict Markdown link mapping (a `.md` link must resolve to included content; other
targets are treated as assets), `manifest.ts` and `validation.ts` own the build manifest and
publication gate, and `routes.ts` owns logical routes. `docsite/scripts/render-diagrams.ts` adapts
the officially installed project-local Archify 2.16 skill and atomically promotes complete delivery
sets under the ignored `generated/architecture/` tree; `prepare-publication.ts` orders diagram
delivery before registry validation and materialization; the preview and production wrappers invoke
that shared preparation before Docusaurus runs. Production output is rendered into a fresh candidate
and promoted to `docsite/build/` only after source, route, rendering, and manifest validation
succeeds.

### Archify renderer contract (bounded summary)

`contract.documentation.archify-renderer`

- **Role / flow**: required, bidirectional.
- **Provider**: external Archify.
- **Representation**: commonly adopted Archify architecture JSON schema and generated HTML contract.
- **Guarantees required**: valid maintained JSON produces deterministic, self-contained diagram output.
- **Failure**: renderer diagnostics are preserved and publication stops for the affected view.
- **Evidence**: both maintained architecture views pass all 9 Archify showcase checks; disposable
  deliveries are recreated under ignored `generated/architecture/`, while durable attempt evidence is
  recorded in `specs/concorde/features/002-create-project-docsite/design.md`.

The other four contracts are summarized in `module.md` and defined in full under `contracts/`.

### Evidence status

The publication feature is implemented. Its locked dependency installation, validation interface,
two-root/three-view source discovery, strict link mapping, permanent feature specification and
realization projection, sandboxed Archify embedding, local search, accessible presentation,
schema-valid manifest, atomic promotion, repeatability, and source immutability all have executable
evidence in `docsite/tests/` and
`specs/concorde/features/002-create-project-docsite/design.md`. Browser containment
and light/dark perceptual review of the current root and Documentation artifacts remain pending
because Chrome/Chromium is unavailable in the validation environment; structural checks are not
treated as perceptual evidence.

## Design Rationale

- Two roots, one authority each: `docs/` and `specs/` are read where they live, and generated pages
  link canonical sources instead of copying normative text, so the site cannot drift into a second
  authority.
- A publication gate rather than best effort: identities, links, and routes are validated, every
  declared view must be deliverable, provenance and the manifest are deterministic, and the last
  successful site survives a failed build.
- Temporal `attempt/` artifacts are excluded so the site shows only durable intent and
  accepted realizations.
- Archify keeps ownership of schema validation and standalone HTML rendering and Docusaurus keeps
  ownership of the generated site; Documentation only orchestrates, embeds, and validates.

## Alternatives Considered

- Sharing one physical `specs/` loader root between separate Docusaurus content-plugin instances was
  rejected because it is not safe; Architecture and Features use ignored projections instead.
- Keeping the documentation collection identifiers while only changing file globs was rejected in the
  current document-model attempt because manifest consumers would see pages whose provenance no
  longer matched their source name.
- No other alternatives have been recorded for this module yet.

## Decision Log

- 2026-08-27 — Adopted the module summary / design reference split and renamed feature design.md to
  implementation.md (feature.concorde.workflow); this module's `module.md` was rewritten to the
  summary shape and its renderer narrative and evidence status moved here. The same attempt proposes,
  pending hardening: the feature-realization collection becomes `feature-implementations`
  (the feature-root `implementation.md` beside feature `design.md`, paired by directory, with `abstract.md` as the landing page), module `design.md` joins the
  Architecture collection as kind `module-design` linked from the module page, and Build Manifest
  moves from v4 to v5.
- 2026-08-27 — Switched diagram delivery to the project-local Archify 2.16 skill.
- 2026-08-26 — Rendered Archify diagrams during docsite builds; published the site to GitHub Pages.
