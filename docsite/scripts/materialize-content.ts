import {copyFile, lstat, mkdir, rm, writeFile} from 'node:fs/promises';
import {dirname, relative, resolve, sep} from 'node:path';

import matter from 'gray-matter';

import {buildRegistry} from '../plugins/concorde-content/registry';
import type {
  ContentRegistry, FeatureDesign, ModuleArchitecture, ProjectDocument, SourceDocument,
} from '../plugins/concorde-content/types';
import {assertValidRegistry} from '../plugins/concorde-content/validation';

const siteDir = resolve(__dirname, '..');
const projectRoot = resolve(siteDir, '..');
export const generatedContentRoot = resolve(siteDir, '.generated/content');
export const generatedStaticRoot = resolve(siteDir, '.generated/static');
export const generatedFeatureSidebarPath = resolve(siteDir, '.generated/features-sidebar.json');
export const generatedArchitectureSidebarPath = resolve(siteDir, '.generated/architecture-sidebar.json');

function rendererFrontMatter(document: SourceDocument): Record<string, unknown> {
  const {id: _canonicalId, slug: _canonicalSlug, sidebar_label: _label, sidebar_position: _position, ...rest} = document.frontMatter;
  return rest;
}

/** Stage one direct feature source as one flat renderer file at its stable feature-ID route. */
export function stageFeatureDocument(document: FeatureDesign): string {
  return matter.stringify(document.content, {
    ...rendererFrontMatter(document), slug: document.route.slice('/features'.length),
    sidebar_label: document.sidebarLabel ?? document.title,
  });
}

/** Stage architecture.md as the module's stable module-ID landing page. */
export function stageArchitectureDocument(document: ModuleArchitecture): string {
  return matter.stringify(document.content, {
    ...rendererFrontMatter(document), slug: document.route.slice('/architecture'.length),
    sidebar_label: document.sidebarLabel ?? document.title,
  });
}

/** Add renderer-only root-route metadata while preserving the maintained README body. */
export function stageHomepageDocument(document: ProjectDocument): string {
  return matter.stringify(document.content, {
    ...rendererFrontMatter(document), slug: '/', sidebar_label: document.sidebarLabel ?? document.title,
  });
}

export type SidebarItem = {
  type: 'category' | 'doc';
  label: string;
  id?: string;
  link?: {type: 'doc'; id: string};
  items?: SidebarItem[];
  collapsed?: boolean;
  className?: string;
};

/** Sidebar class that styles module categories as bold, larger group headings. */
export const moduleSidebarClassName = 'sidebar-module';

function publicationModel(registry: ContentRegistry) {
  const modules = registry.documents.filter((document): document is ModuleArchitecture => document.contentKind === 'module-architecture');
  const features = registry.documents.filter((document): document is FeatureDesign => document.contentKind === 'feature-design');
  return {
    modules,
    features,
    modulesById: new Map(modules.map((module) => [module.moduleId, module])),
    featuresById: new Map(features.map((feature) => [feature.featureId, feature])),
  };
}

/** Build Architecture navigation from the declared recursive module hierarchy. */
export function architectureSidebarItems(registry: ContentRegistry): SidebarItem[] {
  const {modules, modulesById} = publicationModel(registry);
  const included = new Set<string>();
  const moduleItem = (moduleId: string, root = false): SidebarItem => {
    const module = modulesById.get(moduleId);
    if (!module?.stagedPath) throw new Error(`Architecture sidebar cannot resolve module "${moduleId}".`);
    if (included.has(moduleId)) throw new Error(`Architecture sidebar includes module "${moduleId}" more than once.`);
    included.add(moduleId);
    return {
      type: 'category', label: module.sidebarLabel ?? module.title, className: moduleSidebarClassName,
      link: {type: 'doc', id: module.stagedPath.replace(/\.md$/, '')},
      items: module.moduleIds.map((childId) => moduleItem(childId)), collapsed: !root,
    };
  };
  const result = modules.filter((module) => !module.parentId).map((module) => moduleItem(module.moduleId, true));
  const missing = modules.map((module) => module.moduleId).filter((id) => !included.has(id));
  if (missing.length) throw new Error(`Architecture sidebar omits modules: ${missing.join(', ')}.`);
  return result;
}

