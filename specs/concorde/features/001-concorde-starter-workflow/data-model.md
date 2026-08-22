# Phase 1 Data Model: Concorde Starter Workflow

## Overview

The starter workflow has three related domains:

1. the Spec Kit distribution domain, which installs and tracks one bundle, one preset, and one
   extension; and
2. the Concorde architecture domain, which maintains project intent and returns deterministic
   proposals, bounded contexts, and validation findings; and
3. the explanatory publication domain, which renders feature-owned supplemental diagrams without
   changing package, feature, contract, or module authority.

Installation provenance is evidence about deployed tooling. Architecture documents remain intended
design. Neither is allowed to imply that implementation agrees with that intent.

## Entity Relationship Summary

```text
ComponentCatalogEntry (bundle, preset, or extension)
  └── is resolved by Spec Kit into an ExpandedComponentPlan
        ├── reads one ConcordeStarterBundle recipe
        ├── pins exactly one ConcordeCorePreset
        ├── pins exactly one ConcordeExtension
        └── produces one InstallationRecord per project

ConcordeCorePreset
  └── contributes guidance to the normal Spec Kit lifecycle
        └── produces one canonical feature spec at its owning module

ConcordeExtension
  └── is rendered by one ActiveAgentIntegration
        └── registers three AgentCommands
              └── invoke one ArchitectureOperation each

ArchitecturePackage
  ├── contains Modules
  │     ├── own Features
  │     ├── declare Contracts
  │     └── contain immediate child Modules
  ├── contains Scenarios and ArchitectureViews
  └── yields BoundedContexts and ValidationReports

SupplementalExplanatoryView
  └── renders one generated HTML projection plus visual evidence
```

## Distribution Entities

### Concorde Starter Bundle

The native Spec Kit installation unit.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `schema_version` | string | yes | Must be a Spec Kit-supported bundle schema version; initial value `1.0`. |
| `id` | slug | yes | Stable value `concorde-starter`. |
| `name` | string | yes | Human-readable display name. |
| `version` | semver | yes | Release version; component pins must resolve for this release. |
| `role` | string | yes | Initial role `developer`. |
| `description` | string | yes | States the starter workflow outcome. |
| `author` | string | yes | Release authority. |
| `license` | SPDX string | yes | Must match distributed component licensing. |
| `speckit_version` | version range | yes | Must include only versions with acceptance evidence; initial release targets 0.16.4. |
| `extensions` | component reference list | yes | Exactly one entry: `concorde` with a pinned semver. |
| `presets` | component reference list | yes | Exactly one entry: `concorde-core`, pinned, with priority and `append` strategy. |
| `steps` | list | yes | Explicitly empty. |
| `workflows` | list | yes | Explicitly empty. |
| `tags` | string list | yes | Discovery terms such as architecture, context, validation, and spec-driven-development. |

Relationships:

- Resolves one `Concorde Core Preset` and one `Concorde Extension` through active component catalogs.
- Produces or updates one `Installation Record` after the complete plan succeeds.

Validation:

- Manifest fields satisfy the native bundle contract.
- Component count is exactly two and kinds are exactly preset plus extension.
- Every non-step component has a pinned version.
- No integration is declared, so the target project's active integration is inherited.

### Component Catalog Entry

Spec Kit discovery and trust metadata for one independently packaged release unit. The catalog is
not the archive and does not own component behavior.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `catalog_kind` | enum | yes | `bundle`, `preset`, or `extension`. |
| `catalog_url` | URL | yes | Source configured with a Spec Kit trust/install policy. |
| `id` | slug | yes | Matches the archive manifest identity. |
| `version` | semver | yes | Matches the archive manifest version. |
| `download_url` | URL | yes | Location from which Spec Kit later retrieves the archive. |
| `sha256` | digest | conditional | Required when the catalog profile supplies digests; must match archive bytes. |
| `requires` | compatibility metadata | yes | Includes the supported Spec Kit range. |
| `trust` | enum/policy | yes at resolution | Must permit installation, not discovery only. |

The release builder derives `download_url` from its `--base-url` input and writes it into the catalog;
it does not contact that URL. Local acceptance serves the already-built files afterward.

### Expanded Component Plan

The accepted preview Spec Kit resolves before mutation. It is lifecycle state, not a second bundle
manifest.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `bundle` | ID/version | yes | Resolved `concorde-starter` identity and version. |
| `components` | ordered component list | yes | Exactly the pinned preset and extension for this release. |
| `compatibility` | result | yes | Evaluated against the current Spec Kit version before mutation. |
| `integration` | inherited integration ID | yes | Comes from the target project because the bundle declares none. |
| `sources` | catalog provenance list | yes | Records catalog URL and trust decision for each unit. |
| `overlaps` | ownership analysis | yes | Names components already installed or shared with another bundle. |
| `accepted_snapshot` | canonical JSON/digest | yes before install | The `info` plan against which installation results are compared. |

