import {mkdtemp, mkdir, readFile, rm, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';

import {afterEach, describe, expect, it} from 'vitest';

import {promoteCandidate} from '../../scripts/build';

const roots: string[] = [];
afterEach(async () => Promise.all(roots.splice(0).map((root) => rm(root, {recursive: true, force: true}))));

describe('atomic candidate promotion', () => {
  it('replaces successful output and removes stale backup content', async () => {
    const root = await mkdtemp(resolve(tmpdir(), 'concorde-promote-')); roots.push(root);
    const candidate = resolve(root, 'candidate'); const build = resolve(root, 'build'); const backup = resolve(root, 'backup');
    await mkdir(candidate); await mkdir(build); await mkdir(backup);
    await writeFile(resolve(candidate, 'version'), 'new'); await writeFile(resolve(build, 'version'), 'old');
    await writeFile(resolve(backup, 'stale'), 'stale');
    await promoteCandidate(candidate, build, backup);
    expect(await readFile(resolve(build, 'version'), 'utf8')).toBe('new');
    await expect(readFile(resolve(backup, 'stale'), 'utf8')).rejects.toThrow();
  });

  it('rolls back when candidate promotion fails', async () => {
    const root = await mkdtemp(resolve(tmpdir(), 'concorde-rollback-')); roots.push(root);
    const build = resolve(root, 'build'); await mkdir(build); await writeFile(resolve(build, 'version'), 'old');
    await expect(promoteCandidate(resolve(root, 'missing'), build, resolve(root, 'backup'))).rejects.toThrow();
    expect(await readFile(resolve(build, 'version'), 'utf8')).toBe('old');
  });
});
