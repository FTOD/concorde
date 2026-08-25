---
title: Contributing to the Docsite
sidebar_position: 2
---

# Contributing to the Docsite

The docsite is a read-only publication system, not a content-authoring authority. It consumes two
maintained roots—`docs/` and `specs/`—and presents three navigation families: Documentation,
Architecture, and Features.

The complete publication behavior is specified by
[Feature 002](../../specs/concorde/features/002-create-project-docsite/spec.md).

## Know which sources are eligible

| Published collection | Maintained inputs | Public route family |
|---|---|---|
| Documentation | Every regular `docs/**/*.md` file | `/docs` |
| Architecture | Every `specs/**/module.md` and `specs/**/contracts/**/contract.md` | `/architecture` |
| Feature specifications | Every canonical `specs/**/spec.md` | `/features` |
| Feature designs | Every durable `specs/**/design.md` paired with a feature specification | `/features` |

Symbolic links are not followed. Plans, tasks, requirements checklists, research, technical models,
quick-start evidence, and other files below `implementation/` are intentionally excluded from the
Features collection. Their presence under `specs/` does not make them permanent project intent.

Do not copy canonical content into `docsite/`. Docusaurus configuration, components, formatting, and
build logic live there; project explanations live in `docs/`; architecture and feature authorities
live in `specs/`.

## How a build works

A preview and a production build use the same inclusion, routing, and validation rules:

1. The source registry discovers eligible files and records deliberate exclusions.
2. Declared Archify sources are validated and their fresh generated deliveries are resolved.
3. Disposable Docusaurus content is materialized under `docsite/.generated/content/`.
4. Docusaurus renders a candidate site.
5. Candidate pages, routes, links, provenance, and the build manifest are validated.
6. Only a successful candidate is promoted to `docsite/build/`.

Because the generated Architecture and Features pages are projections, never edit files under
`docsite/.generated/` or `docsite/build/`. Correct the maintained source and rebuild.

## Author a documentation page

Add ordinary Markdown under `docs/`; no per-page registration in the Docusaurus configuration is
required. Every page needs either a YAML `title` or a level-one heading. Optional
`sidebar_position`, `sidebar_label`, and `slug` fields control presentation.

Use source-relative Markdown links. Links may cross collections—for example, from a guide to the
[root architecture](../../specs/concorde/module.md)—and fragments are preserved when the registry
maps source paths to published routes. A link to a deliberately excluded implementation artifact is
an error because the generated site could not honor it.

When a guide summarizes normative behavior, link to the relevant module or feature authority and do
not present the summary as stronger or more current than that source.

## Publish a diagram

Architecture and feature Markdown may declare maintained Archify JSON. A declaration identifies the
source, role, kind, explained scenarios, and generated output. The generated page embeds the delivered
HTML in a sandbox and provides source provenance plus a standalone-view link.

For feature diagrams:

- keep maintained JSON directly under the feature's `diagrams/` directory;
- declare no more than one `core` diagram, and make it an architecture/component-interaction view;
- classify sequence, workflow, data-flow, and lifecycle views as `supplemental`;
- provide an equivalent textual explanation; and
- keep the generated delivery fresh and provenance-bearing.

A missing, invalid, escaping, stale, or unpublishable declared diagram stops the build. Edit the JSON
source, redeliver it, and rerun validation; never patch the HTML output.

## Validate changes

From `docsite/`:

```bash
npm ci
npm run inspect
npm run validate
npm run start
npm run build
npm run check
```

- `inspect` reports discovered and deliberately excluded sources.
- `validate` checks identity, metadata, routes, links, diagram declarations, and source-to-page
  mappings without mutating maintained sources.
- `start` validates before opening a local preview.
- `build` renders and verifies a candidate before atomic promotion.
- `check` runs types, tests, validation, and the production build gate.

Repeated builds over identical sources must produce the same page inventory, navigation
relationships, and source-to-page mapping without an LLM call.

## Diagnose a failure

Publication diagnostics identify a rule, source path, reason, and remediation. Typical failures are
unreadable Markdown, invalid front matter, duplicate stable IDs, route collisions, unresolved or
excluded-source links, invalid diagram declarations, and stale generated deliveries.

Fix the canonical source named by the diagnostic and rebuild. A failed candidate must not be
reported as the current complete site, and it must not overwrite the previous successful build.

Return to the [documentation overview](../index.md).
