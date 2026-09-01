import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {createManifest} from '../../plugins/concorde-content/manifest';
import {buildRegistry} from '../../plugins/concorde-content/registry';
import {validateRegistry} from '../../plugins/concorde-content/validation';

const fixture = resolve(__dirname, '../fixtures/valid-project');

describe('Profile 7 content registry', () => {
  it('discovers four source collections and one page per durable authority', async () => {
    const registry = await buildRegistry(fixture);
    expect(validateRegistry(registry)).toEqual([]);
    expect(registry.collections.map((collection) => collection.id)).toEqual([
      'home', 'architecture', 'docs', 'features',
    ]);
    expect(registry.documents.map((item) => item.sourcePath)).toEqual([
      'README.md',
      'docs/guide/intro.md',
      'docs/index.md',
      'specs/example/architecture.md',
      'specs/example/features/001-alpha.md',
      'specs/example/modules/nested/architecture.md',
      'specs/example/modules/nested/features/002-beta.md',
    ]);
    expect(new Set(registry.documents.map((item) => item.route)).size).toBe(7);
    expect(registry.documents.every((item) => item.sourceSha256.length === 64)).toBe(true);
    expect(registry.documents.some((item) => item.sourcePath.startsWith('.concorde/'))).toBe(false);
    expect(registry.excludedSources).toEqual([]);
  });

  it('maps architecture.md and direct feature files to stable identity routes', async () => {
    const registry = await buildRegistry(fixture);
    const byPath = (sourcePath: string) => registry.documents.find((item) => item.sourcePath === sourcePath);
    expect(byPath('specs/example/architecture.md')).toMatchObject({
      collectionId: 'architecture', contentKind: 'module-architecture',
      moduleId: 'module.fixture', route: '/architecture/module.fixture',
      stagedPath: 'module.fixture/architecture.md',
    });
    expect(byPath('specs/example/features/001-alpha.md')).toMatchObject({
      collectionId: 'features', contentKind: 'feature-design', featureId: 'feature.fixture.alpha',
      route: '/features/feature.fixture.alpha', stagedPath: 'feature.fixture.alpha.md',
      title: 'Alpha',
    });
    expect(byPath('specs/example/modules/nested/architecture.md')).toMatchObject({
      moduleId: 'module.fixture.nested', parentId: 'module.fixture',
      route: '/architecture/module.fixture.nested',
    });
  });

  it('projects exactly one navigation and provenance record per included source', async () => {
    const registry = await buildRegistry(fixture);
    const manifest = createManifest(registry);
    expect(manifest.pages).toHaveLength(registry.documents.length);
    expect(manifest.pages.map((page) => page.kind).sort()).toEqual([
      'feature-design', 'feature-design', 'module-architecture', 'module-architecture',
      'project-document', 'project-document', 'project-document',
    ]);
    expect(manifest.pages.find((page) => page.sourcePath === 'specs/example/modules/nested/architecture.md')?.navigation)
      .toEqual({section: 'Architecture', label: 'Nested Fixture Architecture', parentRoute: '/architecture/module.fixture'});
    expect(manifest.pages.find((page) => page.sourcePath === 'specs/example/features/001-alpha.md')?.navigation)
      .toEqual({section: 'Features', label: 'Alpha'});
  });
});
