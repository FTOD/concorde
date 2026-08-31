import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

import {formatFinding, sortFindings} from '../../plugins/concorde-content/validation';
import {validateRegistry} from '../../plugins/concorde-content/validation';
import {buildRegistry} from '../../plugins/concorde-content/registry';
import {discoverDiagramDeclarations} from '../../plugins/concorde-content/diagrams';
import type {ValidationFinding} from '../../plugins/concorde-content/types';

describe('content source diagnostics', () => {
  it('defines the README homepage, docs diagrams, and independent Architecture and Features projections in content-source contract v10', async () => {
    const contract = await readFile(resolve(
      process.cwd(), '../specs/concorde/features/002-auto-docsite/contracts/content-sources.md',
    ), 'utf8');
    const moduleContract = await readFile(resolve(
      process.cwd(), '../specs/concorde/architecture/modules/auto-docs/architecture/contracts/project-content/contract.md',
    ), 'utf8');
    expect(contract).toContain('# Content Sources Contract v10');
    expect(contract).toContain('documentation diagrams from');
    expect(contract).toContain('docs-page front matter');
    expect(contract).toContain('| Project homepage | project root | The regular file `README.md` | `/` |');
    expect(contract).toContain('Architecture navigation and routes follow declared module containment.');
    expect(contract).toContain("Features navigation follows declared module containment and each module's ordered `features`");
    expect(contract).toContain('Adjacent-level `refines` relationships remain metadata and cross-links rather than navigation');
    expect(moduleContract).toContain('version: 9');
    expect(moduleContract).toContain('root `README.md`');
    expect(moduleContract).toContain('all three accepted inputs');
  });

  it('requires the root README and rejects broken or competing homepage sources', async () => {
    const missing = await buildRegistry(resolve(__dirname, '../fixtures/invalid-projects/missing-title'));
    expect(validateRegistry(missing).some((finding) => finding.ruleId === 'content.home.required')).toBe(true);

    const broken = await buildRegistry(resolve(__dirname, '../fixtures/invalid-projects/home-broken-link'));
    expect(validateRegistry(broken).some((finding) =>
      finding.ruleId === 'link.target.missing' && finding.sourcePath === 'README.md')).toBe(true);

    const collision = await buildRegistry(resolve(__dirname, '../fixtures/valid-project'));
    const competing = collision.documents.find((document) => document.sourcePath === 'docs/index.md');
    if (!competing) throw new Error('Expected the fixture documentation landing page.');
    competing.route = '/';
    expect(validateRegistry(collision).some((finding) =>
      finding.ruleId === 'content.route.duplicate' && finding.sourcePath === 'README.md')).toBe(true);
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
    expect(declarations).toHaveLength(10);
    expect(declarations.every((declaration) => declaration.ownerPath.startsWith('specs/') || declaration.ownerPath.startsWith('docs/'))).toBe(true);
    expect(declarations.every((declaration) => declaration.outputPath.startsWith('generated/'))).toBe(true);
    expect(declarations).toContainEqual(expect.objectContaining({
      sourcePath: 'specs/concorde/architecture/diagrams/skill-workspace-file-flow.json',
      outputPath: 'generated/architecture/concorde-skill-workspace-file-flow.html',
    }));
    expect(declarations).toContainEqual(expect.objectContaining({
      ownerPath: 'docs/concorde-workflow.md',
      sourcePath: 'docs/diagrams/concorde-command-workspace-file-flow.json',
      outputPath: 'generated/architecture/concorde-command-workspace-file-flow.html',
    }));
  });

  it('publishes a module-level feature on a stable route independent of its module navigation group', async () => {
    const registry = await buildRegistry(resolve(__dirname, '../../..'));
    const page = registry.documents.find((document) =>
      document.sourcePath === 'specs/concorde/architecture/modules/auto-docs/features/001-publish-project-docsite/abstract.md');
    expect(page).toMatchObject({
      route: '/features/feature.auto-docs.publish-project-docsite',
      stagedPath: 'feature.auto-docs.publish-project-docsite/abstract.md',
      moduleId: 'module.concorde.auto-docs',
      moduleRoute: '/architecture/concorde/modules/auto-docs/module.concorde.auto-docs',
      refinements: [expect.objectContaining({
        featureId: 'feature.concorde.publish-project-docsite',
        route: '/features/feature.concorde.publish-project-docsite',
      })],
    });
  });
});
