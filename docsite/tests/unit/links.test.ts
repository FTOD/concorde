import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {resolveContentLink} from '../../plugins/concorde-content/links';
import {buildRegistry} from '../../plugins/concorde-content/registry';

const fixture = resolve(__dirname, '../fixtures/valid-project');

describe('module diagram links', () => {
  it('resolves a summary or design-reference link to a module diagram, spelled root-relative or document-relative', async () => {
    const registry = await buildRegistry(resolve(__dirname, '../../..'));
    const root = registry.documents.find((item) => item.sourcePath === 'specs/concorde/module.md')!;
    const design = registry.documents.find((item) => item.sourcePath === 'specs/concorde/design.md')!;
    expect(resolveContentLink('specs/concorde/architecture/diagrams/level-view.json', root, registry).reference.targetRoute)
      .toBe('/architecture/concorde-interaction-architecture.html');
    expect(resolveContentLink('architecture/diagrams/level-view.json', root, registry).reference.targetRoute)
      .toBe('/architecture/concorde-interaction-architecture.html');
    expect(resolveContentLink('architecture/diagrams/level-view.json', design, registry).reference.targetRoute)
      .toBe('/architecture/concorde-interaction-architecture.html');
    expect(resolveContentLink('architecture/diagrams/missing-view.json', root, registry).reference.kind).toBe('asset');
  });

  it('publishes module and contract pages at routes without the architecture/ grouping segment', async () => {
    const registry = await buildRegistry(resolve(__dirname, '../../..'));
    const byPath = (sourcePath: string) => registry.documents.find((item) => item.sourcePath === sourcePath)!;
    expect(byPath('specs/concorde/architecture/modules/auto-docs/module.md').route)
      .toBe('/architecture/concorde/modules/auto-docs/module.concorde.auto-docs');
    expect(byPath('specs/concorde/architecture/contracts/concorde-workflow/contract.md').route)
      .toBe('/architecture/concorde/contracts/concorde-workflow/contract.concorde.workflow');
    expect(byPath('specs/concorde/architecture/modules/auto-docs/features/001-publish-project-docsite/abstract.md').route)
      .toBe('/features/feature.auto-docs.publish-project-docsite');
    expect(byPath('specs/concorde/architecture/modules/auto-docs/features/001-publish-project-docsite/abstract.md').stagedPath)
      .toBe('feature.auto-docs.publish-project-docsite/abstract.md');
    expect(byPath('specs/concorde/architecture/modules/auto-docs/module.md').stagedPath)
      .toBe('concorde/modules/auto-docs/module.md');
    expect(resolveContentLink('architecture/modules/auto-docs/module.md', byPath('specs/concorde/module.md'), registry).reference.targetRoute)
      .toBe('/architecture/concorde/modules/auto-docs/module.concorde.auto-docs');
  });
});

describe('repository-relative links', () => {
  it('maps README links into every published collection and delivered diagrams', async () => {
    const registry = await buildRegistry(fixture);
    const readme = registry.documents.find((item) => item.sourcePath === 'README.md')!;
    expect(resolveContentLink('docs/index.md', readme, registry).reference.targetRoute).toBe('/docs');
    expect(resolveContentLink('specs/example/module.md', readme, registry).reference.targetRoute)
      .toBe('/architecture/example/module.fixture');
    expect(resolveContentLink('specs/001-alpha/abstract.md', readme, registry).reference.targetRoute)
      .toBe('/features/feature.fixture.alpha');
    expect(resolveContentLink('specs/001-alpha/diagrams/alpha-components.json', readme, registry).reference.targetRoute)
      .toBe('/architecture/fixture-alpha-components.html');
  });

  it('maps same-collection and cross-collection Markdown while preserving fragments', async () => {
    const registry = await buildRegistry(fixture);
    const home = registry.documents.find((item) => item.sourcePath === 'docs/index.md')!;
    expect(resolveContentLink('guide/intro.md', home, registry).reference.targetRoute).toBe('/docs/guide/intro');
    expect(resolveContentLink('../specs/001-alpha/design.md#requirements', home, registry).reference.targetRoute)
      .toBe('/features/feature.fixture.alpha/design#requirements');
    expect(resolveContentLink('../specs/001-alpha/abstract.md', home, registry).reference.targetRoute)
      .toBe('/features/feature.fixture.alpha');
  });

  it('resolves the three feature pages to each other as included sources', async () => {
    const registry = await buildRegistry(fixture);
    const byPath = (sourcePath: string) => registry.documents.find((item) => item.sourcePath === sourcePath)!;
    const abstract = byPath('specs/001-alpha/subfeatures/001-prepare/abstract.md');
    const design = byPath('specs/001-alpha/subfeatures/001-prepare/design.md');
    const implementation = byPath('specs/001-alpha/subfeatures/001-prepare/implementation.md');
    expect(resolveContentLink('design.md', abstract, registry).reference)
      .toMatchObject({kind: 'included-source', targetRoute: '/features/feature.fixture.alpha/feature.fixture.alpha.prepare/design'});
    expect(resolveContentLink('implementation.md', abstract, registry).reference)
      .toMatchObject({kind: 'included-source', targetRoute: '/features/feature.fixture.alpha/feature.fixture.alpha.prepare/implementation'});
    expect(resolveContentLink('abstract.md', design, registry).reference)
      .toMatchObject({kind: 'included-source', targetRoute: '/features/feature.fixture.alpha/feature.fixture.alpha.prepare'});
    expect(resolveContentLink('abstract.md', implementation, registry).reference)
      .toMatchObject({kind: 'included-source', targetRoute: '/features/feature.fixture.alpha/feature.fixture.alpha.prepare'});
    expect(resolveContentLink('../../abstract.md', abstract, registry).reference)
      .toMatchObject({kind: 'included-source', targetRoute: '/features/feature.fixture.alpha'});
    expect(resolveContentLink('../002-finish/abstract.md', abstract, registry).finding).toBeUndefined();
  });

  it('reports missing, excluded, and escaping targets with distinct rules', async () => {
    const registry = await buildRegistry(fixture);
    const home = registry.documents.find((item) => item.sourcePath === 'docs/index.md')!;
    expect(resolveContentLink('missing.md', home, registry).finding?.ruleId).toBe('link.target.missing');
    const excluded = resolveContentLink('../specs/001-alpha/plan.md', home, registry).finding;
    expect(excluded?.ruleId).toBe('link.target.excluded');
    expect(excluded?.remediation).toContain('abstract.md, feature design.md, implementation.md');
    expect(resolveContentLink('../../outside.md', home, registry).finding?.ruleId).toBe('link.target.outside-root');
  });
});
