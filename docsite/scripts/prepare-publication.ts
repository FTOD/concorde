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

export async function preparePublication(projectRoot: string): Promise<PreparedPublication> {
  const root = resolve(projectRoot);
  const diagrams = await renderDeclaredDiagrams(root);
  const registry = assertValidRegistry(await buildRegistry(root));
  await materializeContent(registry);
  return {registry, diagrams};
}
