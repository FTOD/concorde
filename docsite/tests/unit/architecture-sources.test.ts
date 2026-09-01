import {mkdtemp, mkdir, rm, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {buildRegistry} from '../../plugins/concorde-content/registry';
import {validateRegistry} from '../../plugins/concorde-content/validation';
import type {ModuleArchitecture} from '../../plugins/concorde-content/types';

describe('module architecture publication', () => {
  it('uses each architecture.md as its module landing page and diagram owner', async () => {
    const registry = await buildRegistry(resolve(__dirname, '../fixtures/valid-project'));
    const modules = registry.documents.filter(
      (document): document is ModuleArchitecture => document.contentKind === 'module-architecture',
    );
    expect(validateRegistry(registry)).toEqual([]);
    expect(modules.map((module) => module.moduleId)).toEqual(['module.fixture', 'module.fixture.nested']);
    expect(modules[0]).toMatchObject({
      route: '/architecture/module.fixture', moduleIds: ['module.fixture.nested'],
      featureIds: ['feature.fixture.alpha'],
      architectureDiagrams: [expect.objectContaining({
        source: 'specs/example/diagrams/fixture-level-view.json',
        route: '/architecture/fixture-level-view.html',
      })],
    });
  });

  it('discovers every architecture-owned diagram directly beneath the module diagrams directory', async () => {
    const root = await mkdtemp(resolve(tmpdir(), 'concorde-architecture-'));
    try {
      await mkdir(resolve(root, 'specs/example/diagrams'), {recursive: true});
      await writeFile(resolve(root, 'README.md'), '# Example\n');
      await writeFile(resolve(root, 'specs/example/architecture.md'), `---\nid: module.example\nkind: module\nparent: null\nmodules: []\nfeatures: []\n---\n# Example\n\n[View](diagrams/view.json)\n`);
      await writeFile(resolve(root, 'specs/example/diagrams/view.json'), JSON.stringify({
        schema_version: 1, diagram_type: 'architecture',
        meta: {title: 'Example View', output: '../../../generated/architecture/example.html', quality_profile: 'showcase', legend: {mode: 'hidden'}},
      }));
      const registry = await buildRegistry(root);
      expect(validateRegistry(registry)).toEqual([]);
      const module = registry.documents.find((item) => item.contentKind === 'module-architecture') as ModuleArchitecture;
      expect(module.architectureDiagrams).toEqual([expect.objectContaining({
        source: 'specs/example/diagrams/view.json', route: '/architecture/example.html',
      })]);
      expect(module.links).toContainEqual(expect.objectContaining({
        targetSourcePath: 'specs/example/diagrams/view.json', targetRoute: '/architecture/example.html',
      }));
    } finally {
      await rm(root, {recursive: true, force: true});
    }
  });
});
