import {relative, resolve, sep} from 'node:path';

import type {ArchitectureSource, ContentRegistry, FeatureSpecification, SourceDocument, ValidationFinding} from './types';

const isFeature = (document: SourceDocument): document is FeatureSpecification => document.collectionId === 'features';
const isArchitecture = (document: SourceDocument): document is ArchitectureSource => document.collectionId === 'architecture';

export function sortFindings(findings: ValidationFinding[]): ValidationFinding[] {
  return [...findings].sort((left, right) =>
    [left.sourcePath ?? '', left.location?.line ?? 0, left.location?.column ?? 0, left.ruleId].join('\0')
      .localeCompare(
        [right.sourcePath ?? '', right.location?.line ?? 0, right.location?.column ?? 0, right.ruleId].join('\0'),
      ),
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
  return [...groups.entries()].flatMap(([key, matches]) =>
    matches.length < 2
      ? []
      : matches.map((document) => ({
          ruleId,
          severity: 'error' as const,
          sourcePath: document.sourcePath,
          message: `${label} "${key}" is used by ${matches.length} sources.`,
          remediation: `Assign a unique ${label.toLowerCase()} to each source.`,
        })),
  );
}

export function validateRegistry(registry: ContentRegistry): ValidationFinding[] {
  const findings: ValidationFinding[] = [];
  for (const document of registry.documents) {
    if (!isContainedPath(registry.projectRoot, document.realPath)) {
      findings.push({
        ruleId: 'content.path.outside-root', severity: 'error', sourcePath: document.sourcePath,
        message: 'The resolved source path escapes the project root.',
        remediation: 'Move the source into architecture/, docs/, or specs/ and remove escaping symbolic links.',
      });
    }
    if (!document.title.trim()) {
      findings.push({
        ruleId: 'content.title.required', severity: 'error', sourcePath: document.sourcePath,
        message: 'The document has no title.',
        remediation: 'Add front matter title or a level-one Markdown heading.',
      });
    }
    if (isFeature(document)) {
      if (!document.featureId) findings.push({
        ruleId: 'feature.id.required', severity: 'error', sourcePath: document.sourcePath,
        message: 'Canonical feature specifications require a stable front matter id.',
        remediation: 'Add a non-empty id field to the specification front matter.',
      });
      if (document.kind !== 'feature') findings.push({
        ruleId: 'feature.kind.invalid', severity: 'error', sourcePath: document.sourcePath,
        message: 'Canonical feature specifications require kind: feature.',
        remediation: 'Set front matter kind to feature.',
      });
      if (!document.moduleId) findings.push({
        ruleId: 'feature.module.required', severity: 'error', sourcePath: document.sourcePath,
        message: 'Canonical feature specifications require an owning module.',
        remediation: 'Add a non-empty module field to the specification front matter.',
      });
      if (!document.status) findings.push({
        ruleId: 'feature.status.required', severity: 'error', sourcePath: document.sourcePath,
        message: 'Canonical feature specifications require a lifecycle status.',
        remediation: 'Add a **Status** field to the specification body.',
      });
    }
    if (isArchitecture(document)) {
      if (!document.architectureId) findings.push({
        ruleId: 'architecture.id.required', severity: 'error', sourcePath: document.sourcePath,
        message: 'Architecture sources require a stable front matter id.',
        remediation: 'Add a non-empty id field using the module.*, feature.*, or contract.* namespace.',
      });
      if (!['module', 'feature', 'contract'].includes(document.architectureKind)) findings.push({
        ruleId: 'architecture.kind.invalid', severity: 'error', sourcePath: document.sourcePath,
        message: 'Architecture sources require kind: module, feature, or contract.',
        remediation: 'Set kind to the architectural entity represented by this source.',
      });
      if (document.architectureKind !== 'module' && !document.moduleId) findings.push({
        ruleId: 'architecture.module.required', severity: 'error', sourcePath: document.sourcePath,
        message: 'Architecture feature and contract sources require an owning module.',
        remediation: 'Add a non-empty module field that resolves to the owning module ID.',
      });
      if (document.architectureViewSource && (!document.architectureViewSha256 || !document.architectureViewRoute)) findings.push({
        ruleId: 'architecture.view.unpublishable', severity: 'error', sourcePath: document.sourcePath,
        message: `Declared architecture view "${document.architectureViewSource}" cannot be mapped to a generated site artifact.`,
        remediation: 'Correct the view path, ensure its JSON is valid, set meta.output beneath generated/, and deliver the HTML artifact.',
      });
    }
  }
  findings.push(...duplicateFindings(registry.documents, (document) => document.route, 'content.route.duplicate', 'Route'));
  findings.push(...duplicateFindings(
    registry.documents.filter((document) => document.collectionId === 'features'),
    (document) => isFeature(document) ? document.featureId : undefined,
    'feature.id.duplicate',
    'Feature ID',
  ));
  findings.push(...duplicateFindings(
    registry.documents.filter((document) => document.collectionId === 'architecture'),
    (document) => isArchitecture(document) ? document.architectureId : undefined,
    'architecture.id.duplicate',
    'Architecture ID',
  ));
  return sortFindings([...registry.findings, ...findings]);
}

export function assertValidRegistry(registry: ContentRegistry): ContentRegistry {
  const findings = validateRegistry(registry);
  if (findings.length > 0) {
    throw new Error(`Concorde content validation failed:\n${findings.map(formatFinding).join('\n')}`);
  }
  return {...registry, findings};
}
