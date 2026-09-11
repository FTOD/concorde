import {mkdir,rm,writeFile} from 'node:fs/promises';
import {dirname,resolve} from 'node:path';
import matter from 'gray-matter';
import {injectAnchors,primaryDocument,rewriteLinks,type Page,type ScopedRegistry,type Target} from './model';
import {hasDocsProjections,loadInstructionsProjection,loadWireProjection,renderInstructionsPage,renderWirePage} from './projections';
const PROJECTIONS_GROUP={type:'category',label:'Projections',collapsed:false,items:[
  {type:'doc',id:'projections/instructions',label:'Agent instructions'},
  {type:'doc',id:'projections/wire',label:'Wire contracts'},
]};
interface SidebarItem {type:string; label:string; id?:string; href?:string; link?:{type:'doc';id:string}; collapsed?:boolean; items?:SidebarItem[]}
export function scopedSidebar(registry: ScopedRegistry): SidebarItem[] {
  const byPath = new Map(registry.pages.map(p=>[p.sourcePath,p]));
  const placed = new Set<string>();
  const id=(page:Page)=>page.stagedPath.replace(/\.md$/,'');
  // Shared Module documents remain reachable from every owner, with one Docusaurus doc entry.
  const document=(page:Page):SidebarItem=>{
    if (placed.has(page.sourcePath)) return {type:'link',label:page.title,href:page.route};
    placed.add(page.sourcePath);
    return {type:'doc',id:id(page),label:page.title};
  };
  const item=(target:Target,depth=0):SidebarItem=>{
    const main=byPath.get(primaryDocument(target))!;
    placed.add(main.sourcePath);
    const items=[
      ...target.documents.filter(path=>path!==main.sourcePath).map(path=>document(byPath.get(path)!)),
      ...registry.targets.filter(t=>t.parent===target.id).map(child=>item(child,depth+1)),
    ];
    // The Module itself opens module.md; there is no extra main-Spec child entry.
    return items.length
      ? {type:'category',label:main.title,link:{type:'doc',id:id(main)},collapsed:depth>0,items}
      : {type:'doc',id:id(main),label:main.title};
  };
  return [
    ...registry.targets.filter(t=>!t.parent).map(target=>item(target)),
    ...(hasDocsProjections(registry.projectRoot)?[PROJECTIONS_GROUP]:[]),
  ];
}
/** Registered source paths supply the reading tree; composition is a linked secondary view. */
export function publicationSidebar(registry:ScopedRegistry):SidebarItem[] {
  interface Directory {items:Map<string,Directory|Page>}
  const tree:Directory={items:new Map()};
  for(const page of registry.pages){
    const parts=page.stagedPath.split('/');let directory=tree;
    for(const part of parts.slice(0,-1)){
      if(!directory.items.has(part))directory.items.set(part,{items:new Map()});
      directory=directory.items.get(part) as Directory;
    }
    directory.items.set(parts.at(-1)!,page);
  }
  // Composition owns the doc references so Module categories can open their entries.
  // Directory appearances link to the same canonical pages without duplicate doc IDs.
  const render=(directory:Directory):SidebarItem[]=>[...directory.items].map(([name,value])=>{
    if('sourcePath' in value)return {type:'link',label:value.title,href:value.route};
    return {type:'category',label:name,collapsed:false,items:render(value)};
  });
  return [...render(tree),{type:'category',label:'Module composition',collapsed:true,
    items:scopedSidebar(registry).filter(item=>item!==PROJECTIONS_GROUP)},
    ...(hasDocsProjections(registry.projectRoot)?[PROJECTIONS_GROUP]:[])];
}
export async function materializeScoped(registry:ScopedRegistry) {
  const generated=resolve(registry.projectRoot,'docsite/.generated');
  const identity=resolve(generated,'scoped-materialization.json');
  await rm(identity,{force:true});
  await rm(resolve(generated,'content'),{recursive:true,force:true});
  await rm(resolve(generated,'static'),{recursive:true,force:true});
  const filesByTargetId=new Map(registry.targets.map(t=>[t.id,t.files]));
  for(const page of registry.pages){
    const path=resolve(generated,'content/specs',page.stagedPath);await mkdir(dirname(path),{recursive:true});
    // A Module's declared listing entries, exact files and directory prefixes alike, listed on its
    // own primary Spec page; the complete inventory stays in the registered `concorde-entities`
    // blocks, this is a reading convenience only.
    const files=page.primaryOf?filesByTargetId.get(page.primaryOf):undefined;
    const filesSection=files?.length?`\n\n## Files\n\n${files.map(f=>`- \`${f}\``).join('\n')}\n`:'';
    // Identity is displayed by ContentProvenance; keep machine-readable metadata out of the
    // reading flow while leaving the authored source and its digest intact. Scenario, requirement
    // and entity IDs become anchors so that `path#id` links reach their definitions.
    const content=injectAnchors(rewriteLinks(registry,page).replace(/^```concorde-document\s*\n[\s\S]*?^```\s*$/m,'').trimStart())+filesSection;
    await writeFile(path,matter.stringify(content,{format:'md',slug:page.route.slice('/specs'.length),title:page.title,sidebar_label:page.title,
      displayed_sidebar:'moduleSpecsSidebar'}));
  }
  if(hasDocsProjections(registry.projectRoot)){
    const projectionsDirectory=resolve(generated,'content/specs/projections');
    await mkdir(projectionsDirectory,{recursive:true});
    const instructions=loadInstructionsProjection(registry.projectRoot);
    const wire=loadWireProjection(registry.projectRoot);
    await writeFile(resolve(projectionsDirectory,'instructions.md'),matter.stringify(renderInstructionsPage(instructions),
      {format:'md',slug:'/projections/instructions',title:'Agent instructions',sidebar_label:'Agent instructions',displayed_sidebar:'moduleSpecsSidebar'}));
    await writeFile(resolve(projectionsDirectory,'wire.md'),matter.stringify(renderWirePage(wire),
      {format:'md',slug:'/projections/wire',title:'Wire contracts',sidebar_label:'Wire contracts',displayed_sidebar:'moduleSpecsSidebar'}));
  }
  await writeFile(resolve(generated,'specs-sidebar.json'),JSON.stringify({moduleSpecsSidebar:publicationSidebar(registry)},null,2)+'\n');
  await writeFile(identity,JSON.stringify({schema_version:1,sourceDigest:registry.sourceDigest})+'\n');
}
