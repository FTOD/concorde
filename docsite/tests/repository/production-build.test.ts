import {createHash} from 'node:crypto';
import {readdir, readFile, rm} from 'node:fs/promises';
import {resolve} from 'node:path';
import {spawnSync} from 'node:child_process';

import Ajv2020 from 'ajv/dist/2020.js';
import {beforeAll, describe, expect, it} from 'vitest';

import {validateBuildManifest} from '../../plugins/concorde-content/manifest';
import type {BuildManifest, FeatureGraph} from '../../plugins/concorde-content/types';

const siteDir = resolve(__dirname, '../..');
const buildDir = resolve(siteDir, 'build');
let firstManifestText = '';
let firstFeatureGraphText = '';
let firstDiagramHashes: Record<string, string> = {};

async function diagramHashes(): Promise<Record<string, string>> {
  const directory = resolve(siteDir, '../generated/architecture');
  let names: string[];
  try {
    names = (await readdir(directory)).filter((name) => name.endsWith('.html')).sort();
  } catch {
    names = [];
  }
  return Object.fromEntries(await Promise.all(names.map(async (name) => [
    name, createHash('sha256').update(await readFile(resolve(directory, name))).digest('hex'),
  ])));
}

function build(): void {
  const result = spawnSync(process.execPath, [resolve(siteDir, 'node_modules/tsx/dist/cli.mjs'), 'scripts/build.ts'], {
    cwd: siteDir, encoding: 'utf8', timeout: 120_000,
  });
  if (result.status !== 0) throw new Error(`${result.stdout}\n${result.stderr}`);
}

beforeAll(async () => {
  await rm(resolve(siteDir, '../generated'), {recursive: true, force: true});
  build();
  firstManifestText = await readFile(resolve(buildDir, 'build-manifest.json'), 'utf8');
  firstFeatureGraphText = await readFile(resolve(buildDir, 'feature-graph.json'), 'utf8');
  firstDiagramHashes = await diagramHashes();
}, 120_000);

