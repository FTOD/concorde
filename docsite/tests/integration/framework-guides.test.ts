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
  ['docs/ontology.md', '/docs/ontology'],
  ['docs/specification-model.md', '/docs/specification-model'],
  ['docs/project-structure.md', '/docs/project-structure'],
  ['docs/concorde-workflow.md', '/docs/concorde-workflow'],
  ['docs/self-hosting.md', '/docs/self-hosting'],
  ['docs/commands.md', '/docs/commands'],
  ['docs/releasing.md', '/docs/releasing'],
  ['docs/contributing/docsite.md', '/docs/contributing/docsite'],
]);

const learningGuides = [...baseline.keys()].filter(
  (sourcePath) => sourcePath !== 'docs/index.md' && sourcePath !== 'docs/contributing/docsite.md',
);

describe('maintained Concorde framework guides', () => {
  it('opens the shared README with the module model and complete workflow before installation', async () => {
    const registry = await buildRegistry(projectRoot);
    const readme = registry.documents.find((document) => document.sourcePath === 'README.md');
    if (!readme) throw new Error('Expected root README.md in the content registry.');
    const model = readme.content.indexOf('## The model');
    const workflow = readme.content.indexOf('## Workflow');
    const install = readme.content.indexOf('## Install');
    expect(model).toBeGreaterThan(-1);
    expect(workflow).toBeGreaterThan(model);
    expect(install).toBeGreaterThan(workflow);
    for (const command of ['init', 'context', 'ask', 'validate', 'deliver']) {
      expect(readme.content).toContain(`$speckit-concorde-${command}`);
    }
    expect(readme.links.some((link) => link.targetSourcePath === 'docs/commands.md')).toBe(true);
    const homepageTargets = new Set(readme.links.map((link) => link.targetRoute));
    for (const route of ['/architecture/module.concorde', '/docs/ontology', '/docs/concorde-workflow']) {
      expect(homepageTargets).toContain(route);
    }
  });

  it('publishes the eleven-page baseline exactly once at stable Documentation routes', async () => {
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

  it('links the landing journey to every learning guide and collectively explains each authority', async () => {
    const manifest = createManifest(await buildRegistry(projectRoot));
    const landing = manifest.pages.find((page) => page.sourcePath === 'docs/index.md');
    if (!landing) throw new Error('Expected docs/index.md in the build manifest.');

    const landingTargets = new Set(landing.links.map((link) => link.targetSourcePath));
    for (const sourcePath of learningGuides) expect(landingTargets).toContain(sourcePath);

    const guideText = learningGuides.map((sourcePath) =>
      manifest.pages.find((page) => page.sourcePath === sourcePath)?.sourcePath ?? '').join('\n');
    expect(guideText).toContain('docs/specification-model.md');
    const maintainedText = (await buildRegistry(projectRoot)).documents
      .filter((document) => learningGuides.includes(document.sourcePath))
      .map((document) => document.content).join('\n');
    for (const authority of [
      'architecture.md', 'features/', '.concorde/attempts/', '.concorde/reflections/log.md', 'source code', 'tests',
    ]) {
      expect(maintainedText.toLowerCase()).toContain(authority);
    }
  });

  it('does not present temporal implementation artifacts as permanent guide authority', async () => {
    const manifest = createManifest(await buildRegistry(projectRoot));
    expect(manifest.pages.some((page) => page.sourcePath.startsWith('.concorde/'))).toBe(false);
    expect(manifest.excludedSources.some((source) => source.sourcePath.startsWith('.concorde/'))).toBe(false);
  });

  it('keeps the current no-diagram prototype explicit on every module architecture', async () => {
    const registry = await buildRegistry(projectRoot);
    const architecturePages = registry.documents.filter((document) => document.contentKind === 'module-architecture');
    expect(architecturePages.flatMap((document) =>
      'architectureDiagrams' in document ? document.architectureDiagrams ?? [] : [])).toEqual([]);
    expect(registry.documents.filter((document) => document.contentKind !== 'module-architecture')
      .every((document) => !('architectureDiagrams' in document))).toBe(true);
  });

  it('documents ask as a cited read-only agent surface rather than a runtime operation', async () => {
    const registry = await buildRegistry(projectRoot);
    const commands = registry.documents.find((document) => document.sourcePath === 'docs/commands.md');
    if (!commands) throw new Error('Expected docs/commands.md in the documentation registry.');
    const text = commands.content.toLowerCase();
    expect(text).toContain('speckit.concorde.ask');
    expect(text).toContain('read-only');
    expect(text).toContain('never invokes another command');
    expect(text).toContain('protocol 12');
  });
});
