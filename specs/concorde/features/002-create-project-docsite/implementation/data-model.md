# Data Model: Unified Project Docsite

The model is an in-memory and generated build model. It introduces no database and never writes to
canonical sources.

## 1. Source Collection

Represents one canonical content authority.

| Field | Type | Rules |
|---|---|---|
| `id` | `architecture`, `docs`, or `features` | Unique and stable within manifest version 2. |
| `sourceBase` | project-relative path | `specs` for Architecture and Features; `docs` for Documentation. |
| `routeBase` | site-root path | `/architecture`, `/docs`, or `/features`; values must not overlap. |
| `include` | ordered glob list | Architecture selects `**/module.md` and `**/contracts/**/contract.md`; docs selects `**/*.md`; features selects `**/spec.md`. |
| `contentKind` | enum | `architecture-source`, `project-document`, or `feature-specification`. |

Relationships: one Source Collection contains zero or more Source Documents and maps to exactly one
Docusaurus docs-plugin instance. Documentation is read directly from `docs/`; Architecture and
Features reach their instances through disposable Renderer Projections generated from `specs/`.

## 2. Source Document

Shared attributes for a maintained Markdown source.

| Field | Type | Rules |
|---|---|---|
| `collectionId` | Source Collection ID | Required. |
| `sourcePath` | project-relative POSIX path | Required, unique, inside the collection root, no traversal. |
| `realPath` | build-local absolute path | Internal only; never emitted in the manifest or UI. |
| `title` | non-empty string | Front-matter title, otherwise first level-one heading. |
| `sourceSha256` | lowercase hex string | SHA-256 of exact source bytes. |
| `frontMatter` | key/value map | Parsed YAML; unknown keys remain source-owned. |
| `links` | Link Reference list | Sorted by source location and target. |
| `state` | Source State | Tracks validation and mapping. |

Validation rules:

- Only regular `.md` files are eligible; symbolic links are not followed in version 1.
- The normalized real path must remain within its declared source root.
- Source paths are compared case-sensitively and normalized to `/` separators.
- Title and source path must be present before route mapping.
- Discovery never changes file contents, metadata, or timestamps.

### 2.1 Project Document

Extends Source Document with optional navigation metadata.

| Field | Type | Rules |
|---|---|---|
| `sidebarLabel` | optional string | Overrides navigation label only; does not change canonical title. |
| `sidebarPosition` | optional finite number | Orders siblings; path order is the deterministic fallback. |
| `slug` | optional route segment | Must remain within `/docs` and must not collide. |

### 2.2 Feature Specification

Extends Source Document with Spec Kit and Concorde identity.

| Field | Type | Rules |
|---|---|---|
| `featureId` | stable ID string | Required from YAML `id`; globally unique. |
| `kind` | literal `feature` | Required. |
| `moduleId` | stable module ID | Required from YAML `module`. |
| `status` | non-empty string | Required from the specification metadata block. |
| `featureDirectory` | project-relative directory | Parent directory of canonical `spec.md`. |
| `diagrams` | Feature Diagram list | Derived only from the specification's declarations; sorted by source path. |

Only the canonical `spec.md` becomes a Feature Specification. Other files in the feature directory
become Excluded Source records and are never labeled as feature specifications.

#### 2.2.1 Feature Diagram

Maintained visual explanation owned by one Feature Specification but not itself a content page.

| Field | Type | Rules |
|---|---|---|
| `source` | project-relative path | Directly below the owning feature's `diagrams/`; descriptive JSON filename. |
| `sourceSha256` | lowercase hex string | SHA-256 of the exact maintained JSON bytes. |
| `kind` | Archify diagram kind | Must agree with JSON `diagram_type`. |
| `scenarios` | non-empty ID/question list | Declared by the owning `spec.md`. |
| `title` | non-empty string | Read from JSON `meta.title`. |
| `route` | generated site route | Derived from a matching `meta.output` beneath `generated/`. |

The generated HTML must exist before publication. The shared feature layout sandbox-embeds each
diagram, displays source provenance, and provides a standalone-view link. The JSON remains durable
explanatory intent; HTML and page markup remain generated projections.

### 2.3 Architecture Source

Extends Source Document with stable architecture identity, entity kind (`module` or `contract`),
owning module or parent where applicable, and optional declared-view metadata. Feature `spec.md` files
belong only to the Features collection. A declared view records its project-relative Archify JSON
source, SHA-256, and delivered site route. Invalid or missing view sources and generated outputs are
publication errors.

### 2.4 Renderer Projection

Internal, disposable input used only to isolate Docusaurus plugin loader roots.

