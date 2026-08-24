# Published Project Site Contract v3

**Contract ID**: `contract.documentation.architecture-site`

**Owner**: `module.concorde.documentation`

**Role / flow**: provided, output

**Consumers**: maintainer, contributor, and reviewer web browsers

## Purpose

Provide one browsable, searchable, read-only projection of canonical architecture sources, project
documentation, and permanent feature specifications and accepted designs.

## Representation

Static HTML conforming to the [HTML Living Standard](https://html.spec.whatwg.org/), with linked CSS,
JavaScript, assets, a local search index, and `build-manifest.json`.

## Route Contract

| Route | Meaning |
|---|---|
| `/` | Project landing page with Architecture, Documentation, and Features entry points and source counts |
| `/architecture/**` | Architecture module and contract Markdown plus declared embedded views |
| `/docs/**` | Project documents sourced from `docs/**/*.md` |
| `/features/**` | Permanent feature specifications from `specs/**/spec.md` and accepted designs from `specs/**/design.md`; specification pages include their declared feature diagrams |
| `/build-manifest.json` | Machine-readable successful-build inventory |

Every source-derived page displays its content kind and project-relative source path. Architecture
pages also display stable entity identity, hierarchy metadata, and declared-view provenance; feature
specification pages display stable feature ID, owning module, recorded lifecycle status, and every
declared fresh feature diagram, while feature-design pages identify their durable source provenance.
Draft status is visible and does not imply approval or implementation agreement.

## Guarantees

- Every eligible valid source has exactly one primary page and navigation entry.
- Architecture, Documentation, and Features remain distinct navigation sections and share
  project-wide local search.
- Delivered Archify HTML is sandboxed and paired with accessible, searchable architecture or feature
  Markdown; feature diagrams are embedded automatically from `spec.md` declarations.
- Cross-collection source links resolve to the corresponding site pages with fragments preserved.
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

The three top-level route spaces and manifest schema version remain stable within published-site
contract version 3. Source renames may change their derived routes unless a later redirect feature is
specified. Adding new content pages is compatible; changing a route base or removing provenance is
breaking.

## Evidence

- Production build route-inventory test.
- Navigation completeness and search smoke tests.
- Source-provenance component tests.
- Cross-collection link fixtures.
- Failed-candidate preservation test.
- Build manifest schema and representative example validation.
