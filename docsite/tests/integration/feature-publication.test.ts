import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {createManifest} from '../../plugins/concorde-content/manifest';
import {buildRegistry} from '../../plugins/concorde-content/registry';

const fixture = resolve(__dirname, '../fixtures/valid-project');

describe('canonical feature publication', () => {
  it('includes permanent spec.md and implementation.md recursively and excludes temporal Markdown', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    expect(manifest.pages.filter((page) => page.kind === 'feature-specification')).toHaveLength(4);
    expect(manifest.pages.filter((page) => page.kind === 'feature-implementation')).toHaveLength(4);
    expect(manifest.pages.some((page) => page.sourcePath.endsWith('/plan.md'))).toBe(false);
    expect(manifest.pages.some((page) => page.sourcePath.includes('/implementation/'))).toBe(false);
    expect(manifest.excludedSources).toEqual([
      {sourcePath: 'specs/001-alpha/implementation/contracts/draft/contract.md', reason: 'not-canonical-feature-artifact'},
      {sourcePath: 'specs/001-alpha/plan.md', reason: 'not-canonical-feature-artifact'},
      {sourcePath: 'specs/001-alpha/subfeatures/001-prepare/implementation/plan.md', reason: 'not-canonical-feature-artifact'},
    ]);
  });

  it('pairs every specification with its accepted realization in both directions', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    const specification = manifest.pages.find((page) => page.sourcePath === 'specs/001-alpha/subfeatures/001-prepare/spec.md');
    const implementation = manifest.pages.find(
      (page) => page.sourcePath === 'specs/001-alpha/subfeatures/001-prepare/implementation.md',
    );
    expect(specification?.implementationRoute).toBe('/features/001-alpha/subfeatures/001-prepare/implementation');
    expect(implementation).toMatchObject({
      kind: 'feature-implementation',
      title: 'Feature Implementation: Prepare Alpha',
      featureId: 'feature.fixture.alpha.prepare',
      moduleId: 'module.fixture',
      featureLevel: 'subfeature',
      parentFeatureId: 'feature.fixture.alpha',
      parentFeatureRoute: '/features/001-alpha/feature.fixture.alpha',
      specificationRoute: '/features/001-alpha/subfeatures/001-prepare/feature.fixture.alpha.prepare',
      navigation: {section: 'Features', parentRoute: '/features/001-alpha/feature.fixture.alpha'},
    });
    expect(implementation?.siblings?.map((sibling) => sibling.featureId)).toEqual(['feature.fixture.alpha.finish']);
    for (const page of manifest.pages.filter((candidate) => candidate.kind === 'feature-specification')) {
      const companion = manifest.pages.find((candidate) => candidate.route === page.implementationRoute);
      expect(companion?.kind).toBe('feature-implementation');
      expect(companion?.specificationRoute).toBe(page.route);
    }
  });

  it('publishes the module design reference beside its module page with companion links', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    const module = manifest.pages.find((page) => page.sourcePath === 'specs/example/module.md');
    const design = manifest.pages.find((page) => page.sourcePath === 'specs/example/design.md');
    expect(module).toMatchObject({
      kind: 'architecture-source', architectureKind: 'module', architectureId: 'module.fixture',
      route: '/architecture/example/module.fixture', designReferenceRoute: '/architecture/example/design',
    });
    expect(module?.links).toContainEqual({targetSourcePath: 'specs/example/design.md', targetRoute: '/architecture/example/design'});
    expect(design).toMatchObject({
      kind: 'module-design', title: 'Design Reference: Example', route: '/architecture/example/design',
      moduleId: 'module.fixture', moduleRoute: '/architecture/example/module.fixture',
      navigation: {section: 'Architecture'},
    });
    expect(design?.architectureId).toBeUndefined();
  });
});
