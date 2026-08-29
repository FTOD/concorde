import {createHash} from 'node:crypto';
import {realpath, readFile} from 'node:fs/promises';
import {dirname, posix, relative, resolve} from 'node:path';

import fg from 'fast-glob';
import matter from 'gray-matter';

import type {
  ArchitectureKind, ArchitectureSource, CollectionId, ContentRegistry, DiagramKind, ExcludedSource, FeatureImplementation, FeatureDiagram,
  FeaturePageContext, FeatureDesign, FeatureAbstract, ModuleDesign, ModuleDiagram, ProjectDocument, SourceCollection, SourceDocument,
  ValidationFinding,
} from './types';
import {diagramKinds, listModuleDiagramSources} from './diagrams';
import {populateLinks} from './links';
import {projectedSpecPath, semanticFeaturePath, semanticFeatureRoutes, semanticFeatureStagedPath} from './routes';

export const collections: SourceCollection[] = [
  {id: 'home', sourceBase: '.', routeBase: '/', include: ['README.md'], contentKind: 'project-document'},
  {
    // `**/design.md` is admitted here only beside `module.md`; feature design.md belongs to `features`.
    id: 'architecture', sourceBase: 'specs', routeBase: '/architecture',
    include: ['**/module.md', '**/design.md', '**/architecture/contracts/**/contract.md'], contentKind: 'architecture-source',
  },
  {id: 'docs', sourceBase: 'docs', routeBase: '/docs', include: ['**/*.md'], contentKind: 'project-document'},
  // The abstract takes the feature landing route; design and implementation are companion pages.
  {id: 'feature-abstracts', sourceBase: 'specs', routeBase: '/features', include: ['**/abstract.md'], contentKind: 'feature-abstract'},
  {id: 'features', sourceBase: 'specs', routeBase: '/features', include: ['**/design.md'], contentKind: 'feature-design'},
  {id: 'feature-implementations', sourceBase: 'specs', routeBase: '/features', include: ['**/implementation.md'], contentKind: 'feature-implementation'},
];

/** Temporal attempts (`<feature root>/attempt/**`) are never publishable sources. */
const temporalWorkspaceIgnore = ['**/attempt/**'];
const temporalWorkspacePattern = /(^|\/)attempt\//;
const legacyWorkspacePattern = /(^|\/)implementation\//;

/** Sidebar labels of the two feature pages that sit beneath the abstract landing page. */
const featureCompanionLabels: Partial<Record<CollectionId, string>> = {features: 'Design', 'feature-implementations': 'Implementation'};

const posixPath = (value: string) => value.split('\\').join('/');
const sha256 = (value: string) => createHash('sha256').update(value).digest('hex');
const compareText = (left: string, right: string) => left < right ? -1 : left > right ? 1 : 0;

