import {copyFile, mkdir, rm} from 'node:fs/promises';
import {dirname, relative, resolve} from 'node:path';

import {buildRegistry} from '../plugins/concorde-content/registry';
import {assertValidRegistry} from '../plugins/concorde-content/validation';

const siteDir = resolve(__dirname, '..');
const projectRoot = resolve(siteDir, '..');
export const generatedContentRoot = resolve(siteDir, '.generated/content');

export async function materializeContent(): Promise<void> {
  const registry = assertValidRegistry(await buildRegistry(projectRoot));
  await rm(generatedContentRoot, {recursive: true, force: true});

  for (const document of registry.documents) {
    if (!['architecture', 'features', 'feature-designs'].includes(document.collectionId)) continue;
    const relativeSpecPath = relative(resolve(projectRoot, 'specs'), resolve(projectRoot, document.sourcePath));
    const collectionDirectory = document.collectionId === 'feature-designs' ? 'features' : document.collectionId;
    const destination = resolve(generatedContentRoot, collectionDirectory, relativeSpecPath);
    await mkdir(dirname(destination), {recursive: true});
    await copyFile(resolve(projectRoot, document.sourcePath), destination);
  }
}

if (require.main === module) {
  void materializeContent().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
}
