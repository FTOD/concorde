import {useBaseUrlUtils} from '@docusaurus/useBaseUrl';

import type {ContentPage} from '../../plugins/concorde-content/types';

export default function FeatureDiagrams({page}: {page: ContentPage}) {
  const {withBaseUrl} = useBaseUrlUtils();
  if (!page.diagrams?.length) return null;
  const documentation = page.kind === 'project-document';
  const headingId = documentation ? 'documentation-diagrams-heading' : 'feature-diagrams-heading';
  return (
    <section className="featureDiagrams" aria-labelledby={headingId}>
      <div className="featureDiagrams__intro">
        <p className="featureDiagrams__eyebrow">{documentation ? 'Documentation diagrams' : 'Feature diagrams'}</p>
        <h2 id={headingId}>{documentation ? 'Explore this guide visually' : 'Explore component involvement'}</h2>
        <p>{documentation
          ? 'These interactive views explain the guide; maintained Markdown remains the textual reference.'
          : 'These interactive views supplement the feature text; the design and contracts remain authoritative.'}</p>
      </div>
      <div className="featureDiagrams__list">
        {page.diagrams.map((diagram, index) => {
          const diagramHeadingId = `${documentation ? 'documentation' : 'feature'}-diagram-${index + 1}`;
          const diagramUrl = withBaseUrl(diagram.route);
          return (
            <article className="featureDiagram" key={diagram.source} aria-labelledby={diagramHeadingId}>
              <div className="featureDiagram__heading">
                <div>
                  <p className="featureDiagram__kind">{documentation ? diagram.kind : `${diagram.role} · ${diagram.kind}`} diagram</p>
                  <h3 id={diagramHeadingId}>{diagram.title}</h3>
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
