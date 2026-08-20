# Contract: Concorde Architecture Source Profile 1

**Profile ID**: `profile.concorde.architecture-sources.v1`

**Governing boundary contract**: `contract.core.architecture-services`. This document is the
normative maintained-source representation used by that service, not an additional module boundary.

**Representation**: UTF-8 Markdown with constrained YAML front matter and UTF-8 JSON

## Authority

- Markdown owns module, feature, scenario, contract, constraint, and decision prose plus stable
  relationship metadata.
- Archify JSON owns module-level component placement, connections, and named scenario views.
- Each feature has one canonical module-owned specification at
  `specs/<root-slug>[/modules/<child-slug>...]/features/<number-name>/spec.md`; its textual outcome and
  requirements are primary, while scenarios are representative examples. Architecture metadata and
  behavioral text coexist there instead of being split across parallel feature documents.
- Code and tests own implementation and executable evidence. Missing evidence remains `unknown`.

## Package Discovery

`.concorde/config.json` is JSON with this initial shape:

```json
{
  "profile_version": 1,
  "specification_root": "specs/example",
  "root_module_id": "module.example"
}
```

`specification_root` is the unified subtree recursively containing `module.md`,
`contracts/**/contract.md`, `features/*/spec.md`, and declared Archify JSON views. Readers MAY accept
the legacy key `architecture_root` only as an explicitly versioned migration alias; writers emit
`specification_root`. Paths are project-relative POSIX paths. Absolute paths, backslashes, empty
segments, `.` segments, `..` segments, and symlink escapes are invalid.

## Front-Matter Subset

Profile 1 supports:

- a document beginning with `---`, a closing `---`, then Markdown;
- mappings expressed by indentation in multiples of two spaces;
- string, integer, boolean, and null scalars;
- inline empty arrays (`[]`) and mappings (`{}`);
- block scalar lists using `- value`;
- nested mappings and lists of mappings needed by contract representations and scenario interactions;
- quoted strings without YAML tags, anchors, aliases, merge keys, or executable/custom types.

Unsupported YAML constructs produce a parse finding; the runtime never guesses their meaning.

## Document Profiles

### Module

Required front matter:

```yaml
id: module.example
kind: module
parent: null
view: specs/example/architecture.json
children: []
features: []
contracts:
  provided: []
  required: []
```

Required Markdown sections are `Responsibility` and `Boundary`. A leaf may omit `view` or set it to
null; a non-leaf must identify exactly one current-level view.

### Feature

Required front matter:

```yaml
id: feature.example.outcome
kind: feature
module: module.example
refines: []
scenarios:
  - scenario.example.primary
contracts:
  provided:
    - contract.example.workflow
  required: []
architecture_view: specs/example/architecture.json
evidence_status: unknown
canonical_spec: specs/example/features/001-outcome/spec.md
```

A lower-level feature without a parent refinement must include `internal: true` and a non-empty
`internal_rationale`. Its Markdown body contains the primary textual definition and requirements;
scenario references supply examples and do not exhaustively define the feature.

### Contract

Required front matter:

```yaml
id: contract.example.workflow
kind: contract
module: module.example
role: provided
flow: bidirectional
counterparties:
  - external.maintainer
representation:
  kind: standard
  format: Example Protocol
  version: "1"
  definition: https://example.invalid/protocol
features:
  - feature.example.outcome
evidence_status: unknown
```

Required Markdown sections are `Purpose`, `Information`, `Obligations`, `Failure Semantics`,
`Compatibility`, and `Evidence`. A custom representation uses a project-relative schema or grammar,
includes complete field semantics and compatibility rules, and references at least one representative
example.

### Scenario

A scenario may be a dedicated Markdown document or a structured current-level record referenced by a
feature. Its machine-readable data includes a stable ID, owning module, participants, and ordered
interactions. Each interaction has `from`, `to`, `description`, and `contract` when it crosses a
module boundary. A prose-only scenario sets `prose_only: true` and supplies a rationale.

### Architecture view

The JSON document follows the Archify architecture schema supported by this project and must also
satisfy Concorde visibility rules:

- participants are the current module boundary, its immediate child modules, and permitted externals;
- child features, grandchild modules, and implementation details are absent;
- every referenced scenario belongs to the current module level;
- every connection endpoint resolves within the view; and
- every boundary-crossing connection can be traced to a declared contract in maintained Markdown.

## Stable IDs

- IDs use lowercase dotted namespaces and hyphenated terminal words.
- IDs are unique across all documents of the same kind and may not be reassigned to a different
  meaning within the same Concorde major version.
- References use IDs, not titles or inferred filenames.
- Module containment and feature refinement are acyclic.
- Feature refinements cross one adjacent module level only.

## Diagnostics

Every invalid source yields a `Validation Finding` with a stable rule ID, severity, project-relative
source and optional location, message, and concrete remediation. The validator is read-only and
reports all independently detectable findings in deterministic order.

## Compatibility

Readers of profile 1 reject an unsupported `profile_version`. Adding optional fields is compatible;
removing a required field, changing field meaning, or expanding accepted syntax incompatibly requires
a new profile version and migration guidance.
