import {spawnSync} from 'node:child_process';
import {existsSync} from 'node:fs';
import {mkdir, mkdtemp, readFile, rm, symlink, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';

import {afterAll, beforeAll, describe, expect, it} from 'vitest';

/**
 * Concorde-repository evidence for feature.concorde.publish-project-docsite FR-009: a project holding
 * only Profile 9 initialization outputs receives the packaged docsite through the native `docsite`
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
  const initialized=run('python3',['-c', `import sys;from pathlib import Path
sys.path.insert(0,sys.argv[1]+'/src')
from concorde.specification.initialize import project_proposal,apply_project_proposal
from concorde.host.typed_data import typed
root=Path(sys.argv[2]);package=Path(sys.argv[1])
config=typed('concorde-capability-configuration',{'integration':'codex','enforcement':'native'})
apply_project_proposal(root,package,project_proposal(root,package,'Atlas',config,'module.atlas'))`,repositoryRoot,root],root);
  expect(initialized.status,initialized.stderr).toBe(0);

  docsiteProposal = tool(root, 'docsite', '--propose', '--allow-primary-worktree');
  expect(docsiteProposal.status).toBe('proposal');
  await writeFile(resolve(root, '.concorde/docsite-proposal.json'), JSON.stringify(docsiteProposal), 'utf8');
  const applied = tool(root, 'docsite', '--apply', '--proposal', '.concorde/docsite-proposal.json', '--allow-primary-worktree');
  expect(applied.status).toBe('success');
  await symlink(resolve(siteDir, 'node_modules'), resolve(root, 'docsite/node_modules'), 'dir');
  await mkdir(resolve(root, '.agents/skills'), {recursive: true});
  await symlink(resolve(repositoryRoot, '.agents/skills/archify'), resolve(root, '.agents/skills/archify'), 'dir');
  await writeFile(resolve(root, 'skills-lock.json'), await readFile(resolve(repositoryRoot, 'skills-lock.json')));
  await mkdir(resolve(root, 'generated/protocol'), {recursive: true});
  await writeFile(resolve(root, 'generated/protocol/framework-owned.txt'), 'Preserve Framework build assets.');
}, 300_000);

afterAll(async () => {
  if (root) await rm(root, {recursive: true, force: true});
});

describe('a project holding only Profile 9 initialization outputs', () => {
  it('receives the packaged adapter and identity without synthetic prose or repository evidence', async () => {
    const files = (docsiteProposal.result.proposal as {files: Array<{path: string}>}).files.map((file) => file.path);
    expect(files).toContain('docsite/docusaurus.config.ts');
    expect(files).toContain('docsite/package-lock.json');
    expect(files).toContain('docsite/site.json');
    expect(files).not.toContain('README.md');
    expect(files.some((path) => path.startsWith('docsite/tests/repository/') || path.startsWith('docsite/scaffold/'))).toBe(false);
    expect(files).not.toContain('.github/workflows/deploy-docsite.yml');
    const identity = JSON.parse(await readFile(resolve(root, 'docsite/site.json'), 'utf8')) as Record<string, unknown>;
    expect(identity).toMatchObject({schema_version: 1, title: 'Atlas', baseUrl: '/'});
    expect(identity.protocolDocs).toBeUndefined();
    expect(existsSync(resolve(root, 'README.md'))).toBe(false);
    expect(existsSync(resolve(root, 'docs'))).toBe(false);
    expect(existsSync(resolve(root, 'docsite/site.json'))).toBe(true);
    expect(await readFile(resolve(root, 'docsite/docusaurus.config.ts'), 'utf8'))
      .toBe(await readFile(resolve(siteDir, 'docusaurus.config.ts'), 'utf8'));
  });

  it('is unchanged on a second proposal and refuses to overwrite', () => {
    expect(tool(root, 'docsite', '--propose', '--allow-primary-worktree').status).toBe('unchanged');
    expect(tool(root, 'docsite', '--apply', '--proposal', '.concorde/docsite-proposal.json', '--allow-primary-worktree').status).toBe('unchanged');
  });

  it('validates and builds with the adapter it received', async () => {
    await mkdir(resolve(root,'docsite/.docusaurus'),{recursive:true});
    await writeFile(resolve(root,'docsite/.docusaurus/preview-sentinel.json'),'Preview cache stays independent.');
    const validate = run(process.execPath, ['--import','tsx','scripts/validate.ts'], resolve(root, 'docsite'));
    expect(validate.status, `${validate.stdout}\n${validate.stderr}`).toBe(0);
    const build = run(process.execPath, ['--import','tsx','scripts/build.ts'], resolve(root, 'docsite'));
    expect(build.status, `${build.stdout}\n${build.stderr}`).toBe(0);
    const manifest = JSON.parse(await readFile(resolve(root,'docsite/build/build-manifest.json'),'utf8'));
    expect(manifest.schema_version).toBe(16);expect(manifest.pages).toHaveLength(1);
    expect(manifest.pages[0].route).toBe('/specs/modules/project/module');
    expect(manifest.pages[0].targets).toEqual(['module.atlas']);
    expect(manifest.pages[0].aliases).toEqual([expect.stringMatching(/^\/specs\/module\.atlas\/[0-9a-f]{16}$/)]);
    const homepage=await readFile(resolve(root,'docsite/build/index.html'),'utf8');expect(homepage).toContain(manifest.pages[0].route);
    expect(existsSync(resolve(root,'docsite/build',manifest.pages[0].route.slice(1)+'.html'))).toBe(true);
    const [legacyAlias]=manifest.pages[0].aliases as string[];
    const redirectStub=await readFile(resolve(root,'docsite/build',legacyAlias.slice(1)+'.html'),'utf8');
    expect(redirectStub).toContain(manifest.pages[0].route);
    expect(await readFile(resolve(root,'generated/protocol/framework-owned.txt'),'utf8')).toBe('Preserve Framework build assets.');
    const mainPage=await readFile(resolve(root,'docsite/build',manifest.pages[0].route.slice(1)+'.html'),'utf8');
    expect(mainPage.match(/<nav\b[\s\S]*?<\/nav>/)![0]).not.toContain('Spec Protocol');
    expect(mainPage).toContain('<iframe');
    expect(mainPage).toContain('/diagrams/');
    expect(mainPage.indexOf('<iframe')).toBeLessThan(mainPage.indexOf('<h1'));
    expect(mainPage).toContain('Spec metadata');
    expect(await readFile(resolve(root,'docsite/.docusaurus/preview-sentinel.json'),'utf8')).toBe('Preview cache stays independent.');
    expect(existsSync(resolve(root,'docsite/.generated/docusaurus-production'))).toBe(true);
  }, 240_000);
});
