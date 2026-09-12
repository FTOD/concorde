# Project Docsite

`docsite/` is the packaged, project-neutral publishing template. Project-owned `site.json`,
`custom-docs/`, Concorde's `concorde-only/` extension assets and `tests/repository/` are excluded
from its packaged inventory. A scaffold copies the common adapter and creates a neutral identity;
it does not copy Concorde's homepage, Protocol chapters, Agent Flows or their resources.

The adapter publishes the host project's explicitly registered Module Specs. Canonical content
stays outside `docsite/`; `.concorde/specs.json` names the documents, Module relationships and each
Module's implementation file listing. Nearby Markdown is not discovered as authority. Control state
under `.concorde/` is excluded from published prose.

## Navigation

The adapter publishes Profile 12 projects only: it reads `plugins/scoped-content` and registry
schema 4, and refuses any other `profile_version` with an explicit error. Every registered document
publishes once at a readable source-derived route: `specs/project/module.md` becomes
`/specs/project/module`. The navbar exposes a single `Module Specs` tab;
there is no separate Implementation Specs tab, because Implementation Specs no longer exist. A
Module name opens its `module.md` directly, while its additional documents and child Modules appear
underneath; no duplicate main-Spec entry is generated. Module labels use registry titles;
supplemental document labels use their filenames without `.md`, independently of Markdown headings. Source paths
remain visible in provenance. Supplementary documents appear under their sole owning Module. References retain one canonical
page and do not duplicate it in the sidebar. Registry `parent` alone determines nesting; root
Modules appear directly, without a directory tree or Module composition wrapper.

Publication validates composition, dependencies and matched provided/required structured
contracts. Shared capability Modules are siblings of their consumers. Implementation entries may be listed by several Modules. Each Module's Files
section repeats its declared entries as written: an exact file, or a directory prefix ending in `/`
that binds the regular files below it. Publication validates that an existing exact entry is a file
and an existing directory entry a directory, and that no listed directory contains a registered Spec
document; it does not read or publish implementation file bytes, and it never expands a directory
entry into file names. Every Module's Ontology Relationships
subsection renders its own inline Mermaid flowchart directly from the registered Markdown, with node
labels equal to the declared entity titles and every edge labeled; there is no separate diagram
source or build step.

Stable target/path-hash aliases redirect to current canonical document routes. Changed source
paths require deliberate migration of external links. Human navigation does not widen agent context.
Older profiles require explicit migration; there is no compatibility publishing path for them.

The docsite has no standalone graph page or Graph navigation entry. Understand Anything export
and viewer commands remain independent of publication; inline Mermaid diagrams remain available
in the documents that author them.

## Site identity

The adapter reads `docsite/site.json` (site identity schema 1). Project-specific content is optional;
without custom docs or a homepage the only documentation tab is **Module Specs**.

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
| `customDocs` | array, optional | Independent project-owned documentation collections; see below. |
| `homepage` | object, optional | Enables the project introduction at `/`; omitted by default so the root redirects to the registered entry Module. |

The optional `homepage` object contains project-owned presentation copy. Its required fields are
nonempty strings `eyebrow`, `title` and `description`; `features` with a nonempty `title` and `items`
array; `workflow` with nonempty `title`, `description` and `steps` array; and `quickstart` with
nonempty `title`, `description` and `code`. Each feature or step has nonempty `title` and
`description` strings. Invalid or incomplete configuration fails with the field path in the error.
Text renders as text, and the quickstart code block supports copying through the docsite theme.

An optional `homepage.reference` adds a reference section after the quickstart. It has nonempty
`title` and `description` strings and a nonempty `tables` array. Each table has nonempty `title`
and `description` strings, a nonempty `columns` array of nonempty strings, and a nonempty `rows`
array. Every row contains one nonempty string per column. All copy renders as plain text.
The section includes table navigation, column headers and keyboard-accessible horizontal scrolling
for narrow screens. Omitting it preserves the existing homepage layout.

Concorde enables this introduction to present its core capabilities and installation steps. The
renderer is the same packaged template every project receives; consumer scaffolding does not copy
Concorde's homepage content. The main Spec link resolves from the registered entry Module, and
project-owned `homepage.links` and repository links appear only when configured.
All local navigation respects `baseUrl`. Homepage copy is outside Spec membership and
the registered-page manifest; it grants no agent context and does not replace any Module's Spec.

`docusaurus.config.ts` loads the identity once at startup and fails with an actionable error naming
`docsite/site.json` and the violated rule when the file is missing or invalid.

## Add custom docs

Keep human-authored guides outside the Spec registry and publish them in independent tabs. They
will not enter a Module's agent Spec context or its registered-page manifest. This is the recommended
extension path; do not add reading guides to Module Specs merely to make them visible on the site.

