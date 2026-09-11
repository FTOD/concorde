import {existsSync,mkdtempSync,mkdirSync,readFileSync,writeFileSync,rmSync,symlinkSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {resolve,dirname} from 'node:path';
import {beforeEach,afterEach,it,expect} from 'vitest';
import {legacyAliasRoute,loadScopedRegistry,rewriteLinks,primaryDocument,type Target} from '../plugins/scoped-content/model';
import {materializeScoped,scopedSidebar} from '../plugins/scoped-content/materialize';
import scopedContent,{validateScopedBuild} from '../plugins/scoped-content';
import {promoteCandidate} from '../scripts/build';
import type {LoadContext} from '@docusaurus/types';
interface SidebarItem {type:string; label:string; href?:string; id?:string; link?:{type:'doc';id:string}; collapsed?:boolean; items?:SidebarItem[]}
let root:string,targets:Target[];
function put(path:string,text:string){mkdirSync(dirname(resolve(root,path)),{recursive:true});writeFileSync(resolve(root,path),text);}
function target(id:string,documents:string[]):Target{return{id,kind:'module',title:id,documents,parent:null,uses:[],files:[],checks:[]};}
function save(){put('.concorde/specs.json',JSON.stringify({schema_version:3,project_id:'project.bank',entry_target:'scope.bank',targets,checks:[]}));}
/** A minimal, Protocol-compliant module.md body: Purpose, Requirements, Scenarios and Ontology
 * (Entities with a concorde-entities block, Relationships with a Mermaid flowchart) — appended
 * only when writing a target's own primary document, never a shared or secondary document. */
function requiredSections(owner:Target):string {
 const entityId='entity.'+owner.id.replace(/^[a-z]+\./,'').replace(/\./g,'-');
 return '\n\n## Purpose\n\nLocal purpose prose for '+owner.title+'.\n\n'+
  '## Requirements\n\nIntroductory requirement prose.\n\n'+
  '## Scenarios\n\nIntroductory scenario prose.\n\n'+
  '## Ontology\n\n### Entities\n\n```concorde-entities\n'+JSON.stringify([{id:entityId,title:owner.title,kind:'concept',responsibility:'Represents the module core responsibility.'}])+'\n```\n\n'+
  '### Relationships\n\n```mermaid\nflowchart TB\n    core["'+owner.title+'"]\n```\n';
}
function putSpec(path:string,references:string[],body:string,mainVisible=true){
 const id='document.'+path.replace(/\.md$/,'').replaceAll('/','.').replace(/[^a-z0-9.-]/g,'-');
 const owner=targets.find(t=>primaryDocument(t)===path);
 if(owner){
  if(!body.includes('## Purpose'))body+=requiredSections(owner);
  const peers=[...owner.uses,...targets.filter(t=>t.parent===owner.id).map(t=>t.id)];
  if(peers.length)body+='\n```concorde-dependencies\n'+JSON.stringify(peers.map(target_id=>({target_id,responsibility:'Provide the declared capability.',selection_condition:'Select for '+target_id,relied_upon_promises:['The interface returns a declared result or an explicit failure.']})))+'\n```\n';
 }
 put(path,'```concorde-document\n'+JSON.stringify({id,targets:references,main_visible:mainVisible},null,2)+'\n```\n\n'+body);
}
function updateDocument(path:string,updates:Record<string,unknown>){
 const text=readFileSync(resolve(root,path),'utf8');const match=text.match(/^```concorde-document\s*\n([\s\S]*?)^```/m)!;
 const value={...JSON.parse(match[1]),...updates};put(path,'```concorde-document\n'+JSON.stringify(value,null,2)+'\n```'+text.slice(match[0].length));
}
beforeEach(()=>{
 root=mkdtempSync(resolve(tmpdir(),'concorde-scoped-'));put('.concorde/config.json',JSON.stringify({profile_version:11,registry:'.concorde/specs.json'}));
 targets=[target('scope.bank',['specs/bank/module.md']),target('scope.audit',['specs/audit/module.md']),target('service.transfer',['specs/transfer/module.md','specs/transfer/promises.md']),target('module.ledger',['specs/ledger/module.md'])];
 targets[0].uses=['service.transfer'];targets[1].uses=['service.transfer'];targets[3].parent='service.transfer';
 targets[3].files=['src/ledger.ts'];put('src/ledger.ts','export const ledger = true;\n');
 const references=new Map<string,string[]>();for(const t of targets)for(const p of t.documents)references.set(p,[...(references.get(p)??[]),t.id]);
 for(const [p,ids] of references){const t=targets.find(target=>target.documents.includes(p))!;putSpec(p,ids,'# '+t.title+'\n\nLocal rules.');}
 save();
});
afterEach(()=>rmSync(root,{recursive:true,force:true}));
it('scenario.views.publish-repeat-without-graph: checked directory replacement removes obsolete output on consecutive promotions',async()=>{
 const obsolete=['graph.html','graph/index.html','architecture-graph.json','assets/obsolete-graph.js'];
 for(const path of obsolete)put('published/'+path,'previous graph output');
 for(let iteration=0;iteration<2;iteration++){
  const registry=loadScopedRegistry(root);await materializeScoped(registry);
  const plugin=scopedContent({siteDir:resolve(root,'docsite'),baseUrl:'/'} as LoadContext,{});
  await plugin.loadContent!();
  const outDir=resolve(root,'candidate');mkdirSync(outDir);
  // Stand in for rendered pages; admission and promotion use the real plugin and validator.
  for(const page of registry.pages)put('candidate/'+page.route.slice(1)+'.html',page.sourcePath);
  await plugin.postBuild!({outDir,routesPaths:registry.pages.map(page=>page.route)} as any);
  await validateScopedBuild(root,outDir);
  await promoteCandidate(outDir,resolve(root,'published'),resolve(root,'backup'));
  await validateScopedBuild(root,resolve(root,'published'));
  for(const path of obsolete)expect(existsSync(resolve(root,'published',path))).toBe(false);
  for(const page of registry.pages)
   expect(readFileSync(resolve(root,'published',page.route.slice(1)+'.html'),'utf8')).toBe(page.sourcePath);
 }
});
it('scenario.views.publish-without-graph: global data retains page metadata without bodies or architecture projections',async()=>{
 put('docsite/site.json',JSON.stringify({schema_version:1,title:'Bank',url:'https://localhost',baseUrl:'/',organizationName:'bank',projectName:'bank'}));
 const registry=loadScopedRegistry(root);await materializeScoped(registry);
 const plugin=scopedContent({siteDir:resolve(root,'docsite'),baseUrl:'/'} as LoadContext,{});
 let data:any;
 await plugin.contentLoaded!({content:registry,actions:{setGlobalData:(value:unknown)=>{data=value;}}} as any);
 expect(data.schema_version).toBe(18);
 expect(data.entryTarget).toBe(registry.entryTarget);
 expect(data.pages).toEqual(registry.pages.map(({content,...page})=>page));
 expect(data).not.toHaveProperty('nodes');expect(data).not.toHaveProperty('edges');
 expect(data).not.toHaveProperty('targets');
});
it('admits arbitrary multi-document collections without frontmatter or ambient discovery',()=>{put('specs/ignored.md','UNREGISTERED');const r=loadScopedRegistry(root);expect(r.pages).toHaveLength(5);expect(r.pages.some(p=>p.content.includes('UNREGISTERED'))).toBe(false);});
it('scenario.views.load-registry: separates private Module composition from shared sibling dependencies',()=>{const r=loadScopedRegistry(root);expect(r.targets.flatMap(t=>t.uses)).toHaveLength(2);expect(r.targets.find(t=>t.id==='module.ledger')?.parent).toBe('service.transfer');expect(r).not.toHaveProperty('edges');});
it('allows the same implementation file to be listed by more than one Module',()=>{
 targets[0].files=['src/shared.ts'];targets[1].files=['src/shared.ts'];save();put('src/shared.ts','export const shared = true;\n');
 const r=loadScopedRegistry(root);
 expect(r.targets.find(t=>t.id==='scope.bank')?.files).toEqual(['src/shared.ts']);
 expect(r.targets.find(t=>t.id==='scope.audit')?.files).toEqual(['src/shared.ts']);
});
it('admits files pending creation but rejects directories, generated paths and symlink bindings',()=>{
 targets[0].files=['src/future.ts'];save();expect(()=>loadScopedRegistry(root)).not.toThrow();
 mkdirSync(resolve(root,'src'),{recursive:true});targets[0].files=['src'];save();expect(()=>loadScopedRegistry(root)).toThrow(/must name a file/);
 targets[0].files=['generated/result.ts'];save();expect(()=>loadScopedRegistry(root)).toThrow(/Unsafe file binding/);
 symlinkSync(resolve(root,'missing'),resolve(root,'src/link'));targets[0].files=['src/link/file.ts'];save();
 expect(()=>loadScopedRegistry(root)).toThrow(/Symlink file binding/);
});
it('admits a directory prefix entry, shares it, and rejects a file or Spec document under it',()=>{
 // A trailing slash binds the regular files below the directory, existing and future alike.
 targets[0].files=['src/'];targets[1].files=['src/ledger.ts'];save();
 const r=loadScopedRegistry(root);
 expect(r.targets.find(t=>t.id==='scope.bank')?.files).toEqual(['src/']);
 expect(r.targets.find(t=>t.id==='scope.audit')?.files).toEqual(['src/ledger.ts']);
 // A directory pending creation is admitted; an existing entry must be the declared kind.
 targets[0].files=['src/future/'];save();expect(()=>loadScopedRegistry(root)).not.toThrow();
 targets[0].files=['src/ledger.ts/'];save();expect(()=>loadScopedRegistry(root)).toThrow(/must name a directory/);
 targets[0].files=['generated/'];save();expect(()=>loadScopedRegistry(root)).toThrow(/Unsafe file binding/);
 targets[0].files=['specs/'];save();expect(()=>loadScopedRegistry(root)).toThrow(/cannot contain a Spec document/);
 symlinkSync(resolve(root,'missing'),resolve(root,'src/linked'));targets[0].files=['src/linked/'];save();
 expect(()=>loadScopedRegistry(root)).toThrow(/Symlink file binding/);
});
it('rejects a file binding that names a registered Spec document',()=>{
 targets[0].files=['specs/audit/module.md'];save();
 expect(()=>loadScopedRegistry(root)).toThrow(/Unsafe file binding/);
});
it('rejects cycles and unknown Module parents',()=>{
 targets[0].parent='scope.audit';targets[1].parent='scope.bank';save();expect(()=>loadScopedRegistry(root)).toThrow(/cycle/);
 targets[0].parent=null;targets[1].parent=null;targets[3].parent='missing';save();expect(()=>loadScopedRegistry(root)).toThrow(/Unknown Module parent/);
});
it('supports explicitly shared documents but rejects duplicate members in one collection',()=>{
 targets[3].documents.push('specs/transfer/promises.md');save();updateDocument('specs/transfer/promises.md',{targets:['service.transfer','module.ledger']});
 const r=loadScopedRegistry(root);expect(r.pages).toHaveLength(5);
 const shared=r.pages.find(p=>p.sourcePath==='specs/transfer/promises.md')!;
 expect(shared.memberships.map(m=>m.targetId).sort()).toEqual(['module.ledger','service.transfer']);
 expect(shared.contextSection).toBe('shared_specs');
 targets[3].documents.push('specs/transfer/promises.md');save();expect(()=>loadScopedRegistry(root)).toThrow(/unique/);
});
it('validates document identity, exact references and visibility type',()=>{updateDocument('specs/transfer/promises.md',{targets:['service.transfer','module.ledger']});expect(()=>loadScopedRegistry(root)).toThrow(/differ/);updateDocument('specs/transfer/promises.md',{targets:['service.transfer']});updateDocument('specs/ledger/module.md',{id:'document.specs.transfer.promises'});expect(()=>loadScopedRegistry(root)).toThrow(/Duplicate document identity/);updateDocument('specs/ledger/module.md',{id:'document.specs.ledger.module'});updateDocument('specs/transfer/promises.md',{main_visible:'yes'});expect(()=>loadScopedRegistry(root)).toThrow(/main_visible/);});
it('binds source identity to content and membership order',()=>{const first=loadScopedRegistry(root).sourceDigest;targets[2].documents.reverse();save();const second=loadScopedRegistry(root).sourceDigest;expect(second).not.toBe(first);put('specs/transfer/promises.md',readFileSync(resolve(root,'specs/transfer/promises.md'),'utf8')+'\nChanged');expect(loadScopedRegistry(root).sourceDigest).not.toBe(second);});
it('rejects symlink path components',()=>{rmSync(resolve(root,'specs/transfer/module.md'));symlinkSync(resolve(root,'specs/transfer/promises.md'),resolve(root,'specs/transfer/module.md'));expect(()=>loadScopedRegistry(root)).toThrow(/Symlink/);});
it('scenario.views.publish-candidate: rewrites only registered navigation to canonical routes and leaves code examples intact',()=>{
 putSpec('specs/transfer/module.md',['service.transfer'],'# Use\n\n[Promise](promises.md)\n\n```md\n[Example](unknown.md)\n```');
 let r=loadScopedRegistry(root);let p=r.pages.find(p=>p.sourcePath==='specs/transfer/module.md')!;
 expect(rewriteLinks(r,p)).toContain('[Promise](/specs/transfer/promises)');
 expect(rewriteLinks(r,p)).toContain('[Example](unknown.md)');
 p.content+='\n[Wrong](unknown.md)';expect(()=>rewriteLinks(r,p)).toThrow(/Unregistered/);
});
it('derives readable canonical routes, staged paths and legacy alias routes from source paths',()=>{
 const r=loadScopedRegistry(root);
 const arbitrary=r.pages.find(p=>p.sourcePath==='specs/transfer/module.md')!;
 expect(arbitrary.route).toBe('/specs/transfer/module');expect(arbitrary.stagedPath).toBe('transfer/module.md');
 expect(arbitrary.aliases).toEqual([legacyAliasRoute('service.transfer','specs/transfer/module.md')]);
 const bank=r.pages.find(p=>p.sourcePath==='specs/bank/module.md')!;
 expect(bank.route).toBe('/specs/bank/module');expect(bank.stagedPath).toBe('bank/module.md');
 expect(bank.aliases).toEqual([legacyAliasRoute('scope.bank','specs/bank/module.md')]);
});
it('binds the Module category to module.md even when it is not the first member',()=>{
 const topic='specs/bank/routing.md';targets[0].documents.unshift(topic);putSpec(topic,['scope.bank'],'# Routing\nLocal routing facts.');save();
 const registry=loadScopedRegistry(root);const main=registry.pages.find(p=>p.memberships.some(m=>m.targetId==='scope.bank'&&m.primary))!;
 expect(primaryDocument(targets[0])).toBe('specs/bank/module.md');expect(main.sourcePath).toBe('specs/bank/module.md');
 const sidebar=scopedSidebar(registry) as SidebarItem[];
 const module=sidebar[0];
 expect(module.link).toEqual({type:'doc',id:'bank/module'});
 expect(module.items!.some(i=>i.id==='bank/module')).toBe(false);
 expect(registry.pages.filter(p=>p.memberships.some(m=>m.targetId==='scope.bank'))).toHaveLength(2);
});
it('requires one local Module entry and treats visibility as metadata',()=>{
 const main=targets[0].documents[0];targets[0].documents=['specs/unknown.md'];save();expect(()=>loadScopedRegistry(root)).toThrow(/module.md/);
 targets[0].documents=[main,'specs/extra/module.md'];save();expect(()=>loadScopedRegistry(root)).toThrow(/exactly one/);
 targets[0].documents=[main];targets[2].documents.push(main);save();updateDocument(main,{targets:['scope.bank','service.transfer']});expect(()=>loadScopedRegistry(root)).toThrow(/must be local|exactly one/);
 targets[2].documents.pop();save();updateDocument(main,{targets:['scope.bank'],main_visible:false});expect(loadScopedRegistry(root).pages.find(p=>p.sourcePath===main)?.mainVisible).toBe(false);
});
it('requires the Purpose, Requirements, Scenarios and Ontology headings on module.md, in order, with Entities and Relationships inside Ontology',()=>{
 const main=targets[0].documents[0];
 const section=(heading:string)=>`## ${heading}\n\nProse for ${heading}.\n`;
 const entities='### Entities\n\n```concorde-entities\n'+JSON.stringify([{id:'entity.bank.core',title:'Bank',kind:'concept',responsibility:'Represents the module.'}])+'\n```\n';
 const relationships='### Relationships\n\n```mermaid\nflowchart TB\n    core["Bank"]\n```\n';
 const ontology=['## Ontology\n',entities,relationships].join('\n');
 putSpec(main,['scope.bank'],[section('Purpose'),section('Requirements'),section('Scenarios'),ontology].join('\n'));save();
 expect(()=>loadScopedRegistry(root)).not.toThrow();
 putSpec(main,['scope.bank'],[section('Purpose'),section('Scenarios'),section('Requirements'),ontology].join('\n'));save();
 expect(()=>loadScopedRegistry(root)).toThrow(/Purpose, Requirements, Scenarios, Ontology/);
 putSpec(main,['scope.bank'],[section('Purpose'),section('Requirements'),section('Scenarios'),'## Ontology\n',relationships].join('\n'));save();
 expect(()=>loadScopedRegistry(root)).toThrow(/Entities, Relationships/);
 putSpec(main,['scope.bank'],[section('Purpose'),section('Requirements'),section('Scenarios'),'## Ontology\n',relationships,entities].join('\n'));save();
 expect(()=>loadScopedRegistry(root)).toThrow(/Entities, Relationships/);
 putSpec(main,['scope.bank'],[section('Purpose'),section('Requirements'),section('Scenarios'),'## Ontology\n',entities,'## Relationships\n\n```mermaid\nflowchart TB\n    core["Bank"]\n```\n'].join('\n'));save();
 expect(()=>loadScopedRegistry(root)).toThrow(/Entities, Relationships/);
 putSpec(main,['scope.bank'],[section('Purpose'),section('Requirements'),section('Scenarios'),'~~~~markdown\n## Ontology\n~~~~\n'].join('\n'));save();
 expect(()=>loadScopedRegistry(root)).toThrow(/Purpose, Requirements, Scenarios, Ontology/);
});
it('scenario.views.id-anchors: injects the ID of every scenario, requirement and entity as an anchor when materializing',async()=>{
 const main=targets[0].documents[0];
 const body=['## Purpose\n\nBank purpose.\n','## Requirements\n\n### req.bank.retry — Repeated requests\n\nBanking SHALL treat a repeated request as a new decision.\n',
  '## Scenarios\n\n#### scenario.bank.settle - Settlement\n\n- GIVEN a sender\n- WHEN a transfer is accepted\n- THEN both accounts settle\n\nSee [retry](#req.bank.retry) and [ledger](../ledger/module.md#entity.ledger.core).\n',
  '## Ontology\n\n### Entities\n\n```concorde-entities\n'+JSON.stringify([{id:'entity.bank.core',title:'Bank',kind:'concept',responsibility:'Represents the module.'},{id:'entity.bank.request',title:'Request',kind:'record',responsibility:'One transfer request.'}])+'\n```\n',
  '### Relationships\n\n```mermaid\nflowchart TB\n    core["Bank"]\n    request["Request"]\n    request -->|reaches| core\n```\n',
  '```markdown\n### req.bank.example — Not a definition\n```\n'].join('\n');
 putSpec(main,['scope.bank'],body);save();
 await materializeScoped(loadScopedRegistry(root));
 const page=readFileSync(resolve(root,'docsite/.generated/content/specs/bank/module.md'),'utf8');
 expect(page).toContain('### req.bank.retry — Repeated requests {#req.bank.retry}');
 expect(page).toContain('#### scenario.bank.settle - Settlement {#scenario.bank.settle}');
 expect(page).toContain('<a id="entity.bank.core"></a><a id="entity.bank.request"></a>\n\n```concorde-entities');
 expect(page).toContain('[retry](#req.bank.retry)');expect(page).toContain('[ledger](/specs/ledger/module#entity.ledger.core)');
 expect(page).toContain('### req.bank.example — Not a definition\n');expect(page).not.toContain('{#req.bank.example}');
});
it('rejects sources changed between materialization and plugin loading even when routes are unchanged',async()=>{
 const original=loadScopedRegistry(root);await materializeScoped(original);
 const staged=readFileSync(resolve(root,'docsite/.generated/content/specs/transfer/promises.md'),'utf8');
 expect(staged).toContain('title: promises');expect(staged).toContain('sidebar_label: promises');
 expect(staged).toContain('displayed_sidebar: moduleSpecsSidebar');
 const plugin=()=>scopedContent({siteDir:resolve(root,'docsite'),baseUrl:'/'} as LoadContext,{});
 expect((await plugin().loadContent!())?.sourceDigest).toBe(original.sourceDigest);
 put('specs/transfer/promises.md',readFileSync(resolve(root,'specs/transfer/promises.md'),'utf8')+'\nNew promise.');
 const changed=loadScopedRegistry(root);expect(changed.pages.map(p=>p.route)).toEqual(original.pages.map(p=>p.route));
 await expect(plugin().loadContent!()).rejects.toThrow(/Materialized Spec source identity differs/);
 await materializeScoped(changed);
 expect((await plugin().loadContent!())?.sourceDigest).toBe(changed.sourceDigest);
});
it('scenario.views.materialize: invalidates the previous materialization identity before a failed preparation',async()=>{
 await materializeScoped(loadScopedRegistry(root));
 put('specs/transfer/promises.md',readFileSync(resolve(root,'specs/transfer/promises.md'),'utf8')+'\n[Missing](missing.md)');
 await expect(materializeScoped(loadScopedRegistry(root))).rejects.toThrow(/Unregistered/);
 const plugin=scopedContent({siteDir:resolve(root,'docsite'),baseUrl:'/'} as LoadContext,{});
 await expect(plugin.loadContent!()).rejects.toThrow(/ENOENT/);
});
it('starts with Module roots and nests documents and children by registry ownership',()=>{
 targets[0].documents.push('specs/bank/routing.md');putSpec('specs/bank/routing.md',['scope.bank'],'# Routing\nLocal routing facts.');save();
 const sidebar=scopedSidebar(loadScopedRegistry(root));
 expect(sidebar.map(item=>item.label)).toEqual(['scope.bank','scope.audit','service.transfer']);
 expect(sidebar[0]).toMatchObject({type:'category',collapsed:false});
 expect(sidebar[0].items).toEqual([
  {type:'doc',id:'bank/routing',label:'routing'},
 ]);
 expect(sidebar[2].items!.at(-1)).toMatchObject({type:'doc',label:'module.ledger',id:'ledger/module'});
});
it('scenario.views.materialize: renders a Files section on a Module primary page from its bound files, and omits it when empty',async()=>{
 const registry=loadScopedRegistry(root);await materializeScoped(registry);
 const ledgerPage=readFileSync(resolve(root,'docsite/.generated/content/specs/ledger/module.md'),'utf8');
 expect(ledgerPage).toContain('## Files');expect(ledgerPage).toContain('`src/ledger.ts`');
 const bankPage=readFileSync(resolve(root,'docsite/.generated/content/specs/bank/module.md'),'utf8');
 expect(bankPage).not.toContain('## Files');
});
it('renders a directory prefix entry exactly as declared',async()=>{
 targets[3].files=['src/'];save();
 await materializeScoped(loadScopedRegistry(root));
 const ledgerPage=readFileSync(resolve(root,'docsite/.generated/content/specs/ledger/module.md'),'utf8');
 expect(ledgerPage).toContain('- `src/`');expect(ledgerPage).not.toContain('`src/ledger.ts`');
});
it('keeps one sidebar without duplicate document entries when a document is shared',()=>{
 targets[3].documents.push('specs/transfer/promises.md');save();
 updateDocument('specs/transfer/promises.md',{targets:['service.transfer','module.ledger']});
 const r=loadScopedRegistry(root);const sidebar=scopedSidebar(r);
 expect(sidebar.map(item=>item.label)).toEqual(['scope.bank','scope.audit','service.transfer']);
 const flatten=(items:SidebarItem[]):SidebarItem[]=>items.flatMap(item=>[item,...flatten(item.items??[])]);
 const items=flatten(sidebar);const docs=items.flatMap(item=>item.type==='doc'?[item.id]:item.link?[item.link.id]:[]);
 expect(docs).toHaveLength(r.pages.length);
 expect(new Set(docs).size).toBe(r.pages.length);
 expect(items.filter(item=>item.href==='/specs/transfer/promises')).toHaveLength(1);
});
it('strips the specs/ root only when every registered document is under it',()=>{
 targets[3].documents.push('docs/outside.md');putSpec('docs/outside.md',['module.ledger'],'# Outside\nNot under specs.');save();
 const registry=loadScopedRegistry(root);
 const outside=registry.pages.find(p=>p.sourcePath==='docs/outside.md')!;
 expect(outside.route).toBe('/specs/docs/outside');expect(outside.stagedPath).toBe('docs/outside.md');
 const bank=registry.pages.find(p=>p.sourcePath==='specs/bank/module.md')!;
 expect(bank.route).toBe('/specs/specs/bank/module');expect(bank.stagedPath).toBe('specs/bank/module.md');
});
it('rejects a canonical route that collides with an alias',()=>{
 const alias=legacyAliasRoute('service.transfer','specs/transfer/module.md');
 const collidingPath='specs'+alias.slice('/specs'.length)+'.md';
 targets[1].documents.push(collidingPath);putSpec(collidingPath,['scope.audit'],'# Colliding\nCrafted to collide with a legacy alias.');save();
 expect(()=>loadScopedRegistry(root)).toThrow(/collides with an alias/);
});
it('rejects a registered document staged under the reserved projections/ prefix',()=>{
 targets[1].documents.push('specs/projections/foo.md');putSpec('specs/projections/foo.md',['scope.audit'],'# Foo\nReserved staged path.');save();
 expect(()=>loadScopedRegistry(root)).toThrow(/[Pp]rojections/);
});
it('scenario.views.validate-candidate-mismatch: writes a legacy redirect stub for every alias during postBuild, and validateScopedBuild checks them',async()=>{
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
 expect(existsSync(resolve(outDir,'architecture-graph.json'))).toBe(false);
 const manifestPath=resolve(outDir,'build-manifest.json');
 const manifest=JSON.parse(readFileSync(manifestPath,'utf8'));
 writeFileSync(manifestPath,JSON.stringify({...manifest,schema_version:17}));
 await expect(validateScopedBuild(root,outDir)).rejects.toThrow(/Build Manifest 18/);
 writeFileSync(manifestPath,JSON.stringify(manifest));
 const [firstPage]=registry.pages;const [firstAlias]=firstPage.aliases;
 rmSync(resolve(outDir,firstAlias.slice(1)+'.html'));
 await expect(validateScopedBuild(root,outDir)).rejects.toThrow(/redirect stub/);
 rmSync(outDir,{recursive:true,force:true});
});

// Exercise the plugin's real post-build hook so no test bypasses route admission
// by manufacturing a successful manifest.
it('scenario.views.validate-candidate-mismatch: rejects every altered inventory without repairing it',async()=>{
 const registry=loadScopedRegistry(root);await materializeScoped(registry);
 const plugin=scopedContent({siteDir:resolve(root,'docsite'),baseUrl:'/'} as LoadContext,{});
 await plugin.loadContent!();
 const outDir=resolve(root,'candidate');mkdirSync(outDir);
 await plugin.postBuild!({outDir,routesPaths:registry.pages.map(p=>p.route)} as any);
 const path=resolve(outDir,'build-manifest.json');
 const original=readFileSync(path,'utf8');
 const manifest=JSON.parse(original);
 const variants=[
  '{invalid json',
  JSON.stringify({...manifest,sourceDigest:'sha256:'+'0'.repeat(64)}),
  JSON.stringify({...manifest,pages:manifest.pages.slice(1)}),
  JSON.stringify({...manifest,pages:[...manifest.pages].reverse()}),
  ...['sourcePath','route','contentDigest','targets','aliases'].map(field=>{
   const changed=JSON.parse(original);
   changed.pages[0][field]=Array.isArray(changed.pages[0][field])?[]:'changed';
   return JSON.stringify(changed);
  }),
 ];
 for(const bytes of variants){
  writeFileSync(path,bytes);
  await expect(validateScopedBuild(root,outDir)).rejects.toThrow();
  expect(readFileSync(path,'utf8')).toBe(bytes);
 }
 rmSync(path);
 await expect(validateScopedBuild(root,outDir)).rejects.toThrow();
 expect(existsSync(path)).toBe(false);
 writeFileSync(path,original);
 const stub=resolve(outDir,registry.pages[0].aliases[0].slice(1)+'.html');
 writeFileSync(stub,'<a href="/wrong">Wrong destination</a>');
 await expect(validateScopedBuild(root,outDir)).rejects.toThrow(/canonical route/);
 expect(readFileSync(stub,'utf8')).toBe('<a href="/wrong">Wrong destination</a>');
});

it('scenario.views.publish-preserves-previous-on-failure: postBuild refuses missing routes and changed sources before artifacts',async()=>{
 const registry=loadScopedRegistry(root);await materializeScoped(registry);
 const plugin=scopedContent({siteDir:resolve(root,'docsite'),baseUrl:'/'} as LoadContext,{});
 await plugin.loadContent!();
 const outDir=resolve(root,'candidate');mkdirSync(outDir);
 const routesPaths=registry.pages.map(p=>p.route);
 await expect(plugin.postBuild!({outDir,routesPaths:routesPaths.slice(1)} as any)).rejects.toThrow(/not rendered/);
 expect(existsSync(resolve(outDir,'build-manifest.json'))).toBe(false);
 const source='specs/transfer/promises.md';
 put(source,readFileSync(resolve(root,source),'utf8')+'\nChanged during build.');
 await expect(plugin.postBuild!({outDir,routesPaths} as any)).rejects.toThrow(/source changed/);
 expect(existsSync(resolve(outDir,'build-manifest.json'))).toBe(false);
});
