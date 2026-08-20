import {spawn} from 'node:child_process';
import {readFile, rename, rm, stat} from 'node:fs/promises';
import {resolve} from 'node:path';

import Ajv2020 from 'ajv/dist/2020';

import {buildRegistry} from '../plugins/concorde-content/registry';
import {assertValidRegistry} from '../plugins/concorde-content/validation';
import {materializeContent} from './materialize-content';

const siteDir = resolve(__dirname, '..');
const projectRoot = resolve(siteDir, '..');

async function exists(path: string): Promise<boolean> {
  try { await stat(path); return true; } catch { return false; }
}

export async function promoteCandidate(candidate: string, destination: string, backup: string): Promise<void> {
  const hadDestination = await exists(destination);
  await rm(backup, {recursive: true, force: true});
  try {
    if (hadDestination) await rename(destination, backup);
    await rename(candidate, destination);
    await rm(backup, {recursive: true, force: true});
  } catch (error) {
    await rm(destination, {recursive: true, force: true});
    if (hadDestination && await exists(backup)) await rename(backup, destination);
    throw error;
  }
}

async function runDocusaurus(candidate: string): Promise<void> {
  const cli = resolve(siteDir, 'node_modules/@docusaurus/core/bin/docusaurus.mjs');
  await new Promise<void>((accept, reject) => {
    const child = spawn(process.execPath, [cli, 'build', '--out-dir', candidate], {
      cwd: siteDir, stdio: 'inherit', env: {...process.env, NODE_ENV: 'production'},
    });
    child.once('error', reject);
    child.once('exit', (code) => code === 0 ? accept() : reject(new Error(`Docusaurus exited with status ${code ?? 'unknown'}.`)));
  });
}

async function validateGeneratedManifest(candidate: string): Promise<void> {
  const [schemaText, manifestText] = await Promise.all([
    readFile(resolve(projectRoot, 'specs/concorde/features/002-create-project-docsite/contracts/build-manifest.schema.json'), 'utf8'),
    readFile(resolve(candidate, 'build-manifest.json'), 'utf8'),
  ]);
  const validate = new Ajv2020({allErrors: true}).compile(JSON.parse(schemaText));
  if (!validate(JSON.parse(manifestText))) throw new Error(`Generated manifest violates its schema: ${JSON.stringify(validate.errors)}`);
}

export async function buildSite(): Promise<void> {
  const candidate = resolve(siteDir, '.generated/candidate');
  const destination = resolve(siteDir, 'build');
  const backup = resolve(siteDir, '.generated/previous-build');
  await rm(candidate, {recursive: true, force: true});
  assertValidRegistry(await buildRegistry(projectRoot));
  await materializeContent();
  try {
    await runDocusaurus(candidate);
    await validateGeneratedManifest(candidate);
    await promoteCandidate(candidate, destination, backup);
    process.stdout.write(`Verified site promoted to ${destination}\n`);
  } catch (error) {
    await rm(candidate, {recursive: true, force: true});
    throw error;
  }
}

if (require.main === module) {
  void buildSite().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
}