1. Create `docsite/custom-docs/guides/index.md`:

   ```markdown
   ---
   slug: /
   ---
   # Team handbook

   Human-authored onboarding and operating notes.
   ```

2. Add a collection to `docsite/site.json`:

   ```json
   "customDocs": [
     {"id": "guides", "label": "Handbook", "path": "./custom-docs/guides", "routeBasePath": "handbook"}
   ]
   ```

3. Run `npm run build`. The Handbook tab opens `/handbook`, has its own generated sidebar and
   participates in local search. Use `slug: /` on its landing document as above.

Each collection has a unique lowercase slug `id` (except `default`), a label, a content path relative
to `docsite/`, and a distinct `routeBasePath` without leading/trailing slashes. Route bases must not
be `specs`, below `specs/`, or overlap another collection. Optional `sidebarPath` names a
project-owned Docusaurus sidebar file relative to `docsite/`. Collections cannot include registered
Spec files. Missing content, duplicate routes and broken links fail the build.
Paths may use `../` to reach project-owned content beside `docsite/`, but cannot be absolute or
use Windows drive prefixes or backslashes. Content paths name directories; sidebar paths name files.

For executable custom pages, create `docsite/custom-docs/index.ts` and export an additive extension:

```typescript
import type {CustomDocsExtension} from '../plugins/scoped-content/custom-docs';
import handbookPlugin from './handbook-plugin';

export default {
  plugins: [handbookPlugin],
  navbarItems: [{to: '/handbook-app', label: 'Handbook app', position: 'left'}],
} satisfies CustomDocsExtension;
```

The plugin uses normal Docusaurus `addRoute`/`createData` APIs. Keep its routes outside `/specs`;
route conflicts with registered pages are build errors. The optional extension and all custom docs
are authored and maintained by the project, never generated by the scaffold.

Optional `homepage.links` is an array such as `[{"label":"Handbook","to":"/handbook"}]`. Labels
render as text; destinations are local `/routes` or HTTP(S) URLs. Local links respect `baseUrl`.
This configures homepage links without adding project-specific logic to the shared renderer.

Concorde's own `site.json` selects `../protocol` with a sidebar in `custom-docs/sidebars.protocol.ts`.
Its `custom-docs/index.ts` enables the existing Agent Flows plugin. These retain `/protocol` and
`/agent-flows` and are examples of project-owned extensions, not consumer defaults.

### Migration

- `protocolDocs` has been removed, including the false form. Delete the field. To retain a Protocol
  collection, add `{"id":"protocol","label":"Spec Protocol","path":"../protocol","routeBasePath":"protocol"}`
  to `customDocs` and supply your own content and optional sidebar. The adapter reports this
  migration explicitly instead of inferring a Concorde-specific collection.
- Scaffold proposal version 2 reflects the new inventory. Regenerate old proposals with
  `docsite --propose`; version 1 is rejected. Scaffolding stays creation-only: it cannot upgrade or
  overwrite an existing site. Apply template changes to existing sites through a reviewed source
  update while preserving their own identity and custom docs.
- The file-directory navigation, Module composition wrapper and unregistered Projections pages
  are removed. Builds ignore stale `generated/docs` inputs and successful promotion removes old
  published projection pages. Framework runtime instructions and schema APIs remain available.

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

Successful builds emit `build/build-manifest.json` using Build Manifest 19. It records registered
document routes, aliases and exact source identities. It neither emits nor requires
`architecture-graph.json`; older manifest versions require a fresh build. A stale
materialization or changed source prevents candidate promotion. The manifest stores no claim that
a Module's implementation currently satisfies its promises.

A failed candidate is removed and never replaces the last verified `build/`. Perceptual review of
a published page remains an explicit human-evidence step.
Successful promotion replaces the whole build directory, removing obsolete graph pages and their
dedicated assets from previous builds. Scaffolding remains creation-only and does not delete old
source files from existing consumer sites.

## Repository-specific evidence

`docsite/tests/repository/` holds tests that assert facts about the Concorde repository itself —
its own Module navigation, its own maintained specifications, and that `docsite/site.json` and
`.github/workflows/deploy-docsite.yml` reproduce Concorde's identity and deployment workflow. These
tests are not part of the template: every other project that scaffolds the adapter carries its own
`docsite/site.json` and no `tests/repository/` content.

## Concorde repository deployment

For this repository, `.github/workflows/deploy-docsite.yml` shares the scaffold workflow
with additional dependency preparation for its own executable Flow documentation. It runs the
verified build on `main` and deploys `build/` to
`https://ftod.github.io/concorde/`. This package does not prescribe deployment for other Concorde
projects; `--github-pages` at scaffold time is how another project opts in.
