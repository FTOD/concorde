```concorde-document
{
  "id": "document.specs.implementations.publication-docsite",
  "targets": [
    "implementation.publication-docsite"
  ],
  "main_visible": false
}
```

# Publication Docsite implementation

This Implementation Spec binds the exact files below. It is reused by `module.publication`.

## Responsibility

Create navigable documentation and diagrams from registered Module and Implementation Specs. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

## Bound files

- `docsite/README.md`
- `docsite/docusaurus.config.ts`
- `docsite/package-lock.json`
- `docsite/package.json`
- `docsite/plugins/concorde-content/diagrams.ts`
- `docsite/plugins/concorde-content/graph.ts`
- `docsite/plugins/concorde-content/index.ts`
- `docsite/plugins/concorde-content/links.ts`
- `docsite/plugins/concorde-content/manifest.ts`
- `docsite/plugins/concorde-content/registry.ts`
- `docsite/plugins/concorde-content/routes.ts`
- `docsite/plugins/concorde-content/site-identity.ts`
- `docsite/plugins/concorde-content/types.ts`
- `docsite/plugins/concorde-content/validation.ts`
- `docsite/plugins/scoped-content/build-freshness.ts`
- `docsite/plugins/scoped-content/index.ts`
- `docsite/plugins/scoped-content/materialize.ts`
- `docsite/plugins/scoped-content/model.ts`
- `docsite/plugins/scoped-content/projections.ts`
- `docsite/scaffold/deploy-docsite.yml`
- `docsite/scripts/build.ts`
- `docsite/scripts/inspect.ts`
- `docsite/scripts/materialize-content.ts`
- `docsite/scripts/prepare-publication.ts`
- `docsite/scripts/render-diagrams.ts`
- `docsite/scripts/start.ts`
- `docsite/scripts/validate.ts`
- `docsite/sidebars.architecture.ts`
- `docsite/sidebars.features.ts`
- `docsite/sidebars.specs.ts`
- `docsite/site.json`
- `docsite/src/components/ArchitectureView.tsx`
- `docsite/src/components/ContentProvenance.tsx`
- `docsite/src/components/FeatureGraph.tsx`
- `docsite/src/components/FeatureNeighborhood.tsx`
- `docsite/src/components/FeatureRelations.tsx`
- `docsite/src/components/ScopedGraph.tsx`
- `docsite/src/css/custom.css`
- `docsite/src/pages/graph.tsx`
- `docsite/src/pages/index.tsx`
- `docsite/src/theme/DocItem/Layout/index.tsx`
- `docsite/src/theme/MDXComponents/index.tsx`
- `docsite/src/types/cytoscape-fcose.d.ts`
- `docsite/static/img/favicon.svg`
- `docsite/tests/contract/build-interface.test.ts`
- `docsite/tests/contract/build-manifest.test.ts`
- `docsite/tests/contract/content-sources.test.ts`
- `docsite/tests/contract/feature-graph.test.ts`
- `docsite/tests/fixtures/interfaces/build-manifest.example.json`
- `docsite/tests/fixtures/interfaces/build-manifest.schema.json`
- `docsite/tests/fixtures/interfaces/feature-graph.example.json`
- `docsite/tests/fixtures/interfaces/feature-graph.schema.json`
- `docsite/tests/fixtures/invalid-projects/broken-link/specs/example/architecture.md`
- `docsite/tests/fixtures/invalid-projects/duplicate-id/specs/example/architecture.md`
- `docsite/tests/fixtures/invalid-projects/duplicate-id/specs/example/features/001-one.md`
- `docsite/tests/fixtures/invalid-projects/duplicate-id/specs/example/features/002-two.md`
- `docsite/tests/fixtures/invalid-projects/feature-diagram/specs/example/architecture.md`
- `docsite/tests/fixtures/invalid-projects/feature-diagram/specs/example/features/001-diagram.md`
- `docsite/tests/fixtures/invalid-projects/legacy-control-state/specs/example/architecture.md`
- `docsite/tests/fixtures/invalid-projects/legacy-control-state/specs/example/attempts/feature.fixture.legacy-control/plan.md`
- `docsite/tests/fixtures/invalid-projects/legacy-control-state/specs/example/features/001-legacy-control.md`
- `docsite/tests/fixtures/invalid-projects/legacy-control-state/specs/example/reflections.md`
- `docsite/tests/fixtures/invalid-projects/legacy-residue/specs/example/architecture.md`
- `docsite/tests/fixtures/invalid-projects/legacy-residue/specs/example/features/001-legacy.md`
- `docsite/tests/fixtures/invalid-projects/legacy-residue/specs/example/features/001-legacy/abstract.md`
- `docsite/tests/fixtures/invalid-projects/legacy-residue/specs/example/features/001-legacy/contracts/example/contract.md`
- `docsite/tests/fixtures/invalid-projects/legacy-residue/specs/example/features/001-legacy/implementation.md`
- `docsite/tests/fixtures/invalid-projects/missing-architecture/specs/features/001-orphan.md`
- `docsite/tests/fixtures/invalid-projects/missing-feature/specs/example/architecture.md`
- `docsite/tests/fixtures/invalid-projects/missing-title/specs/example/architecture.md`
- `docsite/tests/fixtures/invalid-projects/nested-feature/specs/example/architecture.md`
- `docsite/tests/fixtures/invalid-projects/nested-feature/specs/example/features/001-parent.md`
- `docsite/tests/fixtures/invalid-projects/nested-feature/specs/example/features/001-parent/subfeatures/001-child.md`
- `docsite/tests/fixtures/invalid-projects/parallel-docs/docs/guide.md`
- `docsite/tests/fixtures/invalid-projects/route-collision/specs/one/architecture.md`
- `docsite/tests/fixtures/invalid-projects/route-collision/specs/two/architecture.md`
- `docsite/tests/fixtures/valid-project/.concorde/attempts/feature.fixture.alpha/plan.md`
- `docsite/tests/fixtures/valid-project/.concorde/config.json`
- `docsite/tests/fixtures/valid-project/.concorde/reflections/log.md`
- `docsite/tests/fixtures/valid-project/.concorde/reflections/plans/R-001.md`
- `docsite/tests/fixtures/valid-project/README.md`
- `docsite/tests/fixtures/valid-project/specs/example/architecture.md`
- `docsite/tests/fixtures/valid-project/specs/example/diagrams/fixture-level-view.json`
- `docsite/tests/fixtures/valid-project/specs/example/features/001-alpha.md`
- `docsite/tests/fixtures/valid-project/specs/example/modules/nested/architecture.md`
- `docsite/tests/fixtures/valid-project/specs/example/modules/nested/features/002-beta.md`
- `docsite/tests/integration/accessibility.test.ts`
- `docsite/tests/integration/atomic-promotion.test.ts`
- `docsite/tests/integration/diagram-delivery.test.ts`
- `docsite/tests/integration/document-authoring.test.ts`
- `docsite/tests/integration/feature-publication.test.ts`
- `docsite/tests/integration/performance.test.ts`
- `docsite/tests/integration/source-immutability.test.ts`
- `docsite/tests/repository/diagram-inventory.test.ts`
- `docsite/tests/repository/feature-graph.test.ts`
- `docsite/tests/repository/framework-guides.test.ts`
- `docsite/tests/repository/fresh-project-scaffold.test.ts`
- `docsite/tests/repository/github-pages.test.ts`
- `docsite/tests/repository/production-build.test.ts`
- `docsite/tests/scoped-registry.test.ts`
- `docsite/tests/setup.ts`
- `docsite/tests/unit/architecture-sources.test.ts`
- `docsite/tests/unit/build-freshness.test.ts`
- `docsite/tests/unit/diagram-delivery.test.ts`
- `docsite/tests/unit/feature-designs.test.ts`
- `docsite/tests/unit/graph.test.ts`
- `docsite/tests/unit/links.test.ts`
- `docsite/tests/unit/materialize-content.test.ts`
- `docsite/tests/unit/projections.test.ts`
- `docsite/tests/unit/registry.test.ts`
- `docsite/tests/unit/site-identity.test.ts`
- `docsite/tsconfig.json`
- `docsite/vitest.config.ts`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `docsite/plugins/scoped-content/model.ts` | Admits registry schema 2, publishes explicit Module and Implementation documents, and builds composition/dependency/reuse edges. |
| `docsite/plugins/scoped-content/materialize.ts` | Creates one canonical page per physical Spec and separate Module and Implementation navigation. |
| `docsite/plugins/scoped-content/index.ts` | Binds Build Manifest 16 and graph outputs to current sources before publication. |
| `docsite/src/components/ScopedGraph.tsx` | Presents Module relationships and reusable Implementation bindings to developers. |
| `docsite/scripts/` | Prepares diagrams, checks candidates and promotes a complete site while preserving the prior successful output. |

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
