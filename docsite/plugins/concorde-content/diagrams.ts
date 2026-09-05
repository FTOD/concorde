import {isScoped,loadScopedRegistry} from '../scoped-content/model';
import {lstat, readFile, realpath} from 'node:fs/promises';
import {dirname, extname, posix, relative, resolve, sep} from 'node:path';

import fg from 'fast-glob';

import type {DiagramDeclaration, DiagramKind} from './types';

export const diagramKinds = new Set<DiagramKind>(['architecture', 'workflow', 'sequence', 'dataflow', 'lifecycle']);
/** Module-owned diagrams live directly beside architecture.md under `<module>/diagrams/`. */
export const moduleDiagramsDirectory = 'diagrams';
const posixPath = (value: string) => value.split(sep).join('/');

function relativeWithin(root: string, candidate: string): string | undefined {
  const result = relative(resolve(root), resolve(candidate));
  if (result === '..' || result.startsWith(`..${sep}`)) return undefined;
  return posixPath(result);
}

async function requireRegularSource(projectRoot: string, sourcePath: string): Promise<string> {
  const absolute = resolve(projectRoot, sourcePath);
  const contained = relativeWithin(projectRoot, absolute);
  if (contained === undefined) throw new Error(`${sourcePath}: diagram source escapes the project root.`);
  const [info, rootReal, sourceReal] = await Promise.all([lstat(absolute), realpath(projectRoot), realpath(absolute)]);
  if (!info.isFile() || info.isSymbolicLink()) throw new Error(`${sourcePath}: diagram source must be a regular non-symbolic file.`);
  if (relativeWithin(rootReal, sourceReal) === undefined) throw new Error(`${sourcePath}: resolved diagram source escapes the project root.`);
  return absolute;
}

/** Every JSON source directly beneath the owning module's diagrams directory, in stable name order. */
export async function listModuleDiagramSources(projectRoot: string, moduleSourcePath: string): Promise<string[]> {
  const directory = posix.join(posix.dirname(moduleSourcePath), moduleDiagramsDirectory);
  const absoluteDirectory = resolve(projectRoot, directory);
  try {
    if (!(await lstat(absoluteDirectory)).isDirectory()) return [];
  } catch {
    return [];
  }
  const names = await fg(['*.json'], {cwd: absoluteDirectory, onlyFiles: true, unique: true, followSymbolicLinks: false});
  return names.map((name) => posix.join(directory, posixPath(name))).sort();
}

export async function discoverDiagramDeclarations(projectRoot: string): Promise<DiagramDeclaration[]> {
  const root = resolve(projectRoot);
  const pending: Array<{ownerPath: string; sourcePath: string}> = [];
  if (isScoped(root)) {
    for (const target of loadScopedRegistry(root).targets)
      for (const diagram of target.diagrams) pending.push({ownerPath:target.documents[0],sourcePath:diagram.source});
  } else {
    const architectureFiles = await fg(['**/architecture.md'], {
      cwd: resolve(root, 'specs'), onlyFiles: true, unique: true, followSymbolicLinks: false,
      ignore: ['**/attempts/**'],
    });
    for (const relativeArchitecture of architectureFiles.sort()) {
      const ownerPath = posix.join('specs', posixPath(relativeArchitecture));
      for (const sourcePath of await listModuleDiagramSources(root, ownerPath)) pending.push({ownerPath, sourcePath});
    }
  }

  const declarations: DiagramDeclaration[] = [];
  const outputs = new Map<string, string>();
  for (const candidate of pending.sort((left, right) => left.sourcePath.localeCompare(right.sourcePath))) {
    const absoluteSourcePath = await requireRegularSource(root, candidate.sourcePath);
    let document: {
      diagram_type?: unknown;
      meta?: {title?: unknown; output?: unknown; quality_profile?: unknown; legend?: {mode?: unknown}};
    };
    try {
      document = JSON.parse(await readFile(absoluteSourcePath, 'utf8')) as typeof document;
    } catch (error) {
      throw new Error(`${candidate.sourcePath}: invalid diagram JSON: ${error instanceof Error ? error.message : String(error)}`);
    }
    if (typeof document.diagram_type !== 'string' || !diagramKinds.has(document.diagram_type as DiagramKind)) {
      throw new Error(`${candidate.sourcePath}: diagram_type must be one of ${[...diagramKinds].join(', ')}.`);
    }
    if (typeof document.meta?.title !== 'string' || !document.meta.title.trim()) {
      throw new Error(`${candidate.sourcePath}: meta.title is required.`);
    }
    if (document.meta.quality_profile !== 'showcase') {
      throw new Error(`${candidate.sourcePath}: meta.quality_profile must be showcase.`);
    }
    if (document.meta.legend?.mode !== 'hidden') {
      throw new Error(`${candidate.sourcePath}: meta.legend.mode must be hidden.`);
    }
    if (typeof document.meta.output !== 'string' || !document.meta.output.trim()) {
      throw new Error(`${candidate.sourcePath}: meta.output is required beneath generated/.`);
    }
    const absoluteOutputPath = resolve(dirname(absoluteSourcePath), document.meta.output);
    const outputFromGenerated = relativeWithin(resolve(root, 'generated'), absoluteOutputPath);
    if (outputFromGenerated === undefined || outputFromGenerated === '' || extname(absoluteOutputPath).toLowerCase() !== '.html') {
      throw new Error(`${candidate.sourcePath}: output must be a unique HTML file beneath generated/.`);
    }
    const outputPath = posixPath(relative(root, absoluteOutputPath));
    const previousSource = outputs.get(outputPath);
    if (previousSource) {
      throw new Error(`${candidate.sourcePath}: duplicate output "${outputPath}" also declared by ${previousSource}.`);
    }
    outputs.set(outputPath, candidate.sourcePath);
    declarations.push({
      ownerPath: candidate.ownerPath,
      sourcePath: candidate.sourcePath,
      absoluteSourcePath,
      outputPath,
      absoluteOutputPath,
      outputFromGenerated,
      kind: document.diagram_type as DiagramKind,
      title: document.meta.title.trim(),
    });
  }
  return declarations;
}
