import {createHash} from 'node:crypto';
import {lstat, readFile, realpath} from 'node:fs/promises';
import {posix, relative, resolve} from 'node:path';

import fg from 'fast-glob';
import matter from 'gray-matter';

import {diagramKinds, listModuleDiagramSources} from './diagrams';
import {populateLinks} from './links';
import {featureRoute, featureStagedPath, moduleRoute, moduleStagedPath} from './routes';
import type {
  ContentRegistry, DiagramKind, ExcludedSource, FeatureDesign, ModuleArchitecture, ModuleDiagram,
  ProjectDocument, SourceCollection, SourceDocument, ValidationFinding,
} from './types';

export const collections: SourceCollection[] = [
  {id: 'home', sourceBase: '.', routeBase: '/', include: ['README.md'], contentKind: 'project-document'},
  {id: 'architecture', sourceBase: 'specs', routeBase: '/architecture', include: ['**/architecture.md'], contentKind: 'module-architecture'},
  {id: 'docs', sourceBase: 'docs', routeBase: '/docs', include: ['**/*.md'], contentKind: 'project-document'},
  {id: 'features', sourceBase: 'specs', routeBase: '/features', include: ['**/features/*.md'], contentKind: 'feature-design'},
];

// Never admit legacy specification-local control state as a page; profile validation below rejects it.
const legacyControlStateIgnore = ['**/attempts/**'];
const legacyAttemptPattern = /(^|\/)attempts\//;
const nestedFeaturePattern = /(^|\/)subfeatures\//;
const canonicalFeaturePattern = /(^|\/)features\/[^/]+\.md$/;
const legacyArtifactNames = new Set(['abstract.md', 'implementation.md', 'module.md', 'contract.md', 'spec.md', 'tldr.md']);
const posixPath = (value: string) => value.split('\\').join('/');
const sha256 = (value: string) => createHash('sha256').update(value).digest('hex');
const compareText = (left: string, right: string) => left < right ? -1 : left > right ? 1 : 0;

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string' && Boolean(item.trim())).map((item) => item.trim()) : [];
}

function headingTitle(content: string): string {
  return content.match(/^#\s+(.+?)\s*$/m)?.[1]
    ?.replace(/^(?:Feature Design|Module Architecture):\s*/i, '').trim() ?? '';
}

function sectionText(content: string, heading: string): string {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return content.match(new RegExp(`^##\\s+${escaped}(?:\\s+and\\s+[^\\n]+)?\\s*$\\n([\\s\\S]*?)(?=^##\\s+|$)`, 'mi'))?.[1]
    ?.replace(/\s+/g, ' ').trim() ?? '';
}

function docsRoute(collection: SourceCollection, relativePath: string, slug?: unknown): string {
  if (collection.id === 'home') return '/';
  if (typeof slug === 'string' && slug.trim()) {
    const clean = slug.trim().replace(/^\/+|\/+$/g, '');
    return clean ? `${collection.routeBase}/${clean}` : collection.routeBase;
  }
  const withoutExtension = relativePath.replace(/\.md$/i, '').replace(/(^|\/)index$/i, '$1');
  const clean = withoutExtension.replace(/^\/+|\/+$/g, '');
  return clean ? `${collection.routeBase}/${clean}` : collection.routeBase;
}

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
      const outputPath = resolve(absoluteSource, '..', document.meta.output);
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
    route: docsRoute(collection, posixPath(relativePath), parsed.data.slug),
    sidebarLabel: typeof parsed.data.sidebar_label === 'string' ? parsed.data.sidebar_label : title,
    sidebarPosition: typeof parsed.data.sidebar_position === 'number' ? parsed.data.sidebar_position : undefined,
    slug: typeof parsed.data.slug === 'string' ? parsed.data.slug : undefined,
  };
  if (collection.id === 'home' || collection.id === 'docs') {
    return {
      ...base,
      ...(collection.id === 'home' ? {stagedPath: relativePath} : {}),
    } as ProjectDocument;
  }
  if (collection.id === 'architecture') {
    const moduleId = typeof parsed.data.id === 'string' ? parsed.data.id.trim() : '';
    const architecture: ModuleArchitecture = {
      ...base,
      collectionId: 'architecture',
      contentKind: 'module-architecture',
      route: moduleRoute(moduleId),
      stagedPath: moduleStagedPath(moduleId),
      moduleId,
      kind: parsed.data.kind as 'module',
      parentId: typeof parsed.data.parent === 'string' ? parsed.data.parent.trim() : undefined,
      moduleIds: stringList(parsed.data.modules),
      featureIds: stringList(parsed.data.features),
      architectureDiagrams: [],
    };
    const {diagrams, unpublishable} = await discoverModuleDiagrams(projectRoot, sourcePath);
    architecture.architectureDiagrams = diagrams;
    if (unpublishable.length) architecture.unpublishableDiagrams = unpublishable;
    return architecture;
  }
  const featureId = typeof parsed.data.id === 'string' ? parsed.data.id.trim() : '';
  return {
    ...base,
    collectionId: 'features',
    contentKind: 'feature-design',
    route: featureRoute(featureId),
    stagedPath: featureStagedPath(featureId),
    featureId,
    kind: parsed.data.kind as 'feature',
    moduleId: typeof parsed.data.module === 'string' ? parsed.data.module.trim() : '',
    status: parsed.content.match(/^\*\*Status\*\*:\s*(.+?)\s*$/m)?.[1]?.trim() ??
      (typeof parsed.data.evidence_status === 'string' ? parsed.data.evidence_status.trim() : ''),
    outcome: sectionText(parsed.content, 'Outcome') || title,
    relatedFeatureIds: stringList(parsed.data.related_features),
    relatedFeatures: [],
  } as FeatureDesign;
}

