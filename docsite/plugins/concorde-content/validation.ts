import {relative, resolve, sep} from 'node:path';

import type {
  ContentRegistry, FeatureDesign, ModuleArchitecture, SourceDocument, ValidationFinding,
} from './types';

const isFeature = (document: SourceDocument): document is FeatureDesign => document.contentKind === 'feature-design';
const isModule = (document: SourceDocument): document is ModuleArchitecture => document.contentKind === 'module-architecture';
const controlStatePattern = /^(?:\.concorde\/|specs\/(?:.*\/)?attempts\/|specs\/(?:.*\/)?reflections\.md$)/;

export function sortFindings(findings: ValidationFinding[]): ValidationFinding[] {
  return [...findings].sort((left, right) =>
    [left.sourcePath ?? '', left.location?.line ?? 0, left.location?.column ?? 0, left.ruleId].join('\0')
      .localeCompare([right.sourcePath ?? '', right.location?.line ?? 0, right.location?.column ?? 0, right.ruleId].join('\0')),
  );
}

export function formatFinding(finding: ValidationFinding): string {
  const position = finding.sourcePath
    ? `${finding.sourcePath}${finding.location ? `:${finding.location.line}:${finding.location.column}` : ''}`
    : '<project>';
  return `${finding.ruleId} ${position}: ${finding.message}\nRemediation: ${finding.remediation}`;
}

export function isContainedPath(projectRoot: string, candidate: string): boolean {
  const pathFromRoot = relative(resolve(projectRoot), resolve(candidate));
  return pathFromRoot === '' || (!pathFromRoot.startsWith(`..${sep}`) && pathFromRoot !== '..');
}

function duplicateFindings(
  documents: SourceDocument[],
  value: (document: SourceDocument) => string | undefined,
  ruleId: string,
  label: string,
): ValidationFinding[] {
  const groups = new Map<string, SourceDocument[]>();
  for (const document of documents) {
    const key = value(document);
    if (!key) continue;
    groups.set(key, [...(groups.get(key) ?? []), document]);
  }
  return [...groups.entries()].flatMap(([key, matches]) => matches.length < 2 ? [] : matches.map((document) => ({
    ruleId, severity: 'error' as const, sourcePath: document.sourcePath,
    message: `${label} "${key}" is used by ${matches.length} sources.`,
    remediation: `Assign a unique ${label.toLowerCase()} to each source.`,
  })));
}

