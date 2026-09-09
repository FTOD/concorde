# Project Docsite

`docsite/` is the packaged, project-neutral docsite template Concorde ships. Every byte in this
directory is identical whether it lives in the Concorde repository or in any other Concorde project
that scaffolds the adapter — except `docsite/site.json`, which is project-owned, and
`docsite/tests/repository/`, which holds evidence specific to the Concorde repository itself, outside
the template (see below). This repository's own `docsite/` is simply the template's first instance:
Concorde develops itself with Concorde.

The adapter publishes the host project's explicitly registered Module and Implementation Specs.
Canonical content stays outside `docsite/`; `.concorde/specs.json` names the documents, Module
relationships and implementation file bindings. Nearby Markdown is not discovered as authority.
Control state under `.concorde/` is excluded from published prose.

## Profile 9 navigation

A Profile 9 project uses `plugins/scoped-content` and registry schema 2. Every registered document
publishes once at a readable source-derived route: `specs/modules/project/module.md` becomes
`/specs/modules/project/module`. The navbar separates `Module Specs`, `Graph` and `Implementation
Specs` (the last appears when implementations are registered). Module and Implementation Specs have
independent sidebars. A Module name opens its `module.md` directly, while its additional documents
and child Modules appear underneath; no duplicate main-Spec entry is generated. Document names omit
`.md`. Source paths remain visible in provenance. Additional documents, including explicitly shared
Module documents, remain part of the complete registered collection.

The relationship graph distinguishes `composes`, `uses`, `implemented_by` and required interface
contracts. Shared capability Modules are siblings of their consumers. Reused Implementation Specs
appear once, with edges from every using Module and their exact bound file list. Publication does
not read or publish the implementation source bytes. Registered architecture diagrams describe a
Module's internal model and render beneath `generated/diagrams/`. A registered System overview
appears before the Module prose. The generator rewrites the overview's Markdown source link to the
delivered interactive HTML. Very simple Modules may omit the overview.

Stable target/path-hash aliases redirect to current canonical document routes. Changed source
paths require deliberate migration of external links. Human navigation does not widen agent context.
The older Architecture/Features adapter and its fixtures remain for Profile 7 diagnostic publication;
its directory-discovery rules do not govern Profile 9 projects. Profile 8 requires explicit migration.

## Site identity

Concorde enables a separate **Spec Protocol** tab for the independent Markdown standard under
`protocol/`. It has its own sidebar and `/protocol/` routes and participates in site search.
These chapters bypass the project Spec registry: they have no Module/Feature identity, membership,
Spec provenance wrapper or architecture-graph node. Framework Module and Implementation Specs
remain under their existing tabs. Protocol documentation is opt-in; scaffolded consumer sites do
not enable it or acquire Concorde's standard as their own project Specs.

The Protocol sidebar includes Required format and the canonical Module, Implementation and
Feature templates. Template code blocks are authoring examples, not declarations that the
Protocol pages themselves belong to the illustrated Modules.

Spec and Context is a child chapter of Spec management. It defines queryable entities, their
authoritative Spec collections and deterministic file membership, with an entity-selection diagram.

Mermaid fences render directly in Markdown pages through Docusaurus's Mermaid theme. Protocol
diagrams remain inline in their authored chapters, with accessible titles and descriptions. They
illustrate the specification language and do not register additional software Modules or diagram
assets in the project Spec registry.

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
| `protocolDocs` | boolean, optional | Enables the independent `../protocol/` Markdown collection and Spec Protocol tab; defaults to disabled. |

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
| `npm run validate` | Validate registered sources, identities, relations, routes, provenance and links. |
| `npm run render-diagrams` | Validate and atomically deliver all architecture-owned diagrams. |
| `npm run start` | Prepare current content and diagrams, then start Docusaurus preview. |
| `npm test` | Run unit, contract, fixture, and integration evidence. |
| `npm run build` | Build, validate, and atomically promote the verified site. |
| `npm run typecheck` | Type-check maintained TypeScript. |
| `npm run check` | Run typechecking, all tests, source validation, and a production build. |

Successful Profile 9 builds emit `build/build-manifest.json` using Build Manifest 16. It records
registered document routes, typed relationships, exact source identities, diagram provenance and
completed build checks. A stale materialization or changed source prevents candidate promotion.
The retained Profile 7 adapter uses its own Build Manifest 13 boundary. Neither publication model
stores a claim that a feature's implementation currently satisfies its promises.

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