| Field | Type | Rules |
|---|---|---|
| `collectionId` | `architecture` or `features` | Documentation does not require projection. |
| `canonicalSourcePath` | project-relative path under `specs/` | Resolves to exactly one validated Source Document. |
| `stagedPath` | path under `docsite/.generated/content/<collection>/` | Preserves the canonical path relative to `specs/`; never appears as provenance. |
| `sourceSha256` | lowercase hex string | Must equal the canonical source hash after copying. |
| `lifecycle` | enum | `materialized` for the current run or absent; never maintained or resumed. |

Every preview/build removes the prior projection root and recreates it from the validated registry.
The projection owns no meaning, is excluded from the build manifest's source inventory, and cannot be
edited as a source.

## 3. Link Reference

Represents an internal or external Markdown link encountered in one source.

| Field | Type | Rules |
|---|---|---|
| `rawTarget` | string | Exact authored destination. |
| `kind` | enum | `anchor`, `included-source`, `excluded-source`, `external`, or `asset`. |
| `targetSourcePath` | optional project path | Required for included/excluded source targets. |
| `targetRoute` | optional site route | Required for included sources after mapping. |
| `fragment` | optional string | Preserved during source-to-route mapping. |
| `location` | line/column | Used in actionable diagnostics. |

An included-source link may cross collections. A missing, ambiguous, outside-root, or excluded Markdown
target is invalid unless the source explicitly uses a published site URL rather than a source link.

## 4. Content Page

Read-only projection of one validated Source Document.

| Field | Type | Rules |
|---|---|---|
| `route` | absolute site path | Unique, stable for the source path and optional slug. |
| `sourcePath` | project-relative path | Resolves to exactly one Source Document. |
| `kind` | content-kind enum | Controls provenance label and metadata display. |
| `title` | string | Mirrors the canonical source title. |
| `navigation` | Navigation Entry | Exactly one primary placement. |
| `featureMetadata` | optional object | Feature ID, module, and status for feature pages only. |
| `diagrams` | optional Feature Diagram list | Included for feature pages, including an empty list when none are declared. |

The Content Page does not own prose. Presentation components may add provenance chrome but cannot
rewrite canonical requirements or documentation meaning.

## 5. Navigation Entry

| Field | Type | Rules |
|---|---|---|
| `section` | `Architecture`, `Documentation`, or `Features` | Derived from collection. |
| `label` | string | Sidebar label or canonical title. |
| `route` | site route | Must resolve to one Content Page. |
| `parentRoute` | optional site route | Must remain in the same section. |
| `position` | number or lexical fallback | Produces stable sibling ordering. |

Navigation is a forest with three roots. It must be acyclic, contain every Content Page exactly once,
and never point at an excluded source.

## 6. Excluded Source

| Field | Type | Rules |
|---|---|---|
| `sourcePath` | project-relative path | Unique and sorted. |
| `reason` | enum | Initially `not-canonical-feature-artifact`. |

This record makes the exclusion of `plan.md`, `tasks.md`, checklists, and other feature artifacts
observable rather than silently dropping them.

## 7. Validation Finding

| Field | Type | Rules |
|---|---|---|
| `ruleId` | stable string | Examples: `source.title.required`, `feature.id.unique`, `route.unique`. |
| `severity` | `error` | Version 1 has no warning path for contract violations. |
| `sourcePath` | optional project path | Included whenever a source caused the finding. |
| `location` | optional line/column | Included when parsing supplies it. |
| `message` | string | Explains the violation. |
| `remediation` | string | Gives a concrete correction. |

Any error prevents candidate rendering or promotion.

## 8. Build Manifest

The custom JSON contract is defined by `contracts/build-manifest.schema.json`.

| Field | Type | Rules |
|---|---|---|
| `schemaVersion` | integer | `2` after adding architecture publication. |
| `generator` | identity object | Concorde docsite and pinned Docusaurus versions; no timestamp. |
| `collections` | Source Collection list | Sorted by collection ID. |
| `pages` | Content Page summaries | Sorted by source path. |
| `excludedSources` | Excluded Source list | Sorted by source path. |
| `routeInventory` | unique route list | Sorted lexically and verified after render. |
| `validation` | passed checks | Successful manifests only; failed runs emit diagnostics, not a success manifest. |

## 9. State Transitions

### Source State

```text
discovered -> parsed -> validated -> mapped -> rendered
     |           |          |          |
     +----------> invalid <-+----------+
```

- `invalid` is terminal for the current build.
- A source enters `rendered` only when its expected route appears in actual production routes.

### Build State

```text
created -> validating -> materializing -> candidate-building -> candidate-verified -> promoting -> successful
              |              |                |                    |              |
              +--------------+----------------+--------------------+--------------> failed
```

- `failed` never changes the last successful `docsite/build/`.
- `successful` requires schema-valid manifest output and complete route verification.
- A new run always starts from `created`; stale candidates are disposable and never resumed.
