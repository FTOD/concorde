import {isScoped,loadScopedRegistry,rewriteLinks} from '../plugins/scoped-content/model';
import {verifyConcordeBuildFresh} from '../plugins/scoped-content/build-freshness';
import {hasDocsProjections} from '../plugins/scoped-content/projections';
import {resolve} from 'node:path';

import {buildRegistry} from '../plugins/concorde-content/registry';
import {discoverDiagramDeclarations} from '../plugins/concorde-content/diagrams';
import {formatFinding, validateRegistry} from '../plugins/concorde-content/validation';

function projectRoot(): string {
  const index = process.argv.indexOf('--project-root');
  return resolve(index >= 0 && process.argv[index + 1] ? process.argv[index + 1] : resolve(__dirname, '../..'));
}

async function main() {
  const root = projectRoot();
  if (isScoped(root)) {
    // The Agent instructions/Wire contracts pages are rendered from generated/docs/*.json, itself
    // a Concorde build output; only check its freshness when this project actually produces it
    // (today, only this repository's own dogfood docsite — see plugins/scoped-content/projections.ts).
    if (hasDocsProjections(root)) verifyConcordeBuildFresh(root);
    const registry=loadScopedRegistry(root);registry.pages.forEach(p=>rewriteLinks(registry,p));
    await discoverDiagramDeclarations(root);
    process.stdout.write(`Validated Profile 8: ${registry.targets.length} targets, ${registry.pages.length} document memberships.\n`);
    return;
  }
  await discoverDiagramDeclarations(root);
  const registry = await buildRegistry(root);
  const findings = validateRegistry(registry);
  if (findings.length) {
    process.stderr.write(`${findings.map(formatFinding).join('\n')}\n`);
    process.exitCode = 1;
  } else {
    process.stdout.write(`Validated Profile 7: ${registry.documents.length} pages (${registry.excludedSources.length} excluded sources); 0 errors.\n`);
  }
}

void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
