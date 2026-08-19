---
id: module.concorde.architecture-core
kind: module
parent: module.concorde
children: []
features: []
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

Explicitly empty during root-feature specification. Lower-level core features MUST be specified before
implementation begins and MUST refine `feature.concorde.install-starter-workflow`.

## Canonical Contract Definition

### `contract.core.architecture-services`

- **Role / flow**: provided, bidirectional.
- **Consumers**: Spec Kit Integration and Documentation.
- **Representation**: custom Concorde Architecture Service Protocol v1.
- **Message meaning**: request one deterministic operation over one project architecture package and
  return either a complete result or explicit findings.

#### Normative grammar

```text
request  = operation, target, options
response = operation, target, status, artifacts, findings
operation = "init" | "context" | "validate"
status = "success" | "proposal" | "unchanged" | "invalid" | "conflict" | "failed"
```

#### Field semantics

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `operation` | string | yes | One of `init`, `context`, or `validate`. |
| `target` | string | yes | Project-relative path or stable module/feature ID. |
| `options` | mapping | yes | Operation-specific, documented options; empty is valid. |
| `status` | string | response | Completed outcome: success, proposal, unchanged, invalid source, conflict, or execution failure. |
| `artifacts` | list | response | Project-relative sources read, created, or returned. |
| `findings` | list | response | Deterministic diagnostics with rule, location, and remediation. |

#### Representative serialized example

```yaml
operation: context
target: module.concorde
options:
  depth: 1
status: success
artifacts:
  - architecture/concorde/module.md
  - architecture/concorde/architecture.json
findings: []
```

- **Compatibility**: v1 consumers ignore unknown optional fields; removing or changing a required
  field requires a new major protocol version.
- **Validation evidence**: unknown until request/response schema and contract tests are implemented.
- **Required contracts**: explicit empty set for the starter slice; filesystem access is treated as an
  implementation detail constrained to the project root.
