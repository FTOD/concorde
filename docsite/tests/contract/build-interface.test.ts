import {readFile} from 'node:fs/promises';
import {mkdtemp, rm, mkdir, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';
import {captureProcess} from '../capture-process';

import {afterEach, describe, expect, it} from 'vitest';

const siteDir = resolve(__dirname, '../..');
const temporaryRoots: string[] = [];

afterEach(async () => {
  await Promise.all(temporaryRoots.splice(0).map((root) => rm(root, {recursive: true, force: true})));
});

async function temporaryRoot(prefix: string): Promise<string> {
  const root = await mkdtemp(resolve(tmpdir(), prefix));
  temporaryRoots.push(root);
  return root;
}

function validate(root: string) {
  const result = captureProcess(process.execPath, ['--import', 'tsx', 'scripts/validate.ts', '--project-root', root],
    {cwd: siteDir});
  expect(result.error).toBeUndefined();
  expect(result.signal).toBeNull();
  return result;
}

describe('build interface', () => {
  it('exposes every stable command', async () => {
    const packageJson = JSON.parse(await readFile(resolve(siteDir, 'package.json'), 'utf8'));
    expect(packageJson.version).toBe('0.7.0');
    expect(Object.keys(packageJson.scripts)).toEqual(expect.arrayContaining([
      'validate', 'start', 'test', 'build', 'typecheck', 'check',
    ]));
    expect(packageJson.scripts.start).toBe('node --import tsx scripts/start.ts');
    expect(packageJson.scripts.build).toBe('node --import tsx scripts/build.ts');
    expect(packageJson.scripts.validate).toBe('node --import tsx scripts/validate.ts');
    // Preparation and preview-cache isolation are exercised by the real build tests, rather
    // than requiring a particular private call expression or cache-removal implementation.
  });

  it('returns a non-zero diagnostic for an unconfigured project root', async () => {
    const root = await temporaryRoot('concorde-unconfigured-');
    const result = validate(root);
    expect(result.status).toBe(1);
    expect(`${result.stdout}${result.stderr}`).toContain('.concorde/config.json');
  });

  it('refuses to publish a project that does not declare Profile 12', async () => {
    const root = await temporaryRoot('concorde-legacy-profile-');
    await mkdir(resolve(root, '.concorde'), {recursive: true});
    await writeFile(resolve(root, '.concorde/config.json'), JSON.stringify({profile_version: 7}), 'utf8');
    const result = validate(root);
    expect(result.status).toBe(1);
    expect(`${result.stdout}${result.stderr}`).toContain('Profile 12 is required');
  });
});
