# Views design notes

The full reading, building and scaffolding walkthrough and the design reasons summarized in the
[Views](module.md) entry. The publisher's mechanics are in the [pipeline](pipeline.md); exact
formats are in the [contracts](contracts.md).

## Reading the site

The navigation bar has a **Module documents** tab and, when any document has the role
`implementation`, an **Implementation documents** tab; the names are the Protocol's two document
roles. Both show the same tree of Modules, built from the `contains` relations: the root Module at
the top, and under each Module its child Modules. In Module documents, clicking a Module's name
opens its entry `module.md`; its explanatory topics and child Modules are listed beneath it.
Implementation documents shows only the precise documents (requirements, scenarios, contracts)
under the same tree. Both tabs belong to one Module specification: an implementation document is
not a separate kind of Spec. The role declared in each document's
metadata decides the tab. Moving a document from one role to the other moves it between tabs and
changes nothing else: its route, owner and the Modules that read it stay the same.

Every registered document has exactly one canonical page, under the Module that owns it. Its route
comes from its source path: `specs/concorde/spec-tooling/views/scenarios.md` is published at
`/specs/concorde/spec-tooling/views/scenarios`. When another Module reads the document through `uses` or
`includes`, the site does not copy it; links from that Module lead to the same page. So a shared
contract always has one page and one owner.

Each page starts with a short provenance bar: whether it is a Module document or an
Implementation document, its source path, links between the entry and the Module's implementation
documents, and a "Spec metadata" disclosure with the document identity, its owner, the Modules whose
context selects it and why, and the digests of its reading and metadata files.

Every stable identity is an anchor on its page: the Module on its entry, the document, and every
concept, realization, requirement, scenario and contract the document defines. A link written in a Spec as
`scenarios.md#scenario.views.build-site` arrives at
`/specs/concorde/spec-tooling/views/scenarios#scenario.views.build-site`. Requirement and scenario headings
display only their title; the identity stays in the page as the heading's anchor. A Terminology
import row, which in the source holds only a link, is shown with the imported definition next to
the link, read from the defining document when the site is built and marked "Imported from" the
owning Module. D2 diagrams appear exactly where the document places them, and a diagram marked
`illustrative` carries a visible label saying it is not normative.

**A diagram's source states meaning; its look is the publisher's.** A checked D2 block only names
shapes, nests them and draws edges, which is what Spec core checks against the declarations. The
publisher resolves every shape the same way and gives each kind one fixed look: containment is a
block inside a block, a realization drawn with its files is a table of them, a `uses` is a solid
arrow and a `relates` a dashed arrow with its verb. Every Module's pages therefore share one visual
language that no Spec can override, and changing the house style restyles every diagram at once.
Rendering calls the `d2` program from github.com/d2lang/d2 once per diagram, with the ELK layout,
and fails with the diagram's location when the program is missing or rejects the input.

User documents come first. They are the project's documentation for its users, kept in one
directory in whatever structure suits them, and the site publishes that directory as it is: the
first tab, a sidebar that follows the folders, and the root page as the site's home page at `/`.
Concorde publishes its `docs/` this way, so its home page is `docs/README.md`. The Spec tabs come
next, and custom docs, such as the Spec Protocol chapters Concorde publishes at `/protocol`, come
last in their own tabs. User documents and custom docs are ordinary documentation: they belong to
no Module and are never part of any agent's context.

## Building and previewing

Run the commands from `docsite/` after installing its dependencies with `npm ci` (Node.js 20 or
newer). `npm run start` stages the current Specs and starts a local preview. `npm run validate`
loads and checks the registered sources without building. `npm run build` stages the Specs, builds
a publication candidate in `docsite/.generated/candidate`, checks it against the current sources
and, only if every check passes, promotes it to `docsite/build/`, the published site. `npm test`
runs the publisher's tests, and `npm run check` runs type checks, tests, validation and a build.

A successful build leaves a build manifest, `build-manifest.json`, at the root of the published
site. It lists every published document with its route, owner, reading collection and the digests
of its two source files, together with one digest over all inputs. It tells you exactly which
sources a site was built from; it says nothing about whether the code satisfies them.

If anything fails, the candidate is deleted and the published site stays exactly as it was. For
example, if a scenario moves to another document and a link still points to the old
`requirements.md#scenario...` location, the build stops with an error naming the referring page and
the missing destination. Fix the link and build again.

## Adding a site to a project

In an initialized Concorde project, ask for a scaffold proposal, read it, and then apply exactly
that proposal:

```bash
concorde docsite --propose > proposal.json
concorde docsite --apply --proposal proposal.json
```

