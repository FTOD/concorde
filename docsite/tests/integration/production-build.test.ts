import {createHash} from 'node:crypto';
import {readdir, readFile, rm} from 'node:fs/promises';
import {resolve} from 'node:path';
import {spawnSync} from 'node:child_process';

import Ajv2020 from 'ajv/dist/2020';
import {beforeAll, describe, expect, it} from 'vitest';

const siteDir = resolve(__dirname, '../..');
const buildDir = resolve(siteDir, 'build');
let firstManifest = '';
let firstDiagramHashes: Record<string, string> = {};

async function diagramHashes(): Promise<Record<string, string>> {
  const directory = resolve(siteDir, '../generated/architecture');
  const names = (await readdir(directory)).filter((name) => name.endsWith('.html')).sort();
  return Object.fromEntries(await Promise.all(names.map(async (name) => [
    name,
    createHash('sha256').update(await readFile(resolve(directory, name))).digest('hex'),
  ])));
}

function build() {
  const result = spawnSync(process.execPath, [resolve(siteDir, 'node_modules/tsx/dist/cli.mjs'), 'scripts/build.ts'], {
    cwd: siteDir, encoding: 'utf8', timeout: 120_000,
  });
  if (result.status !== 0) throw new Error(`${result.stdout}\n${result.stderr}`);
}

beforeAll(async () => {
  await rm(resolve(siteDir, '../generated'), {recursive: true, force: true});
  build();
  firstManifest = await readFile(resolve(buildDir, 'build-manifest.json'), 'utf8');
  firstDiagramHashes = await diagramHashes();
}, 120_000);

