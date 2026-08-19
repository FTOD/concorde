import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {createManifest} from '../../plugins/concorde-content/manifest';
import {buildRegistry} from '../../plugins/concorde-content/registry';
import {validateRegistry} from '../../plugins/concorde-content/validation';

const fixture = resolve(__dirname, '../fixtures/valid-project');

describe('content registry', () => {
  it('discovers all three collections with unique routes and stable source ordering', async () => {
    const registry = await buildRegistry(fixture);
    expect(validateRegistry(registry)).toEqual([]);
    expect(registry.documents.map((item) => item.sourcePath)).toEqual([
      'architecture/example/module.md', 'docs/guide/intro.md', 'docs/index.md',
      'specs/001-alpha/spec.md', 'specs/nested/002-beta/spec.md',
    ]);
    expect(new Set(registry.documents.map((item) => item.route)).size).toBe(5);
    expect(registry.documents.every((item) => item.sourceSha256.length === 64)).toBe(true);
  });

  it('projects exactly one navigation record per included page', async () => {
    const registry = await buildRegistry(fixture);
    const manifest = createManifest(registry);
    expect(manifest.pages).toHaveLength(registry.documents.length);
    expect(manifest.pages.map((page) => page.navigation.section)).toEqual([
      'Architecture', 'Documentation', 'Documentation', 'Features', 'Features',
    ]);
  });
});
