import Head from '@docusaurus/Head';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import {usePluginData} from '@docusaurus/useGlobalData';

import type {Page} from '../../plugins/scoped-content/model';

interface GlobalData {pages: Page[]; entryTarget: string}

/** Root redirects to the registered entry target's main Spec without creating another content source. */
export default function RootModuleRedirect() {
  const data = usePluginData('concorde-content') as unknown as GlobalData;
  const root = data.pages.find((page) => page.primaryOf === data.entryTarget);
  if (!root) throw new Error('The docsite requires a registered entry target.');
  const target = useBaseUrl(root.route);
  return <>
    <Head>
      <meta httpEquiv="refresh" content={`0; url=${target}`} />
      <link rel="canonical" href={target} />
    </Head>
    <main className="container margin-vert--xl">
      <h1>{root.title}</h1>
      <p>Opening the project Spec. <Link to={root.route}>Continue to {root.title}</Link>.</p>
    </main>
  </>;
}
