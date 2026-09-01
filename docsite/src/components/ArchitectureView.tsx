import {useBaseUrlUtils} from '@docusaurus/useBaseUrl';

import type {ContentPage} from '../../plugins/concorde-content/types';

/** The module's own Archify diagrams (`<module>/diagrams/*.json`), embedded in stable source order. */
export default function ArchitectureView({page}: {page: ContentPage}) {
  const {withBaseUrl} = useBaseUrlUtils();
  if (!page.architectureDiagrams?.length) return null;
  return (
    <section className="architectureView" aria-labelledby="architecture-view-heading">
      <div className="architectureView__heading">
        <div>
          <p className="architectureView__eyebrow">Bounded architecture views</p>
          <h2 id="architecture-view-heading">Explore this architectural level</h2>
        </div>
      </div>
      {page.architectureDiagrams.map((diagram, index) => {
        const diagramUrl = withBaseUrl(diagram.route);
        const headingId = `architecture-diagram-${index + 1}`;
        return (
          <article className="architectureDiagram" key={diagram.source} aria-labelledby={headingId}>
            <div className="architectureView__heading">
              <div>
                <p className="architectureView__eyebrow">{diagram.kind} diagram</p>
                <h3 id={headingId}>{diagram.title}</h3>
              </div>
              <a href={diagramUrl} target="_blank" rel="noreferrer">Open full view</a>
            </div>
            <iframe
              className="architectureView__frame"
              src={diagramUrl}
              title={`Interactive architecture view for ${page.title}: ${diagram.title}`}
              loading="lazy"
              sandbox="allow-downloads allow-scripts"
            />
            <p className="architectureView__source">
              Structural source: <code>{diagram.source}</code> · SHA-256 <code>{diagram.sourceSha256.slice(0, 12)}…</code>
            </p>
          </article>
        );
      })}
    </section>
  );
}
