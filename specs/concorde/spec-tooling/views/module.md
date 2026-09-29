# Views

## Purpose

Views publishes a project's Specs as a documentation website for reading the Modules, how they fit
together, and their precise promises. The publisher, a Docusaurus site under `docsite/`, turns
registered documents into pages, checks the result, and only then replaces the previous site; the
scaffold copies that publisher into another project. A published page only views the Specs — no
context granted, no [Spec](../../glossary.json#concept.spec) changed, nothing proved about the code
— and Views neither defines the Spec format (Spec core does), installs Node dependencies, nor
deploys without opting into the GitHub Pages workflow.

## Core concepts

### What the site shows

The site's Spec pages form two **reading collections**, chosen by each document's role.
**[Module](../../glossary.json#concept.module) documents** are listed in the site's one Spec tab,
whose sidebar shows the Module tree built from `contains`. **Implementation documents**, the precise
promises readers look up rather than read through, are in no tab or sidebar: each Module's entry
page ends with a folded list of its own, and links, term links, search and their addresses reach
them.

Every **canonical page** sits under its owner; a Module reading it through `uses` or `includes`
links there instead of copying it. Each page shows its owner, the Modules selecting it and why, and
its source digests, with every identity anchored, term links leading to the glossary page, and
illustrative diagrams labelled non-normative; an implementation page also names the Module it
belongs to, linking to its entry. The glossary is one page under the root Module, and an owning
Module's entry page lists the terms it owns.

**User documents** are written for the people who use the project, in any structure: the site
publishes their directory as it is, with a sidebar that follows its folders, as the first tab, and
their root page (`README` or `index`, `.md` or `.mdx`) is the home page at `/`. Without them the
home page opens the root Module's entry. **Custom docs** are further collections, such as
Concorde's own Spec Protocol, each in its own tab after the Module documents tab. Neither belongs to
a Module, may contain a registered document, or is ever agent context.

### How a site is published

A build makes a **publication candidate** apart from the site readers see, checks it, and only then
makes it, by **promotion**, the **published site** in `docsite/build/`. A successful build writes a
**site manifest** — every registered document's route, owner and source digests, nothing about the
code; user documents, custom docs and the Glossary page are not in it. A failure, such as a moved
anchor's link, deletes the candidate and keeps the published site.

### How a site reaches another project

A **scaffold proposal** is the exact template files plus a new **site identity**
`docsite/site.json`, which names the site and configures its user documents and custom docs.
Applying a proposal creates exactly those files, never replacing or deleting one.

## Overview

Views has three parts: the publisher that builds the site, the scaffold that copies the publisher
into another project, and Concorde's own site configuration:

```d2
views: Views {
  publisher: Docsite publisher {
    "docsite/"
  }
  scaffold: Docsite scaffold {
    "src/concorde/views/"
  }
  site: Concorde site {
    "site.json"
    "custom-docs/"
    "deploy-docsite.yml"
  }
  scaffold -> publisher: copies
  site -> publisher: configures
}
```

The publisher and scaffold never touch each other's output: the scaffold creates files once;
publication only reads Specs and writes derived output under `docsite/`.

### Publishing

Rendering can fail halfway and sources can change while a build runs, so a build publishes only a
candidate whose inputs did not move and whose links all resolve:

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

### Scaffolding

A scaffold proposal is created, reviewed and then applied, and applying it writes either every file
or none:

```d2 illustrative
direction: down
propose: "concorde docsite --propose:\ntemplate files and a new\nsite identity (+ Pages workflow)"
apply: "concorde docsite --apply\n--proposal FILE"
match: "Matches the installed\ntemplate inventory?" {shape: diamond}
same: "Every file already\nhas the proposed bytes?" {shape: diamond}
exists: "Any destination\nexists?" {shape: diamond}
write: "Create every file through\na file transaction"
invalid: "invalid" {shape: page}
unchanged: "unchanged:\nnothing written" {shape: page}
conflict: "conflict:\nnothing written" {shape: page}
created: "Files created, or\nrolled back if one appeared" {shape: page}
propose -> apply -> match
match -> invalid: no
match -> same: yes
same -> unchanged: yes
same -> exists: no
exists -> conflict: yes
exists -> write: no
write -> created
```

## The commands

The site's commands run from `docsite/` (Concorde's own, or one the scaffold created) after
`npm ci` has installed its dependencies there; `start` and `build` render diagrams with the `d2`
program, found as `CONCORDE_D2`, the `.concorde/tools/d2` the Concorde installer places, or `d2` on
`PATH`:

| Command | Effect |
| --- | --- |
| `npm run start` | Previews the site, restarting the preview whenever its Specs change. |
| `npm run validate` | Checks without building. |
| `npm run build` | Builds a publication candidate, checks it, and, by promotion, makes it the published site in `docsite/build/`. |

For another project, `concorde docsite --propose` returns a scaffold proposal and
`--apply --proposal FILE` creates exactly those files, never replacing or deleting: `unchanged`
when every file already has the proposed bytes, otherwise `conflict` when any destination exists,
and `invalid` when the proposal no longer matches the installed template (another package version
or an altered file list). With `--github-pages` the proposal also holds
`.github/workflows/deploy-docsite.yml`, which on every push to `main` runs `npm run build` and
deploys `docsite/build/` to GitHub Pages. The exact commands and fields are in the
[contracts](contracts.md).

## How it is built

<a id="realization.views.publisher"></a>

**Docsite publisher** finds Spec pages only through the project configuration, the registry and the
documents the registry lists: it never scans directories for Markdown or follows links to find
documents, so a nearby file that looks like a Spec never becomes a Spec page and no Spec page is
published that no Module owns. Its other inputs are declared separately, each with its own admission
rules: the glossary the root Module declares, the site identity, and the user documents and custom
docs that the site identity configures. The navigation follows `contains`, the Protocol's top-down
reading path, and directory layout plays no part. Each document is published once, at a route
derived from its source path, so its address does not depend on which Modules read it; consumers
link to the owner's page instead of receiving a copy that could drift. There are no alias routes:
moving a document changes its route, and the build refuses a link that still points to the old one.

Every enrichment, such as hidden identities in headings, anchors, imported definitions and
illustrative labels, is made on a staged copy under `docsite/.generated/`. The Spec files stay
byte-for-byte unchanged, so a published enrichment can never become a second, unreviewed
definition. A diagram's source states meaning and its look is the publisher's: a checked D2 block
only names, nests and connects shapes, which is what Spec core checks, and the publisher gives each
kind of shape and edge one fixed look. Every Module's pages therefore share one visual language
that no Spec can override, which is why a Mermaid block or a checked diagram that sets its own look
is refused.

The publisher builds its candidate apart from the published site and compares one source digest,
over the configuration, the registry, both files of every document, the glossary and the site
identity, at staging, after the Docusaurus build and in the final validation, which also follows
every internal link and anchor in the built HTML. Promotion renames whole directories with
rollback.

The publisher refuses only what it cannot publish correctly (the
[pipeline](pipeline.md#loading-and-admission) lists it); it is not the Protocol validator, and a
site that builds proves nothing about conformance. It is TypeScript and does not call Spec tooling,
so it recomputes each document's selecting Modules itself; that must equal Spec core's
`selected-by` [impact index](../../glossary.json#concept.impact-index), and a difference is a
publisher defect, never a second definition of context. Preview and production keep Docusaurus's
generated files in different directories, so a build never clears or overwrites the preview's; both
modes stage the same pages under `docsite/.generated/`, which a build run beside a preview rewrites
from the same sources.

<a id="realization.views.scaffold"></a>

**Docsite scaffold** owns the template inventory, the one rule selecting the template files of the
package's `docsite/`: the scaffold proposes those files without `scaffold/`, and Distribution's
installer calls the same rule to ship them, `scaffold/` included, into a project's
`.concorde/framework/docsite/`, where an installed scaffold reads them. A project therefore
receives exactly the adapter Concorde runs itself, and the proposal binds that inventory by
digest. Applying goes through Spec core's
[file transactions](../../glossary.json#concept.file-transaction): every destination must be
absent before staging and again before each write, and a concurrent change rolls back what was
written. Because the scaffold can neither replace nor delete, accepting a proposal can never damage
an existing site or Spec; bringing a site up to a newer template is a manual, reviewed change.

<a id="realization.views.concorde-site"></a>

**Concorde site** is Concorde's own publication configuration — `site.json` with its user documents
and Protocol collection, the repository tests and the Pages workflow. The template excludes it, so
a scaffolded project never receives Concorde's user documents or Protocol chapters.

## Around it

Views sits between the Spec core it reads and the Distribution that packages and calls it:

```d2
views: Views
core: Spec core
distribution: Distribution
views -> core
distribution -> views
```

<a id="uses-spec"></a>

**Spec core** owns the project [registry](../../glossary.json#concept.registry), Spec loading,
[impact indexes](../../glossary.json#concept.impact-index) and
[file transactions](../../glossary.json#concept.file-transaction). The publisher relies on the
registry for which Modules and documents exist and which contains which, and on the meaning of
`selected-by` for the provenance it shows; it parses the registry and metadata itself in TypeScript
and refuses any input it can't publish, failing the build and keeping the old site; it leaves full
structural conformance to the Spec validator. The scaffold relies on it for the root Module's
title, the common result shape, and a file transaction writing everything or nothing (a null digest
meaning the file must still be absent), returning `invalid` and asking for initialization when the
project's Spec configuration isn't readable.

Distribution calls the scaffold and packages it — `distribution -> views` above is its own `uses`,
declared there. Its CLI dispatches `concorde docsite` to the scaffold, which reads templates from
the installed package, returning `invalid` (asking for a reinstall) if `concorde.json`, the
descriptor of the package, omits `docsite` as a package root
or the template is missing or unsafe; its installer ships the template files by calling the
inventory rule Views defines rather than repeating it, so the two cannot disagree on the template.
Its [build manifest](../../glossary.json#concept.build-manifest), unrelated to the docsite's,
records Concorde's own build outputs.
