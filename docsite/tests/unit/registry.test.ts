import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {createManifest} from '../../plugins/concorde-content/manifest';
import {buildRegistry} from '../../plugins/concorde-content/registry';
import {validateRegistry} from '../../plugins/concorde-content/validation';

const fixture = resolve(__dirname, '../fixtures/valid-project');

describe('content registry', () => {
  it('discovers all four collections with unique routes and stable source ordering', async () => {
    const registry = await buildRegistry(fixture);
    expect(validateRegistry(registry)).toEqual([]);
    expect(registry.documents.map((item) => item.sourcePath)).toEqual([
      'docs/guide/intro.md', 'docs/index.md', 'specs/001-alpha/design.md',
      'specs/001-alpha/spec.md',
      'specs/001-alpha/subfeatures/001-prepare/design.md',
      'specs/001-alpha/subfeatures/001-prepare/spec.md',
      'specs/001-alpha/subfeatures/002-finish/design.md',
      'specs/001-alpha/subfeatures/002-finish/spec.md',
      'specs/example/module.md',
      'specs/nested/002-beta/design.md', 'specs/nested/002-beta/spec.md',
    ]);
    expect(new Set(registry.documents.map((item) => item.route)).size).toBe(11);
    expect(registry.documents.every((item) => item.sourceSha256.length === 64)).toBe(true);
  });

  it('projects exactly one navigation record per included page', async () => {
    const registry = await buildRegistry(fixture);
    const manifest = createManifest(registry);
    expect(manifest.pages).toHaveLength(registry.documents.length);
    expect(manifest.pages.map((page) => page.navigation.section)).toEqual([
      'Documentation', 'Documentation', 'Features', 'Features', 'Features', 'Features', 'Features',
      'Features', 'Architecture', 'Features', 'Features',
    ]);
  });
});
