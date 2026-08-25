import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {createManifest} from '../../plugins/concorde-content/manifest';
import {buildRegistry} from '../../plugins/concorde-content/registry';
import {validateRegistry} from '../../plugins/concorde-content/validation';

const projectRoot = resolve(__dirname, '../../..');

const baseline = new Map([
  ['docs/index.md', '/docs'],
  ['docs/quick-start.md', '/docs/quick-start'],
  ['docs/framework-overview.md', '/docs/framework-overview'],
  ['docs/specification-model.md', '/docs/specification-model'],
  ['docs/project-structure.md', '/docs/project-structure'],
  ['docs/core-workflow.md', '/docs/core-workflow'],
  ['docs/commands.md', '/docs/commands'],
  ['docs/contributing/docsite.md', '/docs/contributing/docsite'],
]);

const learningGuides = [...baseline.keys()].filter(
  (sourcePath) => sourcePath !== 'docs/index.md' && sourcePath !== 'docs/contributing/docsite.md',
);

describe('maintained Concorde framework guides', () => {
  it('publishes the eight-page baseline exactly once at stable Documentation routes', async () => {
    const registry = await buildRegistry(projectRoot);
    expect(validateRegistry(registry)).toEqual([]);

    const documents = registry.documents.filter((document) => document.collectionId === 'docs');
    expect(documents).toHaveLength(baseline.size);
    expect(new Set(documents.map((document) => document.sourcePath))).toEqual(new Set(baseline.keys()));

    for (const [sourcePath, route] of baseline) {
      expect(documents.filter((document) => document.sourcePath === sourcePath)).toHaveLength(1);
      expect(documents.find((document) => document.sourcePath === sourcePath)?.route).toBe(route);
    }
  });

  it('links the landing journey to every learning guide and each guide to canonical authority', async () => {
    const manifest = createManifest(await buildRegistry(projectRoot));
    const landing = manifest.pages.find((page) => page.sourcePath === 'docs/index.md');
    if (!landing) throw new Error('Expected docs/index.md in the build manifest.');

    const landingTargets = new Set(landing.links.map((link) => link.targetSourcePath));
    for (const sourcePath of learningGuides) expect(landingTargets).toContain(sourcePath);

    for (const sourcePath of learningGuides) {
      const guide = manifest.pages.find((page) => page.sourcePath === sourcePath);
      if (!guide) throw new Error(`Expected ${sourcePath} in the build manifest.`);
      expect(guide.links.some((link) =>
        link.targetSourcePath.startsWith('specs/') &&
        (link.targetSourcePath.endsWith('/spec.md') || link.targetSourcePath.endsWith('/module.md')),
      )).toBe(true);
    }
  });

  it('does not present temporal implementation artifacts as permanent guide authority', async () => {
    const manifest = createManifest(await buildRegistry(projectRoot));
    expect(manifest.pages.some((page) => page.sourcePath.includes('/implementation/'))).toBe(false);
    expect(manifest.excludedSources.some((source) =>
      source.sourcePath === 'specs/concorde/features/002-create-project-docsite/implementation/plan.md' &&
      source.reason === 'not-canonical-feature-artifact',
    )).toBe(true);
  });
});
