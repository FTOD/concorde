import {copyFile, mkdir, rm, writeFile} from 'node:fs/promises';
import {dirname, posix, relative, resolve} from 'node:path';

import matter from 'gray-matter';

import {buildRegistry} from '../plugins/concorde-content/registry';
import type {
  ArchitectureSource, CollectionId, ContentRegistry, FeatureDesign, ProjectDocument, SourceDocument,
} from '../plugins/concorde-content/types';
import {assertValidRegistry} from '../plugins/concorde-content/validation';

const siteDir = resolve(__dirname, '..');
const projectRoot = resolve(siteDir, '..');
export const generatedContentRoot = resolve(siteDir, '.generated/content');
export const generatedFeatureSidebarPath = resolve(siteDir, '.generated/features-sidebar.json');

/** The three pages of a feature root are staged together beneath the Features root. */
const featureCollections = new Set<CollectionId>(['feature-abstracts', 'features', 'feature-implementations']);
/** Sidebar order inside one feature root: abstract, design, then implementation. */
const featureSidebarPositions = {'feature-abstract': 1, 'feature-design': 2, 'feature-implementation': 3} as const;

/**
 * A feature page is staged with the route the registry assigned it, so Docusaurus renders the abstract at
 * `/features/<root>` and the specification and design reference one segment below it instead of deriving
 * routes from the specification's front matter id. The staged copy is a renderer projection only.
 */
export function stageFeatureDocument(document: SourceDocument): string {
  const contentKind = document.contentKind as keyof typeof featureSidebarPositions;
  return matter.stringify(document.content, {
    ...document.frontMatter,
    slug: document.route.slice('/features'.length),
    sidebar_label: document.sidebarLabel ?? document.title,
    sidebar_position: featureSidebarPositions[contentKind],
  });
}

/** Add renderer-only route metadata while preserving the maintained README body and front matter. */
export function stageHomepageDocument(document: ProjectDocument): string {
  return matter.stringify(document.content, {
    ...document.frontMatter,
    slug: '/',
    sidebar_label: document.sidebarLabel ?? document.title,
  });
}

export function featureCategoryPath(document: FeatureDesign): string {
  if (!document.stagedPath) throw new Error(`Feature "${document.featureId}" has no semantic staged path.`);
  return posix.join(posix.dirname(document.stagedPath), '_category_.json');
}

export function featureCategoryMetadata(document: FeatureDesign): {
  label: string;
  link: {type: 'doc'; id: string};
} {
  if (!document.stagedPath) throw new Error(`Feature "${document.featureId}" has no semantic staged path.`);
  const directory = posix.dirname(document.stagedPath);
  return {label: document.title, link: {type: 'doc', id: posix.join(directory, 'abstract')}};
}

type FeatureSidebarItem = {
  type: 'category' | 'doc';
  label: string;
  id?: string;
  link?: {type: 'doc'; id: string};
  items?: FeatureSidebarItem[];
  collapsed?: boolean;
};

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
}

