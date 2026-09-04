import {mkdir, mkdtemp, rm, writeFile} from 'node:fs/promises';
import {performance} from 'node:perf_hooks';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';

import {afterEach, expect, it} from 'vitest';

import {buildRegistry} from '../../plugins/concorde-content/registry';
import {validateRegistry} from '../../plugins/concorde-content/validation';

const roots: string[] = [];
afterEach(async () => Promise.all(roots.splice(0).map((root) => rm(root, {recursive: true, force: true}))));

it('discovers and validates 1,000 architecture/feature specifications within five seconds', async () => {
  const root = await mkdtemp(resolve(tmpdir(), 'concorde-scale-')); roots.push(root);
  await Promise.all([
    (async () => {
      await mkdir(resolve(root, 'specs/scale'), {recursive: true});
      await writeFile(resolve(root, 'specs/scale/architecture.md'), `---\nid: module.scale\nkind: module\nparent: null\nmodules:\n${Array.from({length: 749}, (_, index) => `  - module.scale.m${index}`).join('\n')}\nfeatures:\n${Array.from({length: 250}, (_, index) => `  - feature.scale.${index}`).join('\n')}\n---\n# Scale Architecture\n`);
    })(),
    ...Array.from({length: 749}, async (_, index) => {
      const dir = resolve(root, 'specs/scale/modules', `m${index}`); await mkdir(dir, {recursive: true});
      await writeFile(resolve(dir, 'architecture.md'), `---\nid: module.scale.m${index}\nkind: module\nparent: module.scale\nmodules: []\nfeatures: []\n---\n# Module ${index}\n`);
    }),
    ...Array.from({length: 250}, async (_, index) => {
      const dir = resolve(root, 'specs/scale/features'); await mkdir(dir, {recursive: true});
      await writeFile(resolve(dir, `${String(index).padStart(3, '0')}-feature.md`), `---\nid: feature.scale.${index}\nkind: feature\nmodule: module.scale\nrelated_features: []\n---\n# Feature Design: Feature ${index}\n\n## Outcome\n\nScale.\n`);
    }),
  ]);
  const start = performance.now();
  const registry = await buildRegistry(root);
  expect(validateRegistry(registry)).toEqual([]);
  expect(registry.documents).toHaveLength(1000);
  expect(performance.now() - start).toBeLessThan(5000);
}, 20_000);
