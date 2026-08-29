# Build Manifest Contract v5

**Contract ID**: `contract.documentation.build-manifest`

**Owner**: `module.concorde.documentation`

**Role / flow**: provided, output

**Consumers**: maintainers, tests, CI freshness checks, and later Concorde publication commands

## Representation

Custom JSON serialized as UTF-8 and validated against
[`build-manifest.schema.json`](build-manifest.schema.json). Object keys follow schema order when
written; all source, page, exclusion, route, link, and check arrays are deterministically sorted.

## Semantics

- `schemaVersion`: manifest compatibility version, currently `9`.
- `generator`: Concorde docsite and Docusaurus version identities; deliberately contains no timestamp.
- `collections`: logical view definitions, canonical source roots, inclusion patterns, and route bases,
  including the one-file `home` collection rooted at the project and mapped to `/`.
- `pages`: one record per included source, including hash, route, title, navigation, provenance,
  optional feature identity/status, providing-module route, containment relationships, and
  adjacent-level refinement relationships, plus architecture
  identity metadata and, for a module page, `architectureDiagrams` (source, source hash, kind,
  title, and delivered route of every diagram beneath the module's `architecture/diagrams/`). Relationship summaries contain stable identity, title, source-owned
  outcome, status, and route without copying specification bodies.
- `excludedSources`: Markdown artifacts considered during discovery but deliberately not published.
- `routeInventory`: all verified public routes relevant to this contract.
- `validation`: `passed` only after every named deterministic check succeeds.

The representative serialized payload is
[`build-manifest.example.json`](build-manifest.example.json).

## Failure Semantics

A failed run does not emit or promote a success manifest. Schema-invalid, incomplete, unsorted,
absolute-path-bearing, or unverified manifests fail the candidate build. Diagnostics identify the
schema path or governing rule.

## Compatibility

Consumers MUST reject unsupported `schemaVersion` values. Adding optional fields is compatible.
Removing or redefining fields, weakening relative-path rules, or changing the meaning of validation
status requires a new schema version. The schema and representative example change together.
Version 5 adopts schema v9, which adds the required root README collection and admits `README.md` as
a project-relative source path. Version 4 used schema v8 and five collections rooted only at `docs/`
and `specs/`.

## Evidence

- The representative example validates against the normative schema.
- Homepage evidence asserts exactly one `README.md` page at `/` with project-document kind and provenance.
- Unit tests validate sorting, relative paths, source hashes, feature conditional fields, authored
  child order, parent/sibling/refinement navigation, providing-module links, and exclusion of
  parent/child attempts.
- Production integration validates the emitted manifest and compares two unchanged builds.
