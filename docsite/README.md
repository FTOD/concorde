# Concorde Project Docsite

This private package builds a read-only projection of the Concorde project. Canonical content stays
outside `docsite/`:

- `../README.md` owns the repository introduction and the generated `/` homepage.
- `../docs/**/*.md` owns project documentation.
- Every `../specs/**/architecture.md` is its module's Architecture landing page.
- Every direct `../specs/**/features/*.md` is its feature's only Features page and landing page.
- Every `../specs/**/diagrams/*.json` belongs to the adjacent module `architecture.md`; generated
  Archify HTML beneath `../generated/architecture/` is disposable.

The adapter publishes four collections: Home, Architecture, Documentation, and Features. Public
module and feature routes use stable IDs (`/architecture/<module-id>` and
`/features/<feature-id>`). Generated sidebars follow declared module containment, while features
remain flat capabilities grouped beneath their providing modules. Module entries carry the module
name without the `Architecture:` heading prefix, and both sidebars start at the root module rather
than a collection-level category. `related_features` become
cross-links, never navigation containment.

Feature abstracts, accepted implementation narratives, module summary/design pairs, standalone
specification contracts, nested feature hierarchies, and feature-owned diagrams are rejected as
legacy residue. `.concorde/attempts/<stable-feature-id>/`, `.concorde/reflections/log.md`, and all
other `.concorde/**` control state are outside publication discovery and Manifest provenance.

## Prerequisites

- Node.js 20 or newer
- npm with lockfile support
- the pinned project-local Archify 2.16 skill at `../.agents/skills/archify`

Install dependencies with `npm ci`. `node_modules/`, `.docusaurus/`, `.generated/`,
`../generated/`, `coverage/`, and `build/` are disposable.

## Commands

Run commands from `docsite/`:

| Command | Purpose |
|---|---|
| `npm run inspect` | Print stable source-to-route mappings, exclusions, and finding counts. |
| `npm run validate` | Validate Profile 7 sources, identities, relations, routes, provenance, and links. |
| `npm run render-diagrams` | Validate and atomically deliver all architecture-owned diagrams. |
| `npm run start` | Prepare current content and diagrams, then start Docusaurus preview. |
| `npm test` | Run unit, contract, fixture, integration, and production evidence. |
| `npm run build` | Build, validate, and atomically promote the verified site. |
| `npm run typecheck` | Type-check maintained TypeScript. |
| `npm run check` | Run typechecking, all tests, source validation, and a production build. |

Successful builds emit deterministic `build/build-manifest.json` using Build Manifest 10. It records
the four collections, one page per source authority, stable routes and relations, SHA-256 source
provenance, architecture diagrams, publication-root exclusions, and passed checks. The build
validates that custom JSON boundary directly; it no longer depends on a specification-owned schema
file.

A failed candidate is removed and never replaces the last verified `build/`. Ordinary builds do not
run Archify `visual-check`; perceptual review remains an explicit human-evidence step.

The authoring and troubleshooting guide is
[`../docs/contributing/docsite.md`](../docs/contributing/docsite.md).

## Concorde repository deployment

For this repository, `.github/workflows/deploy-docsite.yml` runs the verified build on `main` and
deploys `build/` to `https://ftod.github.io/concorde/`. This package does not prescribe deployment
for other Concorde projects.
