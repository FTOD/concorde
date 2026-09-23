# Publication pipeline

How the [Views](module.md) publisher turns registered Specs into a checked site: loading and
admission, routes, staging, navigation, the Docusaurus build hooks, validation and promotion. The
code lives in `docsite/plugins/scoped-content/` and `docsite/scripts/`.

## Loading and admission {#loading-and-admission}

`requireScoped(root)` only checks that `.concorde/config.json` is readable and names the registry;
without it every command fails with a message asking to initialize the project first.

`loadScopedRegistry(root)` reads the configuration, the registry it names and, for every Module,
the documents the registry record lists in `owns`: both the reading file and its `.md.json`
metadata. The registry must be `{"schema_version": 3, "modules": [...]}` with a nonempty list of
records having exactly `id`, `title`, `entry`, `owns`, `contains`, `uses`, `includes` and
`participates`. The publisher reads the Module relations from these records; it does not compare
them with the entries' `module` blocks, which is the Spec validator's mirror check.

Paths must be safe relative POSIX paths; every path component is checked for symbolic links, and
two members that are the same physical file are rejected. Files are decoded as strict UTF-8, JSON
is parsed with duplicate keys rejected, and Markdown front matter is removed from the reading.

Loading fails with an `Error` naming the source when:

- the configuration or registry cannot be read, the registry is not schema 3, or a record is
  malformed, repeats a Module identity or title, or has an entry that is not an owned `module.md`;
- a document is owned twice, an identity is invalid or defined twice, a contained Module is
  unknown or the Module itself, a Module has two parents, composition has a cycle, or no Module is
  uncontained;
- metadata is not schema 3, has unknown fields, names another owner, or has a `role` other than
  `module` or `implementation`;
- an entry's metadata lacks the `module` block, or any other document's metadata has one;
- an entry has role `implementation`, or its first level-2 headings are not Purpose, Terminology,
  Usage, Design and Relationships, once each and in order;
- a `module`-role document contains a requirement or scenario heading or a `concorde-contract`
  fence, or an `implementation`-role document defines a concept;
- a `module`-role document contains a Graph Spec flowchart, recognized as a Mermaid block with a
  line matching `%% graph:`; Graph Specs belong to their owners' implementation documents, as
  Agent execution defines;
- an unmarked Mermaid block does not start with `flowchart` or `graph`;
- a concept or realization `meaning` anchor has no readable prose;
- a `concorde-contract` fence has no valid identity or no positive integer version (the publisher
  does not check the schema or example; the Spec validator does);
- a Terminology import row links to a concept anywhere but its defining document;
- a `relies_on` identity names no node defined by the relation's target, or an inclusion names an
  unknown Module or document;
- two documents would share a route.

These are the checks the publisher needs to produce correct pages. Checked flowcharts, realization
bindings, the registry mirror and contract examples are left to Spec tooling's validator.
Loading never fetches anything and never reads implementation files.

The **root Module** is the first Module in registry order that no Module contains. The loaded model
holds the Module records, the defined concepts and realizations with their owner, document and
definition, and one page per document with: source and metadata paths, route, staged path, title,
reading content, reading and metadata digests, document identity, owner, reading collection (the
role), whether it is its Module's entry, and the selecting Modules.

**Selecting Modules.** For each Module the publisher computes its one-level Spec context: its own
documents (`owns`), and for every `contains` and `uses` the target's documents, or only the target's
entry and the documents defining the `relies_on` identities when that list is present, and the
documents of every `module` or `document` inclusion. This is the Protocol's context selection, and
the resulting per-document list must equal Spec tooling's `selected-by` index for the same registry
and documents. A page lists every Module whose context holds it, in registry order, each with its
reasons. A reason is `{relation, id}`, where `relation` is `owns`, `contains` or `uses` and `id` is
the owning or target Module; an inclusion reason is `{relation: "includes", kind, id}`, where `kind`
is `module` or `document` and `id` is the included Module or document. Reasons are sorted by
`relation`, then `kind`, then `id`.

## Source digest {#source-digest}

`hash(value)` is `sha256:` followed by the lowercase hex SHA-256 of the bytes. The source digest is
`hash` of the JSON serialization of the ordered list of `[path, hash(bytes)]` pairs for the
configuration, the registry and both members of every document in registry order. Any byte change
in any of them, including a metadata-only edit, changes it. It identifies inputs; it is not a
claim about meaning.

## Routes {#routes}

A page's staged path is its source path, with a leading `specs/` removed when every registered
document lies under `specs/`. Its route is `/specs/` followed by the staged path without `.md`.
Its title is the document's first level-1 heading, falling back to the owner's title. A page has
no other route.

## Staging

`materializeScoped(model)` writes under `docsite/.generated/`:

