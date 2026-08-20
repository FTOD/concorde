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
  });

  it('projects sorted relative paths and repeatable route inventory without real paths', async () => {
    const root = resolve(__dirname, '../fixtures/valid-project');
    const first = createManifest(await buildRegistry(root));
    const second = createManifest(await buildRegistry(root));
    expect(second).toEqual(first);
    expect(first.pages.map((page) => page.sourcePath)).toEqual([...first.pages.map((page) => page.sourcePath)].sort());
    expect(first.routeInventory).toEqual([...first.routeInventory].sort());
    expect(JSON.stringify(first)).not.toContain(root);
    expect(JSON.stringify(first)).not.toContain('realPath');
  });
});
