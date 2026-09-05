import {writeFile,readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import type {LoadContext,Plugin} from '@docusaurus/types';
import {loadScopedRegistry,type ScopedRegistry} from './model';
import {canonicalRoute,normalizeRoute} from '../concorde-content/routes';
export async function validateScopedBuild(root:string,directory:string) {
  const registry=loadScopedRegistry(root);
  const manifest=JSON.parse(await readFile(resolve(directory,'build-manifest.json'),'utf8'));
  const graph=JSON.parse(await readFile(resolve(directory,'architecture-graph.json'),'utf8'));
  const expected=registry.pages.map(({sourcePath,route,contentDigest})=>({sourcePath,route,contentDigest}));
  if(manifest.schema_version!==14||manifest.sourceDigest!==registry.sourceDigest||JSON.stringify(manifest.pages)!==JSON.stringify(expected))throw new Error('Stale or incomplete Build Manifest 14');
  if(graph.schema_version!==1||graph.sourceDigest!==registry.sourceDigest||JSON.stringify(graph.edges)!==JSON.stringify(registry.edges)||JSON.stringify(graph.nodes)!==JSON.stringify(registry.targets))throw new Error('Stale architecture graph');
}
export default function scopedContent(context:LoadContext,options:unknown):Plugin<ScopedRegistry>{
  const root=resolve((options as {projectRoot?:string})?.projectRoot??resolve(context.siteDir,'..'));let loaded:ScopedRegistry;
  return {name:'concorde-content',
    async loadContent(){loaded=loadScopedRegistry(root);return loaded;},
    async contentLoaded({content,actions}){actions.setGlobalData({schema_version:14,entryTarget:content.entryTarget,
      pages:content.pages.map(({content:_,...page})=>page),architectureGraph:{nodes:content.targets,edges:content.edges}});},
    getPathsToWatch(){return ['.concorde/config.json',...(loaded?[loaded.registryPath,...loaded.pages.map(p=>p.sourcePath),...loaded.targets.flatMap(t=>t.diagrams.map(d=>d.source))]:[])].map(p=>resolve(root,p));},
    async postBuild({outDir,routesPaths}){
      const current=loadScopedRegistry(root);if(current.sourceDigest!==loaded.sourceDigest)throw new Error('Spec source changed during publication');
      const routes=new Set(routesPaths.map(p=>normalizeRoute(canonicalRoute(p,context.baseUrl))));
      if(loaded.pages.some(p=>!routes.has(normalizeRoute(p.route))))throw new Error('Registered Spec page was not rendered');
      await writeFile(resolve(outDir,'build-manifest.json'),JSON.stringify({schema_version:14,sourceDigest:loaded.sourceDigest,
        pages:loaded.pages.map(({sourcePath,route,contentDigest})=>({sourcePath,route,contentDigest}))},null,2)+'\n');
      await writeFile(resolve(outDir,'architecture-graph.json'),JSON.stringify({schema_version:1,sourceDigest:loaded.sourceDigest,nodes:loaded.targets,edges:loaded.edges},null,2)+'\n');
    }};
}
