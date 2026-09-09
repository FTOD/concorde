import Link from '@docusaurus/Link';

import type {ContentPage} from '../../plugins/concorde-content/types';

type Membership = {targetId: string; kind: string; primary: boolean};

function kindLabel(page: ContentPage & {memberships?: Membership[]}): string {
  if (page.memberships) return page.memberships.length > 1 ? 'Shared Spec' : `${page.kind[0].toUpperCase()}${page.kind.slice(1)} Spec`;
  const kind: string = page.kind;
  return kind === 'feature-design' ? 'Direct feature' : kind === 'module-architecture' ? 'Module architecture' : kind[0].toUpperCase()+kind.slice(1)+' Spec';
}

export default function ContentProvenance({page}: {page: ContentPage & {documentId?:string;documentTargets?:string[];mainVisible?:boolean;memberships?:Membership[]}}) {
  return (
    <aside className="provenance" aria-label="Content provenance">
      <span className="provenance__kind">{kindLabel(page)}</span>
      {page.featureId && <code>{page.featureId}</code>}
      {page.moduleId && <span>Owner: {page.moduleRoute
        ? <Link to={page.moduleRoute}><code>{page.moduleId}</code></Link>
        : <code>{page.moduleId}</code>}</span>}
      {page.parentId && <span>Parent: <code>{page.parentId}</code></span>}
      <span>Canonical source: <code>{page.sourcePath}</code></span>
      {page.documentId&&<details><summary>Spec metadata</summary>
        <div>Document: <code>{page.documentId}</code></div>
        <div>Targets: {(page.memberships??[]).map(m=><code key={m.targetId}>{m.targetId}{m.primary?' (main Spec)':''} </code>)}</div>
        <div>Main visibility: {page.mainVisible?'visible':'private'}</div>
      </details>}
    </aside>
  );
}
