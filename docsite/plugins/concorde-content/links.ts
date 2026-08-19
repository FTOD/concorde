import {dirname, posix, relative, resolve} from 'node:path';

import {unified} from 'unified';
import remarkParse from 'remark-parse';
import {visit} from 'unist-util-visit';

import type {ContentRegistry, LinkReference, SourceDocument, ValidationFinding} from './types';

interface MarkdownLinkNode {
  type: 'link';
  url: string;
  position?: {start?: {line?: number; column?: number}};
}

const externalPattern = /^(?:[a-z][a-z0-9+.-]*:|\/\/)/i;
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
  if (!/\.md$/i.test(path)) return {reference: {rawTarget, kind: 'asset', fragment}};

  const sourceRelativeTarget = path.startsWith('/')
    ? posix.normalize(path.slice(1))
    : posix.normalize(posix.join(posix.dirname(source.sourcePath), path));
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
        ? `Markdown link "${rawTarget}" targets an excluded Spec Kit artifact.`
        : `Markdown link "${rawTarget}" does not resolve to included content.`,
      remediation: excluded
        ? 'Link to the canonical feature spec.md or treat the target as a repository asset.'
        : 'Correct the relative path or add the referenced Markdown source.',
    },
  };
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

export function remarkConcordeLinks(options: {projectRoot: string; getRegistry: () => Promise<ContentRegistry>}) {
  return async (tree: unknown, file: {path?: string}) => {
    if (!file.path) return;
    const projectRoot = resolve(options.projectRoot);
    const promise = registryCache.get(projectRoot) ?? options.getRegistry();
    registryCache.set(projectRoot, promise);
    const registry = await promise;
    const sourcePath = posixPath(relative(projectRoot, resolve(file.path)));
    const source = registry.documents.find((document) => document.sourcePath === sourcePath);
    if (!source) return;
    visit(tree as Parameters<typeof visit>[0], 'link', (node: MarkdownLinkNode) => {
      const {reference} = resolveContentLink(node.url, source, registry);
      if (reference.kind === 'included-source' && reference.targetRoute) node.url = reference.targetRoute;
    });
  };
}

export function sourceLinkBase(sourcePath: string): string {
  return dirname(sourcePath);
}
