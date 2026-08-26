import useBaseUrl from '@docusaurus/useBaseUrl';

import type {ContentPage} from '../../plugins/concorde-content/types';

export default function ArchitectureView({page}: {page: ContentPage}) {
  const architectureViewUrl = useBaseUrl(page.architectureViewRoute ?? '');
  if (!page.architectureViewRoute || !page.architectureViewSource) return null;
  return (
    <section className="architectureView" aria-labelledby="architecture-view-heading">
      <div className="architectureView__heading">
        <div>
          <p className="architectureView__eyebrow">Bounded architecture view</p>
          <h2 id="architecture-view-heading">Explore this architectural level</h2>
        </div>
        <a href={architectureViewUrl} target="_blank" rel="noreferrer">Open full view</a>
      </div>
      <iframe
        className="architectureView__frame"
        src={architectureViewUrl}
        title={`Interactive architecture view for ${page.title}`}
        loading="lazy"
        sandbox="allow-downloads allow-scripts"
      />
      <p className="architectureView__source">
        Structural source: <code>{page.architectureViewSource}</code>
      </p>
    </section>
  );
}
