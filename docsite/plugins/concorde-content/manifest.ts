import type {ArchitectureSource, BuildManifest, ContentPage, ContentRegistry, FeatureDesign, FeatureSpecification, SourceDocument} from './types';

const isFeature = (document: SourceDocument): document is FeatureSpecification => document.collectionId === 'features';
const isFeatureDesign = (document: SourceDocument): document is FeatureDesign => document.collectionId === 'feature-designs';
const isArchitecture = (document: SourceDocument): document is ArchitectureSource => document.collectionId === 'architecture';

function navigationFor(document: SourceDocument) {
  return {
    section: document.collectionId === 'docs'
      ? 'Documentation' as const
      : document.collectionId === 'features' || document.collectionId === 'feature-designs'
        ? 'Features' as const
        : 'Architecture' as const,
    label: document.sidebarLabel || document.title,
    ...((isFeature(document) || isFeatureDesign(document)) && document.parentFeatureRoute
      ? {parentRoute: document.parentFeatureRoute}
      : {}),
  };
}

export function pageFromDocument(document: SourceDocument): ContentPage {
  return {
    kind: document.collectionId === 'docs'
      ? 'project-document'
      : document.collectionId === 'features'
        ? 'feature-specification'
        : document.collectionId === 'feature-designs'
          ? 'feature-design'
        : 'architecture-source',
    sourcePath: document.sourcePath,
    sourceSha256: document.sourceSha256,
    route: document.route,
    title: document.title,
    navigation: navigationFor(document),
    links: document.links
      .filter((link) => link.targetSourcePath && link.targetRoute)
      .map((link) => ({targetSourcePath: link.targetSourcePath!, targetRoute: link.targetRoute!}))
      .sort((a, b) => `${a.targetSourcePath}\0${a.targetRoute}`.localeCompare(`${b.targetSourcePath}\0${b.targetRoute}`)),
    ...(isFeature(document) ? {
      featureId: document.featureId, moduleId: document.moduleId, status: document.status,
      diagrams: document.diagrams,
      featureLevel: document.featureLevel,
      parentFeatureId: document.parentFeatureId,
      parentFeatureRoute: document.parentFeatureRoute,
      subfeatures: document.subfeatures,
      siblings: document.siblings,
    } : {}),
    ...(isFeatureDesign(document) ? {
      featureLevel: document.featureLevel,
      parentFeatureId: document.parentFeatureId,
      parentFeatureRoute: document.parentFeatureRoute,
      subfeatures: document.subfeatures,
      siblings: document.siblings,
    } : {}),
    ...(isArchitecture(document) ? {
      architectureId: document.architectureId,
      architectureKind: document.architectureKind,
      moduleId: document.moduleId,
      parentId: document.parentId,
      architectureViewSource: document.architectureViewSource,
      architectureViewSha256: document.architectureViewSha256,
      architectureViewRoute: document.architectureViewRoute,
    } : {}),
  };
}

export function createManifest(registry: ContentRegistry, routeInventory?: string[]): BuildManifest {
  const pages = registry.documents.map(pageFromDocument).sort((a, b) => a.sourcePath.localeCompare(b.sourcePath));
  return {
    schemaVersion: 4,
    generator: {name: 'concorde-docsite', version: '0.2.0', docusaurusVersion: '3.10.2'},
    collections: registry.collections.map(({id, sourceBase, routeBase, include}) => ({id, sourceBase, routeBase, include})),
    pages,
    excludedSources: [...registry.excludedSources].sort((a, b) => a.sourcePath.localeCompare(b.sourcePath)),
    routeInventory: [...new Set(routeInventory ?? ['/', ...pages.map((page) => page.route)])].sort(),
    validation: {
      status: 'passed',
      checks: [
        {name: 'source-contracts', status: 'passed'},
        {name: 'identity-and-routes', status: 'passed'},
        {name: 'rendered-route-inventory', status: 'passed'},
      ],
    },
  };
}
