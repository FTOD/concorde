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
      ['feature.fixture.alpha.prepare', 'module.fixture', 'Ready', 'specs/001-alpha/subfeatures/001-prepare'],
      ['feature.fixture.alpha.finish', 'module.fixture', 'Planned', 'specs/001-alpha/subfeatures/002-finish'],
      ['feature.fixture.beta', 'module.fixture', 'Approved', 'specs/nested/002-beta'],
    ]);
    expect(features.map((item) => item.route)).toEqual([
      '/features/001-alpha/spec',
      '/features/001-alpha/subfeatures/001-prepare/spec',
      '/features/001-alpha/subfeatures/002-finish/spec',
      '/features/nested/002-beta/spec',
    ]);
    const parent = features[0];
    expect(parent.landingRoute).toBe('/features/001-alpha/feature.fixture.alpha');
    expect(parent.tldrRoute).toBe(parent.landingRoute);
    expect(parent.designRoute).toBe('/features/001-alpha/design');
    expect(parent.subfeatures.map((item) => item.featureId)).toEqual([
      'feature.fixture.alpha.prepare', 'feature.fixture.alpha.finish',
    ]);
    expect(features[1].parentFeatureRoute).toBe(parent.landingRoute);
    expect(features[1].siblings.map((item) => item.featureId)).toEqual(['feature.fixture.alpha.finish']);
  });

  it('points parent, sub-feature, and sibling navigation at TL;DR landing routes', async () => {
    const registry = await buildRegistry(resolve(__dirname, '../fixtures/valid-project'));
    const features = registry.documents.filter((item): item is FeatureSpecification => item.collectionId === 'features');
    expect(features[0].subfeatures.map((item) => item.route)).toEqual([
      '/features/001-alpha/subfeatures/001-prepare/feature.fixture.alpha.prepare',
      '/features/001-alpha/subfeatures/002-finish/feature.fixture.alpha.finish',
    ]);
    expect(features[1].siblings.map((item) => item.route)).toEqual([
      '/features/001-alpha/subfeatures/002-finish/feature.fixture.alpha.finish',
    ]);
    expect(features[0].subfeatures.map((item) => [item.title, item.outcome, item.status])).toEqual([
      ['Prepare Alpha', 'Alpha inputs are prepared.', 'Ready'],
      ['Finish Alpha', 'Alpha produces its final result.', 'Planned'],
    ]);
  });

  it('rejects duplicate feature IDs deterministically', async () => {
    const registry = await buildRegistry(resolve(__dirname, '../fixtures/invalid-projects/duplicate-id'));
    expect(validateRegistry(registry).map((finding) => finding.ruleId)).toEqual([
      'feature.id.duplicate', 'feature.id.duplicate',
    ]);
  });

  it('rejects disagreeing parent and child registration', async () => {
    const registry = await buildRegistry(resolve(__dirname, '../fixtures/invalid-projects/subfeature-registration'));
    expect(validateRegistry(registry).map((finding) => finding.ruleId)).toContain('feature.containment.registration');
  });

  it('maps declared feature diagrams without requiring delivered HTML', async () => {
    const registry = await buildRegistry(resolve(__dirname, '../../..'));
    const features = registry.documents.filter((item): item is FeatureSpecification => item.collectionId === 'features');
    const diagrams = features.flatMap((feature) => feature.diagrams);
    expect(diagrams).toHaveLength(5);
    expect(diagrams.find((diagram) => diagram.source.includes('project-docsite-publication-flow'))).toMatchObject({
      kind: 'sequence',
      role: 'supplemental',
      route: '/architecture/project-docsite-publication-flow.html',
    });
  });
});