function headingTitle(content: string): string {
  return content.match(/^#\s+(.+?)\s*$/m)?.[1]?.replace(/^(?:Feature Design|Feature Abstract):\s*/i, '').trim() ?? '';
}

function sectionText(content: string, heading: string): string {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return content.match(new RegExp(`^##\\s+${escaped}\\s*$\\n([\\s\\S]*?)(?=^##\\s+|$)`, 'm'))?.[1]
    ?.replace(/\s+/g, ' ').trim() ?? '';
}

function routeFor(collection: SourceCollection, relativePath: string, slug?: unknown, sourceId?: unknown): string {
  if (collection.id === 'home') return '/';
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

async function parseDeclaredDiagrams(
  projectRoot: string,
  ownerSourcePath: string,
  rawDeclarations: unknown,
  ownerKind: 'feature' | 'documentation',
): Promise<FeatureDiagram[]> {
  if (rawDeclarations === undefined) return [];
  if (!Array.isArray(rawDeclarations)) throw new Error('Diagrams must be declared as a list.');
  const ownerDirectory = posix.dirname(ownerSourcePath);
  const diagramDirectory = posix.join(ownerDirectory, 'diagrams');
  const diagrams: FeatureDiagram[] = [];
  for (const rawDeclaration of rawDeclarations) {
    if (!rawDeclaration || typeof rawDeclaration !== 'object' || Array.isArray(rawDeclaration)) {
      throw new Error('Each diagram declaration must be a mapping.');
    }
    const declaration = rawDeclaration as Record<string, unknown>;
    const source = typeof declaration.source === 'string' ? posix.normalize(posixPath(declaration.source)) : '';
    if (!source || posix.dirname(source) !== diagramDirectory || posix.basename(source) === 'architecture.json') {
      throw new Error(`Declared diagram "${source || '<missing>'}" must be directly under ${diagramDirectory}/ with a descriptive filename.`);
    }
    const absoluteSource = resolve(projectRoot, source);
    const sourceFromRoot = posixPath(relative(resolve(projectRoot), absoluteSource));
    if (sourceFromRoot === '..' || sourceFromRoot.startsWith('../')) {
      throw new Error(`Declared diagram "${source}" escapes the project root.`);
    }
    const sourceText = await readFile(absoluteSource, 'utf8');
    const diagram = JSON.parse(sourceText) as {diagram_type?: unknown; meta?: {title?: unknown; output?: unknown}};
    const role = declaration.role;
    const kind = declaration.kind;
    const scenarios = declaration.scenarios;
    if (typeof kind !== 'string' || !diagramKinds.has(kind as DiagramKind) || diagram.diagram_type !== kind) {
      throw new Error(`Declared diagram "${source}" has a missing or inconsistent diagram kind.`);
    }
    if (role !== 'core' && role !== 'supplemental') {
      throw new Error(`Declared diagram "${source}" must declare role as core or supplemental.`);
    }
    if (role === 'core' && kind !== 'architecture') {
      throw new Error(`Core feature diagram "${source}" must use the architecture kind; dynamic views are supplemental.`);
    }
    if (ownerKind === 'documentation' && role !== 'supplemental') {
      throw new Error(`Documentation diagram "${source}" must use supplemental role.`);
    }
    if (!Array.isArray(scenarios) || scenarios.length === 0 || !scenarios.every((value) => typeof value === 'string' && value.length > 0)) {
      throw new Error(`Declared diagram "${source}" must declare at least one scenario or named question.`);
    }
    if (typeof diagram.meta?.title !== 'string' || !diagram.meta.title.trim() || typeof diagram.meta.output !== 'string') {
      throw new Error(`Declared diagram "${source}" requires meta.title and meta.output.`);
    }
    const outputPath = resolve(dirname(absoluteSource), diagram.meta.output);
    const generatedRelative = posixPath(relative(resolve(projectRoot, 'generated'), outputPath));
    if (generatedRelative === '..' || generatedRelative.startsWith('../')) {
      throw new Error(`Declared diagram "${source}" output must be beneath generated/.`);
    }
    const declaredOutput = typeof declaration.output === 'string' ? resolve(projectRoot, declaration.output) : '';
    if (!declaredOutput || declaredOutput !== outputPath) {
      throw new Error(`Declared diagram "${source}" output does not match its owner declaration.`);
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
    throw new Error(`Owner "${ownerSourcePath}" may declare at most one core diagram.`);
  }
  return diagrams.sort((left, right) =>
    left.role.localeCompare(right.role) || left.source.localeCompare(right.source));
}

/** Map every diagram beneath the module's `architecture/diagrams/` to its delivered route; unmappable sources are reported. */
async function discoverModuleDiagrams(
  projectRoot: string,
  moduleSourcePath: string,
): Promise<{diagrams: ModuleDiagram[]; unpublishable: string[]}> {
  const diagrams: ModuleDiagram[] = [];
  const unpublishable: string[] = [];
  for (const source of await listModuleDiagramSources(projectRoot, moduleSourcePath)) {
    try {
      const absoluteSource = resolve(projectRoot, source);
      const text = await readFile(absoluteSource, 'utf8');
      const document = JSON.parse(text) as {diagram_type?: unknown; meta?: {title?: unknown; output?: unknown}};
      if (typeof document.diagram_type !== 'string' || !diagramKinds.has(document.diagram_type as DiagramKind)) {
        throw new Error('unsupported diagram_type');
      }
      if (typeof document.meta?.title !== 'string' || !document.meta.title.trim() || typeof document.meta.output !== 'string') {
        throw new Error('meta.title and meta.output are required');
      }
      const outputPath = resolve(dirname(absoluteSource), document.meta.output);
      const generatedRelative = posixPath(relative(resolve(projectRoot, 'generated'), outputPath));
      if (generatedRelative === '..' || generatedRelative.startsWith('../')) throw new Error('output must be beneath generated/');
      diagrams.push({
        source,
        sourceSha256: sha256(text),
        kind: document.diagram_type as DiagramKind,
        title: document.meta.title.trim(),
        route: `/${generatedRelative}`,
      });
    } catch {
      // The deterministic validator emits the actionable finding after discovery.
      unpublishable.push(source);
    }
  }
  return {diagrams, unpublishable};
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
  // Routes and staging paths of specs sources drop the `architecture/` grouping segment.
  const projectedPath = collection.sourceBase === 'specs' ? projectedSpecPath(posixPath(relativePath)) : posixPath(relativePath);
  const route = routeFor(collection, projectedPath, parsed.data.slug, parsed.data.id);
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
    ...(collection.sourceBase === 'specs' ? {stagedPath: projectedPath} : {}),
    sidebarLabel: typeof parsed.data.sidebar_label === 'string' ? parsed.data.sidebar_label : featureCompanionLabels[collection.id] ?? title,
    sidebarPosition: typeof parsed.data.sidebar_position === 'number' ? parsed.data.sidebar_position : undefined,
    slug: typeof parsed.data.slug === 'string' ? parsed.data.slug : undefined,
  };
  if (collection.id === 'home' || collection.id === 'docs') {
    return {
      ...base,
      ...(collection.id === 'home' ? {stagedPath: relativePath} : {}),
      ...(collection.id === 'docs' ? {
        diagrams: await parseDeclaredDiagrams(projectRoot, sourcePath, parsed.data.diagrams, 'documentation'),
      } : {}),
    } as ProjectDocument;
  }
  if (collection.id === 'feature-abstracts') {
    // The path-derived route stands in until the abstract is paired with design.md and takes the landing route.
    return {...base, collectionId: 'feature-abstracts', route: routeFor(collection, projectedPath, parsed.data.slug)} as FeatureAbstract;
  }
  if (collection.id === 'feature-implementations') {
    return {...base, collectionId: 'feature-implementations', route: routeFor(collection, projectedPath, parsed.data.slug)} as FeatureImplementation;
  }
  if (collection.id === 'architecture') {
    if (posix.basename(relativePath) === 'design.md') {
      return {
        ...base,
        collectionId: 'architecture',
        contentKind: 'module-design',
        route: routeFor(collection, projectedPath, parsed.data.slug),
        moduleSourcePath: posix.join(posix.dirname(sourcePath), 'module.md'),
      } as ModuleDesign;
    }
    const architectureKind = parsed.data.kind as ArchitectureKind;
    const architecture = {
      ...base,
      collectionId: 'architecture',
      architectureId: typeof parsed.data.id === 'string' ? parsed.data.id.trim() : '',
      architectureKind,
      moduleId: typeof parsed.data.module === 'string' ? parsed.data.module.trim() : undefined,
      parentId: typeof parsed.data.parent === 'string' ? parsed.data.parent.trim() : undefined,
    } as ArchitectureSource;
    if (architectureKind === 'module') {
      const {diagrams, unpublishable} = await discoverModuleDiagrams(projectRoot, sourcePath);
      architecture.architectureDiagrams = diagrams;
      if (unpublishable.length) architecture.unpublishableDiagrams = unpublishable;
    }
    return architecture;
  }
  return {
    ...base,
    collectionId: 'features',
    // The id-derived landing route belongs to abstract.md; design.md is published at `<root>/design`.
    route: routeFor(collection, projectedPath),
    landingRoute: route,
    featureId: typeof parsed.data.id === 'string' ? parsed.data.id.trim() : '',
    kind: parsed.data.kind === 'feature' ? 'feature' : (parsed.data.kind as 'feature'),
    moduleId: typeof parsed.data.module === 'string' ? parsed.data.module.trim() : '',
    status: parsed.content.match(/^\*\*Status\*\*:\s*(.+?)\s*$/m)?.[1]?.trim() ?? '',
    featureDirectory: posix.dirname(sourcePath),
    diagrams: await parseDeclaredDiagrams(projectRoot, sourcePath, parsed.data.diagrams, 'feature'),
    featureLevel: typeof parsed.data.parent_feature === 'string' ? 'subfeature' : 'feature',
    parentFeatureId: typeof parsed.data.parent_feature === 'string' ? parsed.data.parent_feature.trim() : undefined,
    outcome: sectionText(parsed.content, 'Outcome') || title,
    refinementIds: Array.isArray(parsed.data.refines)
      ? parsed.data.refines.filter((value): value is string => typeof value === 'string')
      : [],
    refinements: [],
    subfeatureIds: Array.isArray(parsed.data.subfeatures)
      ? parsed.data.subfeatures.filter((value): value is string => typeof value === 'string')
      : [],
    subfeatures: [],
    siblings: [],
  } as FeatureDesign;
}

/** The identity and abstract-routed navigation shared by a feature root's three pages. */
function featureContext(design: FeatureDesign): FeaturePageContext {
  return {
    featureId: design.featureId,
    moduleId: design.moduleId,
    moduleRoute: design.moduleRoute,
    featureLevel: design.featureLevel,
    parentFeatureId: design.parentFeatureId,
    parentFeatureRoute: design.parentFeatureRoute,
    subfeatures: design.subfeatures,
    siblings: design.siblings,
    refinements: design.refinements,
  };
}

function resolveFeatureRelations(documents: SourceDocument[], findings: ValidationFinding[]): void {
  const features = documents.filter((document): document is FeatureDesign => document.collectionId === 'features');
  const byId = new Map(features.map((feature) => [feature.featureId, feature]));
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
  }

  // Assign identity-derived routes only after feature containment resolves. Module containment is
  // projected separately into the generated Features sidebar and never leaks storage wrappers into URLs.
  const semanticPaths = new Map<string, string>();
  for (const feature of features.filter((item) => item.featureLevel === 'feature')) {
    semanticPaths.set(feature.featureId, semanticFeaturePath(feature.featureId));
  }
  for (const feature of features.filter((item) => item.featureLevel === 'subfeature')) {
    const parentPath = feature.parentFeatureId ? semanticPaths.get(feature.parentFeatureId) : undefined;
    semanticPaths.set(feature.featureId, semanticFeaturePath(feature.featureId, parentPath));
  }
  for (const feature of features) {
    const semanticPath = semanticPaths.get(feature.featureId) ?? semanticFeaturePath(feature.featureId);
    const routes = semanticFeatureRoutes(semanticPath);
    feature.landingRoute = routes.landing;
    feature.route = routes.design;
    feature.stagedPath = semanticFeatureStagedPath(semanticPath, 'design');
    if (feature.parentFeatureId) feature.parentFeatureRoute = byId.get(feature.parentFeatureId)?.landingRoute;
  }
  for (const feature of features) {
    feature.refinements = feature.refinementIds.flatMap((refinementId) => {
      const target = byId.get(refinementId);
      return target
        ? [{featureId: target.featureId, title: target.title, outcome: target.outcome, status: target.status, route: target.landingRoute}]
        : [];
    });
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
      return [{featureId: child.featureId, title: child.title, outcome: child.outcome, status: child.status, route: child.landingRoute}];
    });
    for (const child of features.filter((feature) => feature.parentFeatureId === parent.featureId)) {
      child.siblings = parent.subfeatures.filter((item) => item.featureId !== child.featureId);
    }
  }
  // Pair each design with its sibling abstract (which takes the landing route) and implementation.
  const abstracts = new Map(documents
    .filter((document): document is FeatureAbstract => document.collectionId === 'feature-abstracts')
    .map((abstract) => [posix.dirname(abstract.sourcePath), abstract]));
  const implementations = new Map(documents
    .filter((document): document is FeatureImplementation => document.collectionId === 'feature-implementations')
    .map((implementation) => [posix.dirname(implementation.sourcePath), implementation]));
  for (const design of features) {
    const abstract = abstracts.get(design.featureDirectory);
    const implementation = implementations.get(design.featureDirectory);
    if (abstract) {
      abstract.route = design.landingRoute;
      const semanticPath = posix.dirname(design.stagedPath ?? '');
      abstract.stagedPath = semanticFeatureStagedPath(semanticPath, 'abstract');
      design.abstractRoute = abstract.route;
    }
    if (implementation) {
      const semanticPath = posix.dirname(design.stagedPath ?? '');
      implementation.route = semanticFeatureRoutes(semanticPath).implementation;
      implementation.stagedPath = semanticFeatureStagedPath(semanticPath, 'implementation');
      design.implementationRoute = implementation.route;
    }
    if (abstract) {
      Object.assign(abstract, featureContext(design), {
        status: design.status,
        diagrams: design.diagrams,
        designRoute: design.route,
        implementationRoute: design.implementationRoute,
      });
    }
    if (implementation) {
      Object.assign(implementation, featureContext(design), {
        abstractRoute: design.abstractRoute,
        designRoute: design.route,
      });
    }
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
  const modulesById = new Map([...modules.values()].map((module) => [module.architectureId, module]));
  for (const feature of documents.filter((document): document is FeatureDesign => document.collectionId === 'features')) {
    feature.moduleRoute = modulesById.get(feature.moduleId)?.route;
  }
}

