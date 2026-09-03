import {spawnSync} from 'node:child_process';
import {existsSync} from 'node:fs';
import {mkdir, mkdtemp, readFile, rm, symlink, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';

import {afterAll, beforeAll, describe, expect, it} from 'vitest';

/**
 * Concorde-repository evidence for feature.concorde.publish-project-docsite FR-009: a project holding
 * only Initialization Proposal 3 outputs receives the packaged docsite through the native `docsite`
 * Tool and passes the adapter's validate and build steps. It reuses this checkout's installed
 * dependencies and pinned Archify skill, so it stays outside the packaged template.
 */
const siteDir = resolve(__dirname, '../..');
const repositoryRoot = resolve(siteDir, '..');
const concordeTool = resolve(repositoryRoot, 'scripts/concorde.py');

type Envelope = {status: string; artifacts?: string[]; findings?: Array<{rule_id: string; message: string}>; result: Record<string, unknown>};

function run(command: string, args: string[], cwd: string) {
  const result = spawnSync(command, args, {cwd, encoding: 'utf8', timeout: 240_000, env: {...process.env, NODE_ENV: 'production'}});
  return result;
}

function tool(root: string, ...args: string[]): Envelope {
  const result = run('python3', [concordeTool, '--project-root', root, ...args], root);
  if (!result.stdout) throw new Error(`concorde ${args.join(' ')} produced no envelope: ${result.stderr}`);
  return JSON.parse(result.stdout) as Envelope;
}

let root = '';
let docsiteProposal: Envelope;

beforeAll(async () => {
  root = await mkdtemp(resolve(tmpdir(), 'concorde-fresh-project-'));
  await mkdir(resolve(root, '.concorde'), {recursive: true});
  const initProposal = tool(root, 'init', '--propose', '--name', 'Atlas');
  expect(initProposal.status).toBe('proposal');
  await writeFile(resolve(root, '.concorde/init-proposal.json'), JSON.stringify(initProposal), 'utf8');
  expect(tool(root, 'init', '--apply', '--proposal', '.concorde/init-proposal.json').status).toBe('success');
  // Reuse this checkout's pinned Archify skill; publishing needs it, scaffolding does not.
  await symlink(resolve(repositoryRoot, '.agents'), resolve(root, '.agents'), 'dir');
  await symlink(resolve(repositoryRoot, 'skills-lock.json'), resolve(root, 'skills-lock.json'));

  docsiteProposal = tool(root, 'docsite', '--propose');
  expect(docsiteProposal.status).toBe('proposal');
  await writeFile(resolve(root, '.concorde/docsite-proposal.json'), JSON.stringify(docsiteProposal), 'utf8');
  const applied = tool(root, 'docsite', '--apply', '--proposal', '.concorde/docsite-proposal.json');
  expect(applied.status).toBe('success');
  await symlink(resolve(siteDir, 'node_modules'), resolve(root, 'docsite/node_modules'), 'dir');
}, 300_000);

afterAll(async () => {
  if (root) await rm(root, {recursive: true, force: true});
});

describe('a project holding only Initialization Proposal 3 outputs', () => {
  it('receives the packaged adapter, its identity, and a homepage, but no repository evidence', async () => {
    const files = (docsiteProposal.result.proposal as {files: Array<{path: string}>}).files.map((file) => file.path);
    expect(files).toContain('docsite/docusaurus.config.ts');
    expect(files).toContain('docsite/package-lock.json');
    expect(files).toContain('docsite/site.json');
    expect(files).toContain('README.md');
    expect(files.some((path) => path.startsWith('docsite/tests/repository/') || path.startsWith('docsite/scaffold/'))).toBe(false);
    expect(files).not.toContain('.github/workflows/deploy-docsite.yml');
    const identity = JSON.parse(await readFile(resolve(root, 'docsite/site.json'), 'utf8')) as Record<string, unknown>;
    expect(identity).toMatchObject({schema_version: 1, title: 'Atlas', baseUrl: '/'});
    expect(existsSync(resolve(root, 'docs'))).toBe(false);
    expect(existsSync(resolve(root, 'docsite/site.json'))).toBe(true);
    expect(await readFile(resolve(root, 'docsite/docusaurus.config.ts'), 'utf8'))
      .toBe(await readFile(resolve(siteDir, 'docusaurus.config.ts'), 'utf8'));
  });

  it('is unchanged on a second proposal and refuses to overwrite', () => {
    expect(tool(root, 'docsite', '--propose').status).toBe('unchanged');
    expect(tool(root, 'docsite', '--apply', '--proposal', '.concorde/docsite-proposal.json').status).toBe('unchanged');
  });

  it('validates and builds with the adapter it received', async () => {
    const validate = run('npm', ['run', 'validate'], resolve(root, 'docsite'));
    expect(validate.status, `${validate.stdout}\n${validate.stderr}`).toBe(0);
    const build = run('npm', ['run', 'build'], resolve(root, 'docsite'));
    expect(build.status, `${build.stdout}\n${build.stderr}`).toBe(0);
    const manifest = JSON.parse(await readFile(resolve(root, 'docsite/build/build-manifest.json'), 'utf8')) as {
      pages: Array<{route: string; kind: string}>;
    };
    expect(manifest.pages.map((page) => page.route).sort()).toEqual(['/', '/architecture/module.atlas']);
    const homepage = await readFile(resolve(root, 'docsite/index.html').replace('docsite/index.html', 'docsite/build/index.html'), 'utf8');
    expect(homepage).toContain('Atlas');
    expect(homepage).not.toContain('>Documentation</a>');
    expect(existsSync(resolve(root, 'docsite/build/architecture/module.atlas.html'))).toBe(true);
  }, 240_000);
});
