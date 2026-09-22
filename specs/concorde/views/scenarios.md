# Views scenarios

Concrete situations of [Views](module.md). Exact formats are in [contracts](contracts.md) and the
publisher's mechanics in the [pipeline](pipeline.md).

## Loading the Specs

### scenario.views.load-registry — Loading the registered Specs

- GIVEN `.concorde/config.json` names a registry whose Modules list their entries and owned documents
- WHEN the publisher loads the project
- THEN it returns one model of the Modules, their `contains` tree, the root Module and one page per owned document
- AND loading the same unchanged inputs again gives the same model and the same source digest
- BUT an unsafe path, a symbolic link, duplicate JSON keys, a duplicate identity, a composition cycle, an unmarked Mermaid block that is not a flowchart, a `relies_on` identity its target does not define, or a Terminology import row that does not link to its concept's defining document fails loading before anything is written

The root Module is the first Module in registry order that no Module contains. The model holds
no graph projection of its own: the Module relations it keeps serve navigation, provenance and
admission. The publisher does not compare the registry with the entries' `module` blocks; the Spec
validator does.

### scenario.views.reject-reading-collection — A document without a valid role is refused

- GIVEN a document whose metadata is not schema 3 or has no valid `role`, an entry `module.md` whose role is `implementation` or whose metadata lacks the `module` block, another document whose metadata has a `module` block, a `module`-role document containing a requirement, a scenario, a canonical contract or a Graph Spec flowchart, or an `implementation`-role document defining a concept
- WHEN the publisher loads the project
- THEN loading fails with an error naming the offending document
- AND no candidate is staged or promoted

## Pages and navigation

### scenario.views.publish-candidate — One canonical page per registered document

- GIVEN a valid registered project
- WHEN the site is built
- THEN every registered document is published at exactly one page whose route is `/specs/` followed by its source path without `.md`, with a leading `specs/` removed when every document lies under `specs/`
- AND each Module appears in the navigation under the Module that contains it, and root Modules at the top level
- AND a Module's name opens its entry, with its explanatory topics and then its child Modules beneath it
- AND Mermaid fences render where the document places them

### scenario.views.reading-collections — Two reading collections, one Module specification

- GIVEN a project in which some documents declare the role `implementation`
- WHEN the site is built
- THEN the navigation bar shows the Module Specs and Implementation Specs tabs
- AND Module Specs lists every entry and `module`-role topic, and Implementation Specs lists only `implementation`-role documents under the same Module tree, omitting Modules without such documents
- AND an implementation page links back to its Module's entry, and the entry's pages link to the Module's implementation documents
- AND changing only a document's role moves it between tabs without changing its route
- BUT without any `implementation`-role document the Implementation Specs tab does not appear

### scenario.views.publish-reference-link — A shared document is published once

- GIVEN one document owned by Module A and selected by Modules B and C through `uses` or `includes`
- WHEN the site is built
- THEN the document has one page under A, and B and C list no copy of it in their navigation
- AND its provenance names A as owner and lists every selecting Module with the relation that selected it
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

- GIVEN a document containing a Mermaid block marked `illustrative`
- WHEN the site is built
- THEN the diagram renders in its place with a visible label saying that it is illustrative and not normative
- AND an unmarked flowchart renders without that label

### scenario.views.publish-without-graph — Diagrams appear only in their documents

- GIVEN a valid registered project
- WHEN the site is built and promoted
- THEN the site has no generated graph page, graph navigation entry or graph data file
- AND registered pages, navigation, provenance, anchors and inline Mermaid diagrams are available
- AND the homepage and custom docs, when configured, behave as usual

### scenario.views.operation-graphs-in-owner-specs — Graph Specs are read in their owners' Specs

- GIVEN Concorde's own project, where every executable Graph has one Graph Spec in an implementation document of its owning Module
- WHEN the site is built
- THEN each Graph Spec appears once, on its owner's implementation page, with its State, Nodes and Edges before its flowchart
- AND no tab, homepage link or route publishes a separate Operation or Graph page

Building the site needs no Python Graph environment: the flowchart is ordinary reading. Whether a
Graph Spec matches its compiled Graph is checked by the Graph Spec check, not by publication.

## Building and promotion

### scenario.views.materialize — Staging the pages

- GIVEN a loaded project model
- WHEN the publisher stages it
- THEN it replaces the staged content under `docsite/.generated/` with one Markdown page per document, carrying its route, title and reading collection, and one sidebar per reading collection
- AND each page's table of contents lists its level-2 and level-3 headings
- AND only after every page and sidebar is written does it write the staging identity record with the source digest
- BUT a failure before that point leaves no identity record, so a later build refuses the partial staging

### scenario.views.build-site — A build runs every step before promotion

