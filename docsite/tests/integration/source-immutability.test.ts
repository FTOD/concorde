import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

import fg from 'fast-glob';
import {describe, expect, it} from 'vitest';

import {buildRegistry} from '../../plugins/concorde-content/registry';
import {discoverDiagramDeclarations} from '../../plugins/concorde-content/diagrams';
import {assertValidRegistry} from '../../plugins/concorde-content/validation';

async function hashes(root: string) {
  const paths = (await fg([
    'README.md', 'docs/**/*.{json,md}', 'specs/**/*.{json,md}',
    '.concorde/config.json', '.concorde/attempts/**/*.{json,md}', '.concorde/reflections/log.md',
  ], {cwd: root, dot: true})).sort();
  return Promise.all(paths.map(async (path) => [path, createHash('sha256').update(await readFile(resolve(root, path))).digest('hex')]));
}

it('validation does not mutate canonical sources', async () => {
  const root = resolve(__dirname, '../fixtures/valid-project');
  const before = await hashes(root);
  assertValidRegistry(await buildRegistry(root));
  expect(await hashes(root)).toEqual(before);
});

it('diagram declaration discovery does not mutate canonical sources', async () => {
  const root = resolve(__dirname, '../../..');
  const before = await hashes(root);
  expect(await discoverDiagramDeclarations(root)).toHaveLength(6);
  expect(await hashes(root)).toEqual(before);
});
