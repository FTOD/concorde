# Views scenarios

Concrete situations of [Views](module.md). Exact formats are in [contracts](contracts.md).
The publisher's mechanics are in the [pipeline](pipeline.md).

## Loading the Specs

### scenario.views.load-registry — Loading the registered Specs

- GIVEN a project whose registry `.concorde/specs.json` lists Modules with their entries and owned documents
- WHEN the publisher loads the project
- THEN it returns one model of the Modules
- AND the model includes their `contains` tree and the root [Module](../../glossary.json#concept.module)
- AND the model includes one page per owned document
- AND loading the same unchanged inputs again gives the same model and the same source digest

The root Module is the first Module in registry order that no Module contains. The Module relations
the model keeps serve navigation, provenance and admission. The publisher does not compare the
registry with the entries' `module` blocks. The [Spec](../../glossary.json#concept.spec) validator
does.

### scenario.views.load-registry-refused — Inputs the publisher cannot publish are refused

- GIVEN a project with an input that [loading and admission](pipeline.md#loading-and-admission)
  refuses
- WHEN the publisher loads the project
- THEN loading fails with an error naming the source
- BUT nothing is staged or promoted

The pipeline lists every such input, one per item. Examples are an unsafe path, a symbolic link,
a source that is not valid UTF-8, duplicate JSON keys, a duplicate identity and a composition
cycle. A Mermaid block, an unresolved `relies_on` identity and a malformed glossary are refused
too.

### scenario.views.reject-reading-collection — A document whose role or shape cannot be published is refused

- GIVEN a document whose role or shape [loading and admission](pipeline.md#loading-and-admission)
  refuses
- WHEN the publisher loads the project
- THEN loading fails with an error naming the offending document
- AND no candidate is staged or promoted

Examples are metadata that is not schema 3 or has no valid `role`, and an entry `module.md` whose
role is `implementation`. A `module`-role document containing a requirement, a scenario or a
canonical contract is refused too.

### scenario.views.diagram-subset-refused — A checked diagram that sets its own look is refused

- GIVEN a document whose checked `d2` block sets a style, shape, class or layout, or draws an edge other than `->`
- WHEN the site is built
- THEN the build fails with an error naming the document, the line and the statement that leaves the semantic subset
- AND no candidate is promoted

See [req.views.diagram-subset](requirements.md#req.views.diagram-subset).

### scenario.views.d2-missing — Without the d2 program diagrams cannot be published

- GIVEN a registered document containing a `d2` block
- AND no `CONCORDE_D2`, no `.concorde/tools/d2` and no `d2` program on `PATH`
- WHEN the site is built
- THEN the build fails with an error naming the diagram's document and line
- AND the error says how to install the program
- AND no candidate is promoted

See [req.views.d2-failure](requirements.md#req.views.d2-failure).

### scenario.views.d2-program — The installed d2 is found without configuration

- GIVEN a project that may have `CONCORDE_D2` set and may have `.concorde/tools/d2`, which the
  Concorde installer places
- WHEN the publisher looks for the `d2` program
- THEN when `CONCORDE_D2` is set, it uses `CONCORDE_D2`
- AND otherwise the installed `.concorde/tools/d2`
- AND otherwise `d2` on `PATH`

See [req.views.d2-program](requirements.md#req.views.d2-program).

## Pages and navigation

### scenario.views.publish-candidate — One canonical page per registered document

- GIVEN a valid registered project
- WHEN the site is built
- THEN every registered document is published at exactly one page
- AND its route is `/specs/` followed by its source path without `.md`
- AND when every document lies under `specs/`, a leading `specs/` is removed from that source path
- AND each Module appears in the navigation under the Module that contains it
- AND the uncontained Modules appear at the top level
- AND a Module's name opens its entry, with its explanatory topics and then its child Modules beneath it
- AND D2 diagrams render where the document places them

### scenario.views.reading-collections — Implementation documents are reached from their Module

- GIVEN a project in which some documents declare the role `implementation`
- WHEN the site is built
- THEN the navigation bar shows the Module documents tab and no Implementation documents tab
- AND its sidebar lists every entry and `module`-role topic and no `implementation`-role document
- AND the entry page of each Module owning `implementation`-role documents ends with a folded list
- AND that list is labelled "Implementation documents" with their count and links to each of them
- AND each implementation page is published at its route with every identity anchored
- AND each implementation page shows the Module documents sidebar without being listed in it
- AND each implementation page names its Module, linking to the Module's entry
- AND changing only a document's role moves it between the sidebar and its Module's list without changing its route

### scenario.views.reading-collections-single — The navigation does not depend on implementation documents

- GIVEN a project in which no document declares the role `implementation`
- WHEN the site is configured
- THEN the navigation bar shows the same Spec tab, Module documents, as when some document does
- AND no entry page ends with a list of implementation documents

### scenario.views.publish-reference-link — A shared document is published once

- GIVEN one document owned by Module A and selected by Modules B and C through `uses` or `includes`
- WHEN the site is built
- THEN the document has one page under A
- AND B and C list no copy of it in their navigation
- AND its provenance names A as owner
- AND its provenance lists every selecting Module with the relation that selected it, exactly as
  Spec core's `selected-by` index lists them
- AND links from B's and C's documents lead to that page and its anchors without embedding its content

### scenario.views.id-anchors — Definition titles keep their identities as anchors

- GIVEN a document defining requirements, scenarios and a contract, and anchoring concepts and realizations
- WHEN the site is built
- THEN each requirement and scenario heading shows only its title
- AND its identity is the heading's anchor
- AND the page's table of contents uses the titles
- AND every concept, realization and contract identity and the document identity are anchors on
  the page
- AND on an entry, the Module identity is also an anchor on the page
- AND a link of the form `path#identity` from another page resolves to that anchor
- BUT the source document, the definition bodies and fenced examples are unchanged

Two definitions with the same title keep distinct anchors. Changing a title does not change its
anchor.

### scenario.views.glossary-page — The glossary is one page under the root Module

- GIVEN a project whose root Module declares a glossary with several concepts
- WHEN the site is built
- THEN one Glossary page is listed under the root Module in the navigation
- AND the page shows every concept with its identity as anchor and its definition
- AND each concept also shows its owning Module and a link to its explanation
- AND the page groups the concepts, first those the root Module owns
- AND then it shows one group per Module the root contains, in `contains` order
- AND each such group holds the concepts whose owner is that Module or lies below it
- AND each group is sorted by title
- AND an index before the groups lists every term by initial letter, each linking to its entry
- AND the entry page of a Module that owns concepts lists them, each linking to the glossary page
- BUT no document's source changes

### scenario.views.term-links — Term links lead to the glossary page

- GIVEN a document that links a term to the glossary, and another that links the glossary file without a fragment
- WHEN the site is built
- THEN the term link leads to the concept's anchor on the glossary page
- AND the plain link leads to the page itself
- BUT a term link to a concept the glossary does not declare fails the build and promotes nothing

### scenario.views.illustrative-label — An illustrative diagram is labelled

- GIVEN a document containing a D2 block marked `illustrative`
- WHEN the site is built
- THEN the diagram renders in its place with a visible label saying that it is illustrative and not normative
- AND a checked D2 diagram renders without that label

### scenario.views.diagram-style — The look of a checked diagram comes from what it names

- GIVEN a checked D2 diagram that nests the page's child Modules and realizations with their files
- AND the diagram draws an edge between two Modules and an edge with a verb between two nodes
- WHEN the site is built
- THEN the page's Module, its child Modules, other Modules, concepts and realizations each render in their own fixed look
- AND a realization drawn with files renders as a table whose rows are the files
- AND the edge between Modules renders as a solid arrow
- AND the edge between nodes renders as a dashed arrow labelled with its verb
- BUT the source block holds no styling

See [req.views.diagram-look](requirements.md#req.views.diagram-look).

### scenario.views.inline-diagrams — Diagrams render where their documents place them

- GIVEN a registered document containing D2 fences
- WHEN the site is built and promoted
- THEN each diagram renders on that document's page at the position of its fence, from the fence's own text
- AND the site contains no page, navigation entry or data file drawn from diagrams or relations outside the documents

See [req.views.diagram-source-identity](requirements.md#req.views.diagram-source-identity).

## Building and promotion

### scenario.views.materialize — Staging the pages

- GIVEN a loaded project model
- WHEN the publisher stages it
- THEN it replaces the staged content in its mode's staging directory under `docsite/.generated/`
  with one Markdown page per document and the one Module documents sidebar
- AND an implementation page displays that sidebar without being listed in it
- AND each page carries its route, title and reading collection
- AND each page's table of contents lists its level-2 and level-3 headings
- AND only after every page and sidebar is written does it write the staging identity record with the source digest

### scenario.views.materialize-failure — A failed staging is never built

- GIVEN a staging that fails before every page and sidebar is written
- WHEN a later build step reads the staged content
- THEN there is no staging identity record
- AND the build refuses the partial staging

### scenario.views.outputs-disjoint — Sources inside publication output are refused

- GIVEN a registered source inside `docsite/.generated/`, `docsite/build/` or `docsite/.docusaurus/`
- WHEN `npm run start`, `npm run validate` or `npm run build` runs
- THEN it fails naming the source and the output directory
- AND it clears nothing
- AND every source keeps its bytes

A source is inside an output directory by its path or by its physical location. When one of those
directories is a symbolic link, publication is refused the same way.

See [req.views.outputs-disjoint](requirements.md#req.views.outputs-disjoint).

### scenario.views.production-preview-isolation — A build beside a preview leaves the preview alone

- GIVEN a running `npm run start` preview that has staged its pages
- WHEN `npm run build` runs beside it
- THEN the build stages into its own staging directory
- AND the preview's staged pages, sidebar, staging identity record and Docusaurus files keep their
  bytes

See [req.views.production-preview-isolation](requirements.md#req.views.production-preview-isolation).

### scenario.views.build-site — A build runs every step before promotion

- GIVEN installed site dependencies and a valid registered project
- WHEN `npm run build` runs
- THEN it clears the previous candidate
- AND it stages the Specs
- AND it builds the candidate
- AND it validates the candidate
- AND only after all these steps does it promote the candidate

### scenario.views.build-site-failure — A failed step stops the build

- GIVEN a build in which Docusaurus fails to start, exits nonzero or the validation fails
- WHEN `npm run build` runs
- THEN the build stops with an error
- AND it deletes the candidate and promotes nothing

### scenario.views.validate-candidate-mismatch — A stale or incomplete candidate is rejected

- GIVEN a candidate whose site manifest version, source digest or page inventory differs from the current sources, or which contains an internal link to a missing page or anchor
- WHEN the candidate is validated
- THEN validation fails, naming the problem
- AND for a link, validation also names the referring page and destination
- BUT it repairs nothing and promotes nothing

### scenario.views.publish-preserves-previous-on-failure — A failed build keeps the published site

- GIVEN a published site and a build in which sources change during the build, a registered page is not rendered, a link does not resolve or a diagram fails to render
- WHEN the build checks the candidate
- THEN promotion is refused
- AND the candidate is deleted
- AND the published site is unchanged

### scenario.views.first-publication — The first build publishes without a backup

- GIVEN a valid registered project and no published site in `docsite/build/`
- WHEN `npm run build` runs
- THEN the candidate becomes the published site in `docsite/build/`
- AND no backup is made or left in `docsite/.generated/previous-build/`

See [req.views.promote-atomic](requirements.md#req.views.promote-atomic).

### scenario.views.backup-cleanup-failure — A failed backup cleanup keeps the promoted site

- GIVEN a published site and a build whose candidate is promoted
- WHEN removing the previous site's backup fails after deleting part of it
- THEN the promoted site stays complete in `docsite/build/`
- AND the build reports the failure as a warning naming the backup
- AND the build succeeds

See [req.views.promoted-site-kept](requirements.md#req.views.promoted-site-kept).

### scenario.views.rebuild-removes-stale-pages — Rebuilding removes pages no longer produced

- GIVEN a published site containing pages or files that the current sources no longer produce
- WHEN a new build succeeds and is promoted
- THEN the published site contains only what the new build produced

### scenario.views.preview-restart — A running preview follows the Specs

- GIVEN a running `npm run start` preview
- WHEN a registered document or its metadata, the glossary, the registry, the configuration or `docsite/site.json` changes, including a change that adds, moves or removes a document
- THEN the preview stops
- AND the Specs are staged again
- AND the preview starts again from the new staging without opening another browser window
- AND changes made together cause one restart

See [req.views.preview-follows-specs](requirements.md#req.views.preview-follows-specs) and
[req.views.preview-restart](requirements.md#req.views.preview-restart).

### scenario.views.preview-restart-failure — A staging failure during the preview is reported and retried

- GIVEN a running `npm run start` preview
- WHEN a change leaves Specs that cannot be staged, such as metadata listing a document not yet written
- THEN the preview stops
- AND the error is reported in full
- AND the next change to an input or to a Spec document beside one stages again
- AND when that staging succeeds, it starts the preview
- BUT when the first staging of the command fails, the command exits nonzero

### scenario.views.cross-module-link — Cross-Module links resolve to the owner's page

- GIVEN a document of Module A that links, by relative source path and fragment, to a definition in a document owned by Module B
- WHEN the site is built and validated
- THEN the rendered link leads to the canonical page of B's document
- AND the requested anchor exists there

A document has only its canonical route. Moving a document therefore requires updating the links
to it. A link to a page or anchor that does not exist stops promotion, as
[validate-candidate-mismatch](#scenario.views.validate-candidate-mismatch) states.

## Site configuration

### scenario.views.user-docs — User documents as the home page and first tab

- GIVEN `docsite/site.json` sets `userDocs.path` to a directory whose root page is `README.md`, `README.mdx`, `index.md` or `index.mdx`
- WHEN the site is built
- THEN the root page is the site's home page at `/`
- AND every other document is published at its path in the directory
- AND the first navigation tab, labelled `userDocs.label` or "User documents", leads to them
- AND its sidebar follows the directory's folders
- AND the Module documents tab and one tab per configured custom docs collection follow in that order
- BUT user documents are not Spec pages
- BUT user documents are not listed in the site manifest
- BUT user documents belong to no Module
- BUT user documents grant no context

### scenario.views.publish-homepage-default — No user documents configured

- GIVEN `docsite/site.json` has no `userDocs`
- WHEN the site is built
- THEN the site root redirects to the root Module's entry page
- AND the site root shows a visible link to it
- AND the template adds no Concorde-specific content

### scenario.views.user-docs-invalid — An invalid user documents entry is refused

- GIVEN `docsite/site.json` contains a `userDocs` value that is not an object with a relative `path` and an optional nonblank `label`, or still contains the removed `homepage` field
- WHEN the site identity is loaded
- THEN loading fails with an error naming `docsite/site.json` and the invalid field
- AND a `homepage` field is told to become the root page of user documents
- AND no candidate is promoted

### scenario.views.user-docs-refused — User documents that cannot be published fail the build

- GIVEN `userDocs.path` names a missing directory, one without a root page, one containing a
  registered Spec document, or one whose top-level document or folder would publish under `/specs`,
  `/search` or a custom docs route
- WHEN the site is configured
- THEN the build fails naming `userDocs` and the offending path
- AND nothing is promoted

### scenario.views.custom-docs — Custom docs in their own tabs

- GIVEN `docsite/site.json` configures `customDocs` collections, or the project provides `docsite/custom-docs/index.ts`
- WHEN the site is built
- THEN each collection and each extension item has its own navigation entry after the Module documents tab
- AND custom pages are not listed in the site manifest
- AND custom pages belong to no Module

### scenario.views.custom-docs-refused — Invalid custom docs fail the build

- GIVEN a custom docs collection containing a registered Spec document, a route that conflicts with a Spec page, missing content or a broken internal link
- WHEN the site is built
- THEN the build fails naming the collection or link
- AND nothing is promoted

### scenario.views.protocol-docs-tab — Concorde publishes its Protocol as custom docs

- GIVEN Concorde's `docsite/site.json` configures `protocol/` as a custom docs collection with its own sidebar
- WHEN Concorde's site is built
- THEN the Spec Protocol appears at `/protocol` with its chapter sidebar and search
- AND its pages carry no Spec provenance
- AND its pages belong to no Module
- BUT a scaffolded project receives neither this collection nor its sidebar

## Scaffold

### scenario.views.scaffold-propose — Proposing a docsite scaffold

- GIVEN an initialized project and optional `--title`, `--repository`, `--url`, `--base-url` and `--github-pages` options
- WHEN `concorde docsite --propose` runs
- THEN it returns a deterministic scaffold proposal listing the template files and a new
  `docsite/site.json`
- AND with `--github-pages`, the proposal also lists the deployment workflow
- AND it reports whether Node.js 20 or newer and npm are present, without changing the proposal
- AND it lists already existing destinations as conflicts
- BUT it writes nothing to the project

### scenario.views.scaffold-apply — Applying a scaffold proposal

- GIVEN a proposal that still matches the installed template and a project in which none of its destinations exist
- WHEN `concorde docsite --apply --proposal PATH` runs
- THEN it creates exactly the proposed files with the proposed bytes
- AND it returns `success` with their paths
- AND it leaves every other file, including every Spec document, unchanged

### scenario.views.scaffold-apply-repeat — Applying an applied proposal changes nothing

- GIVEN a proposal whose files all already exist with the proposed bytes
- WHEN `concorde docsite --apply --proposal PATH` runs
- THEN it returns `unchanged` without writing

### scenario.views.scaffold-stale-rejected — A stale or altered proposal is refused

- GIVEN a proposal that no longer matches the installed template: another proposal version, a changed template digest, or an altered file list or hash
- WHEN it is applied
- THEN the result is `invalid`
- BUT nothing is written

### scenario.views.scaffold-concurrent-create — A destination created during apply rolls back

- GIVEN a valid proposal
- AND when applying starts, its destinations are absent
- WHEN another process creates one of the destinations during application of the proposal, even
  just before that destination is created
- THEN the result is `failed`
- AND every file this application had already created is removed
- BUT files it did not create keep their bytes
- AND a created file that another process replaced keeps that process's bytes

### scenario.views.scaffold-uninitialized — A proposal is not applied to an uninitialized project

- GIVEN a saved valid proposal
- AND the project's Spec configuration has since been removed or made unreadable
- WHEN `concorde docsite --apply --proposal PATH` runs
- THEN the result is `invalid`, asking for initialization
- BUT nothing is written

### scenario.views.scaffold-conflict — Existing destinations block a scaffold

- GIVEN a valid proposal and a project in which at least one destination already exists, but not every destination has the proposed bytes
- WHEN it is applied
- THEN the result is `conflict`, naming every existing destination
- BUT no file is written

A partially applied proposal, whose existing destinations already have the proposed bytes and whose
other destinations are absent, is a conflict too.
