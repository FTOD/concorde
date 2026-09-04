import {createHash} from 'node:crypto';

import type {
  ContentRegistry, EdgeKind, FeatureDesign, FeatureGraph, GraphEdge, ModuleArchitecture, RelationKind,
  ValidationFinding,
} from './types';

const isFeature = (document: {contentKind: string}): document is FeatureDesign => document.contentKind === 'feature-design';
const isModule = (document: {contentKind: string}): document is ModuleArchitecture => document.contentKind === 'module-architecture';

const compareText = (left: string, right: string) => left < right ? -1 : left > right ? 1 : 0;
const sha256Hex = (value: string) => createHash('sha256').update(value).digest('hex');

/** Every directional family a `requires` and typed `related_features` edge can belong to (FR-005). */
export const DIRECTIONAL_EDGE_KINDS: EdgeKind[] = ['composes', 'refines', 'depends_on', 'requires'];
/** Every edge kind Feature Graph 1 can carry, in the deterministic order `counts.edges_by_kind` reports. */
export const ALL_EDGE_KINDS: EdgeKind[] = ['composes', 'refines', 'depends_on', 'relates_to', 'requires'];

/** Declared relation -> {forward edge kind, whether source/target must swap} (FR-002/FR-003). */
const FORWARD_RELATION: Partial<Record<RelationKind, {kind: EdgeKind; swap: boolean}>> = {
  composes: {kind: 'composes', swap: false},
  composed_by: {kind: 'composes', swap: true},
  refines: {kind: 'refines', swap: false},
  refined_by: {kind: 'refines', swap: true},
  depends_on: {kind: 'depends_on', swap: false},
  depended_on_by: {kind: 'depends_on', swap: true},
  relates_to: {kind: 'relates_to', swap: false},
};

interface DeclaredEdge {
  kind: EdgeKind;
  source: string;
  target: string;
  declaredBy: string;
  interfaceId?: string;
}

function edgeId(kind: EdgeKind, source: string, target: string, interfaceId?: string): string {
  return interfaceId ? `${kind}:${source}->${target}:${interfaceId}` : `${kind}:${source}->${target}`;
}

/**
 * Typed `related_features` edges (FR-002/FR-003): inverse relations normalize to the forward kind
 * with source/target swapped; a self-reference or an unrecognized relation is reported and excluded
 * from the edge set rather than silently accepted.
 */
function collectRelationEdges(features: FeatureDesign[], findings: ValidationFinding[]): DeclaredEdge[] {
  const edges: DeclaredEdge[] = [];
  for (const feature of features) {
    for (const entry of feature.relatedFeatureEntries) {
      if (entry.id === feature.featureId) {
        findings.push({
          ruleId: 'feature.relation.self', severity: 'error', sourcePath: feature.sourcePath,
          message: `Feature "${feature.featureId}" declares a related_features relation to itself.`,
          remediation: 'Remove the self-referencing related_features entry.',
        });
        continue;
      }
      const mapping = FORWARD_RELATION[entry.relation];
      if (!mapping) {
        findings.push({
          ruleId: 'feature.relation.unknown', severity: 'error', sourcePath: feature.sourcePath,
          message: `Feature "${feature.featureId}" declares an unknown relation "${entry.relation}" to "${entry.id}".`,
          remediation: 'Use one of composes, refines, depends_on, composed_by, refined_by, depended_on_by, or relates_to.',
        });
        continue;
      }
      edges.push({
        kind: mapping.kind,
        source: mapping.swap ? entry.id : feature.featureId,
        target: mapping.swap ? feature.featureId : entry.id,
        declaredBy: feature.featureId,
      });
    }
  }
  return edges;
}

/**
 * Interface-derived `requires` edges (FR-004): one edge per (feature, required interface) whose
 * provider is exactly one other published feature; an interface with an external provider block
 * yields no edge and no finding; zero or several published providers fails publication.
 */
