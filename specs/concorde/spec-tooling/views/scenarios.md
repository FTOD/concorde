# Views scenarios

Concrete situations of [Views](module.md). Exact formats are in [contracts](contracts.md) and the
publisher's mechanics in the [pipeline](pipeline.md).

## Loading the Specs

### scenario.views.load-registry — Loading the registered Specs

- GIVEN `.concorde/config.json` names a registry whose Modules list their entries and owned documents
- WHEN the publisher loads the project
- THEN it returns one model of the Modules, their `contains` tree, the root Module and one page per owned document
- AND loading the same unchanged inputs again gives the same model and the same source digest

The root Module is the first Module in registry order that no Module contains. The Module relations
the model keeps serve navigation, provenance and admission. The publisher does not compare the
registry with the entries' `module` blocks; the Spec validator does.

### scenario.views.load-registry-refused — Inputs the publisher cannot publish are refused

- GIVEN an unsafe path, a symbolic link, duplicate JSON keys, a duplicate identity, a composition cycle, a Mermaid block, a `relies_on` identity its target does not define, or a Terminology import row that does not link to its concept's defining document
- WHEN the publisher loads the project
- THEN loading fails with an error naming the source
- BUT nothing is staged or promoted

### scenario.views.reject-reading-collection — A document without a valid role is refused

- GIVEN a document whose metadata is not schema 3 or has no valid `role`, an entry `module.md` whose role is `implementation` or whose metadata lacks the `module` block, another document whose metadata has a `module` block, a `module`-role document containing a requirement, a scenario or a canonical contract, or an `implementation`-role document defining a concept
- WHEN the publisher loads the project
- THEN loading fails with an error naming the offending document
- AND no candidate is staged or promoted

### scenario.views.diagram-subset-refused — A checked diagram that sets its own look is refused

- GIVEN a document whose checked `d2` block sets a style, shape, class or layout, or draws an edge other than `->`
- WHEN the site is built
- THEN the build fails with an error naming the document, the line and the statement that leaves the semantic subset
- AND no candidate is promoted

