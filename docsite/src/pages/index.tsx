import Head from '@docusaurus/Head';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import {usePluginData} from '@docusaurus/useGlobalData';

import type {ContentPage} from '../../plugins/concorde-content/types';

interface GlobalData {pages: ContentPage[]}

/** Root is a route-only projection of the root module architecture, never a third content source. */
export default function RootArchitectureRedirect() {
  const data = usePluginData('concorde-content') as unknown as GlobalData;
  const root = data.pages.find((page) => page.kind === 'module-architecture' && !page.parentId);
  if (!root) throw new Error('The docsite requires exactly one root module architecture.');
  const target = useBaseUrl(root.route);
  return <>
    <Head>
      <meta httpEquiv="refresh" content={`0; url=${target}`} />
      <link rel="canonical" href={target} />
    </Head>
    <main className="container margin-vert--xl">
      <h1>{root.title}</h1>
      <p>Opening the root architecture. <Link to={root.route}>Continue to {root.title}</Link>.</p>
    </main>
  </>;
}
