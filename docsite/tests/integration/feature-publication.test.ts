import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {createManifest} from '../../plugins/concorde-content/manifest';
import {buildRegistry} from '../../plugins/concorde-content/registry';

const fixture = resolve(__dirname, '../fixtures/valid-project');

describe('single-file feature publication', () => {
  it('includes one landing page per feature and excludes its temporal attempt', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    expect(manifest.pages.filter((page) => page.kind === 'feature-design')).toHaveLength(2);
    expect(manifest.pages.some((page) => page.sourcePath.startsWith('.concorde/'))).toBe(false);
    expect(manifest.excludedSources.some((source) => source.sourcePath.startsWith('.concorde/'))).toBe(false);
    expect(manifest.excludedSources).toEqual([]);
    expect(JSON.stringify(manifest.pages)).not.toMatch(/abstractRoute|implementationRoute|designRoute|featureLevel/);
  });

  it('uses the single design as the feature landing page with module and relation links', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    expect(manifest.pages.find((page) => page.featureId === 'feature.fixture.alpha')).toMatchObject({
      kind: 'feature-design', sourcePath: 'specs/example/features/001-alpha.md',
      route: '/features/feature.fixture.alpha', moduleId: 'module.fixture',
      moduleRoute: '/architecture/module.fixture', status: 'Draft',
      relatedFeatures: [expect.objectContaining({
        featureId: 'feature.fixture.beta', route: '/features/feature.fixture.beta',
      })],
    });
  });

  it('publishes every module architecture as its module landing page', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    expect(manifest.pages.find((page) => page.moduleId === 'module.fixture' && page.kind === 'module-architecture'))
      .toMatchObject({
        sourcePath: 'specs/example/architecture.md', route: '/architecture/module.fixture',
        architectureDiagrams: [expect.objectContaining({
          source: 'specs/example/diagrams/fixture-level-view.json',
          route: '/architecture/fixture-level-view.html',
        })],
      });
    expect(manifest.pages.find((page) => page.moduleId === 'module.fixture.nested' && page.kind === 'module-architecture'))
      .toMatchObject({
        sourcePath: 'specs/example/modules/nested/architecture.md',
        route: '/architecture/module.fixture.nested', parentId: 'module.fixture',
      });
  });
});
