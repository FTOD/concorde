import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {resolveContentLink} from '../../plugins/concorde-content/links';
import {buildRegistry} from '../../plugins/concorde-content/registry';

const fixture = resolve(__dirname, '../fixtures/valid-project');

describe('Profile 7 source links', () => {
  it('maps specification-relative links into architecture, feature, and diagram routes', async () => {
    const registry = await buildRegistry(fixture);
    const alpha = registry.documents.find((item) => item.sourcePath === 'specs/example/features/001-alpha.md')!;
    expect(resolveContentLink('../architecture.md', alpha, registry).reference.targetRoute)
      .toBe('/architecture/module.fixture');
    expect(resolveContentLink('../modules/nested/features/002-beta.md', alpha, registry).reference.targetRoute)
      .toBe('/features/feature.fixture.beta');
    expect(resolveContentLink('../diagrams/fixture-level-view.json', alpha, registry).reference.targetRoute)
      .toBe('/architecture/fixture-level-view.html');
  });

  it('preserves fragments across collection boundaries', async () => {
    const registry = await buildRegistry(fixture);
    const architecture = registry.documents.find((item) => item.sourcePath === 'specs/example/architecture.md')!;
    expect(resolveContentLink('features/001-alpha.md#requirements', architecture, registry).reference.targetRoute)
      .toBe('/features/feature.fixture.alpha#requirements');
  });

  it('reports missing, control-state, and escaping targets with Profile 7 remediation', async () => {
    const registry = await buildRegistry(fixture);
    const architecture = registry.documents.find((item) => item.sourcePath === 'specs/example/architecture.md')!;
    expect(resolveContentLink('missing.md', architecture, registry).finding?.ruleId).toBe('link.target.missing');
    const excluded = resolveContentLink('../../.concorde/attempts/feature.fixture.alpha/plan.md', architecture, registry).finding;
    expect(excluded?.ruleId).toBe('link.target.excluded');
    expect(excluded?.message).toContain('Concorde control artifact');
    expect(excluded?.remediation).toContain('architecture.md or a direct feature file');
    expect(resolveContentLink('../../.concorde/reflections/R-001.md', architecture, registry).finding)
      .toMatchObject({ruleId: 'link.target.excluded'});
    expect(resolveContentLink('../../.concorde/config.json', architecture, registry).finding)
      .toMatchObject({ruleId: 'link.target.excluded'});
    expect(resolveContentLink('../../../outside.md', architecture, registry).finding?.ruleId).toBe('link.target.outside-root');
  });
});
