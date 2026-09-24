# Views requirements

The Module-wide obligations of [Views](module.md). The entry explains why they exist; the
[pipeline](pipeline.md) explains how the publisher meets them.

## Sources and pages

### req.views.registry-derived-pages — Pages derive from the registry

Publication SHALL publish as Spec pages exactly the documents that the registry's Modules own.

User documents and custom docs are separate surfaces and are not Spec pages.

### req.views.no-directory-scanning — No discovery of documents

Publication SHALL NOT discover Spec documents by scanning directories or following links.

### req.views.one-page-per-document — One canonical page per document

Publication SHALL publish every registered document at exactly one canonical page, however many Modules select it.

### req.views.navigation-follows-composition — Navigation follows composition

The Spec navigation SHALL nest one Module under another only where the other declares `contains` for it.

### req.views.reading-collections — Role selects the reading collection

Publication SHALL place each document in the reading collection named by its declared role without changing its route, owner or selecting Modules.

A document with role `module` is listed in Module documents and one with role `implementation` in
Implementation documents. The role is read from metadata and never inferred from a file name, a heading
or the presence of definitions.

## Rendering

### req.views.stable-anchors — Identities are anchors

Publication SHALL expose every concept, realization, requirement, scenario and contract identity as an anchor on the canonical page of the document that defines it.

### req.views.import-definition — Imported definitions are shown

Publication SHALL show next to each Terminology import row the definition of the imported concept as written in its defining document at build time.

### req.views.illustrative-label — Illustrative diagrams are labelled

Publication SHALL render every D2 block marked `illustrative` with a visible label stating that it is not normative.

### req.views.derived-views-not-written — Rendering never edits sources

Publication SHALL NOT write rendered, enriched or rewritten content into any registered Spec document.

### req.views.diagram-source-identity — A fence is its diagram's only source

Publication SHALL render each D2 diagram from its fence in the containing document and from no other source.

The rendered image is staged beside its page and derived only from the fence and the publisher's
house style, so a diagram changes only when the document containing it or the house style changes.

### req.views.diagram-look — The publisher decides how a diagram looks

Publication SHALL choose how a checked D2 diagram looks from what each shape resolves to.

A shape that names the page's Module, one of its descendants, another Module, a concept, a
realization or a file each has one fixed look, and an edge between two Modules looks different
from an edge that relates nodes.

### req.views.diagram-subset — A diagram that sets its own look is refused

Publication SHALL refuse a checked D2 block that leaves the semantic subset, naming its document and line.

The semantic subset is the Protocol's. A reading that sets a style, shape, class or layout is
refused because the look is the publisher's.

### req.views.d2-program — Diagrams are rendered by the d2 program

Publication SHALL render D2 with the `d2` program from github.com/d2lang/d2, taken from `CONCORDE_D2`, else from `.concorde/tools/d2`, else from `PATH`.

The Concorde installer places a pinned, checksum-verified release at `.concorde/tools/d2`, so an
installed project needs no configuration; a source checkout uses `d2` on `PATH`.

### req.views.d2-failure — A diagram that cannot be rendered fails the build

Publication SHALL fail naming the diagram's document and line when the `d2` program is missing or rejects the diagram.

A missing program is reported with how to install it, and a rejected diagram with the program's own
message.

### req.views.user-docs — User documents are the home page and the first tab

Publication SHALL publish configured user documents from their directory as it is, in the first navigation tab, with their root page as the site's home page, never as Spec pages.

Their sidebar follows the directory's folders. Without user documents the home page opens the root
Module's entry.

### req.views.custom-docs — Custom docs stay outside the Specs

Publication SHALL publish custom docs only in their own tabs and routes, after the Spec tabs, never as Spec pages or inside a Spec collection.

### req.views.provenance-selection — Provenance agrees with Spec core

The selecting Modules that publication shows for a document SHALL equal Spec core's `selected-by` index for that document.

### req.views.no-agent-context-grant — Pages grant no context

Views SHALL NOT supply a published page to any agent as context or as a substitute for a registered document.

## Build and promotion

### req.views.current-internal-links — Internal links resolve

The build SHALL promote only a candidate in which every internal link resolves to an existing page and every requested fragment to an anchor on that page.

Links to other origins, or outside the site's base URL, are not checked; publication does not
promise that another website stays available.

### req.views.promote-requires-checked-candidate — Only checked candidates are promoted

The build SHALL promote only a candidate whose build manifest, source digest and page inventory match the current sources.

### req.views.promote-atomic — Failed promotion restores the published site

Promotion SHALL restore the previous published site when moving the candidate into place fails.

### req.views.production-preview-isolation — Production does not disturb the preview

A production build SHALL NOT clear or overwrite the generated files of the development preview.

### req.views.hash-format — Digest format

Every content or source digest that publication records SHALL be `sha256:` followed by 64 lowercase hexadecimal digits.

### req.views.safe-relative-paths — Safe source paths

Publication SHALL read only source paths that are relative POSIX paths without empty, `.` or `..` components, backslashes or symbolic links.

## Scaffold

### req.views.scaffold-creation-only — The scaffold only creates

The scaffold SHALL NOT replace or delete any existing file.

### req.views.template-inventory — One template inventory

The scaffold and the installer SHALL select the packaged docsite template files by one shared inventory rule.
