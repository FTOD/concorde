import {mkdtemp, mkdir, rm, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {buildRegistry} from '../../plugins/concorde-content/registry';
import {validateRegistry} from '../../plugins/concorde-content/validation';
import type {ArchitectureSource} from '../../plugins/concorde-content/types';

describe('architecture source publication', () => {
  it('publishes the real hierarchy with stable identities and delivered views', async () => {
    const projectRoot = resolve(__dirname, '../../..');
    const registry = await buildRegistry(projectRoot);
    const sources = registry.documents.filter(
      (document): document is ArchitectureSource => document.contentKind === 'architecture-source',
    );
    expect(validateRegistry(registry)).toEqual([]);
    expect(sources).toHaveLength(21);
    expect(new Set(sources.map((source) => source.architectureId)).size).toBe(sources.length);
    expect(sources.find((source) => source.architectureId === 'module.concorde')).toMatchObject({
      architectureKind: 'module',
      route: '/architecture/concorde/module.concorde',
      architectureDiagrams: [expect.objectContaining({
        source: 'specs/concorde/architecture/diagrams/level-view.json',
        kind: 'architecture',
        route: '/architecture/concorde-root.html',
      })],
    });
    expect(sources.find((source) => source.architectureId === 'module.concorde.documentation')).toMatchObject({
      parentId: 'module.concorde',
      sourcePath: 'specs/concorde/architecture/modules/documentation/module.md',
      route: '/architecture/concorde/modules/documentation/module.concorde.documentation',
      architectureDiagrams: [expect.objectContaining({route: '/architecture/documentation.html'})],
    });
    expect(sources.find((source) => source.architectureId === 'contract.integration.feature-workspace')).toMatchObject({
      architectureKind: 'contract',
      moduleId: 'module.concorde.spec-kit-integration',
    });
  });

  it('publishes logical routes for every module diagram without requiring pre-generated HTML', async () => {
    const projectRoot = await mkdtemp(resolve(tmpdir(), 'concorde-architecture-'));
    try {
      await mkdir(resolve(projectRoot, 'specs/example/architecture/diagrams'), {recursive: true});
      await writeFile(resolve(projectRoot, 'specs/example/module.md'), `---
id: module.example
kind: module
parent: null
children: []
features: []
contracts:
  provided: []
  required: []
---

# Example

## Responsibility

Exercise declared-view validation.

## Boundary

No child modules.

## Structure

The level view is [level-view.json](architecture/diagrams/level-view.json); the
[release flow](architecture/diagrams/release-flow.json) explains publication order.
`, 'utf8');
      await writeFile(resolve(projectRoot, 'specs/example/design.md'), '# Design Reference: Example\n\n## Implementation Notes\n\nSeed.\n', 'utf8');
      await writeFile(resolve(projectRoot, 'specs/example/architecture/diagrams/level-view.json'), JSON.stringify({
        diagram_type: 'architecture',
        meta: {title: 'Example', output: '../../../../generated/architecture/example.html'},
      }), 'utf8');
      await writeFile(resolve(projectRoot, 'specs/example/architecture/diagrams/release-flow.json'), JSON.stringify({
        diagram_type: 'sequence',
        meta: {title: 'Release flow', output: '../../../../generated/architecture/example-release-flow.html'},
      }), 'utf8');
      const registry = await buildRegistry(projectRoot);
      expect(validateRegistry(registry)).toEqual([]);
      const source = registry.documents.find((document) => document.contentKind === 'architecture-source') as ArchitectureSource;
      expect(source.architectureDiagrams).toEqual([
        expect.objectContaining({source: 'specs/example/architecture/diagrams/level-view.json', kind: 'architecture', route: '/architecture/example.html'}),
        expect.objectContaining({source: 'specs/example/architecture/diagrams/release-flow.json', kind: 'sequence', route: '/architecture/example-release-flow.html'}),
      ]);
      expect(source.links.filter((link) => link.kind === 'included-source').map((link) => link.targetRoute)).toEqual([
        '/architecture/example.html', '/architecture/example-release-flow.html',
      ]);
      expect(source.designReferenceRoute).toBe('/architecture/example/design');
    } finally {
      await rm(projectRoot, {recursive: true, force: true});
    }
  });
});
