import {mkdtempSync,mkdirSync,readFileSync,writeFileSync,rmSync,symlinkSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {resolve,dirname} from 'node:path';
import {beforeEach,afterEach,it,expect} from 'vitest';
import {hash,legacyAliasRoute,loadScopedRegistry,rewriteLinks,primaryDocument,type Target} from '../plugins/scoped-content/model';
import {materializeScoped,scopedSidebar} from '../plugins/scoped-content/materialize';
import scopedContent,{validateScopedBuild} from '../plugins/scoped-content';
import type {LoadContext} from '@docusaurus/types';
interface SidebarItem {type:string; label:string; href?:string; id?:string; collapsed?:boolean; items?:SidebarItem[]}
let root:string,targets:Target[];
function put(path:string,text:string){mkdirSync(dirname(resolve(root,path)),{recursive:true});writeFileSync(resolve(root,path),text);}
function target(id:string,kind:Target['kind'],documents:string[]):Target{return{id,kind,title:id,documents,scope_parent:null,component_parent:null,participates_in:[],implementation:[],features:[],apis:[],checks:[],diagrams:[]};}
function save(){put('.concorde/specs.json',JSON.stringify({schema_version:1,project_id:'project.bank',entry_target:'scope.bank',targets,checks:[]}));}
function putSpec(path:string,references:string[],body:string,mainVisible=references.some(id=>targets.find(t=>t.id===id)?.kind!=='module')){
 const id='document.'+path.replace(/\.md$/,'').replaceAll('/','.').replace(/[^a-z0-9.-]/g,'-');
 put(path,'```concorde-document\n'+JSON.stringify({id,targets:references,main_visible:mainVisible},null,2)+'\n```\n\n'+body);
}
function updateDocument(path:string,updates:Record<string,unknown>){
 const text=readFileSync(resolve(root,path),'utf8');const match=text.match(/^```concorde-document\s*\n([\s\S]*?)^```/m)!;
 const value={...JSON.parse(match[1]),...updates};put(path,'```concorde-document\n'+JSON.stringify(value,null,2)+'\n```'+text.slice(match[0].length));
}
beforeEach(()=>{
 root=mkdtempSync(resolve(tmpdir(),'concorde-scoped-'));put('.concorde/config.json',JSON.stringify({profile_version:8,registry:'.concorde/specs.json'}));
 targets=[target('scope.bank','domain',['specs/bank/ontology.md']),target('scope.audit','domain',['specs/audit/ontology.md']),target('service.transfer','service',['specs/arbitrary.md','specs/promises.md']),target('module.ledger','module',['specs/api.md'])];
 targets[2].participates_in=['scope.bank','scope.audit'];targets[3].component_parent='service.transfer';targets[3].apis=[{id:'api.read',title:'Read',document:'specs/api.md'}];
 for(const t of targets.filter(t=>t.kind==='domain')){
  const source=dirname(t.documents[0])+'/overview.json';const output='generated/diagrams/'+t.id+'.html';
  t.diagrams=[{source,kind:'architecture',title:t.title,recipe:'system-overview'}];
  put(source,JSON.stringify({schema_version:1,diagram_type:'architecture',meta:{title:t.title,quality_profile:'showcase',output:'../../'+output},components:[{id:'local',type:'backend',label:t.title}]}));
  put(output,'<!doctype html><p>Test diagram artifact</p>');
 }
 const references=new Map<string,string[]>();for(const t of targets)for(const p of t.documents)references.set(p,[...(references.get(p)??[]),t.id]);
 for(const [p,ids] of references){const t=targets.find(target=>target.documents.includes(p))!;putSpec(p,ids,'# '+t.title+'\n\n'+(t.kind==='module'?'## api.read\nread(id) returns balance.':t.kind==='domain'?'## Ontology\nLocal rules.':'Local rules.'));}
 save();
});
afterEach(()=>rmSync(root,{recursive:true,force:true}));
it('admits arbitrary multi-document collections without frontmatter or ambient discovery',()=>{put('specs/ignored.md','UNREGISTERED');const r=loadScopedRegistry(root);expect(r.pages).toHaveLength(5);expect(r.pages.some(p=>p.content.includes('UNREGISTERED'))).toBe(false);});
it('separates component composition and multiple scope participation',()=>{const r=loadScopedRegistry(root);expect(r.edges.filter(e=>e.kind==='participates_in')).toHaveLength(2);expect(r.edges.find(e=>e.kind==='composes')).toMatchObject({source:'service.transfer',target:'module.ledger'});});
it('rejects cycles and incorrect parent dimensions',()=>{targets[0].scope_parent='scope.audit';targets[1].scope_parent='scope.bank';save();expect(()=>loadScopedRegistry(root)).toThrow(/cycle/);targets[0].scope_parent=null;targets[1].scope_parent=null;targets[3].component_parent='scope.bank';save();expect(()=>loadScopedRegistry(root)).toThrow(/dimension/);});
it('supports explicitly shared documents but rejects duplicate members in one collection',()=>{
 targets[3].documents.push('specs/promises.md');save();updateDocument('specs/promises.md',{targets:['service.transfer','module.ledger']});
 const r=loadScopedRegistry(root);expect(r.pages).toHaveLength(5);
 const shared=r.pages.find(p=>p.sourcePath==='specs/promises.md')!;
 expect(shared.memberships.map(m=>m.targetId).sort()).toEqual(['module.ledger','service.transfer']);
 expect(shared.contextSection).toBe('shared_specs');
 targets[3].documents.push('specs/promises.md');save();expect(()=>loadScopedRegistry(root)).toThrow(/unique/);
});
it('validates document identity, exact references and visibility type',()=>{updateDocument('specs/promises.md',{targets:['service.transfer','module.ledger']});expect(()=>loadScopedRegistry(root)).toThrow(/differ/);updateDocument('specs/promises.md',{targets:['service.transfer']});updateDocument('specs/api.md',{id:'document.specs.promises'});expect(()=>loadScopedRegistry(root)).toThrow(/Duplicate document identity/);updateDocument('specs/api.md',{id:'document.specs.api'});updateDocument('specs/promises.md',{main_visible:'yes'});expect(()=>loadScopedRegistry(root)).toThrow(/main_visible/);});
it('binds source identity to content and membership order',()=>{const first=loadScopedRegistry(root).sourceDigest;targets[2].documents.reverse();save();const second=loadScopedRegistry(root).sourceDigest;expect(second).not.toBe(first);put('specs/promises.md',readFileSync(resolve(root,'specs/promises.md'),'utf8')+'\nChanged');expect(loadScopedRegistry(root).sourceDigest).not.toBe(second);});
it('rejects symlink path components',()=>{rmSync(resolve(root,'specs/arbitrary.md'));symlinkSync(resolve(root,'specs/promises.md'),resolve(root,'specs/arbitrary.md'));expect(()=>loadScopedRegistry(root)).toThrow(/Symlink/);});
it('rewrites only registered navigation to canonical routes and leaves code examples intact',()=>{
 putSpec('specs/arbitrary.md',['service.transfer'],'# Use\n\n[Promise](promises.md)\n\n```md\n[Example](unknown.md)\n```');
 let r=loadScopedRegistry(root);let p=r.pages.find(p=>p.sourcePath==='specs/arbitrary.md')!;
 expect(rewriteLinks(r,p)).toContain('[Promise](/specs/promises)');
 expect(rewriteLinks(r,p)).toContain('[Example](unknown.md)');
 p.content+='\n[Wrong](unknown.md)';expect(()=>rewriteLinks(r,p)).toThrow(/Unregistered/);
});
it('exposes Module APIs directly and independent navigation trees',()=>{const r=loadScopedRegistry(root);expect(scopedSidebar(r).map(g=>g.label)).toEqual(['Specs by source path','Specs by target']);targets[3].features=[{id:'feature.ledger',title:'Artificial',document:'specs/api.md'}];save();expect(()=>loadScopedRegistry(root)).toThrow(/APIs/);});
it('derives readable canonical routes, staged paths and legacy alias routes from source paths',()=>{
 const r=loadScopedRegistry(root);
 const arbitrary=r.pages.find(p=>p.sourcePath==='specs/arbitrary.md')!;
 expect(arbitrary.route).toBe('/specs/arbitrary');expect(arbitrary.stagedPath).toBe('arbitrary.md');
 expect(arbitrary.aliases).toEqual([legacyAliasRoute('service.transfer','specs/arbitrary.md')]);
 const bank=r.pages.find(p=>p.sourcePath==='specs/bank/ontology.md')!;
 expect(bank.route).toBe('/specs/bank/ontology');expect(bank.stagedPath).toBe('bank/ontology.md');
 expect(bank.aliases).toEqual([legacyAliasRoute('scope.bank','specs/bank/ontology.md')]);
});
it('binds the Domain category and diagram to ontology.md even when it is not the first member',()=>{
 const topic='specs/bank/routing.md';targets[0].documents.unshift(topic);putSpec(topic,['scope.bank'],'# Routing\nLocal routing facts.');save();
 const registry=loadScopedRegistry(root);const main=registry.pages.find(p=>p.memberships.some(m=>m.targetId==='scope.bank'&&m.primary))!;
 expect(primaryDocument(targets[0])).toBe('specs/bank/ontology.md');expect(main.sourcePath).toBe('specs/bank/ontology.md');
 expect(main.architectureDiagrams).toHaveLength(1);expect(registry.pages.find(p=>p.sourcePath===topic)?.architectureDiagrams).toBeUndefined();
 const sidebar=scopedSidebar(registry) as SidebarItem[];
 const domain=sidebar[1].items![0].items![0];
 expect(domain.items![0]).toEqual({type:'link',label:'scope.bank · Main Spec',href:main.route});
 expect(domain.items!.filter(i=>i.href===main.route)).toHaveLength(1);
 expect(registry.pages.filter(p=>p.memberships.some(m=>m.targetId==='scope.bank'))).toHaveLength(2);
});
it('rejects missing, duplicate, shared or hidden Domain main Specs',()=>{
 const main=targets[0].documents[0];targets[0].documents=['specs/unknown.md'];save();expect(()=>loadScopedRegistry(root)).toThrow(/ontology.md/);
 targets[0].documents=[main,'specs/extra/ontology.md'];save();expect(()=>loadScopedRegistry(root)).toThrow(/exactly one/);
 targets[0].documents=[main];targets[2].documents.push(main);save();updateDocument(main,{targets:['scope.bank','service.transfer']});expect(()=>loadScopedRegistry(root)).toThrow(/must be local/);
 targets[2].documents.pop();save();updateDocument(main,{targets:['scope.bank'],main_visible:false});expect(()=>loadScopedRegistry(root)).toThrow(/main_visible/);
});
it('requires a real Ontology section and the System overview recipe',()=>{
 const main=targets[0].documents[0];const original=readFileSync(resolve(root,main),'utf8');
 put(main,original.replace('## Ontology','## Vocabulary')+'\n~~~~markdown\n## Ontology\n~~~~\n');
 expect(()=>loadScopedRegistry(root)).toThrow(/Ontology section/);put(main,original);
 const diagram=targets[0].diagrams[0];targets[0].diagrams=[];save();expect(()=>loadScopedRegistry(root)).toThrow(/System overview/);
 targets[0].diagrams=[{...diagram,kind:'workflow'}];save();expect(()=>loadScopedRegistry(root)).toThrow(/architecture/);
});
it('rejects sources changed between materialization and plugin loading even when routes are unchanged',async()=>{
 const original=loadScopedRegistry(root);await materializeScoped(original);
 const plugin=()=>scopedContent({siteDir:resolve(root,'docsite'),baseUrl:'/'} as LoadContext,{});
 expect((await plugin().loadContent!())?.sourceDigest).toBe(original.sourceDigest);
 put('specs/promises.md',readFileSync(resolve(root,'specs/promises.md'),'utf8')+'\nNew promise.');
 const changed=loadScopedRegistry(root);expect(changed.pages.map(p=>p.route)).toEqual(original.pages.map(p=>p.route));
 await expect(plugin().loadContent!()).rejects.toThrow(/Materialized Spec source identity differs/);
 await materializeScoped(changed);
 expect((await plugin().loadContent!())?.sourceDigest).toBe(changed.sourceDigest);
});
it('invalidates the previous materialization identity before a failed preparation',async()=>{
 await materializeScoped(loadScopedRegistry(root));
 put('specs/promises.md',readFileSync(resolve(root,'specs/promises.md'),'utf8')+'\n[Missing](missing.md)');
 await expect(materializeScoped(loadScopedRegistry(root))).rejects.toThrow(/Unregistered/);
 const plugin=scopedContent({siteDir:resolve(root,'docsite'),baseUrl:'/'} as LoadContext,{});
 await expect(plugin.loadContent!()).rejects.toThrow(/ENOENT/);
});
it('mirrors the registered source-path directory structure with directories before files, both alphabetical',()=>{
 targets[0].documents.push('specs/bank/routing.md');putSpec('specs/bank/routing.md',['scope.bank'],'# Routing\nLocal routing facts.');save();
 const registry=loadScopedRegistry(root);
 const tree=scopedSidebar(registry)[0] as {label:string;collapsed:boolean;items:{type:string;label:string;collapsed?:boolean;items?:{type:string;label:string}[]}[]};
 expect(tree.label).toBe('Specs by source path');expect(tree.collapsed).toBe(false);
 const [audit,bank,...files]=tree.items;
 expect(audit).toMatchObject({type:'category',label:'audit',collapsed:false});
 expect(bank).toMatchObject({type:'category',label:'bank',collapsed:false});
 expect(bank.items!.map(i=>({type:i.type,label:i.label}))).toEqual([{type:'doc',label:'ontology.md'},{type:'doc',label:'routing.md'}]);
 expect(files.map(f=>f.label)).toEqual(['api.md','arbitrary.md','promises.md']);
 expect(files.every(f=>f.type==='doc')).toBe(true);
});
it('strips the specs/ root only when every registered document is under it',()=>{
 targets[3].documents.push('docs/outside.md');putSpec('docs/outside.md',['module.ledger'],'# Outside\nNot under specs.');save();
 const registry=loadScopedRegistry(root);
 const outside=registry.pages.find(p=>p.sourcePath==='docs/outside.md')!;
 expect(outside.route).toBe('/specs/docs/outside');expect(outside.stagedPath).toBe('docs/outside.md');
 const bank=registry.pages.find(p=>p.sourcePath==='specs/bank/ontology.md')!;
 expect(bank.route).toBe('/specs/specs/bank/ontology');expect(bank.stagedPath).toBe('specs/bank/ontology.md');
});
it('rejects a canonical route that collides with a legacy alias route',()=>{
 const alias=legacyAliasRoute('service.transfer','specs/arbitrary.md');
 const collidingPath='specs'+alias.slice('/specs'.length)+'.md';
 targets[1].documents.push(collidingPath);putSpec(collidingPath,['scope.audit'],'# Colliding\nCrafted to collide with a legacy alias.');save();
 expect(()=>loadScopedRegistry(root)).toThrow(/collides with a legacy alias route/);
});
it('rejects a registered document staged under the reserved projections/ prefix',()=>{
 targets[1].documents.push('specs/projections/foo.md');putSpec('specs/projections/foo.md',['scope.audit'],'# Foo\nReserved staged path.');save();
 expect(()=>loadScopedRegistry(root)).toThrow(/[Pp]rojections/);
});
it('writes a legacy redirect stub for every alias during postBuild, and validateScopedBuild checks them',async()=>{
 const registry=loadScopedRegistry(root);await materializeScoped(registry);
 const plugin=scopedContent({siteDir:resolve(root,'docsite'),baseUrl:'/'} as LoadContext,{});
 await plugin.loadContent!();
 const outDir=mkdtempSync(resolve(tmpdir(),'concorde-outdir-'));
 const routesPaths=registry.pages.map(p=>p.route);
 // eslint-disable-next-line @typescript-eslint/no-explicit-any
 await plugin.postBuild!({outDir,routesPaths} as any);
 for(const page of registry.pages) for(const alias of page.aliases){
  const stub=readFileSync(resolve(outDir,alias.slice(1)+'.html'),'utf8');
  expect(stub).toContain(page.route);expect(stub).toContain('refresh');
 }
 await expect(validateScopedBuild(root,outDir)).resolves.toBeUndefined();
 const manifestPath=resolve(outDir,'build-manifest.json');
 const manifest=JSON.parse(readFileSync(manifestPath,'utf8'));
 writeFileSync(manifestPath,JSON.stringify({...manifest,schema_version:14}));
 await expect(validateScopedBuild(root,outDir)).rejects.toThrow(/Build Manifest 15/);
 writeFileSync(manifestPath,JSON.stringify(manifest));
 const [firstPage]=registry.pages;const [firstAlias]=firstPage.aliases;
 rmSync(resolve(outDir,firstAlias.slice(1)+'.html'));
 await expect(validateScopedBuild(root,outDir)).rejects.toThrow(/redirect stub/);
 rmSync(outDir,{recursive:true,force:true});
});
