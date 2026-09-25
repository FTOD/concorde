# Views

## Purpose

Views publishes a project's Specs as a documentation website for reading the Modules, how they fit
together, and their precise promises. The publisher, a Docusaurus site under `docsite/`, turns
registered documents into pages, checks the result, and only then replaces the previous site; the
scaffold copies that publisher into another project. A published page only views the Specs — no
context granted, no Spec changed, nothing proved about the code — and Views neither defines the
Spec format (Spec core does), installs Node dependencies, nor deploys without opting into the
GitHub Pages workflow.

## Terminology

| Term | Definition |
| --- | --- |
| Published site | The last docsite build that passed every check, kept in `docsite/build/`. |
| Publication candidate | A complete new build, generated apart from the published site, that must pass every check before it may replace it. |
| Promotion | The directory swap that makes a checked publication candidate the new published site. |
| Canonical page | The single page at which one registered Spec document is published. |
| Reading collection | One of the two Spec tabs of the site, Module documents or Implementation documents, chosen for each document by its declared role. |
| User documents | Project-owned documentation for the project's users, published from one directory as the site's first tab, whose root page is the site's home page. |
| Custom docs | Project-owned documentation that the site publishes in its own tab after the Spec tabs, beside the Specs and outside them. |
| Site identity | The project-owned file `docsite/site.json` that names the site and configures its optional user documents and custom docs. |
| Scaffold proposal | The exact list of files, with their digests, that the scaffold command would create in a project. |
| Build manifest | The record a build writes beside its pages, listing every published document with its route and source digests. |
| [Developer](../../vocabulary.md#concept.concorde.developer) | |
| [Module](../../vocabulary.md#concept.concorde.module) | |
| [Spec](../../vocabulary.md#concept.concorde.spec) | |
| [Context](../../vocabulary.md#concept.concorde.context) | |
| [Registry](../spec/module.md#concept.spec.registry) | |
| [Impact index](../spec/module.md#concept.spec.impact-index) | |
| [File transaction](../spec/module.md#concept.spec.file-transaction) | |

## Usage

<a id="concept.views.canonical-page"></a><a id="concept.views.reading-collection"></a>

The site has a **Module documents** tab and, when any document is role `implementation`, an
**Implementation documents** tab, both showing the Module tree built from `contains`. Every
**canonical page** sits under its owner; a Module reading it through `uses` or `includes` links
there instead of copying it. Each page shows its owner, the Modules selecting it and why, and its
source digests, with every identity anchored, imports showing the imported definition, and
illustrative diagrams labelled non-normative.

<a id="concept.views.user-docs"></a><a id="concept.views.custom-docs"></a>

**User documents** are written for the people who use the project, in any structure: the site
publishes their directory as it is, with a sidebar that follows its folders, as the first tab, and
their root page (`README.md` or `index.md`) is the home page at `/`. Without them the home page
opens the root Module's entry. **Custom docs** are further collections, such as Concorde's own
Spec Protocol, each in its own tab after the Spec tabs. Neither belongs to a Module, may contain a
registered document, or is ever agent context.

<a id="concept.views.publication-candidate"></a><a id="concept.views.promotion"></a><a id="concept.views.published-site"></a><a id="concept.views.build-manifest"></a>

| Command | Effect |
| --- | --- |
| `npm run start` | Previews the site, restarting the preview whenever its Specs change. |
| `npm run validate` | Checks without building. |
| `npm run build` | Builds a **publication candidate**, checks it, and promotes it to the **published site** in `docsite/build/`. |

A successful build writes a **build manifest** — every page's route, owner and source digests,
nothing about the code. A failure, such as a moved anchor's link, deletes the candidate and keeps
the published site.

<a id="concept.views.scaffold-proposal"></a><a id="concept.views.site-identity"></a>

For another project, `concorde docsite --propose` returns a **scaffold proposal** — the exact
template files plus a new **site identity** `docsite/site.json` — and `--apply --proposal FILE`
creates exactly those files, never replacing or deleting: `conflict` for an existing destination,
`unchanged` if already applied, refused for bytes from another package. The exact commands and
fields are in the [contracts](contracts.md).

## Design

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

<a id="realization.views.publisher"></a>

**Docsite publisher** reads the project configuration, the registry and the documents the registry
lists, and nothing else: it never scans directories for Markdown or follows links to find
documents, so a nearby file that looks like a Spec never becomes a page and nothing is published
that no Module owns. The navigation follows `contains`, the Protocol's top-down reading path, and
directory layout plays no part. Each document is published once, at a route derived from its
source path, so its address does not depend on which Modules read it; consumers link to the owner's
page instead of receiving a copy that could drift. There are no alias routes: moving a document
changes its route, and the build refuses a link that still points to the old one.

Every enrichment, such as hidden identities in headings, anchors, imported definitions and
illustrative labels, is made on a staged copy under `docsite/.generated/`. The Spec files stay
byte-for-byte unchanged, so a published enrichment can never become a second, unreviewed
definition. A diagram's source states meaning and its look is the publisher's: a checked D2 block
only names, nests and connects shapes, which is what Spec core checks, and the publisher gives each
kind of shape and edge one fixed look. Every Module's pages therefore share one visual language
that no Spec can override, which is why a Mermaid block or a checked diagram that sets its own look
is refused.

Rendering can fail halfway and sources can change while a build runs, so the publisher builds a
candidate apart from the published site and compares one source digest, over the configuration, the
registry and both files of every document, at staging, after the Docusaurus build and in the final
validation, which also follows every internal link and anchor in the built HTML. Promotion renames
whole directories with rollback:

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

The publisher refuses only what it cannot publish correctly (the
[pipeline](pipeline.md#loading-and-admission) lists it); it is not the Protocol validator, and a
site that builds proves nothing about conformance. It is TypeScript and does not call Spec tooling,
so it recomputes each document's selecting Modules itself; that must equal Spec core's
`selected-by` [impact index](../spec/module.md#concept.spec.impact-index), and a difference is a
publisher defect, never a second definition of context. Preview and production keep Docusaurus's
generated files in different directories, so a build never breaks a running preview.

<a id="realization.views.scaffold"></a>

**Docsite scaffold** computes the template inventory with the rule the installer uses to ship
`docsite/`, so a project receives exactly the adapter Concorde runs itself, and the proposal binds
that inventory by digest. Applying goes through Spec core's
[file transactions](../spec/module.md#concept.spec.file-transaction): every destination must be
absent before staging and again before each write, and a concurrent change rolls back what was
written. Because the scaffold can neither replace nor delete, accepting a proposal can never damage
an existing site or Spec; bringing a site up to a newer template is a manual, reviewed change.

<a id="realization.views.concorde-site"></a>

**Concorde site** is Concorde's own publication configuration — `site.json` with its user documents
and Protocol collection, the repository tests and the Pages workflow. The template excludes it, so
a scaffolded project never receives Concorde's user documents or Protocol chapters.

## Relationships

```d2
views: Views
core: Spec core
distribution: Distribution
views -> core
distribution -> views
```

The publisher and scaffold never touch each other's output: the scaffold creates files once;
publication only reads Specs and writes derived output under `docsite/`.

<a id="uses-spec"></a>

**Spec core** owns the project [registry](../spec/module.md#concept.spec.registry), Spec loading,
[impact indexes](../spec/module.md#concept.spec.impact-index) and
[file transactions](../spec/module.md#concept.spec.file-transaction). The publisher relies on the
registry for which Modules and documents exist and which contains which, and on the meaning of
`selected-by` for the provenance it shows; it parses the registry and metadata itself in TypeScript
and refuses any input it can't publish, failing the build and keeping the old site; it leaves full
structural conformance to the Spec validator. The scaffold relies on it for the root Module's
title, the common result shape, and a file transaction writing everything or nothing (a null digest
meaning the file must still be absent), returning `invalid` and asking for initialization when the
project's Spec configuration isn't readable.

Distribution calls the scaffold and packages it — `distribution -> views` above is its own `uses`,
declared there. Its CLI dispatches `concorde docsite` to the scaffold, which reads templates from
the installed package, returning `invalid` (asking for a reinstall) if `concorde.json` omits
`docsite` as a package root or lists it unsafely; its installer ships `docsite/` by the inventory
rule Views defines, so the two cannot disagree on the template. Its build manifest, unrelated to
the docsite's, records Concorde's own build outputs.