describe('production build', () => {
  it('publishes landing, three-part navigation, provenance, diagrams, local search, and all manifest routes', async () => {
    const manifest = JSON.parse(firstManifest);
    expect(manifest.schemaVersion).toBe(6);
    const schema = JSON.parse(await readFile(resolve(siteDir, '../specs/concorde/features/002-create-project-docsite/contracts/build-manifest.schema.json'), 'utf8'));
    expect(new Ajv2020().compile(schema)(manifest)).toBe(true);
    expect(await readFile(resolve(buildDir, 'index.html'), 'utf8')).toContain('One project, two source roots, three views');
    const searchIndex = await readFile(resolve(buildDir, 'search-index.json'), 'utf8');
    expect(searchIndex).toContain('Create Unified Project Docsite');
    expect(searchIndex).toContain('Architecture Core');
    expect(await readFile(resolve(buildDir, 'architecture/concorde-root.html'), 'utf8')).toContain('Concorde — Root Features and Invocation');
    expect(await readFile(resolve(buildDir, 'architecture/concorde-spec-kit-component-model.html'), 'utf8'))
      .toContain('How Concorde Commands Reach a Clean Project');
    expect(await readFile(resolve(buildDir, 'architecture/concorde-bundle-installation-flow.html'), 'utf8'))
      .toContain('Install, Materialize, and Prove Concorde');
    expect(await readFile(resolve(buildDir, 'architecture/concorde-workflow-components.html'), 'utf8'))
      .toContain('Concorde Workflow — Installed Surfaces, Runtime, and Workspace');
    expect(await readFile(resolve(buildDir, 'architecture/concorde-self-hosting-components.html'), 'utf8'))
      .toContain('Concorde Self-Hosting Components');
    expect(await readFile(resolve(buildDir, 'architecture/project-docsite-publication-flow.html'), 'utf8'))
      .toContain('Project Docsite — Publication Invocation');
    expect(Object.keys(firstDiagramHashes)).toHaveLength(7);
    expect((await readdir(resolve(siteDir, '../generated/architecture'))).every((name) => name.endsWith('.html'))).toBe(true);
    const concordeFeature = manifest.pages.find((page: {featureId?: string; kind?: string}) => page.kind === 'feature-tldr' && page.featureId === 'feature.concorde.workflow');
    const docsiteFeature = manifest.pages.find((page: {featureId?: string; kind?: string}) => page.kind === 'feature-tldr' && page.featureId === 'feature.concorde.publish-project-docsite');
    const selfHostingFeature = manifest.pages.find((page: {featureId?: string; kind?: string}) => page.kind === 'feature-tldr' && page.featureId === 'feature.concorde.self-host-framework');
    if (!concordeFeature || !docsiteFeature || !selfHostingFeature) throw new Error('Expected the TL;DR landing pages of Features 001, 002, and 004 in the build manifest.');
    expect(concordeFeature.diagrams).toEqual(expect.arrayContaining([expect.objectContaining({
      source: 'specs/concorde/features/001-concorde-workflow/diagrams/concorde-workflow-components.json',
      role: 'core',
      kind: 'architecture',
      route: '/architecture/concorde-workflow-components.html',
    })]));
    expect(docsiteFeature.diagrams).toEqual(expect.arrayContaining([expect.objectContaining({
      source: 'specs/concorde/features/002-create-project-docsite/diagrams/project-docsite-publication-flow.json',
      route: '/architecture/project-docsite-publication-flow.html',
    })]));
    expect(selfHostingFeature.diagrams).toEqual(expect.arrayContaining([expect.objectContaining({
      source: 'specs/concorde/features/004-self-host-concorde/diagrams/concorde-self-hosting-components.json',
      role: 'core',
      kind: 'architecture',
      route: '/architecture/concorde-self-hosting-components.html',
    })]));
    const concordeFeatureHtml = await readFile(resolve(buildDir, `${concordeFeature.route.slice(1)}.html`), 'utf8');
    const docsiteFeatureHtml = await readFile(resolve(buildDir, `${docsiteFeature.route.slice(1)}.html`), 'utf8');
    const selfHostingFeatureHtml = await readFile(resolve(buildDir, `${selfHostingFeature.route.slice(1)}.html`), 'utf8');
    expect(concordeFeatureHtml).toContain('Feature diagrams');
    expect(concordeFeatureHtml).toContain('Concorde Workflow — Installed Surfaces, Runtime, and Workspace');
    expect(concordeFeatureHtml).toContain('/architecture/concorde-workflow-components.html');
    expect(docsiteFeatureHtml).toContain('Feature diagrams');
    expect(docsiteFeatureHtml).toContain('Project Docsite — Publication Invocation');
    expect(docsiteFeatureHtml).toContain('/architecture/project-docsite-publication-flow.html');
    expect(selfHostingFeatureHtml).toContain('Feature diagrams');
    expect(selfHostingFeatureHtml).toContain('Concorde Self-Hosting Components');
    expect(selfHostingFeatureHtml).toContain('/architecture/concorde-self-hosting-components.html');
    // The landing page links its specification and design reference; each of those links back to the TL;DR.
    for (const landing of [concordeFeature, docsiteFeature, selfHostingFeature]) {
      const html = await readFile(resolve(buildDir, `${landing.route.slice(1)}.html`), 'utf8');
      expect(html).toContain(`${landing.specificationRoute}"`);
      expect(html).toContain(`${landing.designRoute}"`);
      for (const companionRoute of [landing.specificationRoute, landing.designRoute]) {
        expect(await readFile(resolve(buildDir, `${companionRoute.slice(1)}.html`), 'utf8')).toContain(`${landing.route}"`);
      }
    }
    const rootModule = await readFile(resolve(buildDir, 'architecture/concorde/module.concorde.html'), 'utf8');
    expect(rootModule).toContain('Interactive architecture view for Concorde');
    expect(rootModule).toContain('/architecture/concorde-root.html');
    const documentationModule = await readFile(
      resolve(buildDir, 'architecture/concorde/modules/documentation/module.concorde.documentation.html'),
      'utf8',
    );
    expect(documentationModule).toContain('Interactive architecture view for Documentation');
    expect(documentationModule).toContain('/architecture/documentation.html');
    for (const page of manifest.pages) {
      const route = page.route === '/' ? '/index' : page.route.replace(/\/$/, '');
      const target = `${route}.html`;
      const html = await readFile(resolve(buildDir, target.slice(1)), 'utf8');
      expect(html).toContain(page.sourcePath);
    }
  });

  it('emits an identical manifest on an unchanged second build', async () => {
    const beforeHash = createHash('sha256').update(firstManifest).digest('hex');
    build();
    const second = await readFile(resolve(buildDir, 'build-manifest.json'), 'utf8');
    expect(createHash('sha256').update(second).digest('hex')).toBe(beforeHash);
    expect(await diagramHashes()).toEqual(firstDiagramHashes);
  }, 120_000);
});
