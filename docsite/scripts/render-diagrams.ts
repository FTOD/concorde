import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdir, mkdtemp, readFile, realpath, rename, rm, stat} from 'node:fs/promises';
import {dirname, relative, resolve, sep} from 'node:path';

import {discoverDiagramDeclarations} from '../plugins/concorde-content/diagrams';
import type {DiagramDeclaration, DiagramDeliveryReceipt, DiagramDeliverySet} from '../plugins/concorde-content/types';

const expectedArchify = {
  name: 'archify',
  version: '2.14.0',
  bin: './bin/archify.mjs',
} as const;

interface ArchifyPackage {
  root: string;
  bin: string;
  version: '2.14.0';
}

interface CommandResult {
  status: number | null;
  stdout: string;
  stderr: string;
  error?: Error;
}

type CommandRunner = (bin: string, args: string[]) => CommandResult;

const defaultRunner: CommandRunner = (bin, args) => {
  const result = spawnSync(process.execPath, [bin, ...args], {
    encoding: 'utf8',
    maxBuffer: 16 * 1024 * 1024,
  });
  return {
    status: result.status,
    stdout: result.stdout ?? '',
    stderr: result.stderr ?? '',
    error: result.error,
  };
};

async function exists(path: string): Promise<boolean> {
  try {
    await stat(path);
    return true;
  } catch {
    return false;
  }
}

function isWithin(root: string, candidate: string): boolean {
  const fromRoot = relative(resolve(root), resolve(candidate));
  return fromRoot === '' || (fromRoot !== '..' && !fromRoot.startsWith(`..${sep}`));
}

export async function resolveArchifyPackage(configuredRoot: string | undefined): Promise<ArchifyPackage> {
  if (!configuredRoot?.trim()) {
    throw new Error('ARCHIFY_ROOT is required and must point to the Archify 2.14.0 package directory.');
  }
  const root = await realpath(resolve(configuredRoot));
  const packagePath = resolve(root, 'package.json');
  let document: {name?: unknown; version?: unknown; bin?: {archify?: unknown}};
  try {
    document = JSON.parse(await readFile(packagePath, 'utf8')) as typeof document;
  } catch (error) {
    throw new Error(`ARCHIFY_ROOT package.json is unreadable: ${error instanceof Error ? error.message : String(error)}`);
  }
  if (document.name !== expectedArchify.name || document.version !== expectedArchify.version ||
      document.bin?.archify !== expectedArchify.bin) {
    throw new Error(
      `ARCHIFY_ROOT must provide archify ${expectedArchify.version} with bin.archify ${expectedArchify.bin}.`,
    );
  }
  const bin = await realpath(resolve(root, expectedArchify.bin));
  if (!isWithin(root, bin) || !(await stat(bin)).isFile()) {
    throw new Error('ARCHIFY_ROOT bin.archify must resolve to a regular file inside the package root.');
  }
  return {root, bin, version: expectedArchify.version};
}

function runChecked(runner: CommandRunner, bin: string, args: string[], subject: string): string {
  const result = runner(bin, args);
  if (result.error || result.status !== 0) {
    const detail = [result.stderr.trim(), result.stdout.trim(), result.error?.message].filter(Boolean).join('\n');
    throw new Error(`${subject} failed${result.status === null ? '' : ` with exit ${result.status}`}: ${detail || 'no diagnostic output'}`);
  }
  return result.stdout.trim();
}

function parseJsonReceipt(raw: string, subject: string): Record<string, unknown> {
  try {
    const receipt = JSON.parse(raw) as unknown;
    if (!receipt || typeof receipt !== 'object' || Array.isArray(receipt)) throw new Error('receipt is not an object');
    return receipt as Record<string, unknown>;
  } catch (error) {
    throw new Error(`${subject} returned malformed JSON: ${error instanceof Error ? error.message : String(error)}`);
  }
}

function validateShowcaseReceipt(receipt: Record<string, unknown>, declaration: DiagramDeclaration): void {
  const checks = receipt.checks;
  const composition = receipt.composition as Record<string, unknown> | undefined;
  const summary = composition?.summary as Record<string, unknown> | undefined;
  if (receipt.schemaVersion !== 1 || receipt.ok !== true || receipt.command !== 'validate' ||
      receipt.type !== declaration.kind || !Array.isArray(checks) || checks.length !== 9 ||
      !checks.every((check) => check && typeof check === 'object' && (check as Record<string, unknown>).ok === true) ||
      composition?.profile !== 'showcase' || composition.status !== 'pass' ||
      summary?.errors !== 0 || summary.warnings !== 0) {
    throw new Error(`${declaration.sourcePath}: Archify validate receipt did not prove a 9/9 showcase pass with zero errors and warnings.`);
  }
}

