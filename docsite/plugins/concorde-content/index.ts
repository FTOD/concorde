import {mkdir, writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';

import type {LoadContext, Plugin} from '@docusaurus/types';

import {createManifest, pageFromDocument} from './manifest';
import {buildRegistry} from './registry';
import type {ConcordeContentOptions, ContentRegistry} from './types';
import {assertValidRegistry} from './validation';

const normalizeRoute = (route: string) => route === '/' ? route : route.replace(/\/$/, '');

export default function concordeContentPlugin(
  context: LoadContext,
  rawOptions: unknown,
): Plugin<ContentRegistry> {
  const options = (rawOptions ?? {}) as ConcordeContentOptions;
  const projectRoot = resolve(options.projectRoot ?? resolve(context.siteDir, '..'));
  let loadedRegistry: ContentRegistry | undefined;
  return {
    name: 'concorde-content',
    async loadContent() {
      loadedRegistry = assertValidRegistry(await buildRegistry(projectRoot));
      return loadedRegistry;
    },
    async contentLoaded({content, actions}) {
      actions.setGlobalData({
        pages: content.documents.map(pageFromDocument),
        counts: {
          architecture: content.documents.filter((document) => document.collectionId === 'architecture').length,
          docs: content.documents.filter((document) => document.collectionId === 'docs').length,
          features: content.documents.filter((document) => document.collectionId === 'features').length,
          designs: content.documents.filter((document) => document.collectionId === 'feature-designs').length,
        },
      });
    },
    getPathsToWatch() {
      return [
        resolve(projectRoot, 'specs/**/*.md'), resolve(projectRoot, 'specs/**/architecture.json'),
        resolve(projectRoot, 'specs/**/features/*/diagrams/*.json'),
        resolve(projectRoot, 'specs/**/features/*/subfeatures/*/diagrams/*.json'),
        resolve(projectRoot, 'docs/**/*.md'),
      ];
    },
    async postBuild({outDir, routesPaths}) {
      if (!loadedRegistry) throw new Error('Concorde content registry was not loaded before postBuild.');
      const rendered = new Set(routesPaths.map(normalizeRoute));
      const missing = loadedRegistry.documents
        .map((document) => document.route)
        .filter((route) => !rendered.has(normalizeRoute(route)));
      if (missing.length) throw new Error(`Rendered route verification failed: ${missing.join(', ')}`);
      const manifest = createManifest(loadedRegistry, routesPaths);
      await mkdir(outDir, {recursive: true});
      await writeFile(resolve(outDir, 'build-manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
    },
  };
}

export {createManifest} from './manifest';
export {buildRegistry} from './registry';
export {assertValidRegistry, formatFinding, validateRegistry} from './validation';
export type * from './types';
