import Head from '@docusaurus/Head';

import ScopedGraph from '../components/ScopedGraph';

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

export default function ArchitectureGraphPage() {
  return <>
    <Head>
      {/* react-helmet-async expects a plain string child for <script>, not dangerouslySetInnerHTML;
          it converts that child into the tag's innerHTML itself. */}
      <script>{NORMALIZE_HTML_URL_SCRIPT}</script>
    </Head>
    <ScopedGraph />
  </>;
}
