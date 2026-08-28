# Concorde Project Docsite

This private package builds the read-only Concorde project website. Canonical content remains outside
this package:

- `../docs/**/*.md` owns project documentation.
- `../specs/**/spec.md` owns feature specifications at any module level. Its sibling `tldr.md` is the
  feature's landing page (published at `/features/<root>`, the route the specification used to own)
  and its sibling `design.md` owns the accepted design reference; the three are published together
  under Features (`<root>`, `<root>/spec`, `<root>/design`) with companion links
  (TL;DR · Specification · Design reference) and TL;DR-routed parent, sub-feature, and sibling
  navigation. A `spec.md` without `tldr.md` or `design.md`, and a legacy `implementation.md` beside
  `spec.md`, are validation errors. Temporal `implementation/` workspaces are never published.
- `../specs/**/module.md` (module summary), its sibling `design.md` (module design reference, published
  as a separately linked Architecture page), and `../specs/**/contracts/**/contract.md` own
  architecture intent. A `design.md` is classified by its sibling: beside `module.md` it is a module
  design reference, beside `spec.md` a feature design reference; beside neither it is a validation
  error.
- `../specs/**/architecture.json` owns structural views; the build creates their ignored,
  disposable standalone Archify projections beneath `../generated/architecture/`.
- `../specs/**/features/*/diagrams/*.json` owns feature scenario explanations declared by `spec.md`;
  each fresh generated view is embedded automatically on the feature's TL;DR landing page.

Before preview or build, the package classifies the unified `specs/` tree and writes disposable
Architecture and Features inputs beneath `.generated/content/`. Feature pages are staged with the
route the registry assigned them (front matter `slug`, `sidebar_label`, and `sidebar_position`) so
the TL;DR renders at `/features/<root>`. These are renderer projections only; all provenance,
validation, and edits continue to reference the canonical files under `../specs/`.

## Prerequisites

- Node.js 20 or newer
- npm with lockfile support
- the officially installed Archify 2.16 project-local skill at `../.agents/skills/archify`

Install dependencies with `npm ci`. Generated directories (`node_modules/`, `.docusaurus/`,
`.generated/`, `../generated/`, `coverage/`, and `build/`) are ignored and disposable. The configured
The project-local Archify skill must contain `package.json` and `bin/archify.mjs`; builds verify its
exact identity and `skills-lock.json` snapshot, then run its doctor check instead of probing
environment variables, global tools, or agent-home installation directories.

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
repository only, `.github/workflows/deploy-docsite.yml` consumes the checked-in project-local Archify
skill, runs the verified build on every push to `main`, and deploys `build/` to
`https://ftod.github.io/concorde/` with GitHub Pages. The workflow can also be run manually.