See [req.views.diagram-subset](requirements.md#req.views.diagram-subset).

### scenario.views.d2-missing — Without the d2 program diagrams cannot be published

- GIVEN a registered document containing a `d2` block
- AND no `d2` program on `PATH` and no `CONCORDE_D2`
- WHEN the site is built
- THEN the build fails with an error naming the diagram's document and line and saying how to install the program
- AND no candidate is promoted

See [req.views.d2-failure](requirements.md#req.views.d2-failure).

### scenario.views.d2-program — The installed d2 is found without configuration

- GIVEN a project into which the Concorde installer placed `.concorde/tools/d2`
- WHEN the publisher looks for the `d2` program
- THEN it uses `CONCORDE_D2` when that is set
- AND otherwise the installed `.concorde/tools/d2`
- AND otherwise `d2` on `PATH`

See [req.views.d2-program](requirements.md#req.views.d2-program).

## Pages and navigation

### scenario.views.publish-candidate — One canonical page per registered document

- GIVEN a valid registered project
- WHEN the site is built
- THEN every registered document is published at exactly one page whose route is `/specs/` followed by its source path without `.md`, with a leading `specs/` removed when every document lies under `specs/`
- AND each Module appears in the navigation under the Module that contains it, and root Modules at the top level
- AND a Module's name opens its entry, with its explanatory topics and then its child Modules beneath it
- AND D2 diagrams render where the document places them

### scenario.views.reading-collections — Two reading collections, one Module specification

- GIVEN a project in which some documents declare the role `implementation`
- WHEN the site is built
- THEN the navigation bar shows the Module documents and Implementation documents tabs
- AND Module documents lists every entry and `module`-role topic, and Implementation documents lists only `implementation`-role documents under the same Module tree, omitting Modules without such documents
- AND an implementation page links back to its Module's entry, and the entry's pages link to the Module's implementation documents
- AND changing only a document's role moves it between tabs without changing its route

### scenario.views.reading-collections-single — Without implementation documents there is one tab

- GIVEN a project in which no document declares the role `implementation`
- WHEN the site is built
- THEN the navigation bar shows only the Module documents tab

### scenario.views.publish-reference-link — A shared document is published once

- GIVEN one document owned by Module A and selected by Modules B and C through `uses` or `includes`
- WHEN the site is built
- THEN the document has one page under A, and B and C list no copy of it in their navigation
- AND its provenance names A as owner and lists every selecting Module with the relation that selected it, exactly as Spec core's `selected-by` index lists them
- AND links from B's and C's documents lead to that page and its anchors without embedding its content

### scenario.views.id-anchors — Definition titles keep their identities as anchors

- GIVEN a document defining requirements, scenarios and a contract, and anchoring concepts and realizations
- WHEN the site is built
- THEN each requirement and scenario heading shows only its title, and its identity is the heading's anchor
- AND the page's table of contents uses the titles
- AND every concept, realization and contract identity, the document identity and, on an entry, the Module identity are anchors on the page
- AND a link of the form `path#identity` from another page resolves to that anchor
- BUT the source document, the definition bodies and fenced examples are unchanged

Two definitions with the same title keep distinct anchors, and changing a title does not change its
anchor.

### scenario.views.import-definition — An import row shows the imported definition

- GIVEN a Terminology table with an import row linking to another Module's concept
- WHEN the site is built
- THEN the rendered row shows the link and, beside it, the concept's one-sentence definition from its defining document, followed by "Imported from" and a link to the owning Module's entry
- BUT the importing document's source still holds only the link

### scenario.views.illustrative-label — An illustrative diagram is labelled

- GIVEN a document containing a D2 block marked `illustrative`
- WHEN the site is built
- THEN the diagram renders in its place with a visible label saying that it is illustrative and not normative
- AND a checked D2 diagram renders without that label

### scenario.views.diagram-style — The look of a checked diagram comes from what it names

- GIVEN a checked D2 diagram that nests the page's child Modules and realizations with their files, and draws an edge between two Modules and an edge with a verb between two nodes
- WHEN the site is built
- THEN the page's Module, its child Modules, other Modules, concepts and realizations each render in their own fixed look
- AND a realization drawn with files renders as a table whose rows are the files
- AND the edge between Modules renders as a solid arrow and the edge between nodes as a dashed arrow labelled with its verb
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
- THEN it replaces the staged content under `docsite/.generated/` with one Markdown page per document, carrying its route, title and reading collection, and one sidebar per reading collection
- AND each page's table of contents lists its level-2 and level-3 headings
- AND only after every page and sidebar is written does it write the staging identity record with the source digest

### scenario.views.materialize-failure — A failed staging is never built

- GIVEN a staging that fails before every page and sidebar is written
- WHEN a later build step reads the staged content
- THEN there is no staging identity record
- AND the build refuses the partial staging

### scenario.views.build-site — A build runs every step before promotion

- GIVEN installed site dependencies and a valid registered project
- WHEN `npm run build` runs
- THEN it clears the previous candidate, stages the Specs, builds the candidate, validates it and only then promotes it

### scenario.views.build-site-failure — A failed step stops the build

- GIVEN a build in which Docusaurus fails to start, exits nonzero or the validation fails
- WHEN `npm run build` runs
- THEN the build stops with an error
- AND it deletes the candidate and promotes nothing

### scenario.views.validate-candidate-mismatch — A stale or incomplete candidate is rejected

- GIVEN a candidate whose build manifest version, source digest or page inventory differs from the current sources, or which contains an internal link to a missing page or anchor
- WHEN the candidate is validated
- THEN validation fails, naming the problem and, for a link, the referring page and destination
- BUT it repairs nothing and promotes nothing

### scenario.views.publish-preserves-previous-on-failure — A failed build keeps the published site

- GIVEN a published site and a build in which sources change during the build, a registered page is not rendered, a link does not resolve or a diagram fails to render
- WHEN the build checks the candidate
- THEN promotion is refused and the candidate is deleted
- AND the published site is unchanged

### scenario.views.rebuild-removes-stale-pages — Rebuilding removes pages no longer produced

- GIVEN a published site containing pages or files that the current sources no longer produce
- WHEN a new build succeeds and is promoted
- THEN the published site contains only what the new build produced

### scenario.views.cross-module-link — Cross-Module links resolve to the owner's page

- GIVEN a document of Module A that links, by relative source path and fragment, to a definition in a document owned by Module B
- WHEN the site is built and validated
- THEN the rendered link leads to the canonical page of B's document and the requested anchor exists there

A document has only its canonical route, so moving a document requires updating the links to it;
a link to a page or anchor that does not exist stops promotion, as
[validate-candidate-mismatch](#scenario.views.validate-candidate-mismatch) states.

## Site configuration

### scenario.views.user-docs — User documents as the home page and first tab

- GIVEN `docsite/site.json` sets `userDocs.path` to a directory whose root page is `README.md` or `index.md`
- WHEN the site is built
- THEN the root page is the site's home page at `/`, and every other document is published at its path in the directory
- AND the first navigation tab, labelled `userDocs.label` or "User documents", leads to them, with a sidebar that follows the directory's folders
- AND the Module documents, Implementation documents and custom docs tabs follow in that order
- BUT user documents are not Spec pages, are not listed in the build manifest, belong to no Module and grant no context

### scenario.views.publish-homepage-default — No user documents configured

- GIVEN `docsite/site.json` has no `userDocs`
- WHEN the site is built
- THEN the site root redirects to the root Module's entry page and shows a visible link to it
- AND the template adds no Concorde-specific content

### scenario.views.user-docs-invalid — An invalid user documents entry is refused

- GIVEN `docsite/site.json` contains a `userDocs` value that is not an object with a relative `path` and an optional nonblank `label`, or still contains the removed `homepage` field
- WHEN the site identity is loaded
- THEN loading fails with an error naming `docsite/site.json` and the invalid field, and a `homepage` field is told to become the root page of user documents
- AND no candidate is promoted

### scenario.views.user-docs-refused — User documents that cannot be published fail the build

- GIVEN `userDocs.path` names a missing directory, a directory without a root page, a directory containing a registered Spec document, or a directory whose top-level document or folder would publish under `/specs`, `/search` or a custom docs route
- WHEN the site is configured
- THEN the build fails naming `userDocs` and the offending path
- AND nothing is promoted

### scenario.views.custom-docs — Custom docs in their own tabs

- GIVEN `docsite/site.json` configures `customDocs` collections, or the project provides `docsite/custom-docs/index.ts`
- WHEN the site is built
- THEN each collection and each extension item has its own navigation entry after the Spec tabs
- AND custom pages are not listed in the build manifest and belong to no Module

### scenario.views.custom-docs-refused — Invalid custom docs fail the build

- GIVEN a custom docs collection containing a registered Spec document, a route that conflicts with a Spec page, missing content or a broken internal link
- WHEN the site is built
- THEN the build fails naming the collection or link
- AND nothing is promoted

### scenario.views.protocol-docs-tab — Concorde publishes its Protocol as custom docs

- GIVEN Concorde's `docsite/site.json` configures `protocol/` as a custom docs collection with its own sidebar
- WHEN Concorde's site is built
- THEN the Spec Protocol appears at `/protocol` with its chapter sidebar and search
- AND its pages carry no Spec provenance and belong to no Module
- BUT a scaffolded project receives neither this collection nor its sidebar

## Scaffold

### scenario.views.scaffold-propose — Proposing a docsite scaffold

- GIVEN an initialized project and optional `--title`, `--repository`, `--url`, `--base-url` and `--github-pages` options
- WHEN `concorde docsite --propose` runs
- THEN it returns a deterministic scaffold proposal listing the template files, a new `docsite/site.json` and, with `--github-pages`, the deployment workflow
- AND it reports whether Node.js 20 or newer and npm are present, without changing the proposal
- AND it lists already existing destinations as conflicts
- BUT it writes nothing to the project

### scenario.views.scaffold-apply — Applying a scaffold proposal

- GIVEN a proposal that still matches the installed template and a project in which none of its destinations exist
- WHEN `concorde docsite --apply --proposal PATH` runs
- THEN it creates exactly the proposed files with the proposed bytes and returns `success` with their paths
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

- GIVEN a valid proposal whose destinations are absent when applying starts
- WHEN another process creates one of the destinations while the proposal is being applied
- THEN the result is `failed`
- AND every file this application had already created is removed
- BUT files it did not create keep their bytes

### scenario.views.scaffold-conflict — Existing destinations block a scaffold

- GIVEN a valid proposal and a project in which at least one destination already exists with other content
- WHEN it is applied
- THEN the result is `conflict`, naming every existing destination
- BUT no file is written
