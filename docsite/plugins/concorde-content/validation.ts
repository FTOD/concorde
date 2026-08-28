import {relative, resolve, sep} from 'node:path';

import type {
  ArchitectureSource, ContentRegistry, FeatureDesign, FeatureSpecification, FeatureTldr, ModuleDesign, SourceDocument, ValidationFinding,
} from './types';

const isFeature = (document: SourceDocument): document is FeatureSpecification => document.collectionId === 'features';
const isFeatureTldr = (document: SourceDocument): document is FeatureTldr => document.collectionId === 'feature-tldrs';
const isFeatureDesign = (document: SourceDocument): document is FeatureDesign => document.collectionId === 'feature-designs';
const isArchitecture = (document: SourceDocument): document is ArchitectureSource => document.contentKind === 'architecture-source';
const isModuleDesign = (document: SourceDocument): document is ModuleDesign => document.contentKind === 'module-design';
const temporalWorkspacePattern = /(^|\/)implementation\//;

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
  const featureDiagramRoutes = new Map<string, FeatureSpecification[]>();
  for (const document of registry.documents) {
    if (!isContainedPath(registry.projectRoot, document.realPath)) {
      findings.push({
        ruleId: 'content.path.outside-root', severity: 'error', sourcePath: document.sourcePath,
        message: 'The resolved source path escapes the project root.',
        remediation: 'Move the source into docs/ or specs/ and remove escaping symbolic links.',
      });
    }
    if (!document.title.trim()) {
      findings.push({
        ruleId: 'content.title.required', severity: 'error', sourcePath: document.sourcePath,
        message: 'The document has no title.',
        remediation: 'Add front matter title or a level-one Markdown heading.',
      });
    }
    if (temporalWorkspacePattern.test(document.sourcePath)) {
      findings.push({
        ruleId: 'content.path.temporal', severity: 'error', sourcePath: document.sourcePath,
        message: 'Temporal implementation workspace content is never published.',
        remediation: 'Keep publishable sources outside implementation/ directories; the accepted design reference lives in design.md beside spec.md.',
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
      if (document.featureLevel === 'subfeature' && (!document.parentFeatureId || !document.outcome)) findings.push({
        ruleId: 'feature.containment.summary', severity: 'error', sourcePath: document.sourcePath,
        message: 'Sub-feature pages require one parent and a non-empty Outcome section.',
        remediation: 'Declare parent_feature and add one concise ## Outcome section.',
      });
      if (!document.tldrRoute) findings.push({
        ruleId: 'feature.tldr.missing', severity: 'error', sourcePath: document.sourcePath,
        message: 'Feature specification has no sibling tldr.md landing page.',
        remediation: 'Add tldr.md beside spec.md (no front matter; H1 "TL;DR: <title>"; sections Purpose, Functionality, Structure, Logic, and Read Next) so the feature opens on its TL;DR.',
      });
      if (!document.designRoute) findings.push({
        ruleId: 'feature.design.required', severity: 'error', sourcePath: document.sourcePath,
        message: 'Feature specification has no companion design.md design reference.',
        remediation: 'Add design.md beside spec.md (a placeholder design reference is acceptable) so the specification and its accepted design are published together.',
      });
      for (const diagram of document.diagrams) {
        featureDiagramRoutes.set(diagram.route, [...(featureDiagramRoutes.get(diagram.route) ?? []), document]);
      }
    }
    if (isFeatureTldr(document) && !document.specificationRoute) {
      findings.push({
        ruleId: 'tldr.unpaired', severity: 'error', sourcePath: document.sourcePath,
        message: 'tldr.md has no publishable sibling spec.md, so it cannot be published as a feature landing page.',
        remediation: 'Place tldr.md beside the feature or sub-feature spec.md it summarizes, or remove it.',
      });
    }
    if (isFeatureDesign(document) && !document.specificationRoute) {
      findings.push({
        ruleId: 'feature.design.unpaired', severity: 'error', sourcePath: document.sourcePath,
        message: 'design.md has no publishable sibling spec.md, so it cannot be published as a feature design reference.',
        remediation: 'Ensure the sibling spec.md is a readable canonical feature specification, or remove design.md.',
      });
    }
    if (isModuleDesign(document) && !document.moduleRoute) {
      findings.push({
        ruleId: 'module.design.unpaired', severity: 'error', sourcePath: document.sourcePath,
        message: 'design.md is not paired with a publishable module summary in the same directory.',
        remediation: 'Ensure the sibling module.md declares kind: module and a stable id.',
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
      if (document.architectureKind === 'module' && !document.designReferenceRoute) findings.push({
        ruleId: 'module.design.required', severity: 'error', sourcePath: document.sourcePath,
        message: 'Module summary has no companion design.md design reference.',
        remediation: 'Create design.md beside module.md with a level-one heading and at least one level-two section (seed text is acceptable), and link it from the summary.',
      });
    }
  }
  for (const [route, owners] of featureDiagramRoutes) {
    if (owners.length < 2) continue;
    for (const owner of owners) findings.push({
      ruleId: 'feature.diagram.route.duplicate', severity: 'error', sourcePath: owner.sourcePath,
      message: `Feature diagram route "${route}" is declared by ${owners.length} feature specifications.`,
      remediation: 'Give each generated feature diagram a unique output beneath generated/.',
    });
  }
  findings.push(...duplicateFindings(registry.documents, (document) => document.route, 'content.route.duplicate', 'Route'));
  findings.push(...duplicateFindings(
    registry.documents.filter((document) => document.collectionId === 'features'),
    (document) => isFeature(document) ? document.featureId : undefined,
    'feature.id.duplicate',
    'Feature ID',
  ));
  findings.push(...duplicateFindings(
    registry.documents.filter(isArchitecture),
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
