# Concorde Project Docsite

This private package builds the read-only Concorde project website. Canonical content remains outside
this package:

- `../docs/**/*.md` owns project documentation.
- `../specs/**/spec.md` owns feature specifications.
- `../architecture/**/*.md` owns architectural modules, features, and contracts.
- `../architecture/**/architecture.json` owns structural views; `../generated/architecture/*.html`
  contains their delivered, disposable Archify projections.

## Prerequisites

- Node.js 20 or newer
- npm with lockfile support

Install dependencies with `npm ci`. Generated directories (`node_modules/`, `.docusaurus/`,
`.generated/`, `coverage/`, and `build/`) are ignored and disposable.

## Commands

Run all commands from `docsite/`:

| Command | Purpose |
|---|---|
| `npm run inspect` | Print sorted source-to-route mappings, exclusions, and finding counts. |
| `npm run validate` | Validate sources, metadata, identities, routes, and links without rendering. |
| `npm run start` | Validate and start the local Docusaurus preview. |
| `npm test` | Run unit, contract, fixture integration, atomicity, and production tests. |
| `npm run build` | Render a clean candidate, verify it, and atomically promote `build/`. |
| `npm run typecheck` | Check all maintained TypeScript. |
| `npm run check` | Run type checks, tests, validation, and a verified production build. |

Validation diagnostics use a stable rule ID, project-relative source, reason, and remediation. A
failed candidate is removed and never replaces the last verified `build/`. Successful builds emit
`build/build-manifest.json`, including actual routes and SHA-256 source provenance.

The complete authoring and troubleshooting workflow is in
[`../docs/contributing/docsite.md`](../docs/contributing/docsite.md).
