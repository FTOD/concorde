import {copyFile, mkdir, rm, writeFile} from 'node:fs/promises';
import {dirname, relative, resolve} from 'node:path';

import matter from 'gray-matter';

import {buildRegistry} from '../plugins/concorde-content/registry';
import type {CollectionId, ContentRegistry, SourceDocument} from '../plugins/concorde-content/types';
import {assertValidRegistry} from '../plugins/concorde-content/validation';

const siteDir = resolve(__dirname, '..');
const projectRoot = resolve(siteDir, '..');
export const generatedContentRoot = resolve(siteDir, '.generated/content');

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

export async function materializeContent(providedRegistry?: ContentRegistry): Promise<void> {
  const registry = providedRegistry ?? assertValidRegistry(await buildRegistry(projectRoot));
  await rm(generatedContentRoot, {recursive: true, force: true});

  for (const document of registry.documents) {
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
    } else {
      await copyFile(document.realPath, destination);
    }
  }
}

if (require.main === module) {
  void materializeContent().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
}
