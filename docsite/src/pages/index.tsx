import Layout from '@theme/Layout';
import {usePluginData} from '@docusaurus/useGlobalData';

import ProjectSummary from '../components/ProjectSummary';

interface GlobalData {counts: {architecture: number; docs: number; features: number}}

export default function Home() {
  const data = usePluginData('concorde-content') as unknown as GlobalData;
  return (
    <Layout title="Project knowledge" description="Concorde documentation and canonical feature specifications">
      <main className="homeMain">
        <header className="heroBanner">
          <p className="heroBanner__eyebrow">Concorde project knowledge</p>
          <h1>Architecture and specifications, kept in agreement.</h1>
          <p>Browse maintained guidance and the feature specifications that define Concorde itself.</p>
        </header>
        <ProjectSummary architecture={data.counts.architecture} docs={data.counts.docs} features={data.counts.features} />
      </main>
    </Layout>
  );
}