For unchanged catalog and project state, `info` and `install` must resolve the same ordered component
plan. Spec Kit owns resolution, mutation, registry records, rollback, update, and removal.

### Concorde Core Preset

The composable architecture-aware guidance layer.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `id` | slug | yes | Stable value `concorde-core`. |
| `version` | semver | yes | Independently versioned and equal to the catalog/archive metadata. |
| `speckit_version` | version range | yes | Initial supported line is 0.16.4. |
| `templates` | template contribution list | yes | Exactly the needed spec, plan, and task fragments. |
| `strategy` | enum | yes per contribution | `append`; content must not contain a second full core template. |
| `priority` | integer | installation | Set by the bundle reference; lower values have higher precedence. |

Relationships:

- Composes over Spec Kit core and below any higher-priority local override.
- Adds requirements consumed by canonical `spec.md`, `plan.md`, and `tasks.md` artifacts.

### Concorde Extension

The Spec Kit capability package.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `id` | slug | yes | Stable value `concorde`. |
| `version` | semver | yes | Independently versioned and pinned by the bundle. |
| `speckit_version` | version range | yes | Initial supported line is 0.16.4. |
| `commands` | command definition list | yes | Exactly the three canonical starter commands. |
| `runtime` | file set | yes | Installed project-local deterministic implementation. |
| `effect` | enum | yes | `read-write`; only initialization apply may write maintained architecture. |

Relationships:

- Registers `Agent Command` artifacts through the active integration.
- Commands invoke the extension's installed `Architecture Operation` runtime.

### Active Agent Integration

The Spec Kit-selected adapter that presents portable extension commands in one coding agent. It owns
presentation and registration syntax, not Concorde semantics or runtime behavior.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `integration_id` | stable Spec Kit ID | yes | Selected by the initialized target project. |
| `presentation_mode` | enum/string | yes | For example Codex skills or a slash-command surface. |
| `invocation_syntax` | string profile | yes | Agent-native command naming and separators. |
| `rendered_artifacts` | project-relative path list | yes | Native command files produced from portable extension definitions. |
| `registration_state` | enum | yes | `registered`, `partial`, or `failed`. |

The bundle inherits this integration. Changing integrations may change rendered files and invocation
syntax, but must not change command inputs, architecture operations, structured outputs, or failure
semantics.

### Installation Record

Spec Kit-owned lifecycle provenance for one project.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `bundle_id` | slug | yes | `concorde-starter`. |
| `version` | semver | yes | Successfully installed bundle version. |
| `installed_at` | UTC timestamp | yes | Lifecycle provenance; excluded from reproducible artifact comparisons. |
| `contributed_components` | component reference list | yes | Only components actually attributable to this or another bundle. |
| `source` | provenance | yes in aggregate status | Catalog/artifact source and trust policy. |
| `state` | enum | yes in aggregate status | `active`, `disabled`, `partial`, or `absent`. |

State transitions:

```text
absent --install succeeds--> active
absent --install fails-----> absent (plus residual-state diagnostic if rollback is incomplete)
active --repeat install----> active (no source changes)
active --disable component-> disabled
active --update succeeds---> active at new accepted version
active --update fails-------> active at prior recorded version or partial with explicit residuals
active --remove succeeds---> absent (project-authored architecture retained)
```

## Agent and Runtime Entities

### Agent Command

Portable command metadata and orchestration instructions.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `name` | command ID | yes | One of `speckit.concorde.init`, `.context`, or `.validate`. |
| `description` | string | yes | Same intent across integrations. |
| `arguments` | command-specific tokens | yes | Parsed according to `contracts/agent-commands.md`. |
| `effect` | enum | yes | `init`: propose/read or approved write; `context` and `validate`: read-only. |
| `runtime_operation` | enum | yes | Exactly one of `init`, `context`, `validate`. |

### Architecture Operation

A deterministic request and response pair.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `schema_version` | integer | yes | Initial value `1`. |
| `operation` | enum | yes | `init`, `context`, or `validate`. |
| `target` | string | yes | Stable ID or project-relative path; `.` is valid for project root. |
| `options` | object | yes | Operation-specific; unknown required behavior is rejected. |
| `status` | enum | response | `success`, `proposal`, `unchanged`, `invalid`, `conflict`, or `failed`. |
| `artifacts` | path list | response | Sorted project-relative paths only. |
| `findings` | finding list | response | Sorted by rule, source, location, and message. |
| `result` | object | response | Operation-specific payload. |

Validation:

- Must conform to `contracts/architecture-service.schema.json`.
- Must never include absolute paths, timestamps, random identifiers, or agent-authored commentary.
- Same sources and arguments must produce byte-equivalent canonical JSON.

