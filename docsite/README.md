# Project Docsite

`docsite/` is the packaged, project-neutral publisher of a Concorde project's Specs. A scaffold
copies it into another project with a neutral `site.json`. Project-owned `site.json`,
`custom-docs/` and `tests/repository/` are excluded from the packaged inventory, so a scaffolded
project never receives Concorde's homepage, Protocol chapters or repository tests.

## What it publishes

The publisher reads `.concorde/config.json`, the registry it names and the documents the registry's
Modules own, each as a reading file plus its `.md.json` metadata. Nothing else is a source: it never
scans directories for Markdown or follows links to find documents.

- **One page per document.** Every owned document is published once, at a route derived from its
  source path: `specs/project/module.md` becomes `/specs/project/module` (the leading `specs/` is
  dropped when every document lies under it). A document read by other Modules through `uses` or
  `includes` is not copied; their links lead to its owner's page.
- **Two reading collections.** The **Module documents** tab shows entries and `module`-role topics;
  the **Implementation documents** tab, present when any document has role `implementation`, shows
  requirements, scenarios and contracts. The role in each document's metadata decides the tab.
- **Navigation follows composition.** Both tabs follow the `contains` tree from the root Module, in
  the parent's `contains` order. A Module's name opens its `module.md`; its topics (in `owns`
  order) and child Modules appear beneath it. Topic labels are file names without `.md`.
- **Provenance.** Each page shows its collection, source path, links between the entry and the
  Module's implementation documents, and a "Spec metadata" disclosure with the document identity,
  owner, the Modules whose Spec context selects the document (and the `owns`, `contains`, `uses` or
  `includes` relation that selects it) and the digests of both members.

## What rendering adds

Rendering works on a staged copy under `.generated/`; Spec files are never changed.

- Every stable identity is an anchor: the Module (on its entry), the document, and every concept,
  realization, requirement, scenario and contract it defines. Requirement and scenario headings
  show only their titles and keep their identity as the heading anchor, so
  `scenarios.md#scenario.x.y` resolves. A concept or realization whose identity the reading does
  not carry gets an anchor at its Terminology row or explanation anchor.
- A Terminology import row, which holds only a link in its source, shows the imported concept's
  definition from its owner's defining row, marked *Imported from* the owning Module. A definition
  cell that is written is shown as written.
