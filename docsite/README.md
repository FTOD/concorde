# Concorde Project Docsite

This private package builds the read-only Concorde project website. Canonical content remains outside
this package:

- `../docs/**/*.md` owns project documentation.
- `../specs/**/spec.md` owns feature specifications at any module level.
- `../specs/**/module.md` and `../specs/**/contracts/**/contract.md` own architecture intent.
- `../specs/**/architecture.json` owns structural views; the build creates their ignored,
  disposable standalone Archify projections beneath `../generated/architecture/`.
- `../specs/**/features/*/diagrams/*.json` owns feature scenario explanations declared by `spec.md`;
  each fresh generated view is embedded automatically on its canonical feature page.

Before preview or build, the package classifies the unified `specs/` tree and writes disposable
Architecture and Features inputs beneath `.generated/content/`. These are renderer projections only;
all provenance, validation, and edits continue to reference the canonical files under `../specs/`.

## Prerequisites

- Node.js 20 or newer
- npm with lockfile support
- Archify 2.14.0, with `ARCHIFY_ROOT` set to its package directory

Install dependencies with `npm ci`. Generated directories (`node_modules/`, `.docusaurus/`,
`.generated/`, `../generated/`, `coverage/`, and `build/`) are ignored and disposable. The configured
Archify root must contain `package.json` and `bin/archify.mjs`; builds verify its exact identity and
run its doctor check instead of probing agent-specific installation directories.

## Commands

Run all commands from `docsite/`:

| Command | Purpose |
|---|---|
| `npm run inspect` | Print sorted source-to-route mappings, exclusions, and finding counts. |
| `npm run validate` | Validate sources, metadata, identities, routes, and links without rendering. |
| `npm run render-diagrams` | Validate and atomically deliver every declared Archify view. |
| `npm run start` | Deliver diagrams, validate, and start the local Docusaurus preview. |
| `npm test` | Run unit, contract, fixture integration, atomicity, and production tests. |
| `npm run build` | Deliver diagrams, render a clean candidate, verify it, and atomically promote `build/`. |
| `npm run typecheck` | Check all maintained TypeScript. |
| `npm run check` | Run type checks, tests, validation, and a verified production build. |

Validation diagnostics use a stable rule ID, project-relative source, reason, and remediation. A
failed candidate is removed and never replaces the last verified `build/`. Successful builds emit
`build/build-manifest.json`, including actual routes and SHA-256 source provenance.

Ordinary builds do not run Archify `visual-check`: it requires Chrome/Chromium and produces captures
for human inspection. Run it explicitly when perceptual evidence is required, and never treat an
automated receipt as completed human review.

The complete authoring and troubleshooting workflow is in
[`../docs/contributing/docsite.md`](../docs/contributing/docsite.md).

## Concorde repository deployment

This package does not define deployment behavior for projects that adopt Concorde. For this
repository only, `.github/workflows/deploy-docsite.yml` checks out the pinned public Archify 2.14.0
release, runs the verified build on every push to `main`, and deploys `build/` to
`https://ftod.github.io/concorde/` with GitHub Pages. The workflow can also be run manually.
