import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {spawnSync} from 'node:child_process';

import {describe, expect, it} from 'vitest';

const siteDir = resolve(__dirname, '../..');

describe('build interface', () => {
  it('exposes every stable command', async () => {
    const packageJson = JSON.parse(await readFile(resolve(siteDir, 'package.json'), 'utf8'));
    expect(Object.keys(packageJson.scripts)).toEqual(expect.arrayContaining([
      'inspect', 'validate', 'start', 'test', 'build', 'typecheck', 'check',
    ]));
    expect(packageJson.scripts.start).toContain('npm run validate');
  });

  it('returns non-zero actionable diagnostics for invalid content', () => {
    const result = spawnSync(process.execPath, [
      resolve(siteDir, 'node_modules/tsx/dist/cli.mjs'), 'scripts/validate.ts', '--project-root',
      resolve(siteDir, 'tests/fixtures/invalid-projects/missing-title'),
    ], {cwd: siteDir, encoding: 'utf8'});
    expect(result.status).not.toBe(0);
    expect(result.stderr).toContain('content.title.required docs/no-title.md:');
    expect(result.stderr).toContain('Remediation:');
  });
});
