# Content Sources Contract v2

**Contract ID**: `contract.documentation.project-content`

**Owner**: `module.concorde.documentation`

**Role / flow**: required, input

**Providers**: Architecture Core for `architecture/`; project maintainers for `docs/`; Spec Kit lifecycle for `specs/`

## Purpose

Provide canonical architecture sources, project documentation, and feature specifications to the
generated site without copying or modifying their maintained sources.

## Representation

- UTF-8 Markdown files using [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/) plus the Markdown
  features supported by the pinned Docusaurus release.
- Optional YAML front matter using [YAML 1.2.2](https://yaml.org/spec/1.2.2/).
- Project-relative POSIX paths in diagnostics and generated manifests.

## Accepted Inputs

| Collection | Source root | Eligible inputs | Public route base |
|---|---|---|---|
| Architecture | `architecture/` | Every regular file matching `**/*.md` | `/architecture` |
| Project documentation | `docs/` | Every regular file matching `**/*.md` | `/docs` |
| Feature specifications | `specs/` | Every regular file matching `**/spec.md` | `/features` |

Symbolic links are not followed. Normalized source paths must remain beneath their declared root.

## Field Semantics

### Project Documentation

- `title`: optional YAML title; otherwise the first level-one Markdown heading; one is required.
- `sidebar_label`: optional navigation label that does not replace the canonical title.
- `sidebar_position`: optional finite number used to order siblings.
- `slug`: optional route override constrained to the `/docs` route space.
- Markdown links: repository-relative links to included Markdown are mapped to their published routes;
  fragments are preserved.

### Feature Specifications

- `id`: required globally unique stable feature ID.
- `kind`: required and equal to `feature`.
- `module`: required owning module ID.
- first level-one heading: required feature title.
- `Status` metadata line: required lifecycle status and displayed without changing its meaning.
- Parent directory: the feature directory; only its `spec.md` is canonical site content in version 1.

### Architecture Sources

- `id`: required globally unique stable architecture entity ID.
- `kind`: required and equal to `module`, `feature`, or `contract`.
- `module`: required owning module ID for feature and contract sources.
- `parent`: optional parent module ID for non-root module sources.
- `view` or `architecture_view`: optional project-relative path to maintained Archify JSON.
- A declared view must contain a valid `meta.output` beneath `generated/`, and the delivered HTML must
  exist before publication. The page records the JSON source hash and embeds the HTML in a sandbox.

## Obligations

- Consumers MUST read sources without writing content, metadata, or timestamps.
- Consumers MUST include each eligible valid source exactly once.
- Consumers MUST report deliberately excluded Markdown below `specs/` as
  `not-canonical-feature-artifact` in the build manifest.
- Consumers MUST preserve authored prose, headings, code, tables, and supported links.
- Consumers MUST expose content kind and project-relative provenance on every page; architecture pages
  additionally expose stable ID, kind, hierarchy metadata, and view provenance when applicable.
- Providers MUST keep stable feature IDs unique and internal Markdown targets resolvable.

## Failure Semantics

Unreadable sources, invalid YAML or JSON, missing required identity, duplicate feature or architecture
IDs, escaping paths, missing or ambiguous Markdown targets, excluded-source links, unpublishable
declared views, and route collisions are errors. Each
diagnostic includes a rule ID, source path when applicable, reason, and remediation. Any error stops
candidate publication.

## Compatibility

This is contract version 2; it adds the Architecture collection and declared-view projection. Adding
optional metadata is backward compatible. Changing source roots,
eligibility globs, required fields, route bases, path semantics, or exclusion meaning requires a new
contract version and a route/content migration decision.

## Evidence

- Contract fixtures for valid documents and feature specifications.
- Negative fixtures for every failure class.
- Source-immutability integration test around validation, preview setup, and production build.
- Manifest completeness comparison against the discovered source inventory.
