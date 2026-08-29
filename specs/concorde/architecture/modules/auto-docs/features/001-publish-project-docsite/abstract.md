# Feature Abstract: Publish the Project Docsite

`feature.auto-docs.publish-project-docsite` · specified at `module.concorde.auto-docs` ·
refines `feature.concorde.publish-project-docsite` · about three minutes. This page is enough to
understand what the Auto-Docs module builds and what must hold; the links at the end only
redirect you when you want more.

## Purpose

The Auto-Docs module projects architecture, permanent feature specifications and designs from
the unified `specs/` hierarchy, and project Markdown from `docs/` into one searchable, traceable,
read-only website, embedding each declared delivered Archify view beside its textual source. The
project-level feature owns the project-wide outcome; this feature owns the module's narrower behavior,
contracts, scenario, and evidence, for the maintainer who builds and browses the site without ever
treating a generated page as authority.

## Functionality

| View | Sources | Boundary |
|---|---|---|
| Architecture | `specs/**/module.md`, its sibling `design.md`, `specs/**/architecture/contracts/**/contract.md`, and every diagram beneath `specs/**/architecture/diagrams/` | Authority stays with the sources; a renderer projection is never maintained content. |
| Features | `specs/**/design.md` and each feature's permanent design reference | Temporal implementation artifacts are excluded. |
| Documentation | `docs/**/*.md` | A third view over the same two canonical roots. |

Architecture preserves declared module containment. Features uses the same module groups for
top-level feature ownership and explicit parent/sub-feature containment within each group, while
keeping identity-derived routes stable. A build is deterministic: unchanged inputs give an identical manifest and identical
source-to-route mappings, and every eligible source appears exactly once in the manifest. Any
renderer-specific staging is disposable, ignored, regenerated from the canonical registry, and
invisible in published provenance.

**Not part of this feature**: maintained architecture intent, validation semantics, Archify
rendering itself, user-authored sources, and any mutation of `specs/` or `docs/`.

## Structure

The maintained level view is <a href="/architecture/auto-docs.html">Auto-Docs</a>
(maintained source `specs/concorde/architecture/modules/auto-docs/architecture/diagrams/level-view.json`): the validated read
model inside its module boundary, its providers Project Docs, Project Specifications, and Archify,
and the maintainer who builds and browses. The parent's supplemental
<a href="/architecture/project-docsite-publication-flow.html">publication flow</a> explains the
build sequence.

```text
maintainer ──build-interface──▶ Auto-Docs
   docs/** · specs/** ──project-content──▶ │ registry: classify · route · validate
   Archify ◀──archify-renderer──▶          │ deliver declared views
                                           ├──build-manifest──▶ maintainer / freshness checks
                                           └──architecture-site──▶ maintainer browser
```

Five contracts bound the module: it provides `contract.auto-docs.architecture-site`,
`contract.auto-docs.build-interface`, and `contract.auto-docs.build-manifest`, and requires
`contract.auto-docs.project-content` and `contract.auto-docs.archify-renderer`. When any step
fails, the last successful site is preserved.

## Logic

**One build**

1. The maintainer invokes the documented build interface.
2. Auto-Docs consumes module and contract specifications, project Markdown, and canonical
   feature specification and design pairs through the project-content contract.
3. Each declared Archify JSON view is handed to the renderer and its delivered HTML associated with
   the source.
4. The read model is validated (identities, links, routes) and rendered; the deterministic build
   manifest is emitted.
5. The finished site is provided to the browser; a failure at any step keeps the previous site.

**Rules the implementation must keep**

- `module.md` and `contract.md` sources form the Architecture view without moving their authority
  or treating a renderer projection as maintained content (FR-DOC-001).
- Feature specifications and permanent designs form the Features view, and temporal implementation
  artifacts are excluded from it (FR-DOC-002).
- Architecture preserves module containment; Features groups by owning module and explicit feature containment
  (FR-DOC-003).
- `docs/` is a third view while only two canonical source roots exist: `specs/` and `docs/`
  (FR-DOC-004).
- Renderer-specific staging is disposable, ignored, regenerated from the canonical registry, and
  invisible in published provenance (FR-DOC-005).

## Read Next

- **Exact outcome, scenario, requirements, and success criteria** — [design.md](design.md): FR-DOC-001
  to FR-DOC-005 and SC-DOC-001 to SC-DOC-003.
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md).
- **The contracts** — [architecture-site](../../architecture/contracts/architecture-site/contract.md),
  [build-interface](../../architecture/contracts/build-interface/contract.md),
  [build-manifest](../../architecture/contracts/build-manifest/contract.md),
  [project-content](../../architecture/contracts/project-content/contract.md), and
  [archify-renderer](../../architecture/contracts/archify-renderer/contract.md).
- **The level this feature belongs to** — [module.md](../../module.md) (the Auto-Docs summary)
  and its [design reference](../../design.md); the project module summary is
  [module.md](../../../../../module.md).
- **The parent feature** — [Create Unified Project Docsite](../../../../../features/002-create-project-docsite/abstract.md)
  and its [design.md](../../../../../features/002-create-project-docsite/design.md), which carries the
  project-wide requirements and evidence.
- **Contributor guide** — [docs/contributing/docsite.md](../../../../../../../docs/contributing/docsite.md).
