---
title: Contributing to the Docsite
sidebar_position: 2
---

# Contributing to the Docsite

The docsite is a read-only publication system, not a content-authoring authority. It consumes two
maintained roots—`docs/` and `specs/`—and presents three navigation families: Documentation,
Architecture, and Features.

The complete publication behavior is specified by
[Feature 002](../../specs/concorde/features/002-create-project-docsite/design.md).

## Know which sources are eligible

| Published collection | Maintained inputs | Public route family |
|---|---|---|
| Documentation | Every regular `docs/**/*.md` file | `/docs` |
| Architecture | Every `specs/**/module.md` (module summary, with its level view embedded), its adjacent `design.md` (module design reference, published as a separately linked page), and `specs/**/contracts/**/contract.md` | `/architecture` |
| Feature abstracts | Every `specs/**/abstract.md` beside a canonical `design.md`; the page each feature opens on | `/features/<root>` |
| Feature designs | Every canonical feature-root `design.md` | `/features/<root>/design` |
| Feature implementations | Every feature-root `implementation.md` beside `design.md` | `/features/<root>/implementation` |

The build manifest names these collections `docs`, `architecture`, `feature-abstracts`, `features`,
and `feature-implementations`. Module and feature `design.md` files are distinguished by whether
`module.md` is adjacent. A feature `design.md` without `abstract.md` or `implementation.md` is an
error. Symbolic links are not followed. Plans, tasks,
requirements checklists, research, technical models, quick-start evidence, and other files below
`attempt/` are intentionally excluded from the Features collection. Their presence under
`specs/` does not make them permanent project intent.

Do not copy canonical content into `docsite/`. Docusaurus configuration, components, formatting, and
build logic live there; project explanations live in `docs/`; architecture and feature authorities
live in `specs/`.

## How a build works

A preview and a production build use the same inclusion, routing, and validation rules:

1. Maintained module and feature declarations identify the complete Archify source set.
2. The build verifies the installed project-local Archify 2.16 skill, validates every source, and atomically delivers a fresh,
   complete ignored `generated/` set.
3. The source registry discovers eligible files, routes, and deliberate exclusions against those
   current deliveries.
4. Disposable Docusaurus content is materialized under `docsite/.generated/content/`.
5. Docusaurus renders a candidate site.
6. Candidate pages, routes, links, provenance, and the build manifest (Build Manifest v7) are
   validated.
7. Only a successful candidate is promoted to `docsite/build/`.

Because generated diagrams, Architecture/Features pages, and site output are projections, never edit
files under `generated/`, `docsite/.generated/`, or `docsite/build/`. Correct the maintained source
and rebuild.

## Author a documentation page

Add ordinary Markdown under `docs/`; no per-page registration in the Docusaurus configuration is
required. Every page needs either a YAML `title` or a level-one heading. Optional
`sidebar_position`, `sidebar_label`, and `slug` fields control presentation.

Use source-relative Markdown links. Links may cross collections—for example, from a guide to the
[root architecture](../../specs/concorde/module.md), or from a module summary to its adjacent
`design.md`—and fragments are preserved when the registry maps source paths to published routes.
A link to a deliberately excluded implementation artifact is an error because the generated site
could not honor it.

When a guide summarizes normative behavior, link to the relevant module or feature authority and do
not present the summary as stronger or more current than that source.

## Publish a diagram

Architecture and feature Markdown may declare maintained Archify JSON. A declaration identifies the
source, role, kind, explained scenarios, and generated output. The generated page embeds the delivered
HTML in a sandbox and provides source provenance plus a standalone-view link; for a feature, that
page is its abstract.

For feature diagrams:

- keep maintained JSON directly under the feature's `diagrams/` directory;
- declare no more than one `core` diagram, and make it an architecture/component-interaction view;
- classify sequence, workflow, data-flow, and lifecycle views as `supplemental`;
- provide an equivalent textual explanation; and
- keep the generated delivery fresh and provenance-bearing.

A missing, invalid, escaping, duplicate, stale, or unpublishable declared diagram stops the build.
Edit the JSON source and rerun preview/build; delivery is now part of that operation, so never patch
or commit the HTML output.

## Validate changes

From `docsite/`:

```bash
npm ci
npm run inspect
npm run validate
npm run render-diagrams
npm run start
npm run build
npm run check
```

- `inspect` reports discovered and deliberately excluded sources.
- `validate` checks identity, metadata, routes, links, diagram declarations, and source-to-page
  mappings without mutating maintained sources.
- `render-diagrams` verifies the installed `.agents/skills/archify` package and replaces the complete disposable
  delivery set only after every declaration passes.
- `start` delivers and validates before opening a local preview.
- `build` delivers diagrams, renders the site, and verifies a candidate before atomic promotion.
- `check` runs types, tests, validation, and the production build gate.

Repeated builds over identical sources must produce the same page inventory, navigation
relationships, and source-to-page mapping without an LLM call.

Browser-based `visual-check` remains an explicit review step because it requires Chrome/Chromium and
human inspection of its captures. Its HTML, JSON, image, and contact-sheet evidence is disposable and
must not be committed.

## Diagnose a failure

Publication diagnostics identify a rule, source path, reason, and remediation. Typical failures are
unreadable Markdown, invalid front matter, duplicate stable IDs, route collisions, unresolved or
excluded-source links, invalid diagram declarations, and stale generated deliveries.

Fix the canonical source named by the diagnostic and rebuild. A failed candidate must not be
reported as the current complete site, and it must not overwrite the previous successful build.

Return to the [documentation overview](../index.md).
