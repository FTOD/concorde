---
id: feature.understanding.validate-architecture
kind: feature
module: module.concorde.understanding
related_features:
  - feature.concorde.workflow
  - feature.concorde.define-project-ontology
interfaces:
  provided:
    - interface.concorde.validate
  required: []
evidence_status: partial
---

# Feature Design: Validate Architecture

## Outcome and Scope

A maintainer receives a repeatable, complete, actionable account of Profile 7 layout, module/entity/
relationship/interface/reference integrity, Script/Skill/Operation structure, evidence status,
diagrams, freshness, and reflections.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `module.concorde.capabilities` | Routes validation targets and formats one structured result. |
| `entity.understanding.validator` | Loads the normalized source package and executes focused/full validators. |
| `entity.understanding.model-rules` | Supplies the deterministic layout/hierarchy/entity/feature/diagram/evidence/freshness rule sets the validator composes. |
| `entity.concorde.specification` | Supplies all maintained Profile 7 architecture/design/diagram sources. |
| `entity.concorde.control-state` | Supplies the reflection authority and active stable-ID attempts for control-state validation. |

## Interfaces

### `interface.concorde.validate` — Validate Profile 7 sources and control state

- **Consumer**: Maintainer, CI, planning/implementation/delivery gates, and Auto-Docs.
- **Direction**: Project/target input to read-only structured findings.
- **Entry points**: Leaf Skill `concorde-validate` and native Runtime `validate` Tool in source or
  installed framework.
- **Inputs**: Project root plus optional stable module/feature focus.
- **Outputs**: Status, source digest, exact findings with rule/severity/subject/path/remediation, and evidence summary.
- **Obligations**: Be deterministic/non-mutating, report all applicable findings, and distinguish structure from behavior proof.
- **Failures**: Loader/config/source errors become actionable diagnostics and never trigger repair writes.
- **Compatibility**: Profile 7 validation rejects every legacy durable artifact, module-local attempt, specification-root reflection log, and removed protocol field.
- **Implementing entities**: `entity.understanding.validator`, `entity.understanding.model-rules`, `module.concorde.capabilities`.

## Usage Scenarios

1. Validate a complete project and receive all applicable findings plus one source digest.
2. Focus validation on one module/feature while retaining required ancestor/reference context.
3. Feed valid source/diagram state to Auto-Docs or delivery without either consumer repairing it.

## Related Features

- `feature.concorde.workflow` composes this feature as the deterministic gate every lifecycle phase
  and delivery consult before proceeding.
- `feature.concorde.define-project-ontology` states the capability-partition and typed-entity rules
  this feature enforces deterministically across every module.

## Requirements

- **FR-001**: Validation MUST check Profile 7 config/layout, rooted module cycles, exact inventories,
  path-safe IDs, stable-ID control bindings, entity types/locators, and relationship endpoints/direction.
- **FR-002**: It MUST check flat feature placement, related IDs, embedded interface completeness/ownership,
  zoom visibility, requirements/evidence state, one showcase Archify architecture system overview per
  module with principal entity relationships, diagram freshness, and reflection grammar/paths.
- **FR-003**: Legacy module-pair/trio/contracts/subfeatures and unsafe/symlinked sources MUST receive distinct actionable findings.
- **FR-004**: Validation MUST enumerate all applicable findings deterministically and MUST NOT mutate or claim implementation correctness.
- **FR-005**: Package-scoped validation MUST enforce Package Manifest 2's exact root inventories,
  leaf-Skill directories, globally unique capability names, exact Operation Python/Markdown pairs,
  declared multi-Skill membership, and absence of compatibility capability sources without importing
  arbitrary Operation Python.

## Edge Cases

- An external/conceptual entity has no filesystem path but a valid explicit locator.
- A relationship uses an undefined custom predicate or correct labels in the wrong direction.
