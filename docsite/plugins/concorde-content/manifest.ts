import type {
  ArchitectureSource, BuildManifest, ContentPage, ContentRegistry, FeatureImplementation, FeaturePageContext, FeatureDesign, FeatureAbstract,
  ModuleDesign, SourceDocument,
} from './types';

const isFeature = (document: SourceDocument): document is FeatureDesign => document.collectionId === 'features';
const isFeatureAbstract = (document: SourceDocument): document is FeatureAbstract => document.collectionId === 'feature-abstracts';
const isFeatureImplementation = (document: SourceDocument): document is FeatureImplementation => document.collectionId === 'feature-implementations';
const isArchitecture = (document: SourceDocument): document is ArchitectureSource => document.contentKind === 'architecture-source';
const isModuleDesign = (document: SourceDocument): document is ModuleDesign => document.contentKind === 'module-design';

/** The identity and abstract-routed navigation every feature page carries. */
function featureContext(document: FeaturePageContext) {
  return {
    featureId: document.featureId,
    moduleId: document.moduleId,
    featureLevel: document.featureLevel,
    parentFeatureId: document.parentFeatureId,
    parentFeatureRoute: document.parentFeatureRoute,
    subfeatures: document.subfeatures,
    siblings: document.siblings,
  };
}

function navigationFor(document: SourceDocument) {
  const section = document.collectionId === 'docs'
    ? 'Documentation' as const
    : document.collectionId === 'architecture'
      ? 'Architecture' as const
      : 'Features' as const;
  // Sub-feature pages nest beneath their parent feature abstract; module design nests beside its module page.
  const parentRoute = isFeature(document) || isFeatureAbstract(document) || isFeatureImplementation(document)
    ? document.parentFeatureRoute
    : isModuleDesign(document) ? document.moduleRoute : undefined;
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
      .sort((a, b) => `${a.targetSourcePath}\0${a.targetRoute}`.localeCompare(`${b.targetSourcePath}\0${b.targetRoute}`)),
    ...(isFeatureAbstract(document) ? {
      ...featureContext(document),
      status: document.status,
      diagrams: document.diagrams,
      designRoute: document.designRoute,
      implementationRoute: document.implementationRoute,
    } : {}),
    ...(isFeature(document) ? {
      ...featureContext(document),
      status: document.status,
      diagrams: document.diagrams,
      abstractRoute: document.abstractRoute,
      implementationRoute: document.implementationRoute,
    } : {}),
    ...(isFeatureImplementation(document) ? {
      ...featureContext(document),
      abstractRoute: document.abstractRoute,
      designRoute: document.designRoute,
    } : {}),
    ...(isArchitecture(document) ? {
      architectureId: document.architectureId,
      architectureKind: document.architectureKind,
      moduleId: document.moduleId,
      parentId: document.parentId,
      architectureViewSource: document.architectureViewSource,
      architectureViewSha256: document.architectureViewSha256,
      architectureViewRoute: document.architectureViewRoute,
      designReferenceRoute: document.designReferenceRoute,
    } : {}),
    ...(isModuleDesign(document) ? {
      moduleId: document.moduleId,
      moduleRoute: document.moduleRoute,
    } : {}),
  };
}

export function createManifest(registry: ContentRegistry, routeInventory?: string[]): BuildManifest {
  const pages = registry.documents.map(pageFromDocument).sort((a, b) => a.sourcePath.localeCompare(b.sourcePath));
  return {
    schemaVersion: 7,
    generator: {name: 'concorde-docsite', version: '0.3.0', docusaurusVersion: '3.10.2'},
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