describe('Profile 7 production build', () => {
  it('publishes architecture and design landing pages with provenance and architecture-owned diagrams', async () => {
    const manifest = JSON.parse(firstManifestText) as BuildManifest;
    expect(() => validateBuildManifest(manifest)).not.toThrow();
    expect(manifest.schemaVersion).toBe(12);
    expect(new Set(manifest.pages.map((page) => page.kind))).toEqual(new Set([
      'module-architecture', 'feature-design',
    ]));
    expect(manifest.collections.map((collection) => collection.id)).toEqual(['architecture', 'features']);
    expect(manifest.pages.some((page) => page.sourcePath === 'README.md' || page.sourcePath.startsWith('docs/'))).toBe(false);
    expect(manifest.routeInventory.some((route) => route === '/docs' || route.startsWith('/docs/'))).toBe(false);
    expect(firstManifestText).not.toMatch(/feature-abstract|feature-implementation|module-design|abstractRoute|implementationRoute/);
    expect(manifest.pages.some((page) => page.sourcePath.startsWith('.concorde/'))).toBe(false);
    expect(manifest.excludedSources.some((source) => source.sourcePath.startsWith('.concorde/'))).toBe(false);

    const homepage = await readFile(resolve(buildDir, 'index.html'), 'utf8');
    expect(homepage).toContain('/architecture/module.concorde');
    expect(homepage).not.toContain('README.md');

    const rootModule = manifest.pages.find((page) => page.kind === 'module-architecture' && page.moduleId === 'module.concorde');
    expect(rootModule).toMatchObject({
      sourcePath: 'specs/concorde/architecture.md', route: '/architecture/module.concorde',
    });
    const rootFeature = manifest.pages.find((page) => page.kind === 'feature-design' && page.featureId === 'feature.concorde.workflow');
    const autoDocsFeature = manifest.pages.find((page) =>
      page.kind === 'feature-design' && page.featureId === 'feature.auto-docs.publish-project-docsite');
    expect(rootFeature).toMatchObject({route: '/features/feature.concorde.workflow', moduleRoute: '/architecture/module.concorde'});
    expect(autoDocsFeature).toMatchObject({moduleRoute: '/architecture/module.concorde.auto-docs'});

    const diagrams = manifest.pages.flatMap((page) => page.architectureDiagrams ?? []);
    expect(diagrams).toHaveLength(7);
    expect(diagrams.every((diagram) =>
      diagram.kind === 'architecture' && diagram.source.endsWith('/diagrams/system-overview.json'))).toBe(true);
    expect(Object.keys(firstDiagramHashes).sort()).toEqual([
      'concorde-auto-docs-system-overview.html',
      'concorde-capabilities-system-overview.html',
      'concorde-distribution-system-overview.html',
      'concorde-lifecycle-system-overview.html',
      'concorde-reflections-system-overview.html',
      'concorde-system-overview.html',
      'concorde-understanding-system-overview.html',
    ]);
    expect(manifest.pages.filter((page) => page.kind !== 'module-architecture')
      .every((page) => page.architectureDiagrams === undefined)).toBe(true);

    const stagedFeatures = await readdir(resolve(siteDir, '.generated/content/features'), {recursive: true});
    expect(stagedFeatures).toContain('feature.auto-docs.publish-project-docsite.md');
    expect(stagedFeatures.every((path) => !/(?:^|\/)(?:modules|features|subfeatures)(?:\/|$)/.test(path))).toBe(true);
    const featureSidebar = JSON.parse(await readFile(resolve(siteDir, '.generated/features-sidebar.json'), 'utf8'));
    const sidebarDocIds = (items: Array<{type: string; id?: string; items?: unknown[]}>): string[] => items.flatMap((item) =>
      item.type === 'doc' && item.id ? [item.id] : sidebarDocIds((item.items ?? []) as Array<{type: string; id?: string; items?: unknown[]}>));
    expect(sidebarDocIds(featureSidebar).sort()).toEqual(manifest.pages
      .filter((candidate) => candidate.kind === 'feature-design')
      .map((page) => page.featureId!).sort());

    for (const page of manifest.pages) {
      const output = page.route === '/' ? 'index.html' : `${page.route.slice(1)}.html`;
      expect(await readFile(resolve(buildDir, output), 'utf8')).toContain(page.sourcePath);
    }
  });

  it('emits a schema-valid feature-graph.json and a /graph page carrying the same edges as text', async () => {
    const manifest = JSON.parse(firstManifestText) as BuildManifest;
    const graph = JSON.parse(firstFeatureGraphText) as FeatureGraph;
    const schema = JSON.parse(await readFile(resolve(siteDir, 'tests/fixtures/interfaces/feature-graph.schema.json'), 'utf8'));
    const validate = new Ajv2020({allErrors: true, strictTypes: true, strictTuples: true}).compile(schema);
    expect(validate(graph), JSON.stringify(validate.errors, null, 2)).toBe(true);
    expect(graph.features.length).toBeGreaterThan(0);
    expect(graph.edges.length).toBeGreaterThan(0);
    expect(manifest.featureGraph).toBe('feature-graph.json');
    expect(manifest.featureGraphCounts).toEqual(graph.counts);

    const graphPage = await readFile(resolve(buildDir, 'graph.html'), 'utf8');
    expect(graphPage).toContain('<table');
    for (const feature of graph.features) expect(graphPage).toContain(feature.id);
    for (const edge of graph.edges) {
      expect(graphPage).toContain(edge.source);
      expect(graphPage).toContain(edge.target);
    }
  });

  it('emits an identical manifest, feature graph, and diagram set on an unchanged second build', async () => {
    const beforeHash = createHash('sha256').update(firstManifestText).digest('hex');
    const beforeGraphHash = createHash('sha256').update(firstFeatureGraphText).digest('hex');
    build();
    const second = await readFile(resolve(buildDir, 'build-manifest.json'), 'utf8');
    const secondGraph = await readFile(resolve(buildDir, 'feature-graph.json'), 'utf8');
    expect(createHash('sha256').update(second).digest('hex')).toBe(beforeHash);
    expect(createHash('sha256').update(secondGraph).digest('hex')).toBe(beforeGraphHash);
    expect(await diagramHashes()).toEqual(firstDiagramHashes);
  }, 120_000);
});
