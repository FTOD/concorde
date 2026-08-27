import {createHash} from 'node:crypto';
import {mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {mkdir, mkdtemp, readFile, rm, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {dirname, resolve} from 'node:path';

import {afterEach, describe, expect, it} from 'vitest';

import {renderDeclaredDiagrams} from '../../scripts/render-diagrams';

const roots: string[] = [];

afterEach(async () => {
  await Promise.all(roots.splice(0).map((root) => rm(root, {recursive: true, force: true})));
});

async function fixtureRoot(): Promise<string> {
  const project = await mkdtemp(resolve(tmpdir(), 'concorde-delivery-set-'));
  roots.push(project);
  for (const name of ['one', 'two']) {
    const sourceDirectory = resolve(project, 'specs', name);
    await mkdir(sourceDirectory, {recursive: true});
    await writeFile(resolve(sourceDirectory, 'module.md'), `---
id: module.${name}
kind: module
parent: null
view: specs/${name}/architecture.json
children: []
features: []
contracts:
  provided: []
  required: []
---
# ${name}
`, 'utf8');
    await writeFile(resolve(sourceDirectory, 'architecture.json'), `${JSON.stringify({
      schema_version: 1,
      diagram_type: 'architecture',
      meta: {title: name, output: `../../generated/architecture/${name}.html`, quality_profile: 'showcase'},
      components: [], boundaries: [], connections: [], cards: [],
    })}\n`, 'utf8');
  }
  await mkdir(resolve(project, 'generated/architecture'), {recursive: true});
  await writeFile(resolve(project, 'generated/architecture/previous.html'), 'previous', 'utf8');

  const archify = resolve(project, '.agents/skills/archify');
  await mkdir(resolve(archify, 'bin'), {recursive: true});
  await writeFile(resolve(archify, 'bin/archify.mjs'), '// fake', 'utf8');
  await writeFile(resolve(archify, 'package.json'), JSON.stringify({
    name: 'archify', version: '2.16.0-dev.0', bin: {archify: './bin/archify.mjs'},
  }), 'utf8');
  await writeFile(resolve(project, 'skills-lock.json'), JSON.stringify({
    version: 1,
    skills: {archify: {
      source: 'tt-a1i/archify', skillPath: 'archify/SKILL.md',
      computedHash: '4317bc82ecb43a3a5279fed696a2f4afd25c189d4412e83d4558ed0f281f7d1e',
    }},
  }), 'utf8');
  return project;
}

function runner(failOnTwo: boolean) {
  return (_bin: string, args: string[]) => {
    if (args[0] === 'doctor') return {status: 0, stdout: 'ready', stderr: ''};
    const kind = args[1];
    const sourcePath = args[2];
    if (args[0] === 'validate') {
      return {
        status: 0,
        stderr: '',
        stdout: JSON.stringify({
          schemaVersion: 1, ok: true, command: 'validate', type: kind,
          checks: Array.from({length: 9}, (_, index) => ({name: `check-${index}`, ok: true})),
          composition: {profile: 'showcase', status: 'pass', summary: {errors: 0, warnings: 0}},
        }),
      };
    }
    if (failOnTwo && sourcePath.includes('/two/')) {
      return {status: 1, stdout: '', stderr: 'seeded second delivery failure'};
    }
    const outputPath = args[3];
    const source = readFileSync(sourcePath);
    const artifact = Buffer.from(`<html><meta name="generator" content="archify 2.16.0-dev.0">${sourcePath}</html>`);
    mkdirSync(dirname(outputPath), {recursive: true});
    writeFileSync(outputPath, artifact);
    return {
      status: 0,
      stderr: '',
      stdout: JSON.stringify({
        schemaVersion: 1, ok: true, command: 'deliver', type: kind,
        specification: {
          sha256: createHash('sha256').update(source).digest('hex'), bytes: source.byteLength,
        },
        artifact: {
          sha256: createHash('sha256').update(artifact).digest('hex'), bytes: artifact.byteLength,
        },
        validation: {
          checksPassed: 9, checkCount: 9, compositionProfile: 'showcase',
          compositionStatus: 'pass', errors: 0, warnings: 0,
        },
      }),
    };
  };
}

describe('complete diagram delivery set', () => {
  it('preserves the previous set when a later delivery fails', async () => {
    const project = await fixtureRoot();
    await expect(renderDeclaredDiagrams(project, {runner: runner(true)}))
      .rejects.toThrow(/seeded second delivery failure/);
    expect(await readFile(resolve(project, 'generated/architecture/previous.html'), 'utf8')).toBe('previous');
    await expect(readFile(resolve(project, 'generated/architecture/one.html'), 'utf8')).rejects.toThrow();
  });

  it('promotes all current outputs together and removes stale orphans', async () => {
    const project = await fixtureRoot();
    const sourceBefore = await Promise.all(['one', 'two'].map((name) =>
      readFile(resolve(project, `specs/${name}/architecture.json`), 'utf8')));
    const result = await renderDeclaredDiagrams(project, {runner: runner(false)});
    expect(result.receipts.map((receipt) => receipt.sourcePath)).toEqual([
      'specs/one/architecture.json', 'specs/two/architecture.json',
    ]);
    expect(await readFile(resolve(project, 'generated/architecture/one.html'), 'utf8')).toContain('archify 2.16.0-dev.0');
    expect(await readFile(resolve(project, 'generated/architecture/two.html'), 'utf8')).toContain('archify 2.16.0-dev.0');
    await expect(readFile(resolve(project, 'generated/architecture/previous.html'), 'utf8')).rejects.toThrow();
    expect(await Promise.all(['one', 'two'].map((name) =>
      readFile(resolve(project, `specs/${name}/architecture.json`), 'utf8')))).toEqual(sourceBefore);
  });
});