### Initialization Proposal

Reviewable intended changes before any maintained-source write.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `proposal_version` | integer | yes | Initial value `1`. |
| `project_root_id` | stable module ID | yes | Slug-derived or explicitly supplied; cannot collide. |
| `responsibility` | string | yes | Observable project-level responsibility. |
| `boundary` | string | yes | Owned and explicitly excluded concerns. |
| `provided_contracts` | ID list | yes | Explicit list; empty is valid. |
| `required_contracts` | ID list | yes | Explicit list; empty is valid. |
| `children` | child summary list | yes | Immediate submodules only; empty is valid. |
| `files` | proposed file list | yes | Project-relative targets and complete proposed content hashes. |
| `conflicts` | conflict list | yes | Existing or unsafe targets that prevent apply. |

State transitions:

```text
candidate -> proposed -> accepted -> applied
                  \-> rejected
proposed -> conflict (if target state changes before apply)
applied  -> unchanged (on idempotent repeat)
```

Only the agent/user interaction can mark a proposal accepted. The runtime accepts a proposal file but
does not infer approval.

## Architecture Source Entities

### Architecture Package

The maintained project specification root. It contains architecture and module-owned feature
specifications in one recursive hierarchy while preserving their distinct canonical meanings.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `profile_version` | integer | yes | Initial value `1`, recorded in `.concorde/config.json`. |
| `root` | project-relative path | yes | `specs/<root-slug>/`, containing the root `module.md`. |
| `root_module_id` | stable module ID | yes | Resolves exactly once. |
| `modules` | module set | yes | Contains one root and an acyclic containment hierarchy. |
| `features` | feature set | yes | Every feature has one providing module. |
| `contracts` | contract set | yes | Every reference resolves with owner and role. |
| `scenarios` | scenario set | yes | Participants obey the owning view's boundary. |
| `views` | view set | yes | One for every non-leaf module. |

### Module

| Field | Type | Required | Rules |
|---|---|---:|---|
| `id` | stable ID | yes | Globally unique, `module.<namespace>[.<segment>...]`. |
| `parent` | module ID or null | yes | Null only for the single root. |
| `responsibility` | Markdown section | yes | One clear responsibility. |
| `boundary` | Markdown section | yes | States owned and excluded concerns. |
| `children` | module ID list | yes | Immediate children only; explicit empty list for leaves. |
| `features` | feature ID list | yes | Features owned at this abstraction level. |
| `contracts.provided` | contract ID list | yes | Explicit, possibly empty. |
| `contracts.required` | contract ID list | yes | Explicit, possibly empty. |
| `view` | project-relative path or null | yes | Required for non-leaf modules; null/omitted only for leaves. |

Relationships:

- Contains zero or more immediate child `Module` entities.
- Owns zero or more `Feature` and `Contract` entities.
- Has at most one parent, and the containment graph is acyclic.

### Feature

| Field | Type | Required | Rules |
|---|---|---:|---|
| `id` | stable ID | yes | Globally unique, `feature.<namespace>.<name>`. |
| `module` | module ID | yes | Exactly one providing module. |
| `outcome` | Markdown text | yes | Primary, normative description of the observable behavior at this level. |
| `refines` | feature ID list | yes | Root features use explicit empty list; child features link only to adjacent parent-level features unless internal. |
| `internal_rationale` | string | conditional | Required only when a lower-level feature intentionally has no parent refinement. |
| `scenarios` | scenario ID list | yes | Representative, non-exhaustive examples; at least one unless an explicit no-example rationale exists. |
| `contracts.provided` | contract ID list | yes | At least one provided contract. |
| `contracts.required` | contract ID list | yes | Explicit, possibly empty. |
| `evidence_status` | enum | yes | `unknown`, `partial`, `verified`, or `disagrees`. |
| `canonical_spec` | project-relative path | yes for Spec Kit features | Points to the single Spec Kit `spec.md` where applicable. |
| `workspace` | project-relative directory | yes | `<owning-module-path>/features/<number-name>/`; supporting plan/task artifacts stay beside, but do not replace, `spec.md`. |

### Contract

| Field | Type | Required | Rules |
|---|---|---:|---|
| `id` | stable ID | yes | Globally unique, `contract.<namespace>.<name>`. |
| `module` | module ID | yes | Owning module. |
| `role` | enum | yes | `provided` or `required`. |
| `flow` | enum/string | yes | Direction meaningful to the boundary. |
| `counterparties` | ID/string list | yes | At least one audience, provider, consumer, or external actor. |
| `obligations` | Markdown section | yes | Observable guarantees. |
| `failure_semantics` | Markdown section | yes | Named failure behavior. |
| `compatibility` | Markdown section | yes | Version and evolution expectations. |
| `representation.kind` | enum | yes | `standard` or `custom`. |
| `representation.format` | string | yes | Named format. |
| `representation.version` | string/integer | yes | Relevant version. |
| `representation.definition` | URL/path | yes | Authoritative definition or checked-in schema/grammar. |
| `examples` | path list | conditional | Required for custom representations. |
| `evidence` | evidence reference list | yes | Explicit; may record unknown. |

