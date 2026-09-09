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
 const html=await readFile(resolve(output,'graph.html'),'utf8');expect(html).toContain('Architecture relationships');expect(html).toContain('service.workflow-host');
});
it('publishes the Agent instructions and Wire contracts projection pages as rendered projections',async()=>{
 const instructions=await readFile(resolve(output,'specs/projections/instructions.html'),'utf8');
 expect(instructions).toContain('concorde-main');expect(instructions).toContain('rendered projection');
 const wire=await readFile(resolve(output,'specs/projections/wire.html'),'utf8');
 expect(wire).toContain('concorde-main-request');expect(wire).toContain('rendered projection');
});
