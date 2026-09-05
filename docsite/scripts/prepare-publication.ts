import {isScoped,loadScopedRegistry,type ScopedRegistry} from '../plugins/scoped-content/model';
import {materializeScoped} from '../plugins/scoped-content/materialize';
import {rm} from 'node:fs/promises';
import {resolve} from 'node:path';

import {buildRegistry} from '../plugins/concorde-content/registry';
import type {ContentRegistry, DiagramDeliverySet} from '../plugins/concorde-content/types';
import {assertValidRegistry} from '../plugins/concorde-content/validation';
import {materializeContent} from './materialize-content';
import {renderDeclaredDiagrams} from './render-diagrams';

export interface PreparedPublication {
  registry: ContentRegistry;
  diagrams: DiagramDeliverySet;
}

export async function preparePublication(projectRoot: string): Promise<PreparedPublication | {registry: ScopedRegistry}> {
  const root = resolve(projectRoot);
  if (isScoped(root)) {
    const registry=loadScopedRegistry(root);
    if (registry.targets.some(t=>t.diagrams.length)) await renderDeclaredDiagrams(root);
    await materializeScoped(registry);
    await rm(resolve(root,'docsite/.docusaurus'),{recursive:true,force:true});
    return {registry};
  }
  const diagrams = await renderDeclaredDiagrams(root);
  const registry = assertValidRegistry(await buildRegistry(root));
  await materializeContent(registry);
  // Route and staging projections can change while Docusaurus's compiled content cache remains.
  // Discard that ignored cache so preview and production consume only the just-materialized registry.
  await Promise.all([
    rm(resolve(__dirname, '../.docusaurus'), {recursive: true, force: true}),
    rm(resolve(__dirname, '../node_modules/.cache'), {recursive: true, force: true}),
  ]);
  return {registry, diagrams};
}
