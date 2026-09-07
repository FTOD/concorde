import {mkdtempSync,mkdirSync,readFileSync,writeFileSync,rmSync,symlinkSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {resolve,dirname} from 'node:path';
import {beforeEach,afterEach,it,expect} from 'vitest';
import {loadScopedRegistry,rewriteLinks,type Target} from '../plugins/scoped-content/model';
import {materializeScoped,scopedSidebar} from '../plugins/scoped-content/materialize';
import scopedContent from '../plugins/scoped-content';
import type {LoadContext} from '@docusaurus/types';
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
 targets=[target('scope.bank','domain',['specs/meaning.md']),target('scope.audit','domain',['specs/audit.md']),target('service.transfer','service',['specs/arbitrary.md','specs/promises.md']),target('module.ledger','module',['specs/api.md'])];
 targets[2].participates_in=['scope.bank','scope.audit'];targets[3].component_parent='service.transfer';targets[3].apis=[{id:'api.read',title:'Read',document:'specs/api.md'}];
 const references=new Map<string,string[]>();for(const t of targets)for(const p of t.documents)references.set(p,[...(references.get(p)??[]),t.id]);
 for(const [p,ids] of references){const t=targets.find(target=>target.documents.includes(p))!;putSpec(p,ids,'# '+t.title+'\n\n'+(t.kind==='module'?'## api.read\nread(id) returns balance.':'Local rules.'));}
 save();
});
afterEach(()=>rmSync(root,{recursive:true,force:true}));
it('admits arbitrary multi-document collections without frontmatter or ambient discovery',()=>{put('specs/ignored.md','UNREGISTERED');const r=loadScopedRegistry(root);expect(r.pages).toHaveLength(5);expect(r.pages.some(p=>p.content.includes('UNREGISTERED'))).toBe(false);});
it('separates component composition and multiple scope participation',()=>{const r=loadScopedRegistry(root);expect(r.edges.filter(e=>e.kind==='participates_in')).toHaveLength(2);expect(r.edges.find(e=>e.kind==='composes')).toMatchObject({source:'service.transfer',target:'module.ledger'});});
it('rejects cycles and incorrect parent dimensions',()=>{targets[0].scope_parent='scope.audit';targets[1].scope_parent='scope.bank';save();expect(()=>loadScopedRegistry(root)).toThrow(/cycle/);targets[0].scope_parent=null;targets[1].scope_parent=null;targets[3].component_parent='scope.bank';save();expect(()=>loadScopedRegistry(root)).toThrow(/dimension/);});
it('supports explicitly shared documents but rejects duplicate members in one collection',()=>{targets[3].documents.push('specs/promises.md');save();updateDocument('specs/promises.md',{targets:['service.transfer','module.ledger']});const r=loadScopedRegistry(root);expect(r.pages).toHaveLength(6);expect(r.pages.filter(p=>p.sourcePath==='specs/promises.md').every(p=>p.contextSection==='shared_specs')).toBe(true);targets[3].documents.push('specs/promises.md');save();expect(()=>loadScopedRegistry(root)).toThrow(/unique/);});
it('validates document identity, exact references and visibility type',()=>{updateDocument('specs/promises.md',{targets:['service.transfer','module.ledger']});expect(()=>loadScopedRegistry(root)).toThrow(/differ/);updateDocument('specs/promises.md',{targets:['service.transfer']});updateDocument('specs/api.md',{id:'document.specs.promises'});expect(()=>loadScopedRegistry(root)).toThrow(/Duplicate document identity/);updateDocument('specs/api.md',{id:'document.specs.api'});updateDocument('specs/promises.md',{main_visible:'yes'});expect(()=>loadScopedRegistry(root)).toThrow(/main_visible/);});
it('binds source identity to content and membership order',()=>{const first=loadScopedRegistry(root).sourceDigest;targets[2].documents.reverse();save();const second=loadScopedRegistry(root).sourceDigest;expect(second).not.toBe(first);put('specs/promises.md',readFileSync(resolve(root,'specs/promises.md'),'utf8')+'\nChanged');expect(loadScopedRegistry(root).sourceDigest).not.toBe(second);});
it('rejects symlink path components',()=>{rmSync(resolve(root,'specs/arbitrary.md'));symlinkSync(resolve(root,'specs/promises.md'),resolve(root,'specs/arbitrary.md'));expect(()=>loadScopedRegistry(root)).toThrow(/Symlink/);});
it('rewrites only registered navigation and leaves code examples intact',()=>{putSpec('specs/arbitrary.md',['service.transfer'],'# Use\n\n[Promise](promises.md)\n\n```md\n[Example](unknown.md)\n```');let r=loadScopedRegistry(root);let p=r.pages.find(p=>p.sourcePath==='specs/arbitrary.md')!;expect(rewriteLinks(r,p)).toContain('/specs/service.transfer/');expect(rewriteLinks(r,p)).toContain('[Example](unknown.md)');p.content+='\n[Wrong](unknown.md)';expect(()=>rewriteLinks(r,p)).toThrow(/Unregistered/);});
it('exposes Module APIs directly and independent navigation trees',()=>{const r=loadScopedRegistry(root);expect(scopedSidebar(r).map(g=>g.label)).toEqual(['Domain scopes','Components']);targets[3].features=[{id:'feature.ledger',title:'Artificial',document:'specs/api.md'}];save();expect(()=>loadScopedRegistry(root)).toThrow(/APIs/);});
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
