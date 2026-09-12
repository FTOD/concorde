import {resolve} from 'node:path';

import {loadScopedRegistry, requireScoped, rewriteLinks} from '../plugins/scoped-content/model';

function projectRoot(): string {
  const index = process.argv.indexOf('--project-root');
  return resolve(index >= 0 && process.argv[index + 1] ? process.argv[index + 1] : resolve(__dirname, '../..'));
}

async function main() {
  const root = projectRoot();
  requireScoped(root);
  const registry = loadScopedRegistry(root);
  registry.pages.forEach((page) => rewriteLinks(registry, page));
  process.stdout.write(`Validated Profile 12: ${registry.targets.length} targets, ${registry.pages.length} owned documents.\n`);
}

void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
