---
id: module.concorde.architecture-core
kind: module
parent: module.concorde
children: []
features:
  - feature.architecture-core.manage-bounded-sources
contracts:
  provided:
    - contract.core.architecture-services
  required: []
---

# Architecture Core

## Responsibility

Define the Concorde source model and provide deterministic initialization, bounded context retrieval,
and validation over module, feature, scenario, contract, and architecture-view relationships.

## Boundary

Architecture Core owns source semantics, stable identity, relationship resolution, one-level
visibility, and validation findings. It does not own agent invocation syntax, distribution, Archify
rendering, Docusaurus publication, or implementation correctness.

## Feature Set

- `feature.architecture-core.manage-bounded-sources` refines
  `feature.concorde.workflow` and owns initialization, bounded feature/module context, and
  deterministic validation.

## Canonical Contract Definition

The maintained definition is `contracts/architecture-services/contract.md`; the summary below
provides bounded context.

### `contract.core.architecture-services`

- **Role / flow**: provided, bidirectional.
- **Consumers**: Spec Kit Integration and Documentation.
- **Representation**: custom Concorde Architecture Service Protocol v1.
- **Message meaning**: request one deterministic operation over one project architecture package and
  return either a complete result or explicit findings.

The normative JSON Schema is
`specs/concorde/features/001-concorde-workflow/contracts/architecture-service.schema.json`.
The outline below is explanatory and does not replace it.

#### Field semantics

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `schema_version` | integer | yes | Contract version; exactly `1`. |
| `operation` | string | yes | One of `init`, `context`, or `validate`. |
| `target` | string | yes | Project-relative path or stable module/feature ID. |
| `options` | object | request | Operation-specific documented options; empty is valid. |
| `status` | string | response | Completed outcome: success, proposal, unchanged, invalid source, conflict, or execution failure. |
| `artifacts` | list | response | Project-relative sources read, created, or returned. |
| `findings` | list | response | Deterministic diagnostics with rule, location, and remediation. |
| `result` | object | response | Operation-specific proposal, context, or validation result. |

#### Representative serialized example

```json
{
  "schema_version": 1,
  "operation": "context",
  "target": "module.concorde",
  "status": "success",
  "artifacts": ["specs/concorde/architecture.json", "specs/concorde/module.md"],
  "findings": [],
  "result": {"context": {"requested_id": "module.concorde"}}
}
```

The complete representative context and validation values linked by the child contract contain every
required nested field; this shortened value illustrates only the common envelope.

- **Compatibility**: v1 consumers ignore unknown optional fields; removing or changing a required
  field requires a new major protocol version.
- **Validation evidence**: verified by schema/example contract tests, deterministic operation tests,
  and zero-finding self-application to Concorde's maintained hierarchy.
- **Required contracts**: explicit empty set for the current slice; filesystem access is treated as an
  implementation detail constrained to the project root.
