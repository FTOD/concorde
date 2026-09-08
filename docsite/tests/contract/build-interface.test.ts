import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {spawnSync} from 'node:child_process';

import {describe, expect, it} from 'vitest';

const siteDir = resolve(__dirname, '../..');

describe('build interface', () => {
  it('exposes every stable command', async () => {
    const packageJson = JSON.parse(await readFile(resolve(siteDir, 'package.json'), 'utf8'));
    expect(packageJson.version).toBe('0.7.0');
    expect(Object.keys(packageJson.scripts)).toEqual(expect.arrayContaining([
      'inspect', 'validate', 'render-diagrams', 'start', 'test', 'build', 'typecheck', 'check',
    ]));
    expect(packageJson.scripts.start).toBe('node --import tsx scripts/start.ts');
    expect(packageJson.scripts['render-diagrams']).toBe('node --import tsx scripts/render-diagrams.ts');
    expect(packageJson.scripts.build).toBe('node --import tsx scripts/build.ts');
    expect(packageJson.scripts.validate).toBe('node --import tsx scripts/validate.ts');
    // Preparation and preview-cache isolation are exercised by the real build tests, rather
    // than requiring a particular private call expression or cache-removal implementation.
  });

  it('returns non-zero actionable diagnostics for invalid content', () => {
    const result = spawnSync(process.execPath, [
      '--import', 'tsx', 'scripts/validate.ts', '--project-root',
      resolve(siteDir, 'tests/fixtures/invalid-projects/missing-title'),
    ], {cwd: siteDir, encoding: 'utf8'});
    expect(result.status).not.toBe(0);
    expect(result.stderr).toContain('content.title.required specs/example/architecture.md:');
    expect(result.stderr).toContain('Remediation:');
  });

  it('returns a non-zero migration diagnostic for a parallel root docs tree', () => {
    const result = spawnSync(process.execPath, [
      '--import', 'tsx', 'scripts/validate.ts', '--project-root',
      resolve(siteDir, 'tests/fixtures/invalid-projects/parallel-docs'),
    ], {cwd: siteDir, encoding: 'utf8'});
    expect(result.status).not.toBe(0);
    expect(result.stderr).toContain('source.parallel.docs docs:');
    expect(result.stderr).toContain('merge unique intent into the owning module architecture or feature design');
  });
});
