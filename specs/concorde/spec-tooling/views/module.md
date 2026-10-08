# Views

## Purpose

Views publishes a project's Specs as a documentation website for reading:

- The Modules.
- How they fit together.
- Their precise promises.

The publisher is a Docusaurus site under `docsite/`. It turns registered documents into pages.
It checks the result. Only then does it replace the previous site. The scaffold copies that publisher
into another project. A published page only views the Specs:

- No context is granted.
- No [Spec](../../glossary.json#concept.spec) is changed.
- Nothing is proved about the code.

Views does not define the Spec format. Spec core does. Views does not install Node dependencies.
Without opting into the GitHub Pages workflow, Views does not deploy.

## Core concepts

### What the site shows

The site's Spec pages form two **reading collections**, chosen by each document's role.
**[Module](../../glossary.json#concept.module) documents** are listed in the site's one Spec tab.
Its sidebar shows the Module tree built from `contains`. **Implementation documents** are the
precise promises readers look up rather than read through. They are in no tab or sidebar. Each
Module's entry page ends with a folded list of its own implementation documents. Readers reach
implementation documents through:

- Links.
- Term links.
- Search.
- Their addresses.

Every **canonical page** sits under its owner. When a Module reads it through `uses` or
`includes`, the Module links there instead of copying it. Each page shows:

- Its owner.
- The Modules selecting it and why.
- Its source digests.

Every identity is anchored. Term links lead to the glossary page. Illustrative diagrams are
labelled non-normative. An implementation page also names the Module it belongs to, linking to its
entry. The glossary is one page under the root Module. An owning Module's entry page lists the
terms it owns.

**User documents** are written for the people who use the project, in any structure. The site
publishes their directory as it is, as the first tab. Their sidebar follows their folders. Their
root page (`README` or `index`, `.md` or `.mdx`) is the home page at `/`. Without them, the home
page opens the root Module's entry. **Custom docs** are further collections, such as Concorde's own
Spec Protocol. Each has its own tab after the Module documents tab. Neither user documents nor
custom docs:

- Belongs to a Module.
- May contain a registered document.
- Is ever agent context.

### How a site is published

A build makes a **publication candidate** apart from the site readers see. It checks the candidate.
Only then does the build make it, by **promotion**, the **published site** in `docsite/build/`.
A successful build writes a **site manifest** containing every registered document's route, owner
and source digests. The manifest says nothing about the code. User documents, custom docs and the
Glossary page are not in it. On a failure, such as a moved anchor's link, the build deletes the
candidate and keeps the published site.

### How a site reaches another project

A **scaffold proposal** is the exact template files plus a new **site identity**
`docsite/site.json`. The site identity names the site. It configures its user documents and custom
docs. Applying a proposal creates exactly those files, never replacing or deleting one.

## Overview

Views has three parts:

- The publisher that builds the site.
- The scaffold that copies the publisher into another project.
- Concorde's own site configuration.

```d2
views: Views {
  publisher: Docsite publisher {
    "docsite/"
  }
  scaffold: Docsite scaffold {
    "src/concorde/spec/views/"
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

The publisher and scaffold never touch each other's output. The scaffold creates files once.
Publication only reads Specs and writes derived output under `docsite/`.

### Publishing

Rendering can fail halfway. Sources can change while a build runs. A build therefore publishes only
a candidate whose inputs did not move and whose links all resolve:

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

A scaffold proposal goes through these steps:

- It is created.
- It is reviewed.
- It is applied.

Applying it writes either every file or none:

```d2 illustrative
direction: down
propose: "concorde docsite --propose:\ntemplate files and a new\nsite identity (+ Pages workflow)"
apply: "concorde docsite --apply\n--proposal FILE"
match: "Matches the installed\ntemplate inventory?" {shape: diamond}
same: "Every file already\nhas the proposed bytes?" {shape: diamond}
exists: "Any destination\nexists?" {shape: diamond}
write: "Create each file only\nwhere nothing exists"
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

After `npm ci` installs its dependencies there, the site's commands run from `docsite/`
(Concorde's own, or one the scaffold created). `start` and `build` render diagrams with the `d2`
program, found through these alternatives:

- `CONCORDE_D2`.
- The `.concorde/tools/d2` the Concorde installer places.
- `d2` on `PATH`.

| Command | Effect |
| --- | --- |
| `npm run start` | Previews the site, restarting the preview whenever its Specs change. |
| `npm run validate` | Checks without building. |
| `npm run build` | Builds a publication candidate, checks it, and, by promotion, makes it the published site in `docsite/build/`. |

Run one `npm run build` of a docsite at a time. A build owns its candidate, the published site
and the backup until it ends, so two overlapping builds can delete each other's candidate or
recovery backup. A preview may run beside a build. The
[build commands](contracts.md#build-commands) state this prerequisite.

For another project, `concorde docsite --propose` returns a scaffold proposal.
`--apply --proposal FILE` creates exactly those files, never replacing or deleting. Its results
follow these cases:

- When every file already has the proposed bytes, the result is `unchanged`.
- Otherwise, when any destination exists, the result is `conflict`.
- When the proposal no longer matches the installed template, the result is `invalid`.

Another package version or an altered file list can cause the template mismatch.
With `--github-pages`, the proposal also holds `.github/workflows/deploy-docsite.yml`.
On every push to `main`, that workflow runs `npm run build` and deploys `docsite/build/` to GitHub
Pages. The exact commands and fields are in the [contracts](contracts.md).

## How it is built

<a id="realization.views.publisher"></a>

**Docsite publisher** finds Spec pages only through:

- The project configuration.
- The registry.
- The documents the registry lists.

It never scans directories for Markdown or follows links to find documents. Therefore, a nearby
file that looks like a Spec never becomes a Spec page. No Spec page is published that no Module
owns. The publisher's other inputs are declared separately, each with its own admission rules:

- The glossary the root Module declares.
- The site identity.
- The user documents and custom docs that the site identity configures.

The navigation follows `contains`, the Protocol's top-down reading path. Directory layout plays
no part. Each document is published once, at a route derived from its source path. Its address
therefore does not depend on which Modules read it. Consumers link to the owner's page instead
of receiving a copy that could drift. There are no alias routes. Moving a document changes its
route. When a link still points to the old route, the build refuses it.

Every enrichment is made on a staged copy under `docsite/.generated/`. Examples include:

- Hidden identities in headings.
- Anchors.
- Imported definitions.
- Illustrative labels.

The Spec files stay byte-for-byte unchanged. A published enrichment therefore can never become a
second, unreviewed definition. A diagram's source states meaning. Its look is the publisher's.
A checked D2 block performs only these actions:

- It names shapes.
- It nests shapes.
- It connects shapes.

That is what Spec core checks. The publisher gives each kind of shape and edge one fixed look.
Every Module's pages therefore share one visual language that no Spec can override. For that
reason, a Mermaid block or a checked diagram that sets its own look is refused.

The publisher builds its candidate apart from the published site. It compares one source digest
over these inputs:

- The configuration.
- The registry.
- Both files of every document.
- The glossary.
- The site identity.

The comparison occurs at these stages:

- At staging.
- After the Docusaurus build.
- In the final validation.

The final validation also follows every internal link and anchor in the built HTML. Promotion
renames whole directories with rollback.

The publisher refuses only what it cannot publish correctly. The
[pipeline](pipeline.md#loading-and-admission) lists it. The publisher is not the Protocol
validator. A site that builds proves nothing about conformance. The publisher is TypeScript.
It does not call Spec tooling. It therefore recomputes each document's selecting Modules itself.
That must equal Spec core's `selected-by` [impact index](../../glossary.json#concept.impact-index).
A difference is a publisher defect, never a second definition of context. Preview and production
stage their pages into directories of their own under `docsite/.generated/`. They also keep
Docusaurus's generated files apart. A build therefore never clears or overwrites what a running
preview reads.

Publication clears and replaces its own output directories: `docsite/.generated/`,
`docsite/build/` and `docsite/.docusaurus/`. A registered source inside one of them, lexically or
through a symbolic link, would be deleted by that cleanup. So would a source reached through an
output directory that is a symbolic link. The publisher therefore refuses both before it clears
anything.

<a id="realization.views.scaffold"></a>

**Docsite scaffold** owns the template inventory, the one rule selecting the template files of the
package's `docsite/`. The scaffold proposes those files without `scaffold/`. Distribution's
installer calls the same rule to ship them, `scaffold/` included, into a project's
`.concorde/framework/docsite/`. An installed scaffold reads them there. A project therefore
receives exactly the adapter Concorde runs itself. The proposal binds that inventory by digest.
Applying creates each file only where nothing exists, in one step the operating system makes
exclusive: the file is written apart and then hard-linked into place, which fails when anything
is already there. Spec core's [file transaction](../../glossary.json#concept.file-transaction)
cannot do this, since it replaces a file another process creates between its check and its
rename. When a destination appears meanwhile, or a creation fails, the scaffold removes the files
it created. It removes each only while it is still the file it created, judged by its device and
inode, so a file another process put there keeps its bytes. Only a replacement made between that
check and the removal itself can be lost, a window of one system call. Because the scaffold can
neither replace nor delete what it did not create, accepting a proposal can never damage an
existing site or Spec. Bringing a site up to a newer template is a manual, reviewed change.

<a id="realization.views.concorde-site"></a>

**Concorde site** is Concorde's own publication configuration:

- `site.json` with its user documents and Protocol collection.
- The repository tests.
- The Pages workflow.

The template excludes it. A scaffolded project therefore never receives Concorde's user documents
or Protocol chapters.

## Around it

Views sits between the Spec core it reads and the Distribution that packages and calls it.
Views also relies on Distribution's package layout:

```d2
views: Views
core: Spec core
distribution: Distribution
views -> core
views -> distribution
distribution -> views
```

<a id="uses-spec"></a>

**Spec core** owns:

- The project [registry](../../glossary.json#concept.registry).
- Spec loading.
- [impact indexes](../../glossary.json#concept.impact-index).

The publisher relies on the registry for which Modules and documents exist and which contains
which. It relies on the meaning of `selected-by` for the provenance it shows. The publisher parses
the registry and metadata itself in TypeScript. When it can't publish an input, the publisher
refuses it, failing the build and keeping the old site. It leaves full structural conformance to
the Spec validator. The scaffold relies on Spec core for:

- The root Module's title.
- The common result shape and error record.
- Safe project-relative paths without symbolic links.

It creates its files itself, as the scaffold's design above says. Both proposing and applying
first read the project's Spec configuration. When it isn't readable, the scaffold returns
`invalid` and asks for initialization, before it reads the proposal or touches a destination.

The scaffold returns Spec core's [command-line envelope](../spec/contracts.md#validation-result)
and its [error record](../spec/errors.md). Views includes both documents for these definitions.

<a id="uses-distribution"></a>

**Distribution** packages Views and installs its template. Views relies on two of its promises, as
data and an installation layout, never by importing Distribution's code:

- The package descriptor `concorde.json`, which must name `docsite` as a package root.
- The installer, which
  [places the template](../../distribution/requirements.md#req.distribution.installer-docsite-template)
  under `.concorde/framework/docsite/`, where an installed scaffold reads it.

Distribution calls the scaffold and packages it. The `distribution -> views` above is its own
`uses`, declared there as an [optional integration](../../glossary.json#concept.optional-integration)
with the spec part. The spec part registers `concorde
docsite` and the docsite template as its install contribution. Distribution's command dispatches
`docsite` to the scaffold. The scaffold reads templates from the installed package. Under any of
these conditions, the scaffold returns `invalid` and asks for a reinstall:

- `concorde.json`, the descriptor of the package, omits `docsite` as a package root.
- The template is missing.
- The template is unsafe.

Distribution's installer ships the template files by calling the inventory rule Views defines
rather than repeating it. The two therefore cannot disagree on the template. Its
[build manifest](../../glossary.json#concept.build-manifest) records Concorde's own build outputs.
That manifest is unrelated to the docsite's.
