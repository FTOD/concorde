import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {createManifest} from '../../plugins/concorde-content/manifest';
import {buildRegistry} from '../../plugins/concorde-content/registry';
import type {ModuleArchitecture} from '../../plugins/concorde-content/types';
import {validateRegistry} from '../../plugins/concorde-content/validation';

const projectRoot = resolve(__dirname, '../../..');

describe('maintained Concorde specification documentation', () => {
  it('keeps README as repository orientation but outside publication', async () => {
    const [readme, registry] = await Promise.all([
      readFile(resolve(projectRoot, 'README.md'), 'utf8'),
      buildRegistry(projectRoot),
    ]);
    expect(readme).toContain('## The model');
    expect(readme).toContain('## Leaf Skills and Operations');
    expect(registry.documents.some((document) => document.sourcePath === 'README.md')).toBe(false);
    expect(createManifest(registry).pages.some((page) => page.sourcePath === 'README.md')).toBe(false);
  });

  it('publishes exactly the maintained architecture and direct feature specifications', async () => {
    const registry = await buildRegistry(projectRoot);
    expect(validateRegistry(registry)).toEqual([]);
    expect(registry.collections.map((collection) => collection.id)).toEqual(['architecture', 'features']);
    expect(registry.documents).toHaveLength(33);
    expect(registry.documents.filter((document) => document.contentKind === 'module-architecture')).toHaveLength(7);
    expect(registry.documents.filter((document) => document.contentKind === 'feature-design')).toHaveLength(26);
    expect(registry.documents.every((document) => document.sourcePath.startsWith('specs/'))).toBe(true);
  });

  it('carries migrated workflow, capability, ontology, and publication guidance in owning specs', async () => {
    const registry = await buildRegistry(projectRoot);
    const source = (path: string) => registry.documents.find((document) => document.sourcePath === path)?.content ?? '';
    expect(source('specs/concorde/features/001-concorde-workflow.md')).toContain('concorde-standard-dev-loop');
    const skills = source('specs/concorde/modules/capabilities/features/002-provide-capability-surfaces.md').toLowerCase();
    expect(skills).toContain('concorde-ask');
    expect(skills).toContain('read-only');
    expect(skills).toContain('protocol 13');
    expect(source('specs/concorde/features/002-project-ontology.md')).toContain('## Target Specification Model');
    const publication = source('specs/concorde/modules/auto-docs/features/001-publish-project-docsite.md');
    expect(publication).toContain('docsite/site.json');
    expect(publication).toContain('parallel prose authority');
  });

  it('does not present temporal or framework control state as permanent publication authority', async () => {
    const manifest = createManifest(await buildRegistry(projectRoot));
    expect(manifest.pages.some((page) => page.sourcePath.startsWith('.concorde/'))).toBe(false);
    expect(manifest.excludedSources.some((source) => source.sourcePath.startsWith('.concorde/'))).toBe(false);
  });

  it('publishes one Archify system overview on every module architecture', async () => {
    const registry = await buildRegistry(projectRoot);
    const architecturePages = registry.documents.filter(
      (document): document is ModuleArchitecture => document.contentKind === 'module-architecture',
    );
    expect(architecturePages).toHaveLength(7);
    expect(architecturePages.every((document) => document.architectureDiagrams.length === 1)).toBe(true);
    expect(architecturePages.flatMap((document) => document.architectureDiagrams)
      .every((diagram) => diagram.kind === 'architecture' && diagram.source.endsWith('/diagrams/system-overview.json'))).toBe(true);
    expect(registry.documents.filter((document) => document.contentKind !== 'module-architecture')
      .every((document) => !('architectureDiagrams' in document))).toBe(true);
  });
});
