import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {buildRegistry} from '../../plugins/concorde-content/registry';
import type {FeatureDesign, ProjectDocument} from '../../plugins/concorde-content/types';
import {
  architectureSidebarItems, featureSidebarItems, stageFeatureDocument, stageHomepageDocument,
} from '../../scripts/materialize-content';

const fixture = resolve(__dirname, '../fixtures/valid-project');

describe('content materialization', () => {
  it('adds renderer-only route metadata without changing canonical bodies', async () => {
    const registry = await buildRegistry(fixture);
    const homepage = registry.documents.find((item): item is ProjectDocument => item.collectionId === 'home')!;
    const feature = registry.documents.find((item): item is FeatureDesign => item.collectionId === 'features')!;
    expect(stageHomepageDocument(homepage)).toContain('slug: /');
    const staged = stageFeatureDocument(feature);
    expect(staged).toContain('slug: /feature.fixture.alpha');
    expect(staged).toContain(feature.content.trim());
    expect(feature.frontMatter.slug).toBeUndefined();
  });

  it('builds architecture navigation from module containment', async () => {
    const registry = await buildRegistry(fixture);
    expect(architectureSidebarItems(registry)).toEqual([{
      type: 'category', label: 'Fixture Architecture',
      link: {type: 'doc', id: 'module.fixture/architecture'}, collapsed: false,
      items: [{
        type: 'category', label: 'Nested Fixture Architecture',
        link: {type: 'doc', id: 'module.fixture.nested/architecture'}, collapsed: true, items: [],
      }],
    }]);
  });

  it('groups each direct feature file once under its providing module', async () => {
    const registry = await buildRegistry(fixture);
    const sidebar = featureSidebarItems(registry);
    expect(sidebar).toHaveLength(1);
    expect(sidebar[0]).toMatchObject({type: 'category', label: 'Fixture Architecture', collapsed: false});
    expect(sidebar[0].items?.map((item) => item.label)).toEqual(['Alpha', 'Nested Fixture Architecture']);
    expect(sidebar[0].items?.[0]).toEqual({
      type: 'doc', id: 'feature.fixture.alpha', label: 'Alpha',
    });
    expect(sidebar[0].items?.[1].items?.[0]).toEqual({
      type: 'doc', id: 'feature.fixture.beta', label: 'Beta',
    });
  });
});
