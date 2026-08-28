import {createHash} from 'node:crypto';
import {realpath, readFile} from 'node:fs/promises';
import {dirname, posix, relative, resolve} from 'node:path';

import fg from 'fast-glob';
import matter from 'gray-matter';

import type {
  ArchitectureKind, ArchitectureSource, ContentRegistry, ExcludedSource, FeatureDiagram, FeatureImplementation, FeatureSpecification,
  ModuleDesign, ProjectDocument, SourceCollection, SourceDocument, ValidationFinding,
} from './types';
import {populateLinks} from './links';

export const collections: SourceCollection[] = [
  {
    // `**/design.md` is admitted only beside a `module.md` (a module design reference, kind `module-design`);
    // buildRegistry reports any other design.md instead of publishing it.
    id: 'architecture', sourceBase: 'specs', routeBase: '/architecture',
    include: ['**/module.md', '**/design.md', '**/contracts/**/contract.md'], contentKind: 'architecture-source',
  },
  {id: 'docs', sourceBase: 'docs', routeBase: '/docs', include: ['**/*.md'], contentKind: 'project-document'},
  {id: 'features', sourceBase: 'specs', routeBase: '/features', include: ['**/spec.md'], contentKind: 'feature-specification'},
  {
    id: 'feature-implementations', sourceBase: 'specs', routeBase: '/features',
    include: ['**/implementation.md'], contentKind: 'feature-implementation',
  },
];

/** Temporal implementation attempts (`<feature root>/implementation/**`) are never publishable sources. */
const temporalWorkspaceIgnore = ['**/implementation/**'];

const posixPath = (value: string) => value.split('\\').join('/');
const sha256 = (value: string) => createHash('sha256').update(value).digest('hex');
const diagramKinds = new Set(['architecture', 'workflow', 'sequence', 'dataflow', 'lifecycle']);

