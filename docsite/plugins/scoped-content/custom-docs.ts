import {existsSync, realpathSync, statSync} from 'node:fs';
import {isAbsolute, relative, resolve} from 'node:path';
import type {PluginConfig} from '@docusaurus/types';
import type {NavbarItem} from '@docusaurus/theme-common';
import type {SiteIdentity} from './site-identity';
import type {ScopedRegistry} from './model';

/** Shape of the optional project-authored custom-docs/index.ts extension. */
export interface CustomDocsExtension {
  plugins?: PluginConfig[];
  navbarItems?: NavbarItem[];
}

export function customDocsConfiguration(siteDir: string, identity: SiteIdentity, registry: ScopedRegistry) {
  const collections = identity.customDocs ?? [];
  for (const collection of collections) {
    const directory = realpathSync(resolve(siteDir, collection.path));
    if (!statSync(directory).isDirectory()) throw new Error(`customDocs ${collection.id}.path must name a directory.`);
    if (collection.sidebarPath && !statSync(resolve(siteDir, collection.sidebarPath)).isFile()) {
      throw new Error(`customDocs ${collection.id}.sidebarPath must name a file.`);
    }
    for (const page of registry.pages) {
      const path = relative(directory, realpathSync(resolve(registry.projectRoot, page.sourcePath)));
      if (path === '' || (path !== '..' && !path.startsWith('../') && !isAbsolute(path))) {
        throw new Error(`customDocs ${collection.id} includes registered Spec ${page.sourcePath}; keep custom docs separate from Module Specs.`);
      }
    }
  }
  const extensionPath = resolve(siteDir, 'custom-docs/index.ts');
  const extension: CustomDocsExtension = existsSync(extensionPath) ? require(extensionPath).default : {};
  if (!extension || typeof extension !== 'object' || Array.isArray(extension)) throw new Error('custom-docs/index.ts must export a CustomDocsExtension object.');
  for (const field of ['plugins', 'navbarItems'] as const) {
    if (extension[field] !== undefined && !Array.isArray(extension[field])) {
      throw new Error(`custom-docs/index.ts ${field} must be an array.`);
    }
  }
  return {
    plugins: [
      ...collections.map(collection => ['@docusaurus/plugin-content-docs', {
        id: collection.id, path: collection.path, routeBasePath: collection.routeBasePath,
        sidebarPath: collection.sidebarPath ? resolve(siteDir, collection.sidebarPath) : undefined,
        include: ['**/*.md', '**/*.mdx'], numberPrefixParser: false,
        showLastUpdateAuthor: false, showLastUpdateTime: false,
      }] as PluginConfig),
      ...(extension.plugins ?? []),
    ],
    navbarItems: [
      ...collections.map(collection => ({to: '/' + collection.routeBasePath, label: collection.label, position: 'left' as const})),
      ...(extension.navbarItems ?? []),
    ],
    docsRouteBasePath: collections.map(collection => '/' + collection.routeBasePath),
    docsDir: collections.map(collection => collection.path),
  };
}
