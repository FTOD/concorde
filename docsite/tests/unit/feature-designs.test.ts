import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {buildRegistry} from '../../plugins/concorde-content/registry';
import type {FeatureDesign} from '../../plugins/concorde-content/types';
import {validateRegistry} from '../../plugins/concorde-content/validation';

const fixtures = resolve(__dirname, '../fixtures');

describe('single-file feature publication', () => {
  it('extracts stable identity, owner, outcome, and direct source path', async () => {
    const registry = await buildRegistry(resolve(fixtures, 'valid-project'));
    const features = registry.documents.filter((item): item is FeatureDesign => item.collectionId === 'features');
    expect(features.map((item) => [item.featureId, item.moduleId, item.sourcePath])).toEqual([
      ['feature.fixture.alpha', 'module.fixture', 'specs/example/features/001-alpha.md'],
      ['feature.fixture.beta', 'module.fixture.nested', 'specs/example/modules/nested/features/002-beta.md'],
    ]);
    expect(features.some((item) => 'status' in item || 'evidenceStatus' in item)).toBe(false);
    expect(features.map((item) => item.route)).toEqual([
      '/features/feature.fixture.alpha', '/features/feature.fixture.beta',
    ]);
  });

  it('resolves related_features as flat cross-links rather than containment', async () => {
    const registry = await buildRegistry(resolve(fixtures, 'valid-project'));
    const features = registry.documents.filter((item): item is FeatureDesign => item.collectionId === 'features');
    expect(features[0].relatedFeatures).toEqual([{
      featureId: 'feature.fixture.beta', title: 'Beta', outcome: 'Beta links to the root architecture.',
      route: '/features/feature.fixture.beta', relation: 'relates_to',
    }]);
    expect(features[1].relatedFeatures[0].featureId).toBe('feature.fixture.alpha');
    expect(features[1].relatedFeatures[0].relation).toBe('relates_to');
    expect(JSON.stringify(features)).not.toMatch(/parentFeature|subfeatures|siblings|refinements/);
  });

  it('rejects duplicate IDs, nested features, and feature-owned diagrams deterministically', async () => {
    const duplicate = await buildRegistry(resolve(fixtures, 'invalid-projects/duplicate-id'));
    expect(validateRegistry(duplicate).filter((item) => item.ruleId === 'feature.id.duplicate')).toHaveLength(2);

    const nested = await buildRegistry(resolve(fixtures, 'invalid-projects/nested-feature'));
    expect(validateRegistry(nested).map((item) => item.ruleId)).toContain('feature.hierarchy.forbidden');

    const diagram = await buildRegistry(resolve(fixtures, 'invalid-projects/feature-diagram'));
    expect(validateRegistry(diagram).map((item) => item.ruleId)).toContain('feature.diagram.forbidden');
  });
});
