import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {spawnSync} from 'node:child_process';

import Ajv2020 from 'ajv/dist/2020';
import {beforeAll, describe, expect, it} from 'vitest';

const siteDir = resolve(__dirname, '../..');
const buildDir = resolve(siteDir, 'build');
let firstManifest = '';

function build() {
  const result = spawnSync(process.execPath, [resolve(siteDir, 'node_modules/tsx/dist/cli.mjs'), 'scripts/build.ts'], {
    cwd: siteDir, encoding: 'utf8', timeout: 120_000,
  });
  if (result.status !== 0) throw new Error(`${result.stdout}\n${result.stderr}`);
}

beforeAll(async () => {
  build();
  firstManifest = await readFile(resolve(buildDir, 'build-manifest.json'), 'utf8');
}, 120_000);

describe('production build', () => {
  it('publishes landing, three-part navigation, provenance, diagrams, local search, and all manifest routes', async () => {
    const manifest = JSON.parse(firstManifest);
    const schema = JSON.parse(await readFile(resolve(siteDir, '../specs/concorde/features/002-create-project-docsite/contracts/build-manifest.schema.json'), 'utf8'));
    expect(new Ajv2020().compile(schema)(manifest)).toBe(true);
    expect(await readFile(resolve(buildDir, 'index.html'), 'utf8')).toContain('One project, two source roots, three views');
    const searchIndex = await readFile(resolve(buildDir, 'search-index.json'), 'utf8');
    expect(searchIndex).toContain('Create Unified Project Docsite');
    expect(searchIndex).toContain('Architecture Core');
    expect(await readFile(resolve(buildDir, 'architecture/concorde-root.html'), 'utf8')).toContain('Concorde — Root Features and Invocation');
    expect(await readFile(resolve(buildDir, 'architecture/concorde-spec-kit-component-model.html'), 'utf8'))
      .toContain('How Concorde Is Installed through Spec Kit');
    expect(await readFile(resolve(buildDir, 'architecture/concorde-starter-installation-flow.html'), 'utf8'))
      .toContain('Install and Maintain Concorde');
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
  }, 120_000);
});
