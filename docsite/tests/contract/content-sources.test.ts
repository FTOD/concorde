import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {buildRegistry} from '../../plugins/concorde-content/registry';
import {discoverDiagramDeclarations} from '../../plugins/concorde-content/diagrams';
import type {ValidationFinding} from '../../plugins/concorde-content/types';
import {formatFinding, sortFindings, validateRegistry} from '../../plugins/concorde-content/validation';

const fixtures = resolve(__dirname, '../fixtures');

describe('Profile 7 content source contract', () => {
  it('publishes module architecture.md and direct feature Markdown only', async () => {
    const registry = await buildRegistry(resolve(fixtures, 'valid-project'));
    expect(validateRegistry(registry)).toEqual([]);
    expect(registry.collections.map(({id, include}) => [id, include])).toEqual([
      ['architecture', ['**/architecture.md']],
      ['features', ['**/features/*.md']],
    ]);
    expect(registry.documents.every((page) =>
      page.sourcePath.startsWith('specs/') &&
      (page.contentKind === 'module-architecture' || page.contentKind === 'feature-design'))).toBe(true);
    expect(registry.documents.some((page) => page.sourcePath === 'README.md' || page.sourcePath.startsWith('docs/'))).toBe(false);
    expect(registry.documents.some((page) => page.sourcePath.startsWith('.concorde/'))).toBe(false);
    expect(registry.excludedSources.some((source) => source.sourcePath.startsWith('.concorde/'))).toBe(false);
    expect(registry.excludedSources).toEqual([]);
  });

  it.each([
    ['missing-title', 'content.title.required'],
    ['broken-link', 'link.target.missing'],
    ['route-collision', 'content.route.duplicate'],
    ['duplicate-id', 'feature.id.duplicate'],
    ['missing-architecture', 'feature.module.unresolved'],
    ['missing-feature', 'module.feature.unresolved'],
    ['nested-feature', 'feature.hierarchy.forbidden'],
    ['feature-diagram', 'feature.diagram.forbidden'],
    ['legacy-residue', 'source.profile.legacy'],
    ['legacy-control-state', 'source.profile.legacy'],
  ])('rejects %s with stable rule %s', async (fixtureName, ruleId) => {
    const registry = await buildRegistry(resolve(fixtures, `invalid-projects/${fixtureName}`));
    expect(validateRegistry(registry).some((finding) => finding.ruleId === ruleId)).toBe(true);
  });

  it('diagnoses both specification-local attempt and reflection control state as legacy', async () => {
    const registry = await buildRegistry(resolve(fixtures, 'invalid-projects/legacy-control-state'));
    expect(validateRegistry(registry).filter((finding) => finding.ruleId === 'source.profile.legacy')
      .map((finding) => finding.sourcePath)).toEqual([
      'specs/example/attempts/feature.fixture.legacy-control/plan.md',
      'specs/example/reflections.md',
    ]);
  });

  it('defensively rejects any control-plane document admitted by a future collection change', async () => {
    const registry = await buildRegistry(resolve(fixtures, 'valid-project'));
    registry.documents[0].sourcePath = '.concorde/reflections/R-001.md';
    expect(validateRegistry(registry).map((finding) => finding.ruleId)).toContain('content.path.control');
  });

  it('rejects a root docs tree as a parallel prose authority', async () => {
    const registry = await buildRegistry(resolve(fixtures, 'invalid-projects/parallel-docs'));
    expect(validateRegistry(registry)).toContainEqual(expect.objectContaining({
      ruleId: 'source.parallel.docs', sourcePath: 'docs',
    }));
  });

  it('discovers only architecture-owned diagrams', async () => {
    const declarations = await discoverDiagramDeclarations(resolve(fixtures, 'valid-project'));
    expect(declarations).toEqual([expect.objectContaining({
      ownerPath: 'specs/example/architecture.md',
      sourcePath: 'specs/example/diagrams/fixture-level-view.json',
      outputPath: 'generated/architecture/fixture-level-view.html',
    })]);
  });

  it('formats and sorts actionable findings deterministically', () => {
    const findings: ValidationFinding[] = [
      {ruleId: 'z', severity: 'error', sourcePath: 'specs/z.md', message: 'Z.', remediation: 'Fix Z.'},
      {ruleId: 'a', severity: 'error', sourcePath: 'specs/a.md', location: {line: 2, column: 1}, message: 'A.', remediation: 'Fix A.'},
    ];
    expect(sortFindings(findings).map((finding) => finding.sourcePath)).toEqual(['specs/a.md', 'specs/z.md']);
    expect(formatFinding(findings[1])).toBe('a specs/a.md:2:1: A.\nRemediation: Fix A.');
  });
});
