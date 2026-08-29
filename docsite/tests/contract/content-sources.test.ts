import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

import {formatFinding, sortFindings} from '../../plugins/concorde-content/validation';
import {validateRegistry} from '../../plugins/concorde-content/validation';
import {buildRegistry} from '../../plugins/concorde-content/registry';
import {discoverDiagramDeclarations} from '../../plugins/concorde-content/diagrams';
import type {ValidationFinding} from '../../plugins/concorde-content/types';

describe('content source diagnostics', () => {
  it('defines independent Architecture and Features projections in content-source contract v8', async () => {
    const contract = await readFile(resolve(
      process.cwd(), '../specs/concorde/features/002-create-project-docsite/contracts/content-sources.md',
    ), 'utf8');
    expect(contract).toContain('# Content Sources Contract v8');
    expect(contract).toContain('Architecture navigation and routes follow declared module containment.');
    expect(contract).toContain('Features navigation and routes follow globally unique feature IDs');
    expect(contract).toContain('never create parent categories or route segments in Features');
  });

  it('formats stable rule, source, location, reason, and remediation lines', () => {
    const finding: ValidationFinding = {
      ruleId: 'feature.id.required',
      severity: 'error',
      sourcePath: 'specs/001-missing/design.md',
      location: {line: 2, column: 1},
      message: 'Feature ID is missing.',
      remediation: 'Add a unique YAML id field.',
    };

    expect(formatFinding(finding)).toBe(
      'feature.id.required specs/001-missing/design.md:2:1: Feature ID is missing.\n' +
        'Remediation: Add a unique YAML id field.',
    );
  });

  it('sorts findings by source, rule, and location', () => {
    const findings: ValidationFinding[] = [
      {
        ruleId: 'source.title.required',
        severity: 'error',
        sourcePath: 'docs/z.md',
        message: 'Missing title.',
        remediation: 'Add a title.',
      },
      {
        ruleId: 'feature.id.required',
        severity: 'error',
        sourcePath: 'specs/a/design.md',
        message: 'Missing ID.',
        remediation: 'Add an ID.',
      },
    ];

    expect(sortFindings(findings).map((finding) => finding.sourcePath)).toEqual([
      'docs/z.md',
      'specs/a/design.md',
    ]);
  });

  it('keeps fixtures inside their declared project root', () => {
    const projectRoot = resolve(process.cwd(), 'tests/fixtures/valid-project');
    const docPath = resolve(projectRoot, 'docs/index.md');

    expect(docPath.startsWith(`${projectRoot}/`)).toBe(true);
  });

  it.each([
    ['missing-title', 'content.title.required'],
    ['broken-link', 'link.target.missing'],
    ['route-collision', 'content.route.duplicate'],
    ['duplicate-id', 'feature.id.duplicate'],
    ['missing-abstract', 'feature.abstract.missing'],
    ['missing-feature-implementation', 'feature.implementation.required'],
    ['legacy-feature-names', 'feature.name.legacy'],
    ['unpaired-abstract', 'abstract.unpaired'],
    ['missing-module-design', 'module.design.required'],
    ['unpaired-implementation', 'feature.implementation.unpaired'],
  ])('rejects %s with stable rule %s', async (fixtureName, ruleId) => {
    const registry = await buildRegistry(resolve(__dirname, `../fixtures/invalid-projects/${fixtureName}`));
    expect(validateRegistry(registry).some((finding) => finding.ruleId === ruleId)).toBe(true);
  });

  it('publishes implementation.md and rejects the former spec.md name', async () => {
    const legacy = await buildRegistry(resolve(__dirname, '../fixtures/invalid-projects/legacy-feature-names'));
    expect(legacy.documents.some((document) => document.sourcePath.endsWith('/implementation.md'))).toBe(true);
    expect(legacy.excludedSources).toContainEqual({
      sourcePath: 'specs/001-legacy/spec.md', reason: 'not-canonical-feature-artifact',
    });
    const findings = validateRegistry(legacy);
    const finding = findings.find((candidate) => candidate.ruleId === 'feature.name.legacy');
    expect(finding?.sourcePath).toBe('specs/001-legacy/spec.md');
    expect(finding?.remediation).toContain('abstract.md');
  });

  it('rejects implementation.md without a sibling feature design', async () => {
    const unpaired = await buildRegistry(resolve(__dirname, '../fixtures/invalid-projects/unpaired-implementation'));
    const finding = validateRegistry(unpaired).find((candidate) => candidate.ruleId === 'feature.implementation.unpaired');
    expect(finding?.sourcePath).toBe('specs/notes/implementation.md');
    expect(finding?.remediation).toContain('design.md');
  });

  it('requires an abstract beside every feature design and names the five sections', async () => {
    const registry = await buildRegistry(resolve(__dirname, '../fixtures/invalid-projects/missing-abstract'));
    const finding = validateRegistry(registry).find((candidate) => candidate.ruleId === 'feature.abstract.missing');
    expect(finding?.sourcePath).toBe('specs/001-bare/design.md');
    expect(finding?.remediation).toContain('abstract.md');
    for (const section of ['Purpose', 'Functionality', 'Structure', 'Logic', 'Read Next']) {
      expect(finding?.remediation).toContain(section);
    }
  });

  it('discovers maintained diagram declarations without treating HTML as an input source', async () => {
    const declarations = await discoverDiagramDeclarations(resolve(__dirname, '../../..'));
    expect(declarations).toHaveLength(8);
    expect(declarations.every((declaration) => declaration.ownerPath.startsWith('specs/'))).toBe(true);
    expect(declarations.every((declaration) => declaration.outputPath.startsWith('generated/'))).toBe(true);
  });

  it('publishes a real module-level feature without module storage segments in its feature route', async () => {
    const registry = await buildRegistry(resolve(__dirname, '../../..'));
    const page = registry.documents.find((document) =>
      document.sourcePath === 'specs/concorde/architecture/modules/documentation/features/001-publish-project-docsite/abstract.md');
    expect(page).toMatchObject({
      route: '/features/feature.documentation.publish-project-docsite',
      stagedPath: 'feature.documentation.publish-project-docsite/abstract.md',
      moduleId: 'module.concorde.documentation',
      moduleRoute: '/architecture/concorde/modules/documentation/module.concorde.documentation',
      refinements: [expect.objectContaining({
        featureId: 'feature.concorde.publish-project-docsite',
        route: '/features/feature.concorde.publish-project-docsite',
      })],
    });
  });
});
