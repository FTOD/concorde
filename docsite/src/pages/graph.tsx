import {useMemo, useState} from 'react';

import Head from '@docusaurus/Head';
import Link from '@docusaurus/Link';
import {usePluginData} from '@docusaurus/useGlobalData';
import Layout from '@theme/Layout';

import type {EdgeKind, FeatureGraph as FeatureGraphDocument} from '../../plugins/concorde-content/types';
import FeatureGraph from '../components/FeatureGraph';

interface GlobalData {featureGraph: FeatureGraphDocument}

const EDGE_KINDS: EdgeKind[] = ['composes', 'refines', 'depends_on', 'relates_to', 'requires'];
const DEFAULT_VISIBLE_KINDS: EdgeKind[] = ['requires', 'composes', 'refines', 'depends_on'];

function formatKind(kind: string): string {
  return kind.replace(/_/g, ' ');
}

/**
 * A visitor who opens this page's static file directly (a raw `graph.html` URL — from a bookmark, a
 * search result, or a plain static host with no clean-URL rewriting) lands with `location.pathname`
 * literally ending in `.html`, one character off from the extensionless path Docusaurus's client
 * router registers this route under. React Router's hydration then fails to match the current
 * location to this route, and the client falls back to inserting a second, freshly client-rendered
 * copy of the page next to the untouched server-rendered one instead of reconciling in place — with
 * nothing logged to explain it. Normalizing the URL before the router reads it (synchronously, before
 * the deferred client bundle runs) avoids the mismatch entirely; navigating via `/graph` (what every
 * in-site link and a properly configured static host such as GitHub Pages both produce) never hits
 * this at all.
 */
const NORMALIZE_HTML_URL_SCRIPT = `(function () {
  if (window.location.pathname.endsWith('/graph.html')) {
    window.history.replaceState(null, '', window.location.pathname.slice(0, -'.html'.length) + window.location.search + window.location.hash);
  }
})();`;