/** Which canonical sibling anchors a specs/ directory: module.md or feature design.md. */
function rootSibling(relativePath: string, specsMarkdown: Set<string>): 'module' | 'feature' | undefined {
  const directory = posix.dirname(relativePath);
  const sibling = (name: string) => (directory === '.' ? name : posix.join(directory, name));
  if (specsMarkdown.has(sibling('module.md'))) return 'module';
  if (specsMarkdown.has(sibling('design.md'))) return 'feature';
  return undefined;
}

function legacyNameFinding(relativePath: string): ValidationFinding {
  const directoryPath = posix.join('specs', posix.dirname(relativePath));
  return {
    ruleId: 'feature.name.legacy', severity: 'error', sourcePath: posix.join('specs', relativePath),
    message: `${posix.basename(relativePath)} is a legacy feature artifact name.`,
    remediation: `Use ${directoryPath}/abstract.md, ${directoryPath}/design.md, ${directoryPath}/implementation.md, and ${directoryPath}/attempt/ for the canonical feature layout.`,
  };
}

function legacyWorkspaceFinding(relativePath: string): ValidationFinding {
  return {
    ruleId: 'feature.attempt.legacy', severity: 'error', sourcePath: posix.join('specs', relativePath),
    message: 'A temporal artifact remains under the former implementation/ directory name.',
    remediation: 'Rename the feature-root implementation/ directory to attempt/.',
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
      const relativePath = posixPath(path);
      if (collection.sourceBase === 'specs' && posix.basename(relativePath) === 'design.md') {
        // module.md makes design.md a module reference; otherwise it is the feature design authority.
        const sibling = rootSibling(relativePath, specsMarkdown);
        if (sibling !== (collection.id === 'architecture' ? 'module' : 'feature')) {
          continue;
        }
      }
      try {
        documents.push(await parseDocument(root, collection, path));
      } catch (error) {
        findings.push({
          ruleId: 'content.read.failed', severity: 'error',
          sourcePath: posix.join(collection.sourceBase, relativePath),
          message: error instanceof Error ? error.message : 'The source could not be read.',
          remediation: 'Ensure the source is a readable UTF-8 Markdown file within the project root.',
        });
      }
    }
  }

  if (!documents.some((document) => document.collectionId === 'home') &&
      !findings.some((finding) => finding.sourcePath === 'README.md')) {
    findings.push({
      ruleId: 'content.home.required', severity: 'error', sourcePath: 'README.md',
      message: 'The required project README homepage is missing.',
      remediation: 'Add a readable root README.md with a level-one title and project introduction.',
    });
  }

  const includedSources = new Set(documents.map((document) => document.sourcePath));
  for (const path of [...specsMarkdown].sort()) {
    const sourcePath = posix.join('specs', path);
    if (!includedSources.has(sourcePath)) {
      excludedSources.push({sourcePath, reason: 'not-canonical-feature-artifact'});
    }
    if (!temporalWorkspacePattern.test(path) && ['spec.md', 'tldr.md'].includes(posix.basename(path))) {
      findings.push(legacyNameFinding(path));
    }
    if (legacyWorkspacePattern.test(path)) findings.push(legacyWorkspaceFinding(path));
  }

  documents.sort((left, right) => compareText(left.sourcePath, right.sourcePath));
  resolveModuleRelations(documents);
  resolveFeatureRelations(documents, findings);
  return populateLinks({projectRoot: root, collections, documents, excludedSources, findings});
}

export function sourcePathFromAbsolute(projectRoot: string, absolutePath: string): string {
  return posixPath(relative(resolve(projectRoot), resolve(absolutePath)));
}

export function sourceDirectory(sourcePath: string): string {
  return posixPath(dirname(sourcePath));
}
