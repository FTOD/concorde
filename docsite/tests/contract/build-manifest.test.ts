import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

import Ajv2020 from 'ajv/dist/2020.js';

import {createManifest} from '../../plugins/concorde-content/manifest';
import {buildRegistry} from '../../plugins/concorde-content/registry';

describe('build manifest contract', () => {
  it('accepts the normative representative example', async () => {
    const contractRoot = resolve(
      process.cwd(),
      '../specs/concorde/features/002-create-project-docsite/contracts',
    );
    const schema = JSON.parse(
      await readFile(resolve(contractRoot, 'build-manifest.schema.json'), 'utf8'),
    );
    const example = JSON.parse(
      await readFile(resolve(contractRoot, 'build-manifest.example.json'), 'utf8'),
    );
    const validate = new Ajv2020({allErrors: true}).compile(schema);

    expect(validate(example), JSON.stringify(validate.errors, null, 2)).toBe(true);
    expect(example.schemaVersion).toBe(7);
  });

  it('projects a fixture manifest that satisfies the v7 schema', async () => {
    const schema = JSON.parse(await readFile(resolve(
      process.cwd(), '../specs/concorde/features/002-create-project-docsite/contracts/build-manifest.schema.json',
    ), 'utf8'));
    const validate = new Ajv2020({allErrors: true}).compile(schema);
    const manifest = JSON.parse(JSON.stringify(createManifest(await buildRegistry(resolve(__dirname, '../fixtures/valid-project')))));
    expect(validate(manifest), JSON.stringify(validate.errors, null, 2)).toBe(true);
    expect(manifest.pages.map((page: {kind: string}) => page.kind).sort()).toEqual([
      'architecture-source',
      'feature-abstract', 'feature-abstract', 'feature-abstract', 'feature-abstract',
      'feature-design', 'feature-design', 'feature-design', 'feature-design',
      'feature-implementation', 'feature-implementation', 'feature-implementation', 'feature-implementation',
      'module-design', 'project-document', 'project-document',
    ]);
  });

  it('projects sorted relative paths and repeatable route inventory without real paths', async () => {
    const root = resolve(__dirname, '../fixtures/valid-project');
    const first = createManifest(await buildRegistry(root));
    const second = createManifest(await buildRegistry(root));
    expect(first.schemaVersion).toBe(7);
    expect(first.generator).toEqual({name: 'concorde-docsite', version: '0.3.0', docusaurusVersion: '3.10.2'});
    expect(first.collections.map((collection) => collection.id)).toEqual([
      'architecture', 'docs', 'feature-abstracts', 'features', 'feature-implementations',
    ]);
    expect(first.collections.map((collection) => collection.include)).toEqual([
      ['**/module.md', '**/design.md', '**/contracts/**/contract.md'], ['**/*.md'], ['**/abstract.md'], ['**/design.md'], ['**/implementation.md'],
    ]);
    expect(second).toEqual(first);
    expect(first.pages.map((page) => page.sourcePath)).toEqual([...first.pages.map((page) => page.sourcePath)].sort());
    expect(first.routeInventory).toEqual([...first.routeInventory].sort());
    expect(JSON.stringify(first)).not.toContain(root);
    expect(JSON.stringify(first)).not.toContain('realPath');
  });
});