function headingTitle(content: string): string {
  return content.match(/^#\s+(.+?)\s*$/m)?.[1]?.replace(/^Feature Specification:\s*/i, '').trim() ?? '';
}

function sectionText(content: string, heading: string): string {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return content.match(new RegExp(`^##\\s+${escaped}\\s*$\\n([\\s\\S]*?)(?=^##\\s+|$)`, 'm'))?.[1]
    ?.replace(/\s+/g, ' ').trim() ?? '';
}

function routeFor(collection: SourceCollection, relativePath: string, slug?: unknown, sourceId?: unknown): string {
  if (typeof slug === 'string' && slug.trim()) {
    const clean = slug.trim().replace(/^\/+|\/+$/g, '');
    return clean ? `${collection.routeBase}/${clean}` : collection.routeBase;
  }
  if (collection.id !== 'docs' && typeof sourceId === 'string' && sourceId.trim()) {
    const directory = posix.dirname(relativePath);
    return `${collection.routeBase}/${directory === '.' ? '' : `${directory}/`}${sourceId.trim()}`;
  }
  const withoutExtension = relativePath.replace(/\.md$/i, '').replace(/(^|\/)index$/i, '$1');
  const clean = withoutExtension.replace(/^\/+|\/+$/g, '');
  return clean ? `${collection.routeBase}/${clean}` : collection.routeBase;
}

async function parseFeatureDiagrams(
  projectRoot: string,
  featureSourcePath: string,
  rawDeclarations: unknown,
): Promise<FeatureDiagram[]> {
  if (rawDeclarations === undefined) return [];
  if (!Array.isArray(rawDeclarations)) throw new Error('Feature diagrams must be declared as a list.');
  const featureDirectory = posix.dirname(featureSourcePath);
  const diagramDirectory = posix.join(featureDirectory, 'diagrams');
  const diagrams: FeatureDiagram[] = [];
  for (const rawDeclaration of rawDeclarations) {
    if (!rawDeclaration || typeof rawDeclaration !== 'object' || Array.isArray(rawDeclaration)) {
      throw new Error('Each feature diagram declaration must be a mapping.');
    }
    const declaration = rawDeclaration as Record<string, unknown>;
    const source = typeof declaration.source === 'string' ? posix.normalize(posixPath(declaration.source)) : '';
    if (!source || posix.dirname(source) !== diagramDirectory || posix.basename(source) === 'architecture.json') {
      throw new Error(`Feature diagram "${source || '<missing>'}" must be directly under ${diagramDirectory}/ with a descriptive filename.`);
    }
    const absoluteSource = resolve(projectRoot, source);
    const sourceFromRoot = posixPath(relative(resolve(projectRoot), absoluteSource));
    if (sourceFromRoot === '..' || sourceFromRoot.startsWith('../')) {
      throw new Error(`Feature diagram "${source}" escapes the project root.`);
    }
    const sourceText = await readFile(absoluteSource, 'utf8');
    const diagram = JSON.parse(sourceText) as {diagram_type?: unknown; meta?: {title?: unknown; output?: unknown}};
    const role = declaration.role;
    const kind = declaration.kind;
    const scenarios = declaration.scenarios;
    if (typeof kind !== 'string' || !diagramKinds.has(kind) || diagram.diagram_type !== kind) {
      throw new Error(`Feature diagram "${source}" has a missing or inconsistent diagram kind.`);
    }
    if (role !== 'core' && role !== 'supplemental') {
      throw new Error(`Feature diagram "${source}" must declare role as core or supplemental.`);
    }
    if (role === 'core' && kind !== 'architecture') {
      throw new Error(`Core feature diagram "${source}" must use the architecture kind; dynamic views are supplemental.`);
    }
    if (!Array.isArray(scenarios) || scenarios.length === 0 || !scenarios.every((value) => typeof value === 'string' && value.length > 0)) {
      throw new Error(`Feature diagram "${source}" must declare at least one scenario or named question.`);
    }
    if (typeof diagram.meta?.title !== 'string' || !diagram.meta.title.trim() || typeof diagram.meta.output !== 'string') {
      throw new Error(`Feature diagram "${source}" requires meta.title and meta.output.`);
    }
    const outputPath = resolve(dirname(absoluteSource), diagram.meta.output);
    const generatedRelative = posixPath(relative(resolve(projectRoot, 'generated'), outputPath));
    if (generatedRelative === '..' || generatedRelative.startsWith('../')) {
      throw new Error(`Feature diagram "${source}" output must be beneath generated/.`);
    }
    const declaredOutput = typeof declaration.output === 'string' ? resolve(projectRoot, declaration.output) : '';
    if (!declaredOutput || declaredOutput !== outputPath) {
      throw new Error(`Feature diagram "${source}" output does not match its specification declaration.`);
    }
    diagrams.push({
      source,
      sourceSha256: sha256(sourceText),
      role,
      kind: kind as FeatureDiagram['kind'],
      scenarios: [...scenarios] as string[],
      title: diagram.meta.title.trim(),
      route: `/${generatedRelative}`,
    });
  }
  if (diagrams.filter((diagram) => diagram.role === 'core').length > 1) {
    throw new Error(`Feature "${featureSourcePath}" may declare at most one core diagram.`);
  }
  return diagrams.sort((left, right) =>
    left.role.localeCompare(right.role) || left.source.localeCompare(right.source));
}

async function parseDocument(
  projectRoot: string,
  collection: SourceCollection,
  relativePath: string,
): Promise<SourceDocument> {
  const sourcePath = posix.join(collection.sourceBase, posixPath(relativePath));
  const absolutePath = resolve(projectRoot, sourcePath);
  const [source, resolvedPath] = await Promise.all([readFile(absolutePath, 'utf8'), realpath(absolutePath)]);
  const parsed = matter(source);
  const title = typeof parsed.data.title === 'string' ? parsed.data.title.trim() : headingTitle(parsed.content);
  const route = routeFor(collection, posixPath(relativePath), parsed.data.slug, parsed.data.id);
  const base = {
    collectionId: collection.id,
    contentKind: collection.contentKind,
    sourcePath,
    realPath: resolvedPath,
    title,
    sourceSha256: sha256(source),
    frontMatter: parsed.data,
    content: parsed.content,
    links: [],
    state: 'parsed' as const,
    route,
    sidebarLabel: typeof parsed.data.sidebar_label === 'string' ? parsed.data.sidebar_label : title,
    sidebarPosition: typeof parsed.data.sidebar_position === 'number' ? parsed.data.sidebar_position : undefined,
    slug: typeof parsed.data.slug === 'string' ? parsed.data.slug : undefined,
  };
  if (collection.id === 'docs') return base as ProjectDocument;
  if (collection.id === 'feature-implementations') return base as FeatureImplementation;
  if (collection.id === 'architecture') {
    if (posix.basename(relativePath) === 'design.md') {
      return {
        ...base,
        collectionId: 'architecture',
        contentKind: 'module-design',
        route: routeFor(collection, posixPath(relativePath), parsed.data.slug),
        moduleSourcePath: posix.join(posix.dirname(sourcePath), 'module.md'),
      } as ModuleDesign;
    }
    const architectureKind = parsed.data.kind as ArchitectureKind;
    const view = typeof parsed.data.view === 'string'
      ? parsed.data.view.trim()
      : typeof parsed.data.architecture_view === 'string'
        ? parsed.data.architecture_view.trim()
        : undefined;
    let architectureViewSource: string | undefined;
    let architectureViewSha256: string | undefined;
    let architectureViewRoute: string | undefined;
    if (view) {
      architectureViewSource = posix.normalize(posixPath(view));
      const viewPath = resolve(projectRoot, architectureViewSource);
      try {
        const viewText = await readFile(viewPath, 'utf8');
        const viewDocument = JSON.parse(viewText) as {meta?: {output?: unknown}};
        architectureViewSha256 = sha256(viewText);
        if (typeof viewDocument.meta?.output === 'string') {
          const outputPath = resolve(dirname(viewPath), viewDocument.meta.output);
          const generatedRelative = posixPath(relative(resolve(projectRoot, 'generated'), outputPath));
          if (generatedRelative !== '..' && !generatedRelative.startsWith('../')) {
            architectureViewRoute = `/${generatedRelative}`;
          }
        }
      } catch (error) {
        // The deterministic validator emits the actionable finding after discovery.
      }
    }
    return {
      ...base,
      collectionId: 'architecture',
      architectureId: typeof parsed.data.id === 'string' ? parsed.data.id.trim() : '',
      architectureKind,
      moduleId: typeof parsed.data.module === 'string' ? parsed.data.module.trim() : undefined,
      parentId: typeof parsed.data.parent === 'string' ? parsed.data.parent.trim() : undefined,
      architectureViewSource,
      architectureViewSha256,
      architectureViewRoute,
    } as ArchitectureSource;
  }
  return {
    ...base,
    collectionId: 'features',
    featureId: typeof parsed.data.id === 'string' ? parsed.data.id.trim() : '',
    kind: parsed.data.kind === 'feature' ? 'feature' : (parsed.data.kind as 'feature'),
    moduleId: typeof parsed.data.module === 'string' ? parsed.data.module.trim() : '',
    status: parsed.content.match(/^\*\*Status\*\*:\s*(.+?)\s*$/m)?.[1]?.trim() ?? '',
    featureDirectory: posix.dirname(sourcePath),
    diagrams: await parseFeatureDiagrams(projectRoot, sourcePath, parsed.data.diagrams),
    featureLevel: typeof parsed.data.parent_feature === 'string' ? 'subfeature' : 'feature',
    parentFeatureId: typeof parsed.data.parent_feature === 'string' ? parsed.data.parent_feature.trim() : undefined,
    outcome: sectionText(parsed.content, 'Outcome') || title,
    subfeatureIds: Array.isArray(parsed.data.subfeatures)
      ? parsed.data.subfeatures.filter((value): value is string => typeof value === 'string')
      : [],
    subfeatures: [],
    siblings: [],
  } as FeatureSpecification;
}

function resolveFeatureRelations(documents: SourceDocument[], findings: ValidationFinding[]): void {
  const features = documents.filter((document): document is FeatureSpecification => document.collectionId === 'features');
  const byId = new Map(features.map((feature) => [feature.featureId, feature]));
  const byDirectory = new Map(features.map((feature) => [feature.featureDirectory, feature]));
  for (const feature of features) {
    const childPath = /\/subfeatures\/[^/]+$/.test(`/${feature.featureDirectory}`);
    if ((feature.featureLevel === 'subfeature') !== childPath) {
      findings.push({
        ruleId: 'feature.containment.path', severity: 'error', sourcePath: feature.sourcePath,
        message: 'Sub-feature metadata and canonical subfeatures/<NNN-name>/ path disagree.',
        remediation: 'Use parent_feature only at one immediate canonical sub-feature level.',
      });
    }
    if (feature.featureLevel === 'subfeature' && feature.subfeatureIds.length) {
      findings.push({
        ruleId: 'feature.containment.depth', severity: 'error', sourcePath: feature.sourcePath,
        message: 'A sub-feature cannot register another sub-feature.',
        remediation: 'Keep feature containment to one immediate level.',
      });
    }
    if (feature.featureLevel !== 'subfeature') continue;
    const parent = feature.parentFeatureId ? byId.get(feature.parentFeatureId) : undefined;
    const expectedParentDirectory = posix.dirname(posix.dirname(feature.featureDirectory));
    if (!parent || parent.featureDirectory !== expectedParentDirectory) {
      findings.push({
        ruleId: 'feature.containment.parent', severity: 'error', sourcePath: feature.sourcePath,
        message: `Parent feature "${feature.parentFeatureId ?? '<missing>'}" does not match the canonical parent directory.`,
        remediation: 'Declare one existing top-level parent and place the child directly beneath its subfeatures/ directory.',
      });
      continue;
    }
    if (parent.moduleId !== feature.moduleId || !parent.subfeatureIds.includes(feature.featureId)) {
      findings.push({
        ruleId: 'feature.containment.registration', severity: 'error', sourcePath: feature.sourcePath,
        message: 'Parent registration, child back-reference, or providing module disagrees.',
        remediation: 'Make the parent subfeatures list, child parent_feature, and module agree bidirectionally.',
      });
      continue;
    }
    feature.parentFeatureRoute = parent.route;
  }
  for (const parent of features.filter((feature) => feature.featureLevel === 'feature')) {
    parent.subfeatures = parent.subfeatureIds.flatMap((childId) => {
      const child = byId.get(childId);
      if (!child) {
        findings.push({
          ruleId: 'feature.containment.child', severity: 'error', sourcePath: parent.sourcePath,
          message: `Registered sub-feature "${childId}" does not resolve.`,
          remediation: 'Create the canonical child or remove the dangling registration.',
        });
        return [];
      }
      return [{featureId: child.featureId, title: child.title, outcome: child.outcome, status: child.status, route: child.route}];
    });
    for (const child of features.filter((feature) => feature.parentFeatureId === parent.featureId)) {
      child.siblings = parent.subfeatures.filter((item) => item.featureId !== child.featureId);
    }
  }
  for (const implementation of documents.filter(
    (document): document is FeatureImplementation => document.collectionId === 'feature-implementations',
  )) {
    const specification = byDirectory.get(posix.dirname(implementation.sourcePath));
    if (!specification) continue;
    implementation.featureId = specification.featureId;
    implementation.moduleId = specification.moduleId;
    implementation.featureLevel = specification.featureLevel;
    implementation.parentFeatureId = specification.parentFeatureId;
    implementation.parentFeatureRoute = specification.parentFeatureRoute;
    implementation.subfeatures = specification.subfeatures;
    implementation.siblings = specification.siblings;
    implementation.specificationRoute = specification.route;
    specification.implementationRoute = implementation.route;
  }
}

function resolveModuleRelations(documents: SourceDocument[]): void {
  const modules = new Map(documents
    .filter((document): document is ArchitectureSource =>
      document.contentKind === 'architecture-source' && (document as ArchitectureSource).architectureKind === 'module')
    .map((module) => [module.sourcePath, module]));
  for (const design of documents.filter((document): document is ModuleDesign => document.contentKind === 'module-design')) {
    const module = modules.get(design.moduleSourcePath);
    if (!module) continue;
    design.moduleId = module.architectureId;
    design.moduleRoute = module.route;
    module.designReferenceRoute = design.route;
  }
}

function unpairedDesignFinding(relativePath: string, specsMarkdown: Set<string>): ValidationFinding | undefined {
  const directory = posix.dirname(relativePath);
  const sibling = (name: string) => (directory === '.' ? name : posix.join(directory, name));
  if (specsMarkdown.has(sibling('module.md'))) return undefined;
  const sourcePath = posix.join('specs', relativePath);
  const directoryPath = posix.join('specs', directory);
  if (specsMarkdown.has(sibling('spec.md'))) {
    return {
      ruleId: 'feature.design.legacy', severity: 'error', sourcePath,
      message: `Legacy feature design "${sourcePath}" sits beside spec.md; a feature root's accepted realization is published from implementation.md.`,
      remediation: `Rename ${directoryPath}/design.md to ${directoryPath}/implementation.md (merging into an existing implementation.md first) so it is published as the feature's implementation page.`,
    };
  }
  return {
    ruleId: 'module.design.unpaired', severity: 'error', sourcePath,
    message: 'design.md has no sibling module.md, so it cannot be published as a module design reference.',
    remediation: `Add ${directoryPath}/module.md (the module summary this reference describes) or move design.md out of specs/.`,
  };
}

export async function buildRegistry(projectRoot: string): Promise<ContentRegistry> {
  const root = resolve(projectRoot);
  const documents: SourceDocument[] = [];
  const excludedSources: ExcludedSource[] = [];
  const findings: ValidationFinding[] = [];
  const specsMarkdown = new Set((await fg(['**/*.md'], {
    cwd: resolve(root, 'specs'), onlyFiles: true, unique: true, followSymbolicLinks: false,
  })).map(posixPath));

  for (const collection of collections) {
    const basePath = resolve(root, collection.sourceBase);
    const paths = await fg(collection.include, {
      cwd: basePath, onlyFiles: true, unique: true, followSymbolicLinks: false,
      ignore: collection.sourceBase === 'specs' ? temporalWorkspaceIgnore : [],
    });
    for (const path of paths.sort()) {
      if (collection.id === 'architecture' && posix.basename(posixPath(path)) === 'design.md') {
        const finding = unpairedDesignFinding(posixPath(path), specsMarkdown);
        if (finding) {
          findings.push(finding);
          continue;
        }
      }
      try {
        documents.push(await parseDocument(root, collection, path));
      } catch (error) {
        findings.push({
          ruleId: 'content.read.failed', severity: 'error',
          sourcePath: posix.join(collection.sourceBase, posixPath(path)),
          message: error instanceof Error ? error.message : 'The source could not be read.',
          remediation: 'Ensure the source is a readable UTF-8 Markdown file within the project root.',
        });
      }
    }
  }

  const includedSources = new Set(documents.map((document) => document.sourcePath));
  for (const path of [...specsMarkdown].sort()) {
    const sourcePath = posix.join('specs', path);
    if (!includedSources.has(sourcePath)) {
      excludedSources.push({sourcePath, reason: 'not-canonical-feature-artifact'});
    }
  }

  documents.sort((left, right) => left.sourcePath.localeCompare(right.sourcePath));
  resolveFeatureRelations(documents, findings);
  resolveModuleRelations(documents);
  return populateLinks({projectRoot: root, collections, documents, excludedSources, findings});
}

export function sourcePathFromAbsolute(projectRoot: string, absolutePath: string): string {
  return posixPath(relative(resolve(projectRoot), resolve(absolutePath)));
}

export function sourceDirectory(sourcePath: string): string {
  return posixPath(dirname(sourcePath));
}