### Scenario

| Field | Type | Required | Rules |
|---|---|---:|---|
| `id` | stable ID | yes | Unique within the package. |
| `module` | module ID | yes | Module-level view that owns the scenario. |
| `participants` | ID list | yes | Current module, immediate children, or permitted externals only. |
| `interactions` | ordered interaction list | yes | Every boundary crossing names a governing contract. |
| `prose_only` | boolean | no | If true, includes rationale and need not resolve to the view. |

### Architecture View

The canonical one-level structural view owned by a module and validated by Architecture Core source
profile 1.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `path` | project-relative JSON path | yes | Referenced by its current module. |
| `current_module` | module ID | derived/yes | Exactly one owning module. |
| `components` | view participant list | yes | Current-level child modules and permitted external actors; no grandchildren. |
| `connections` | ordered/identified edge list | yes | Participants resolve and boundary crossings map to contracts. |
| `scenarios` | view IDs | yes | Resolve corresponding module-level scenarios unless prose-only. |

### Supplemental Explanatory View

A Feature-001-owned visual explanation that is deliberately outside the module-owned Architecture
View entity and Architecture Core source profile 1. It cannot define modules, feature behavior,
contract obligations, or package contents.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `source_path` | project-relative JSON path | yes | Maintained beside Feature 001; not named `architecture.json`. |
| `diagram_kind` | enum | yes | `component-model` or `installation-flow`. |
| `question_answered` | string | yes | Structural ownership or temporal release/install/use flow. |
| `authority_references` | path/ID list | yes | Points to manifests, feature prose, and contracts that own represented facts. |
| `textual_counterparts` | path/section list | yes | Complete explanation available without the visual. |
| `generated_output` | project-relative HTML path | yes | Reproducible projection under `generated/architecture/`. |
| `generator_provenance` | version/digest | yes | Records renderer version and source/output freshness. |
| `validation_receipt` | evidence reference | yes | All Archify showcase checks must pass. |
| `viewport_evidence` | evidence list | yes | Four desktop sizes plus light/dark perceptual review. |
| `publication_route` | route | yes | Existing documentation-site route; no starter runtime command is added. |

Instances:

- `spec-kit-component-model.json` owns only the layout of the package-role explanation.
- `starter-installation-flow.json` owns only the layout of release-to-install and the two use-time
  paths.

## Result Entities

### Bounded Context

| Field | Type | Required | Rules |
|---|---|---:|---|
| `requested_id` | stable ID | yes | Original module or feature target. |
| `current_module` | full module projection | yes | Includes current features, provided/required contracts, and organization. |
| `children` | summary list | yes | Immediate children and their I/O only. |
| `externals` | participant list | yes | Only actors present in the current module's view. |
| `scenarios` | scenario list | yes | Current-level scenarios only. |
| `refinement_links` | feature link list | yes | Adjacent-level links relevant to the current module. |
| `deeper_references` | ID/path list | yes | Navigation references without expanded content. |

Validation:

- No child feature body or grandchild body may appear.
- Every returned entity belongs to the current module, an immediate child summary, or permitted
  external actor.

### Validation Finding

| Field | Type | Required | Rules |
|---|---|---:|---|
| `rule_id` | stable rule ID | yes | Machine-stable identifier such as `CONCORDE-ID-001`. |
| `severity` | enum | yes | `error`, `warning`, or `info`. |
| `source` | project-relative path | yes | No absolute path. |
| `line` | positive integer | no | Included when known. |
| `column` | positive integer | no | Included when known. |
| `subject_id` | stable ID | no | Affected declared entity when resolvable. |
| `message` | string | yes | Describes the violation without volatile data. |
| `remediation` | string | yes | Concrete maintainer action. |

### Validation Report

| Field | Type | Required | Rules |
|---|---|---:|---|
| `status` | enum | yes | `success` when no errors; otherwise `invalid` or `failed`. |
| `artifacts` | path list | yes | All inspected maintained sources, sorted. |
| `findings` | finding list | yes | Complete and deterministically sorted. |
| `summary.errors` | integer | yes | Count derived from findings. |
| `summary.warnings` | integer | yes | Count derived from findings. |
| `summary.infos` | integer | yes | Count derived from findings. |
| `source_digest` | SHA-256 string | yes | Digest of normalized ordered source path/byte pairs. |

Evidence status is validated as explicit metadata but is not promoted to `verified` by architecture
validation itself.
