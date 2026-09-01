import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {resolveContentLink} from '../../plugins/concorde-content/links';
import {buildRegistry} from '../../plugins/concorde-content/registry';

const fixture = resolve(__dirname, '../fixtures/valid-project');

describe('Profile 7 source links', () => {
  it('maps repository-relative links into architecture, feature, docs, and diagram routes', async () => {
    const registry = await buildRegistry(fixture);
    const readme = registry.documents.find((item) => item.sourcePath === 'README.md')!;
    expect(resolveContentLink('docs/index.md', readme, registry).reference.targetRoute).toBe('/docs');
    expect(resolveContentLink('specs/example/architecture.md', readme, registry).reference.targetRoute)
      .toBe('/architecture/module.fixture');
    expect(resolveContentLink('specs/example/features/001-alpha.md', readme, registry).reference.targetRoute)
      .toBe('/features/feature.fixture.alpha');
    expect(resolveContentLink('specs/example/diagrams/fixture-level-view.json', readme, registry).reference.targetRoute)
      .toBe('/architecture/fixture-level-view.html');
  });

  it('preserves fragments across collection boundaries', async () => {
    const registry = await buildRegistry(fixture);
    const docs = registry.documents.find((item) => item.sourcePath === 'docs/index.md')!;
    expect(resolveContentLink('../specs/example/features/001-alpha.md#requirements', docs, registry).reference.targetRoute)
      .toBe('/features/feature.fixture.alpha#requirements');
  });

  it('reports missing, control-state, and escaping targets with Profile 7 remediation', async () => {
    const registry = await buildRegistry(fixture);
    const docs = registry.documents.find((item) => item.sourcePath === 'docs/index.md')!;
    expect(resolveContentLink('missing.md', docs, registry).finding?.ruleId).toBe('link.target.missing');
    const excluded = resolveContentLink('../.concorde/attempts/feature.fixture.alpha/plan.md', docs, registry).finding;
    expect(excluded?.ruleId).toBe('link.target.excluded');
    expect(excluded?.message).toContain('Concorde control artifact');
    expect(excluded?.remediation).toContain('architecture.md or a direct feature file');
    expect(resolveContentLink('../.concorde/reflections/log.md', docs, registry).finding)
      .toMatchObject({ruleId: 'link.target.excluded'});
    expect(resolveContentLink('../.concorde/config.json', docs, registry).finding)
      .toMatchObject({ruleId: 'link.target.excluded'});
    expect(resolveContentLink('../../outside.md', docs, registry).finding?.ruleId).toBe('link.target.outside-root');
  });
});