function collectRequiresEdges(features: FeatureDesign[], findings: ValidationFinding[]): DeclaredEdge[] {
  const edges: DeclaredEdge[] = [];
  const providersByInterface = new Map<string, FeatureDesign[]>();
  for (const feature of features) {
    for (const interfaceId of feature.providedInterfaceIds) {
      providersByInterface.set(interfaceId, [...(providersByInterface.get(interfaceId) ?? []), feature]);
    }
  }
  for (const feature of features) {
    for (const interfaceId of feature.requiredInterfaceIds) {
      const providers = (providersByInterface.get(interfaceId) ?? []).filter((candidate) => candidate.featureId !== feature.featureId);
      if (providers.length === 1) {
        edges.push({
          kind: 'requires', source: feature.featureId, target: providers[0].featureId,
          declaredBy: feature.featureId, interfaceId,
        });
      } else if (providers.length === 0) {
        if (!feature.externalRequiredInterfaceIds.includes(interfaceId)) findings.push({
          ruleId: 'feature.interface.provider.missing', severity: 'error', sourcePath: feature.sourcePath,
          message: `Required interface "${interfaceId}" has no published provider and no external provider block.`,
          remediation: 'Publish a feature that provides this interface, or add an Interfaces H3 block for it with `- **Provider**: `external:...``.',
        });
      } else {
        findings.push({
          ruleId: 'feature.interface.provider.duplicate', severity: 'error', sourcePath: feature.sourcePath,
          message: `Required interface "${interfaceId}" has ${providers.length} published providers: ${providers.map((provider) => provider.featureId).sort(compareText).join(', ')}.`,
          remediation: 'Ensure exactly one other published feature provides this interface.',
        });
      }
    }
  }
  return edges;
}

/**
 * Merges reciprocal declarations of the same normalized edge into one edge with sorted `declared_by`
 * (FR-003); `relates_to` endpoints are ordered lexically before the merge key is computed so both
 * declaring directions collapse together.
 */
function mergeEdges(raw: DeclaredEdge[]): GraphEdge[] {
  const merged = new Map<string, {kind: EdgeKind; source: string; target: string; interfaceId?: string; declaredBy: Set<string>}>();
  for (const declared of raw) {
    let {source, target} = declared;
    if (declared.kind === 'relates_to' && source > target) [source, target] = [target, source];
    const key = edgeId(declared.kind, source, target, declared.interfaceId);
    const existing = merged.get(key);
    if (existing) existing.declaredBy.add(declared.declaredBy);
    else merged.set(key, {kind: declared.kind, source, target, interfaceId: declared.interfaceId, declaredBy: new Set([declared.declaredBy])});
  }
  return [...merged.entries()]
    .map(([id, edge]) => ({
      id, kind: edge.kind, source: edge.source, target: edge.target,
      ...(edge.interfaceId ? {interface: edge.interfaceId} : {}),
      declared_by: [...edge.declaredBy].sort(compareText),
    }))
    .sort((left, right) => compareText(left.id, right.id));
}

/** Tarjan's algorithm: strongly connected components of a directed graph given as an adjacency map. */
function stronglyConnectedComponents(nodes: string[], adjacency: Map<string, string[]>): string[][] {
  let counter = 0;
  const index = new Map<string, number>();
  const lowlink = new Map<string, number>();
  const onStack = new Set<string>();
  const stack: string[] = [];
  const components: string[][] = [];

  function strongConnect(v: string): void {
    index.set(v, counter);
    lowlink.set(v, counter);
    counter += 1;
    stack.push(v);
    onStack.add(v);
    for (const w of adjacency.get(v) ?? []) {
      if (!index.has(w)) {
        strongConnect(w);
        lowlink.set(v, Math.min(lowlink.get(v)!, lowlink.get(w)!));
      } else if (onStack.has(w)) {
        lowlink.set(v, Math.min(lowlink.get(v)!, index.get(w)!));
      }
    }
    if (lowlink.get(v) === index.get(v)) {
      const component: string[] = [];
      let member: string;
      do {
        member = stack.pop()!;
        onStack.delete(member);
        component.push(member);
      } while (member !== v);
      components.push(component);
    }
  }

  for (const node of nodes) if (!index.has(node)) strongConnect(node);
  return components;
}

/**
 * Per-family acyclicity (FR-005): each directional family (`composes`, `refines`, `depends_on`,
 * `requires`) must be acyclic. Every feature on a cycle gets one finding naming the family and every
 * other member of that cycle.
 */
