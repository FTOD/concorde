import {cp, mkdtemp, readFile, rename, rm, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';

import {afterEach, describe, expect, it} from 'vitest';

import {buildRegistry} from '../../plugins/concorde-content/registry';
import {validateRegistry} from '../../plugins/concorde-content/validation';

const roots: string[] = [];
afterEach(async () => Promise.all(roots.splice(0).map((root) => rm(root, {recursive: true, force: true}))));

describe('specification authoring', () => {
  it('keeps a feature route stable across a source rename and diagnoses removal', async () => {
    const root = await mkdtemp(resolve(tmpdir(), 'concorde-authoring-')); roots.push(root);
    await cp(resolve(__dirname, '../fixtures/valid-project'), root, {recursive: true});
    const original = resolve(root, 'specs/example/features/001-alpha.md');
    const renamed = resolve(root, 'specs/example/features/003-renamed.md');
    await rename(original, renamed);
    expect((await buildRegistry(root)).documents.find((item) => item.sourcePath.endsWith('003-renamed.md'))?.route)
      .toBe('/features/feature.fixture.alpha');
    await rm(renamed);
    expect(validateRegistry(await buildRegistry(root)).map((finding) => finding.ruleId))
      .toContain('module.feature.unresolved');
  });

  it('reflects terminology table edits without a parallel registry', async () => {
    const root = await mkdtemp(resolve(tmpdir(), 'concorde-terminology-')); roots.push(root);
    await cp(resolve(__dirname, '../fixtures/valid-project'), root, {recursive: true});
    const featurePath = resolve(root, 'specs/example/features/001-alpha.md');
    const original = await readFile(featurePath, 'utf8');
    await writeFile(featurePath, `${original}\n\n## Terminology\n\n| Term | Meaning | Relationships |\n|---|---|---|\n| \`Alpha input\` | One prepared input. | None |\n`, 'utf8');
    const registry = await buildRegistry(root);
    const feature = registry.documents.find((item) => item.sourcePath === 'specs/example/features/001-alpha.md');
    expect(feature?.content).toContain('## Terminology');
    expect(feature?.content).toContain('`Alpha input`');
  });
});
