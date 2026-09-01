import {cp, mkdtemp, readFile, rename, rm, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';

import {afterEach, describe, expect, it} from 'vitest';

import {buildRegistry} from '../../plugins/concorde-content/registry';

const roots: string[] = [];
afterEach(async () => Promise.all(roots.splice(0).map((root) => rm(root, {recursive: true, force: true}))));

describe('documentation authoring', () => {
  it('reflects add, rename, hierarchy, and removal without docsite registration', async () => {
    const root = await mkdtemp(resolve(tmpdir(), 'concorde-authoring-')); roots.push(root);
    await cp(resolve(__dirname, '../fixtures/valid-project'), root, {recursive: true});
    await writeFile(resolve(root, 'docs/guide/new.md'), '# New page\n', 'utf8');
    expect((await buildRegistry(root)).documents.some((item) => item.route === '/docs/guide/new')).toBe(true);
    await rename(resolve(root, 'docs/guide/new.md'), resolve(root, 'docs/guide/renamed.md'));
    expect((await buildRegistry(root)).documents.some((item) => item.route === '/docs/guide/renamed')).toBe(true);
    await rm(resolve(root, 'docs/guide/renamed.md'));
    expect((await buildRegistry(root)).documents.some((item) => item.route.endsWith('/renamed'))).toBe(false);
  });

  it('reflects terminology table edits without a parallel registry', async () => {
    const root = await mkdtemp(resolve(tmpdir(), 'concorde-terminology-')); roots.push(root);
    await cp(resolve(__dirname, '../fixtures/valid-project'), root, {recursive: true});
    const design = resolve(root, 'specs/001-alpha/design.md');
    const original = await readFile(design, 'utf8');
    await writeFile(design, `${original}\n\n## Terminology\n\n| Term | Meaning | Relationships |\n|---|---|---|\n| \`Alpha input\` | One prepared input. | None |\n`, 'utf8');
    const registry = await buildRegistry(root);
    const feature = registry.documents.find((item) => item.sourcePath === 'specs/001-alpha/design.md');
    expect(feature?.content).toContain('## Terminology');
    expect(feature?.content).toContain('`Alpha input`');
  });
});
