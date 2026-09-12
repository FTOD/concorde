import {resolve} from 'node:path';

import {loadScopedRegistry, requireScoped, rewriteLinks} from '../plugins/scoped-content/model';
import {verifyConcordeBuildFresh} from '../plugins/scoped-content/build-freshness';
import {hasDocsProjections} from '../plugins/scoped-content/projections';

function projectRoot(): string {
  const index = process.argv.indexOf('--project-root');
  return resolve(index >= 0 && process.argv[index + 1] ? process.argv[index + 1] : resolve(__dirname, '../..'));
}

async function main() {
  const root = projectRoot();
  requireScoped(root);
  // The Agent instructions/Wire contracts pages are rendered from generated/docs/*.json, itself
  // a Concorde build output; only check its freshness when this project actually produces it
  // (today, only this repository's own dogfood docsite — see plugins/scoped-content/projections.ts).
  if (hasDocsProjections(root)) verifyConcordeBuildFresh(root);
  const registry = loadScopedRegistry(root);
  registry.pages.forEach((page) => rewriteLinks(registry, page));
  process.stdout.write(`Validated Profile 12: ${registry.targets.length} targets, ${registry.pages.length} owned documents.\n`);
}

void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
