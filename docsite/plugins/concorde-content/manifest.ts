import {ALL_EDGE_KINDS, deriveFeatureGraph} from './graph';
import {moduleRoute} from './routes';
import type {
  BuildManifest, ContentPage, ContentRegistry, FeatureDesign, FeatureGraphCounts, ModuleArchitecture, SourceDocument,
} from './types';

const isFeature = (document: SourceDocument): document is FeatureDesign => document.contentKind === 'feature-design';
const isModule = (document: SourceDocument): document is ModuleArchitecture => document.contentKind === 'module-architecture';

/** The docsite adapter version; also the Feature Graph 1 `generator.version` (docsite/package.json stays in sync). */
export const GENERATOR_VERSION = '0.7.0';

function navigationFor(document: SourceDocument) {
  const section = document.collectionId === 'architecture' ? 'Architecture' as const : 'Features' as const;
  const parentRoute = isModule(document) && document.parentId ? moduleRoute(document.parentId) : undefined;
  return {section, label: document.sidebarLabel || document.title, ...(parentRoute ? {parentRoute} : {})};
}

export function pageFromDocument(document: SourceDocument): ContentPage {
  return {
    kind: document.contentKind,
    sourcePath: document.sourcePath,
    sourceSha256: document.sourceSha256,
    route: document.route,
    title: document.title,
    navigation: navigationFor(document),
    links: document.links
      .filter((link) => link.targetSourcePath && link.targetRoute)
      .map((link) => ({targetSourcePath: link.targetSourcePath!, targetRoute: link.targetRoute!}))
      .sort((left, right) => `${left.targetSourcePath}\0${left.targetRoute}`.localeCompare(`${right.targetSourcePath}\0${right.targetRoute}`)),
    ...(isModule(document) ? {
      moduleId: document.moduleId,
      ...(document.parentId ? {parentId: document.parentId} : {}),
      architectureDiagrams: document.architectureDiagrams,
    } : {}),
    ...(isFeature(document) ? {
      featureId: document.featureId,
      moduleId: document.moduleId,
      ...(document.moduleRoute ? {moduleRoute: document.moduleRoute} : {}),
      status: document.status,
      relatedFeatures: document.relatedFeatures,
    } : {}),
  };
}

function isRelativePath(value: string): boolean {
  return Boolean(value) && !value.startsWith('/') && !value.startsWith('\\') && !/^[A-Za-z]:[\\/]/.test(value) &&
    value !== '..' && !value.startsWith('../');
}

function assertSorted(values: string[], subject: string): void {
  if (new Set(values).size !== values.length || values.some((value, index) => index > 0 && values[index - 1] > value)) {
    throw new Error(`${subject} must be unique and sorted.`);
  }
}

function assertFeatureGraphCounts(counts: FeatureGraphCounts | undefined): void {
  if (!counts || typeof counts.features !== 'number' || typeof counts.modules !== 'number' || !counts.edges_by_kind) {
    throw new Error('Build Manifest featureGraphCounts is incomplete.');
  }
  for (const kind of ALL_EDGE_KINDS) {
    if (typeof counts.edges_by_kind[kind] !== 'number') throw new Error(`Build Manifest featureGraphCounts.edges_by_kind.${kind} must be a number.`);
  }
}

