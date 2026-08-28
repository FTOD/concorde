import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {resolveContentLink} from '../../plugins/concorde-content/links';
import {buildRegistry} from '../../plugins/concorde-content/registry';

const fixture = resolve(__dirname, '../fixtures/valid-project');

describe('module summary view links', () => {
  it('resolves a summary link to its declared level view, spelled root-relative or summary-relative', async () => {
    const registry = await buildRegistry(resolve(__dirname, '../../..'));
    const root = registry.documents.find((item) => item.sourcePath === 'specs/concorde/module.md')!;
    expect(resolveContentLink('specs/concorde/architecture.json', root, registry).reference.targetRoute)
      .toBe('/architecture/concorde-root.html');
    expect(resolveContentLink('architecture.json', root, registry).reference.targetRoute)
      .toBe('/architecture/concorde-root.html');
    expect(resolveContentLink('missing-view.json', root, registry).reference.kind).toBe('asset');
  });
});

describe('repository-relative links', () => {
  it('maps same-collection and cross-collection Markdown while preserving fragments', async () => {
    const registry = await buildRegistry(fixture);
    const home = registry.documents.find((item) => item.sourcePath === 'docs/index.md')!;
    expect(resolveContentLink('guide/intro.md', home, registry).reference.targetRoute).toBe('/docs/guide/intro');
    expect(resolveContentLink('../specs/001-alpha/spec.md#requirements', home, registry).reference.targetRoute)
      .toBe('/features/001-alpha/feature.fixture.alpha#requirements');
  });

  it('reports missing, excluded, and escaping targets with distinct rules', async () => {
    const registry = await buildRegistry(fixture);
    const home = registry.documents.find((item) => item.sourcePath === 'docs/index.md')!;
    expect(resolveContentLink('missing.md', home, registry).finding?.ruleId).toBe('link.target.missing');
    expect(resolveContentLink('../specs/001-alpha/plan.md', home, registry).finding?.ruleId).toBe('link.target.excluded');
    expect(resolveContentLink('../../outside.md', home, registry).finding?.ruleId).toBe('link.target.outside-root');
  });
});
