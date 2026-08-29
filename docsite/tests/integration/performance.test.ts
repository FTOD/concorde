import {mkdir, mkdtemp, rm, writeFile} from 'node:fs/promises';
import {performance} from 'node:perf_hooks';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';

import {afterEach, expect, it} from 'vitest';

import {buildRegistry} from '../../plugins/concorde-content/registry';
import {validateRegistry} from '../../plugins/concorde-content/validation';

const roots: string[] = [];
afterEach(async () => Promise.all(roots.splice(0).map((root) => rm(root, {recursive: true, force: true}))));

it('discovers and validates 1,000 documents and 250 three-page feature roots within five seconds', async () => {
  const root = await mkdtemp(resolve(tmpdir(), 'concorde-scale-')); roots.push(root);
  await Promise.all([
    ...Array.from({length: 1000}, async (_, index) => {
      const dir = resolve(root, 'docs', String(Math.floor(index / 100))); await mkdir(dir, {recursive: true});
      await writeFile(resolve(dir, `${index}.md`), `# Document ${index}\n`);
    }),
    ...Array.from({length: 250}, async (_, index) => {
      const dir = resolve(root, 'specs', String(index).padStart(3, '0')); await mkdir(dir, {recursive: true});
      await writeFile(resolve(dir, 'abstract.md'), `# Feature Abstract: Feature ${index}\n\n## Purpose\n\nScale.\n\n## Functionality\n\nScale.\n\n## Structure\n\nScale.\n\n## Logic\n\nScale.\n\n## Read Next\n\n- [design.md](design.md) and [implementation.md](implementation.md).\n`);
      await writeFile(resolve(dir, 'design.md'), `---\nid: feature.scale.${index}\nkind: feature\nmodule: module.scale\n---\n# Feature Design: Feature ${index}\n\n**Status**: Draft\n`);
      await writeFile(resolve(dir, 'implementation.md'), `# Feature Implementation: Feature ${index}\n`);
    }),
  ]);
  const start = performance.now();
  const registry = await buildRegistry(root);
  expect(validateRegistry(registry)).toEqual([]);
  expect(registry.documents).toHaveLength(1750);
  expect(performance.now() - start).toBeLessThan(5000);
}, 20_000);
