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
      'architecture', 'docs', 'feature-tldrs', 'features', 'feature-designs',
    ]);
    expect(registry.documents.map((item) => item.sourcePath)).toEqual([
      'docs/guide/intro.md', 'docs/index.md',
      'specs/001-alpha/design.md',
      'specs/001-alpha/spec.md',
      'specs/001-alpha/subfeatures/001-prepare/design.md',
      'specs/001-alpha/subfeatures/001-prepare/spec.md',
      'specs/001-alpha/subfeatures/001-prepare/tldr.md',
      'specs/001-alpha/subfeatures/002-finish/design.md',
      'specs/001-alpha/subfeatures/002-finish/spec.md',
      'specs/001-alpha/subfeatures/002-finish/tldr.md',
      'specs/001-alpha/tldr.md',
      'specs/example/design.md',
      'specs/example/module.md',
      'specs/nested/002-beta/design.md', 'specs/nested/002-beta/spec.md', 'specs/nested/002-beta/tldr.md',
    ]);
    expect(new Set(registry.documents.map((item) => item.route)).size).toBe(16);
    expect(registry.documents.every((item) => item.sourceSha256.length === 64)).toBe(true);
  });

  it('classifies design.md by its sibling: module.md means module design, spec.md means feature design', async () => {
    const registry = await buildRegistry(fixture);
    expect(registry.documents.find((item) => item.sourcePath === 'specs/example/design.md')).toMatchObject({
      collectionId: 'architecture', contentKind: 'module-design', route: '/architecture/example/design',
    });
    expect(registry.documents.find((item) => item.sourcePath === 'specs/001-alpha/design.md')).toMatchObject({
      collectionId: 'feature-designs', contentKind: 'feature-design', route: '/features/001-alpha/design',
      title: 'Feature Design Reference: Alpha',
    });
    expect(registry.excludedSources.map((item) => item.sourcePath)).not.toContain('specs/001-alpha/design.md');
  });

  it('opens each feature on its TL;DR and places the specification and design one segment below', async () => {
    const registry = await buildRegistry(fixture);
    const byPath = (sourcePath: string) => registry.documents.find((item) => item.sourcePath === sourcePath)!;
    expect(byPath('specs/001-alpha/tldr.md')).toMatchObject({
      collectionId: 'feature-tldrs', contentKind: 'feature-tldr', title: 'Alpha',
      route: '/features/001-alpha/feature.fixture.alpha',
    });
    expect(byPath('specs/001-alpha/spec.md').route).toBe('/features/001-alpha/spec');
    expect(byPath('specs/001-alpha/design.md').route).toBe('/features/001-alpha/design');
    expect(byPath('specs/001-alpha/subfeatures/001-prepare/tldr.md').route)
      .toBe('/features/001-alpha/subfeatures/001-prepare/feature.fixture.alpha.prepare');
  });

  it('projects exactly one navigation record per included page', async () => {
    const registry = await buildRegistry(fixture);
    const manifest = createManifest(registry);
    expect(manifest.pages).toHaveLength(registry.documents.length);
    expect(manifest.pages.map((page) => page.navigation.section)).toEqual([
      'Documentation', 'Documentation',
      'Features', 'Features', 'Features', 'Features', 'Features', 'Features', 'Features', 'Features', 'Features',
      'Architecture', 'Architecture',
      'Features', 'Features', 'Features',
    ]);
    const design = manifest.pages.find((page) => page.sourcePath === 'specs/example/design.md');
    expect(design?.navigation).toEqual({
      section: 'Architecture', label: 'Design Reference: Example', parentRoute: '/architecture/example/module.fixture',
    });
    const byPath = (sourcePath: string) => manifest.pages.find((page) => page.sourcePath === sourcePath)?.navigation;
    expect(byPath('specs/001-alpha/tldr.md')).toEqual({section: 'Features', label: 'Alpha'});
    expect(byPath('specs/001-alpha/spec.md')).toEqual({section: 'Features', label: 'Specification'});
    expect(byPath('specs/001-alpha/design.md')).toEqual({section: 'Features', label: 'Design reference'});
    for (const name of ['tldr', 'spec', 'design']) {
      expect(byPath(`specs/001-alpha/subfeatures/001-prepare/${name}.md`)?.parentRoute).toBe('/features/001-alpha/feature.fixture.alpha');
    }
  });
});
