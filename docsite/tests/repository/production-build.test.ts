import {spawnSync} from 'node:child_process';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {beforeAll,it,expect} from 'vitest';
import {loadScopedRegistry} from '../../plugins/scoped-content/model';
import {validateScopedBuild} from '../../plugins/scoped-content';
const site=resolve(__dirname,'../..'),root=resolve(site,'..'),output=resolve(site,'build');
beforeAll(()=>{
 const result=spawnSync(process.execPath,['--import','tsx','scripts/build.ts'],{cwd:site,encoding:'utf8',timeout:120000});
 expect(result.status,result.stdout+'\n'+result.stderr).toBe(0);
},120000);
it('publishes the current exact registry and verifies the promoted manifest',async()=>{
 await validateScopedBuild(root,output);const r=loadScopedRegistry(root);
 for(const page of r.pages){const html=await readFile(resolve(output,page.route.slice(1)+'.html'),'utf8');expect(html).toContain(page.sourcePath);}
 const home=await readFile(resolve(output,'index.html'),'utf8');expect(home).toContain(r.pages.find(p=>p.primaryOf===r.entryTarget)!.route);
 const entry=r.pages.find(p=>p.primaryOf===r.entryTarget)!;
 const html=await readFile(resolve(output,entry.route.slice(1)+'.html'),'utf8');
 expect(html).toContain('theme-doc-sidebar-container');
 expect(html).not.toContain('>Specs by source path<');expect(html).not.toContain('>Specs by target<');
 const navbar=html.match(/<nav\b[\s\S]*?<\/nav>/)![0];
 expect(navbar).toContain('Spec Protocol');
 expect(navbar.indexOf('Spec Protocol')).toBeLessThan(navbar.indexOf('Module Specs'));
 expect(navbar).toContain('Module Specs');
 expect(navbar.indexOf('Module Specs')).toBeLessThan(navbar.indexOf('>Graph<'));
 expect(html).toContain('id="purpose"');expect(html).toContain('id="scenarios"');expect(html).toContain('id="entities"');expect(html).toContain('id="ontology"');expect(html).toContain('id="relationships"');expect(html).toContain('id="req.concorde.routing-no-access"');
 expect(html).not.toContain('<iframe');
});
it('publishes the independent standard with chapter navigation and no Spec wrapper',async()=>{
 const overview=await readFile(resolve(output,'protocol.html'),'utf8');
 expect(overview).toContain('Spec Protocol');
 expect(overview).toContain('Spec management');
 expect(overview).toContain('Required format');
 expect(overview).toContain('Templates');
 expect(overview).not.toContain('provenanceShell');
 expect(overview).not.toContain('feature.concorde.evolve-protocol');
 for(const chapter of ['principles','module','spec-management','spec-management/spec-and-context','format','templates/module','templates/scenario']) {
  const html=await readFile(resolve(output,`protocol/${chapter}.html`),'utf8');
  expect(html).toContain('theme-doc-sidebar-container');
  expect(html).not.toContain('provenanceShell');
 }
 const graph=JSON.parse(await readFile(resolve(output,'architecture-graph.json'),'utf8'));
 expect(graph.nodes.some((node:{id:string})=>node.id==='module.protocol')).toBe(false);
});
it('publishes the configured introduction at the root while preserving direct Spec navigation',async()=>{
 const home=await readFile(resolve(output,'index.html'),'utf8');
 expect(home).toContain('Give every agent a contract.');
 expect(home).toContain('Shared code. Every consumer counted.');
 expect(home).toContain('id="get-started"');
 expect(home).toContain('href="/concorde/specs/concorde/module"');
 expect(home).toContain('href="/concorde/graph"');
 expect(home).toContain('href="/concorde/protocol"');
 expect(home).toContain('name="description"');
 expect(home).not.toMatch(/http-equiv="refresh"/i);
 expect(home).not.toContain('provenanceShell');
 const manifest=JSON.parse(await readFile(resolve(output,'build-manifest.json'),'utf8'));
 expect(manifest.pages.some((page:{route:string})=>page.route==='/')).toBe(false);
});
it('preserves every legacy membership route as a redirect stub to its canonical page',async()=>{
 const r=loadScopedRegistry(root);
 for(const page of r.pages) for(const alias of page.aliases){
  const stub=await readFile(resolve(output,alias.slice(1)+'.html'),'utf8');
  expect(stub).toContain(page.route);expect(stub).toContain('refresh');
 }
});
it('publishes the same typed relationship graph as the human navigation',async()=>{
 const graph=JSON.parse(await readFile(resolve(output,'architecture-graph.json'),'utf8'));const r=loadScopedRegistry(root);
 expect(graph.nodes).toEqual(r.targets);expect(graph.edges).toEqual(r.edges);
 const html=await readFile(resolve(output,'graph.html'),'utf8');expect(html).toContain('Architecture relationships');expect(html).toContain('module.development');
});
it('publishes the Agent instructions and Wire contracts projection pages as rendered projections',async()=>{
 const instructions=await readFile(resolve(output,'specs/projections/instructions.html'),'utf8');
 expect(instructions).toContain('concorde-main');expect(instructions).toContain('rendered projection');
 const wire=await readFile(resolve(output,'specs/projections/wire.html'),'utf8');
 expect(wire).toContain('concorde-main-request');expect(wire).toContain('rendered projection');
});
