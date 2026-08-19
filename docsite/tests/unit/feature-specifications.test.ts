import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {buildRegistry} from '../../plugins/concorde-content/registry';
import type {FeatureSpecification} from '../../plugins/concorde-content/types';
import {validateRegistry} from '../../plugins/concorde-content/validation';

describe('feature specifications', () => {
  it('extracts stable identity, owner, lifecycle status, and nested directory', async () => {
    const registry = await buildRegistry(resolve(__dirname, '../fixtures/valid-project'));
    const features = registry.documents.filter((item): item is FeatureSpecification => item.collectionId === 'features');
    expect(features.map((item) => [item.featureId, item.moduleId, item.status, item.featureDirectory])).toEqual([
      ['feature.fixture.alpha', 'module.fixture', 'Draft', 'specs/001-alpha'],
      ['feature.fixture.beta', 'module.fixture', 'Approved', 'specs/nested/002-beta'],
    ]);
  });

  it('rejects duplicate feature IDs deterministically', async () => {
    const registry = await buildRegistry(resolve(__dirname, '../fixtures/invalid-projects/duplicate-id'));
    expect(validateRegistry(registry).map((finding) => finding.ruleId)).toEqual([
      'feature.id.duplicate', 'feature.id.duplicate',
    ]);
  });
});
