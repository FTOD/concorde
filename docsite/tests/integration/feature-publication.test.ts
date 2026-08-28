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
  it('includes permanent tldr.md, spec.md, and design.md recursively and excludes temporal Markdown', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    expect(manifest.pages.filter((page) => page.kind === 'feature-tldr')).toHaveLength(4);
    expect(manifest.pages.filter((page) => page.kind === 'feature-specification')).toHaveLength(4);
    expect(manifest.pages.filter((page) => page.kind === 'feature-design')).toHaveLength(4);
    expect(manifest.pages.some((page) => page.sourcePath.endsWith('/plan.md'))).toBe(false);
    expect(manifest.pages.some((page) => page.sourcePath.includes('/implementation/'))).toBe(false);
    expect(manifest.excludedSources).toEqual([
      {sourcePath: 'specs/001-alpha/implementation/contracts/draft/contract.md', reason: 'not-canonical-feature-artifact'},
      {sourcePath: 'specs/001-alpha/plan.md', reason: 'not-canonical-feature-artifact'},
      {sourcePath: 'specs/001-alpha/subfeatures/001-prepare/implementation/plan.md', reason: 'not-canonical-feature-artifact'},
    ]);
  });

  it('opens every feature on its TL;DR with the specification and design reference one link away', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    const tldr = manifest.pages.find((page) => page.sourcePath === `${prepareRoot}/tldr.md`);
    const specification = manifest.pages.find((page) => page.sourcePath === `${prepareRoot}/spec.md`);
    const design = manifest.pages.find((page) => page.sourcePath === `${prepareRoot}/design.md`);
    expect(tldr).toMatchObject({
      kind: 'feature-tldr',
      title: 'Prepare Alpha',
      route: prepareLanding,
      featureId: 'feature.fixture.alpha.prepare',
      moduleId: 'module.fixture',
      status: 'Ready',
      featureLevel: 'subfeature',
      parentFeatureId: 'feature.fixture.alpha',
      parentFeatureRoute: alphaLanding,
      specificationRoute: `/features/001-alpha/subfeatures/001-prepare/spec`,
      designRoute: `/features/001-alpha/subfeatures/001-prepare/design`,
      navigation: {section: 'Features', label: 'Prepare Alpha', parentRoute: alphaLanding},
    });
    expect(specification).toMatchObject({
      kind: 'feature-specification',
      route: '/features/001-alpha/subfeatures/001-prepare/spec',
      featureId: 'feature.fixture.alpha.prepare',
      featureLevel: 'subfeature',
      parentFeatureRoute: alphaLanding,
      tldrRoute: prepareLanding,
      designRoute: '/features/001-alpha/subfeatures/001-prepare/design',
      navigation: {section: 'Features', label: 'Specification', parentRoute: alphaLanding},
    });
    expect(design).toMatchObject({
      kind: 'feature-design',
      title: 'Feature Design Reference: Prepare Alpha',
      route: '/features/001-alpha/subfeatures/001-prepare/design',
      featureId: 'feature.fixture.alpha.prepare',
      moduleId: 'module.fixture',
      featureLevel: 'subfeature',
      parentFeatureId: 'feature.fixture.alpha',
      parentFeatureRoute: alphaLanding,
      tldrRoute: prepareLanding,
      specificationRoute: '/features/001-alpha/subfeatures/001-prepare/spec',
      navigation: {section: 'Features', label: 'Design reference', parentRoute: alphaLanding},
    });
    for (const page of [tldr, specification, design]) {
      expect(page?.siblings).toEqual([expect.objectContaining({featureId: 'feature.fixture.alpha.finish', route: finishLanding})]);
    }
    for (const landing of manifest.pages.filter((candidate) => candidate.kind === 'feature-tldr')) {
      const pairedSpecification = manifest.pages.find((candidate) => candidate.route === landing.specificationRoute);
      const pairedDesign = manifest.pages.find((candidate) => candidate.route === landing.designRoute);
      expect(pairedSpecification).toMatchObject({kind: 'feature-specification', tldrRoute: landing.route, designRoute: landing.designRoute});
      expect(pairedDesign).toMatchObject({kind: 'feature-design', tldrRoute: landing.route, specificationRoute: landing.specificationRoute});
      expect(landing.links).toEqual(expect.arrayContaining([
        {targetSourcePath: pairedSpecification!.sourcePath, targetRoute: landing.specificationRoute!},
        {targetSourcePath: pairedDesign!.sourcePath, targetRoute: landing.designRoute!},
      ]));
    }
  });

  it('embeds the declared core diagram on the TL;DR landing page and lists sub-features by TL;DR route', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    const landing = manifest.pages.find((page) => page.sourcePath === 'specs/001-alpha/tldr.md');
    expect(landing).toMatchObject({kind: 'feature-tldr', route: alphaLanding, featureLevel: 'feature', status: 'Draft'});
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
      {targetSourcePath: `${prepareRoot}/tldr.md`, targetRoute: prepareLanding},
    ]));
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
    expect(design?.tldrRoute).toBeUndefined();
  });
});
