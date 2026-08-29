import {mkdir, mkdtemp, readFile, rm, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';

import {afterEach, describe, expect, it} from 'vitest';

import {discoverDiagramDeclarations} from '../../plugins/concorde-content/diagrams';
import {atomicReplaceDirectory, resolveArchifyPackage} from '../../scripts/render-diagrams';

const roots: string[] = [];

afterEach(async () => {
  await Promise.all(roots.splice(0).map((root) => rm(root, {recursive: true, force: true})));
});

async function temporaryRoot(prefix: string): Promise<string> {
  const root = await mkdtemp(resolve(tmpdir(), prefix));
  roots.push(root);
  return root;
}

async function writeModuleDiagram(
  root: string,
  moduleName: string,
  output: string,
  diagramType = 'architecture',
): Promise<void> {
  const directory = resolve(root, 'specs', moduleName);
  await mkdir(resolve(directory, 'architecture/diagrams'), {recursive: true});
  await writeFile(resolve(directory, 'module.md'), `---
id: module.${moduleName}
kind: module
parent: null
children: []
features: []
contracts:
  provided: []
  required: []
---
# ${moduleName}
`, 'utf8');
  await writeFile(resolve(directory, 'architecture/diagrams/level-view.json'), `${JSON.stringify({
    schema_version: 1,
    diagram_type: diagramType,
    meta: {title: moduleName, output, quality_profile: 'showcase'},
    components: [], boundaries: [], connections: [], cards: [],
  }, null, 2)}\n`, 'utf8');
}

describe('diagram declaration discovery', () => {
  it('discovers the nine real declarations in stable source order without generated HTML', async () => {
    const projectRoot = resolve(__dirname, '../../..');
    const declarations = await discoverDiagramDeclarations(projectRoot);
    expect(declarations).toHaveLength(9);
    expect(declarations.map((item) => item.sourcePath)).toEqual(
      [...declarations.map((item) => item.sourcePath)].sort(),
    );
    expect(new Set(declarations.map((item) => item.outputPath)).size).toBe(9);
    expect(declarations.every((item) => item.outputPath.startsWith('generated/architecture/'))).toBe(true);
  });

  it('rejects duplicate normalized outputs before delivery', async () => {
    const root = await temporaryRoot('concorde-diagram-duplicate-');
    await writeModuleDiagram(root, 'one', '../../../../generated/architecture/shared.html');
    await writeModuleDiagram(root, 'two', '../../../../generated/architecture/shared.html');
    await expect(discoverDiagramDeclarations(root)).rejects.toThrow(/duplicate output.*shared\.html/i);
  });

  it('accepts every supported diagram kind beneath architecture/diagrams/ and rejects unsupported kinds or escaping outputs', async () => {
    const kindRoot = await temporaryRoot('concorde-diagram-kind-');
    await writeModuleDiagram(kindRoot, 'kind', '../../../../generated/architecture/kind.html', 'sequence');
    expect((await discoverDiagramDeclarations(kindRoot)).map((item) => [item.sourcePath, item.kind])).toEqual([
      ['specs/kind/architecture/diagrams/level-view.json', 'sequence'],
    ]);

    const unsupportedRoot = await temporaryRoot('concorde-diagram-unsupported-');
    await writeModuleDiagram(unsupportedRoot, 'odd', '../../../../generated/architecture/odd.html', 'mindmap');
    await expect(discoverDiagramDeclarations(unsupportedRoot)).rejects.toThrow(/specs\/odd\/architecture\/diagrams\/level-view\.json.*diagram_type/i);

    const escapeRoot = await temporaryRoot('concorde-diagram-escape-');
    await writeModuleDiagram(escapeRoot, 'escape', '../../../../../outside.html');
    await expect(discoverDiagramDeclarations(escapeRoot)).rejects.toThrow(/specs\/escape\/architecture\/diagrams\/level-view\.json.*generated/i);
  });
});

describe('Archify package contract', () => {
  it('requires the project-local installed skill', async () => {
    const root = await temporaryRoot('concorde-archify-missing-');
    await expect(resolveArchifyPackage(root)).rejects.toThrow(/\.agents\/skills\/archify/);
  });

  it('rejects an incompatible package before invoking its bin', async () => {
    const root = await temporaryRoot('concorde-archify-package-');
    const archify = resolve(root, '.agents/skills/archify');
    await mkdir(resolve(archify, 'bin'), {recursive: true});
    await writeFile(resolve(archify, 'bin/archify.mjs'), '', 'utf8');
    await writeFile(resolve(archify, 'package.json'), JSON.stringify({
      name: 'archify', version: '2.13.0', bin: {archify: './bin/archify.mjs'},
    }), 'utf8');
    await expect(resolveArchifyPackage(root)).rejects.toThrow(/2\.16\.0-dev\.0/);
  });

  it('rejects project-local Archify without the supported installer lock', async () => {
    const root = await temporaryRoot('concorde-archify-unlocked-');
    const archify = resolve(root, '.agents/skills/archify');
    await mkdir(resolve(archify, 'bin'), {recursive: true});
    await writeFile(resolve(archify, 'bin/archify.mjs'), '', 'utf8');
    await writeFile(resolve(archify, 'package.json'), JSON.stringify({
      name: 'archify', version: '2.16.0-dev.0', bin: {archify: './bin/archify.mjs'},
    }), 'utf8');
    await expect(resolveArchifyPackage(root)).rejects.toThrow(/skills-lock\.json/);
  });
});

describe('atomic diagram-set promotion', () => {
  it('replaces a complete set and removes stale files', async () => {
    const root = await temporaryRoot('concorde-diagram-promote-');
    const candidate = resolve(root, 'candidate');
    const destination = resolve(root, 'generated');
    const backup = resolve(root, 'backup');
    await mkdir(resolve(candidate, 'architecture'), {recursive: true});
    await mkdir(resolve(destination, 'architecture'), {recursive: true});
    await writeFile(resolve(candidate, 'architecture/current.html'), 'current', 'utf8');
    await writeFile(resolve(destination, 'architecture/stale.html'), 'stale', 'utf8');

    await atomicReplaceDirectory(candidate, destination, backup);

    expect(await readFile(resolve(destination, 'architecture/current.html'), 'utf8')).toBe('current');
    await expect(readFile(resolve(destination, 'architecture/stale.html'), 'utf8')).rejects.toThrow();
  });
});
