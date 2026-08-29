# Published Project Site Contract v5

**Contract ID**: `contract.auto-docs.architecture-site`

**Owner**: `module.concorde.auto-docs`

**Role / flow**: provided, output

**Consumers**: maintainer, contributor, and reviewer web browsers

## Purpose

Provide one browsable, searchable, read-only projection of the root README introduction, canonical
architecture sources (including module design references), project documentation, and permanent
feature specifications and accepted implementations.

## Representation

Static HTML conforming to the [HTML Living Standard](https://html.spec.whatwg.org/), with linked CSS,
JavaScript, assets, a local search index, and `build-manifest.json`.

## Route Contract

| Route | Meaning |
|---|---|
| `/` | Root `README.md`, leading with project purpose, key features, and all Concorde-specific commands, with Architecture, Documentation, and Features entry points |
| `/architecture/**` | Architecture module, module design reference, and contract Markdown plus declared embedded views |
| `/docs/**` | Project documents sourced from `docs/**/*.md` |
| `/features/<feature-id>` | Top-level feature abstract, derived from stable feature identity rather than its module storage path |
| `/features/<parent-feature-id>/<sub-feature-id>` | Immediate sub-feature abstract nested only by explicit feature containment |
| `/features/**/design` | Canonical feature `design.md` companion page |
| `/features/**/implementation` | Accepted `implementation.md` companion page for a feature |
| `/build-manifest.json` | Machine-readable successful-build inventory |

For the Concorde self-hosting site, the Documentation route space includes this maintained baseline:

| Route | Reader outcome |
|---|---|
| `/docs/` | Documentation overview and progressive reading path |
| `/docs/quick-start` | Project-site preview, local framework installation, and first feature |
| `/docs/framework-overview` | Concorde purpose, influences, hierarchy, and adjacent-tool boundaries |
| `/docs/specification-model` | Durable architecture, module design reference, specification, and accepted implementation versus the temporal implementation attempt |
| `/docs/project-structure` | Workspace authority and correct edit locations |
| `/docs/concorde-workflow` | End-to-end architecture-aware development lifecycle |
| `/docs/commands` | Normal Spec Kit phases, Concorde operations, and installed command layers |
| `/docs/contributing/docsite` | Docsite authoring, validation, build, and troubleshooting |

Every source-derived page displays its content kind and project-relative source path. Architecture
pages also display stable entity identity, hierarchy metadata, and declared-view provenance; feature
specification pages display stable feature ID, owning module, recorded lifecycle status, and every
declared fresh feature diagram, while feature implementation pages and module design reference pages
identify their durable source provenance and owning feature or module.
Draft status is visible and does not imply approval or implementation agreement.

## Guarantees

- Every eligible valid source has exactly one primary page and navigation entry.
- Root `README.md` has exactly one source-derived page at `/`, includes visible source provenance,
  and replaces any independently authored site-only homepage narrative.
- Architecture, Documentation, and Features remain distinct navigation sections and share
  project-wide local search.
- Architecture navigation follows module containment. Features navigation follows stable feature
  identity and explicit parent/sub-feature containment; architecture/module source wrappers never
  appear as Features categories or route parents.
- Feature pages retain their providing module and refinement relationships as metadata and links
  without treating those relationships as feature containment.
- Delivered Archify HTML is sandboxed and paired with accessible, searchable architecture or feature
  Markdown; feature diagrams are embedded automatically from `design.md` declarations.
- Cross-collection source links resolve to the corresponding site pages with fragments preserved.
- The Documentation landing page links directly to all six framework learning guides, and guides
  that summarize normative behavior link to the relevant canonical Architecture or Features page.
- Presentation does not change canonical prose or write to the source trees.
- The site includes accessible textual content and provenance independent of decorative formatting.
- The manifest identifies included pages, deliberate exclusions, verified routes, generator versions,
  source hashes, and passed validation checks.
- Failed publication does not replace the last successfully promoted site.

## Failure Semantics

No candidate is publishable when source validation, link/route validation, rendering, search-index
generation, manifest-schema validation, or atomic promotion fails. Failure is reported through the
build interface and the prior successful output remains untouched.

## Compatibility

The three collection route spaces remain stable within published-site contract version 5; the
manifest schema version is owned by the build-manifest contract (schema version 9). Version 5 makes
the existing `/` route a source-backed projection of root `README.md`, changing its content authority
and provenance while preserving the public URL. The named
self-hosting Documentation baseline adds compatible pages within the
existing `/docs` route space. Version 4
replaces source/module-path-derived feature deep routes with stable-ID and explicit-containment
routes; this is a breaking deep-link migration inside the stable `/features` route base. Source
renames no longer change feature routes when stable IDs and containment remain unchanged. Adding new
content pages is compatible; changing a route base, route identity semantics, or provenance is
breaking.

## Evidence

- Production build route-inventory test.
- Navigation completeness and search smoke tests.
- Feature hierarchy tests covering root, module-level, and explicitly contained feature sources.
- Source-provenance component tests.
- Cross-collection link fixtures.
- Failed-candidate preservation test.
- Build manifest schema and representative example validation.