function relationSummary(feature: FeatureDesign) {
  return {featureId: feature.featureId, title: feature.title, outcome: feature.outcome, status: feature.status, route: feature.route};
}

function resolveRelations(documents: SourceDocument[], findings: ValidationFinding[]): void {
  const modules = documents.filter((document): document is ModuleArchitecture => document.contentKind === 'module-architecture');
  const features = documents.filter((document): document is FeatureDesign => document.contentKind === 'feature-design');
  const modulesById = new Map(modules.map((module) => [module.moduleId, module]));
  const featuresById = new Map(features.map((feature) => [feature.featureId, feature]));

  for (const module of modules) {
    for (const childId of module.moduleIds) {
      const child = modulesById.get(childId);
      if (!child) findings.push({
        ruleId: 'module.child.unresolved', severity: 'error', sourcePath: module.sourcePath,
        message: `Registered child module "${childId}" does not resolve to architecture.md.`,
        remediation: 'Add the direct child module architecture or remove the registration.',
      });
      else if (child.parentId !== module.moduleId) findings.push({
        ruleId: 'module.parent.disagrees', severity: 'error', sourcePath: child.sourcePath,
        message: `Child module "${childId}" does not name "${module.moduleId}" as its parent.`,
        remediation: 'Make the parent modules list and child parent field agree.',
      });
    }
    for (const featureId of module.featureIds) {
      const feature = featuresById.get(featureId);
      if (!feature) findings.push({
        ruleId: 'module.feature.unresolved', severity: 'error', sourcePath: module.sourcePath,
        message: `Registered feature "${featureId}" does not resolve to a direct feature file.`,
        remediation: 'Add the direct level-local feature file or remove the registration.',
      });
      else if (feature.moduleId !== module.moduleId) findings.push({
        ruleId: 'module.feature.owner', severity: 'error', sourcePath: feature.sourcePath,
        message: `Feature "${featureId}" names a different providing module.`,
        remediation: 'Make the feature module field and architecture feature inventory agree.',
      });
    }
  }

  for (const feature of features) {
    const owner = modulesById.get(feature.moduleId);
    feature.moduleRoute = owner?.route;
    if (!owner) findings.push({
      ruleId: 'feature.module.unresolved', severity: 'error', sourcePath: feature.sourcePath,
      message: `Providing module "${feature.moduleId || '<missing>'}" has no published architecture.md.`,
      remediation: 'Declare a real providing module and place the feature directly in that module features directory.',
    });
    else {
      const physicalOwner = posix.dirname(posix.dirname(feature.sourcePath));
      if (posix.dirname(owner.sourcePath) !== physicalOwner || !owner.featureIds.includes(feature.featureId)) findings.push({
        ruleId: 'feature.module.registration', severity: 'error', sourcePath: feature.sourcePath,
        message: 'Feature placement, module field, and architecture feature inventory disagree.',
        remediation: 'Place the feature directly under its providing module and register its stable ID once.',
      });
    }
    feature.relatedFeatures = feature.relatedFeatureIds.flatMap((relatedId) => {
      const related = featuresById.get(relatedId);
      if (related) return [relationSummary(related)];
      findings.push({
        ruleId: 'feature.related.unresolved', severity: 'error', sourcePath: feature.sourcePath,
        message: `Related feature "${relatedId}" does not resolve.`,
        remediation: 'Reference a published feature stable ID or remove the dangling relation.',
      });
      return [];
    });
    if ('diagrams' in feature.frontMatter) findings.push({
      ruleId: 'feature.diagram.forbidden', severity: 'error', sourcePath: feature.sourcePath,
      message: 'Feature designs cannot own diagram sources in Profile 7.',
      remediation: 'Move the maintained diagram to the providing module diagrams/ directory and reference it from architecture.md.',
    });
    if (['parent_feature', 'subfeatures', 'refines'].some((field) => field in feature.frontMatter)) findings.push({
      ruleId: 'feature.hierarchy.forbidden', severity: 'error', sourcePath: feature.sourcePath,
      message: 'Features are flat module capabilities and cannot declare containment metadata.',
      remediation: 'Move the feature directly under a module and express composition with related_features.',
    });
  }
}

