# Content Sources Contract v7

**Contract ID**: `contract.documentation.project-content`

**Owner**: `module.concorde.documentation`

**Role / flow**: required, input

**Providers**: Architecture Core and the Spec Kit lifecycle for `specs/`; project maintainers for `docs/`

## Purpose

Provide canonical architecture sources (including module design references), project documentation,
feature specifications, and accepted feature implementations to the generated site without copying
or modifying their maintained sources.

## Representation

- UTF-8 Markdown files using [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/) plus the Markdown
  features supported by the pinned Docusaurus release.
- Optional YAML front matter using [YAML 1.2.2](https://yaml.org/spec/1.2.2/).
- Project-relative POSIX paths in diagnostics and generated manifests.

## Accepted Inputs

| Collection | Source root | Eligible inputs | Public route base |
|---|---|---|---|
| Architecture | `specs/` | Every regular file matching `**/module.md` or `**/contracts/**/contract.md` | `/architecture` |
| Architecture (module design references) | `specs/` | Every regular file named `design.md` whose directory also contains a `module.md`; published in the Architecture collection as kind `module-design` | `/architecture` |
| Project documentation | `docs/` | Every regular file matching `**/*.md` | `/docs` |
| Feature abstracts | `specs/` | Every regular file matching `**/abstract.md` beside a `design.md`; the feature's landing page | `/features` |
| Feature designs | `specs/` | Every canonical feature-root `design.md` | `/features` |
| Feature implementations | `specs/` | Every feature-root `implementation.md` beside `design.md` | `/features` |

Symbolic links are not followed. Normalized source paths must remain beneath their declared root.
Architecture, feature abstracts, feature designs, and feature implementations are disjoint
projections. A `design.md` beside `module.md` is a module design reference; otherwise a canonical
feature `design.md` owns behavior. Missing feature companions and legacy names are errors.

## Field Semantics

### Project Documentation

- `title`: optional YAML title; otherwise the first level-one Markdown heading; one is required.
- `sidebar_label`: optional navigation label that does not replace the canonical title.
- `sidebar_position`: optional finite number used to order siblings.
- `slug`: optional route override constrained to the `/docs` route space.
- Markdown links: repository-relative links to included Markdown are mapped to their published routes;
  fragments are preserved.
- Concorde's self-hosting documentation baseline: `docs/index.md`, six framework learning guides,
  and `docs/contributing/docsite.md`; all remain ordinary Project Documents rather than a new content
  kind.
- Canonical authority links: a framework guide that summarizes normative architecture, feature, or
  command behavior includes at least one repository-relative link to the relevant included source.

### Feature Designs

- `id`: required globally unique stable feature ID.
- `kind`: required and equal to `feature`.
- `module`: required owning module ID.
- `subfeatures`: optional ordered IDs on a top-level feature. Each ID resolves to one immediate child
  beneath that feature's `subfeatures/<number-name>/` directory.
- `parent_feature`: required on an immediate sub-feature and absent on a top-level feature. The child
  inherits its parent's module, cannot register children, and owns one non-empty `## Outcome` used in
  concise navigation summaries.
- first level-one heading: required feature title.
- `Status` metadata line: required lifecycle status and displayed without changing its meaning.
- `diagrams`: optional list of feature-owned Archify declarations. Every source must be directly
  below the feature's `diagrams/` directory and name its `core` or `supplemental` role, kind,
  scenarios or question, and generated output. A feature may declare at most one core diagram, and
  its kind must be `architecture`; dynamic kinds are supplemental. The JSON `diagram_type` and
  `meta.output` must agree with the declaration.
- Parent directory: the feature or immediate sub-feature directory; its `abstract.md`, `design.md`, and
  `implementation.md` are permanent site content. No third feature level is publishable.

### Feature Implementations

- first level-one heading: required feature-implementation title.
- Parent directory: the feature directory containing the paired `design.md`; the page is published as
  kind `feature-implementation` and linked with that design.
- Content: the accepted durable realization of the feature (a not-yet-hardened placeholder is still
  published with its provenance); temporal files beneath `attempt/` remain excluded.

### Module Design References

- first level-one heading: required title.
- Parent directory: the module directory containing the paired `module.md`; a `design.md` anywhere
  else (including a feature root) is not eligible and is reported as an error by the architecture
  validator, not published.
- Content: the module's implementation detail and design rationale. The file has no front matter and
  no independent ID; the page is published in the Architecture collection as kind `module-design`
  with the owning module's ID and provenance and is linked from the module page.

### Architecture Sources

- `id`: required globally unique stable architecture entity ID.
- `kind`: required and equal to `module` or `contract`; feature `design.md` is classified only as a
  Feature Specification, and a module design reference derives kind `module-design` from its
  adjacency to `module.md`.
- `module`: required owning module ID for feature and contract sources.
- `parent`: optional parent module ID for non-root module sources.
- `view` or `architecture_view`: optional project-relative path to maintained Archify JSON.
- A declared view must contain a valid `meta.output` beneath `generated/`. Preview and production
  publication discover the declaration and create its verified disposable HTML before the registry
  admits the route. The page records the JSON source hash and embeds the HTML in a sandbox.

## Obligations

- Consumers MUST read sources without writing content, metadata, or timestamps.
- Consumers MUST include each eligible valid source exactly once.
- Consumers MUST report deliberately excluded Markdown below `specs/` as
  `not-canonical-feature-artifact` in the build manifest.
- Consumers MUST preserve authored prose, headings, code, tables, and supported links.
- Consumers MUST expose content kind and project-relative provenance on every page; architecture pages
  additionally expose stable ID, kind, hierarchy metadata, and view provenance when applicable.
- Consumers MUST discover feature diagrams from `design.md`, deliver and verify their generated outputs before publication, include
  their source hashes and routes in the manifest, and embed every declared view on the canonical
  feature page with a standalone-view link.
- Consumers MUST reject duplicate, escaping, mismatched, stale, failed, or incomplete diagram
  deliveries and MUST NOT require committed HTML or machine-local visual-check evidence.
- Providers MUST keep stable feature IDs unique and internal Markdown targets resolvable.
- Providers MUST keep parent registration and child back-references bidirectionally consistent.
  Consumers publish ordered child summaries on the parent and parent/sibling links on the child,
  without copying requirements or publishing any `attempt/` source.
- The Concorde self-hosting provider MUST keep the eight-page framework guide baseline discoverable,
  keep the landing page linked to all six learning guides, and retain resolvable canonical-authority
  links from guides that summarize normative behavior.

## Failure Semantics

Unreadable sources, invalid YAML or JSON, missing required identity, invalid feature-diagram
placement/declarations, duplicate feature or architecture
IDs, escaping paths, missing or ambiguous Markdown targets, excluded-source links, unpublishable
declared views or feature diagrams, and route collisions are errors. Each
diagnostic includes a rule ID, source path when applicable, reason, and remediation. Any error stops
candidate publication.

## Compatibility

This is contract version 7. It publishes `abstract.md` as `feature-abstract`, feature `design.md` as
`feature-design` at `/design`, and `implementation.md` as `feature-implementation` at
`/implementation`, while excluding `attempt/**`; it matches Build Manifest schema version 7.
Earlier versions used the former filenames and route meanings. Version 4 moved diagram delivery from a
manually prepared prerequisite into preview/production publication. Adding optional metadata or more project
documents is backward compatible. Changing source roots, eligibility globs, required fields, route
bases, path semantics, or exclusion meaning requires a new contract version and a route/content
migration decision.

## Evidence

- Contract fixtures for valid documents and feature specifications.
- Negative fixtures for every failure class.
- Source-immutability integration test around validation, preview setup, and production build.
- Manifest completeness comparison against the discovered source inventory.
