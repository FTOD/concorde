import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {createManifest} from '../../plugins/concorde-content/manifest';
import {buildRegistry} from '../../plugins/concorde-content/registry';

const fixture = resolve(__dirname, '../fixtures/valid-project');
const prepareRoot = 'specs/001-alpha/subfeatures/001-prepare';
const prepareLanding = '/features/001-alpha/subfeatures/001-prepare/feature.fixture.alpha.prepare';
const finishLanding = '/features/001-alpha/subfeatures/002-finish/feature.fixture.alpha.finish';
const alphaLanding = '/features/001-alpha/feature.fixture.alpha';

describe('canonical feature publication', () => {
  it('includes permanent abstract.md, design.md, and implementation.md recursively and excludes temporal Markdown', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    expect(manifest.pages.filter((page) => page.kind === 'feature-abstract')).toHaveLength(4);
    expect(manifest.pages.filter((page) => page.kind === 'feature-implementation')).toHaveLength(4);
    expect(manifest.pages.filter((page) => page.kind === 'feature-design')).toHaveLength(4);
    expect(manifest.pages.some((page) => page.sourcePath.endsWith('/plan.md'))).toBe(false);
    expect(manifest.pages.some((page) => page.sourcePath.includes('/attempt/'))).toBe(false);
    expect(manifest.excludedSources).toEqual([
      {sourcePath: 'specs/001-alpha/attempt/contracts/draft/contract.md', reason: 'not-canonical-feature-artifact'},
      {sourcePath: 'specs/001-alpha/plan.md', reason: 'not-canonical-feature-artifact'},
      {sourcePath: 'specs/001-alpha/subfeatures/001-prepare/attempt/plan.md', reason: 'not-canonical-feature-artifact'},
    ]);
  });

  it('opens every feature on its abstract with design and implementation one link away', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    const abstract = manifest.pages.find((page) => page.sourcePath === `${prepareRoot}/abstract.md`);
    const design = manifest.pages.find((page) => page.sourcePath === `${prepareRoot}/design.md`);
    const implementation = manifest.pages.find((page) => page.sourcePath === `${prepareRoot}/implementation.md`);
    expect(abstract).toMatchObject({
      kind: 'feature-abstract',
      title: 'Prepare Alpha',
      route: prepareLanding,
      featureId: 'feature.fixture.alpha.prepare',
      moduleId: 'module.fixture',
      status: 'Ready',
      featureLevel: 'subfeature',
      parentFeatureId: 'feature.fixture.alpha',
      parentFeatureRoute: alphaLanding,
      designRoute: `/features/001-alpha/subfeatures/001-prepare/design`,
      implementationRoute: `/features/001-alpha/subfeatures/001-prepare/implementation`,
      navigation: {section: 'Features', label: 'Prepare Alpha', parentRoute: alphaLanding},
    });
    expect(design).toMatchObject({
      kind: 'feature-design',
      route: '/features/001-alpha/subfeatures/001-prepare/design',
      featureId: 'feature.fixture.alpha.prepare',
      featureLevel: 'subfeature',
      parentFeatureRoute: alphaLanding,
      abstractRoute: prepareLanding,
      implementationRoute: '/features/001-alpha/subfeatures/001-prepare/implementation',
      navigation: {section: 'Features', label: 'Design', parentRoute: alphaLanding},
    });
    expect(implementation).toMatchObject({
      kind: 'feature-implementation',
      title: 'Feature Implementation: Prepare Alpha',
      route: '/features/001-alpha/subfeatures/001-prepare/implementation',
      featureId: 'feature.fixture.alpha.prepare',
      moduleId: 'module.fixture',
      featureLevel: 'subfeature',
      parentFeatureId: 'feature.fixture.alpha',
      parentFeatureRoute: alphaLanding,
      abstractRoute: prepareLanding,
      designRoute: '/features/001-alpha/subfeatures/001-prepare/design',
      navigation: {section: 'Features', label: 'Implementation', parentRoute: alphaLanding},
    });
    for (const page of [abstract, design, implementation]) {
      expect(page?.siblings).toEqual([expect.objectContaining({featureId: 'feature.fixture.alpha.finish', route: finishLanding})]);
    }
    for (const landing of manifest.pages.filter((candidate) => candidate.kind === 'feature-abstract')) {
      const pairedDesign = manifest.pages.find((candidate) => candidate.route === landing.designRoute);
      const pairedImplementation = manifest.pages.find((candidate) => candidate.route === landing.implementationRoute);
      expect(pairedDesign).toMatchObject({kind: 'feature-design', abstractRoute: landing.route, implementationRoute: landing.implementationRoute});
      expect(pairedImplementation).toMatchObject({kind: 'feature-implementation', abstractRoute: landing.route, designRoute: landing.designRoute});
      expect(landing.links).toEqual(expect.arrayContaining([
        {targetSourcePath: pairedDesign!.sourcePath, targetRoute: landing.designRoute!},
        {targetSourcePath: pairedImplementation!.sourcePath, targetRoute: landing.implementationRoute!},
      ]));
    }
  });

  it('embeds the declared core diagram on the abstract and lists sub-features by abstract route', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    const landing = manifest.pages.find((page) => page.sourcePath === 'specs/001-alpha/abstract.md');
    expect(landing).toMatchObject({kind: 'feature-abstract', route: alphaLanding, featureLevel: 'feature', status: 'Draft'});
    expect(landing?.diagrams).toEqual([expect.objectContaining({
      source: 'specs/001-alpha/diagrams/alpha-components.json',
      role: 'core',
      kind: 'architecture',
      title: 'Alpha Components',
      route: '/architecture/fixture-alpha-components.html',
    })]);
    expect(landing?.diagrams?.[0].sourceSha256).toMatch(/^[a-f0-9]{64}$/);
    expect(landing?.subfeatures).toEqual([
      expect.objectContaining({featureId: 'feature.fixture.alpha.prepare', title: 'Prepare Alpha', route: prepareLanding}),
      expect.objectContaining({featureId: 'feature.fixture.alpha.finish', title: 'Finish Alpha', route: finishLanding}),
    ]);
    expect(landing?.parentFeatureRoute).toBeUndefined();
    expect(landing?.links).toEqual(expect.arrayContaining([
      {targetSourcePath: `${prepareRoot}/abstract.md`, targetRoute: prepareLanding},
    ]));
  });

  it('publishes the module design reference beside its module page with companion links', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    const module = manifest.pages.find((page) => page.sourcePath === 'specs/example/module.md');
    const design = manifest.pages.find((page) => page.sourcePath === 'specs/example/design.md');
    expect(module).toMatchObject({
      kind: 'architecture-source', architectureKind: 'module', architectureId: 'module.fixture',
      route: '/architecture/example/module.fixture', designReferenceRoute: '/architecture/example/design',
      architectureDiagrams: [expect.objectContaining({
        source: 'specs/example/architecture/diagrams/fixture-level-view.json', kind: 'architecture', title: 'Fixture Level View',
        route: '/architecture/fixture-level-view.html',
      })],
    });
    expect(module?.architectureDiagrams?.[0].sourceSha256).toMatch(/^[a-f0-9]{64}$/);
    expect(module?.links).toContainEqual({targetSourcePath: 'specs/example/design.md', targetRoute: '/architecture/example/design'});
    expect(module?.links).toContainEqual({
      targetSourcePath: 'specs/example/architecture/diagrams/fixture-level-view.json', targetRoute: '/architecture/fixture-level-view.html',
    });
    expect(design).toMatchObject({
      kind: 'module-design', title: 'Design Reference: Example', route: '/architecture/example/design',
      moduleId: 'module.fixture', moduleRoute: '/architecture/example/module.fixture',
      navigation: {section: 'Architecture'},
    });
    expect(design?.architectureId).toBeUndefined();
    expect(design?.abstractRoute).toBeUndefined();
  });
});
