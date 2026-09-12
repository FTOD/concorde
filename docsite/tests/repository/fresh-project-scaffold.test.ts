import {captureProcess} from '../capture-process';
import {existsSync} from 'node:fs';
import {mkdir, mkdtemp, readFile, readdir, rm, symlink, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';

import {afterAll, beforeAll, describe, expect, it} from 'vitest';

/**
 * Concorde-repository evidence for scenario.views.scaffold-propose: a project holding
 * only Profile 12 initialization outputs receives the packaged docsite through the native `docsite`
 * Tool and passes the adapter's validate and build steps. It reuses this checkout's installed
 * dependencies without a separate diagram renderer, so it stays outside the packaged template.
 */
const siteDir = resolve(__dirname, '../..');
const repositoryRoot = resolve(siteDir, '..');
const concordeTool = resolve(repositoryRoot, 'scripts/concorde.py');

type Envelope = {status: string; artifacts?: string[]; findings?: Array<{rule_id: string; message: string}>; result: Record<string, unknown>};

function run(command: string, args: string[], cwd: string) {
  const result = captureProcess(command, args, {cwd, timeout: 240_000, env: {...process.env, NODE_ENV: 'production'}});
  expect(result.error).toBeUndefined();
  expect(result.signal).toBeNull();
  return result;
}

function tool(root: string, ...args: string[]): Envelope {
  const result = run(process.env.CONCORDE_PYTHON ?? 'python3', [concordeTool, '--project-root', root, ...args], root);
  expect(result.status, result.stderr).toBe(0);
  if (!result.stdout) throw new Error(`concorde ${args.join(' ')} produced no envelope: ${result.stderr}`);
  return JSON.parse(result.stdout) as Envelope;
}

let root = '';
let docsiteProposal: Envelope;

beforeAll(async () => {
  root = await mkdtemp(resolve(tmpdir(), 'concorde-fresh-project-'));
  await mkdir(resolve(root, '.concorde'), {recursive: true});
  const initialized=run(process.env.CONCORDE_PYTHON ?? 'python3',['-c', `import sys;from pathlib import Path
sys.path.insert(0,sys.argv[1]+'/src')
from concorde.spec.initialize import project_proposal,apply_project_proposal
from concorde.spec.typed_data import typed
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
  await mkdir(resolve(root, 'generated/protocol'), {recursive: true});
  await writeFile(resolve(root, 'generated/protocol/framework-owned.txt'), 'Preserve Framework build assets.');
}, 300_000);

afterAll(async () => {
  if (root) await rm(root, {recursive: true, force: true});
});

describe('a project holding only Profile 12 initialization outputs', () => {
  it('scenario.views.scaffold-propose: receives the graph-free adapter and identity', async () => {
    const files = (docsiteProposal.result.proposal as {files: Array<{path: string}>}).files.map((file) => file.path);
    expect(files).toContain('docsite/docusaurus.config.ts');
    expect(files).toContain('docsite/package-lock.json');
    expect(files).toContain('docsite/site.json');
    expect(files).not.toContain('README.md');
    expect(files).not.toContain('docsite/src/pages/graph.tsx');
    expect(files).not.toContain('docsite/src/components/ScopedGraph.tsx');
    expect(files.some(path => path.startsWith('docsite/concorde-only/'))).toBe(false);
    expect(files.some((path) => path.startsWith('docsite/tests/repository/') || path.startsWith('docsite/scaffold/'))).toBe(false);
    expect(files).not.toContain('.github/workflows/deploy-docsite.yml');
    const identity = JSON.parse(await readFile(resolve(root, 'docsite/site.json'), 'utf8')) as Record<string, unknown>;
    expect(identity).toMatchObject({schema_version: 1, title: 'Atlas', baseUrl: '/'});
    expect(identity.protocolDocs).toBeUndefined();
    expect(identity.customDocs).toBeUndefined();
    expect(files.some(path => path.startsWith('docsite/custom-docs/'))).toBe(false);
    expect(files).not.toContain('docsite/sidebars.protocol.ts');
    expect(existsSync(resolve(root, 'README.md'))).toBe(false);
    expect(existsSync(resolve(root, 'docs'))).toBe(false);
    expect(existsSync(resolve(root, 'docsite/site.json'))).toBe(true);
    expect(await readFile(resolve(root, 'docsite/docusaurus.config.ts'), 'utf8'))
      .toBe(await readFile(resolve(siteDir, 'docusaurus.config.ts'), 'utf8'));
  });

  it('scenario.views.scaffold-apply: is unchanged on a second proposal and refuses to overwrite', () => {
    expect(tool(root, 'docsite', '--propose', '--allow-primary-worktree').status).toBe('unchanged');
    expect(tool(root, 'docsite', '--apply', '--proposal', '.concorde/docsite-proposal.json', '--allow-primary-worktree').status).toBe('unchanged');
  });

  it('scenario.views.publish-without-graph / scenario.views.publish-homepage-default: builds the received adapter', async () => {
    // scenario.views.publish-candidate / scenario.views.id-anchors: Specs remain literal Markdown.
    const sourcePath=resolve(root,'specs/project/module.md');
    await writeFile(sourcePath,await readFile(sourcePath,'utf8')+'\nLiteral Spec expression: {6 * 7}.\n');
    await mkdir(resolve(root,'docsite/.docusaurus'),{recursive:true});
    await writeFile(resolve(root,'docsite/.docusaurus/preview-sentinel.json'),'Preview cache stays independent.');
    const validate = run(process.execPath, ['--import','tsx','scripts/validate.ts'], resolve(root, 'docsite'));
    expect(validate.status, `${validate.stdout}\n${validate.stderr}`).toBe(0);
    const build = run(process.execPath, ['--import','tsx','scripts/build.ts'], resolve(root, 'docsite'));
    expect(build.status, `${build.stdout}\n${build.stderr}`).toBe(0);
    const manifest = JSON.parse(await readFile(resolve(root,'docsite/build/build-manifest.json'),'utf8'));
    expect(manifest.schema_version).toBe(19);expect(manifest.pages).toHaveLength(1);
    expect(manifest.pages[0].route).toBe('/specs/project/module');
    expect(manifest.pages[0].owner).toEqual('module.atlas');
    expect(manifest.pages[0].aliases).toEqual([expect.stringMatching(/^\/specs\/module\.atlas\/[0-9a-f]{16}$/)]);
    const homepage=await readFile(resolve(root,'docsite/build/index.html'),'utf8');expect(homepage).toContain(manifest.pages[0].route);
    expect(homepage).toMatch(/http-equiv="refresh"/i);
    expect(homepage).not.toContain('Specify the architecture.');
    expect(existsSync(resolve(root,'docsite/build/graph.html'))).toBe(false);
    expect(existsSync(resolve(root,'docsite/build/agent-flows.html'))).toBe(false);
    expect(existsSync(resolve(root,'docsite/build/architecture-graph.json'))).toBe(false);
    expect(existsSync(resolve(root,'docsite/build',manifest.pages[0].route.slice(1)+'.html'))).toBe(true);
    const [legacyAlias]=manifest.pages[0].aliases as string[];
    const redirectStub=await readFile(resolve(root,'docsite/build',legacyAlias.slice(1)+'.html'),'utf8');
    expect(redirectStub).toContain(manifest.pages[0].route);
    expect(await readFile(resolve(root,'generated/protocol/framework-owned.txt'),'utf8')).toBe('Preserve Framework build assets.');
    const mainPage=await readFile(resolve(root,'docsite/build',manifest.pages[0].route.slice(1)+'.html'),'utf8');
    expect(mainPage.match(/<nav\b[\s\S]*?<\/nav>/)![0]).not.toContain('Spec Protocol');
    expect(mainPage).not.toContain('Agent Flows');
    expect(mainPage).not.toContain('<iframe');
    expect(mainPage).toContain('id="purpose"');expect(mainPage).toContain('id="requirements"');expect(mainPage).toContain('id="scenarios"');expect(mainPage).toContain('id="ontology"');
    expect(mainPage).toContain('id="entities"');expect(mainPage).toContain('id="relationships"');
    expect(mainPage).not.toContain('/diagrams/');
    expect(mainPage).toContain('Spec metadata');
    expect(mainPage).toContain('Literal Spec expression: {6 * 7}.');
    expect(await readFile(resolve(root,'docsite/.docusaurus/preview-sentinel.json'),'utf8')).toBe('Preview cache stays independent.');
    expect(existsSync(resolve(root,'docsite/.generated/docusaurus-production'))).toBe(true);
  }, 240_000);
  it('scenario.views.custom-docs: a consumer adds a separate docs tab without changing registered pages', async () => {
    const before=await readFile(resolve(root,'docsite/build/build-manifest.json'),'utf8');
    const registryBefore=await readFile(resolve(root,'.concorde/specs.json'),'utf8');
    const identityPath=resolve(root,'docsite/site.json');
    const identity=JSON.parse(await readFile(identityPath,'utf8'));
    identity.customDocs=[{id:'guides',label:'Team Handbook',path:'./custom-docs/guides',routeBasePath:'handbook'}];
    await mkdir(resolve(root,'docsite/custom-docs/guides'),{recursive:true});
    await writeFile(resolve(root,'docsite/custom-docs/guides/index.md'),'---\nslug: /\n---\n# Team Handbook\n\nHuman-authored onboarding.\n\n```mermaid\nflowchart LR\n  accTitle: Handbook workflow\n  accDescr: Start leads to finish.\n  Start --> Finish\n```\n');
    await writeFile(resolve(root,'docsite/custom-docs/guides/component.mdx'),
      'import React from "react";\n\nexport const Greeting = ({name}) => <strong data-custom-mdx="rendered">Hello {name}</strong>;\n\n# Component guide\n\n<Greeting name="Atlas" />\n\nThe answer is {6 * 7}.\n');
    await writeFile(resolve(root,'docsite/custom-docs/app.tsx'), 'import React from "react"; export default function App(){return <main><h1 id="application">Custom application</h1><a href="/handbook">Handbook</a></main>;}');
    await writeFile(resolve(root,'docsite/custom-docs/index.ts'), 'export default {plugins: [function(){return {name:"custom-app",contentLoaded({actions}){actions.addRoute({path:"/app",component:require.resolve("./app.tsx"),exact:true});}};}],navbarItems:[{to:"/app",label:"Application",position:"left"}]};');
    await writeFile(identityPath,JSON.stringify(identity));
    const build=run(process.execPath,['--import','tsx','scripts/build.ts'],resolve(root,'docsite'));
    expect(build.status,build.stdout+'\n'+build.stderr).toBe(0);
    const html=await readFile(resolve(root,'docsite/build/handbook.html'),'utf8');
    expect(html).toContain('Human-authored onboarding.');
    const mdx=await readFile(resolve(root,'docsite/build/handbook/component.html'),'utf8');
    expect(mdx).toContain('data-custom-mdx="rendered"');
    expect(mdx).toMatch(/Hello (?:<!-- -->)?Atlas/);
    expect(mdx).toMatch(/The answer is (?:<!-- -->)?42/);
    expect(mdx).not.toContain('provenanceShell');
    expect(html).not.toContain('provenanceShell');
    // Mermaid renders after hydration; its page-specific definition is shipped in a client chunk.
    const scripts=resolve(root,'docsite/build/assets/js');
    const clientChunks=await Promise.all((await readdir(scripts)).filter(name=>name.endsWith('.js'))
      .map(name=>readFile(resolve(scripts,name),'utf8')));
    expect(clientChunks.some(chunk=>chunk.includes('Handbook workflow') &&
      /Start --(?:>|\\x3e|\\u003e) Finish/.test(chunk))).toBe(true);
    expect(await readFile(resolve(root,'docsite/build/app.html'),'utf8')).toContain('Custom application');
    expect(await readFile(resolve(root,'docsite/build/build-manifest.json'),'utf8')).toBe(before);
    expect(await readFile(resolve(root,'.concorde/specs.json'),'utf8')).toBe(registryBefore);
    const manifest=JSON.parse(await readFile(resolve(root,'docsite/build/build-manifest.json'),'utf8'));
    expect(manifest.pages).toHaveLength(1);
    expect(manifest.pages[0].route).toBe('/specs/project/module');
    const spec=await readFile(resolve(root,'docsite/build/specs/project/module.html'),'utf8');
    expect(spec.match(/<nav\b[\s\S]*?<\/nav>/)![0]).toContain('Team Handbook');
    expect(spec).not.toContain('Module composition');
  },240_000);

  it('scenario.views.custom-docs scenario.views.publish-preserves-previous-on-failure: invalid custom candidates preserve the published site',async()=>{
    const identityPath=resolve(root,'docsite/site.json');
    const identity=await readFile(identityPath,'utf8');
    const guidePath=resolve(root,'docsite/custom-docs/guides/index.md');
    const guide=await readFile(guidePath,'utf8');
    const previous=await readFile(resolve(root,'docsite/build/handbook.html'),'utf8');
    const manifest=await readFile(resolve(root,'docsite/build/build-manifest.json'),'utf8');
    const duplicate=resolve(root,'docsite/custom-docs/guides/duplicate.md');
    try {
      for(const failure of ['anchor','route','missing','registered']){
        await writeFile(identityPath,identity);await writeFile(guidePath,guide);await rm(duplicate,{force:true});
        if(failure==='anchor')await writeFile(guidePath,guide+'\n[Missing anchor](/handbook#missing-anchor)\n');
        if(failure==='route')await writeFile(duplicate,'---\nslug: /\n---\n# Duplicate landing page');
        if(failure==='missing'||failure==='registered'){
          const value=JSON.parse(identity);value.customDocs[0].path=failure==='missing'?'missing-collection':'../specs';
          await writeFile(identityPath,JSON.stringify(value));
        }
        const result=run(process.execPath,['--import','tsx','scripts/build.ts'],resolve(root,'docsite'));
        expect(result.status, failure).not.toBe(0);
        expect(await readFile(resolve(root,'docsite/build/handbook.html'),'utf8')).toBe(previous);
        expect(await readFile(resolve(root,'docsite/build/build-manifest.json'),'utf8')).toBe(manifest);
      }
    } finally {
      await writeFile(identityPath,identity);await writeFile(guidePath,guide);await rm(duplicate,{force:true});
    }
  }, 960_000);

});
