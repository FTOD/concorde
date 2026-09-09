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

This Implementation Spec binds the exact files below. It is reused by `module.installation`, `module.spec-context`.

## Responsibility

Install, initialize, configure and upgrade Concorde while preserving user-owned content. Resolve complete Module contracts, bind code-writing implementation context and validate explicit Spec structure. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

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

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

Context assembly partitions Module contracts from Implementation Specs. Only the implementation phase adds implementation documents; planners and task authors receive none. Registry and context digests include exact membership. Validation checks Module dependency promises and separate Implementation bindings. Initialization writes an honest Module stub and empty implementation registry.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