function profileFinding(path: string): ValidationFinding | undefined {
  const sourcePath = posix.join('specs', path);
  if (legacyAttemptPattern.test(path) || posix.basename(path) === 'reflections.md') return {
    ruleId: 'source.profile.legacy', severity: 'error', sourcePath,
    message: `${path} is specification-local control state removed in Profile 7.`,
    remediation: 'Move attempts to .concorde/attempts/<stable-feature-id>/ and the reflection log to .concorde/reflections/log.md.',
  };
  if (nestedFeaturePattern.test(path)) return {
    ruleId: 'feature.hierarchy.forbidden', severity: 'error', sourcePath,
    message: 'A nested subfeatures/ source remains in the Profile 7 hierarchy.',
    remediation: 'Move the feature directly into its providing module features/ directory and use related_features.',
  };
  const name = posix.basename(path);
  const explicitlyLegacy = legacyArtifactNames.has(name) || /(^|\/)contracts\//.test(path) ||
    (name === 'design.md' && !canonicalFeaturePattern.test(path));
  return {
    ruleId: 'source.profile.legacy', severity: 'error', sourcePath,
    message: explicitlyLegacy ? `${name} is a removed durable source in Profile 7.` : `${path} is not a Profile 7 publication source.`,
    remediation: 'Keep durable module and feature sources under specs/ and all workflow control state under .concorde/.',
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
  // `.concorde/**` is workflow control state, not a publication source root. Do not discover it
  // here: canonical attempts/logs and unrelated internal control Markdown must be neither pages nor
  // broad Manifest exclusions.

  for (const collection of collections) {
    const paths = await fg(collection.include, {
      cwd: resolve(root, collection.sourceBase), onlyFiles: true, unique: true, followSymbolicLinks: false,
      ignore: collection.sourceBase === 'specs' ? legacyControlStateIgnore : [],
    });
    for (const path of paths.sort()) {
      try {
        documents.push(await parseDocument(root, collection, path));
      } catch (error) {
        findings.push({
          ruleId: 'content.read.failed', severity: 'error', sourcePath: posix.join(collection.sourceBase, posixPath(path)),
          message: error instanceof Error ? error.message : 'The source could not be read.',
          remediation: 'Ensure the source is readable UTF-8 Markdown within the project root.',
        });
      }
    }
  }

  const included = new Set(documents.map((document) => document.sourcePath));
  for (const path of [...specsMarkdown].sort()) {
    const sourcePath = posix.join('specs', path);
    if (included.has(sourcePath)) continue;
    const reason: ExcludedSource['reason'] = profileFinding(path) ? 'legacy-source-profile' : 'non-publication-source';
    excludedSources.push({sourcePath, reason});
    const finding = profileFinding(path);
    if (finding) findings.push(finding);
  }

  documents.sort((left, right) => compareText(left.sourcePath, right.sourcePath));
  resolveRelations(documents, findings);
  const registry = populateLinks({projectRoot: root, collections, documents, excludedSources, findings});
  const assetFindings: ValidationFinding[] = [];
  for (const document of registry.documents) {
    for (const link of document.links.filter((link) => link.kind === 'asset' && !link.rawTarget.startsWith('/'))) {
      if (!link.targetSourcePath) continue;
      try {
        if ((await lstat(resolve(root, link.targetSourcePath))).isFile()) continue;
      } catch { /* Emit one stable source diagnostic below. */ }
      assetFindings.push({
        ruleId: 'link.target.missing', severity: 'error', sourcePath: document.sourcePath, location: link.location,
        message: `Repository asset link "${link.rawTarget}" does not resolve to a regular file.`,
        remediation: 'Correct the relative path, add the maintained asset, or use an explicit external URL.',
      });
    }
  }
  return {...registry, findings: [...registry.findings, ...assetFindings]};
}

export function sourcePathFromAbsolute(projectRoot: string, absolutePath: string): string {
  return posixPath(relative(resolve(projectRoot), resolve(absolutePath)));
}

export function sourceDirectory(sourcePath: string): string {
  return posixPath(posix.dirname(sourcePath));
}
