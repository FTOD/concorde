import Link from '@docusaurus/Link';

import type {ContentPage} from '../../plugins/concorde-content/types';

function kindLabel(page: ContentPage): string {
  const kind: string = page.kind;
  return kind === 'feature-design' ? 'Direct feature' : kind === 'module-architecture' ? 'Module architecture' : kind[0].toUpperCase()+kind.slice(1)+' Spec';
}

export default function ContentProvenance({page}: {page: ContentPage}) {
  return (
    <aside className="provenance" aria-label="Content provenance">
      <span className="provenance__kind">{kindLabel(page)}</span>
      {page.featureId && <code>{page.featureId}</code>}
      {page.moduleId && <span>Owner: {page.moduleRoute
        ? <Link to={page.moduleRoute}><code>{page.moduleId}</code></Link>
        : <code>{page.moduleId}</code>}</span>}
      {page.parentId && <span>Parent: <code>{page.parentId}</code></span>}
      <span>Canonical source: <code>{page.sourcePath}</code></span>
    </aside>
  );
}
