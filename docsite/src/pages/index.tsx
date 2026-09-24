import Head from "@docusaurus/Head";
import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";
import { usePluginData } from "@docusaurus/useGlobalData";

import type { Page } from "../../plugins/scoped-content/model";

interface GlobalData {
  pages: Page[];
  rootModule: string;
}

/**
 * The site root of a project without user documents: it opens the root Module's entry. With user
 * documents configured, their root page is the home page and this page is not built.
 */
export default function Home() {
  // SAFETY: the concorde-content plugin publishes this shape after registry validation.
  const data = usePluginData("concorde-content") as unknown as GlobalData;
  const root = data.pages.find((page) => page.primaryOf === data.rootModule);
  if (!root) throw new Error("The docsite requires a registered root Module.");
  const target = useBaseUrl(root.route);
  return (
    <>
      <Head>
        <meta httpEquiv="refresh" content={`0; url=${target}`} />
        <link rel="canonical" href={target} />
      </Head>
      <main className="container margin-vert--xl">
        <h1>{root.title}</h1>
        <p>
          Opening the project Spec.{" "}
          <Link to={root.route}>Continue to {root.title}</Link>.
        </p>
      </main>
    </>
  );
}
