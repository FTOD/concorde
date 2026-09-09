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

This document defines the project ontology this Module admits, the registry and check evidence it
records, and the deterministic validation it performs. Selection and returned value records are
defined in [registry](registry.md) and [values](values.md).

## feature.spec.ontology

A caller registers Module identities, one structural parent per Module, explicit uses relations,
features, usage interfaces and the complete ordered Markdown collection. Each Module registers
one module.md reading entry. Its collection explains its internal Architecture/domain and all
relied-upon collaborator promises. A planner determines tasks from this Module Spec alone.

Implementation Specs are registered separately by id, title, documents and explicit files.
Each file has one authoritative Implementation Spec; several Modules may reference the same
Spec. The registry derives reverse users and file ownership. An Implementation document cannot
also be Module context. Dependencies, implementation references and navigation links never add
other project Specs implicitly. The local [registry values](values.md) define the complete records.

## Registry and check evidence

Registry schema 2 contains schema_version, project_id, entry_target, targets, implementations
and checks. A Module descriptor has id, kind=module, title, documents, parent, uses,
implementations, features, interfaces, checks and diagrams. An Implementation Spec descriptor
has id, title, documents and explicit files. Every array is explicit; local feature/interface
records have id, title and document. The entry is a Module, and its complete collection starts routing.

Each Markdown declares id, exact targets and main_visible. Module concorde-dependencies entries
contain target_id, responsibility, selection_condition and nonempty relied_upon_promises. A diagram
is authored inline in registered Markdown, with its source path, `mermaid` kind and title stated
locally. Every Concorde Module has a principal entity diagram in `module.md`; this is a project
convention, not an extra Protocol requirement. New declarations use `diagrams: []`. Check
records declare id, target_id, argv, timeout_seconds and optional inputs. Shared implementation
checks run for every using Module, recording separate target IDs and current revisions. They never
combine the using Modules' Spec contexts or grant code to a planner.

Topology preparation stores the exact validated registry/document replacements below the ignored
`.concorde/topology-proposals/` host area. Its public ArtifactRef binds path and digest. Applying the
artifact rechecks its embedded design identity, discovery context, Protocol, registry base and every
file before-digest before one atomic transaction.

## interface.spec.validate

`validate_repository(root, target_id=None, package_root=None) -> ToolResult` returns
`status=success|invalid`, findings with `rule_id`, `message` and `remediation`, and a result
containing `source_digest` for the assessed Spec state. It checks identities, document
declarations, membership, dependency blocks, focus definitions, structured contracts,
implementation bindings and Reflection attribution; it explicitly does not prove semantics.
Configured implementation checks execute separately on the host using the registered `argv`
and `timeout_seconds`, returning `check_id`, `target_id`, `status`, `exit_code`, `source_digest`
and `log_digest` with raw output retained privately. No check result is a source-read proxy for an
agent. Validation reads project files and writes nothing.
