# Publication pipeline

How the [Views](module.md) publisher turns registered Specs into a checked site: loading and
admission, routes, staging, navigation, the Docusaurus build hooks, validation and promotion. The
code lives in `docsite/plugins/scoped-content/` and `docsite/scripts/`.

## Loading and admission {#loading-and-admission}

`requireScoped(root)` only checks that `.concorde/config.json` is readable as a JSON object;
without it every command fails with a message asking to initialize the project first.

`loadScopedRegistry(root)` reads the configuration, the registry `.concorde/specs.json` and, for
every [Module](../../glossary.json#concept.module), the documents the registry record lists in `owns`:
both the reading file and its `.md.json` metadata. The registry must be
`{"schema_version": 3, "modules": [...]}` with a nonempty list of records having exactly `id`,
`title`, `entry`, `owns`, `contains`, `uses`, `includes` and `participates`. The publisher reads the
Module relations from these records; it does not compare them with the entries' `module` blocks,
which is the [Spec](../../glossary.json#concept.spec) validator's mirror check.

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
- an entry has role `implementation`, does not have the level-2 headings Purpose, Usage and
  Design, each exactly once, or has a level-2 Relationships section — the loader rejects
  it (`requireReading` in `docsite/plugins/scoped-content/reading-format.ts`), since a Module's
  relationships belong in its Design;
- a `module`-role document contains a requirement or scenario heading or a `concorde-contract`
  fence, or any document's metadata holds a concept record;
- a document contains a Mermaid block: diagrams in reading are D2;
- a realization `meaning` anchor, or a concept's explanation anchor, has no readable prose;
- the glossary is malformed, not sorted by identity, declared by more than one Module or by a
  contained one, or has an entry whose identity or title repeats, whose owner is no registered
  Module, whose explanation is not in a `module` document of its owner, or whose definition links
  an undeclared concept;
- a `concorde-contract` fence has no valid identity or no positive integer version (the publisher
  does not check the schema or example; the Spec validator does);
- a term link names a concept the glossary does not declare;
- a `relies_on` identity names no node defined by the relation's target, or an inclusion names an
  unknown Module or document;
- two documents would share a route.

These are the checks the publisher needs to produce correct pages. Checked diagrams, realization
bindings, the registry mirror and contract examples are left to Spec core's validator.
Loading never fetches anything and never reads implementation files.

The **root Module** is the first Module in registry order that no Module contains. The loaded model
holds the Module records, the defined concepts and realizations with their owner, document and
definition, and one page per document with: source and metadata paths, route, staged path, title,
reading content, reading and metadata digests, document identity, owner,
reading collection (the role), whether it is its
Module's entry, and the selecting Modules.

**Selecting Modules.** For each Module the publisher computes its one-level
[Spec context](../../glossary.json#concept.spec-context): its own documents (`owns`), and for every
`contains` and `uses` the target's documents, or only the target's entry and the documents defining
the `relies_on` identities when that list is present, and the documents of every `module` or
`document` inclusion. This is the Protocol's context selection, and the resulting per-document list
must equal Spec core's `selected-by` index for the same registry and documents. A page lists every
Module whose context holds it, in registry order, each with its reasons. A reason is
`{relation, id}`, where `relation` is `owns`, `contains` or `uses` and `id` is the owning or target
Module; an inclusion reason is `{relation: "includes", kind, id}`, where `kind` is `module` or
`document` and `id` is the included Module or document. Reasons are sorted by `relation`, then
`kind`, then `id`.

## Source digest {#source-digest}

`hash(value)` is `sha256:` followed by the lowercase hex SHA-256 of the bytes. The source digest is
`hash` of the JSON serialization of the ordered list of `[path, hash(bytes)]` pairs for the
configuration, the registry, both members of every document in registry order, the glossary when
the root Module declares one and, last, the site identity
`docsite/site.json` when it exists, since it shapes every page. Any byte change in any of them,
including a metadata-only edit, changes it. It identifies inputs; it is not a claim about meaning.

## Routes {#routes}

A page's staged path is its source path, with a leading `specs/` removed when every registered
document lies under `specs/`. Its route is `/specs/` followed by the staged path without `.md`.
A page has no other route. Its model title, which the provenance bar uses when it links an entry
and its implementation pages, is the document's first level-1 heading, falling back to the owner's
title.

## Staging

`materializeScoped(model)` writes under `docsite/.generated/`:

1. It deletes the staging identity record, then the previous `content/` and `static/` directories.
2. For every page it writes `content/specs/<staged path>` with front matter giving the slug, the
   title and navigation label (the Module's title for an entry, otherwise the file name without
   `.md`; the page body still shows the document's own level-1 heading), the sidebar of its
   reading collection and a table of contents of level-2 and level-3 headings. The body is
   the reading with these rewrites, applied outside fenced code only:
   - **links**: a relative Markdown link `[label](path)` or image `![label](path)` whose target
     path resolves, relative to the source file, to a registered document is replaced by that
     page's route; the query and fragment are kept in order. A link whose target is the
     glossary is replaced by the glossary page's route, with the concept's anchor when it has a
     fragment; a fragment naming no declared concept fails staging. A path that resolves to no
     registered document fails staging. A link's text may wrap onto the next line. URLs with a
     scheme or starting with `/`, bare `#fragment` links and links inside inline code spans are
     left unchanged;
   - **realization anchors**: a node whose identity the reading does not carry gets an anchor at
     its `meaning` anchor;
   - **owned terms**: the entry page of a Module that owns concepts ends with a Terms list linking
     each to the glossary page;
   - **definition headings**: a level-2 to level-5 heading `req.<id> — Title` or
     `scenario.<id> — Title` (em dash, en dash or hyphen) becomes `Title {#<id>}`;
   - **contract anchors**: an HTML anchor whose id is the contract identity is inserted before
     each `concorde-contract` fence;
   - **diagrams**: each `d2` block is rendered by the `d2` program to an SVG staged beside the page
     and replaced by an image of it. A checked block is first parsed in the semantic subset, whose
     violation fails the build with the document and line; each shape then receives a class of the
     house style from what its label resolves to (the page's Module, a descendant, another Module, a
     concept, a realization, a realization with file rows, a qualified node) and each edge the class
     `uses` when it joins two Modules without a label, and `relates` otherwise. A container of five
     or more children that no edge touches is laid out as a near-square grid instead of one long
     row. A qualified shape that names one of the page's own nodes shows only the node's title,
     since the enclosing Module already shows the owner. A `d2 illustrative` block is rendered as
     written and preceded by the label "Illustrative, non-normative. This diagram explains; it
     declares no relationship.";
   - **page anchors**: the Module identity (on its entry) and the document identity are inserted
     as anchors after the level-1 title, unless the reading already carries them.
3. When the root Module declares a glossary, it writes the Glossary page at the route of the
   glossary's path without `.json` (`/specs/concorde/glossary` here). An index comes first: every
   term by initial letter, each linking to its entry. Level-2 group headings follow, anchored
   `terms.<module id>`: "Core terms" for the concepts the root Module owns, then one group per
   Module the root contains, in `contains` order, holding every concept whose owner is that Module
   or lies below it (an owner outside the root's tree gets the group of its own topmost Module).
   Within a group the concepts are sorted by title, letter case ignored, each a level-3 heading
   anchored by its identity, with its definition (term links inside it pointing to anchors on the
   same page), its owning Module's entry and a link to its explanation, and any retirement or
   external-conflict note. The page's table of contents lists the groups only.
4. It writes `specs-sidebar.json` with `moduleDocumentsSidebar` and, when any page has the
   `implementation` collection, `implementationDocumentsSidebar`. The Glossary page is the last
   item of the declaring Module's category in `moduleDocumentsSidebar`.
5. Last, it writes the staging identity record `scoped-materialization.json`:
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

- **Module documents.** A Module with `module`-role topics or children is a category whose label is
  the Module title and whose link opens its entry; its items are its `module`-role topics in `owns`
  order, then its children. A Module with neither is a single link to its entry. The entry is never
  listed twice.
- **Implementation documents.** A Module is a category labelled with its title, holding its
  `implementation`-role documents in `owns` order and then its children; a Module with no such
  document anywhere below it is omitted. Categories below the top level start collapsed.

Document labels are file names without `.md`. A document appears only under its owner.

## Provenance

The content plugin publishes Docusaurus global data with `schema_version`, `rootModule`, `pages`
(every page without its reading body) and `siteIdentity`. A layout wrapper finds the current page by
route and renders the provenance bar: the collection label, the source path, links between the entry
and the owner's implementation pages, and a "Spec metadata" disclosure with the document identity,
the owner, the selecting Modules with their reasons, the metadata path and both digests. Without
user documents, the site root uses `rootModule` to
redirect to the root Module's entry.

## Build hooks

The Docusaurus configuration loads the site identity
and the model at start-up. The Spec docs instance reads `.generated/content/specs` at route base
`/specs`; user documents are a separate instance at route base `/` with a generated sidebar, and the
root redirect page is then left out; each custom docs
collection is a separate instance; local search indexes all of them. The navigation lists user
documents, then Module documents and Implementation documents, then custom docs. Broken links,
anchors and duplicate routes are build errors.

The content plugin:

- on load, reloads the model and requires the staging identity record to have `schema_version` 2
  and the current source digest;
- after the build, reloads the model and fails if the source digest changed, if the staging record
  no longer matches, or if any registered page route is missing from the rendered routes; then
  writes `build-manifest.json`.

User documents admission, done while configuring the site, fails when the directory is missing,
has no root page, contains a registered document, or has a top-level document or folder that would
publish under `/specs`, `/search` or a custom docs route. Custom docs admission fails when a
collection directory or sidebar file is missing, when a collection directory contains a registered
document, or when `custom-docs/index.ts` does not export an object, or exports `plugins` or
`navbarItems` that is not an array; an omitted property adds nothing.

## Preview {#preview}

A running Docusaurus cannot show a changed Spec: the content plugin refuses staged pages whose
source digest differs from the sources, and the pages, sidebars and navigation are fixed when
staging runs. `npm run start` therefore supervises the preview instead of relying on Docusaurus's
own watching, and the content plugin watches nothing.

The supervisor stages with `preparePublication(root)` and starts `docusaurus start` with the
command's arguments. Its inputs are `docsite/site.json`, the configuration, the registry, both
members of every registered document and the glossary the root Module declares. It watches their
directories, not the files, so an editor that saves by replacing a file is still seen. Changes
within 300 ms form one restart: it stops Docusaurus (`SIGTERM`, then `SIGKILL` after ten seconds),
stages again, recomputes the inputs and their watched directories, and starts Docusaurus again with
`--no-open` added so that no further browser window opens. A change that arrives during a restart
causes one more restart after it.

When staging fails, no preview runs. The supervisor reports the error in full, keeps its last
watched directories, and retries on the next change to an input or to any `.md` or `.md.json` file
in them, since the model that failed may list a document not yet written. When the first staging
fails there is nothing to watch, and the command exits nonzero. When Docusaurus exits on its own
the supervisor reports the status and starts it again on the next change. Interrupting the command
stops Docusaurus and the watchers and exits.

## Validation

`validateScopedBuild(root, directory)` reloads the model from the current sources and fails unless:

- the candidate's `build-manifest.json` has the
  site manifest's `schema_version` (23,
  see the [contracts](contracts.md)) and the current source digest, and its `pages` equal the
  expected entries exactly and in order;
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
rename fails, it removes a partially moved destination and renames the backup back. A failure of the
filesystem during this rollback fails the build with that error and leaves the previous site in the
backup directory, `docsite/.generated/previous-build/`, for manual recovery. The function checks
nothing itself; only `buildSite` calls it, after validation. The caller must own the candidate,
build and backup directories exclusively for the whole build.