/** Runtime boundary validation for the custom Build Manifest 11 JSON interface. */
export function validateBuildManifest(value: unknown): asserts value is BuildManifest {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Build Manifest 11 must be an object.');
  const manifest = value as Partial<BuildManifest>;
  if (manifest.schemaVersion !== 11) throw new Error('Build Manifest requires schemaVersion 11.');
  if (manifest.generator?.name !== 'concorde-docsite' || typeof manifest.generator.version !== 'string' ||
      typeof manifest.generator.docusaurusVersion !== 'string') throw new Error('Build Manifest generator identity is incomplete.');
  const collectionIds = manifest.collections?.map((collection) => collection.id);
  if (JSON.stringify(collectionIds) !== JSON.stringify(['architecture', 'features'])) {
    throw new Error('Build Manifest collections must be architecture and features in canonical order.');
  }
  if (!Array.isArray(manifest.pages)) throw new Error('Build Manifest pages must be an array.');
  const pageKinds = new Set(['module-architecture', 'feature-design']);
  for (const page of manifest.pages) {
    if (!pageKinds.has(page.kind)) throw new Error(`Build Manifest page kind "${page.kind}" is unsupported.`);
    if (!isRelativePath(page.sourcePath)) throw new Error(`Build Manifest sourcePath "${page.sourcePath}" must be project-relative.`);
    if (!page.sourcePath.startsWith('specs/')) throw new Error(`Build Manifest sourcePath "${page.sourcePath}" must be a specification source.`);
    if (!/^[a-f0-9]{64}$/.test(page.sourceSha256)) throw new Error(`${page.sourcePath}: sourceSha256 must be lowercase SHA-256.`);
    if (!page.route.startsWith('/')) throw new Error(`${page.sourcePath}: route must be root-relative.`);
    if (page.kind === 'module-architecture') {
      if (!page.moduleId || !Array.isArray(page.architectureDiagrams)) throw new Error(`${page.sourcePath}: module page metadata is incomplete.`);
      for (const diagram of page.architectureDiagrams) if (!isRelativePath(diagram.source)) {
        throw new Error(`${page.sourcePath}: diagram source must be project-relative.`);
      }
    }
    if (page.kind === 'feature-design' && (!page.featureId || !page.moduleId || !page.moduleRoute ||
        typeof page.status !== 'string' || !Array.isArray(page.relatedFeatures))) {
      throw new Error(`${page.sourcePath}: feature page metadata is incomplete.`);
    }
  }
  assertSorted(manifest.pages.map((page) => page.sourcePath), 'Build Manifest pages');
  if (!Array.isArray(manifest.excludedSources) || manifest.excludedSources.some((source) => !isRelativePath(source.sourcePath))) {
    throw new Error('Build Manifest excluded source paths must be project-relative.');
  }
  assertSorted(manifest.excludedSources.map((source) => source.sourcePath), 'Build Manifest excludedSources');
  if (!Array.isArray(manifest.routeInventory)) throw new Error('Build Manifest routeInventory must be an array.');
  assertSorted(manifest.routeInventory, 'Build Manifest routeInventory');
  if (manifest.pages.some((page) => !manifest.routeInventory!.includes(page.route))) {
    throw new Error('Build Manifest routeInventory must include every page route.');
  }
  if (manifest.featureGraph !== 'feature-graph.json') throw new Error('Build Manifest featureGraph must be "feature-graph.json".');
  assertFeatureGraphCounts(manifest.featureGraphCounts);
  if (manifest.validation?.status !== 'passed' || !manifest.validation.checks?.every((check) => check.status === 'passed')) {
    throw new Error('Build Manifest validation checks must all pass.');
  }
}

export function createManifest(registry: ContentRegistry, routeInventory?: string[]): BuildManifest {
  const pages = registry.documents.map(pageFromDocument).sort((left, right) => left.sourcePath < right.sourcePath ? -1 : left.sourcePath > right.sourcePath ? 1 : 0);
  const graph = deriveFeatureGraph(registry, GENERATOR_VERSION);
  const manifest: BuildManifest = {
    schemaVersion: 11,
    generator: {name: 'concorde-docsite', version: GENERATOR_VERSION, docusaurusVersion: '3.10.2'},
    collections: registry.collections.map(({id, sourceBase, routeBase, include}) => ({id, sourceBase, routeBase, include})),
    pages,
    excludedSources: [...registry.excludedSources].sort((left, right) => left.sourcePath < right.sourcePath ? -1 : left.sourcePath > right.sourcePath ? 1 : 0),
    routeInventory: [...new Set(routeInventory ?? ['/', ...pages.map((page) => page.route)])].sort(),
    featureGraph: 'feature-graph.json',
    featureGraphCounts: graph.counts,
    validation: {
      status: 'passed',
      checks: [
        {name: 'profile-7-sources', status: 'passed'},
        {name: 'identity-relations-and-routes', status: 'passed'},
        {name: 'rendered-route-inventory', status: 'passed'},
      ],
    },
  };
  validateBuildManifest(manifest);
  return manifest;
}
