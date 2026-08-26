export type CollectionId = 'architecture' | 'docs' | 'features' | 'feature-designs';
export type ContentKind = 'architecture-source' | 'project-document' | 'feature-specification' | 'feature-design';
export type SourceState = 'discovered' | 'parsed' | 'validated' | 'mapped' | 'rendered' | 'invalid';

export interface SourceCollection {
  id: CollectionId;
  sourceBase: 'docs' | 'specs';
  routeBase: '/architecture' | '/docs' | '/features';
  include: string[];
  contentKind: ContentKind;
}

export interface SourceLocation {
  line: number;
  column: number;
}

export type LinkKind =
  | 'anchor'
  | 'included-source'
  | 'excluded-source'
  | 'external'
  | 'asset';

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
  sourcePath: string;
  realPath: string;
  title: string;
  sourceSha256: string;
  frontMatter: Record<string, unknown>;
  content: string;
  links: LinkReference[];
  state: SourceState;
  route: string;
  sidebarLabel?: string;
  sidebarPosition?: number;
  slug?: string;
}

export interface ProjectDocument extends SourceDocument {
  collectionId: 'docs';
}

export interface FeatureDesign extends SourceDocument {
  collectionId: 'feature-designs';
  featureId?: string;
  moduleId?: string;
  featureLevel?: 'feature' | 'subfeature';
  parentFeatureId?: string;
  parentFeatureRoute?: string;
  subfeatures?: FeatureRelation[];
  siblings?: FeatureRelation[];
}

export interface FeatureSpecification extends SourceDocument {
  collectionId: 'features';
  featureId: string;
  kind: 'feature';
  moduleId: string;
  status: string;
  featureDirectory: string;
  diagrams: FeatureDiagram[];
  featureLevel: 'feature' | 'subfeature';
  parentFeatureId?: string;
  parentFeatureRoute?: string;
  outcome: string;
  subfeatureIds: string[];
  subfeatures: FeatureRelation[];
  siblings: FeatureRelation[];
}

export interface FeatureRelation {
  featureId: string;
  title: string;
  outcome: string;
  status: string;
  route: string;
}

export interface FeatureDiagram {
  source: string;
  sourceSha256: string;
  role: 'core' | 'supplemental';
  kind: 'architecture' | 'workflow' | 'sequence' | 'dataflow' | 'lifecycle';
  scenarios: string[];
  title: string;
  route: string;
}

export type ArchitectureKind = 'contract' | 'feature' | 'module';

export interface ArchitectureSource extends SourceDocument {
  collectionId: 'architecture';
  architectureId: string;
  architectureKind: ArchitectureKind;
  moduleId?: string;
  parentId?: string;
  architectureViewSource?: string;
  architectureViewSha256?: string;
  architectureViewRoute?: string;
}

export interface NavigationEntry {
  section: 'Architecture' | 'Documentation' | 'Features';
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
  featureId?: string;
  moduleId?: string;
  status?: string;
  featureLevel?: 'feature' | 'subfeature';
  parentFeatureId?: string;
  parentFeatureRoute?: string;
  subfeatures?: FeatureRelation[];
  siblings?: FeatureRelation[];
  diagrams?: FeatureDiagram[];
  architectureId?: string;
  architectureKind?: ArchitectureKind;
  parentId?: string;
  architectureViewSource?: string;
  architectureViewSha256?: string;
  architectureViewRoute?: string;
}

export interface ExcludedSource {
  sourcePath: string;
  reason: 'not-canonical-feature-artifact';
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
  schemaVersion: 4;
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

export interface ConcordeContentOptions {
  projectRoot?: string;
  manifestSchema?: string;
}
