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
      architectureViewSource: 'specs/concorde/architecture.json',
      architectureViewRoute: '/architecture/concorde-root.html',
    });
    expect(sources.find((source) => source.architectureId === 'module.concorde.documentation')).toMatchObject({
      parentId: 'module.concorde',
      architectureViewRoute: '/architecture/documentation.html',
    });
    expect(sources.find((source) => source.architectureId === 'contract.integration.feature-workspace')).toMatchObject({
      architectureKind: 'contract',
      moduleId: 'module.concorde.spec-kit-integration',
    });
  });

  it('publishes a logical view route without requiring pre-generated HTML', async () => {
    const projectRoot = await mkdtemp(resolve(tmpdir(), 'concorde-architecture-'));
    try {
      await mkdir(resolve(projectRoot, 'specs/example'), {recursive: true});
      await writeFile(resolve(projectRoot, 'specs/example/module.md'), `---
id: module.example
kind: module
parent: null
view: specs/example/missing.json
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
`, 'utf8');
      await writeFile(resolve(projectRoot, 'specs/example/design.md'), '# Design Reference: Example\n\n## Implementation Notes\n\nSeed.\n', 'utf8');
      await writeFile(resolve(projectRoot, 'specs/example/missing.json'), JSON.stringify({
        diagram_type: 'architecture',
        meta: {title: 'Example', output: '../../generated/architecture/example.html'},
      }), 'utf8');
      const registry = await buildRegistry(projectRoot);
      expect(validateRegistry(registry)).toEqual([]);
      const source = registry.documents.find((document) => document.contentKind === 'architecture-source') as ArchitectureSource;
      expect(source.architectureViewRoute).toBe('/architecture/example.html');
      expect(source.designReferenceRoute).toBe('/architecture/example/design');
    } finally {
      await rm(projectRoot, {recursive: true, force: true});
    }
  });
});