export default function FeatureGraphPage() {
  const data = usePluginData('concorde-content') as unknown as GlobalData;
  const graph = data.featureGraph;

  const [visibleKinds, setVisibleKinds] = useState<Set<EdgeKind>>(new Set(DEFAULT_VISIBLE_KINDS));
  const [visibleModules, setVisibleModules] = useState<Set<string>>(new Set(graph.modules.map((module) => module.id)));
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState<string | undefined>(undefined);

  const routeById = useMemo(() => new Map(graph.features.map((feature) => [feature.id, feature.route])), [graph]);

  const filteredFeatures = useMemo(() => {
    const query = search.trim().toLowerCase();
    return graph.features.filter((feature) =>
      visibleModules.has(feature.module) &&
      (!query || feature.id.toLowerCase().includes(query) || feature.title.toLowerCase().includes(query)));
  }, [graph, visibleModules, search]);

  const filteredFeatureIds = useMemo(() => new Set(filteredFeatures.map((feature) => feature.id)), [filteredFeatures]);

  const filteredModules = useMemo(() => graph.modules.filter((module) =>
    visibleModules.has(module.id) && filteredFeatures.some((feature) => feature.module === module.id)), [graph, visibleModules, filteredFeatures]);

  const filteredEdges = useMemo(() => graph.edges.filter((edge) =>
    visibleKinds.has(edge.kind) && filteredFeatureIds.has(edge.source) && filteredFeatureIds.has(edge.target)),
  [graph, visibleKinds, filteredFeatureIds]);

  const selectedFeature = selectedId ? graph.features.find((feature) => feature.id === selectedId) : undefined;
  const effectiveSelectedId = selectedFeature && filteredFeatureIds.has(selectedFeature.id) ? selectedFeature.id : undefined;

  function toggleKind(kind: EdgeKind): void {
    setVisibleKinds((previous) => {
      const next = new Set(previous);
      if (next.has(kind)) next.delete(kind); else next.add(kind);
      return next;
    });
  }

  function toggleModule(moduleId: string): void {
    setVisibleModules((previous) => {
      const next = new Set(previous);
      if (next.has(moduleId)) next.delete(moduleId); else next.add(moduleId);
      return next;
    });
  }

  const isEmpty = graph.features.length === 0;

  return (
    <Layout
      title="Feature Graph"
      description="Every published feature, grouped by module, connected by typed and interface-derived relations."
    >
      <Head>
        {/* react-helmet-async expects a plain string child for <script>, not dangerouslySetInnerHTML;
            it converts that child into the tag's innerHTML itself. */}
        <script>{NORMALIZE_HTML_URL_SCRIPT}</script>
      </Head>
      <main className="container margin-vert--lg featureGraphPage">
        <header>
          <h1>Feature Graph</h1>
          <p>
            Every published feature as a node grouped by its module, connected by typed edges: <code>composes</code>,{' '}
            <code>refines</code>, <code>depends_on</code>, <code>relates_to</code>, and interface-derived{' '}
            <code>requires</code>. Derived from validated feature front matter on every build — never hand-edited.
          </p>
        </header>

        <section aria-labelledby="feature-graph-legend-heading" className="featureGraphLegend">
          <h2 id="feature-graph-legend-heading">Legend</h2>
          <ul>
            <li><span className="featureGraphLegend__swatch featureGraphLegend__swatch--module" /> Module group</li>
            <li><span className="featureGraphLegend__swatch featureGraphLegend__swatch--feature" /> Feature</li>
            {EDGE_KINDS.map((kind) => (
              <li key={kind}>
                <span className={`featureGraphLegend__swatch featureGraphLegend__swatch--edge-${kind}`} />
                {' '}<code>{kind}</code>
              </li>
            ))}
          </ul>
        </section>

        {isEmpty ? (
          <p className="featureGraphPage__empty">
            This project has not published any features yet. The feature graph will appear here once at least one
            feature is published.
          </p>
        ) : (
          <>
            <form className="featureGraphControls" onSubmit={(event) => event.preventDefault()}>
              <fieldset>
                <legend>Edge kinds</legend>
                {EDGE_KINDS.map((kind) => (
                  <label key={kind} className="featureGraphControls__option">
                    <input type="checkbox" checked={visibleKinds.has(kind)} onChange={() => toggleKind(kind)} />
                    {formatKind(kind)}
                  </label>
                ))}
              </fieldset>
              <fieldset>
                <legend>Modules</legend>
                {graph.modules.map((module) => (
                  <label key={module.id} className="featureGraphControls__option">
                    <input type="checkbox" checked={visibleModules.has(module.id)} onChange={() => toggleModule(module.id)} />
                    {module.title}
                  </label>
                ))}
              </fieldset>
              <div className="featureGraphControls__search">
                <label htmlFor="feature-graph-search">Search</label>
                <input
                  id="feature-graph-search"
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Feature ID or title"
                />
              </div>
            </form>

            <div className="featureGraphLayout">
              <FeatureGraph
                modules={filteredModules}
                features={filteredFeatures}
                edges={filteredEdges}
                selectedFeatureId={effectiveSelectedId}
                onSelect={setSelectedId}
              />
              <aside className="featureGraphDetail" aria-live="polite" aria-label="Selected feature detail">
                {selectedFeature ? (
                  <>
                    <p className="architectureView__eyebrow">Selected feature</p>
                    <h2><Link to={selectedFeature.route}>{selectedFeature.title}</Link></h2>
                    <p>{selectedFeature.outcome}</p>
                    <p><code>{selectedFeature.id}</code></p>
                    <p>Evidence: {selectedFeature.status}</p>
                  </>
                ) : (
                  <p>Select a node to see its title, outcome, and a link to its page.</p>
                )}
              </aside>
            </div>
          </>
        )}

        <h2 id="feature-graph-edge-table-heading">Every edge</h2>
        <p>
          The same facts as text, independent of the interactive canvas above — every edge in{' '}
          <code>feature-graph.json</code>, regardless of the current filters.
        </p>
        <div className="featureGraphTable">
          <table aria-labelledby="feature-graph-edge-table-heading">
            <thead>
              <tr>
                <th scope="col">Source</th>
                <th scope="col">Target</th>
                <th scope="col">Kind</th>
                <th scope="col">Interface</th>
              </tr>
            </thead>
            <tbody>
              {graph.edges.map((edge) => (
                <tr key={edge.id}>
                  <td>{routeById.has(edge.source) ? <Link to={routeById.get(edge.source)!}>{edge.source}</Link> : edge.source}</td>
                  <td>{routeById.has(edge.target) ? <Link to={routeById.get(edge.target)!}>{edge.target}</Link> : edge.target}</td>
                  <td>{formatKind(edge.kind)}</td>
                  <td>{edge.interface ?? ''}</td>
                </tr>
              ))}
              {graph.edges.length === 0 && (
                <tr><td colSpan={4}>No edges have been derived yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </main>
    </Layout>
  );
}
