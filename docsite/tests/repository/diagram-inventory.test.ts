import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

import fg from 'fast-glob';
import {describe, expect, it} from 'vitest';

import {discoverDiagramDeclarations} from '../../plugins/concorde-content/diagrams';

const projectRoot = resolve(__dirname, '../../..');

async function hashes(root: string) {
  const paths = (await fg([
    'specs/**/*.{json,md}',
    '.concorde/config.json', '.concorde/attempts/**/*.{json,md}', '.concorde/reflections/**/*.{json,md}',
  ], {cwd: root, dot: true})).sort();
  return Promise.all(paths.map(async (path) => [path, createHash('sha256').update(await readFile(resolve(root, path))).digest('hex')]));
}

describe('Concorde repository diagram inventory', () => {
  it('discovers module overviews and the root concept/dataflow views', async () => {
    const declarations = await discoverDiagramDeclarations(projectRoot);
    expect(declarations).toHaveLength(9);
    const overviews = declarations.filter((item) => item.sourcePath.endsWith('/diagrams/system-overview.json'));
    expect(overviews).toHaveLength(7);
    expect(new Set(overviews.map((item) => item.ownerPath)).size).toBe(7);
    expect(overviews.every((item) => item.kind === 'architecture')).toBe(true);
    expect(declarations).toEqual(expect.arrayContaining([
      expect.objectContaining({
        sourcePath: 'specs/concorde/diagrams/operation-dataflow.json',
        ownerPath: 'specs/concorde/architecture.md', kind: 'dataflow',
      }),
      expect.objectContaining({
        sourcePath: 'specs/concorde/diagrams/module-collaboration.json',
        ownerPath: 'specs/concorde/architecture.md', kind: 'architecture',
      }),
    ]));
    expect(declarations.every((item) => item.ownerPath.endsWith('/architecture.md'))).toBe(true);
    expect(declarations.map((item) => item.sourcePath)).toEqual(
      [...declarations.map((item) => item.sourcePath)].sort(),
    );
    expect(new Set(declarations.map((item) => item.outputPath)).size).toBe(declarations.length);
    expect(declarations.every((item) => item.outputPath.startsWith('generated/architecture/'))).toBe(true);
  });

  it('discovery does not mutate canonical sources', async () => {
    const before = await hashes(projectRoot);
    expect(await discoverDiagramDeclarations(projectRoot)).toHaveLength(9);
    expect(await hashes(projectRoot)).toEqual(before);
  });
});
