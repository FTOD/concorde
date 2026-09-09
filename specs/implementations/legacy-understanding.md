```concorde-document
{
  "id": "document.implementation.legacy-understanding",
  "targets": [
    "implementation.legacy-understanding"
  ],
  "main_visible": false
}
```

# Legacy understanding implementation

`implementation.legacy-understanding` follows Spec Protocol 2.1.0 and binds the exact files below. It is reused by `module.reflections`, `module.distribution`, `module.views`.

## Responsibility

Retain the Profile 7 readers, validators, feature-workspace delivery tools and their fixtures until their remaining importers are migrated. This realization is a pending removal; it supplies no cognitive input to any Profile 9 Agent.

## Bound files

- `src/concorde/lifecycle/__init__.py`
- `src/concorde/lifecycle/delivery.py`
- `src/concorde/projection.py`
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
- `tests/concorde/PROFILE8_TEST_MIGRATION.md`
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
- `tests/concorde/lifecycle/__init__.py`
- `tests/concorde/lifecycle/contract/__init__.py`
- `tests/concorde/lifecycle/integration/__init__.py`
- `tests/concorde/lifecycle/integration/test_implementation_delivery.py`
- `tests/concorde/support/feature_workspace.py`
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
| `src/concorde/understanding/` | Profile 7 project repository, validators, alignment explorer and feature workspace. `validate_project` delegates to the Profile 9 validator for a Profile 9 configuration. |
| `src/concorde/projection.py` | Profile 7 projections used only by the understanding package. |
| `src/concorde/lifecycle/` | Profile 7 attempt-directory delivery; no runtime importer remains. |
| `tests/concorde/understanding/`, `tests/concorde/lifecycle/`, `tests/concorde/support/feature_workspace.py` | Legacy regression suites and helpers. |
| `tests/concorde/fixtures/` legacy projects and interface samples | Profile 7 layouts used only by the legacy suites and by two host tests that need any project directory. |

## Implementation interfaces, dependencies and constraints

Four live importers remain: the maintenance CLI's `validate` subcommand and `scripts/reflections_queue.py` call `validate_project`; `src/concorde/reflections/validation.py` uses `RepositoryError` and `safe_relative_path`; `src/concorde/autodocs/docsite_scaffold.py` uses `ProjectRepository` for loading, path resolution and staged promotion. Removal replaces these with `validate_repository`, the typed-value safe-path helpers and `apply_files`, deletes this package with its fixtures and suites, and moves `tests/concorde/host/unit/test_worktree_boundary.py` and the two tests that import legacy helpers onto a Profile 9 fixture. Until then, this package must not be extended and its fixtures are not live project Specs.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

The legacy suites remain regression evidence for the retained utilities only; their removal accompanies the migration of the four importers and is verified by the referencing Modules' own suites.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
