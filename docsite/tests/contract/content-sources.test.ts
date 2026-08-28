import {resolve} from 'node:path';

import {formatFinding, sortFindings} from '../../plugins/concorde-content/validation';
import {validateRegistry} from '../../plugins/concorde-content/validation';
import {buildRegistry} from '../../plugins/concorde-content/registry';
import {discoverDiagramDeclarations} from '../../plugins/concorde-content/diagrams';
import type {ValidationFinding} from '../../plugins/concorde-content/types';

describe('content source diagnostics', () => {
  it('formats stable rule, source, location, reason, and remediation lines', () => {
    const finding: ValidationFinding = {
      ruleId: 'feature.id.required',
      severity: 'error',
      sourcePath: 'specs/001-missing/spec.md',
      location: {line: 2, column: 1},
      message: 'Feature ID is missing.',
      remediation: 'Add a unique YAML id field.',
    };

    expect(formatFinding(finding)).toBe(
      'feature.id.required specs/001-missing/spec.md:2:1: Feature ID is missing.\n' +
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
        sourcePath: 'specs/a/spec.md',
        message: 'Missing ID.',
        remediation: 'Add an ID.',
      },
    ];

    expect(sortFindings(findings).map((finding) => finding.sourcePath)).toEqual([
      'docs/z.md',
      'specs/a/spec.md',
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
    ['missing-implementation', 'feature.implementation.required'],
    ['legacy-feature-design', 'feature.design.legacy'],
    ['missing-module-design', 'module.design.required'],
    ['unpaired-design', 'module.design.unpaired'],
  ])('rejects %s with stable rule %s', async (fixtureName, ruleId) => {
    const registry = await buildRegistry(resolve(__dirname, `../fixtures/invalid-projects/${fixtureName}`));
    expect(validateRegistry(registry).some((finding) => finding.ruleId === ruleId)).toBe(true);
  });

  it('never publishes a design.md that is not a module design reference', async () => {
    const legacy = await buildRegistry(resolve(__dirname, '../fixtures/invalid-projects/legacy-feature-design'));
    expect(legacy.documents.some((document) => document.sourcePath.endsWith('/design.md'))).toBe(false);
    expect(legacy.excludedSources).toContainEqual({
      sourcePath: 'specs/001-legacy/design.md', reason: 'not-canonical-feature-artifact',
    });
    const finding = validateRegistry(legacy).find((candidate) => candidate.ruleId === 'feature.design.legacy');
    expect(finding?.sourcePath).toBe('specs/001-legacy/design.md');
    expect(finding?.remediation).toContain('Rename specs/001-legacy/design.md to specs/001-legacy/implementation.md');
  });

  it('discovers maintained diagram declarations without treating HTML as an input source', async () => {
    const declarations = await discoverDiagramDeclarations(resolve(__dirname, '../../..'));
    expect(declarations).toHaveLength(7);
    expect(declarations.every((declaration) => declaration.ownerPath.startsWith('specs/'))).toBe(true);
    expect(declarations.every((declaration) => declaration.outputPath.startsWith('generated/'))).toBe(true);
  });
});
