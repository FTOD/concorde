import {spawn} from 'node:child_process';
import {rename, rm, stat} from 'node:fs/promises';
import {resolve} from 'node:path';

import {requireScoped} from '../plugins/scoped-content/model';
import {validateScopedBuild} from '../plugins/scoped-content';
import {preparePublication, productionGeneratedDirectory} from './prepare-publication';
import {PUBLICATION_MODE_VARIABLE} from '../plugins/scoped-content/staging';

const siteDir = resolve(__dirname, '..');
const projectRoot = resolve(siteDir, '..');

async function exists(path: string): Promise<boolean> {
  try { await stat(path); return true; } catch { return false; }
}

/**
 * Promotes the candidate by two renames, reversible until both succeed. Removing the backup comes
 * after the promotion and outside its rollback: a recursive removal that fails halfway has already
 * destroyed part of the backup, so the promoted site stays and the problem is reported instead.
 */
export async function promoteCandidate(candidate: string, destination: string, backup: string): Promise<void> {
  const hadDestination = await exists(destination);
  let destinationMoved = false;
  await rm(backup, {recursive: true, force: true});
  try {
    if (hadDestination) {
      await rename(destination, backup);
      destinationMoved = true;
    }
    await rename(candidate, destination);
  } catch (error) {
    if (destinationMoved && await exists(backup)) await rename(backup, destination);
    throw error;
  }
  if (!destinationMoved) return;
  try {
    await rm(backup, {recursive: true, force: true});
  } catch (error) {
    process.stderr.write(
      `Warning: the site was promoted to ${destination}, but removing the previous site's backup ${backup} failed; ` +
        `the next build removes it first. ${error instanceof Error ? error.message : String(error)}\n`,
    );
  }
}

async function runDocusaurus(candidate: string): Promise<void> {
  const cli = resolve(siteDir, 'node_modules/@docusaurus/core/bin/docusaurus.mjs');
  await new Promise<void>((accept, reject) => {
    const child = spawn(process.execPath, [cli, 'build', '--out-dir', candidate], {
      cwd: siteDir, stdio: 'inherit', env: {...process.env, NODE_ENV: 'production',
        DOCUSAURUS_GENERATED_FILES_DIR_NAME:productionGeneratedDirectory, [PUBLICATION_MODE_VARIABLE]: 'build'},
    });
    child.once('error', reject);
    child.once('exit', (code) => code === 0 ? accept() : reject(new Error(`Docusaurus exited with status ${code ?? 'unknown'}.`)));
  });
}

export async function buildSite(): Promise<void> {
  requireScoped(projectRoot);
  const candidate = resolve(siteDir, '.generated/candidate');
  const destination = resolve(siteDir, 'build');
  const backup = resolve(siteDir, '.generated/previous-build');
  await rm(candidate, {recursive: true, force: true});
  try {
    await preparePublication(projectRoot,{mode:'build'});
    await runDocusaurus(candidate);
    await validateScopedBuild(projectRoot,candidate);
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
