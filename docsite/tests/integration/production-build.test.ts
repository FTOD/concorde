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
    expect(manifest.schemaVersion).toBe(9);
    const schema = JSON.parse(await readFile(resolve(siteDir, '../specs/concorde/features/002-create-project-docsite/contracts/build-manifest.schema.json'), 'utf8'));
    expect(new Ajv2020().compile(schema)(manifest)).toBe(true);
    const homepage = await readFile(resolve(buildDir, 'index.html'), 'utf8');
    expect(homepage).toContain('Key features');
    expect(homepage).toContain('Concorde commands');
    expect(homepage).toContain('README.md');
    expect(manifest.pages.filter((page: {sourcePath: string; route: string}) =>
      page.sourcePath === 'README.md' && page.route === '/')).toHaveLength(1);
    const searchIndex = await readFile(resolve(buildDir, 'search-index.json'), 'utf8');
    expect(searchIndex).toContain('Create Unified Project Docsite');
    expect(searchIndex).toContain('Scripts');
    expect(await readFile(resolve(buildDir, 'architecture/concorde-interaction-architecture.html'), 'utf8')).toContain('Concorde Interaction Architecture');
    expect(await readFile(resolve(buildDir, 'architecture/concorde-skill-workspace-file-flow.html'), 'utf8'))
      .toContain('Concorde Skills: Architecture and Feature Workspaces');
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
    expect(Object.keys(firstDiagramHashes)).toHaveLength(9);
    expect((await readdir(resolve(siteDir, '../generated/architecture'))).every((name) => name.endsWith('.html'))).toBe(true);
    const concordeFeature = manifest.pages.find((page: {featureId?: string; kind?: string}) => page.kind === 'feature-abstract' && page.featureId === 'feature.concorde.workflow');
    const docsiteFeature = manifest.pages.find((page: {featureId?: string; kind?: string}) => page.kind === 'feature-abstract' && page.featureId === 'feature.concorde.publish-project-docsite');
    const selfHostingFeature = manifest.pages.find((page: {featureId?: string; kind?: string}) => page.kind === 'feature-abstract' && page.featureId === 'feature.concorde.self-host-framework');
    const documentationFeature = manifest.pages.find((page: {featureId?: string; kind?: string}) =>
      page.kind === 'feature-abstract' && page.featureId === 'feature.auto-docs.publish-project-docsite');
    if (!concordeFeature || !docsiteFeature || !selfHostingFeature) throw new Error('Expected the abstract landing pages of Features 001, 002, and 004 in the build manifest.');
    expect(documentationFeature?.route).toBe('/features/feature.auto-docs.publish-project-docsite');
    for (const page of manifest.pages.filter((candidate: {kind: string}) => candidate.kind.startsWith('feature-'))) {
      expect(page.route.slice('/features/'.length)).not.toMatch(/(?:^|\/)(?:architecture|modules|features)(?:\/|$)/);
    }
    const stagedFeaturePaths = await readdir(resolve(siteDir, '.generated/content/features'), {recursive: true});
    expect(stagedFeaturePaths).toContain('feature.auto-docs.publish-project-docsite/_category_.json');
    expect(stagedFeaturePaths.every((path) => !/(?:^|\/)(?:architecture|modules|features)(?:\/|$)/.test(path))).toBe(true);
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
    expect(docsiteFeatureHtml).not.toMatch(/>modules<\/a>/i);
    const documentationFeatureHtml = await readFile(resolve(buildDir, `${documentationFeature.route.slice(1)}.html`), 'utf8');
    expect(documentationFeatureHtml).toContain('/architecture/concorde/modules/auto-docs/module.concorde.auto-docs');
    expect(documentationFeatureHtml).toContain('/features/feature.concorde.publish-project-docsite');
    expect(selfHostingFeatureHtml).toContain('Feature diagrams');
    expect(selfHostingFeatureHtml).toContain('Concorde Self-Hosting Components');
    expect(selfHostingFeatureHtml).toContain('/architecture/concorde-self-hosting-components.html');
    // The landing page links design and implementation; each links back to the abstract.
    for (const landing of [concordeFeature, docsiteFeature, selfHostingFeature]) {
      const html = await readFile(resolve(buildDir, `${landing.route.slice(1)}.html`), 'utf8');
      expect(html).toContain(`${landing.designRoute}"`);
      expect(html).toContain(`${landing.implementationRoute}"`);
      for (const companionRoute of [landing.designRoute, landing.implementationRoute]) {
        expect(await readFile(resolve(buildDir, `${companionRoute.slice(1)}.html`), 'utf8')).toContain(`${landing.route}"`);
      }
    }
    const rootModule = await readFile(resolve(buildDir, 'architecture/concorde/module.concorde.html'), 'utf8');
    expect(rootModule).toContain('Interactive architecture view for Concorde');
    expect(rootModule).toContain('/architecture/concorde-interaction-architecture.html');
    expect(rootModule).toContain('/architecture/concorde-skill-workspace-file-flow.html');
    expect(rootModule).toContain('specs/concorde/architecture/diagrams/level-view.json');
    const rootPage = manifest.pages.find((page: {sourcePath: string}) => page.sourcePath === 'specs/concorde/module.md');
    expect(rootPage.architectureDiagrams).toEqual([
      expect.objectContaining({
        source: 'specs/concorde/architecture/diagrams/level-view.json', kind: 'architecture', route: '/architecture/concorde-interaction-architecture.html',
      }),
      expect.objectContaining({
        source: 'specs/concorde/architecture/diagrams/skill-workspace-file-flow.json', kind: 'dataflow', route: '/architecture/concorde-skill-workspace-file-flow.html',
      }),
    ]);
    expect(rootPage.links).toEqual(expect.arrayContaining([
      {targetSourcePath: 'specs/concorde/architecture/diagrams/level-view.json', targetRoute: '/architecture/concorde-interaction-architecture.html'},
    ]));
    const rootDesign = manifest.pages.find((page: {sourcePath: string}) => page.sourcePath === 'specs/concorde/design.md');
    expect(rootDesign.links).toEqual(expect.arrayContaining([
      {targetSourcePath: 'specs/concorde/architecture/diagrams/skill-workspace-file-flow.json', targetRoute: '/architecture/concorde-skill-workspace-file-flow.html'},
    ]));
    const documentationModule = await readFile(
      resolve(buildDir, 'architecture/concorde/modules/auto-docs/module.concorde.auto-docs.html'),
      'utf8',
    );
    expect(documentationModule).toContain('Interactive architecture view for Auto-Docs');
    expect(documentationModule).toContain('/architecture/auto-docs.html');
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
