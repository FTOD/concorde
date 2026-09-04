import {createHash} from 'node:crypto';
import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {deriveFeatureGraph, findGraphProblems} from '../../plugins/concorde-content/graph';
import {buildRegistry} from '../../plugins/concorde-content/registry';
import type {
  ContentRegistry, FeatureDesign, FeatureRelationEntry, ModuleArchitecture, RelationKind, SourceDocument,
} from '../../plugins/concorde-content/types';
import {validateRegistry} from '../../plugins/concorde-content/validation';

const fixture = resolve(__dirname, '../fixtures/valid-project');
const sha = (value: string) => createHash('sha256').update(value).digest('hex');

function module_(overrides: Partial<ModuleArchitecture> & {moduleId: string}): ModuleArchitecture {
  return {
    collectionId: 'architecture', contentKind: 'module-architecture',
    sourcePath: `specs/${overrides.moduleId}/architecture.md`, realPath: `/project/specs/${overrides.moduleId}/architecture.md`,
    title: overrides.moduleId, sourceSha256: sha(overrides.moduleId), frontMatter: {}, content: '', links: [],
    state: 'validated', route: `/architecture/${overrides.moduleId}`,
    kind: 'module', moduleIds: [], featureIds: [], architectureDiagrams: [],
    ...overrides,
  };
}

function feature(overrides: Partial<FeatureDesign> & {featureId: string} & {relatedFeatureEntries?: FeatureRelationEntry[]}): FeatureDesign {
  return {
    collectionId: 'features', contentKind: 'feature-design',
    sourcePath: `specs/features/${overrides.featureId}.md`, realPath: `/project/specs/features/${overrides.featureId}.md`,
    title: overrides.featureId, sourceSha256: sha(overrides.featureId), frontMatter: {}, content: '', links: [],
    state: 'validated', route: `/features/${overrides.featureId}`,
    kind: 'feature', moduleId: 'module.test', status: 'Draft', outcome: `${overrides.featureId} outcome.`,
    relatedFeatureIds: (overrides.relatedFeatureEntries ?? []).map((entry) => entry.id),
    relatedFeatureEntries: [], relatedFeatures: [],
    providedInterfaceIds: [], requiredInterfaceIds: [], externalRequiredInterfaceIds: [],
    ...overrides,
  };
}

function registry(documents: SourceDocument[]): ContentRegistry {
  return {projectRoot: '/project', collections: [], documents, excludedSources: [], findings: []};
}

function relation(id: string, relation: RelationKind): FeatureRelationEntry {
  return {id, relation};
}

