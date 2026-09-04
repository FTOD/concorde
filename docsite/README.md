# Project Docsite

`docsite/` is the packaged, project-neutral docsite template Concorde ships. Every byte in this
directory is identical whether it lives in the Concorde repository or in any other Concorde project
that scaffolds the adapter — except `docsite/site.json`, which is project-owned, and
`docsite/tests/repository/`, which holds evidence specific to the Concorde repository itself, outside
the template (see below). This repository's own `docsite/` is simply the template's first instance:
Concorde develops itself with Concorde.

The adapter builds a read-only projection of its host project. Canonical content stays outside
`docsite/`:

- Every `../specs/**/architecture.md` is its module's Architecture landing page.
- Every direct `../specs/**/features/*.md` is its feature's only Features page and landing page.
- Every `../specs/**/diagrams/*.json` belongs to the adjacent module `architecture.md`; generated
  Archify HTML beneath `../generated/architecture/` is disposable.

The adapter publishes exactly Architecture and Features. Root `/` resolves to the configured root
architecture; a repository `README.md` is not a page. A root `docs/` directory is rejected as a
parallel prose authority and must be reconciled into owning specifications before removal. Public
module and feature routes use stable IDs (`/architecture/<module-id>` and
`/features/<feature-id>`). Generated sidebars follow declared module containment, while features
remain flat capabilities grouped beneath their providing modules. Module entries carry the module
name without the `Architecture:` heading prefix, and both sidebars start at the root module rather
than a collection-level category. `related_features` become cross-links, never navigation
containment.

Feature abstracts, accepted implementation narratives, module summary/design pairs, standalone
specification contracts, nested feature hierarchies, and feature-owned diagrams are rejected as
legacy residue. `.concorde/attempts/<stable-feature-id>/`, `.concorde/reflections/<bucket>/R-NNN.md`, and all
other `.concorde/**` control state are outside publication discovery and Manifest provenance.

## Site identity

The adapter reads exactly one project-specific file, `docsite/site.json` (site identity schema 1),
through `plugins/concorde-content/site-identity.ts`. No other adapter byte varies between projects.

| Field | Type | Rule |
|---|---|---|
| `schema_version` | integer | Exactly `1`. |
| `title` | string | Non-empty; site and navbar title. |
| `url` | string | Absolute `http(s)://` URL without path. |
| `baseUrl` | string | Starts and ends with `/`. |
| `organizationName` | string | Non-empty. |
| `projectName` | string | Non-empty. |
| `repository` | string, optional | Absolute URL; enables the navbar repository link (a GitHub host renders the icon-only link; any other host renders a labeled "Source" link). |
| `tagline` | string, optional | Falls back to a generic tagline when absent. |

`docusaurus.config.ts` loads the identity once at startup and fails with an actionable error naming
`docsite/site.json` and the violated rule when the file is missing or invalid.

## Scaffold a docsite

Concorde projects add this adapter with the runtime `docsite` Tool, from
`.concorde/framework/scripts/concorde.py` in installed projects:

```bash
python3 .concorde/framework/scripts/concorde.py docsite --propose
python3 .concorde/framework/scripts/concorde.py docsite --apply --proposal <path>
```

Add `--github-pages` to the proposal to also write `.github/workflows/deploy-docsite.yml` from
`docsite/scaffold/deploy-docsite.yml`, the packaged GitHub Pages workflow template. The scaffold
proposal writes a project-owned `docsite/site.json`; every other copied file is template bytes,
digest-bound to the package. It neither requires nor creates a project README.

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
| `npm test` | Run unit, contract, fixture, and integration evidence. |
| `npm run build` | Build, validate, and atomically promote the verified site. |
| `npm run typecheck` | Type-check maintained TypeScript. |
| `npm run check` | Run typechecking, all tests, source validation, and a production build. |

Successful builds emit deterministic `build/build-manifest.json` using Build Manifest 12. It records
the two collections, one page per specification authority, stable routes and relations, SHA-256 source
provenance, architecture diagrams, publication-root exclusions, and passed checks. The build
validates that custom JSON boundary directly; it no longer depends on a specification-owned schema
file. Feature pages and related-feature summaries carry `evidenceStatus`, which is exactly the
front matter `evidence_status` value (`unknown`, `partial`, `verified`, or `disagrees`); Manifest 12
removed the earlier `status` field that mixed body lifecycle prose with evidence.

A failed candidate is removed and never replaces the last verified `build/`. Ordinary builds do not
run Archify `visual-check`; perceptual review remains an explicit human-evidence step.

## Repository-specific evidence

`docsite/tests/repository/` holds tests that assert facts about the Concorde repository itself —
its own diagram inventory, its own maintained specifications, and that `docsite/site.json` and
`.github/workflows/deploy-docsite.yml` reproduce Concorde's identity and deployment workflow. These
tests are not part of the template: every other project that scaffolds the adapter carries its own
`docsite/site.json` and no `tests/repository/` content.

## Concorde repository deployment

For this repository, `.github/workflows/deploy-docsite.yml` — byte-identical to
`docsite/scaffold/deploy-docsite.yml` — runs the verified build on `main` and deploys `build/` to
`https://ftod.github.io/concorde/`. This package does not prescribe deployment for other Concorde
projects; `--github-pages` at scaffold time is how another project opts in.
