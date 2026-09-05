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
 const home=await readFile(resolve(output,'index.html'),'utf8');expect(home).toContain(r.pages.find(p=>p.targetId===r.entryTarget)!.route);
});
it('publishes the same typed relationship graph as the human navigation',async()=>{
 const graph=JSON.parse(await readFile(resolve(output,'architecture-graph.json'),'utf8'));const r=loadScopedRegistry(root);
 expect(graph.nodes).toEqual(r.targets);expect(graph.edges).toEqual(r.edges);
 const html=await readFile(resolve(output,'graph.html'),'utf8');expect(html).toContain('Architecture relationships');expect(html).toContain('service.workflow-host');
});