describe('Feature Graph derivation', () => {
  it('derives modules, features, and a merged relates_to edge from the valid-project fixture', async () => {
    const source = await buildRegistry(fixture);
    expect(validateRegistry(source)).toEqual([]);
    const graph = deriveFeatureGraph(source, '0.7.0');

    expect(graph.schema_version).toBe(1);
    expect(graph.generator).toEqual({name: 'concorde-docsite', version: '0.7.0'});
    expect(graph.modules.map((module) => module.id)).toEqual(['module.fixture', 'module.fixture.nested']);
    expect(graph.modules.find((module) => module.id === 'module.fixture.nested')).toMatchObject({parent: 'module.fixture'});
    expect(graph.modules.find((module) => module.id === 'module.fixture')?.parent).toBeUndefined();
    expect(graph.features.map((feature_) => feature_.id)).toEqual(['feature.fixture.alpha', 'feature.fixture.beta']);
    expect(graph.features[0]).toMatchObject({
      module: 'module.fixture', route: '/features/feature.fixture.alpha', status: 'Draft',
      source_path: 'specs/example/features/001-alpha.md',
    });
    expect(graph.features[0].source_sha256).toMatch(/^[a-f0-9]{64}$/);

    // Alpha (plain string -> relates_to Beta) and Beta (plain string -> relates_to Alpha) merge into one edge.
    expect(graph.edges).toEqual([{
      id: 'relates_to:feature.fixture.alpha->feature.fixture.beta', kind: 'relates_to',
      source: 'feature.fixture.alpha', target: 'feature.fixture.beta',
      declared_by: ['feature.fixture.alpha', 'feature.fixture.beta'],
    }]);
    expect(graph.counts).toEqual({
      features: 2, modules: 2,
      edges_by_kind: {composes: 0, refines: 0, depends_on: 0, relates_to: 1, requires: 0},
    });
    expect(graph.source_digest).toMatch(/^[a-f0-9]{64}$/);
  });

  it('publishes an empty graph for a registry with no features or modules', () => {
    const graph = deriveFeatureGraph(registry([]), '0.7.0');
    expect(graph.modules).toEqual([]);
    expect(graph.features).toEqual([]);
    expect(graph.edges).toEqual([]);
    expect(graph.counts).toEqual({
      features: 0, modules: 0,
      edges_by_kind: {composes: 0, refines: 0, depends_on: 0, relates_to: 0, requires: 0},
    });
  });

  it('rejects an unknown relation and derives no edge for it', () => {
    const a = feature({featureId: 'feature.a', relatedFeatureEntries: [{id: 'feature.b', relation: 'sideways' as RelationKind}]});
    const b = feature({featureId: 'feature.b'});
    const source = registry([a, b]);

    const problems = findGraphProblems(source);
    expect(problems).toEqual([expect.objectContaining({
      ruleId: 'feature.relation.unknown', sourcePath: 'specs/features/feature.a.md',
    })]);
    expect(deriveFeatureGraph(source, '0.7.0').edges).toEqual([]);
  });

  it('rejects a self-referencing relation and derives no edge for it', () => {
    const a = feature({featureId: 'feature.a', relatedFeatureEntries: [relation('feature.a', 'composes')]});
    const source = registry([a]);

    const problems = findGraphProblems(source);
    expect(problems).toEqual([expect.objectContaining({
      ruleId: 'feature.relation.self', sourcePath: 'specs/features/feature.a.md',
    })]);
    expect(deriveFeatureGraph(source, '0.7.0').edges).toEqual([]);
  });

  it('rejects a three-feature composes cycle with one finding per member naming the family and the others', () => {
    const a = feature({featureId: 'feature.a', relatedFeatureEntries: [relation('feature.b', 'composes')]});
    const b = feature({featureId: 'feature.b', relatedFeatureEntries: [relation('feature.c', 'composes')]});
    const c = feature({featureId: 'feature.c', relatedFeatureEntries: [relation('feature.a', 'composes')]});
    const problems = findGraphProblems(registry([a, b, c]));

    const cycleProblems = problems.filter((finding) => finding.ruleId === 'feature.relation.cycle');
    expect(cycleProblems).toHaveLength(3);
    expect(cycleProblems.map((finding) => finding.sourcePath).sort()).toEqual([
      'specs/features/feature.a.md', 'specs/features/feature.b.md', 'specs/features/feature.c.md',
    ]);
    for (const finding of cycleProblems) {
      expect(finding.message).toContain('composes cycle');
      expect(finding.message).toMatch(/feature\.a/);
      expect(finding.message).toMatch(/feature\.b/);
      expect(finding.message).toMatch(/feature\.c/);
    }
  });

  it('rejects a two-feature contradictory composes cycle (A composes B and B composes A)', () => {
    const a = feature({featureId: 'feature.a', relatedFeatureEntries: [relation('feature.b', 'composes')]});
    const b = feature({featureId: 'feature.b', relatedFeatureEntries: [relation('feature.a', 'composes')]});
    const problems = findGraphProblems(registry([a, b]));
    expect(problems.filter((finding) => finding.ruleId === 'feature.relation.cycle')).toHaveLength(2);
  });

  it('does not confuse a merged reciprocal declaration with a cycle', () => {
    const a = feature({featureId: 'feature.a', relatedFeatureEntries: [relation('feature.b', 'composes')]});
    const b = feature({featureId: 'feature.b', relatedFeatureEntries: [relation('feature.a', 'composed_by')]});
    const source = registry([a, b]);
    expect(findGraphProblems(source)).toEqual([]);

    const graph = deriveFeatureGraph(source, '0.7.0');
    expect(graph.edges).toEqual([{
      id: 'composes:feature.a->feature.b', kind: 'composes', source: 'feature.a', target: 'feature.b',
      declared_by: ['feature.a', 'feature.b'],
    }]);
  });

  it('normalizes a one-sided inverse relation to its forward kind with source and target swapped', () => {
    const a = feature({featureId: 'feature.a', relatedFeatureEntries: [relation('feature.b', 'refined_by')]});
    const b = feature({featureId: 'feature.b'});
    const graph = deriveFeatureGraph(registry([a, b]), '0.7.0');
    expect(graph.edges).toEqual([{
      id: 'refines:feature.b->feature.a', kind: 'refines', source: 'feature.b', target: 'feature.a',
      declared_by: ['feature.a'],
    }]);
  });

  it('orders undirected relates_to endpoints lexically regardless of declaration order', () => {
    const z = feature({featureId: 'feature.z', relatedFeatureEntries: [relation('feature.a', 'relates_to')]});
    const a = feature({featureId: 'feature.a'});
    const graph = deriveFeatureGraph(registry([z, a]), '0.7.0');
    expect(graph.edges).toEqual([{
      id: 'relates_to:feature.a->feature.z', kind: 'relates_to', source: 'feature.a', target: 'feature.z',
      declared_by: ['feature.z'],
    }]);
  });

  it('derives one requires edge for a required interface with exactly one other published provider', () => {
    const a = feature({featureId: 'feature.a', requiredInterfaceIds: ['contract.x']});
    const b = feature({featureId: 'feature.b', providedInterfaceIds: ['contract.x']});
    const source = registry([a, b]);
    expect(findGraphProblems(source)).toEqual([]);

    const graph = deriveFeatureGraph(source, '0.7.0');
    expect(graph.edges).toEqual([{
      id: 'requires:feature.a->feature.b:contract.x', kind: 'requires', source: 'feature.a', target: 'feature.b',
      interface: 'contract.x', declared_by: ['feature.a'],
    }]);
    expect(graph.counts.edges_by_kind.requires).toBe(1);
  });

  it('derives no edge and no finding for a required interface with a declared external provider', () => {
    const a = feature({featureId: 'feature.a', requiredInterfaceIds: ['contract.external'], externalRequiredInterfaceIds: ['contract.external']});
    const source = registry([a]);
    expect(findGraphProblems(source)).toEqual([]);
    expect(deriveFeatureGraph(source, '0.7.0').edges).toEqual([]);
  });

  it('rejects a required interface with zero published providers and no external provider block', () => {
    const a = feature({featureId: 'feature.a', requiredInterfaceIds: ['contract.missing']});
    const problems = findGraphProblems(registry([a]));
    expect(problems).toEqual([expect.objectContaining({
      ruleId: 'feature.interface.provider.missing', sourcePath: 'specs/features/feature.a.md',
    })]);
  });

  it('rejects a required interface with several published providers', () => {
    const a = feature({featureId: 'feature.a', requiredInterfaceIds: ['contract.y']});
    const b = feature({featureId: 'feature.b', providedInterfaceIds: ['contract.y']});
    const c = feature({featureId: 'feature.c', providedInterfaceIds: ['contract.y']});
    const source = registry([a, b, c]);
    const problems = findGraphProblems(source);
    expect(problems).toEqual([expect.objectContaining({
      ruleId: 'feature.interface.provider.duplicate', sourcePath: 'specs/features/feature.a.md',
    })]);
    expect(deriveFeatureGraph(source, '0.7.0').edges).toEqual([]);
  });

  it('produces a byte-identical graph regardless of input document order', () => {
    const a = feature({featureId: 'feature.a', relatedFeatureEntries: [relation('feature.b', 'depends_on')]});
    const b = feature({featureId: 'feature.b', requiredInterfaceIds: ['contract.z']});
    const c = feature({featureId: 'feature.c', providedInterfaceIds: ['contract.z']});
    const moduleA = module_({moduleId: 'module.test'});

    const first = deriveFeatureGraph(registry([moduleA, a, b, c]), '0.7.0');
    const second = deriveFeatureGraph(registry([c, b, a, moduleA]), '0.7.0');
    expect(second).toEqual(first);
    expect(JSON.stringify(second)).toBe(JSON.stringify(first));
    expect(second.source_digest).toBe(first.source_digest);
  });
});
