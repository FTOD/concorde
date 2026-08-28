export type CollectionId = 'architecture' | 'docs' | 'feature-tldrs' | 'features' | 'feature-designs';
export type ContentKind =
  | 'architecture-source'
  | 'module-design'
  | 'project-document'
  | 'feature-tldr'
  | 'feature-specification'
  | 'feature-design';
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
  sidebarLabel?: string;
  sidebarPosition?: number;
  slug?: string;
}

export interface ProjectDocument extends SourceDocument {
  collectionId: 'docs';
  contentKind: 'project-document';
}

export type FeatureLevel = 'feature' | 'subfeature';

/** Identity and navigation shared by a feature root's three pages, taken from the sibling `spec.md` front matter. */
export interface FeaturePageContext {
  featureId?: string;
  moduleId?: string;
  featureLevel?: FeatureLevel;
  parentFeatureId?: string;
  /** The parent feature's TL;DR landing route. */
  parentFeatureRoute?: string;
  subfeatures?: FeatureRelation[];
  siblings?: FeatureRelation[];
}

/** A feature root's landing page (`tldr.md`), published at `/features/<root>` and paired with its sibling `spec.md`. */
export interface FeatureTldr extends SourceDocument, FeaturePageContext {
  collectionId: 'feature-tldrs';
  contentKind: 'feature-tldr';
  status?: string;
  /** The diagrams declared by the paired specification, embedded on this landing page. */
  diagrams?: FeatureDiagram[];
  /** Companion link: the route of the paired feature specification page. */
  specificationRoute?: string;
  /** Companion link: the route of the paired feature design reference page. */
  designRoute?: string;
}

/** A feature root's accepted design reference (`design.md` beside `spec.md`), paired with its sibling `spec.md`. */
export interface FeatureDesign extends SourceDocument, FeaturePageContext {
  collectionId: 'feature-designs';
  contentKind: 'feature-design';
  /** Companion link: the route of the paired TL;DR landing page. */
  tldrRoute?: string;
  /** Companion link: the route of the paired feature specification page. */
  specificationRoute?: string;
}

export interface FeatureSpecification extends SourceDocument {
  collectionId: 'features';
  contentKind: 'feature-specification';
  featureId: string;
  kind: 'feature';
  moduleId: string;
  status: string;
  featureDirectory: string;
  /** The feature's landing route (`/features/<root>`), owned by the sibling `tldr.md`; parent, child, and sibling navigation targets it. */
  landingRoute: string;
  diagrams: FeatureDiagram[];
  featureLevel: FeatureLevel;
  parentFeatureId?: string;
  parentFeatureRoute?: string;
  outcome: string;
  subfeatureIds: string[];
  subfeatures: FeatureRelation[];
  siblings: FeatureRelation[];
  /** Companion link: the route of the paired TL;DR landing page. */
  tldrRoute?: string;
  /** Companion link: the route of the paired feature design reference page. */
  designRoute?: string;
}

export interface FeatureRelation {
  featureId: string;
  title: string;
  outcome: string;
  status: string;
  /** The related feature's TL;DR landing route. */
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
  architectureViewSource?: string;
  architectureViewSha256?: string;
  architectureViewRoute?: string;
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
  diagrams?: FeatureDiagram[];
  tldrRoute?: string;
  specificationRoute?: string;
  designRoute?: string;
  architectureId?: string;
  architectureKind?: ArchitectureKind;
  parentId?: string;
  architectureViewSource?: string;
  architectureViewSha256?: string;
  architectureViewRoute?: string;
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
  schemaVersion: 6;
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
