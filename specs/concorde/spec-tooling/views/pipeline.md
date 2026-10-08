# Publication pipeline

The [Views](module.md) publisher turns registered Specs into a checked site through these stages:

- Loading and admission.
- Routes.
- Staging.
- Navigation.
- The Docusaurus build hooks.
- Validation.
- Promotion.

The code lives in `docsite/plugins/scoped-content/` and `docsite/scripts/`.

## Loading and admission {#loading-and-admission}

`requireScoped(root)` only checks that `.concorde/config.json` is readable as a JSON object.
Without it, every command fails with a message asking to initialize the project first.

`loadScopedRegistry(root)` reads these sources:

- The configuration.
- The registry `.concorde/specs.json`.
- For every [Module](../../glossary.json#concept.module), the documents the registry record lists in
  `owns`: both the reading file and its `.md.json` metadata.

The registry must be `{"schema_version": 3, "modules": [...]}` with a nonempty list of records.
Each record must have exactly `id`, `title`, `entry`, `owns`, `contains`, `uses`, `includes` and
`participates`. The publisher reads the Module relations from these records.
It does not compare them with the entries' `module` blocks.
That comparison is the [Spec](../../glossary.json#concept.spec) validator's mirror check.

Paths must be safe relative POSIX paths. Every path component is checked for symbolic links.
Two members that are the same physical file are rejected. Files are decoded as strict UTF-8.
A file that is not valid UTF-8 fails loading with an error naming its path.
JSON is parsed with duplicate keys rejected. Markdown front matter is removed from the reading.

When any of these conditions holds, loading fails with an `Error` naming the source:

- The configuration or registry cannot be read.
- A source is not valid UTF-8.
- The registry is not schema 3.
- A record is malformed.
- A record repeats a Module identity or title.
- A record has an entry that is not an owned `module.md`.
- A document is owned twice.
- An identity is invalid or defined twice.
- A contained Module is unknown or the Module itself.
- A Module has two parents.
- Composition has a cycle.
- No Module is uncontained.
- Metadata is not schema 3.
- Metadata has unknown fields.
- Metadata names another owner.
- Metadata has a `role` other than `module` or `implementation`.
- An entry's metadata lacks the `module` block, or any other document's metadata has one.
- An entry has role `implementation` (`requireReading` in
  `docsite/plugins/scoped-content/reading-format.ts`). How an entry is organized is never checked,
  since the Protocol requires no section of it.
- A `module`-role document contains any of these:
  - A requirement heading.
  - A scenario heading.
  - A `concorde-contract` fence.
- Any document's metadata holds a concept record.
- A document contains a Mermaid block. Diagrams in reading are D2.
- A realization `meaning` anchor, or a concept's explanation anchor, has no readable prose.
- The glossary is malformed.
- The glossary is not sorted by identity.
- The glossary is declared by more than one Module or by a contained one.
- The glossary has an entry whose identity or title repeats.
- The glossary has an entry whose owner is no registered Module.
- The glossary has an entry whose explanation is not in a `module` document of its owner.
- The glossary has an entry whose definition links an undeclared concept.
- A `concorde-contract` fence has no valid identity or no positive integer version.
  The publisher does not check the schema or example. The Spec validator does.
- A term link names a concept the glossary does not declare.
- A `relies_on` identity names no node defined by the relation's target.
- An inclusion names an unknown Module or document.
- Two documents would share a route.
- A source lies inside a publication output directory: `docsite/.generated/`, `docsite/build/` or
  `docsite/.docusaurus/`.
  The sources are the configuration, the registry, both members of every document, the glossary
  and the site identity.
  A source counts as inside when its path lies there or when its physical location, after every
  symbolic link is resolved, lies inside the output directory's physical location.
- One of those output directories is a symbolic link, which would send its cleanup elsewhere.

Every command loads before it clears or writes anything. So a source that publication could
delete is refused while it is still intact.

These are the checks the publisher needs to produce correct pages.
Spec core's validator handles these checks:

- Checked diagrams.
- Realization bindings.
- The registry mirror.
- Contract examples.

Loading never fetches anything. Loading never reads implementation files.

The **root Module** is the first Module in registry order that no Module contains.
The loaded model holds:

- The Module records.
- The defined concepts and realizations with their owner, document and definition.
- One page per document.

Each page holds:

- Source and metadata paths.
- Route.
- Staged path.
- Title.
- Reading content.
- Reading and metadata digests.
- Document identity.
- Owner.
- Reading collection (the role).
- Whether it is its Module's entry.
- The selecting Modules.

**Selecting Modules.** For each Module, the publisher computes its one-level
[Spec context](../../glossary.json#concept.spec-context) from:

- The publisher selects the Module's own documents (`owns`).
- For every `contains` and `uses`, when the `relies_on` list is present, the publisher selects only
  the target's entry and the documents defining those identities.
  Otherwise, the publisher selects the target's documents.
- The publisher selects the documents of every `module` or `document` inclusion.

This is the Protocol's context selection.
For the same registry and documents, the resulting per-document list must equal Spec core's
`selected-by` index. A page lists every Module whose context holds it, in registry order, each
with its reasons. A reason is `{relation, id}`.
Its `relation` is `owns`, `contains` or `uses`. Its `id` is the owning or target Module.
An inclusion reason is `{relation: "includes", kind, id}`.
Its `kind` is `module` or `document`. Its `id` is the included Module or document.
Reasons are sorted by `relation`, then `kind`, then `id`.

## Source digest {#source-digest}

`hash(value)` is `sha256:` followed by the lowercase hex SHA-256 of the bytes.
The source digest is `hash` of the serialization of the ordered list of `[path, hash(bytes)]`
pairs. The serialization is the compact JSON that ECMAScript's `JSON.stringify` writes:

- A `[`, then the pairs separated by `,`, then a `]`.
- Each pair is `["<path>","<hash>"]`, with no whitespace anywhere.
- Inside a string, `"` and `\` are escaped with a backslash. Control characters cannot occur, since
  source paths exclude them. Every other character, non-ASCII included, is written as it is.
- The text is encoded as UTF-8 and has no final newline.

For example, a configuration `{}` and a registry `{"schema_version": 3}`, each followed by a
newline, serialize as:

```json
[[".concorde/config.json","sha256:ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356"],[".concorde/specs.json","sha256:feaa30087d2ef50cda938089d9ea5d4dd7f0803b82ec53f10561078a9e9259db"]]
```

The digest of that text is
`sha256:4cf77a4e7432e482a2255f3b172934c97232c6e6c5de74f6b9659719e48287d1`.
A real project has more pairs. The pairs cover these sources in order:

- The configuration.
- The registry.
- Both members of every document in registry order.
- When the root Module declares one, the glossary.
- Last, when it exists, the site identity `docsite/site.json`.

The site identity shapes every page.
Any byte change in any of them, including a metadata-only edit, changes it.
It identifies inputs. It is not a claim about meaning.

## Routes {#routes}

When every registered document lies under `specs/`, a page's staged path is its source path with a
leading `specs/` removed. Otherwise, its staged path is its source path.
Its route is `/specs/` followed by the staged path without `.md`.
A page has no other route.
Its model title is the document's first level-1 heading, falling back to the owner's title.
When they link an entry and its implementation pages, the provenance bar and the entry's list of
implementation documents use the model title.

## Staging

`materializeScoped(model, mode)` writes into the **staging directory** of its mode:
`docsite/.generated/preview/` for `preview` (the default) and `docsite/.generated/production/`
for `build`. The steps below name paths inside that directory.

1. It deletes the staging identity record, then the previous `content/` directory.
2. For every page, it writes `content/specs/<staged path>` with front matter giving:
   - The slug.
   - The title and navigation label.
   - The Module documents sidebar.
   - A table of contents of level-2 and level-3 headings.

   For an entry, the title and navigation label are the Module's title.
   Otherwise, they are the file name without `.md`.
   The page body still shows the document's own level-1 heading.
   An implementation page shows the Module documents sidebar for orientation without being listed
   in it. The body is the reading with these rewrites, applied outside fenced code only:
   - **links**: when their target path resolves relative to the source file to a registered
     document, a relative Markdown link `[label](path)` or image `![label](path)` uses that page's
     route.
     The query and fragment are kept in order.
     When a link's target is the glossary, the link uses the glossary page's route, with the
     concept's anchor when it has a fragment.
     On such a link, a fragment naming no declared concept fails staging.
     A path that resolves to no registered document fails staging.
     A link's text may wrap onto the next line. These links are left unchanged:
     - URLs with a scheme or starting with `/`.
     - Bare `#fragment` links.
     - Links inside inline code spans, including a span that wraps onto later lines of the same
       paragraph. A span opens and closes with backtick runs of the same length. It never
       crosses a blank line or a fence.
   - **realization anchors**: when the reading does not carry a node's identity, the node gets an
     anchor at its `meaning` anchor.
   - **owned terms**: the entry page of a Module that owns concepts ends with a Terms list linking
     each to the glossary page.
   - **definition headings**: a heading of any level `req.<id> — Title` or
     `scenario.<id> — Title` (em dash, en dash or hyphen) becomes `Title {#<id>}`.
     These are exactly the headings loading takes as definitions, so every identity it admits is
     anchored.
   - **contract anchors**: an HTML anchor whose id is the contract identity is inserted before
     each `concorde-contract` fence.
   - **diagrams**: each `d2` block is rendered by the `d2` program to an SVG staged beside the page.
     The block is replaced by an image of it. A checked block is first parsed in the semantic
     subset. A violation of that subset fails the build with the document and the line of its
     source file. Each shape of the checked block then receives a class of the house style from what its label
     resolves to:
     - The page's Module.
     - A descendant.
     - Another Module.
     - A concept.
     - A realization.
     - A realization with file rows.
     - A qualified node.

     When an edge of the checked block joins two Modules without a label, it receives the class
     `uses`.
     Otherwise, it receives the class `relates`.
     When no edge touches a container of five or more children, it uses a near-square grid instead
     of one long row.
     When a qualified shape names one of the page's own nodes, the shape shows only the node's
     title.
     The enclosing Module already shows the owner.

     A `d2 illustrative` block is rendered as written.
     It is preceded by the label
     `Illustrative, non-normative. This diagram explains; it declares no relationship.`
   - **page anchors**: unless the reading already carries them, anchors are inserted after the
     level-1 title for the Module identity (on its entry) and the document identity.
3. When the root Module declares a glossary, it writes the Glossary page at the route of the
   glossary's path without `.json` (`/specs/concorde/glossary` here). An index comes first: every
   term by initial letter, each linking to its entry.
   Level-2 group headings follow, anchored `terms.<module id>`.
   "Core terms" for the concepts the root Module owns comes first.
   One group per Module the root contains follows, in `contains` order.

   Each contained Module's group holds every concept whose owner is that Module or lies below it.
   An owner outside the root's tree gets the group of its own topmost Module.
   Within a group, the concepts are sorted by title, letter case ignored.
   Each concept has a level-3 heading anchored by its identity, with:
   - Its definition, with term links inside it pointing to anchors on the same page.
   - Its owning Module's entry and a link to its explanation.
   - Any retirement or external-conflict note.

   The page's table of contents lists the groups only.
4. It writes `specs-sidebar.json` with `moduleDocumentsSidebar` alone. The Glossary page is the
   last item of the declaring Module's category.
5. Last, it writes the staging identity record `scoped-materialization.json`:
   `{"schema_version": 2, "sourceDigest": "<source digest>"}`.

A failure leaves no identity record. The build hooks then refuse the partial staging.
`npm run validate` performs step 2 in memory for every page.
It reports the same link and rendering failures without writing.

`preparePublication(root, {mode})` performs these steps:

- It checks the configuration.
- It loads.
- It stages.
- It clears the Docusaurus generated directory of the mode.

It stages into the staging directory of the mode.
For `preview` (the default), the Docusaurus generated directory is `.docusaurus`.
For `build`, it is `.generated/docusaurus-production`.
The webpack filesystem cache lives inside that directory.
Each launch therefore compiles from scratch.
The two modes never share or clear each other's files.
The publisher tells the Docusaurus process its mode through the environment variable
`CONCORDE_PUBLICATION_MODE`, `preview` or `build`, so that the site configuration reads the
staging directory of that mode.

## Navigation

The Module documents sidebar follows the `contains` tree, starting from the uncontained Modules
in registry order. Children follow the parent's `contains` order.
A Module with `module`-role topics or children is a category.
Its label is the Module title. Its link opens its entry.
Its items are its `module`-role topics in `owns` order, then its children.
A Module with neither is a single link to its entry. The entry is never listed twice.
Categories below the top level start collapsed. Document labels are file names without `.md`.
A document appears only under its owner.

No sidebar or tab lists an `implementation`-role document. Readers reach one from:

- Its Module's entry, which ends with a folded list of them.
- Links and term links in other documents.
- Search.
- Its route.

## Provenance

The content plugin publishes Docusaurus global data with `schema_version`, `rootModule`, `pages`
and `siteIdentity`. `pages` holds every page without its reading body.
A layout wrapper finds the current page by route. It renders the provenance bar with:

- The collection label.
- On an implementation page, a link to its owner's entry.
- The source path.
- A "Spec metadata" disclosure.

The disclosure holds:

- The document identity.
- The owner.
- The selecting Modules with their reasons.
- The metadata path.
- Both digests.

A footer wrapper ends a Module's entry page with a folded "Implementation documents (<count>)"
list. In `owns` order, the list links to each of the owner's implementation pages.
When the Module owns none, the footer wrapper shows nothing.
Without user documents, the site root uses `rootModule` to redirect to the root Module's entry.

## Build hooks {#build-hooks}

The Docusaurus configuration loads the site identity and the model at start-up.
The Spec docs instance reads `content/specs` of the mode's staging directory at route base
`/specs`. Its sidebar is that directory's `specs-sidebar.json`.
User documents are a separate instance at route base `/` with a generated sidebar.
With user documents, the root redirect page is left out.
Each custom docs collection is a separate instance. Local search indexes all of them.
The navigation lists these in order:

- User documents.
- Module documents.
- Custom docs.

These are build errors:

- Broken links.
- Broken anchors.
- Duplicate routes.

The content plugin:

- On load, reloads the model. It requires the staging identity record of its mode to have
  `schema_version` 2 and the current source digest.
- After the build, reloads the model. It fails if any of these conditions holds:
  - The source digest changed.
  - The staging record no longer matches.
  - Any registered page route is missing from the rendered routes.
  - A rendered route under `/specs` is neither a registered page's route nor the glossary's.

  It then writes `build-manifest.json`.

When any of these conditions holds during site configuration, user documents admission fails:

- The directory is missing.
- The directory has no root page, or more than one.
- The directory contains a registered document.
- A top-level document or folder would publish under `/specs`, `/search` or a custom docs route.

When any of these conditions holds, custom docs admission fails:

- A collection directory or sidebar file is missing.
- A collection directory contains a registered document.
- `custom-docs/index.ts` does not export an object.
- `custom-docs/index.ts` exports `plugins` or `navbarItems` that is not an array.
- A docs plugin among those `plugins` names a missing directory, or one that contains a registered
  document.

A directory contains a registered document when the document lies below it or when a symbolic
link inside it reaches the document or a directory holding it. The check follows every link to a
directory and walks each directory it reaches once, so links inside linked directories count too.

An omitted property adds nothing.

## Preview {#preview}

A running Docusaurus cannot show a changed Spec.
The content plugin refuses staged pages whose source digest differs from the sources.
When staging runs, these are fixed:

- The pages.
- The sidebars.
- The navigation.

`npm run start` therefore supervises the preview instead of relying on Docusaurus's own watching.
The content plugin watches nothing.

The supervisor stages with `preparePublication(root)`.
It starts `docusaurus start` with the command's arguments. Its inputs are:

- `docsite/site.json`.
- The configuration.
- The registry.
- Both members of every registered document.
- The glossary the root Module declares.

It watches their directories, not the files, so an editor that saves by replacing a file is still
seen. Changes within 300 ms form one restart, with these steps:

- The supervisor stops Docusaurus (`SIGTERM`, then `SIGKILL` after ten seconds).
- The supervisor stages again.
- The supervisor recomputes the inputs and their watched directories.
- The supervisor starts Docusaurus again with `--no-open` added so that no further browser window
  opens.

A change that arrives during a restart causes one more restart after it.

When staging fails:

- No preview runs.
- The supervisor reports the error in full.
- The supervisor keeps its last watched directories.
- The supervisor retries on the next change to an input or to any `.md` or `.md.json` file in them.

The model that failed may list a document not yet written.
When the first staging fails, there is nothing to watch.
The first staging failure also makes the command exit nonzero.

When Docusaurus exits on its own, the supervisor reports the status and starts it again on the
next change.

Interrupting the command has these effects:

- The command stops Docusaurus.
- The command stops the watchers.
- The command exits.

In any state, an interrupt has these effects:

- The command stops Docusaurus.
- The command stops the watchers.
- The command exits.

The diagram shows the supervisor's states and what moves it between them:

```d2 illustrative
direction: down
start: "npm run start" {shape: oval}
staging: Staging
running: "Running:\nDocusaurus serves the pages"
restart: "Restart pending:\nchanges gathered for 300 ms,\nthen Docusaurus stopped"
failed: "Failed, waiting:\nno preview"
exited: "Exited on its own:\nno preview"
end: "Exit nonzero" {shape: oval}

start -> staging
staging -> running: succeeds
staging -> end: the first staging fails
staging -> failed: a later staging fails
running -> restart: an input changes
running -> exited: Docusaurus exits
exited -> restart: an input changes
failed -> restart: an input or any .md\nor .md.json there changes
restart -> staging
```

A change that arrives during a restart is kept and makes one more restart once it ends.

## Validation

`validateScopedBuild(root, directory)` reloads the model from the current sources.
It fails unless all of these conditions hold:

- The candidate's `build-manifest.json` has the site manifest's `schema_version` (23, see the
  [contracts](contracts.md)).
- The candidate's manifest has the current source digest.
- Its `pages` equal the expected entries exactly and in order.
- Every internal link resolves.

For links, it parses every HTML file of the candidate and collects:

- `id` and `a name` anchors.
- The `href` of `a` and `area` elements.
- `base` elements.
- Meta-refresh redirects.

When a URL has the site's origin and its path lies under the base URL, it is internal.
Each internal URL must reach a file (`path`, `path.html` or `path/index.html`).
Redirect pages are followed, keeping the fragment. A redirect cycle fails.
A nonempty fragment must name an anchor on the final page.
Percent-escapes of unreserved characters are compared decoded. Every registered route is checked as
well. A failure names the referring file and the destination. External URLs are never fetched.
Validation repairs nothing.

## Promotion

`buildSite()` performs these steps:

- It checks the configuration.
- It deletes `docsite/.generated/candidate`.
- It runs `preparePublication` in `build` mode.
- It runs `docusaurus build --out-dir` into the candidate with the production generated directory.
- It validates the candidate.
- It calls `promoteCandidate`.

On any failure, `buildSite()` deletes the candidate and rethrows.

`promoteCandidate(candidate, destination, backup)` performs these steps:

1. It deletes the backup.
2. When the destination exists, it renames the destination to the backup.
   On the first publication there is no destination, so it skips this step and backs up nothing.
3. It renames the candidate to the destination.
4. When step 2 made a backup, it deletes the backup.

Steps 2 and 3 are the promotion. Each is one rename, so a failed rename moves nothing.
When step 2 fails, nothing was moved: the destination is untouched and the build fails.
When step 3 fails after step 2 made a backup, the function renames the backup back to the
destination, then the build fails. It restores only a backup that step 2 made.

Step 4 is cleanup after a finished promotion, outside that rollback.
A recursive deletion that fails may already have removed part of the backup.
The backup is then no safe source to restore from.
So when step 4 fails, the promoted site stays in place.
The function reports the failure as a warning naming the backup, and the build succeeds.
The next build deletes what is left of the backup in step 1.

If the filesystem fails while renaming the backup back, the build fails with that error.
This rollback failure leaves the previous site in the backup directory,
`docsite/.generated/previous-build/`, for manual recovery.

The function checks nothing itself. Only `buildSite` calls it, after validation.
The caller must own the candidate, build and backup directories exclusively for the whole build,
as the [build commands](contracts.md#build-commands) require of whoever runs them.
