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
  await discoverDiagramDeclarations(root);
  const registry = await buildRegistry(root);
  const findings = validateRegistry(registry);
  const summary = {
    projectRoot: '.',
    counts: {
      architecture: registry.documents.filter((document) => document.collectionId === 'architecture').length,
      docs: registry.documents.filter((document) => document.collectionId === 'docs').length,
      tldrs: registry.documents.filter((document) => document.collectionId === 'feature-tldrs').length,
      specifications: registry.documents.filter((document) => document.collectionId === 'features').length,
      designs: registry.documents.filter((document) => document.collectionId === 'feature-designs').length,
      moduleDesigns: registry.documents.filter((document) => document.contentKind === 'module-design').length,
      excluded: registry.excludedSources.length,
      findings: findings.length,
    },
    mappings: registry.documents.map(({sourcePath, route}) => ({sourcePath, route})),
    exclusions: registry.excludedSources,
  };
  process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
  if (findings.length) {
    process.stderr.write(`${findings.map(formatFinding).join('\n')}\n`);
    process.exitCode = 1;
  }
}

void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
