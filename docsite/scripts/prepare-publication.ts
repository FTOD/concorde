import {rm} from 'node:fs/promises';
import {resolve} from 'node:path';

import {loadScopedRegistry, requireScoped, type ScopedRegistry} from '../plugins/scoped-content/model';
import {materializeScoped} from '../plugins/scoped-content/materialize';

export const productionGeneratedDirectory = '.generated/docusaurus-production';

/**
 * Stage the registered Markdown and navigation this build publishes. Registry schema 4 declares no
 * external diagram sources: every Architecture section is an inline Mermaid fence, so publication
 * renders the registered documents. Checkout-only extensions register their own independent routes.
 */
export async function preparePublication(
  projectRoot: string,
  options: {mode?: 'preview' | 'build'} = {},
): Promise<{registry: ScopedRegistry}> {
  const root = resolve(projectRoot);
  requireScoped(root);
  const generatedDirectory = options.mode === 'build' ? productionGeneratedDirectory : '.docusaurus';
  const registry = loadScopedRegistry(root);
  await materializeScoped(registry);
  // Route and staging projections can change while Docusaurus's compiled content cache remains.
  // Discard that ignored cache so preview and production consume only the just-materialized registry.
  await rm(resolve(root, 'docsite', generatedDirectory), {recursive: true, force: true});
  return {registry};
}
