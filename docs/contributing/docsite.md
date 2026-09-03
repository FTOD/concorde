---
title: Contributing to the Docsite
sidebar_position: 2
---

# Contributing to the Docsite

The docsite is a read-only projection, never a content-authoring authority. It publishes root
`README.md`, maintained `docs/`, module `architecture.md` sources, direct `features/*.md` sources,
and module-owned diagrams with provenance.

## Eligible sources

| Collection | Maintained inputs | Route family |
|---|---|---|
| Home | Root `README.md` | `/` |
| Documentation | Regular `docs/**/*.md`, only when `docs/` exists | `/docs` |
| Architecture | Every configured module `architecture.md` | `/architecture/<module-id>` |
| Features | Every direct module `features/<NNN-name>.md` | `/features/<feature-id>` |

The Documentation collection, its navbar item, and its search directory register only when the host
project has a `docs/` directory. A project scaffolded straight from Initialization Proposal 3 output
(a root architecture and README, no `docs/`) still builds and serves; adding `docs/` later is all
that is required to turn Documentation on.

Attempt artifacts under `.concorde/attempts/<stable-feature-id>/`, per-file
`.concorde/reflections/<bucket>/R-NNN.md` documents, other `.concorde/**` control state, code/test fixtures, generated
HTML, and package receipts are outside publication discovery. They are neither pages nor broad
Build Manifest exclusions. Links into `.concorde/**` are diagnosed as excluded control artifacts.
Symbolic links are not followed.
Architecture navigation mirrors recursive module containment. Feature navigation uses providing
module and stable related-feature links; features never form a containment tree. Both sidebars start
at the root module with no collection-level category above it, label each module by its name (the
`Architecture:` heading prefix is dropped), and render module groups as bold headings.

Do not copy canonical content into `docsite/`. Components, formatting, registry/routing, and build
logic live there; publishable prose stays in root/docs/specs, while workflow control prose stays
under `.concorde/`.

## Site identity

`docsite/` is the packaged, project-neutral template Concorde ships; every byte is identical across
projects except the project-owned `docsite/site.json` (site identity schema 1), which
`docusaurus.config.ts` loads once at startup through `plugins/concorde-content/site-identity.ts`.

| Field | Type | Rule |
|---|---|---|
| `schema_version` | integer | Exactly `1`. |
| `title` | string | Non-empty; site and navbar title. |
| `url` | string | Absolute `http(s)://` URL without path. |
| `baseUrl` | string | Starts and ends with `/`. |
| `organizationName` | string | Non-empty. |
| `projectName` | string | Non-empty. |
| `repository` | string, optional | Absolute URL; enables the navbar repository link. |
| `tagline` | string, optional | Falls back to a generic tagline when absent. |

A missing or invalid `docsite/site.json` fails with an error naming the file and the violated rule.
Concorde's own `docsite/site.json` reproduces this repository's identity; every other project
scaffolds the adapter with `concorde.py docsite --propose` / `--apply --proposal <path>` (add
`--github-pages` to also write `.github/workflows/deploy-docsite.yml` from the packaged
`docsite/scaffold/deploy-docsite.yml` template) and edits its own `docsite/site.json` afterwards.
Tests that assert facts specific to the Concorde repository — its diagram inventory, its maintained
framework guides, its own identity and deployment workflow — live under `docsite/tests/repository/`,
outside the template, so they never run against a scaffolded project's copy.

## Build pipeline

1. Discover configured Profile 7 module architectures and direct feature files while keeping the
   `.concorde/**` control plane outside content and provenance discovery.
2. Validate identities, module hierarchy, embedded interfaces, Architecture Zoom references, source
   links, safe routes, and publication-root exclusions; legacy `specs/**/attempts/**` and
   `specs/**/reflections.md` stop the build.
3. Discover diagrams only from each module's declared `diagrams/` sources, validate their textual
   architecture link, hidden legend, safe unique output, and provenance, then deliver a fresh ignored
   generated set.
4. Materialize disposable Home, Architecture, and Feature page trees under
   `docsite/.generated/content/`.
5. Render a Docusaurus candidate.
6. Validate pages, routes, navigation/relations, links, provenance, diagram freshness, and Build
   Manifest 10.
7. Promote only a successful candidate to `docsite/build/`.

Never edit `generated/`, `docsite/.generated/`, or `docsite/build/`. Correct the maintained source
and rebuild.

## Author documentation

Edit root `README.md` for the shared repository/site homepage. Add deeper public guidance under
`docs/`; every page needs YAML `title` or one H1. Use repository-relative links. Cross-collection
links should target canonical architecture/feature sources; the registry rewrites them to public
routes and preserves fragments.

When a guide summarizes normative behavior, link its owning architecture or feature file and make
the source/projection distinction clear.

## Publish an architecture diagram

A diagram source belongs to the module whose structure or interaction it explains. Keep JSON under
that module's `diagrams/`, declare/link it from `architecture.md`, and provide a complete textual
counterpart. Every source sets `meta.legend.mode: hidden`; its normalized generated `.html` target is
unique repository-wide. Dynamic workflow/sequence/data-flow/lifecycle views are explanatory and do
not replace the entity/relationship tables.

Feature files may link a relevant module diagram but own no diagram source. Generated HTML is
sandboxed and linked with source provenance. A missing, invalid, escaping, duplicate, unlinked,
stale, or unpublishable diagram stops the build.

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

`check` runs types, tests, source validation, diagram delivery/freshness, and production build.
Repeated builds over identical sources must produce the same page inventory, relations, and
source-to-page mapping without an LLM call.

Browser visual checks remain explicit review because they require Chrome/Chromium and capture
inspection. Their HTML/JSON/images/contact sheets are disposable. Archify auto-detects a system
Chrome/Chromium on `PATH`; point `ARCHIFY_CHROME` at any other build, such as Playwright's bundled
Chromium (see [Recommended software](../quick-start.md#recommended-software)).

Publication diagnostics identify rule, source path, reason, and remediation. Fix the canonical
source named by a failure. A failed candidate never replaces the previous successful build.

Return to the [documentation overview](../index.md).