/** Build Features navigation from module containment; features themselves remain flat doc items. */
export function featureSidebarItems(registry: ContentRegistry): SidebarItem[] {
  const {modules, features, modulesById, featuresById} = publicationModel(registry);
  const includedModules = new Set<string>();
  const includedFeatures = new Set<string>();
  const featureItem = (featureId: string): SidebarItem => {
    const feature = featuresById.get(featureId);
    if (!feature?.stagedPath) throw new Error(`Feature sidebar cannot resolve registered feature "${featureId}".`);
    if (includedFeatures.has(featureId)) throw new Error(`Feature sidebar includes "${featureId}" more than once.`);
    includedFeatures.add(featureId);
    return {type: 'doc', id: feature.stagedPath.replace(/\.md$/, ''), label: feature.title};
  };
  const moduleItem = (moduleId: string, root = false): SidebarItem => {
    const module = modulesById.get(moduleId);
    if (!module) throw new Error(`Feature sidebar cannot resolve module "${moduleId}".`);
    if (includedModules.has(moduleId)) throw new Error(`Feature sidebar includes module "${moduleId}" more than once.`);
    includedModules.add(moduleId);
    return {
      type: 'category', label: module.sidebarLabel ?? module.title, className: moduleSidebarClassName,
      items: [
        ...module.featureIds.map(featureItem),
        ...module.moduleIds.map((childId) => moduleItem(childId)),
      ],
      collapsed: !root,
    };
  };
  const result = modules.filter((module) => !module.parentId).map((module) => moduleItem(module.moduleId, true));
  const missingModules = modules.map((module) => module.moduleId).filter((id) => !includedModules.has(id));
  const missingFeatures = features.map((feature) => feature.featureId).filter((id) => !includedFeatures.has(id));
  if (missingModules.length || missingFeatures.length) {
    throw new Error(`Feature sidebar omits registered sources: ${[...missingModules, ...missingFeatures].join(', ')}.`);
  }
  return result;
}

export async function materializeContent(providedRegistry?: ContentRegistry): Promise<void> {
  const registry = providedRegistry ?? assertValidRegistry(await buildRegistry(projectRoot));
  await Promise.all([
    rm(generatedContentRoot, {recursive: true, force: true}),
    rm(generatedStaticRoot, {recursive: true, force: true}),
  ]);
  // Each collection backs a Docusaurus content-docs plugin instance that requires its path to exist
  // on disk even when the project currently registers no document in that collection (for example a
  // freshly scaffolded project with zero features).
  await Promise.all(['home', 'architecture', 'features'].map((collectionDirectory) =>
    mkdir(resolve(generatedContentRoot, collectionDirectory), {recursive: true})));

  for (const document of registry.documents) {
    if (document.collectionId === 'docs') continue;
    const collectionDirectory = document.collectionId === 'home' ? 'home' : document.collectionId;
    const destination = resolve(generatedContentRoot, collectionDirectory, document.stagedPath ?? 'README.md');
    await mkdir(dirname(destination), {recursive: true});
    const staged = document.collectionId === 'home'
      ? stageHomepageDocument(document as ProjectDocument)
      : document.contentKind === 'module-architecture'
        ? stageArchitectureDocument(document as ModuleArchitecture)
        : stageFeatureDocument(document as FeatureDesign);
    await writeFile(destination, staged, 'utf8');
  }
  const copiedAssets = new Set<string>();
  for (const link of registry.documents.flatMap((document) => document.links).filter((link) => link.kind === 'asset')) {
    if (!link.targetSourcePath || copiedAssets.has(link.targetSourcePath)) continue;
    const source = resolve(registry.projectRoot, link.targetSourcePath);
    const fromRoot = relative(resolve(registry.projectRoot), source);
    if (fromRoot === '..' || fromRoot.startsWith(`..${sep}`)) continue;
    try {
      if (!(await lstat(source)).isFile()) continue;
    } catch {
      continue;
    }
    const destination = resolve(generatedStaticRoot, link.targetSourcePath);
    await mkdir(dirname(destination), {recursive: true});
    await copyFile(source, destination);
    copiedAssets.add(link.targetSourcePath);
  }
  await Promise.all([
    writeFile(generatedArchitectureSidebarPath, `${JSON.stringify(architectureSidebarItems(registry), null, 2)}\n`, 'utf8'),
    writeFile(generatedFeatureSidebarPath, `${JSON.stringify(featureSidebarItems(registry), null, 2)}\n`, 'utf8'),
  ]);
}

if (require.main === module) {
  void materializeContent().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
}
