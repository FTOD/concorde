import {lstat} from 'node:fs/promises';
import {dirname, posix, relative, resolve} from 'node:path';

import {unified} from 'unified';
import remarkParse from 'remark-parse';
import {visit} from 'unist-util-visit';

import type {CollectionId, ContentRegistry, LinkReference, ModuleArchitecture, SourceDocument, ValidationFinding} from './types';

interface MarkdownLinkNode {
  type: 'link';
  url: string;
  position?: {start?: {line?: number; column?: number}};
}

const externalPattern = /^(?:[a-z][a-z0-9+.-]*:|\/\/)/i;
const controlStatePattern = /^\.concorde(?:\/|$)/;
const posixPath = (value: string) => value.split('\\').join('/');

function splitTarget(rawTarget: string): {path: string; suffix: string; fragment?: string} {
  const match = rawTarget.match(/^([^?#]*)([?#].*)?$/);
  const path = match?.[1] ?? rawTarget;
  const suffix = match?.[2] ?? '';
  return {path, suffix, fragment: suffix.match(/#([^?]*)/)?.[1]};
}

export function resolveContentLink(
  rawTarget: string,
  source: SourceDocument,
  registry: ContentRegistry,
): {reference: LinkReference; finding?: ValidationFinding} {
  if (rawTarget.startsWith('#')) return {reference: {rawTarget, kind: 'anchor', fragment: rawTarget.slice(1)}};
  if (externalPattern.test(rawTarget)) return {reference: {rawTarget, kind: 'external'}};
  const {path, suffix, fragment} = splitTarget(rawTarget);
  const sourceRelativeTarget = path.startsWith('/')
    ? posix.normalize(path.slice(1))
    : posix.normalize(posix.join(posix.dirname(source.sourcePath), path));
  if (controlStatePattern.test(sourceRelativeTarget)) return {
    reference: {rawTarget, kind: 'excluded-source', targetSourcePath: sourceRelativeTarget, fragment},
    finding: {
      ruleId: 'link.target.excluded', severity: 'error', sourcePath: source.sourcePath,
      message: `Link "${rawTarget}" targets an excluded Concorde control artifact.`,
      remediation: 'Link to a published architecture.md or a direct feature file, or describe the control workflow without linking internal state.',
    },
  };
  if (!/\.md$/i.test(path)) {
    const diagramReference = resolveDiagramLink(rawTarget, path, suffix, fragment, source, registry);
    if (diagramReference) return diagramReference;
    const assetSourcePath = sourceRelativeTarget;
    if (assetSourcePath === '..' || assetSourcePath.startsWith('../')) return {
      reference: {rawTarget, kind: 'excluded-source', targetSourcePath: assetSourcePath, fragment},
      finding: {
        ruleId: 'link.target.outside-root', severity: 'error', sourcePath: source.sourcePath,
        message: `Asset link "${rawTarget}" escapes the project root.`,
        remediation: 'Link only to content or assets inside the project repository.',
      },
    };
    return {reference: {
      rawTarget, kind: 'asset', targetSourcePath: assetSourcePath,
      targetRoute: `/${assetSourcePath}${suffix}`, fragment,
    }};
  }

  if (sourceRelativeTarget === '..' || sourceRelativeTarget.startsWith('../')) {
    return {
      reference: {rawTarget, kind: 'excluded-source', targetSourcePath: sourceRelativeTarget, fragment},
      finding: {
        ruleId: 'link.target.outside-root', severity: 'error', sourcePath: source.sourcePath,
        message: `Markdown link "${rawTarget}" escapes the project root.`,
        remediation: 'Link only to content or assets inside the project repository.',
      },
    };
  }
  const target = registry.documents.find((document) => document.sourcePath === sourceRelativeTarget);
  if (target) return {
    reference: {
      rawTarget, kind: 'included-source', targetSourcePath: target.sourcePath,
      targetRoute: `${target.route}${suffix}`, fragment,
    },
  };
  const excluded = registry.excludedSources.find((entry) => entry.sourcePath === sourceRelativeTarget);
  const ruleId = excluded ? 'link.target.excluded' : 'link.target.missing';
  return {
    reference: {rawTarget, kind: 'excluded-source', targetSourcePath: sourceRelativeTarget, fragment},
    finding: {
      ruleId, severity: 'error', sourcePath: source.sourcePath,
      message: excluded
        ? `Markdown link "${rawTarget}" targets an excluded publication-root artifact.`
        : `Markdown link "${rawTarget}" does not resolve to included content.`,
      remediation: excluded
        ? 'Link to a published architecture.md or a direct feature file, or treat the target as a repository asset.'
        : 'Correct the relative path or add the referenced Markdown source.',
    },
  };
}

/**
 * Maintained Markdown links Archify JSON by path: a module architecture links a diagram beneath
 * the module's adjacent `diagrams/`. Spelled relative to the document or to the repository root, the link
 * resolves to the delivered view route, so the published page never carries a dead link.
 */
function resolveDiagramLink(
  rawTarget: string,
  path: string,
  suffix: string,
  fragment: string | undefined,
  source: SourceDocument,
  registry: ContentRegistry,
): {reference: LinkReference} | undefined {
  if (!/\.json$/i.test(path)) return undefined;
  const candidates = new Set<string>([
    posix.normalize(path.startsWith('/') ? path.slice(1) : path),
    posix.normalize(posix.join(posix.dirname(source.sourcePath), path)),
  ]);
  for (const document of registry.documents) {
    const diagrams = (document as ModuleArchitecture).architectureDiagrams ?? [];
    const diagram = diagrams.find((candidate) => candidates.has(candidate.source));
    if (!diagram) continue;
    return {reference: {rawTarget, kind: 'included-source', targetSourcePath: diagram.source, targetRoute: `${diagram.route}${suffix}`, fragment}};
  }
  return undefined;
}

export function populateLinks(registry: ContentRegistry): ContentRegistry {
  const findings: ValidationFinding[] = [...registry.findings];
  for (const document of registry.documents) {
    const tree = unified().use(remarkParse).parse(document.content);
    visit(tree, 'link', (node: MarkdownLinkNode) => {
      const resolved = resolveContentLink(node.url, document, registry);
      resolved.reference.location = {
        line: node.position?.start?.line ?? 1,
        column: node.position?.start?.column ?? 1,
      };
      document.links.push(resolved.reference);
      if (resolved.finding) {
        resolved.finding.location = resolved.reference.location;
        findings.push(resolved.finding);
      }
    });
    document.state = 'mapped';
  }
  return {...registry, findings};
}

let registryCache = new Map<string, Promise<ContentRegistry>>();

export function resetRemarkRegistryCache(): void {
  registryCache = new Map();
}

export function remarkConcordeLinks(options: {
  projectRoot: string;
  getRegistry: () => Promise<ContentRegistry>;
  stagedRoot?: string;
  canonicalSourceBase?: string;
  canonicalCollectionId?: CollectionId;
}) {
  return async (tree: unknown, file: {path?: string}) => {
    if (!file.path) return;
    const projectRoot = resolve(options.projectRoot);
    const promise = registryCache.get(projectRoot) ?? options.getRegistry();
    registryCache.set(projectRoot, promise);
    const registry = await promise;
    const filePath = resolve(file.path);
    const stagedRelative = options.stagedRoot ? relative(resolve(options.stagedRoot), filePath) : undefined;
    const isStaged = stagedRelative !== undefined && stagedRelative !== '..' && !stagedRelative.startsWith('../');
    // A staged specs page is found by the projected path it was staged at; everything else by its source path.
    const source = isStaged
      ? registry.documents.find((document) =>
          document.stagedPath === posixPath(stagedRelative) &&
          (options.canonicalCollectionId
            ? document.collectionId === options.canonicalCollectionId
            : document.sourcePath.startsWith(`${options.canonicalSourceBase ?? 'specs'}/`)))
      : registry.documents.find((document) => document.sourcePath === posixPath(relative(projectRoot, filePath)));
    if (!source) return;
    const materializedAssets = new Set<string>();
    for (const link of source.links.filter((link) => link.kind === 'asset' && link.targetSourcePath)) {
      try {
        if ((await lstat(resolve(projectRoot, link.targetSourcePath!))).isFile()) materializedAssets.add(link.targetSourcePath!);
      } catch { /* Docusaurus reports a missing raw asset. */ }
    }
    visit(tree as Parameters<typeof visit>[0], 'link', (node: MarkdownLinkNode) => {
      const {reference} = resolveContentLink(node.url, source, registry);
      const materializedAsset = reference.kind === 'asset' && Boolean(reference.targetSourcePath && materializedAssets.has(reference.targetSourcePath));
      if ((reference.kind === 'included-source' || materializedAsset) && reference.targetRoute) {
        // Delivered views are static files under generated/; `pathname://` keeps them out of the router
        // (and its route-only broken-link check) exactly like the raw anchors module pages already use.
        node.url = /\.html(?:[?#]|$)/.test(reference.targetRoute) ? `pathname://${reference.targetRoute}` : reference.targetRoute;
      }
    });
  };
}

export function sourceLinkBase(sourcePath: string): string {
  return dirname(sourcePath);
}
