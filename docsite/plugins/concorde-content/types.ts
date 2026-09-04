export type CollectionId = 'architecture' | 'features';
export type ContentKind = 'module-architecture' | 'feature-design';
export type SourceState = 'discovered' | 'parsed' | 'validated' | 'mapped' | 'rendered' | 'invalid';

export interface SourceCollection {
  id: CollectionId;
  sourceBase: 'specs';
  routeBase: '/architecture' | '/features';
  include: string[];
  contentKind: ContentKind;
}

export interface SourceLocation {line: number; column: number}

export type LinkKind = 'anchor' | 'included-source' | 'excluded-source' | 'external' | 'asset';

export interface LinkReference {
  rawTarget: string;
  kind: LinkKind;
  targetSourcePath?: string;
  targetRoute?: string;
  fragment?: string;
  location?: SourceLocation;
}

export interface SourceDocument {
  collectionId: CollectionId;
  contentKind: ContentKind;
  sourcePath: string;
  realPath: string;
  title: string;
  sourceSha256: string;
  frontMatter: Record<string, unknown>;
  content: string;
  links: LinkReference[];
  state: SourceState;
  route: string;
  /** Disposable renderer path; never a canonical source locator. */
  stagedPath?: string;
  sidebarLabel?: string;
  sidebarPosition?: number;
  slug?: string;
}

/**
 * The shared related-feature relation vocabulary (Ontology FR-036/FR-037). The first seven values are
 * the only ones a maintainer may write in front matter `related_features`; `requires` never appears
 * there and is instead derived from interface ownership. Inverse forms (`composed_by`, `refined_by`,
 * `depended_on_by`) normalize to their forward kind during Feature Graph derivation.
 */
export type RelationKind =
  | 'composes' | 'refines' | 'depends_on'
  | 'composed_by' | 'refined_by' | 'depended_on_by'
  | 'relates_to' | 'requires';

/** Closed Profile 7 evidence set carried by feature front matter `evidence_status`. */
export const EVIDENCE_STATUSES = ['unknown', 'partial', 'verified', 'disagrees'] as const;
export type EvidenceStatus = (typeof EVIDENCE_STATUSES)[number];

export interface FeatureRelationEntry {
  id: string;
  relation: RelationKind;
}

export interface FeatureRelation {
  featureId: string;
  title: string;
  outcome: string;
  evidenceStatus: EvidenceStatus;
  route: string;
  relation: RelationKind;
}

export interface FeatureDesign extends SourceDocument {
  collectionId: 'features';
  contentKind: 'feature-design';
  featureId: string;
  kind: 'feature';
  moduleId: string;
  moduleRoute?: string;
  /** Raw front matter `evidence_status`; validation constrains it to EVIDENCE_STATUSES. */
  evidenceStatus: string;
  outcome: string;
  relatedFeatureIds: string[];
  relatedFeatureEntries: FeatureRelationEntry[];
  relatedFeatures: FeatureRelation[];
  /** Stable interface IDs this feature's front matter declares under `interfaces.provided`. */
  providedInterfaceIds: string[];
  /** Stable interface IDs this feature's front matter declares under `interfaces.required`. */
  requiredInterfaceIds: string[];
  /**
   * Required interface IDs whose body has an Interfaces H3 block naming that interface with a
   * `**Provider**: `external:...`` line; these never derive a `requires` edge and never fail
   * publication for lacking a published provider.
   */
  externalRequiredInterfaceIds: string[];
}

export type DiagramKind = 'architecture' | 'workflow' | 'sequence' | 'dataflow' | 'lifecycle';

export interface ModuleDiagram {
  source: string;
  sourceSha256: string;
  kind: DiagramKind;
  title: string;
  route: string;
}

export interface ModuleArchitecture extends SourceDocument {
  collectionId: 'architecture';
  contentKind: 'module-architecture';
  moduleId: string;
  kind: 'module';
  parentId?: string;
  moduleIds: string[];
  featureIds: string[];
  architectureDiagrams: ModuleDiagram[];
  unpublishableDiagrams?: string[];
}