function findCycles(edges: GraphEdge[], sourcePathById: Map<string, string>): ValidationFinding[] {
  const findings: ValidationFinding[] = [];
  for (const kind of DIRECTIONAL_EDGE_KINDS) {
    const nodes = new Set<string>();
    const adjacency = new Map<string, string[]>();
    for (const edge of edges) {
      if (edge.kind !== kind) continue;
      nodes.add(edge.source);
      nodes.add(edge.target);
      adjacency.set(edge.source, [...(adjacency.get(edge.source) ?? []), edge.target]);
    }
    for (const component of stronglyConnectedComponents([...nodes].sort(compareText), adjacency)) {
      if (component.length < 2) continue;
      const members = [...component].sort(compareText);
      for (const member of members) findings.push({
        ruleId: 'feature.relation.cycle', severity: 'error', sourcePath: sourcePathById.get(member),
        message: `Feature "${member}" is on a ${kind} cycle with ${members.filter((id) => id !== member).join(', ')}.`,
        remediation: `Break the cycle by removing or reversing one ${kind} relation among ${members.join(', ')}.`,
      });
    }
  }
  return findings;
}

/** Every edge derivable from the validated registry, shared by `deriveFeatureGraph` and `findGraphProblems`. */
function deriveEdges(features: FeatureDesign[], findings: ValidationFinding[]): GraphEdge[] {
  const raw = [...collectRelationEdges(features, findings), ...collectRequiresEdges(features, findings)];
  return mergeEdges(raw);
}

/**
 * Derives Feature Graph 1 (FR-001, FR-006) from an already-validated registry: sorted module and
 * feature nodes, deterministic typed and interface-derived edges, aggregate counts, and a source
 * digest over every contributing feature's stable ID and content hash. Never throws on a relation or
 * interface problem — publication rejects those beforehand via `findGraphProblems`.
 */
export function deriveFeatureGraph(registry: ContentRegistry, generatorVersion: string): FeatureGraph {
  const modules = [...registry.documents.filter(isModule)].sort((left, right) => compareText(left.moduleId, right.moduleId));
  const features = [...registry.documents.filter(isFeature)].sort((left, right) => compareText(left.featureId, right.featureId));
  const ignoredFindings: ValidationFinding[] = [];
  const edges = deriveEdges(features, ignoredFindings);

  const edgesByKind = Object.fromEntries(ALL_EDGE_KINDS.map((kind) => [kind, 0])) as FeatureGraph['counts']['edges_by_kind'];
  for (const edge of edges) edgesByKind[edge.kind] += 1;

  const digestInput = features.map((feature) => `${feature.featureId}\0${feature.sourceSha256}`).sort(compareText).join('\n');

  return {
    schema_version: 1,
    generator: {name: 'concorde-docsite', version: generatorVersion},
    source_digest: sha256Hex(digestInput),
    modules: modules.map((module) => ({
      id: module.moduleId, title: module.title, ...(module.parentId ? {parent: module.parentId} : {}), route: module.route,
    })),
    features: features.map((feature) => ({
      id: feature.featureId, title: feature.title, module: feature.moduleId, outcome: feature.outcome,
      status: feature.status, route: feature.route, source_path: feature.sourcePath, source_sha256: feature.sourceSha256,
    })),
    edges,
    counts: {features: features.length, modules: modules.length, edges_by_kind: edgesByKind},
  };
}

/**
 * Publication-time findings for the Feature Graph (FR-002, FR-004, FR-005): unknown relations,
 * self-references, missing/duplicate interface providers, and directional-family cycles. Endpoint
 * resolution stays in `feature.related.unresolved` (registry.ts); this only covers what the graph
 * itself derives.
 */
export function findGraphProblems(registry: ContentRegistry): ValidationFinding[] {
  const features = registry.documents.filter(isFeature);
  const findings: ValidationFinding[] = [];
  const edges = deriveEdges(features, findings);
  const sourcePathById = new Map(features.map((feature) => [feature.featureId, feature.sourcePath]));
  findings.push(...findCycles(edges, sourcePathById));
  return findings;
}