/** Build Features navigation from module containment while keeping stable identity-derived feature routes. */
export function featureSidebarItems(registry: ContentRegistry): FeatureSidebarItem[] {
  const modules = registry.documents.filter((document): document is ArchitectureSource =>
    document.contentKind === 'architecture-source' && (document as ArchitectureSource).architectureKind === 'module');
  const features = registry.documents.filter((document): document is FeatureDesign => document.collectionId === 'features');
  const modulesById = new Map(modules.map((module) => [module.architectureId, module]));
  const featuresById = new Map(features.map((feature) => [feature.featureId, feature]));
  const includedModules = new Set<string>();
  const includedFeatures = new Set<string>();

  const featureItem = (featureId: string): FeatureSidebarItem => {
    const feature = featuresById.get(featureId);
    if (!feature?.stagedPath) throw new Error(`Feature sidebar cannot resolve registered feature "${featureId}".`);
    if (includedFeatures.has(featureId)) throw new Error(`Feature sidebar includes "${featureId}" more than once.`);
    includedFeatures.add(featureId);
    const directory = posix.dirname(feature.stagedPath);
    return {
      type: 'category', label: feature.title, link: {type: 'doc', id: posix.join(directory, 'abstract')},
      items: [
        {type: 'doc', id: posix.join(directory, feature.featureId), label: 'Design'},
        {type: 'doc', id: posix.join(directory, 'implementation'), label: 'Implementation'},
        ...feature.subfeatureIds.map(featureItem),
      ],
      collapsed: true,
    };
  };

  const moduleItem = (moduleId: string, root = false): FeatureSidebarItem => {
    const module = modulesById.get(moduleId);
    if (!module) throw new Error(`Feature sidebar cannot resolve registered module "${moduleId}".`);
    if (includedModules.has(moduleId)) throw new Error(`Feature sidebar includes module "${moduleId}" more than once.`);
    includedModules.add(moduleId);
    return {
      type: 'category', label: module.title,
      items: [
        ...stringList(module.frontMatter.features).map(featureItem),
        ...stringList(module.frontMatter.children).map((childId) => moduleItem(childId)),
      ],
      collapsed: !root,
    };
  };

  const result = modules.filter((module) => module.parentId == null).map((module) => moduleItem(module.architectureId, true));
  const missingModules = modules.map((module) => module.architectureId).filter((id) => !includedModules.has(id));
  const missingFeatures = features.map((feature) => feature.featureId).filter((id) => !includedFeatures.has(id));
  if (missingModules.length || missingFeatures.length) {
    throw new Error(`Feature sidebar omits registered sources: ${[...missingModules, ...missingFeatures].join(', ')}.`);
  }
  return result;
}

export async function materializeContent(providedRegistry?: ContentRegistry): Promise<void> {
  const registry = providedRegistry ?? assertValidRegistry(await buildRegistry(projectRoot));
  await rm(generatedContentRoot, {recursive: true, force: true});

  for (const document of registry.documents) {
    if (document.collectionId === 'home') {
      const destination = resolve(generatedContentRoot, 'home', document.stagedPath ?? 'README.md');
      await mkdir(dirname(destination), {recursive: true});
      await writeFile(destination, stageHomepageDocument(document as ProjectDocument), 'utf8');
      continue;
    }
    const isFeaturePage = featureCollections.has(document.collectionId);
    if (document.collectionId !== 'architecture' && !isFeaturePage) continue;
    // Pages are staged at their projected path (the `architecture/` grouping segment dropped), which is the
    // path Docusaurus derives their sidebar position and, for architecture pages, their route from.
    const relativeSpecPath = document.stagedPath ?? relative(resolve(projectRoot, 'specs'), resolve(projectRoot, document.sourcePath));
    // Abstracts, designs, and implementations are staged beside each other under the Features root; module
    // design references belong to the architecture collection and land beside their module.md.
    const destination = resolve(generatedContentRoot, isFeaturePage ? 'features' : document.collectionId, relativeSpecPath);
    await mkdir(dirname(destination), {recursive: true});
    if (isFeaturePage) {
      await writeFile(destination, stageFeatureDocument(document), 'utf8');
      if (document.collectionId === 'features') {
        const feature = document as FeatureDesign;
        const categoryDestination = resolve(generatedContentRoot, 'features', featureCategoryPath(feature));
        await mkdir(dirname(categoryDestination), {recursive: true});
        await writeFile(categoryDestination, `${JSON.stringify(featureCategoryMetadata(feature), null, 2)}\n`, 'utf8');
      }
    } else {
      await copyFile(document.realPath, destination);
    }
  }
  await writeFile(generatedFeatureSidebarPath, `${JSON.stringify(featureSidebarItems(registry), null, 2)}\n`, 'utf8');
}

if (require.main === module) {
  void materializeContent().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
}
