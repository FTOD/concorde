import type {Page} from '../../plugins/scoped-content/model';

function kindLabel(page: Page): string {
  return page.memberships.length > 1 ? 'Shared Spec' : `${page.kind[0].toUpperCase()}${page.kind.slice(1)} Spec`;
}

export default function ContentProvenance({page}: {page: Page}) {
  return (
    <aside className="provenance" aria-label="Content provenance">
      <span className="provenance__kind">{kindLabel(page)}</span>
      <span>Canonical source: <code>{page.sourcePath}</code></span>
      <details><summary>Spec metadata</summary>
        <div>Document: <code>{page.documentId}</code></div>
        <div>Targets: {page.memberships.map(m => <code key={m.targetId}>{m.targetId}{m.primary ? ' (main Spec)' : ''} </code>)}</div>
        <div>Main visibility: {page.mainVisible ? 'visible' : 'private'}</div>
      </details>
    </aside>
  );
}
