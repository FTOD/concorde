import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

import Ajv2020 from 'ajv/dist/2020.js';

import {createManifest} from '../../plugins/concorde-content/manifest';
import {buildRegistry} from '../../plugins/concorde-content/registry';

describe('build manifest contract', () => {
  it('accepts the normative representative example', async () => {
    const contractRoot = resolve(
      process.cwd(),
      '../specs/concorde/features/002-auto-docsite/contracts',
    );
    const schema = JSON.parse(
      await readFile(resolve(contractRoot, 'build-manifest.schema.json'), 'utf8'),
    );
    const example = JSON.parse(
      await readFile(resolve(contractRoot, 'build-manifest.example.json'), 'utf8'),
    );
    const validate = new Ajv2020({allErrors: true, strictTypes: true, strictTuples: true}).compile(schema);

    expect(validate(example), JSON.stringify(validate.errors, null, 2)).toBe(true);
    expect(example.schemaVersion).toBe(9);
    expect(example.collections[0]).toEqual({id: 'home', sourceBase: '.', routeBase: '/', include: ['README.md']});
    expect(example.pages.filter((page: {sourcePath: string; route: string}) =>
      page.sourcePath === 'README.md' && page.route === '/')).toHaveLength(1);
    const featurePages = example.pages.filter((page: {kind: string}) => page.kind.startsWith('feature-'));
    expect(featurePages.map((page: {route: string}) => page.route)).toEqual([
      '/features/feature.concorde.publish-project-docsite/implementation',
      '/features/feature.concorde.publish-project-docsite/design',
      '/features/feature.concorde.publish-project-docsite',
    ]);
    expect(JSON.stringify(featurePages)).not.toMatch(/\/features\/concorde\/features\//);
  });

  it('compiles the normative schema under AJV strict types without diagnostics', async () => {
    const contractRoot = resolve(
      process.cwd(), '../specs/concorde/features/002-auto-docsite/contracts',
    );
    const schema = JSON.parse(await readFile(resolve(contractRoot, 'build-manifest.schema.json'), 'utf8'));
    const logged: string[] = [];
    const logger = {
      log: (message: unknown) => logged.push(String(message)),
      warn: (message: unknown) => logged.push(String(message)),
      error: (message: unknown) => logged.push(String(message)),
    };
    expect(() => new Ajv2020({allErrors: true, strictTypes: true, strictTuples: true, logger}).compile(schema)).not.toThrow();
    expect(logged).toEqual([]);
  });

  it('rejects a core-role diagram on a project-document page', async () => {
    const contractRoot = resolve(
      process.cwd(), '../specs/concorde/features/002-auto-docsite/contracts',
    );
    const schema = JSON.parse(await readFile(resolve(contractRoot, 'build-manifest.schema.json'), 'utf8'));
    const manifest = JSON.parse(await readFile(resolve(contractRoot, 'build-manifest.example.json'), 'utf8'));
    const validate = new Ajv2020({allErrors: true, strictTypes: true, strictTuples: true}).compile(schema);
    const page = manifest.pages.find((candidate: {kind: string; route: string}) =>
      candidate.kind === 'project-document' && candidate.route === '/docs/');
    page.diagrams = [{
      source: 'docs/diagrams/example.json',
      sourceSha256: 'a'.repeat(64),
      role: 'core',
      kind: 'architecture',
      scenarios: ['example'],
      title: 'Example',
      route: '/architecture/example.html',
    }];
    expect(validate(manifest)).toBe(false);
    expect(validate.errors).toEqual(expect.arrayContaining([expect.objectContaining({
      keyword: 'const',
      instancePath: expect.stringMatching(/^\/pages\/\d+\/diagrams\/0\/role$/),
      params: {allowedValue: 'supplemental'},
    })]));
    page.diagrams[0].role = 'supplemental';
    expect(validate(manifest), JSON.stringify(validate.errors, null, 2)).toBe(true);
  });

  it('keeps published-site v5 aligned with Build Manifest schema v9', async () => {
    const contractRoot = resolve(
      process.cwd(), '../specs/concorde/features/002-auto-docsite/contracts',
    );
    const publishedSite = await readFile(resolve(contractRoot, 'published-site.md'), 'utf8');
    expect(publishedSite).toContain('# Published Project Site Contract v5');
    expect(publishedSite).toContain('build-manifest contract (schema version 9)');
    expect(publishedSite).toContain('/features/<feature-id>');
  });

  it('projects a fixture manifest that satisfies the v9 schema', async () => {
    const schema = JSON.parse(await readFile(resolve(
      process.cwd(), '../specs/concorde/features/002-auto-docsite/contracts/build-manifest.schema.json',
    ), 'utf8'));
    const validate = new Ajv2020({allErrors: true, strictTypes: true, strictTuples: true}).compile(schema);
    const manifest = JSON.parse(JSON.stringify(createManifest(await buildRegistry(resolve(__dirname, '../fixtures/valid-project')))));
    expect(validate(manifest), JSON.stringify(validate.errors, null, 2)).toBe(true);
    expect(manifest.pages.map((page: {kind: string}) => page.kind).sort()).toEqual([
      'architecture-source',
      'feature-abstract', 'feature-abstract', 'feature-abstract', 'feature-abstract',
      'feature-design', 'feature-design', 'feature-design', 'feature-design',
      'feature-implementation', 'feature-implementation', 'feature-implementation', 'feature-implementation',
      'module-design', 'project-document', 'project-document', 'project-document',
    ]);
  });

  it('projects sorted relative paths and repeatable route inventory without real paths', async () => {
    const root = resolve(__dirname, '../fixtures/valid-project');
    const first = createManifest(await buildRegistry(root));
    const second = createManifest(await buildRegistry(root));
    expect(first.schemaVersion).toBe(9);
    expect(first.generator).toEqual({name: 'concorde-docsite', version: '0.3.0', docusaurusVersion: '3.10.2'});
    expect(first.collections.map((collection) => collection.id)).toEqual([
      'home', 'architecture', 'docs', 'feature-abstracts', 'features', 'feature-implementations',
    ]);
    expect(first.collections.map((collection) => collection.include)).toEqual([
      ['README.md'], ['**/module.md', '**/design.md', '**/architecture/contracts/**/contract.md'], ['**/*.md'], ['**/abstract.md'], ['**/design.md'], ['**/implementation.md'],
    ]);
    expect(second).toEqual(first);
    expect(first.pages.map((page) => page.sourcePath)).toEqual([...first.pages.map((page) => page.sourcePath)].sort());
    expect(first.routeInventory).toEqual([...first.routeInventory].sort());
    expect(JSON.stringify(first)).not.toContain(root);
    expect(JSON.stringify(first)).not.toContain('realPath');
  });
});
