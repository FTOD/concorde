```concorde-document
{
  "id": "document.specs.implementations.spec-engine",
  "targets": [
    "implementation.spec-engine"
  ],
  "main_visible": false
}
```

# Spec Engine implementation

`implementation.spec-engine` follows Spec Protocol 2.0.0 and binds the exact files below. It is reused by `module.installation`, `module.spec-context`.

## Responsibility

Realize phase-specific context assembly, initialization proposals and deterministic Spec structure/contract checks.

## Bound files

- `src/concorde/__init__.py`
- `src/concorde/__main__.py`
- `src/concorde/diagnostics.py`
- `src/concorde/frontmatter.py`
- `src/concorde/model.py`
- `src/concorde/projection.py`
- `src/concorde/specification/__init__.py`
- `src/concorde/specification/context.py`
- `src/concorde/specification/initialize.py`
- `src/concorde/specification/validation.py`
- `src/concorde/understanding/__init__.py`
- `src/concorde/understanding/alignment.py`
- `src/concorde/understanding/context.py`
- `src/concorde/understanding/feature_workspace.py`
- `src/concorde/understanding/initialize.py`
- `src/concorde/understanding/planning_context.py`
- `src/concorde/understanding/readiness.py`
- `src/concorde/understanding/repository.py`
- `src/concorde/understanding/validate.py`
- `src/concorde/understanding/validation/__init__.py`
- `src/concorde/understanding/validation/diagrams.py`
- `src/concorde/understanding/validation/entities.py`
- `src/concorde/understanding/validation/features.py`
- `src/concorde/understanding/validation/freshness.py`
- `src/concorde/understanding/validation/hierarchy.py`
- `src/concorde/understanding/validation/layout.py`
- `tests/__init__.py`
- `tests/concorde/PROFILE8_TEST_MIGRATION.md`
- `tests/concorde/__init__.py`
- `tests/concorde/fixtures/ask/questions.json`
- `tests/concorde/fixtures/context-project/.concorde/config.json`
- `tests/concorde/fixtures/context-project/specs/example/architecture.md`
- `tests/concorde/fixtures/context-project/specs/example/diagrams/delivery-sequence.json`
- `tests/concorde/fixtures/context-project/specs/example/diagrams/level-view.json`
- `tests/concorde/fixtures/context-project/specs/example/features/001-deliver.md`
- `tests/concorde/fixtures/context-project/specs/example/modules/api/architecture.md`
- `tests/concorde/fixtures/context-project/specs/example/modules/api/diagrams/level-view.json`
- `tests/concorde/fixtures/context-project/specs/example/modules/api/features/001-invoke.md`
- `tests/concorde/fixtures/context-project/specs/example/modules/api/modules/store/architecture.md`
- `tests/concorde/fixtures/context-project/specs/example/modules/api/modules/store/diagrams/system-overview.json`
- `tests/concorde/fixtures/interfaces/alignment/alignment-explorer.example.json`
- `tests/concorde/fixtures/interfaces/alignment/alignment-explorer.schema.json`
- `tests/concorde/fixtures/interfaces/alignment/alignment-input.example.json`
- `tests/concorde/fixtures/interfaces/alignment/alignment-input.schema.json`
- `tests/concorde/fixtures/interfaces/alignment/knowledge-graph.example.json`
- `tests/concorde/fixtures/interfaces/alignment/knowledge-graph.schema.json`
- `tests/concorde/fixtures/interfaces/reflections/index.json`
- `tests/concorde/fixtures/interfaces/reflections/needs-comments/R-001.md`
- `tests/concorde/fixtures/interfaces/reflections/pending/R-002.md`
- `tests/concorde/fixtures/interfaces/workspace/architecture-service.schema.json`
- `tests/concorde/fixtures/interfaces/workspace/context-response.json`
- `tests/concorde/fixtures/interfaces/workspace/deliver-eligible-response.json`
- `tests/concorde/fixtures/interfaces/workspace/deliver-proposal.json`
- `tests/concorde/fixtures/interfaces/workspace/feature-workspace.schema.json`
- `tests/concorde/fixtures/interfaces/workspace/validation-response.json`
- `tests/concorde/fixtures/invalid-projects/broken-reference/seed.json`
- `tests/concorde/fixtures/invalid-projects/contract/seed.json`
- `tests/concorde/fixtures/invalid-projects/cycle/seed.json`
- `tests/concorde/fixtures/invalid-projects/duplicate-id/seed.json`
- `tests/concorde/fixtures/invalid-projects/parse/seed.json`
- `tests/concorde/fixtures/invalid-projects/reflections-malformed/.concorde/reflections/index.json`
- `tests/concorde/fixtures/invalid-projects/reflections-malformed/.concorde/reflections/pending/R-001.md`
- `tests/concorde/fixtures/invalid-projects/reflections-malformed/.concorde/reflections/pending/R-002.md`
- `tests/concorde/fixtures/invalid-projects/reflections-malformed/.concorde/reflections/planned/R-003.md`
- `tests/concorde/fixtures/invalid-projects/reflections-malformed/README.md`
- `tests/concorde/fixtures/invalid-projects/reflections-malformed/seed.json`
- `tests/concorde/fixtures/invalid-projects/scenario/seed.json`
- `tests/concorde/fixtures/invalid-projects/view-depth/seed.json`
- `tests/concorde/fixtures/permission-planning-project/.concorde/attempts/feature.example.consumer.change/tasks.md`
- `tests/concorde/fixtures/permission-planning-project/.concorde/attempts/feature.example.other/secret.md`
- `tests/concorde/fixtures/permission-planning-project/.concorde/config.json`
- `tests/concorde/fixtures/permission-planning-project/.concorde/constitution.md`
- `tests/concorde/fixtures/permission-planning-project/.concorde/feature.json`
- `tests/concorde/fixtures/permission-planning-project/.concorde/reflections/log.md`
- `tests/concorde/fixtures/permission-planning-project/specs/example/architecture.md`
- `tests/concorde/fixtures/permission-planning-project/specs/example/modules/consumer/architecture.md`
- `tests/concorde/fixtures/permission-planning-project/specs/example/modules/consumer/features/001-change.md`
- `tests/concorde/fixtures/permission-planning-project/specs/example/modules/provider/architecture.md`
- `tests/concorde/fixtures/permission-planning-project/specs/example/modules/provider/features/001-api.md`
- `tests/concorde/fixtures/permission-planning-project/specs/example/modules/provider/features/002-unrelated.md`
- `tests/concorde/fixtures/permission-planning-project/src/consumer/service.py`
- `tests/concorde/fixtures/permission-planning-project/src/provider/private.py`
- `tests/concorde/fixtures/permission-planning-project/tests/consumer/test_service.py`
- `tests/concorde/fixtures/permission-planning-project/tests/provider/test_private.py`
- `tests/concorde/fixtures/two-level-project/.concorde/attempts/feature.example.checkout.authorize/plan.md`
- `tests/concorde/fixtures/two-level-project/.concorde/config.json`
- `tests/concorde/fixtures/two-level-project/.specify/feature.json`
- `tests/concorde/fixtures/two-level-project/specs/example/architecture.md`
- `tests/concorde/fixtures/two-level-project/specs/example/diagrams/system-overview.json`
- `tests/concorde/fixtures/two-level-project/specs/example/features/001-checkout.md`
- `tests/concorde/fixtures/two-level-project/specs/example/features/002-atomic.md`
- `tests/concorde/fixtures/two-level-project/specs/example/features/003-authorize-payment.md`
- `tests/concorde/fixtures/two-level-project/specs/example/features/004-confirm-order.md`
- `tests/concorde/fixtures/valid-project/.concorde/config.json`
- `tests/concorde/fixtures/valid-project/specs/example/architecture.md`
- `tests/concorde/fixtures/valid-project/specs/example/diagrams/level-view.json`
- `tests/concorde/fixtures/valid-project/specs/example/features/001-deliver.md`
- `tests/concorde/fixtures/valid-project/specs/example/modules/api/architecture.md`
- `tests/concorde/fixtures/valid-project/specs/example/modules/api/diagrams/system-overview.json`
- `tests/concorde/fixtures/valid-project/specs/example/modules/api/features/001-invoke.md`
- `tests/concorde/specification/__init__.py`
- `tests/concorde/specification/support.py`
- `tests/concorde/specification/test_agent_binding.py`
- `tests/concorde/specification/test_boundaries.py`
- `tests/concorde/specification/test_distribution.py`
- `tests/concorde/specification/test_module_architecture.py`
- `tests/concorde/specification/test_module_model.py`
- `tests/concorde/specification/test_review.py`
- `tests/concorde/specification/test_scope_and_reflections.py`
- `tests/concorde/specification/test_scoped_protocol.py`
- `tests/concorde/support/__init__.py`
- `tests/concorde/support/build_fixture.py`
- `tests/concorde/support/feature_workspace.py`
- `tests/concorde/support/operation_json.py`
- `tests/concorde/support/paths.py`
- `tests/concorde/support/reflection_triage.py`
- `tests/concorde/understanding/__init__.py`
- `tests/concorde/understanding/acceptance/__init__.py`
- `tests/concorde/understanding/contract/__init__.py`
- `tests/concorde/understanding/contract/test_alignment_explorer_contract.py`
- `tests/concorde/understanding/contract/test_feature_workspace_contract.py`
- `tests/concorde/understanding/integration/__init__.py`
- `tests/concorde/understanding/integration/test_alignment_explorer.py`
- `tests/concorde/understanding/integration/test_architecture_readiness.py`
- `tests/concorde/understanding/integration/test_context.py`
- `tests/concorde/understanding/integration/test_feature_workspace.py`
- `tests/concorde/understanding/integration/test_initialize.py`
- `tests/concorde/understanding/integration/test_validation.py`
- `tests/concorde/understanding/unit/__init__.py`
- `tests/concorde/understanding/unit/test_abstract_rules.py`
- `tests/concorde/understanding/unit/test_alignment.py`
- `tests/concorde/understanding/unit/test_contract_validation.py`
- `tests/concorde/understanding/unit/test_entity_rules.py`
- `tests/concorde/understanding/unit/test_feature_relations.py`
- `tests/concorde/understanding/unit/test_feature_rules.py`
- `tests/concorde/understanding/unit/test_feature_workspace.py`
- `tests/concorde/understanding/unit/test_frontmatter.py`
- `tests/concorde/understanding/unit/test_interface_rules.py`
- `tests/concorde/understanding/unit/test_module_diagram_rules.py`
- `tests/concorde/understanding/unit/test_planning_context.py`
- `tests/concorde/understanding/unit/test_repository.py`
- `tests/concorde/understanding/unit/test_rules.py`
- `tests/concorde/understanding/unit/test_summary_rules.py`
- `tests/concorde/understanding/unit/test_terminology_rules.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/specification/context.py` | Builds immutable Module contexts; only code writing appends Implementation Specs and file bindings. |
| `src/concorde/specification/initialize.py` | Creates a Profile 9 Module stub and registry schema 2 without inventing product features. |
| `src/concorde/specification/validation.py` | Checks local Module architecture/dependencies, explicit identities and interface agreement. |
| `src/concorde/understanding/` | Retains isolated legacy diagnostic readers; Profile 9 admission uses the specification package. |
| `tests/concorde/specification/` | Exercises the new model, context isolation, transactions and shared implementation evidence with controlled test doubles. |

## Implementation interfaces, dependencies and constraints

Context assembly selects registered document bytes, rules, instructions, task, admitted stage inputs and lifecycle identity into an immutable canonical snapshot. Global assembly deduplicates complete Markdown and authored diagram bodies into sorted source pools with per-Module references; the coordinator answers directly from those originals. Only code writing appends Implementation Spec bodies; code review receives the separately declared file references. The initializer proposes an honest module.md with an inline Mermaid diagram and an empty external diagrams array. Dependencies are repository selection, wire admission, exact-file application and phase-specific Agent definitions. The retained understanding readers and legacy fixture documents are isolated diagnostic implementation assets, not additional live project Spec collections.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Context and boundary cases must cover local Feature/Interface focus, shared membership, absent implementation bodies in planning, changed document/diagram bytes, malformed or foreign stage inputs and stale Protocol binding. Initialization cases cover absent-only destinations and complete recovery. Deterministic validators establish named structural invariants and never report universal semantic completeness.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
