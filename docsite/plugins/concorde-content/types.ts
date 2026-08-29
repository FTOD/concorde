export type CollectionId = 'home' | 'architecture' | 'docs' | 'feature-abstracts' | 'features' | 'feature-implementations';
export type ContentKind =
  | 'architecture-source'
  | 'module-design'
  | 'project-document'
  | 'feature-abstract'
  | 'feature-design'
  | 'feature-implementation';
export type SourceState = 'discovered' | 'parsed' | 'validated' | 'mapped' | 'rendered' | 'invalid';

export interface SourceCollection {
  id: CollectionId;
  sourceBase: '.' | 'docs' | 'specs';
  routeBase: '/' | '/architecture' | '/docs' | '/features';
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
  /**
   * Disposable renderer path. Feature routes use stable identity and explicit containment; their
   * generated sidebar independently groups them by owning module hierarchy.
   */
  stagedPath?: string;
  sidebarLabel?: string;
  sidebarPosition?: number;
  slug?: string;
}

export interface ProjectDocument extends SourceDocument {
  collectionId: 'home' | 'docs';
  contentKind: 'project-document';
}

export type FeatureLevel = 'feature' | 'subfeature';

/** Identity and navigation shared by a feature root's three pages, taken from design.md front matter. */
export interface FeaturePageContext {
  featureId?: string;
  moduleId?: string;
  /** Architecture cross-link for the level at which the feature is specified. */
  moduleRoute?: string;
  featureLevel?: FeatureLevel;
  parentFeatureId?: string;
  /** The parent feature's abstract landing route. */
  parentFeatureRoute?: string;
  subfeatures?: FeatureRelation[];
  siblings?: FeatureRelation[];
  /** Adjacent-level refinement targets; relationships, never containment parents. */
  refinements?: FeatureRelation[];
}

/** A feature root's abstract.md landing page, paired with design.md. */
export interface FeatureAbstract extends SourceDocument, FeaturePageContext {
  collectionId: 'feature-abstracts';
  contentKind: 'feature-abstract';
  status?: string;
  /** The diagrams declared by the paired design, embedded on this landing page. */
  diagrams?: FeatureDiagram[];
  /** Companion link: the route of the paired feature design page. */
  designRoute?: string;
  /** Companion link: the route of the paired feature implementation page. */
  implementationRoute?: string;
}

/** A feature root's accepted implementation.md, paired with design.md. */
export interface FeatureImplementation extends SourceDocument, FeaturePageContext {
  collectionId: 'feature-implementations';
  contentKind: 'feature-implementation';
  /** Companion link: the route of the paired abstract landing page. */
  abstractRoute?: string;
  /** Companion link: the route of the paired feature design page. */
  designRoute?: string;
}

export interface FeatureDesign extends SourceDocument {
  collectionId: 'features';
  contentKind: 'feature-design';
  featureId: string;
  kind: 'feature';
  moduleId: string;
  moduleRoute?: string;
  status: string;
  featureDirectory: string;
  /** The feature landing route, owned by sibling abstract.md. */
  landingRoute: string;
  diagrams: FeatureDiagram[];
  featureLevel: FeatureLevel;
  parentFeatureId?: string;
  parentFeatureRoute?: string;
  outcome: string;
  subfeatureIds: string[];
  subfeatures: FeatureRelation[];
  siblings: FeatureRelation[];
  refinementIds: string[];
  refinements: FeatureRelation[];
  /** Companion link: the route of the paired abstract landing page. */
  abstractRoute?: string;
  /** Companion link: the route of the paired feature implementation page. */
  implementationRoute?: string;
}

export interface FeatureRelation {
  featureId: string;
  title: string;
  outcome: string;
  status: string;
  /** The related feature's abstract landing route. */
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

export type DiagramKind = FeatureDiagram['kind'];

/** One module-owned Archify diagram discovered beneath `<module>/architecture/diagrams/`. */
export interface ModuleDiagram {
  source: string;
  sourceSha256: string;
  kind: DiagramKind;
  title: string;
  route: string;
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
  role?: FeatureDiagram['role'];
  scenarios?: string[];
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

export type ArchitectureKind = 'contract' | 'feature' | 'module';

export interface ArchitectureSource extends SourceDocument {
  collectionId: 'architecture';
  contentKind: 'architecture-source';
  architectureId: string;
  architectureKind: ArchitectureKind;
  moduleId?: string;
  parentId?: string;
  /** Module summaries: every diagram beneath the module's `architecture/diagrams/`, in source order. */
  architectureDiagrams?: ModuleDiagram[];
  /** Module diagram sources that could not be mapped to a generated site artifact. */
  unpublishableDiagrams?: string[];
  /** Companion link on module summaries: the route of the sibling `design.md` reference page. */
  designReferenceRoute?: string;
}

/** A module design reference (`design.md` beside `module.md`), published as its own Architecture page. */
export interface ModuleDesign extends SourceDocument {
  collectionId: 'architecture';
  contentKind: 'module-design';
  /** Project-relative path of the sibling `module.md` this reference belongs to. */
  moduleSourcePath: string;
  moduleId?: string;
  /** Companion link: the route of the module summary page. */
  moduleRoute?: string;
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
  featureLevel?: FeatureLevel;
  parentFeatureId?: string;
  parentFeatureRoute?: string;
  subfeatures?: FeatureRelation[];
  siblings?: FeatureRelation[];
  refinements?: FeatureRelation[];
  diagrams?: FeatureDiagram[];
  abstractRoute?: string;
  designRoute?: string;
  implementationRoute?: string;
  architectureId?: string;
  architectureKind?: ArchitectureKind;
  parentId?: string;
  architectureDiagrams?: ModuleDiagram[];
  designReferenceRoute?: string;
  moduleRoute?: string;
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
  schemaVersion: 9;
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