The proposal lists every file of the publisher template, a new `docsite/site.json` and, with
`--github-pages`, a deployment workflow at `.github/workflows/deploy-docsite.yml`. `--title`,
`--repository`, `--url` and `--base-url` override the defaults, which come from the root Module's
title and the Git `origin` remote. The proposal also reports whether Node.js and npm are present;
it never installs them.

Applying creates only files that do not exist yet. If every file already has the proposed bytes,
the result is `unchanged`. If any destination exists with other content, the result is `conflict`
and nothing is written. A proposal made from different package bytes is rejected; propose again.
The scaffold never updates or deletes an existing site: bringing an existing site up to a newer
template is a manual, reviewed change.

After applying, edit `docsite/site.json` if needed. It holds the title, address and base URL, an
optional repository link, optional user documents and optional custom docs collections. Without
user documents, the site root redirects to the root Module's entry page. The exact fields are in
[the site identity rules](contracts.md#site-identity).

## Why it is built this way

**The registry is the only source.** The Docsite publisher reads the project configuration, the
registry and the documents the registry lists, and nothing else. It never scans directories for
Markdown or follows links to find documents. A nearby file that looks like a Spec therefore never
becomes a page, and nothing is published that no Module owns. The navigation tree follows
`contains` because composition is the Protocol's top-down reading path; directory layout plays no
part.

**One page per document, one route per path.** A document is published once, at a route derived
from its source path, so its address does not depend on which Modules read it. Consumers link to
the owner's page instead of receiving a copy, which prevents copies from drifting apart. There are
no alias or redirect routes: moving a document changes its route, and the build refuses any link
that still points to the old one.

**Rendered views are never written back.** Hiding identities in headings, adding anchors, filling
in imported definitions and labelling illustrative diagrams all happen on a staged copy under
`docsite/.generated/`. The Spec files stay byte-for-byte unchanged, so a published enrichment can
never become a second, unreviewed definition.

**A candidate protects the published site.** Rendering can fail halfway and sources can change
while a build runs. The publisher therefore builds into a separate directory and checks it before
promotion. It computes one source digest over the configuration, the registry and both files of
every document, and compares it at staging, after the Docusaurus build and in the final
validation. The build manifest records that digest and the page inventory, and the final check
also follows every internal link and anchor in the built HTML. Promotion is a rename of whole
directories with rollback, so a failure leaves the old site in place, and pages that a new build
no longer produces disappear with the old directory.

```d2 illustrative
direction: right
a: Registered Specs
b: Staged pages and sidebars
c: Docusaurus build into the candidate
d: Digest, inventory and links current? {shape: diamond}
e: Promote to docsite/build
f: Delete candidate, keep published site
a -> b -> c -> d
d -> e: yes
d -> f: no
```

**The publisher checks what it depends on, not everything.** It refuses inputs it cannot publish
correctly, such as a document without a valid role, a requirement in a `module`-role document, a
Mermaid block, a checked diagram outside the semantic subset or an unresolved link; the
[pipeline](pipeline.md#loading-and-admission) lists them all. It is not the Protocol validator: the
registry mirror, what checked diagrams assert, realization bindings and contract examples are
checked by Spec core's `concorde validate`, and a site that builds proves nothing more.

**Provenance is computed twice and must agree.** The publisher is TypeScript and does not call Spec
tooling. It recomputes the one-level Spec context of every Module from the registry records to show,
on each page, which Modules select the document and through which relation. That recomputation must
equal Spec core's `selected-by` [impact index](../spec/module.md#concept.spec.impact-index) for
the same inputs; a difference is a defect of the publisher, never a second definition of context. A
published provenance bar grants no reader any context either way.

**Preview and production do not disturb each other.** The preview keeps Docusaurus's generated
files in `docsite/.docusaurus`, a production build in `docsite/.generated/docusaurus-production`,
so building the site does not break a running preview.

**The scaffold only creates.** The Docsite scaffold computes the template inventory with the same
rule the installer uses to ship `docsite/`, so a project receives exactly the adapter Concorde runs
itself. The proposal binds that inventory by digest. Applying it goes through Spec core's
[file transactions](../spec/module.md#concept.spec.file-transaction), which Views uses and does not
own: every destination must be absent before staging and again before each write, and a concurrent
change rolls back the files already written. Because the scaffold can neither replace nor delete,
accepting a proposal can never damage an existing site or a project Spec.

**Concorde's own site is project-owned.** The Concorde site consists of the files that configure
Concorde's publication rather than the template: `docsite/site.json` with Concorde's user documents, the
Protocol collection under `docsite/custom-docs/`, the repository-specific tests in
`docsite/tests/repository/` and the GitHub Pages workflow. The template inventory excludes them, so
a scaffolded project never receives Concorde's user documents or Protocol chapters.
