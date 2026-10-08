import {chmod, mkdtemp, mkdir, readFile, readdir, rm, stat, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';

import {afterEach, describe, expect, it, vi} from 'vitest';

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

  it('preserves output when the initial backup rename fails', async () => {
    const root = await mkdtemp(resolve(tmpdir(), 'concorde-backup-failure-')); roots.push(root);
    const candidate = resolve(root, 'candidate'); const build = resolve(root, 'build');
    await mkdir(candidate); await mkdir(build);
    await writeFile(resolve(candidate, 'version'), 'new'); await writeFile(resolve(build, 'version'), 'old');
    await expect(promoteCandidate(candidate, build, resolve(build, 'nested-backup'))).rejects.toThrow();
    expect(await readFile(resolve(build, 'version'), 'utf8')).toBe('old');
    expect(await readFile(resolve(candidate, 'version'), 'utf8')).toBe('new');
  });
  // verifies: scenario.views.first-publication
  it('publishes the first site when no destination exists', async () => {
    const root = await mkdtemp(resolve(tmpdir(), 'concorde-first-')); roots.push(root);
    const candidate = resolve(root, 'candidate'); const build = resolve(root, 'build'); const backup = resolve(root, 'backup');
    await mkdir(candidate); await writeFile(resolve(candidate, 'version'), 'new');
    await promoteCandidate(candidate, build, backup);
    expect(await readFile(resolve(build, 'version'), 'utf8')).toBe('new');
    await expect(stat(backup)).rejects.toThrow();
  });

  // verifies: scenario.views.backup-cleanup-failure
  it.skipIf(process.getuid?.() === 0)('keeps the promoted site when removing a partly removed backup fails', async () => {
    const root = await mkdtemp(resolve(tmpdir(), 'concorde-cleanup-failure-')); roots.push(root);
    const candidate = resolve(root, 'candidate'); const build = resolve(root, 'build'); const backup = resolve(root, 'backup');
    await mkdir(candidate); await mkdir(resolve(build, 'locked'), {recursive: true});
    await writeFile(resolve(candidate, 'version'), 'new'); await writeFile(resolve(build, 'version'), 'old');
    await writeFile(resolve(build, 'locked/page'), 'old page');
    // The old site's `version` is removed before the removal fails on the directory it cannot empty.
    await chmod(resolve(build, 'locked'), 0o500);
    const warn = vi.spyOn(process.stderr, 'write').mockReturnValue(true);
    let warning = '';
    try {
      await promoteCandidate(candidate, build, backup);
      warning = String(warn.mock.calls[0]?.[0]);
    } finally {
      warn.mockRestore();
      await chmod(resolve(backup, 'locked'), 0o700).catch(() => undefined);
    }
    expect(await readFile(resolve(build, 'version'), 'utf8')).toBe('new');
    expect(await readdir(build)).toEqual(['version']);
    expect(warning).toContain(backup);
  });
});
