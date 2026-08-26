import Link from '@docusaurus/Link';

import type {ContentPage} from '../../plugins/concorde-content/types';

export default function FeatureRelations({page}: {page: ContentPage}) {
  if (!page.parentFeatureRoute && !page.subfeatures?.length && !page.siblings?.length) return null;
  return (
    <nav className="featureRelations" aria-label="Feature relationships">
      <strong>{page.featureLevel === 'subfeature' ? 'Sub-feature context' : 'Sub-features'}</strong>
      {page.parentFeatureRoute && (
        <p>Parent: <Link to={page.parentFeatureRoute}><code>{page.parentFeatureId}</code></Link></p>
      )}
      {page.subfeatures?.length ? (
        <ol>
          {page.subfeatures.map((child) => (
            <li key={child.featureId}>
              <Link to={child.route}>{child.title}</Link> <code>{child.featureId}</code>
              <span>{child.outcome}</span><small>Status: {child.status}</small>
            </li>
          ))}
        </ol>
      ) : null}
      {page.siblings?.length ? (
        <p>Siblings: {page.siblings.map((sibling, index) => (
          <span key={sibling.featureId}>{index ? ', ' : ''}<Link to={sibling.route}>{sibling.title}</Link></span>
        ))}</p>
      ) : null}
    </nav>
  );
}
