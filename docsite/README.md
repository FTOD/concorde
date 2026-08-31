# Concorde Project Docsite

This private package builds the read-only Concorde project website. Canonical content remains outside
this package:

- `../README.md` owns the repository introduction and generated `/` homepage. The build adds only
  disposable route metadata; the maintained README remains ordinary GitHub-flavored Markdown.
- `../docs/**/*.md` owns project documentation.
- Feature-root `design.md` owns required behavior. Sibling `abstract.md` is the landing page and
  sibling `implementation.md` owns the accepted realization; the three publish at `<root>`,
  `<root>/design`, and `<root>/implementation` with abstract-routed feature relationships. Missing
  companions and the former `tldr.md`, `spec.md`, and `implementation/` names are validation errors.
  Temporal `attempt/` workspaces are never published.
- `../specs/**/module.md` (module summary), its sibling `design.md` (module design reference, published
  as a separately linked Architecture page), and `../specs/**/architecture/contracts/**/contract.md` own
  architecture intent. A `design.md` beside `module.md` is a module design reference; elsewhere a
  canonical feature `design.md` is the behavioral authority.
- `../specs/**/architecture/diagrams/*.json` owns module-level architecture diagrams: any number per
  module, discovered from that folder rather than declared, each embedded on its module page. The
  build creates their ignored, disposable standalone Archify projections beneath
  `../generated/architecture/`.
- `../specs/**/features/*/diagrams/*.json` owns feature scenario explanations declared by feature
  `design.md`; each fresh generated view is embedded automatically on the feature abstract.

Before preview or build, the package classifies the root README and unified `specs/` tree and writes
disposable Home, Architecture, and Features inputs beneath `.generated/content/`. These are semantic
projections even though their sources share module packages: Architecture staging follows module
containment, while Features staging follows stable feature identity and explicit parent/sub-feature
containment. A feature's module placement and `refines` relationships remain page metadata and links;
`architecture/`, `modules/`, and module-local `features/` wrappers never become Features sidebar
categories or route parents. Feature pages are staged with the registry-assigned stable-ID route and
generated category metadata, so each category uses the feature title and opens on its abstract.
All provenance, validation, and edits continue to reference the canonical root README, `../docs/`,
and `../specs/` files.

## Prerequisites

- Node.js 20 or newer
- npm with lockfile support
- the officially installed Archify 2.16 project-local skill at `../.agents/skills/archify`

Install dependencies with `npm ci`. Generated directories (`node_modules/`, `.docusaurus/`,
`.generated/`, `../generated/`, `coverage/`, and `build/`) are ignored and disposable. The
project-local Archify skill must contain `package.json` and `bin/archify.mjs`; builds verify its
exact identity and `skills-lock.json` snapshot, then run its doctor check instead of probing
environment variables, global tools, or agent-home installation directories.

## Commands

Run all commands from `docsite/`:

| Command | Purpose |
|---|---|
| `npm run inspect` | Print sorted source-to-route mappings, exclusions, and finding counts. |
| `npm run validate` | Validate sources, metadata, identities, routes, and links without rendering. |
| `npm run render-diagrams` | Validate and atomically deliver every module-owned and feature-declared Archify diagram. |
| `npm run start` | Deliver diagrams, validate, and start the local Docusaurus preview. |
| `npm test` | Run unit, contract, fixture integration, atomicity, and production tests. |
| `npm run build` | Deliver diagrams, render a clean candidate, verify it, and atomically promote `build/`. |
| `npm run typecheck` | Check all maintained TypeScript. |
| `npm run check` | Run type checks, tests, validation, and a verified production build. |

Validation diagnostics use a stable rule ID, project-relative source, reason, and remediation. A
failed candidate is removed and never replaces the last verified `build/`. Successful builds emit
`build/build-manifest.json` (Build Manifest v9), including actual routes, SHA-256 source provenance,
and each module page's `architectureDiagrams`.
The manifest schema is compiled with AJV `strictTypes` and `strictTuples` errors enabled, so a schema
authoring slip fails `npm run build` and `npm test` rather than logging a warning.

Ordinary builds do not run Archify `visual-check`: it requires Chrome/Chromium and produces captures
for human inspection. Run it explicitly when perceptual evidence is required, and never treat an
automated receipt as completed human review.

The complete authoring and troubleshooting workflow is in
[`../docs/contributing/docsite.md`](../docs/contributing/docsite.md).

## Concorde repository deployment

This package does not define deployment behavior for projects that adopt Concorde. For this
repository only, `.github/workflows/deploy-docsite.yml` consumes the checked-in project-local Archify
skill, runs the verified build on every push to `main`, and deploys `build/` to
`https://ftod.github.io/concorde/` with GitHub Pages. The workflow can also be run manually.
