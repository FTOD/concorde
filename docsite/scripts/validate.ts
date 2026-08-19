import {resolve} from 'node:path';

import {buildRegistry} from '../plugins/concorde-content/registry';
import {formatFinding, validateRegistry} from '../plugins/concorde-content/validation';

function projectRoot(): string {
  const index = process.argv.indexOf('--project-root');
  return resolve(index >= 0 && process.argv[index + 1] ? process.argv[index + 1] : resolve(__dirname, '../..'));
}

async function main() {
  const registry = await buildRegistry(projectRoot());
  const findings = validateRegistry(registry);
  if (findings.length) {
    process.stderr.write(`${findings.map(formatFinding).join('\n')}\n`);
    process.exitCode = 1;
  } else {
    process.stdout.write(`Validated ${registry.documents.length} pages (${registry.excludedSources.length} excluded sources); 0 errors.\n`);
  }
}

void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
