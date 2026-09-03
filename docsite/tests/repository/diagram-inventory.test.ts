import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

import fg from 'fast-glob';
import {describe, expect, it} from 'vitest';

import {discoverDiagramDeclarations} from '../../plugins/concorde-content/diagrams';

const projectRoot = resolve(__dirname, '../../..');

async function hashes(root: string) {
  const paths = (await fg([
    'README.md', 'docs/**/*.{json,md}', 'specs/**/*.{json,md}',
    '.concorde/config.json', '.concorde/attempts/**/*.{json,md}', '.concorde/reflections/**/*.{json,md}',
  ], {cwd: root, dot: true})).sort();
  return Promise.all(paths.map(async (path) => [path, createHash('sha256').update(await readFile(resolve(root, path))).digest('hex')]));
}

describe('Concorde repository diagram inventory', () => {
  it('discovers one architecture-owned system overview per real module', async () => {
    const declarations = await discoverDiagramDeclarations(projectRoot);
    expect(declarations).toHaveLength(7);
    expect(declarations.every((item) => item.sourcePath.endsWith('/diagrams/system-overview.json'))).toBe(true);
    expect(declarations.every((item) => item.kind === 'architecture')).toBe(true);
    expect(declarations.every((item) => item.ownerPath.endsWith('/architecture.md'))).toBe(true);
    expect(declarations.map((item) => item.sourcePath)).toEqual(
      [...declarations.map((item) => item.sourcePath)].sort(),
    );
    expect(new Set(declarations.map((item) => item.outputPath)).size).toBe(declarations.length);
    expect(declarations.every((item) => item.outputPath.startsWith('generated/architecture/'))).toBe(true);
  });

  it('discovery does not mutate canonical sources', async () => {
    const before = await hashes(projectRoot);
    expect(await discoverDiagramDeclarations(projectRoot)).toHaveLength(7);
    expect(await hashes(projectRoot)).toEqual(before);
  });
});