1. It deletes the staging identity record, then the previous `content/` and `static/` directories.
2. For every page it writes `content/specs/<staged path>` with front matter giving the slug, the
   title (the Module's title for an entry, otherwise the file name without `.md`), the sidebar of
   its reading collection and a table of contents of level-2 and level-3 headings. The body is
   the reading with these rewrites, applied outside fenced code only:
   - **links**: a relative Markdown link `[label](path)` or image `![label](path)` whose target
     path resolves, relative to the source file, to a registered document is replaced by that
     page's route; the query and fragment are kept in order. A path that resolves to no
     registered document fails staging. URLs with a scheme or starting with `/`, bare
     `#fragment` links and links inside inline code spans are left unchanged;
   - **imported definitions** (in `module`-role documents): the empty definition cell of each
     Terminology import row is filled with the definition from the defining row, its links
     addressed from the defining page, followed by *Imported from [Owner](entry route)*. A cell
     that is already written is left as written;
   - **concept and realization anchors**: a defining Terminology row whose concept has no anchor
     in the reading gets one; any other node whose identity the reading does not carry gets an
     anchor at its `meaning` anchor;
   - **definition headings**: a level-2 to level-5 heading `req.<id> — Title` or
     `scenario.<id> — Title` (em dash, en dash or hyphen) becomes `Title {#<id>}`;
   - **contract anchors**: an HTML anchor whose id is the contract identity is inserted before
     each `concorde-contract` fence;
   - **illustrative diagrams**: each `mermaid illustrative` block becomes a plain `mermaid` block
     preceded by the label "Illustrative, non-normative. This diagram explains; it declares no
     relationship.";
   - **page anchors**: the Module identity (on its entry) and the document identity are inserted
     as anchors after the level-1 title, unless the reading already carries them.
3. It writes `specs-sidebar.json` with `moduleDocumentsSidebar` and, when any page has the
   `implementation` collection, `implementationDocumentsSidebar`.
4. Last, it writes the staging identity record `scoped-materialization.json`:
   `{"schema_version": 2, "sourceDigest": "<source digest>"}`.

A failure leaves no identity record; the build hooks then refuse the partial staging.
`npm run validate` performs step 2 in memory for every page, so it reports the same link and
rendering failures without writing.

`preparePublication(root, {mode})` checks the configuration, loads, stages, and clears the
Docusaurus generated directory of the mode: `.docusaurus` for `preview` (the default) or
`.generated/docusaurus-production` for `build`. The webpack filesystem cache lives inside that
directory, so each launch compiles from scratch and the two modes never share or clear each
other's files.

## Navigation

Both sidebars follow the `contains` tree, starting from the uncontained Modules in registry order;
children follow the parent's `contains` order.

- **Module documents.** A Module with `module`-role topics or children is a category whose label is the
  Module title and whose link opens its entry; its items are its `module`-role topics in `owns`
  order, then its children. A Module with neither is a single link to its entry. The entry is
  never listed twice.
- **Implementation documents.** A Module is a category labelled with its title, holding its
  `implementation`-role documents in `owns` order and then its children; a Module with no such
  document anywhere below it is omitted. Categories below the top level start collapsed.

Document labels are file names without `.md`. A document appears only under its owner.

## Provenance

The content plugin publishes Docusaurus global data with `schema_version`, `rootModule`, `pages`
(every page without its reading body) and `siteIdentity`. A layout wrapper finds the current page
by route and renders the provenance bar: the collection label, the source path, links between the
entry and the owner's implementation pages, and a "Spec metadata" disclosure with the document
identity, the owner, the selecting Modules with their reasons, the metadata path and both digests.
The homepage uses `rootModule` to find the root Module's entry.

## Build hooks

The Docusaurus configuration loads the site identity and the model at start-up. The Spec docs
instance reads `.generated/content/specs` at route base `/specs`; each custom docs collection is a
separate instance; local search indexes all of them. Broken links, anchors and duplicate routes
are build errors.

The content plugin:

- on load, reloads the model and requires the staging identity record to have `schema_version` 2
  and the current source digest;
- watches `docsite/site.json`, the configuration, the registry and both members of every document;
- after the build, reloads the model and fails if the source digest changed, if the staging record
  no longer matches, or if any registered page route is missing from the rendered routes; then
  writes `build-manifest.json`.

Custom docs admission, done while configuring the site, fails when a collection directory or
sidebar file is missing, when a collection directory contains a registered document, or when
`custom-docs/index.ts` does not export an object with array `plugins` and `navbarItems`.

## Validation

`validateScopedBuild(root, directory)` reloads the model from the current sources and fails unless:

- the candidate's `build-manifest.json` has the model's schema version and source digest and its
  `pages` equal the expected entries exactly and in order;
- every internal link resolves.

For links it parses every HTML file of the candidate and collects `id` and `a name` anchors, the
`href` of `a` and `area` elements, `base` elements and meta-refresh redirects. A URL is internal
when it has the site's origin and its path lies under the base URL. Each internal URL must reach a
file (`path`, `path.html` or `path/index.html`); redirect pages are followed, keeping the fragment,
and a redirect cycle fails; a nonempty fragment must name an anchor on the final page.
Percent-escapes of unreserved characters are compared decoded. Every registered route is checked as
well. A failure names the referring file and the destination. External URLs are never fetched.
Validation repairs nothing.

## Promotion

`buildSite()` checks the configuration, deletes `docsite/.generated/candidate`, runs
`preparePublication` in `build` mode, runs `docusaurus build --out-dir` into the candidate with the
production generated directory, validates the candidate and calls `promoteCandidate`. On any
failure it deletes the candidate and rethrows.

`promoteCandidate(candidate, destination, backup)` deletes the backup, renames the existing
destination to the backup, renames the candidate to the destination and deletes the backup. If a
rename fails, it removes a partially moved destination and renames the backup back. A failure of
the filesystem during this rollback can still need manual recovery. The function checks nothing
itself; only `buildSite` calls it, after validation. The caller must own the candidate, build and
backup directories exclusively for the whole build.