async function normalizedDeliveryReceipt(
  receipt: Record<string, unknown>,
  declaration: DiagramDeclaration,
  candidateOutput: string,
): Promise<DiagramDeliveryReceipt> {
  const specification = receipt.specification as Record<string, unknown> | undefined;
  const artifact = receipt.artifact as Record<string, unknown> | undefined;
  const validation = receipt.validation as Record<string, unknown> | undefined;
  const source = await readFile(declaration.absoluteSourcePath);
  const delivered = await readFile(candidateOutput);
  const sourceSha256 = createHash('sha256').update(source).digest('hex');
  const artifactSha256 = createHash('sha256').update(delivered).digest('hex');
  if (receipt.schemaVersion !== 1 || receipt.ok !== true || receipt.command !== 'deliver' ||
      receipt.type !== declaration.kind || specification?.sha256 !== sourceSha256 ||
      specification.bytes !== source.byteLength || artifact?.sha256 !== artifactSha256 ||
      artifact.bytes !== delivered.byteLength || validation?.checksPassed !== 9 ||
      validation.checkCount !== 9 || validation.compositionProfile !== 'showcase' ||
      validation.compositionStatus !== 'pass' || validation.errors !== 0 || validation.warnings !== 0) {
    throw new Error(`${declaration.sourcePath}: Archify delivery receipt disagrees with the maintained source or delivered artifact.`);
  }
  return {
    sourcePath: declaration.sourcePath,
    outputPath: declaration.outputPath,
    kind: declaration.kind,
    sourceSha256,
    sourceBytes: source.byteLength,
    artifactSha256,
    artifactBytes: delivered.byteLength,
    checksPassed: 9,
    checkCount: 9,
    profile: 'showcase',
    compositionStatus: 'pass',
    errors: 0,
    warnings: 0,
  };
}

export async function atomicReplaceDirectory(candidate: string, destination: string, backup: string): Promise<void> {
  const hadDestination = await exists(destination);
  let destinationMoved = false;
  let candidateMoved = false;
  await rm(backup, {recursive: true, force: true});
  try {
    if (hadDestination) {
      await rename(destination, backup);
      destinationMoved = true;
    }
    await rename(candidate, destination);
    candidateMoved = true;
    if (destinationMoved) await rm(backup, {recursive: true, force: true});
  } catch (error) {
    if (candidateMoved) await rm(destination, {recursive: true, force: true});
    if (destinationMoved && await exists(backup)) await rename(backup, destination);
    throw error;
  }
}

export async function renderDeclaredDiagrams(
  projectRoot: string,
  options: {archifyRoot?: string; runner?: CommandRunner} = {},
): Promise<DiagramDeliverySet> {
  const root = resolve(projectRoot);
  const runner = options.runner ?? defaultRunner;
  const archify = await resolveArchifyPackage(options.archifyRoot ?? process.env.ARCHIFY_ROOT);
  runChecked(runner, archify.bin, ['doctor'], 'Archify doctor');
  const declarations = await discoverDiagramDeclarations(root);
  const generatedRoot = resolve(root, 'generated');
  const candidateRoot = await mkdtemp(resolve(root, '.generated-diagrams-'));
  const backupRoot = resolve(root, '.generated-diagrams-previous');
  const receipts: DiagramDeliveryReceipt[] = [];
  try {
    for (const declaration of declarations) {
      const common = [declaration.kind, declaration.absoluteSourcePath, '--quality', 'showcase', '--json'];
      if (declaration.kind === 'architecture') common.push('--repo-root', root);
      const validation = parseJsonReceipt(
        runChecked(runner, archify.bin, ['validate', ...common], `${declaration.sourcePath}: Archify validate`),
        `${declaration.sourcePath}: Archify validate`,
      );
      validateShowcaseReceipt(validation, declaration);
      const candidateOutput = resolve(candidateRoot, declaration.outputFromGenerated);
      if (!isWithin(candidateRoot, candidateOutput)) throw new Error(`${declaration.sourcePath}: candidate output escapes the delivery set.`);
      await mkdir(dirname(candidateOutput), {recursive: true});
      const deliveryArgs = [
        'deliver', declaration.kind, declaration.absoluteSourcePath, candidateOutput,
        '--quality', 'showcase', '--json',
      ];
      if (declaration.kind === 'architecture') deliveryArgs.push('--repo-root', root);
      const delivery = parseJsonReceipt(
        runChecked(runner, archify.bin, deliveryArgs, `${declaration.sourcePath}: Archify deliver`),
        `${declaration.sourcePath}: Archify deliver`,
      );
      receipts.push(await normalizedDeliveryReceipt(delivery, declaration, candidateOutput));
    }
    await atomicReplaceDirectory(candidateRoot, generatedRoot, backupRoot);
  } catch (error) {
    await rm(candidateRoot, {recursive: true, force: true});
    throw error;
  }
  return {generator: {name: 'archify', version: archify.version}, receipts};
}

async function main(): Promise<void> {
  const siteDir = resolve(__dirname, '..');
  const projectRoot = resolve(siteDir, '..');
  const result = await renderDeclaredDiagrams(projectRoot);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

if (require.main === module) {
  void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
}
