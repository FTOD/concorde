import {spawn} from 'node:child_process';
import {resolve} from 'node:path';

import {preparePublication} from './prepare-publication';

const siteDir = resolve(__dirname, '..');
const projectRoot = resolve(siteDir, '..');

async function main(): Promise<void> {
  await preparePublication(projectRoot);
  const cli = resolve(siteDir, 'node_modules/@docusaurus/core/bin/docusaurus.mjs');
  const code = await new Promise<number>((accept, reject) => {
    const child = spawn(process.execPath, [cli, 'start', ...process.argv.slice(2)], {
      cwd: siteDir,
      stdio: 'inherit',
      env: {...process.env, NODE_ENV: 'development'},
    });
    child.once('error', reject);
    child.once('exit', (status) => accept(status ?? 1));
  });
  if (code !== 0) throw new Error(`Docusaurus preview exited with status ${code}.`);
}

void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
