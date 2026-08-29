import Link from '@docusaurus/Link';

import type {ContentPage} from '../../plugins/concorde-content/types';

function kindLabel(page: ContentPage): string {
  const level = page.featureLevel === 'subfeature' ? 'Sub-feature' : 'Feature';
  switch (page.kind) {
    case 'feature-abstract': return `${level} abstract`;
    case 'feature-design': return `${level} design`;
    case 'feature-implementation': return `${level} implementation`;
    case 'module-design': return 'Module design reference';
    case 'architecture-source': return `Architecture ${page.architectureKind ?? 'source'}`;
    default: return 'Project documentation';
  }
}

export default function ContentProvenance({page}: {page: ContentPage}) {
  return (
    <aside className="provenance" aria-label="Content provenance">
      <span className="provenance__kind">{kindLabel(page)}</span>
      {page.featureId && <code>{page.featureId}</code>}
      {page.architectureId && <code>{page.architectureId}</code>}
      {page.moduleId && <span>Owner: {page.moduleRoute
        ? <Link to={page.moduleRoute}><code>{page.moduleId}</code></Link>
        : <code>{page.moduleId}</code>}</span>}
      {page.parentId && <span>Parent: <code>{page.parentId}</code></span>}
      {page.parentFeatureId && <span>Parent feature: <code>{page.parentFeatureId}</code></span>}
      {page.status && <span className="provenance__status">Status: {page.status}</span>}
      <span>Canonical source: <code>{page.sourcePath}</code></span>
    </aside>
  );
}
