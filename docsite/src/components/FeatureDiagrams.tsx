import {useBaseUrlUtils} from '@docusaurus/useBaseUrl';

import type {ContentPage} from '../../plugins/concorde-content/types';

export default function FeatureDiagrams({page}: {page: ContentPage}) {
  const {withBaseUrl} = useBaseUrlUtils();
  if (!page.diagrams?.length) return null;
  return (
    <section className="featureDiagrams" aria-labelledby="feature-diagrams-heading">
      <div className="featureDiagrams__intro">
        <p className="featureDiagrams__eyebrow">Feature diagrams</p>
        <h2 id="feature-diagrams-heading">Explore component involvement</h2>
        <p>These interactive views supplement the feature text; the design and contracts remain authoritative.</p>
      </div>
      <div className="featureDiagrams__list">
        {page.diagrams.map((diagram, index) => {
          const headingId = `feature-diagram-${index + 1}`;
          const diagramUrl = withBaseUrl(diagram.route);
          return (
            <article className="featureDiagram" key={diagram.source} aria-labelledby={headingId}>
              <div className="featureDiagram__heading">
                <div>
                  <p className="featureDiagram__kind">{diagram.role} · {diagram.kind} diagram</p>
                  <h3 id={headingId}>{diagram.title}</h3>
                </div>
                <a href={diagramUrl} target="_blank" rel="noreferrer">Open full view</a>
              </div>
              <iframe
                className="featureDiagram__frame"
                src={diagramUrl}
                title={`${diagram.title} for ${page.title}`}
                loading="lazy"
                sandbox="allow-downloads allow-scripts"
              />
              <p className="featureDiagram__source">
                Source: <code>{diagram.source}</code> · SHA-256 <code>{diagram.sourceSha256.slice(0, 12)}…</code>
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