- GIVEN installed site dependencies and a valid registered project
- WHEN `npm run build` runs
- THEN it clears the previous candidate, stages the Specs, builds the candidate, validates it and only then promotes it
- AND a failure to start Docusaurus, a nonzero exit or a failed validation stops the build without promoting

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

### scenario.views.publish-repeat-without-graph — Rebuilding removes pages no longer produced

- GIVEN a published site containing pages or files that the current sources no longer produce
- WHEN a new build succeeds and is promoted
- THEN the published site contains only what the new build produced
- BUT a failed build leaves the previous published site in place

### scenario.views.publish-legacy-redirect — Cross-Module links resolve to the owner's page

- GIVEN a document of Module A that links, by relative source path and fragment, to a definition in a document owned by Module B
- WHEN the site is built and validated
- THEN the rendered link leads to the canonical page of B's document and the requested anchor exists there
- BUT a link whose page or anchor does not exist in the built site stops promotion until it is corrected

A document has only its canonical route; the publisher keeps no redirects for earlier owners or
paths, so moving a document requires updating the links to it.

## Site configuration

### scenario.views.publish-homepage — A configured homepage

- GIVEN `docsite/site.json` contains a valid `homepage` object
- WHEN the site is built
- THEN the root page shows the configured introduction, features, workflow and quickstart, and a reference section when `homepage.reference` is present
- AND its main Spec link opens the root Module's entry, and local links respect the base URL
- AND configured `homepage.links` and the repository link appear only when present
- BUT the homepage is not a Spec page, is not listed in the build manifest and grants no context

### scenario.views.publish-homepage-default — No homepage configured

- GIVEN `docsite/site.json` has no `homepage`
- WHEN the site is built
- THEN the site root redirects to the root Module's entry page and shows a visible link to it
- AND the template adds no Concorde-specific content

### scenario.views.publish-homepage-invalid — An invalid homepage is refused

- GIVEN `docsite/site.json` contains an incomplete or invalid `homepage` object
- WHEN the site identity is loaded
- THEN loading fails with an error naming `docsite/site.json` and the invalid field
- AND no candidate is promoted

### scenario.views.custom-docs — Custom docs in their own tabs

- GIVEN `docsite/site.json` configures `customDocs` collections, or the project provides `docsite/custom-docs/index.ts`
- WHEN the site is built
- THEN each collection and each extension item has its own navigation entry outside the Spec tabs
- AND custom pages are not listed in the build manifest and belong to no Module
- BUT a collection containing a registered Spec document, a route that conflicts with a Spec page, missing content or a broken internal link fails the build

### scenario.views.protocol-docs-tab — Concorde publishes its Protocol as custom docs

- GIVEN Concorde's `docsite/site.json` configures `protocol/` as a custom docs collection with its own sidebar
- WHEN Concorde's site is built
- THEN the Spec Protocol appears at `/protocol` with its chapter sidebar and search
- AND its pages carry no Spec provenance and belong to no Module
- BUT a scaffolded project receives neither this collection nor its sidebar

## Scaffold

### scenario.views.scaffold-propose — Proposing a docsite scaffold

- GIVEN an initialized project and optional `--title`, `--repository`, `--url`, `--base-url` and `--github-pages` options
- WHEN `concorde.py docsite --propose` runs
- THEN it returns a deterministic scaffold proposal listing the template files, a new `docsite/site.json` and, with `--github-pages`, the deployment workflow
- AND it reports whether Node.js 20 or newer and npm are present, without changing the proposal
- AND it lists already existing destinations as conflicts
- BUT it writes nothing to the project

### scenario.views.scaffold-apply — Applying a scaffold proposal

- GIVEN a proposal that still matches the installed template and a project in which none of its destinations exist
- WHEN `concorde.py docsite --apply --proposal PATH` runs
- THEN it creates exactly the proposed files with the proposed bytes and returns `success` with their paths
- AND it leaves every other file, including every Spec document, unchanged
- AND applying the same proposal again returns `unchanged` without writing

### scenario.views.scaffold-stale-rejected — A stale or altered proposal is refused

- GIVEN a proposal that no longer matches the installed template or the project: another proposal version, a changed template digest, an altered file list or hash, or a destination that another process creates while the proposal is being applied
- WHEN it is applied
- THEN the application is refused
- AND every file this application had already created is removed
- BUT files it did not create keep their bytes

A mismatch found before writing returns `invalid` and writes nothing. A destination that appears
during writing returns `failed` after the rollback.

### scenario.views.scaffold-conflict — Existing destinations block a scaffold

- GIVEN a valid proposal and a project in which at least one destination already exists with other content
- WHEN it is applied
- THEN the result is `conflict`, naming every existing destination
- BUT no file is written
