import type {ContentPage} from '../../plugins/concorde-content/types';

export default function ContentProvenance({page}: {page: ContentPage}) {
  return (
    <aside className="provenance" aria-label="Content provenance">
      <span className="provenance__kind">
        {page.kind === 'feature-specification'
          ? page.featureLevel === 'subfeature' ? 'Sub-feature specification' : 'Feature specification'
          : page.kind === 'feature-design'
            ? page.featureLevel === 'subfeature' ? 'Sub-feature design' : 'Feature design'
          : page.kind === 'architecture-source'
            ? `Architecture ${page.architectureKind ?? 'source'}`
            : 'Project documentation'}
      </span>
      {page.featureId && <code>{page.featureId}</code>}
      {page.architectureId && <code>{page.architectureId}</code>}
      {page.moduleId && <span>Owner: <code>{page.moduleId}</code></span>}
      {page.parentId && <span>Parent: <code>{page.parentId}</code></span>}
      {page.parentFeatureId && <span>Parent feature: <code>{page.parentFeatureId}</code></span>}
      {page.status && <span className="provenance__status">Status: {page.status}</span>}
      <span>Canonical source: <code>{page.sourcePath}</code></span>
    </aside>
  );
}
