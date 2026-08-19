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
      (document): document is ArchitectureSource => document.collectionId === 'architecture',
    );
    expect(validateRegistry(registry)).toEqual([]);
    expect(sources).toHaveLength(12);
    expect(new Set(sources.map((source) => source.architectureId)).size).toBe(sources.length);
    expect(sources.find((source) => source.architectureId === 'module.concorde')).toMatchObject({
      architectureKind: 'module',
      architectureViewSource: 'architecture/concorde/architecture.json',
      architectureViewRoute: '/architecture/concorde-root.html',
    });
    expect(sources.find((source) => source.architectureId === 'module.concorde.documentation')).toMatchObject({
      parentId: 'module.concorde',
      architectureViewRoute: '/architecture/documentation.html',
    });
  });

  it('rejects a declared view without a deliverable generated artifact', async () => {
    const projectRoot = await mkdtemp(resolve(tmpdir(), 'concorde-architecture-'));
    try {
      await mkdir(resolve(projectRoot, 'architecture/example'), {recursive: true});
      await writeFile(resolve(projectRoot, 'architecture/example/module.md'), `---
id: module.example
kind: module
parent: null
view: architecture/example/missing.json
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
      const findings = validateRegistry(await buildRegistry(projectRoot));
      expect(findings.map((finding) => finding.ruleId)).toContain('architecture.view.unpublishable');
    } finally {
      await rm(projectRoot, {recursive: true, force: true});
    }
  });
});
