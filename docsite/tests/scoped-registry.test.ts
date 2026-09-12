import {existsSync,mkdtempSync,mkdirSync,readFileSync,writeFileSync,rmSync,symlinkSync,readdirSync} from 'node:fs';
import {EventEmitter} from 'node:events';
import {createRequire} from 'node:module';
import {runInNewContext} from 'node:vm';
import {transpileModule,ModuleKind} from 'typescript';
import {evaluate} from '@mdx-js/mdx';
import * as jsxRuntime from 'react/jsx-runtime';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {tmpdir} from 'node:os';
import {resolve,dirname} from 'node:path';
import {beforeEach,afterEach,it,expect} from 'vitest';
import {injectAnchors,legacyAliasRoute,loadScopedRegistry,rewriteLinks,primaryDocument,requireScoped,type Target} from '../plugins/scoped-content/model';
import {materializeScoped,scopedSidebar,publicationSidebar} from '../plugins/scoped-content/materialize';
import scopedContent,{validateScopedBuild} from '../plugins/scoped-content';
import {customDocsConfiguration} from '../plugins/scoped-content/custom-docs';
import {parseSiteIdentity} from '../plugins/scoped-content/site-identity';
import {promoteCandidate} from '../scripts/build';
import {preparePublication,productionGeneratedDirectory} from '../scripts/prepare-publication';
import type {LoadContext} from '@docusaurus/types';
interface SidebarItem {type:string; label:string; href?:string; id?:string; link?:{type:'doc';id:string}; collapsed?:boolean; items?:SidebarItem[]}
let root:string,targets:Target[];
function put(path:string,text:string){mkdirSync(dirname(resolve(root,path)),{recursive:true});writeFileSync(resolve(root,path),text);}
function target(id:string,documents:string[]):Target{return{id,kind:'module',title:id,documents,references:[],parent:null,uses:[],files:[],checks:[]};}
function save(){put('.concorde/specs.json',JSON.stringify({schema_version:4,project_id:'project.bank',entry_target:'scope.bank',targets,checks:[]}));}
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
 put(path,'```concorde-document\n'+JSON.stringify({id,owner:references[0],main_visible:mainVisible},null,2)+'\n```\n\n'+body);
}
function updateDocument(path:string,updates:Record<string,unknown>){
 const text=readFileSync(resolve(root,path),'utf8');const match=text.match(/^```concorde-document\s*\n([\s\S]*?)^```/m)!;
 const value={...JSON.parse(match[1]),...updates};put(path,'```concorde-document\n'+JSON.stringify(value,null,2)+'\n```'+text.slice(match[0].length));
}
beforeEach(()=>{
 root=mkdtempSync(resolve(tmpdir(),'concorde-scoped-'));put('.concorde/config.json',JSON.stringify({profile_version:12,registry:'.concorde/specs.json'}));
 put('docsite/site.json',JSON.stringify({schema_version:1,title:'Bank',url:'https://localhost',baseUrl:'/',organizationName:'bank',projectName:'bank'}));
 targets=[target('scope.bank',['specs/bank/module.md']),target('scope.audit',['specs/audit/module.md']),target('service.transfer',['specs/transfer/module.md','specs/transfer/promises.md']),target('module.ledger',['specs/ledger/module.md'])];
 targets[0].uses=['service.transfer'];targets[1].uses=['service.transfer'];targets[3].parent='service.transfer';
 targets[3].files=['src/ledger.ts'];put('src/ledger.ts','export const ledger = true;\n');
 const references=new Map<string,string[]>();for(const t of targets)for(const p of t.documents)references.set(p,[...(references.get(p)??[]),t.id]);
 for(const [p,ids] of references){const t=targets.find(target=>target.documents.includes(p))!;putSpec(p,ids,'# '+t.title+'\n\nLocal rules.');}
 save();
});
afterEach(()=>rmSync(root,{recursive:true,force:true}));
it('scenario.views.publish-reference-link: one-level references retain all provenance without transclusion',async()=>{
 targets[0].references=[{kind:'module',id:'service.transfer'},{kind:'document',id:'document.specs.transfer.promises'}];
 targets[2].references=[{kind:'module',id:'module.ledger'}];
 targets[3].references=[{kind:'module',id:'scope.bank'}];save();
 const r=loadScopedRegistry(root);
 const promise=r.pages.find(p=>p.sourcePath==='specs/transfer/promises.md')!;
 expect(promise.owner).toBe('service.transfer');
 expect(promise.includedBy.find(p=>p.targetId==='scope.bank')!.reasons).toEqual([
  {kind:'document',id:'document.specs.transfer.promises'},{kind:'module',id:'service.transfer'}]);
 expect(r.pages.find(p=>p.sourcePath==='specs/ledger/module.md')!.includedBy.map(p=>p.targetId)).not.toContain('scope.bank');
 expect(r.pages.filter(p=>p.documentId===promise.documentId)).toHaveLength(1);
 putSpec('specs/bank/module.md',['scope.bank'],'# Banking\n\n[Agreement](../transfer/promises.md)');
 const linked=loadScopedRegistry(root);await materializeScoped(linked);
 const body=readFileSync(resolve(root,'docsite/.generated/content/specs/bank/module.md'),'utf8');
 expect(body).toContain('[Agreement](/specs/transfer/promises)');
 expect(body).not.toContain('Local rules.');
 const before=linked.sourceDigest;
 targets[0].references.pop();save();
 expect(loadScopedRegistry(root).pages.map(p=>p.sourcePath)).toEqual(linked.pages.map(p=>p.sourcePath));
 expect(loadScopedRegistry(root).sourceDigest).not.toBe(before);
});
it('canonical contracts have one definition anchor and bindings require their included version',()=>{
 const definition={id:'contract.read',version:2,schema:{type:'integer'},semantics:'Return a balance.',example:42};
 const binding={id:'contract.read',version:2,role:'provided',peer:'service.transfer',selection_condition:'When reading.',relied_upon_guarantees:['Return a balance.'],obligations:['Handle missing accounts.']};
 const fence=(kind:string,value:unknown)=>'\n```'+kind+'\n'+JSON.stringify(value)+'\n```\n';
 put('specs/ledger/module.md',readFileSync(resolve(root,'specs/ledger/module.md'),'utf8')+fence('concorde-contract',definition)+fence('concorde-contract-binding',binding));
 put('specs/transfer/module.md',readFileSync(resolve(root,'specs/transfer/module.md'),'utf8')+fence('concorde-contract-binding',{...binding,role:'required',peer:'module.ledger'}));
 expect(()=>loadScopedRegistry(root)).toThrow(/Missing context definition/);
 targets[2].references=[{kind:'document',id:'document.specs.ledger.module'}];save();
 const r=loadScopedRegistry(root);
 expect(injectAnchors(r.pages.find(p=>p.owner==='module.ledger')!.content).match(/<a id="contract.read"><\/a>/g)).toHaveLength(1);
 expect(injectAnchors(r.pages.find(p=>p.primaryOf==='service.transfer')!.content)).not.toContain('<a id="contract.read">');
});
it('rejects wrong-kind references and malformed UTF-8 source bytes',()=>{
 targets[0].references=[{kind:'document',id:'service.transfer'}];save();
 expect(()=>loadScopedRegistry(root)).toThrow(/Unknown or self reference/);
 targets[0].references=[];save();
 const path=resolve(root,'specs/bank/module.md');
 writeFileSync(path,Buffer.concat([readFileSync(path),Buffer.from([255])]));
 expect(()=>loadScopedRegistry(root)).toThrow();
});
it('scenario.views.materialize scenario.views.publish-candidate scenario.views.publish-without-graph: materialized navigation preserves Module category and leaf links',async()=>{
 targets[3].references.push({kind:'document',id:'document.specs.transfer.promises'});save();
 updateDocument('specs/transfer/promises.md',{owner:'service.transfer'});
 const registry=loadScopedRegistry(root),sidebar=publicationSidebar(registry);
 const flatten=(items:SidebarItem[]):SidebarItem[]=>items.flatMap(item=>[item,...flatten(item.items??[])]);
 const all=flatten(sidebar);
 const docs=all.flatMap(item=>item.type==='doc'?[item.id]:item.link?[item.link.id]:[]);
 expect(docs).toHaveLength(registry.pages.length);
 expect(new Set(docs).size).toBe(registry.pages.length);
 expect(sidebar.some(item=>['Module composition','transfer','Projections'].includes(item.label!))).toBe(false);
 const module=sidebar.find(item=>item.label==='service.transfer')!;
 expect(module.link).toEqual({type:'doc',id:'transfer/module'});
 expect(module.items).toEqual([
  {type:'doc',id:'transfer/promises',label:'promises'},
  {type:'doc',label:'module.ledger',id:'ledger/module'},
 ]);
 expect(sidebar.find(item=>item.label==='scope.audit')).toEqual(
  {type:'doc',id:'audit/module',label:'scope.audit'});
 expect(flatten(module.items!).some(item=>item.id==='transfer/module')).toBe(false);
 expect(flatten(sidebar).filter(item=>item.href==='/specs/transfer/promises')).toHaveLength(0);
 await materializeScoped(registry);
 const materialized=JSON.parse(readFileSync(resolve(root,'docsite/.generated/specs-sidebar.json'),'utf8'));
 expect(materialized.moduleSpecsSidebar).toEqual(sidebar);
 expect(all.some(item=>item.label==='Graph'||item.href==='/graph')).toBe(false);
 expect(existsSync(resolve(root,'docsite/.generated/static/architecture-graph.json'))).toBe(false);
});
it('scenario.views.publish-candidate: ignores retired projections and removes staged copies',async()=>{
 const registry=loadScopedRegistry(root);
 for(const name of ['instructions','wire']) {
  put('generated/docs/'+name+'.json','{invalid retired input');
  put('docsite/.generated/content/specs/projections/'+name+'.md','Retired page');
 }
 await materializeScoped(registry);
 expect(existsSync(resolve(root,'docsite/.generated/content/specs/projections'))).toBe(false);
 expect(scopedSidebar(registry).some(item=>item.label==='Projections')).toBe(false);
 expect(loadScopedRegistry(root).sourceDigest).toBe(registry.sourceDigest);
});
it('scenario.views.publish-repeat-without-graph: checked directory replacement removes obsolete output on consecutive promotions',async()=>{
 const obsolete=['graph.html','graph/index.html','architecture-graph.json','assets/obsolete-graph.js','specs/projections/instructions.html','specs/projections/wire.html'];
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
 expect(data.schema_version).toBe(19);
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
 targets[3].references.push({kind:'document',id:'document.specs.transfer.promises'});save();updateDocument('specs/transfer/promises.md',{owner:'service.transfer'});
 const r=loadScopedRegistry(root);expect(r.pages).toHaveLength(5);
 const shared=r.pages.find(p=>p.sourcePath==='specs/transfer/promises.md')!;
 expect(shared.includedBy.map(m=>m.targetId).sort()).toEqual(['module.ledger','service.transfer']);
 expect(shared.owner).toBe('service.transfer');
 targets[3].references.push({kind:'document',id:'document.specs.transfer.promises'});save();expect(()=>loadScopedRegistry(root)).toThrow(/Duplicate reference/);
});
it('validates document identity, exact references and visibility type',()=>{updateDocument('specs/transfer/promises.md',{owner:'module.ledger'});expect(()=>loadScopedRegistry(root)).toThrow(/differ/);updateDocument('specs/transfer/promises.md',{owner:'service.transfer'});updateDocument('specs/ledger/module.md',{id:'document.specs.transfer.promises'});expect(()=>loadScopedRegistry(root)).toThrow(/Duplicate document identity/);updateDocument('specs/ledger/module.md',{id:'document.specs.ledger.module'});updateDocument('specs/transfer/promises.md',{main_visible:'yes'});expect(()=>loadScopedRegistry(root)).toThrow(/main_visible/);});
it('binds source identity to content and membership order',()=>{const first=loadScopedRegistry(root).sourceDigest;targets[2].documents.reverse();save();const second=loadScopedRegistry(root).sourceDigest;expect(second).not.toBe(first);put('specs/transfer/promises.md',readFileSync(resolve(root,'specs/transfer/promises.md'),'utf8')+'\nChanged');expect(loadScopedRegistry(root).sourceDigest).not.toBe(second);});
it('rejects symlink path components',()=>{rmSync(resolve(root,'specs/transfer/module.md'));symlinkSync(resolve(root,'specs/transfer/promises.md'),resolve(root,'specs/transfer/module.md'));expect(()=>loadScopedRegistry(root)).toThrow(/Symlink/);});
it('scenario.views.publish-candidate: rewrites only registered navigation to canonical routes and leaves code examples intact',()=>{
 putSpec('specs/transfer/module.md',['service.transfer'],'# Use\n\n[Promise](promises.md)\n\n```md\n[Example](unknown.md)\n```');
 let r=loadScopedRegistry(root);let p=r.pages.find(p=>p.sourcePath==='specs/transfer/module.md')!;
 expect(rewriteLinks(r,p)).toContain('[Promise](/specs/transfer/promises)');
 expect(rewriteLinks(r,p)).toContain('[Example](unknown.md)');
 p.content+='\n[Wrong](unknown.md)';expect(()=>rewriteLinks(r,p)).toThrow(/Unregistered/);
});
it('scenario.views.materialize scenario.views.publish-legacy-redirect: source lookup preserves query and fragment suffixes',async()=>{
 const links=[
  ['../transfer/promises.md?view=compact#promise','/specs/transfer/promises?view=compact#promise'],
  ['?view=compact','/specs/bank/module?view=compact'],
  ['?view=compact#purpose','/specs/bank/module?view=compact#purpose'],
  ['../transfer/promises.md?next=a?b#promise','/specs/transfer/promises?next=a?b#promise'],
  ['../transfer/promises.md#promise?detail','/specs/transfer/promises#promise?detail'],
  ['../transfer/promises.md?next=a?b#promise?detail#more','/specs/transfer/promises?next=a?b#promise?detail#more'],
  ['../transfer/promises.md?#','/specs/transfer/promises?#'],
  ['https://example.com/page?view=compact#promise','https://example.com/page?view=compact#promise'],
  ['mailto:reader@example.com?subject=Read','mailto:reader@example.com?subject=Read'],
  ['/specs/transfer/promises?view=compact#promise','/specs/transfer/promises?view=compact#promise'],
  ['#purpose?detail','#purpose?detail'],
 ];
 const unchanged='[Reference][promise]\n\n[promise]: ../transfer/promises.md?view=compact#promise\n\n```md\n[Example](unknown.md?view=compact#promise)\n```';
 putSpec('specs/bank/module.md',['scope.bank'],'# Bank\n\n'+links.map(([url],i)=>`[Link ${i}](${url})`).join('\n')+'\n\n'+unchanged);
 const original=readFileSync(resolve(root,'specs/bank/module.md'));
 const registry=loadScopedRegistry(root),page=registry.pages.find(p=>p.sourcePath==='specs/bank/module.md')!;
 const rewritten=rewriteLinks(registry,page);
 await materializeScoped(registry);
 const staged=readFileSync(resolve(root,'docsite/.generated/content/specs/bank/module.md'),'utf8');
 for(const text of [rewritten,staged]){
  for(const [,destination] of links)expect(text).toContain(`](${destination})`);
  expect(text).toContain(unchanged);
 }
 expect(readFileSync(resolve(root,'specs/bank/module.md'))).toEqual(original);
});
it('scenario.views.materialize: an unknown source with a query still rejects',async()=>{
 putSpec('specs/bank/module.md',['scope.bank'],'# Bank\n\n[Unknown](unknown.md?view=compact#promise)');
 const registry=loadScopedRegistry(root),page=registry.pages[0];
 expect(()=>rewriteLinks(registry,page)).toThrow('Unregistered local link: specs/bank/module.md -> unknown.md?view=compact#promise');
 await expect(materializeScoped(registry)).rejects.toThrow(/Unregistered local link/);
 expect(existsSync(resolve(root,'docsite/.generated/scoped-materialization.json'))).toBe(false);
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
 const registry=loadScopedRegistry(root);const main=registry.pages.find(p=>p.primaryOf==='scope.bank')!;
 expect(primaryDocument(targets[0])).toBe('specs/bank/module.md');expect(main.sourcePath).toBe('specs/bank/module.md');
 const sidebar=scopedSidebar(registry) as SidebarItem[];
 const module=sidebar[0];
 expect(module.link).toEqual({type:'doc',id:'bank/module'});
 expect(module.items!.some(i=>i.id==='bank/module')).toBe(false);
 expect(registry.pages.filter(p=>p.owner==='scope.bank')).toHaveLength(2);
});
it('requires one local Module entry and treats visibility as metadata',()=>{
 const main=targets[0].documents[0];targets[0].documents=['specs/unknown.md'];save();expect(()=>loadScopedRegistry(root)).toThrow(/module.md/);
 targets[0].documents=[main,'specs/extra/module.md'];save();expect(()=>loadScopedRegistry(root)).toThrow(/exactly one/);
 targets[0].documents=[main];targets[2].documents.push(main);save();updateDocument(main,{owner:'scope.bank'});expect(()=>loadScopedRegistry(root)).toThrow(/one owner|must be local|exactly one/);
 targets[2].documents.pop();save();updateDocument(main,{owner:'scope.bank',main_visible:false});expect(loadScopedRegistry(root).pages.find(p=>p.sourcePath===main)?.mainVisible).toBe(false);
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
it('scenario.views.publish-candidate: starts with Module roots and nests documents and children by registry ownership',()=>{
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
 targets[3].references.push({kind:'document',id:'document.specs.transfer.promises'});save();
 updateDocument('specs/transfer/promises.md',{owner:'service.transfer'});
 const r=loadScopedRegistry(root);const sidebar=scopedSidebar(r);
 expect(sidebar.map(item=>item.label)).toEqual(['scope.bank','scope.audit','service.transfer']);
 const flatten=(items:SidebarItem[]):SidebarItem[]=>items.flatMap(item=>[item,...flatten(item.items??[])]);
 const items=flatten(sidebar);const docs=items.flatMap(item=>item.type==='doc'?[item.id]:item.link?[item.link.id]:[]);
 expect(docs).toHaveLength(r.pages.length);
 expect(new Set(docs).size).toBe(r.pages.length);
 expect(items.filter(item=>item.href==='/specs/transfer/promises')).toHaveLength(0);
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
it('allows registered documents under the formerly reserved projections/ prefix',()=>{
 targets[1].documents.push('specs/projections/foo.md');putSpec('specs/projections/foo.md',['scope.audit'],'# Foo\nReserved staged path.');save();
 expect(loadScopedRegistry(root).pages.some(page=>page.route==='/specs/projections/foo')).toBe(true);
});
it('scenario.views.validate-candidate-mismatch: writes a legacy redirect stub for every alias during postBuild, and validateScopedBuild checks them',async()=>{
 const registry=loadScopedRegistry(root);await materializeScoped(registry);
 const plugin=scopedContent({siteDir:resolve(root,'docsite'),baseUrl:'/'} as LoadContext,{});
 await plugin.loadContent!();
 const outDir=mkdtempSync(resolve(tmpdir(),'concorde-outdir-'));
 const routesPaths=registry.pages.map(p=>p.route);
 for(const page of registry.pages){const file=resolve(outDir,page.route.slice(1)+'.html');mkdirSync(dirname(file),{recursive:true});writeFileSync(file,'<main>Rendered page</main>');}
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
 await expect(validateScopedBuild(root,outDir)).rejects.toThrow(/Build Manifest 19/);
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
  ...['sourcePath','route','contentDigest','owner','includedBy','aliases'].map(field=>{
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

it('scenario.views.publish-legacy-redirect: validates current cross-Module links and executes alias redirects',async()=>{
 targets[2].documents=targets[2].documents.filter(path=>path!=='specs/transfer/promises.md');
 targets[0].documents.push('specs/transfer/promises.md');save();
 putSpec('specs/transfer/promises.md',['scope.bank'],'# Promise\n\n## Promise {#promise}\n\nRetained agreement.');
 putSpec('specs/bank/module.md',['scope.bank'],'# Bank\n\n[Source reference](../transfer/promises.md#promise)\n\n[Canonical reference](/specs/transfer/promises#promise)\n\n[Retained form][agreement]\n\n[agreement]: /specs/transfer/promises#promise');
 put('specs/bank/module.md',readFileSync(resolve(root,'specs/bank/module.md'),'utf8')+'\n[Query source reference](../transfer/promises.md?view=compact&next=a?b#promise)\n');
 const originalSource=readFileSync(resolve(root,'specs/bank/module.md'));
 const before=loadScopedRegistry(root);await materializeScoped(before);
 expect(before.pages.find(page=>page.sourcePath==='specs/transfer/promises.md')!.owner).toEqual('scope.bank');
 const oldAlias=legacyAliasRoute('scope.bank','specs/transfer/promises.md');
 targets[0].documents.pop();targets[2].documents.push('specs/transfer/promises.md');save();
 updateDocument('specs/transfer/promises.md',{owner:'service.transfer'});
 const registry=loadScopedRegistry(root);await materializeScoped(registry);
 expect(registry.targets[0].documents).not.toContain('specs/transfer/promises.md');
 const page=registry.pages.find(page=>page.sourcePath==='specs/transfer/promises.md')!;
 const referring=registry.pages[0];
 expect(readFileSync(resolve(root,'specs/bank/module.md'))).toEqual(originalSource);
 const staged=readFileSync(resolve(root,'docsite/.generated/content/specs/bank/module.md'),'utf8');
 expect(staged).toContain('[Source reference](/specs/transfer/promises#promise)');
 expect(staged).toContain('[Query source reference](/specs/transfer/promises?view=compact&next=a?b#promise)');
 expect(staged).toContain('[Canonical reference](/specs/transfer/promises#promise)');
 expect(page.owner).toEqual('service.transfer');
 const plugin=scopedContent({siteDir:resolve(root,'docsite'),baseUrl:'/'} as LoadContext,{});
 await plugin.loadContent!();
 const outDir=resolve(root,'candidate');mkdirSync(outDir);
 for(const entry of registry.pages)put('candidate/'+entry.route.slice(1)+'.html','<h1 id="promise">Promise</h1>');
 await plugin.postBuild!({outDir,routesPaths:registry.pages.map(page=>page.route)} as any);
 const referrer='candidate/'+referring.route.slice(1)+'.html';
 // Use the installed Markdown/MDX renderer for the actual retained source references,
 // including reference syntax that rewriteLinks intentionally leaves untouched.
 const rewritten=rewriteLinks(registry,referring);
 expect(rewritten).toContain('[Retained form][agreement]');
 const rendered=await evaluate(rewritten,{...jsxRuntime});
 put(referrer,renderToStaticMarkup(createElement(rendered.default)));
 expect(readFileSync(resolve(root,referrer),'utf8')).toContain('>Retained form</a>');
 await expect(validateScopedBuild(root,outDir)).resolves.toBeUndefined();
 for(const destination of [page.route,page.aliases[0]]){
  put(referrer,`<a href="${destination}?view=full#promise">Read</a>`);
  await expect(validateScopedBuild(root,outDir)).resolves.toBeUndefined();
 }
 for(const destination of [oldAlias+'#promise',page.route+'#missing']){
  put(referrer,`<a href="${destination}">Read</a>`);
  await expect(validateScopedBuild(root,outDir)).rejects.toThrow(/Unresolved internal navigation/);
 }
 const stub=readFileSync(resolve(outDir,page.aliases[0].slice(1)+'.html'),'utf8');
 const script=stub.match(/<script>([\s\S]*?)<\/script>/)![1];
 for(const [search,hash] of [['?view=full&mode=a%20b','#promise'],['','#promise'],['?view=full','']]){
  const redirected:string[]=[];
  runInNewContext(script,{location:{search,hash,replace:(url:string)=>redirected.push(url)}});
  expect(redirected).toEqual([page.route+search+hash]);
 }
});

it.each(['/', '/%E6%96%87%E6%A1%A3/'])('scenario.views.build-site scenario.views.publish-preserves-previous-on-failure scenario.views.validate-candidate-mismatch scenario.views.publish-repeat-without-graph: real pipeline preserves former graph output on failure and replaces it on success (%s)',async(baseUrl)=>{
 const identity=JSON.parse(readFileSync(resolve(root,'docsite/site.json'),'utf8'));
 put('docsite/site.json',JSON.stringify({...identity,baseUrl}));
 const navigation=(route:string)=>baseUrl.toLowerCase()+route.slice(1);
 const nativeRequire=createRequire(import.meta.url);
 const buildPath=resolve(__dirname,'../scripts/build.ts');
 const compiled=transpileModule(readFileSync(buildPath,'utf8'),{compilerOptions:{module:ModuleKind.CommonJS}}).outputText;
 let destination=navigation('/specs/transfer/promises#promise');
 let renderCount=0;
 let failure:'none'|'source'|'manifest'='none';
 // Execute the actual build module with this fixture as its site directory. Only the
 // Docusaurus child is controlled: preparation, postBuild, validation and promotion run live.
 const fixtureModule={exports:{} as {buildSite:()=>Promise<void>}};
 const spawn=()=>{
  const child=new EventEmitter();
  queueMicrotask(async()=>{
   try{
    const registry=loadScopedRegistry(root);
    const outDir=resolve(root,'docsite/.generated/candidate');
    for(const page of registry.pages)put('docsite/.generated/candidate/'+page.route.slice(1)+'.html',
     `<h1 id="promise">Promise</h1><a href="${destination}">Read</a>`);
    const plugin=scopedContent({siteDir:resolve(root,'docsite'),baseUrl} as LoadContext,{});
    await plugin.loadContent!();
    await plugin.postBuild!({outDir,routesPaths:registry.pages.map(page=>baseUrl+page.route.slice(1))} as any);
    if(failure==='source')put('specs/transfer/promises.md',
     readFileSync(resolve(root,'specs/transfer/promises.md'),'utf8')+'\nChanged after postBuild.');
    if(failure==='manifest'){
     const path=resolve(outDir,'build-manifest.json');
     const manifest=JSON.parse(readFileSync(path,'utf8'));
     writeFileSync(path,JSON.stringify({...manifest,schema_version:17}));
    }
    renderCount++;child.emit('exit',0);
   }catch(error){child.emit('error',error);}
  });
  return child;
 };
 runInNewContext(compiled,{
  module:fixtureModule,exports:fixtureModule.exports,__dirname:resolve(root,'docsite/scripts'),process,
  require:(id:string)=>{
   if(id==='node:child_process')return{spawn};
   if(id==='../plugins/scoped-content/model')return{requireScoped};
   if(id==='../plugins/scoped-content')return{validateScopedBuild};
   if(id==='./prepare-publication')return{preparePublication,productionGeneratedDirectory};
   return nativeRequire(id);
  },
 });
 const snapshot=(directory:string):Record<string,Buffer>=>{
  const result:Record<string,Buffer>={};
  const walk=(path:string)=>{for(const entry of readdirSync(resolve(directory,path),{withFileTypes:true})){
   const name=path+entry.name;
   if(entry.isDirectory())walk(name+'/');else result[name]=readFileSync(resolve(directory,name));
  }};
  walk('');return result;
 };
 await fixtureModule.exports.buildSite();
 const published=resolve(root,'docsite/build');
 const obsolete=['graph.html','graph/index.html','architecture-graph.json','assets/obsolete-graph.js','specs/projections/instructions.html','specs/projections/wire.html'];
 for(const path of obsolete)put('docsite/build/'+path,'previous graph output');
 const previous=snapshot(published);
 expect(Object.keys(previous)).toContain('build-manifest.json');
 expect(Object.keys(previous).length).toBeGreaterThan(5);
 for(const bad of ['/missing','/specs/transfer/promises#missing',legacyAliasRoute('scope.bank','specs/transfer/promises.md')+'#promise']){
  destination=navigation(bad);
  await expect(fixtureModule.exports.buildSite()).rejects.toThrow(/Unresolved internal navigation.*to /);
  expect(snapshot(published)).toEqual(previous);
  expect(existsSync(resolve(root,'docsite/.generated/candidate'))).toBe(false);
  expect(existsSync(resolve(root,'docsite/.generated/previous-build'))).toBe(false);
 }
 destination=navigation('/specs/transfer/promises#promise');
 const source=readFileSync(resolve(root,'specs/transfer/promises.md'),'utf8');
 for(const invalid of ['source','manifest'] as const){
  failure=invalid;
  await expect(fixtureModule.exports.buildSite()).rejects.toThrow(/Build Manifest 19/);
  expect(snapshot(published)).toEqual(previous);
  expect(existsSync(resolve(root,'docsite/.generated/candidate'))).toBe(false);
  expect(existsSync(resolve(root,'docsite/.generated/previous-build'))).toBe(false);
  put('specs/transfer/promises.md',source);
 }
 failure='none';
 for(let repeat=0;repeat<2;repeat++){
  await fixtureModule.exports.buildSite();
  await expect(validateScopedBuild(root,published)).resolves.toBeUndefined();
  for(const path of obsolete)expect(existsSync(resolve(published,path))).toBe(false);
  expect(readFileSync(resolve(published,'specs/bank/module.html'),'utf8')).toContain(destination);
 }
 expect(renderCount).toBe(8);
});

it('scenario.views.materialize scenario.views.build-site: rejects invalid materialization identities before emitting verification artifacts',async()=>{
 const registry=loadScopedRegistry(root);await materializeScoped(registry);
 const plugin=scopedContent({siteDir:resolve(root,'docsite'),baseUrl:'/'} as LoadContext,{});
 await plugin.loadContent!();
 const outDir=resolve(root,'candidate');mkdirSync(outDir);
 const identity='docsite/.generated/scoped-materialization.json';
 for(const bytes of [null,'{malformed',JSON.stringify({schema_version:19,sourceDigest:registry.sourceDigest}),
  JSON.stringify({schema_version:1,sourceDigest:'sha256:'+'0'.repeat(64)})]){
  if(bytes===null)rmSync(resolve(root,identity));else put(identity,bytes);
  await expect(plugin.postBuild!({outDir,routesPaths:registry.pages.map(page=>page.route)} as any)).rejects.toThrow();
  expect(existsSync(resolve(outDir,'build-manifest.json'))).toBe(false);
 }
});


it('scenario.views.custom-docs: rejects registered Spec sources in a custom collection',()=>{
 const registry=loadScopedRegistry(root);
 const identity=parseSiteIdentity({schema_version:1,title:'Bank',url:'https://example.com',baseUrl:'/',organizationName:'bank',projectName:'bank',
  customDocs:[{id:'guides',label:'Guides',path:'../specs',routeBasePath:'guides'}]});
 expect(()=>customDocsConfiguration(resolve(root,'docsite'),identity,registry)).toThrow(/includes registered Spec/);
});

it('scenario.views.custom-docs: rejects a custom page at a registered legacy alias before writing redirects',async()=>{
 const registry=loadScopedRegistry(root);await materializeScoped(registry);
 const plugin=scopedContent({siteDir:resolve(root,'docsite'),baseUrl:'/'} as LoadContext,{});
 await plugin.loadContent!();
 const alias=registry.pages[0].aliases[0];
 const outDir=resolve(root,'candidate');mkdirSync(outDir);
 put('candidate/'+alias.slice(1)+'.html','Custom page');
 await expect(plugin.postBuild!({outDir,routesPaths:[...registry.pages.map(page=>page.route),alias]} as any)).rejects.toThrow(/conflicts with registered Spec alias/);
 expect(readFileSync(resolve(outDir,alias.slice(1)+'.html'),'utf8')).toBe('Custom page');
});

it('scenario.views.publish-candidate scenario.views.materialize: labels and order ignore headings and directories',async()=>{
 const supplement='specs/bank/elsewhere/notes.md';
 targets[2].documents.unshift(supplement);targets[2].title='Transfers';
 putSpec(supplement,['service.transfer'],'# Unrelated heading\n\nSupplement.');
 targets[0].references=[{kind:'module',id:'service.transfer'}];
 targets[1].references=[{kind:'document',id:'document.specs.bank.elsewhere.notes'}];save();
 const registry=loadScopedRegistry(root),sidebar=scopedSidebar(registry);
 expect(sidebar.map(item=>item.label)).toEqual(['scope.bank','scope.audit','Transfers']);
 expect(sidebar[2]).toMatchObject({link:{type:'doc',id:'transfer/module'},items:[
  {type:'doc',id:'bank/elsewhere/notes',label:'notes'},
  {type:'doc',id:'transfer/promises',label:'promises'},
  {type:'doc',id:'ledger/module',label:'module.ledger'},
 ]});
 const refs=(items:SidebarItem[]):string[]=>items.flatMap(item=>[
  ...(item.id?[item.id]:item.link?[item.link.id]:[]),...refs(item.items??[])]);
 expect(refs(sidebar).sort()).toEqual(registry.pages.map(page=>page.stagedPath.replace(/\.md$/,'')).sort());
 await materializeScoped(registry);
 expect(readFileSync(resolve(root,'docsite/.generated/content/specs/bank/elsewhere/notes.md'),'utf8')).toContain('sidebar_label: notes');
});

it('scenario.views.custom-docs: adds collection and executable tabs without changing registered context inputs',()=>{
 const before=loadScopedRegistry(root);
 put('docsite/custom-docs/guides/index.md','---\nslug: /\n---\n# Handbook');
 put('docsite/custom-docs/sidebar.js','module.exports = {guides: ["index"]};');
 put('docsite/custom-docs/index.ts','module.exports.default = {plugins: ["example-plugin"], navbarItems: [{to: "/app", label: "App", position: "left"}]};');
 const identity=parseSiteIdentity({...JSON.parse(readFileSync(resolve(root,'docsite/site.json'),'utf8')),
  customDocs:[{id:'guides',label:'Handbook',path:'./custom-docs/guides',routeBasePath:'handbook',sidebarPath:'custom-docs/sidebar.js'}]});
 const custom=customDocsConfiguration(resolve(root,'docsite'),identity,before);
 expect(custom.plugins).toEqual([
  ['@docusaurus/plugin-content-docs',expect.objectContaining({id:'guides',routeBasePath:'handbook',sidebarPath:resolve(root,'docsite/custom-docs/sidebar.js')})],
  'example-plugin',
 ]);
 expect(custom.navbarItems.map(item=>item.label)).toEqual(['Handbook','App']);
 expect(custom.docsRouteBasePath).toEqual(['/handbook']);
 expect(custom.docsDir).toEqual(['./custom-docs/guides']);
 put('docsite/site.json',JSON.stringify({...JSON.parse(readFileSync(resolve(root,'docsite/site.json'),'utf8')),customDocs:identity.customDocs}));
 expect(loadScopedRegistry(root)).toEqual(before);
});

it.each(['missing','file','sidebar'])('scenario.views.custom-docs: rejects unavailable collection input %s',kind=>{
 put('docsite/guide-file.md','# A file');put('docsite/guides/index.md','---\nslug: /\n---\n# Guide');
 const identity=parseSiteIdentity({...JSON.parse(readFileSync(resolve(root,'docsite/site.json'),'utf8')),
  customDocs:[{id:'guides',label:'Guides',path:kind==='missing'?'missing':kind==='file'?'guide-file.md':'guides',
   routeBasePath:'guides',...(kind==='sidebar'?{sidebarPath:'missing-sidebar.ts'}:{})}]});
 expect(()=>customDocsConfiguration(resolve(root,'docsite'),identity,loadScopedRegistry(root))).toThrow();
});

it('scenario.views.materialize: ignores stale unregistered projection inputs',async()=>{
 const before=loadScopedRegistry(root);
 put('generated/docs/instructions.json','invalid stale JSON');put('generated/docs/wire.json','invalid stale JSON');
 const after=loadScopedRegistry(root);expect(after).toEqual(before);await materializeScoped(after);
 expect(existsSync(resolve(root,'docsite/.generated/content/specs/projections'))).toBe(false);
});

it.each(['[]','{plugins: "bad"}','{navbarItems: {}}'])('scenario.views.custom-docs: rejects malformed executable extension %s',value=>{
 put('docsite/custom-docs/index.ts','module.exports.default = '+value+';');
 const identity=parseSiteIdentity(JSON.parse(readFileSync(resolve(root,'docsite/site.json'),'utf8')));
 expect(()=>customDocsConfiguration(resolve(root,'docsite'),identity,loadScopedRegistry(root))).toThrow(/custom-docs\/index.ts/);
});
