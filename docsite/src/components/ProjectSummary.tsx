import Link from '@docusaurus/Link';

export interface ProjectSummaryProps {architecture: number; docs: number; features: number}

export default function ProjectSummary({architecture, docs, features}: ProjectSummaryProps) {
  return (
    <section className="projectSummary" aria-labelledby="project-content-heading">
      <h2 id="project-content-heading">One project, two source roots, three views</h2>
      <div className="projectSummary__grid">
        <Link className="projectSummary__card" to="/architecture">
          <strong>Architecture</strong><span>{architecture} maintained {architecture === 1 ? 'source' : 'sources'}</span>
        </Link>
        <Link className="projectSummary__card" to="/docs">
          <strong>Documentation</strong><span>{docs} maintained {docs === 1 ? 'page' : 'pages'}</span>
        </Link>
        <Link className="projectSummary__card" to="/features">
          <strong>Features</strong><span>{features} canonical {features === 1 ? 'feature' : 'features'}, each opening on its TL;DR</span>
        </Link>
      </div>
    </section>
  );
}
