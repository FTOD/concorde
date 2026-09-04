import Link from '@docusaurus/Link';

import type {ContentPage} from '../../plugins/concorde-content/types';

function formatRelation(relation: string): string {
  return relation.replace(/_/g, ' ');
}

export default function FeatureRelations({page}: {page: ContentPage}) {
  if (!page.relatedFeatures?.length) return null;
  return (
    <nav className="featureRelations" aria-label="Related features">
      <strong>Related features</strong>
      <ol>
        {page.relatedFeatures.map((related) => (
          <li key={related.featureId}>
            <Link to={related.route}>{related.title}</Link> <code>{related.featureId}</code>
            <span className="featureRelations__relation">{formatRelation(related.relation)}</span>
            <span>{related.outcome}</span><small>Evidence: {related.evidenceStatus}</small>
          </li>
        ))}
      </ol>
    </nav>
  );
}
