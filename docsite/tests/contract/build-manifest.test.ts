import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

import Ajv2020 from 'ajv/dist/2020.js';
import {describe, expect, it} from 'vitest';

import {createManifest, validateBuildManifest} from '../../plugins/concorde-content/manifest';
import {buildRegistry} from '../../plugins/concorde-content/registry';

const fixture = resolve(__dirname, '../fixtures/valid-project');

describe('Build Manifest 10', () => {
  it('accepts the executable representative example under the strict schema', async () => {
    const interfaceRoot = resolve(__dirname, '../fixtures/interfaces');
    const schema = JSON.parse(await readFile(resolve(interfaceRoot, 'build-manifest.schema.json'), 'utf8'));
    const example = JSON.parse(await readFile(resolve(interfaceRoot, 'build-manifest.example.json'), 'utf8'));
    const validate = new Ajv2020({allErrors: true, strictTypes: true, strictTuples: true}).compile(schema);
    expect(validate(example), JSON.stringify(validate.errors, null, 2)).toBe(true);
    expect(example.schemaVersion).toBe(10);
  });

  it('projects only module architectures and feature designs', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    expect(() => validateBuildManifest(manifest)).not.toThrow();
    expect(manifest.schemaVersion).toBe(10);
    expect(manifest.collections.map((collection) => collection.id)).toEqual([
      'architecture', 'features',
    ]);
    expect(manifest.pages.map((page) => page.kind).sort()).toEqual([
      'feature-design', 'feature-design', 'module-architecture', 'module-architecture',
    ]);
    expect(manifest.pages.some((page) => page.sourcePath === 'README.md' || page.sourcePath.startsWith('docs/'))).toBe(false);
    expect(manifest.routeInventory.some((route) => route === '/docs' || route.startsWith('/docs/'))).toBe(false);
    expect(JSON.stringify(manifest)).not.toMatch(/feature-abstract|feature-implementation|module-design|contracts/);
  });

  it('carries architecture diagrams and flat related feature summaries on their owning pages', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    expect(manifest.pages.find((page) => page.kind === 'module-architecture' && page.moduleId === 'module.fixture'))
      .toMatchObject({
        route: '/architecture/module.fixture',
        architectureDiagrams: [expect.objectContaining({source: 'specs/example/diagrams/fixture-level-view.json'})],
      });
    expect(manifest.pages.find((page) => page.kind === 'feature-design' && page.featureId === 'feature.fixture.alpha'))
      .toMatchObject({
        route: '/features/feature.fixture.alpha', moduleId: 'module.fixture',
        moduleRoute: '/architecture/module.fixture', status: 'Draft',
        relatedFeatures: [expect.objectContaining({featureId: 'feature.fixture.beta', route: '/features/feature.fixture.beta'})],
      });
  });

  it('is deterministic, sorted, project-relative, and timestamp-free', async () => {
    const first = createManifest(await buildRegistry(fixture));
    const second = createManifest(await buildRegistry(fixture));
    expect(second).toEqual(first);
    expect(first.generator).toEqual({name: 'concorde-docsite', version: '0.6.0', docusaurusVersion: '3.10.2'});
    expect(first.collections.map((collection) => collection.include)).toEqual([
      ['**/architecture.md'], ['**/features/*.md'],
    ]);
    expect(first.validation.checks.map((check) => check.name)).toEqual([
      'profile-7-sources', 'identity-relations-and-routes', 'rendered-route-inventory',
    ]);
    expect(first.pages.map((page) => page.sourcePath)).toEqual([...first.pages.map((page) => page.sourcePath)].sort());
    expect(first.routeInventory).toEqual([...first.routeInventory].sort());
    expect(JSON.stringify(first)).not.toContain(fixture);
    expect(JSON.stringify(first)).not.toContain('realPath');
    expect(JSON.stringify(first)).not.toMatch(/timestamp|generatedAt/);
  });

  it('projects a fixture manifest accepted by the executable schema', async () => {
    const schema = JSON.parse(await readFile(resolve(__dirname, '../fixtures/interfaces/build-manifest.schema.json'), 'utf8'));
    const validate = new Ajv2020({allErrors: true, strictTypes: true, strictTuples: true}).compile(schema);
    const manifest = createManifest(await buildRegistry(fixture));
    expect(validate(manifest), JSON.stringify(validate.errors, null, 2)).toBe(true);
  });

  it('rejects unsupported versions, absolute provenance, and unsorted routes', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    expect(() => validateBuildManifest({...manifest, schemaVersion: 9} as never)).toThrow(/schemaVersion 10/);
    const absolute = structuredClone(manifest);
    absolute.pages[0].sourcePath = '/tmp/source.md';
    expect(() => validateBuildManifest(absolute)).toThrow(/project-relative/);
    const unsorted = structuredClone(manifest);
    unsorted.routeInventory.reverse();
    expect(() => validateBuildManifest(unsorted)).toThrow(/routeInventory.*sorted/);
  });
});