export function validateRegistry(registry: ContentRegistry): ValidationFinding[] {
  const findings: ValidationFinding[] = [...registry.findings];
  const modules = registry.documents.filter(isModule);
  const modulesById = new Map(modules.map((module) => [module.moduleId, module]));
  const diagramRoutes = new Map<string, ModuleArchitecture[]>();

  for (const document of registry.documents) {
    if (!isContainedPath(registry.projectRoot, document.realPath)) findings.push({
      ruleId: 'content.path.outside-root', severity: 'error', sourcePath: document.sourcePath,
      message: 'The resolved source path escapes the project root.',
      remediation: 'Move the source into specs/ and remove escaping symbolic links.',
    });
    if (!document.title.trim()) findings.push({
      ruleId: 'content.title.required', severity: 'error', sourcePath: document.sourcePath,
      message: 'The document has no title.', remediation: 'Add front matter title or a level-one Markdown heading.',
    });
    if (controlStatePattern.test(document.sourcePath)) findings.push({
      ruleId: 'content.path.control', severity: 'error', sourcePath: document.sourcePath,
      message: 'Concorde control state is never published.',
      remediation: 'Keep publishable architecture and direct feature sources in specs/ and control state only under .concorde/.',
    });
    if (isFeature(document)) {
      if (!document.featureId) findings.push({
        ruleId: 'feature.id.required', severity: 'error', sourcePath: document.sourcePath,
        message: 'Feature designs require a stable front matter id.', remediation: 'Add a non-empty feature.* id.',
      });
      if (document.kind !== 'feature') findings.push({
        ruleId: 'feature.kind.invalid', severity: 'error', sourcePath: document.sourcePath,
        message: 'Feature designs require kind: feature.', remediation: 'Set front matter kind to feature.',
      });
      if (!document.moduleId) findings.push({
        ruleId: 'feature.module.required', severity: 'error', sourcePath: document.sourcePath,
        message: 'Feature designs require an owning module.', remediation: 'Add the providing module.* ID.',
      });
      if (!document.status) findings.push({
        ruleId: 'feature.status.required', severity: 'error', sourcePath: document.sourcePath,
        message: 'Feature designs require publication status metadata.',
        remediation: 'Add evidence_status front matter (or a maintained **Status** field for an older compatible fixture).',
      });
    }
    if (isModule(document)) {
      if (!document.moduleId) findings.push({
        ruleId: 'module.id.required', severity: 'error', sourcePath: document.sourcePath,
        message: 'Module architectures require a stable front matter id.', remediation: 'Add a non-empty module.* id.',
      });
      if (document.kind !== 'module') findings.push({
        ruleId: 'module.kind.invalid', severity: 'error', sourcePath: document.sourcePath,
        message: 'Module architectures require kind: module.', remediation: 'Set front matter kind to module.',
      });
      if ('children' in document.frontMatter || 'contracts' in document.frontMatter) findings.push({
        ruleId: 'module.profile.legacy', severity: 'error', sourcePath: document.sourcePath,
        message: 'Module architecture uses removed children or contracts metadata.',
        remediation: 'Use modules for child containment and keep interfaces inside feature designs.',
      });
      if (document.parentId) {
        const parent = modulesById.get(document.parentId);
        if (!parent) findings.push({
          ruleId: 'module.parent.unresolved', severity: 'error', sourcePath: document.sourcePath,
          message: `Parent module "${document.parentId}" does not resolve.`,
          remediation: 'Reference a published parent architecture or make this the root module.',
        });
        else if (!parent.moduleIds.includes(document.moduleId)) findings.push({
          ruleId: 'module.parent.registration', severity: 'error', sourcePath: document.sourcePath,
          message: 'The parent architecture does not register this immediate child module.',
          remediation: 'Add the child stable ID to the parent modules list.',
        });
      }
      for (const source of document.unpublishableDiagrams ?? []) findings.push({
        ruleId: 'architecture.diagram.unpublishable', severity: 'error', sourcePath: document.sourcePath,
        message: `Module diagram "${source}" cannot be mapped to a generated site artifact.`,
        remediation: 'Ensure the JSON beneath diagrams/ has a supported kind, title, and HTML output beneath generated/.',
      });
      for (const diagram of document.architectureDiagrams) {
        diagramRoutes.set(diagram.route, [...(diagramRoutes.get(diagram.route) ?? []), document]);
      }
    }
  }

  for (const [route, owners] of diagramRoutes) {
    if (owners.length < 2) continue;
    for (const owner of owners) findings.push({
      ruleId: 'diagram.route.duplicate', severity: 'error', sourcePath: owner.sourcePath,
      message: `Diagram route "${route}" is owned by ${owners.length} module architectures.`,
      remediation: 'Give each architecture-owned diagram a unique output beneath generated/.',
    });
  }

  findings.push(...duplicateFindings(registry.documents, (document) => document.route, 'content.route.duplicate', 'Route'));
  findings.push(...duplicateFindings(registry.documents.filter(isFeature), (document) => isFeature(document) ? document.featureId : undefined,
    'feature.id.duplicate', 'Feature ID'));
  findings.push(...duplicateFindings(registry.documents.filter(isModule), (document) => isModule(document) ? document.moduleId : undefined,
    'module.id.duplicate', 'Module ID'));
  return sortFindings(findings);
}

export function assertValidRegistry(registry: ContentRegistry): ContentRegistry {
  const findings = validateRegistry(registry);
  if (findings.length) throw new Error(`Concorde content validation failed:\n${findings.map(formatFinding).join('\n')}`);
  return {...registry, findings};
}
