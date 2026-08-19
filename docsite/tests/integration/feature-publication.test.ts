import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {createManifest} from '../../plugins/concorde-content/manifest';
import {buildRegistry} from '../../plugins/concorde-content/registry';

describe('canonical feature publication', () => {
  it('includes spec.md recursively and records other Markdown as excluded', async () => {
    const registry = await buildRegistry(resolve(__dirname, '../fixtures/valid-project'));
    const manifest = createManifest(registry);
    expect(manifest.pages.filter((page) => page.kind === 'feature-specification')).toHaveLength(2);
    expect(manifest.pages.some((page) => page.sourcePath.endsWith('/plan.md'))).toBe(false);
    expect(manifest.excludedSources).toEqual([
      {sourcePath: 'specs/001-alpha/plan.md', reason: 'not-canonical-feature-artifact'},
    ]);
  });
});
