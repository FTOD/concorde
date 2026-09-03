import {mkdir, mkdtemp, rm, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';

import {afterEach, describe, expect, it} from 'vitest';

import {createManifest} from '../../plugins/concorde-content/manifest';
import {buildRegistry} from '../../plugins/concorde-content/registry';
import type {FeatureDesign, ProjectDocument} from '../../plugins/concorde-content/types';
import {assertValidRegistry} from '../../plugins/concorde-content/validation';
import {
  architectureSidebarItems, featureSidebarItems, moduleSidebarClassName, stageFeatureDocument, stageHomepageDocument,
} from '../../scripts/materialize-content';

const fixture = resolve(__dirname, '../fixtures/valid-project');
const roots: string[] = [];
afterEach(async () => Promise.all(roots.splice(0).map((root) => rm(root, {recursive: true, force: true}))));

/** A minimal project whose architecture headings use the maintained "Architecture: <name>" convention. */
async function prefixedHeadingProject(): Promise<string> {
  const root = await mkdtemp(resolve(tmpdir(), 'concorde-module-labels-')); roots.push(root);
  await mkdir(resolve(root, 'specs/scale/modules/inner/features'), {recursive: true});
  await Promise.all([
    writeFile(resolve(root, 'README.md'), '# Scale Fixture\n'),
    writeFile(resolve(root, 'specs/scale/architecture.md'),
      '---\nid: module.scale\nkind: module\nparent: null\nmodules:\n  - module.scale.inner\nfeatures: []\n---\n# Architecture: Scale\n'),
    writeFile(resolve(root, 'specs/scale/modules/inner/architecture.md'),
      '---\nid: module.scale.inner\nkind: module\nparent: module.scale\nmodules: []\nfeatures:\n  - feature.scale.inner.one\n---\n# Architecture: Inner\n'),
    writeFile(resolve(root, 'specs/scale/modules/inner/features/001-one.md'),
      '---\nid: feature.scale.inner.one\nkind: feature\nmodule: module.scale.inner\nrelated_features: []\n---\n# Feature Design: One\n\n**Status**: Draft\n\n## Outcome\n\nOne.\n'),
  ]);
  return root;
}

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
      type: 'category', label: 'Fixture Architecture', className: 'sidebar-module',
      link: {type: 'doc', id: 'module.fixture/architecture'}, collapsed: false,
      items: [{
        type: 'category', label: 'Nested Fixture Architecture', className: 'sidebar-module',
        link: {type: 'doc', id: 'module.fixture.nested/architecture'}, collapsed: true, items: [],
      }],
    }]);
  });

  it('groups each direct feature file once under its providing module', async () => {
    const registry = await buildRegistry(fixture);
    const sidebar = featureSidebarItems(registry);
    expect(sidebar).toHaveLength(1);
    expect(sidebar[0]).toMatchObject({type: 'category', label: 'Fixture Architecture', className: moduleSidebarClassName, collapsed: false});
    expect(sidebar[0].items?.map((item) => item.label)).toEqual(['Alpha', 'Nested Fixture Architecture']);
    expect(sidebar[0].items?.[0]).toEqual({
      type: 'doc', id: 'feature.fixture.alpha', label: 'Alpha',
    });
    expect(sidebar[0].items?.[1]).toMatchObject({type: 'category', className: moduleSidebarClassName});
    expect(sidebar[0].items?.[1].items?.[0]).toEqual({
      type: 'doc', id: 'feature.fixture.beta', label: 'Beta',
    });
  });

  it('labels every module by its name without the "Architecture:" heading prefix', async () => {
    const registry = assertValidRegistry(await buildRegistry(await prefixedHeadingProject()));
    expect(architectureSidebarItems(registry)).toEqual([{
      type: 'category', label: 'Scale', className: 'sidebar-module',
      link: {type: 'doc', id: 'module.scale/architecture'}, collapsed: false,
      items: [{
        type: 'category', label: 'Inner', className: 'sidebar-module',
        link: {type: 'doc', id: 'module.scale.inner/architecture'}, collapsed: true, items: [],
      }],
    }]);
    const features = featureSidebarItems(registry);
    expect(features[0]).toMatchObject({type: 'category', label: 'Scale'});
    expect(features[0].items?.[0]).toMatchObject({type: 'category', label: 'Inner'});
    expect(features[0].items?.[0].items?.[0]).toEqual({type: 'doc', id: 'feature.scale.inner.one', label: 'One'});
    expect(createManifest(registry).pages.find((page) => page.moduleId === 'module.scale.inner')?.navigation)
      .toEqual({section: 'Architecture', label: 'Inner', parentRoute: '/architecture/module.scale'});
  });
});
