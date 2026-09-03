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

export interface FeatureRelation {
  featureId: string;
  title: string;
  outcome: string;
  status: string;
  route: string;
}

export interface FeatureDesign extends SourceDocument {
  collectionId: 'features';
  contentKind: 'feature-design';
  featureId: string;
  kind: 'feature';
  moduleId: string;
  moduleRoute?: string;
  status: string;
  outcome: string;
  relatedFeatureIds: string[];
  relatedFeatures: FeatureRelation[];
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
  status?: string;
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

export interface BuildManifest {
  schemaVersion: 10;
  generator: {
    name: 'concorde-docsite';
    version: string;
    docusaurusVersion: string;
  };
  collections: Array<Pick<SourceCollection, 'id' | 'sourceBase' | 'routeBase' | 'include'>>;
  pages: ContentPage[];
  excludedSources: ExcludedSource[];
  routeInventory: string[];
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