export interface DiagramDeclaration {
  ownerPath: string;
  sourcePath: string;
  absoluteSourcePath: string;
  outputPath: string;
  absoluteOutputPath: string;
  outputFromGenerated: string;
  kind: DiagramKind;
  title: string;
}

export interface DiagramDeliveryReceipt {
  sourcePath: string;
  outputPath: string;
  kind: DiagramKind;
  sourceSha256: string;
  sourceBytes: number;
  artifactSha256: string;
  artifactBytes: number;
  checksPassed: 9;
  checkCount: 9;
  profile: 'showcase';
  compositionStatus: 'pass';
  errors: 0;
  warnings: 0;
}

export interface DiagramDeliverySet {
  generator: {name: 'archify'; version: '2.16.0-dev.0'};
  receipts: DiagramDeliveryReceipt[];
}

export interface NavigationEntry {
  section: 'Architecture' | 'Features';
  label: string;
  parentRoute?: string;
}

export interface ContentPage {
  kind: ContentKind;
  sourcePath: string;
  sourceSha256: string;
  route: string;
  title: string;
  navigation: NavigationEntry;
  links: Array<{targetSourcePath: string; targetRoute: string}>;
  moduleId?: string;
  parentId?: string;
  architectureDiagrams?: ModuleDiagram[];
  featureId?: string;
  moduleRoute?: string;
  evidenceStatus?: EvidenceStatus;
  relatedFeatures?: FeatureRelation[];
}

export interface ExcludedSource {
  sourcePath: string;
  reason: 'temporal-attempt' | 'non-publication-source' | 'legacy-source-profile';
}

export interface ValidationFinding {
  ruleId: string;
  severity: 'error';
  sourcePath?: string;
  location?: SourceLocation;
  message: string;
  remediation: string;
}

/** Edge kinds that can appear in a derived Feature Graph 1 document (inverse forms already normalized). */
export type EdgeKind = 'composes' | 'refines' | 'depends_on' | 'relates_to' | 'requires';

export interface FeatureGraphCounts {
  features: number;
  modules: number;
  edges_by_kind: Record<EdgeKind, number>;
}

export interface GraphModule {
  id: string;
  title: string;
  parent?: string;
  route: string;
}

export interface GraphFeature {
  id: string;
  title: string;
  module: string;
  outcome: string;
  /** The feature's evidence status; Feature Graph 1 publishes it under the `status` key. */
  status: string;
  route: string;
  source_path: string;
  source_sha256: string;
}

export interface GraphEdge {
  id: string;
  kind: EdgeKind;
  source: string;
  target: string;
  interface?: string;
  declared_by: string[];
}

/** Feature Graph 1: the deterministic, sorted JSON projection published as `feature-graph.json`. */
export interface FeatureGraph {
  schema_version: 1;
  generator: {name: string; version: string};
  source_digest: string;
  modules: GraphModule[];
  features: GraphFeature[];
  edges: GraphEdge[];
  counts: FeatureGraphCounts;
}

export interface BuildManifest {
  schemaVersion: 12;
  generator: {
    name: 'concorde-docsite';
    version: string;
    docusaurusVersion: string;
  };
  collections: Array<Pick<SourceCollection, 'id' | 'sourceBase' | 'routeBase' | 'include'>>;
  pages: ContentPage[];
  excludedSources: ExcludedSource[];
  routeInventory: string[];
  featureGraph: 'feature-graph.json';
  featureGraphCounts: FeatureGraphCounts;
  validation: {
    status: 'passed';
    checks: Array<{name: string; status: 'passed'}>;
  };
}

export interface ContentRegistry {
  projectRoot: string;
  collections: SourceCollection[];
  documents: SourceDocument[];
  excludedSources: ExcludedSource[];
  findings: ValidationFinding[];
}

export interface ConcordeContentOptions {projectRoot?: string}
