import {lstat, readFile, realpath} from 'node:fs/promises';
import {dirname, extname, posix, relative, resolve, sep} from 'node:path';

import fg from 'fast-glob';
import matter from 'gray-matter';

import type {DiagramDeclaration, DiagramKind, FeatureDiagram} from './types';

export const diagramKinds = new Set<DiagramKind>(['architecture', 'workflow', 'sequence', 'dataflow', 'lifecycle']);
/** Module-owned diagrams live directly beneath `<module>/architecture/diagrams/`. */
export const moduleDiagramsDirectory = 'architecture/diagrams';
const posixPath = (value: string) => value.split(sep).join('/');

function relativeWithin(root: string, candidate: string): string | undefined {
  const result = relative(resolve(root), resolve(candidate));
  if (result === '..' || result.startsWith(`..${sep}`) || result === '') return result === '' ? '' : undefined;
  return posixPath(result);
}

function requireProjectPath(projectRoot: string, value: unknown, subject: string): {relative: string; absolute: string} {
  if (typeof value !== 'string' || !value.trim()) throw new Error(`${subject}: path is required.`);
  const normalized = posix.normalize(value.replaceAll('\\', '/'));
  if (normalized.startsWith('/') || normalized === '..' || normalized.startsWith('../')) {
    throw new Error(`${subject}: path must remain project-relative.`);
  }
  const absolute = resolve(projectRoot, normalized);
  const contained = relativeWithin(projectRoot, absolute);
  if (contained === undefined) throw new Error(`${subject}: path escapes the project root.`);
  return {relative: contained, absolute};
}

async function requireRegularSource(projectRoot: string, sourcePath: string, ownerPath: string): Promise<string> {
  const {absolute} = requireProjectPath(projectRoot, sourcePath, ownerPath);
  const [sourceInfo, projectReal, sourceReal] = await Promise.all([lstat(absolute), realpath(projectRoot), realpath(absolute)]);
  if (!sourceInfo.isFile() || sourceInfo.isSymbolicLink()) throw new Error(`${sourcePath}: diagram source must be a regular non-symbolic file.`);
  if (relativeWithin(projectReal, sourceReal) === undefined) throw new Error(`${sourcePath}: resolved diagram source escapes the project root.`);
  return absolute;
}

interface PendingDeclaration {
  ownerPath: string;
  sourcePath: string;
  /** Declared by the owner (feature diagrams); a module diagram takes its kind from its own `diagram_type`. */
  declaredKind?: DiagramKind;
  declaredOutput?: string;
  role?: FeatureDiagram['role'];
  scenarios?: string[];
}

function featureDeclarations(ownerPath: string, raw: unknown): PendingDeclaration[] {
  if (raw === undefined) return [];
  if (!Array.isArray(raw)) throw new Error(`${ownerPath}: diagrams must be a list.`);
  const expectedDirectory = posix.join(posix.dirname(ownerPath), 'diagrams');
  return raw.map((item, index) => {
    if (!item || typeof item !== 'object' || Array.isArray(item)) {
      throw new Error(`${ownerPath}: diagram declaration ${index + 1} must be a mapping.`);
    }
    const declaration = item as Record<string, unknown>;
    const sourcePath = typeof declaration.source === 'string'
      ? posix.normalize(declaration.source.replaceAll('\\', '/')) : '';
    const kind = declaration.kind;
    const role = declaration.role;
    const scenarios = declaration.scenarios;
    if (!sourcePath || posix.dirname(sourcePath) !== expectedDirectory || posix.basename(sourcePath) === 'architecture.json') {
      throw new Error(`${ownerPath}: feature diagram "${sourcePath || '<missing>'}" must be directly under ${expectedDirectory}/.`);
    }
    if (typeof kind !== 'string' || !diagramKinds.has(kind as DiagramKind)) {
      throw new Error(`${ownerPath}: feature diagram "${sourcePath}" has an unsupported kind.`);
    }
    if (role !== 'core' && role !== 'supplemental') {
      throw new Error(`${ownerPath}: feature diagram "${sourcePath}" must declare core or supplemental role.`);
    }
    if (role === 'core' && kind !== 'architecture') {
      throw new Error(`${ownerPath}: core feature diagram "${sourcePath}" must use architecture.`);
    }
    if (!Array.isArray(scenarios) || !scenarios.length || !scenarios.every((value) => typeof value === 'string' && value.length > 0)) {
      throw new Error(`${ownerPath}: feature diagram "${sourcePath}" requires scenarios or a named question.`);
    }
    return {
      ownerPath,
      sourcePath,
      declaredKind: kind as DiagramKind,
      declaredOutput: typeof declaration.output === 'string' ? declaration.output : undefined,
      role,
      scenarios: [...scenarios] as string[],
    };
  });
}

