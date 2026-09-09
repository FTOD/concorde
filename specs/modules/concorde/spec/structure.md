```concorde-document
{
  "id": "document.spec.structure",
  "targets": [
    "module.spec"
  ],
  "main_visible": true
}
```

# Spec structure and validation

This document defines the registry shape this Module admits and the deterministic validation it performs against that shape. Selection and returned value records are defined in [registry](registry.md) and [values](values.md); the admission scenarios for a consistent or inconsistent inventory are defined in [module](module.md).

## Registry shape

Registry schema 3 contains `schema_version`, `project_id`, `entry_target`, `targets` and `checks`. A Module descriptor has `id`, `kind="module"`, `title`, `documents`, `parent`, `uses`, `files` and `checks`. Every array is explicit. `files` MUST equal the sorted union of the Module's own entity file declarations; membership, composition and dependency are checked independently of that file set. The entry names one Module, and its complete collection starts routing.

Each Markdown document declares `id`, exact `targets` and `main_visible`. A Module's `concorde-dependencies` entries contain `target_id`, `responsibility`, `selection_condition` and nonempty `relied_upon_promises`, covering exactly its children and `uses` targets. A Module's `concorde-entities` blocks declare `id`, `title`, `kind`, `responsibility` and optionally `files`, `pending` and `target_id`; every child and used Module needs exactly one entity naming it by `target_id`. Every Concorde Module has a principal entity diagram in its `module.md` Architecture section, whose node labels equal its entity titles; this is a project convention, not an extra Protocol requirement. Check records declare `id`, `target_id`, `argv`, `timeout_seconds` and optional `inputs`. Shared implementation changes affect every Module whose entity lists the changed file; validation and downstream tools evaluate each affected Module's own contract separately.

Topology preparation stores the exact validated registry/document replacements below the ignored `.concorde/topology-proposals/` host area. Its public ArtifactRef binds path and digest. Applying the artifact rechecks its embedded design identity, discovery context, Protocol, registry base and every file before-digest before one atomic transaction.

## Scenarios

### scenario.spec.validate-success — A conforming Spec state validates successfully

- GIVEN a registry and documents that satisfy every structural rule
- WHEN the validator runs
- THEN it returns success with no error findings and a source digest for the assessed state
- BUT success is not represented as proof that every promise is semantically complete

### scenario.spec.validate-structural-errors — Reporting structural errors, not semantics

- GIVEN a Module missing one of its four mandatory sections, an unresolved scenario/requirement/entity identity collision, an entity file union that disagrees with the registry, or a missing local dependency promise
- WHEN the validator runs
- THEN it returns invalid with one rule-identified, remediable finding per problem
- AND it does not attempt to judge whether the underlying behavior is correct

### scenario.spec.validate-pending-warning — A created file still marked pending

- GIVEN an entity lists a file as both present in files and in pending
- AND that file now exists on disk
- WHEN the validator runs
- THEN it reports a warning, not an error
- BUT an undeclared missing file that is not marked pending is still an error

### scenario.spec.validate-architecture-mismatch — Diagram nodes must equal entity titles

- GIVEN a Module's Architecture section flowchart nodes differ from its declared entity titles, or an edge has no label
- WHEN the validator runs
- THEN it reports an architecture finding identifying the mismatched or unlabeled elements
- AND it requires the diagram nodes to be exactly the entity titles before the Module can validate successfully

## Requirements

- req.spec.structural-only: Validation SHALL check structure and explicit references and SHALL NOT claim to prove semantic completeness.
- req.spec.host-checks-separate: Configured implementation checks SHALL execute separately on the host using their registered argv and timeout_seconds, and their result SHALL NOT substitute for an agent reading source.
- req.spec.digest-per-assessment: Every validation result SHALL carry a source digest of the exact state it assessed.

## Validator interface

`validate_repository(root, target_id=None, package_root=None) -> ToolResult` returns
`status=success|invalid`, findings with `rule_id`, `message` and `remediation`, and a result
containing `source_digest` for the assessed Spec state. It checks identities, document
declarations, membership, dependency blocks, scenario/requirement/entity syntax, entity file
listings against the registry, architecture diagrams, structured contracts and Reflection
attribution; it explicitly does not prove semantics. Configured implementation checks execute
separately on the host using the registered `argv` and `timeout_seconds`, returning `check_id`,
`target_id`, `status`, `exit_code`, `source_digest` and `log_digest` with raw output retained
privately. No check result is a source-read proxy for an agent. Validation reads project files and
writes nothing.
