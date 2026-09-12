import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {dirname,resolve} from 'node:path';
import type {LoadContext,Plugin} from '@docusaurus/types';
import {loadScopedRegistry,type Page,type ScopedRegistry} from './model';
import {canonicalRoute,normalizeRoute} from './routes';
import {loadSiteIdentity} from './site-identity';
import {validateInternalLinks} from './internal-links';
async function requireMaterialized(registry:ScopedRegistry):Promise<void> {
  const identity=JSON.parse(await readFile(resolve(registry.projectRoot,'docsite/.generated/scoped-materialization.json'),'utf8'));
  if(identity.schema_version!==1||identity.sourceDigest!==registry.sourceDigest)throw new Error('Materialized Spec source identity differs; prepare publication again');
}
function manifestPages(registry:ScopedRegistry) {
  return registry.pages.map(({sourcePath,route,contentDigest,owner,includedBy,aliases})=>
    ({sourcePath,route,contentDigest,owner,includedBy,aliases}));
}
function withBaseUrl(baseUrl:string,route:string):string {
  return (baseUrl==='/'?'':baseUrl.replace(/\/$/,''))+route;
}
/** A minimal static redirect for a legacy `/specs/<target-id>/<hash>`
 * route kept compatible after the source-path canonical route replaced it. */
function redirectStub(target:string,title:string):string {
  const escape=(value:string)=>value.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const scriptTarget=JSON.stringify(target).replace(/</g,'\\u003c');
  target=escape(target);title=escape(title);
  return '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"/>'+
    `<script>location.replace(${scriptTarget}+location.search+location.hash)</script>`+
    `<meta http-equiv="refresh" content="0; url=${target}"/><link rel="canonical" href="${target}"/>`+
    `<title>${title}</title></head><body><main><p>This page moved. `+
    `<a href="${target}">Continue to ${title}</a>.</p></main></body></html>\n`;
}
export async function validateScopedBuild(root:string,directory:string) {
  const registry=loadScopedRegistry(root);
  const manifest=JSON.parse(await readFile(resolve(directory,'build-manifest.json'),'utf8'));
  const expected=manifestPages(registry);
  if(manifest.schema_version!==19||manifest.sourceDigest!==registry.sourceDigest||JSON.stringify(manifest.pages)!==JSON.stringify(expected))throw new Error('Stale or incomplete Build Manifest 19');
  for (const page of registry.pages) for (const alias of page.aliases) {
    const stubPath=resolve(directory,alias.replace(/^\//,'')+'.html');
    let stub:string;
    try {stub=await readFile(stubPath,'utf8');}
    catch {throw new Error(`Missing legacy redirect stub for ${alias}`);}
    if(!stub.includes(page.route))throw new Error(`Legacy redirect stub does not reference its canonical route: ${alias}`);
  }
  await validateInternalLinks(directory,loadSiteIdentity(resolve(root,'docsite')),
    new Map(registry.pages.flatMap(page=>page.aliases.map(alias=>[alias,page.route] as [string,string]))),
    registry.pages.map(page=>page.route));
}
export default function scopedContent(context:LoadContext,options:unknown):Plugin<ScopedRegistry>{
  const root=resolve((options as {projectRoot?:string})?.projectRoot??resolve(context.siteDir,'..'));let loaded:ScopedRegistry;
  return {name:'concorde-content',
    async loadContent(){loaded=loadScopedRegistry(root);await requireMaterialized(loaded);return loaded;},
    async contentLoaded({content,actions}){actions.setGlobalData({schema_version:content.schema_version,entryTarget:content.entryTarget,
      pages:content.pages.map(({content:_,...page})=>page),
      siteIdentity:loadSiteIdentity(context.siteDir)});},
    getPathsToWatch(){return ['docsite/site.json','.concorde/config.json','generated/docs/instructions.json','generated/docs/wire.json',
      ...(loaded?[loaded.registryPath,...loaded.pages.map(p=>p.sourcePath)]:[])].map(p=>resolve(root,p));},
    async postBuild({outDir,routesPaths}){
      const current=loadScopedRegistry(root);if(current.sourceDigest!==loaded.sourceDigest)throw new Error('Spec source changed during publication');
      await requireMaterialized(loaded);
      const routes=new Set(routesPaths.map(p=>normalizeRoute(canonicalRoute(p,context.baseUrl))));
      if(loaded.pages.some(p=>!routes.has(normalizeRoute(p.route))))throw new Error('Registered Spec page was not rendered');
      await writeFile(resolve(outDir,'build-manifest.json'),JSON.stringify({schema_version:loaded.schema_version,sourceDigest:loaded.sourceDigest,
        pages:manifestPages(loaded)},null,2)+'\n');
      const target=(page:Page)=>withBaseUrl(context.baseUrl,page.route);
      for (const page of loaded.pages) for (const alias of page.aliases) {
        const stubPath=resolve(outDir,alias.replace(/^\//,'')+'.html');
        await mkdir(dirname(stubPath),{recursive:true});
        await writeFile(stubPath,redirectStub(target(page),page.title));
      }
    }};
}
