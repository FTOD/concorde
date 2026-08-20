import {createHash} from 'node:crypto';
import {realpath, readFile} from 'node:fs/promises';
import {dirname, posix, relative, resolve} from 'node:path';

import fg from 'fast-glob';
import matter from 'gray-matter';

import type {
  ArchitectureKind, ArchitectureSource, ContentRegistry, ExcludedSource, FeatureSpecification, ProjectDocument, SourceCollection,
  SourceDocument, ValidationFinding,
} from './types';
import {populateLinks} from './links';

export const collections: SourceCollection[] = [
  {
    id: 'architecture', sourceBase: 'specs', routeBase: '/architecture',
    include: ['**/module.md', '**/contracts/**/contract.md'], contentKind: 'architecture-source',
  },
  {id: 'docs', sourceBase: 'docs', routeBase: '/docs', include: ['**/*.md'], contentKind: 'project-document'},
  {id: 'features', sourceBase: 'specs', routeBase: '/features', include: ['**/spec.md'], contentKind: 'feature-specification'},
];

const posixPath = (value: string) => value.split('\\').join('/');
const sha256 = (value: string) => createHash('sha256').update(value).digest('hex');

function headingTitle(content: string): string {
  return content.match(/^#\s+(.+?)\s*$/m)?.[1]?.replace(/^Feature Specification:\s*/i, '').trim() ?? '';
}

function routeFor(collection: SourceCollection, relativePath: string, slug?: unknown, sourceId?: unknown): string {
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
  const route = routeFor(collection, posixPath(relativePath), parsed.data.slug, parsed.data.id);
  const base = {
    collectionId: collection.id,
    sourcePath,
    realPath: resolvedPath,
    title,
    sourceSha256: sha256(source),
    frontMatter: parsed.data,
    content: parsed.content,
    links: [],
    state: 'parsed' as const,
    route,
    sidebarLabel: typeof parsed.data.sidebar_label === 'string' ? parsed.data.sidebar_label : title,
    sidebarPosition: typeof parsed.data.sidebar_position === 'number' ? parsed.data.sidebar_position : undefined,
    slug: typeof parsed.data.slug === 'string' ? parsed.data.slug : undefined,
  };
  if (collection.id === 'docs') return base as ProjectDocument;
  if (collection.id === 'architecture') {
    const architectureKind = parsed.data.kind as ArchitectureKind;
    const view = typeof parsed.data.view === 'string'
      ? parsed.data.view.trim()
      : typeof parsed.data.architecture_view === 'string'
        ? parsed.data.architecture_view.trim()
        : undefined;
    let architectureViewSource: string | undefined;
    let architectureViewSha256: string | undefined;
    let architectureViewRoute: string | undefined;
    if (view) {
      architectureViewSource = posix.normalize(posixPath(view));
      const viewPath = resolve(projectRoot, architectureViewSource);
      try {
        const viewText = await readFile(viewPath, 'utf8');
        const viewDocument = JSON.parse(viewText) as {meta?: {output?: unknown}};
        architectureViewSha256 = sha256(viewText);
        if (typeof viewDocument.meta?.output === 'string') {
          const outputPath = resolve(dirname(viewPath), viewDocument.meta.output);
          const generatedRelative = posixPath(relative(resolve(projectRoot, 'generated'), outputPath));
          if (generatedRelative !== '..' && !generatedRelative.startsWith('../')) {
            await readFile(outputPath, 'utf8');
            architectureViewRoute = `/${generatedRelative}`;
          }
        }
      } catch (error) {
        // The deterministic validator emits the actionable finding after discovery.
      }
    }
    return {
      ...base,
      collectionId: 'architecture',
      architectureId: typeof parsed.data.id === 'string' ? parsed.data.id.trim() : '',
      architectureKind,
      moduleId: typeof parsed.data.module === 'string' ? parsed.data.module.trim() : undefined,
      parentId: typeof parsed.data.parent === 'string' ? parsed.data.parent.trim() : undefined,
      architectureViewSource,
      architectureViewSha256,
      architectureViewRoute,
    } as ArchitectureSource;
  }
  return {
    ...base,
    collectionId: 'features',
    featureId: typeof parsed.data.id === 'string' ? parsed.data.id.trim() : '',
    kind: parsed.data.kind === 'feature' ? 'feature' : (parsed.data.kind as 'feature'),
    moduleId: typeof parsed.data.module === 'string' ? parsed.data.module.trim() : '',
    status: parsed.content.match(/^\*\*Status\*\*:\s*(.+?)\s*$/m)?.[1]?.trim() ?? '',
    featureDirectory: posix.dirname(sourcePath),
  } as FeatureSpecification;
}

export async function buildRegistry(projectRoot: string): Promise<ContentRegistry> {
  const root = resolve(projectRoot);
  const documents: SourceDocument[] = [];
  const excludedSources: ExcludedSource[] = [];
  const findings: ValidationFinding[] = [];

  for (const collection of collections) {
    const basePath = resolve(root, collection.sourceBase);
    const paths = await fg(collection.include, {
      cwd: basePath, onlyFiles: true, unique: true, followSymbolicLinks: false,
    });
    for (const path of paths.sort()) {
      try {
        documents.push(await parseDocument(root, collection, path));
      } catch (error) {
        findings.push({
          ruleId: 'content.read.failed', severity: 'error',
          sourcePath: posix.join(collection.sourceBase, posixPath(path)),
          message: error instanceof Error ? error.message : 'The source could not be read.',
          remediation: 'Ensure the source is a readable UTF-8 Markdown file within the project root.',
        });
      }
    }
  }

  const includedSources = new Set(documents.map((document) => document.sourcePath));
  const excluded = await fg(['**/*.md'], {
    cwd: resolve(root, 'specs'), onlyFiles: true, unique: true, followSymbolicLinks: false,
  });
  for (const path of excluded.sort()) {
    const sourcePath = posix.join('specs', posixPath(path));
    if (!includedSources.has(sourcePath)) {
      excludedSources.push({sourcePath, reason: 'not-canonical-feature-artifact'});
    }
  }

  documents.sort((left, right) => left.sourcePath.localeCompare(right.sourcePath));
  return populateLinks({projectRoot: root, collections, documents, excludedSources, findings});
}

export function sourcePathFromAbsolute(projectRoot: string, absolutePath: string): string {
  return posixPath(relative(resolve(projectRoot), resolve(absolutePath)));
}

export function sourceDirectory(sourcePath: string): string {
  return posixPath(dirname(sourcePath));
}