- A `d2` block renders where it is written, as an SVG produced by the `d2` program. A checked
  block holds only shapes, nesting and edges; the publisher gives each shape and edge its look from
  what it names (a block inside a block for containment, a realization with its files as a table, a
  plain arrow for `uses`, a dashed arrow with its verb for `relates`). A block marked
  ```` ```d2 illustrative ```` renders as written under a visible "Illustrative, non-normative"
  label.

## What it refuses

The publisher refuses what it cannot publish correctly: an unreadable configuration, a registry
that is not schema 3, malformed Module records or metadata that is not schema 3, a document owned
twice, a duplicate identity, a composition cycle or a Module with two parents, an entry that is not
a `module`-role `module.md` with a `module` block, a requirement, scenario or contract in a
`module`-role document, a concept defined in an `implementation`-role document, a Mermaid block, a
checked `d2` block that sets styles or layout, a `relies_on` identity the target does not own, a
Terminology import row that does not link to its concept's defining document, and a relative link to
an unregistered document. After the build, every internal link and anchor must resolve.

The publisher is not the Protocol validator. Structural conformance, such as what checked diagrams
assert, the registry mirror, realization bindings and contract examples, is established by
`python3 scripts/concorde.py validate`.

## Commands

Run from `docsite/` after `npm ci` (Node.js 20 or newer). Rendering diagrams needs the `d2` program
from [github.com/d2lang/d2](https://github.com/d2lang/d2/releases) on `PATH`, or its path in
`CONCORDE_D2`; the scaffolded deploy workflow installs a pinned release.

| Command             | Purpose                                                                    |
| ------------------- | -------------------------------------------------------------------------- |
| `npm run validate`  | Load and render every page in memory; writes nothing.                      |
| `npm run start`     | Stage the current Specs, then start the Docusaurus preview.                |
| `npm run build`     | Stage, build a candidate, validate it and promote it to `build/`.          |
| `npm test`          | Run the publisher's tests.                                                 |
| `npm run typecheck` | Type-check the TypeScript sources.                                         |
| `npm run check`     | Run typecheck, tests, validate and build.                                  |

A build writes `build/build-manifest.json` (schema 22): every published document with its route,
owner, reading collection, selecting Modules and the digests of both members, plus one digest over
all inputs. A candidate whose manifest, digest or links do not match the current sources is deleted
and the previous `build/` stays. Promotion replaces the whole directory, so pages no longer
produced disappear. `node_modules/`, `.docusaurus/`, `.generated/`, `coverage/` and `build/` are
disposable; preview and production keep separate generated directories.

## Site identity

`docsite/site.json` (schema 1) names the site:

| Field              | Type             | Rule                                                                                 |
| ------------------ | ---------------- | ------------------------------------------------------------------------------------ |
| `schema_version`   | integer          | Exactly `1`.                                                                         |
| `title`            | string           | Non-empty; site and navbar title.                                                    |
| `url`              | string           | Absolute `http(s)://` URL without path.                                              |
| `baseUrl`          | string           | Starts and ends with `/`.                                                            |
| `organizationName` | string           | Non-empty.                                                                           |
| `projectName`      | string           | Non-empty.                                                                           |
| `repository`       | string, optional | Absolute URL; adds a navbar repository link.                                         |
| `tagline`          | string, optional | Falls back to a generic tagline.                                                     |
| `customDocs`       | array, optional  | Project-owned documentation collections; see below.                                  |
| `homepage`         | object, optional | A project introduction at `/`; without it the root redirects to the root Module.     |

`homepage` requires nonempty `eyebrow`, `title` and `description`; `features` (`title`, `items`);
`workflow` (`title`, `description`, `steps`); and `quickstart` (`title`, `description`, `code`).
Optional `reference` adds tables (`title`, `description`, `columns`, `rows`) and optional `links`
adds `{label, to}` links to local routes or HTTP(S) URLs. All copy renders as plain text. An invalid
file fails the build with the field path in the error.

## Custom docs

Human-authored guides live outside the Specs in their own tabs. They belong to no Module and never
enter an agent's context. Add a collection to `site.json`:

```json
"customDocs": [
  {"id": "guides", "label": "Handbook", "path": "./custom-docs/guides", "routeBasePath": "handbook"}
]
```

`id` is a unique lowercase slug other than `default`; `path` is a directory relative to `docsite/`;
`routeBasePath` must not be `specs`, lie below it or overlap another collection; optional
`sidebarPath` names a sidebar file. A collection may not contain a registered Spec document.
For executable pages, export `{plugins, navbarItems}` from `docsite/custom-docs/index.ts` (type
`CustomDocsExtension` in `plugins/scoped-content/custom-docs.ts`) and keep its routes outside
`/specs`.

Concorde's own `site.json` publishes `../protocol` at `/protocol` with the sidebar in
`custom-docs/sidebars.protocol.ts`.

## Scaffold a docsite

```bash
python3 .concorde/framework/scripts/concorde.py docsite --propose
python3 .concorde/framework/scripts/concorde.py docsite --apply --proposal <path>
```

`--github-pages` adds `.github/workflows/deploy-docsite.yml` from `docsite/scaffold/deploy-docsite.yml`.
Scaffolding only creates files; it never updates or deletes an existing site.

## Repository-specific tests

`docsite/tests/repository/` tests the Concorde repository itself: building and publishing its own
Specs, its `site.json` and its deployment workflow. For this repository,
`.github/workflows/deploy-docsite.yml` is the scaffold workflow unchanged; it builds on `main` and
deploys `build/` to `https://ftod.github.io/concorde/`.
