import {resolve} from 'node:path';

import {describe, expect, it} from 'vitest';

import {deriveFeatureGraph, findGraphProblems} from '../../plugins/concorde-content/graph';
import {buildRegistry} from '../../plugins/concorde-content/registry';
import type {EdgeKind, FeatureDesign, ModuleArchitecture, RelationKind} from '../../plugins/concorde-content/types';
import {validateRegistry} from '../../plugins/concorde-content/validation';

const projectRoot = resolve(__dirname, '../../..');

/** Mirrors graph.ts's forward-relation mapping so a real declaration can be traced to its expected edge. */
const FORWARD_RELATION: Partial<Record<RelationKind, {kind: EdgeKind; swap: boolean}>> = {
  composes: {kind: 'composes', swap: false},
  composed_by: {kind: 'composes', swap: true},
  refines: {kind: 'refines', swap: false},
  refined_by: {kind: 'refines', swap: true},
  depends_on: {kind: 'depends_on', swap: false},
  depended_on_by: {kind: 'depends_on', swap: true},
  relates_to: {kind: 'relates_to', swap: false},
};

describe('Concorde repository feature graph', () => {
  it('has zero graph-related validation findings for this repository', async () => {
    const registry = await buildRegistry(projectRoot);
    expect(validateRegistry(registry)).toEqual([]);
    expect(findGraphProblems(registry)).toEqual([]);
  });

  it('publishes every feature as a node and every module as a group', async () => {
    const registry = await buildRegistry(projectRoot);
    const graph = deriveFeatureGraph(registry, '0.7.0');
    const features = registry.documents.filter((document): document is FeatureDesign => document.contentKind === 'feature-design');
    const modules = registry.documents.filter((document): document is ModuleArchitecture => document.contentKind === 'module-architecture');
    expect(features.length).toBeGreaterThan(0);
    expect(modules.length).toBeGreaterThan(0);
    expect(graph.features.map((feature) => feature.id).sort()).toEqual(features.map((feature) => feature.featureId).sort());
    expect(graph.modules.map((module) => module.id).sort()).toEqual(modules.map((module) => module.moduleId).sort());
    expect(graph.counts.features).toBe(features.length);
    expect(graph.counts.modules).toBe(modules.length);
  });

  it('renders every typed related_features declaration as exactly one edge naming its declarer', async () => {
    const registry = await buildRegistry(projectRoot);
    const graph = deriveFeatureGraph(registry, '0.7.0');
    const features = registry.documents.filter((document): document is FeatureDesign => document.contentKind === 'feature-design');
    let declarationCount = 0;
    for (const feature of features) {
      for (const entry of feature.relatedFeatureEntries) {
        declarationCount += 1;
        const mapping = FORWARD_RELATION[entry.relation];
        expect(mapping, `${feature.featureId} declares an unrecognized relation "${entry.relation}"`).toBeDefined();
        let source = mapping!.swap ? entry.id : feature.featureId;
        let target = mapping!.swap ? feature.featureId : entry.id;
        if (mapping!.kind === 'relates_to' && source > target) [source, target] = [target, source];
        const edge = graph.edges.find((candidate) =>
          candidate.kind === mapping!.kind && candidate.source === source && candidate.target === target);
        expect(edge, `no ${mapping!.kind} edge ${source}->${target} for ${feature.featureId}'s "${entry.relation}" declaration`).toBeDefined();
        expect(edge!.declared_by).toContain(feature.featureId);
      }
    }
    expect(declarationCount).toBeGreaterThan(0);
  });

  it('derives one requires edge for every required interface with exactly one other published provider', async () => {
    const registry = await buildRegistry(projectRoot);
    const graph = deriveFeatureGraph(registry, '0.7.0');
    const features = registry.documents.filter((document): document is FeatureDesign => document.contentKind === 'feature-design');
    const providersByInterface = new Map<string, string[]>();
    for (const feature of features) {
      for (const interfaceId of feature.providedInterfaceIds) {
        providersByInterface.set(interfaceId, [...(providersByInterface.get(interfaceId) ?? []), feature.featureId]);
      }
    }
    let expectedRequiresCount = 0;
    for (const feature of features) {
      for (const interfaceId of feature.requiredInterfaceIds) {
        const providers = (providersByInterface.get(interfaceId) ?? []).filter((id) => id !== feature.featureId);
        if (providers.length === 1) expectedRequiresCount += 1;
      }
    }
    expect(expectedRequiresCount).toBeGreaterThan(0);
    expect(graph.counts.edges_by_kind.requires).toBe(expectedRequiresCount);
    expect(graph.edges.filter((edge) => edge.kind === 'requires')).toHaveLength(expectedRequiresCount);
  });

  it('keeps every directional family acyclic', async () => {
    const registry = await buildRegistry(projectRoot);
    expect(findGraphProblems(registry).filter((finding) => finding.ruleId === 'feature.relation.cycle')).toEqual([]);
  });

  it('produces a byte-identical graph across repeated derivations', async () => {
    const registry = await buildRegistry(projectRoot);
    const first = deriveFeatureGraph(registry, '0.7.0');
    const second = deriveFeatureGraph(await buildRegistry(projectRoot), '0.7.0');
    expect(JSON.stringify(second)).toBe(JSON.stringify(first));
  });
});
