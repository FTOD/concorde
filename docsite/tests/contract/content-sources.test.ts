import {resolve} from 'node:path';

import {formatFinding, sortFindings} from '../../plugins/concorde-content/validation';
import {validateRegistry} from '../../plugins/concorde-content/validation';
import {buildRegistry} from '../../plugins/concorde-content/registry';
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
  ])('rejects %s with stable rule %s', async (fixtureName, ruleId) => {
    const registry = await buildRegistry(resolve(__dirname, `../fixtures/invalid-projects/${fixtureName}`));
    expect(validateRegistry(registry).some((finding) => finding.ruleId === ruleId)).toBe(true);
  });
});
