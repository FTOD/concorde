import {copyFile,mkdir,rm,writeFile} from 'node:fs/promises';
import {dirname,resolve,posix} from 'node:path';
import matter from 'gray-matter';
import {primaryDocument,rewriteLinks,safeRead,type Page,type ScopedRegistry,type Target} from './model';
import {hasDocsProjections,loadInstructionsProjection,loadWireProjection,renderInstructionsPage,renderWirePage} from './projections';
const PROJECTIONS_GROUP={type:'category',label:'Projections',collapsed:false,items:[
  {type:'doc',id:'projections/instructions',label:'Agent instructions'},
  {type:'doc',id:'projections/wire',label:'Wire contracts'},
]};
interface DirNode {dirs: Map<string,DirNode>; files: Page[]}
function insert(root: DirNode, page: Page): void {
  const segments = page.stagedPath.split('/');
  let node = root;
  for (let i = 0; i < segments.length - 1; i++) {
    let child = node.dirs.get(segments[i]);
    if (!child) {child = {dirs: new Map(), files: []}; node.dirs.set(segments[i], child);}
    node = child;
  }
  node.files.push(page);
}
/** Directories first, then files, both alphabetically; a nested category per directory segment,
 * collapsed by default except the first level. Every registered document appears exactly once. */
function renderSourceTree(node: DirNode, depth: number): object[] {
  const directories = [...node.dirs.entries()].sort(([a],[b])=>a.localeCompare(b))
    .map(([name,child])=>({type:'category',label:name,collapsed:depth>0,items:renderSourceTree(child,depth+1)}));
  const files = [...node.files].sort((a,b)=>posix.basename(a.stagedPath).localeCompare(posix.basename(b.stagedPath)))
    .map(page=>({type:'doc',id:page.stagedPath.replace(/\.md$/,''),label:posix.basename(page.stagedPath)}));
  return [...directories, ...files];
}
export function scopedSidebar(registry: ScopedRegistry) {
  const byPath = new Map(registry.pages.map(p=>[p.sourcePath,p]));
  // Source navigation lists each document once; Module and Implementation navigation uses links.
  const item=(target:Target):object=>{
    const pages=target.documents.map(path=>byPath.get(path)!);
    const main=byPath.get(primaryDocument(target))!;
    return {type:'category',label:target.title,collapsed:true,items:[
      {type:'link',label:`${target.title} · Spec`,href:main.route},
      ...pages.filter(page=>page!==main).map(page=>({type:'link',label:page.title,href:page.route})),
      ...registry.targets.filter(t=>t.kind==='module'&&t.parent===target.id).map(item),
    ]};
  };
  const sourceTree: DirNode = {dirs: new Map(), files: []};
  for (const page of registry.pages) insert(sourceTree, page);
  return [
    {type:'category',label:'Specs by source path',collapsed:false,items:renderSourceTree(sourceTree,0)},
    {type:'category',label:'Specs by target',collapsed:true,items:[
      {type:'category',label:'Modules',collapsed:false,items:registry.targets.filter(t=>t.kind==='module'&&!t.parent).map(item)},
      {type:'category',label:'Implementation Specs',collapsed:false,items:registry.targets.filter(t=>t.kind==='implementation').map(item)},
    ].filter(group=>group.items.length)},
    ...(hasDocsProjections(registry.projectRoot)?[PROJECTIONS_GROUP]:[]),
  ];
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
    // Identity is displayed by ContentProvenance; keep machine-readable metadata out of the
    // reading flow while leaving the authored source and its digest intact.
    const content=rewriteLinks(registry,page).replace(/^```concorde-document\s*\n[\s\S]*?^```\s*$/m,'').trimStart();
    await writeFile(path,matter.stringify(content,{format:'md',slug:page.route.slice('/specs'.length),title:page.title,sidebar_label:posix.basename(page.stagedPath),
      ...(page.kind==='module'&&page.primaryOf?{hide_table_of_contents:true}:{})}));
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
