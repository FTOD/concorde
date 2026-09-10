# Project Docsite

`docsite/` is the packaged, project-neutral docsite template Concorde ships. Every byte in this
directory is identical whether it lives in the Concorde repository or in any other Concorde project
that scaffolds the adapter — except `docsite/site.json`, which is project-owned, and
`docsite/tests/repository/`, which holds evidence specific to the Concorde repository itself, outside
the template (see below). This repository's own `docsite/` is simply the template's first instance:
Concorde develops itself with Concorde.

The adapter publishes the host project's explicitly registered Module Specs. Canonical content
stays outside `docsite/`; `.concorde/specs.json` names the documents, Module relationships and each
Module's implementation file listing. Nearby Markdown is not discovered as authority. Control state
under `.concorde/` is excluded from published prose.

## Navigation

The adapter publishes Profile 10 projects only: it reads `plugins/scoped-content` and registry
schema 3, and refuses any other `profile_version` with an explicit error. Every registered document
publishes once at a readable source-derived route: `specs/project/module.md` becomes
`/specs/project/module`. The navbar exposes a single `Module Specs` tab alongside `Graph`;
there is no separate Implementation Specs tab, because Implementation Specs no longer exist. A
Module name opens its `module.md` directly, while its additional documents and child Modules appear
underneath; no duplicate main-Spec entry is generated. Document names omit `.md`. Source paths
remain visible in provenance. Additional documents, including explicitly shared Module documents,
remain part of the complete registered collection.

The relationship graph distinguishes `composes`, `uses` and matched provided/required structured
contracts. Shared capability Modules are siblings of their consumers. A listing entry declared by
several Modules' entities appears once, with an edge from every listing Module. Each Module's Files
section repeats its declared entries as written: an exact file, or a directory prefix ending in `/`
that binds the regular files below it. Publication validates that an existing exact entry is a file
and an existing directory entry a directory, and that no listed directory contains a registered Spec
document; it does not read or publish implementation file bytes, and it never expands a directory
entry into file names. Every Module's Architecture
section renders its own inline Mermaid flowchart directly from the registered Markdown, with node
labels equal to the declared entity titles and every edge labeled; there is no separate diagram
source or build step.

Stable target/path-hash aliases redirect to current canonical document routes. Changed source
paths require deliberate migration of external links. Human navigation does not widen agent context.
Older profiles require explicit migration; there is no compatibility publishing path for them.

## Site identity

Concorde enables a separate **Spec Protocol** tab for the independent Markdown standard under
`protocol/`. It has its own sidebar and `/protocol/` routes and participates in site search.
These chapters bypass the project Spec registry: they have no Module identity, membership, Spec
provenance wrapper or architecture-graph node. Framework Module Specs remain under their existing
tab. Protocol documentation is opt-in; scaffolded consumer sites do not enable it or acquire
Concorde's standard as their own project Specs.

The Protocol sidebar includes Required format and the canonical Module template and Scenario
fragment. Template code blocks are authoring examples, not declarations that the Protocol pages
themselves belong to the illustrated Modules.

Spec and Context is a child chapter of Spec management. It defines queryable entities, their
authoritative Spec collections and deterministic file membership, with an entity-selection diagram.

Mermaid fences render directly in Markdown pages through Docusaurus's Mermaid theme. Protocol
diagrams remain inline in their authored chapters, with accessible titles and descriptions. They
illustrate the specification language and do not register additional software Modules or diagram
assets in the project Spec registry.

The adapter reads exactly one project-specific file, `docsite/site.json` (site identity schema 1),
through `plugins/scoped-content/site-identity.ts`. No other adapter byte varies between projects.

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

Install dependencies with `npm ci`. `node_modules/`, `.docusaurus/`, `.generated/`, `coverage/`
and `build/` are disposable.

## Commands

Run commands from `docsite/`:

| Command | Purpose |
|---|---|
| `npm run validate` | Validate registered sources, identities, relations, routes, provenance and links. |
| `npm run start` | Materialize the current registered content, then start Docusaurus preview. |
| `npm test` | Run unit, contract, fixture, and integration evidence. |
| `npm run build` | Build, validate, and atomically promote the verified site. |
| `npm run typecheck` | Type-check maintained TypeScript. |
| `npm run check` | Run typechecking, all tests, source validation, and a production build. |

Successful builds emit `build/build-manifest.json` using Build Manifest 17. It records registered
document routes, typed relationships, exact source identities and completed build checks. A stale
materialization or changed source prevents candidate promotion. The manifest stores no claim that
a Module's implementation currently satisfies its promises.

A failed candidate is removed and never replaces the last verified `build/`. Perceptual review of
a published page remains an explicit human-evidence step.

## Repository-specific evidence

`docsite/tests/repository/` holds tests that assert facts about the Concorde repository itself —
its own Module relationship graph, its own maintained specifications, and that `docsite/site.json` and
`.github/workflows/deploy-docsite.yml` reproduce Concorde's identity and deployment workflow. These
tests are not part of the template: every other project that scaffolds the adapter carries its own
`docsite/site.json` and no `tests/repository/` content.

## Concorde repository deployment

For this repository, `.github/workflows/deploy-docsite.yml` — byte-identical to
`docsite/scaffold/deploy-docsite.yml` — runs the verified build on `main` and deploys `build/` to
`https://ftod.github.io/concorde/`. This package does not prescribe deployment for other Concorde
projects; `--github-pages` at scaffold time is how another project opts in.
