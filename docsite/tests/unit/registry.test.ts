import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {createManifest} from '../../plugins/concorde-content/manifest';
import {buildRegistry} from '../../plugins/concorde-content/registry';
import {validateRegistry} from '../../plugins/concorde-content/validation';

const fixture = resolve(__dirname, '../fixtures/valid-project');

describe('content registry', () => {
  it('discovers all five collections with unique routes and stable source ordering', async () => {
    const registry = await buildRegistry(fixture);
    expect(validateRegistry(registry)).toEqual([]);
    expect(registry.collections.map((collection) => collection.id)).toEqual([
      'architecture', 'docs', 'feature-abstracts', 'features', 'feature-implementations',
    ]);
    expect(registry.documents.map((item) => item.sourcePath)).toEqual([
      'docs/guide/intro.md', 'docs/index.md',
      'specs/001-alpha/abstract.md',
      'specs/001-alpha/design.md',
      'specs/001-alpha/implementation.md',
      'specs/001-alpha/subfeatures/001-prepare/abstract.md',
      'specs/001-alpha/subfeatures/001-prepare/design.md',
      'specs/001-alpha/subfeatures/001-prepare/implementation.md',
      'specs/001-alpha/subfeatures/002-finish/abstract.md',
      'specs/001-alpha/subfeatures/002-finish/design.md',
      'specs/001-alpha/subfeatures/002-finish/implementation.md',
      'specs/example/architecture/modules/nested/features/002-beta/abstract.md',
      'specs/example/architecture/modules/nested/features/002-beta/design.md',
      'specs/example/architecture/modules/nested/features/002-beta/implementation.md',
      'specs/example/design.md',
      'specs/example/module.md',
    ]);
    expect(new Set(registry.documents.map((item) => item.route)).size).toBe(16);
    expect(registry.documents.every((item) => item.sourceSha256.length === 64)).toBe(true);
  });

  it('classifies module design, feature design, and feature implementation separately', async () => {
    const registry = await buildRegistry(fixture);
    expect(registry.documents.find((item) => item.sourcePath === 'specs/example/design.md')).toMatchObject({
      collectionId: 'architecture', contentKind: 'module-design', route: '/architecture/example/design',
    });
    expect(registry.documents.find((item) => item.sourcePath === 'specs/001-alpha/design.md')).toMatchObject({
      collectionId: 'features', contentKind: 'feature-design', route: '/features/feature.fixture.alpha/design',
      stagedPath: 'feature.fixture.alpha/design.md',
      title: 'Alpha',
    });
    expect(registry.documents.find((item) => item.sourcePath === 'specs/001-alpha/implementation.md')).toMatchObject({
      collectionId: 'feature-implementations', contentKind: 'feature-implementation', route: '/features/feature.fixture.alpha/implementation',
      stagedPath: 'feature.fixture.alpha/implementation.md',
      title: 'Feature Implementation: Alpha',
    });
  });

  it('opens each feature on its abstract and places design and implementation below', async () => {
    const registry = await buildRegistry(fixture);
    const byPath = (sourcePath: string) => registry.documents.find((item) => item.sourcePath === sourcePath)!;
    expect(byPath('specs/001-alpha/abstract.md')).toMatchObject({
      collectionId: 'feature-abstracts', contentKind: 'feature-abstract', title: 'Alpha',
      route: '/features/feature.fixture.alpha', stagedPath: 'feature.fixture.alpha/abstract.md',
    });
    expect(byPath('specs/001-alpha/design.md').route).toBe('/features/feature.fixture.alpha/design');
    expect(byPath('specs/001-alpha/implementation.md').route).toBe('/features/feature.fixture.alpha/implementation');
    expect(byPath('specs/001-alpha/subfeatures/001-prepare/abstract.md').route)
      .toBe('/features/feature.fixture.alpha/feature.fixture.alpha.prepare');
    expect(byPath('specs/example/architecture/modules/nested/features/002-beta/abstract.md')).toMatchObject({
      route: '/features/feature.fixture.beta', stagedPath: 'feature.fixture.beta/abstract.md',
    });
  });

  it('projects exactly one navigation record per included page', async () => {
    const registry = await buildRegistry(fixture);
    const manifest = createManifest(registry);
    expect(manifest.pages).toHaveLength(registry.documents.length);
    expect(manifest.pages.map((page) => page.navigation.section)).toEqual([
      'Documentation', 'Documentation',
      'Features', 'Features', 'Features', 'Features', 'Features', 'Features', 'Features', 'Features', 'Features',
      'Features', 'Features', 'Features',
      'Architecture', 'Architecture',
    ]);
    const design = manifest.pages.find((page) => page.sourcePath === 'specs/example/design.md');
    expect(design?.navigation).toEqual({
      section: 'Architecture', label: 'Design Reference: Example', parentRoute: '/architecture/example/module.fixture',
    });
    const byPath = (sourcePath: string) => manifest.pages.find((page) => page.sourcePath === sourcePath)?.navigation;
    expect(byPath('specs/001-alpha/abstract.md')).toEqual({section: 'Features', label: 'Alpha'});
    expect(byPath('specs/001-alpha/design.md')).toEqual({section: 'Features', label: 'Design'});
    expect(byPath('specs/001-alpha/implementation.md')).toEqual({section: 'Features', label: 'Implementation'});
    for (const name of ['abstract', 'design', 'implementation']) {
      expect(byPath(`specs/001-alpha/subfeatures/001-prepare/${name}.md`)?.parentRoute).toBe('/features/feature.fixture.alpha');
    }
  });
});