/** Every `*.json` directly beneath the module's `architecture/diagrams/` directory, in stable name order. */
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
  const specsRoot = resolve(root, 'specs');
  const ownerFiles = await fg(['**/module.md', '**/design.md'], {
    cwd: specsRoot,
    onlyFiles: true,
    unique: true,
    followSymbolicLinks: false,
  });
  const pending: PendingDeclaration[] = [];
  for (const ownerFromSpecs of ownerFiles.sort()) {
    const ownerPath = posix.join('specs', ownerFromSpecs.replaceAll('\\', '/'));
    if (ownerFromSpecs.endsWith('module.md')) {
      for (const sourcePath of await listModuleDiagramSources(root, ownerPath)) pending.push({ownerPath, sourcePath});
      continue;
    }
    if (ownerFiles.includes(ownerFromSpecs.replace(/design\.md$/, 'module.md'))) continue; // module design reference
    const parsed = matter(await readFile(resolve(specsRoot, ownerFromSpecs), 'utf8'));
    pending.push(...featureDeclarations(ownerPath, parsed.data.diagrams));
  }

  const declarations: DiagramDeclaration[] = [];
  const sources = new Map<string, string>();
  const outputs = new Map<string, string>();
  for (const candidate of pending.sort((left, right) => left.sourcePath.localeCompare(right.sourcePath))) {
    const absoluteSourcePath = await requireRegularSource(root, candidate.sourcePath, candidate.ownerPath);
    const sourcePath = posixPath(relative(root, absoluteSourcePath));
    const previousOwner = sources.get(sourcePath);
    if (previousOwner) {
      throw new Error(`${sourcePath}: duplicate diagram source declared by ${previousOwner} and ${candidate.ownerPath}.`);
    }
    sources.set(sourcePath, candidate.ownerPath);
    let document: {
      diagram_type?: unknown;
      meta?: {title?: unknown; output?: unknown; quality_profile?: unknown; legend?: {mode?: unknown}};
    };
    try {
      document = JSON.parse(await readFile(absoluteSourcePath, 'utf8')) as typeof document;
    } catch (error) {
      throw new Error(`${sourcePath}: invalid diagram JSON: ${error instanceof Error ? error.message : String(error)}`);
    }
    const kind = candidate.declaredKind ?? document.diagram_type;
    if (typeof kind !== 'string' || !diagramKinds.has(kind as DiagramKind)) {
      throw new Error(`${sourcePath}: diagram_type must be one of ${[...diagramKinds].join(', ')}.`);
    }
    if (document.diagram_type !== kind) {
      throw new Error(`${sourcePath}: diagram_type must match declared ${kind} kind.`);
    }
    if (typeof document.meta?.title !== 'string' || !document.meta.title.trim()) {
      throw new Error(`${sourcePath}: meta.title is required.`);
    }
    if (document.meta.quality_profile !== 'showcase') {
      throw new Error(`${sourcePath}: meta.quality_profile must be showcase.`);
    }
    if (document.meta.legend?.mode !== 'hidden') {
      throw new Error(`${sourcePath}: meta.legend.mode must be hidden.`);
    }
    if (typeof document.meta.output !== 'string' || !document.meta.output.trim()) {
      throw new Error(`${sourcePath}: meta.output is required beneath generated/.`);
    }
    const absoluteOutputPath = resolve(dirname(absoluteSourcePath), document.meta.output);
    const outputFromGenerated = relativeWithin(resolve(root, 'generated'), absoluteOutputPath);
    if (outputFromGenerated === undefined || outputFromGenerated === '' || extname(absoluteOutputPath).toLowerCase() !== '.html') {
      throw new Error(`${sourcePath}: output must be a unique HTML file beneath generated/.`);
    }
    const outputPath = posixPath(relative(root, absoluteOutputPath));
    if (candidate.declaredOutput) {
      const declared = requireProjectPath(root, candidate.declaredOutput, candidate.ownerPath);
      if (resolve(declared.absolute) !== resolve(absoluteOutputPath)) {
        throw new Error(`${sourcePath}: meta.output does not match ${candidate.ownerPath} output declaration.`);
      }
    }
    const previousSource = outputs.get(outputPath);
    if (previousSource) {
      throw new Error(`${sourcePath}: duplicate output "${outputPath}" also declared by ${previousSource}.`);
    }
    outputs.set(outputPath, sourcePath);
    declarations.push({
      ownerPath: candidate.ownerPath,
      sourcePath,
      absoluteSourcePath,
      outputPath,
      absoluteOutputPath,
      outputFromGenerated,
      kind: kind as DiagramKind,
      title: document.meta.title.trim(),
      role: candidate.role,
      scenarios: candidate.scenarios,
    });
  }
  return declarations.sort((left, right) => left.sourcePath.localeCompare(right.sourcePath));
}
