import {copyFile,mkdir,rm,writeFile} from 'node:fs/promises';
import {dirname,resolve,posix} from 'node:path';
import matter from 'gray-matter';
import {rewriteLinks,safeRead,type ScopedRegistry,type Target} from './model';
import {hasDocsProjections,loadInstructionsProjection,loadWireProjection,renderInstructionsPage,renderWirePage} from './projections';
const PROJECTIONS_GROUP={type:'category',label:'Projections',collapsed:false,items:[
  {type:'doc',id:'projections/instructions',label:'Agent instructions'},
  {type:'doc',id:'projections/wire',label:'Wire contracts'},
]};
export function scopedSidebar(registry: ScopedRegistry) {
  const item=(target:Target):object=>({type:'category',label:target.title,collapsed:true,
    items:[...registry.pages.filter(p=>p.targetId===target.id).map(p=>({type:'doc',id:p.stagedPath.replace(/\.md$/,''),label:p.title})),
      ...registry.targets.filter(t=>(target.kind==='domain'?t.scope_parent:t.component_parent)===target.id).map(item)]});
  return [{type:'category',label:'Domain scopes',collapsed:false,items:registry.targets.filter(t=>t.kind==='domain'&&!t.scope_parent).map(item)},
    {type:'category',label:'Components',collapsed:false,items:registry.targets.filter(t=>t.kind!=='domain'&&!t.component_parent).map(item)},
    ...(hasDocsProjections(registry.projectRoot)?[PROJECTIONS_GROUP]:[])].filter(group=>group.items.length);
}
export async function materializeScoped(registry:ScopedRegistry) {
  const generated=resolve(registry.projectRoot,'docsite/.generated');
  const identity=resolve(generated,'scoped-materialization.json');
  await rm(identity,{force:true});
  await rm(resolve(generated,'content'),{recursive:true,force:true});
  await rm(resolve(generated,'static'),{recursive:true,force:true});
  await mkdir(resolve(generated,'static/diagrams'),{recursive:true});
  for(const page of registry.pages){
    const path=resolve(generated,'content/specs',page.stagedPath);await mkdir(dirname(path),{recursive:true});
    for (const diagram of page.architectureDiagrams ?? []) {
      const source=JSON.parse(safeRead(registry.projectRoot,diagram.source));
      const artifact=posix.normalize(posix.join(posix.dirname(diagram.source),source.meta.output));
      safeRead(registry.projectRoot,artifact);
      await copyFile(resolve(registry.projectRoot,artifact),resolve(generated,'static',diagram.route.slice(1)));
    }
    await writeFile(path,matter.stringify(rewriteLinks(registry,page),{format:'md',slug:page.route.slice('/specs'.length),title:page.title,sidebar_label:page.title}));
  }
  if(hasDocsProjections(registry.projectRoot)){
    const projectionsDirectory=resolve(generated,'content/specs/projections');
    await mkdir(projectionsDirectory,{recursive:true});
    const instructions=loadInstructionsProjection(registry.projectRoot);
    const wire=loadWireProjection(registry.projectRoot);
    await writeFile(resolve(projectionsDirectory,'instructions.md'),matter.stringify(renderInstructionsPage(instructions),
      {format:'md',slug:'/projections/instructions',title:'Agent instructions',sidebar_label:'Agent instructions'}));
    await writeFile(resolve(projectionsDirectory,'wire.md'),matter.stringify(renderWirePage(wire),
      {format:'md',slug:'/projections/wire',title:'Wire contracts',sidebar_label:'Wire contracts'}));
  }
  await writeFile(resolve(generated,'specs-sidebar.json'),JSON.stringify(scopedSidebar(registry),null,2)+'\n');
  await writeFile(identity,JSON.stringify({schema_version:1,sourceDigest:registry.sourceDigest})+'\n');
}
