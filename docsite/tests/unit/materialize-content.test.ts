import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {buildRegistry} from '../../plugins/concorde-content/registry';
import type {FeatureDesign, ProjectDocument} from '../../plugins/concorde-content/types';
import {featureCategoryMetadata, featureCategoryPath, stageHomepageDocument} from '../../scripts/materialize-content';

describe('homepage materialization', () => {
  it('adds disposable root-route metadata without changing the maintained README body', async () => {
    const registry = await buildRegistry(resolve(__dirname, '../fixtures/valid-project'));
    const homepage = registry.documents.find((item): item is ProjectDocument => item.collectionId === 'home')!;
    const staged = stageHomepageDocument(homepage);
    expect(staged).toContain('slug: /');
    expect(staged).toContain('# Fixture Project');
    expect(staged).toContain(homepage.content.trim());
    expect(homepage.frontMatter.slug).toBeUndefined();
  });
});

describe('feature content materialization', () => {
  it('derives human-readable categories from the semantic feature tree', async () => {
    const registry = await buildRegistry(resolve(__dirname, '../fixtures/valid-project'));
    const features = registry.documents.filter((item): item is FeatureDesign => item.collectionId === 'features');
    const parent = features.find((item) => item.featureId === 'feature.fixture.alpha')!;
    const child = features.find((item) => item.featureId === 'feature.fixture.alpha.prepare')!;
    const nestedSource = features.find((item) => item.featureId === 'feature.fixture.beta')!;

    expect(featureCategoryPath(parent)).toBe('feature.fixture.alpha/_category_.json');
    expect(featureCategoryMetadata(parent)).toEqual({
      label: 'Alpha',
      link: {type: 'doc', id: 'feature.fixture.alpha/abstract'},
    });
    expect(featureCategoryPath(child)).toBe('feature.fixture.alpha/feature.fixture.alpha.prepare/_category_.json');
    expect(featureCategoryMetadata(child).link.id)
      .toBe('feature.fixture.alpha/feature.fixture.alpha.prepare/abstract');
    expect(featureCategoryPath(nestedSource)).toBe('feature.fixture.beta/_category_.json');
    expect(features.map((item) => item.stagedPath).join('\n')).not.toMatch(/(?:^|\/)modules\//);
    expect(features.map((item) => item.stagedPath).join('\n')).not.toMatch(/(?:^|\/)architecture\//);
  });
});
