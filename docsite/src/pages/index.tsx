import Head from '@docusaurus/Head';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import {usePluginData} from '@docusaurus/useGlobalData';
import Layout from '@theme/Layout';
import CodeBlock from '@theme/CodeBlock';
import Heading from '@theme/Heading';

import type {Page} from '../../plugins/scoped-content/model';
import type {SiteIdentity} from '../../plugins/scoped-content/site-identity';
import styles from './index.module.css';

interface GlobalData {pages: Page[]; entryTarget: string; siteIdentity: SiteIdentity}

const contractParts = [
  ['Purpose', 'The responsibility. The people it serves.'],
  ['Requirements', 'The guarantees the Module must uphold.'],
  ['Scenarios', 'Concrete situations. Testable outcomes.'],
  ['Ontology', 'The entities, relationships and implementation files.'],
];

/** An opt-in introduction; registered Specs retain their own routes and authority. */
export default function Home() {
  const data = usePluginData('concorde-content') as unknown as GlobalData;
  const root = data.pages.find((page) => page.primaryOf === data.entryTarget);
  if (!root) throw new Error('The docsite requires a registered entry target.');
  const target = useBaseUrl(root.route);
  const {siteIdentity: identity} = data;
  const page = identity.homepage;
  if (!page) return <>
    <Head>
      <meta httpEquiv="refresh" content={`0; url=${target}`} />
      <link rel="canonical" href={target} />
    </Head>
    <main className="container margin-vert--xl">
      <h1>{root.title}</h1>
      <p>Opening the project Spec. <Link to={root.route}>Continue to {root.title}</Link>.</p>
    </main>
  </>;

  return <Layout title={page.title} description={page.description}>
    <main className={styles.home}>
      <section className={styles.hero} aria-labelledby="home-title">
        <div className={styles.heroInner}>
          <div>
            <p className={styles.eyebrow}>{page.eyebrow}</p>
            <h1 id="home-title">{page.title}</h1>
            <p className={styles.intro}>{page.description}</p>
            <div className={styles.actions}>
              <Link className={styles.primary} to="#get-started">Get started <span aria-hidden="true">↗</span></Link>
              <Link className={styles.secondary} to={root.route}>Explore the Specs <span aria-hidden="true">→</span></Link>
            </div>
          </div>
          <div className={styles.contract}>
            <div className={styles.contractHeading}><span className={styles.contractMark} aria-hidden="true">◇</span> The Module contract</div>
            <ol>
              {contractParts.map(([title, description], index) => <li key={title}>
                <span className={styles.number} aria-hidden="true">0{index + 1}</span>
                <div><h2>{title}</h2><p>{description}</p></div>
              </li>)}
            </ol>
            <Link className={styles.contractLink} to={root.route}>Read {root.title} <span aria-hidden="true">↗</span></Link>
          </div>
        </div>
      </section>

      <nav className={styles.explore} aria-label="Explore documentation">
        <span>Go deeper</span>
        <Link to={root.route}>Module Specs <span aria-hidden="true">↗</span></Link>
        {page.links?.map(link => <Link key={link.to} to={link.to}>{link.label} <span aria-hidden="true">↗</span></Link>)}
        {identity.repository && <Link href={identity.repository}>Repository <span aria-hidden="true">↗</span></Link>}
      </nav>

      <section className={styles.section} aria-labelledby="features-title">
        <p className={styles.sectionLabel}>Core capabilities</p>
        <h2 id="features-title">{page.features.title}</h2>
        <div className={styles.features}>
          {page.features.items.map((feature, index) => <article className={styles.feature} key={index}>
            <span className={styles.featureNumber} aria-hidden="true">{String(index + 1).padStart(2, '0')} /</span>
            <h3>{feature.title}</h3><p>{feature.description}</p>
          </article>)}
        </div>
      </section>

      <section className={styles.workflow} aria-labelledby="workflow-title">
        <div className={styles.section}>
          <p className={styles.sectionLabel}>The development loop</p>
          <h2 id="workflow-title">{page.workflow.title}</h2>
          <p className={styles.sectionIntro}>{page.workflow.description}</p>
          <ol className={styles.steps}>
            {page.workflow.steps.map((step, index) => <li key={index}>
              <span className={styles.stepNumber} aria-hidden="true">{String(index + 1).padStart(2, '0')}</span>
              <h3>{step.title}</h3><p>{step.description}</p>
            </li>)}
          </ol>
        </div>
      </section>

      <section className={`${styles.section} ${styles.quickstart}`} aria-labelledby="get-started">
        <div>
          <p className={styles.sectionLabel}>Your next change starts here</p>
          <Heading as="h2" id="get-started">{page.quickstart.title}</Heading>
          <p className={styles.sectionIntro}>{page.quickstart.description}</p>
          {identity.repository && <Link className={styles.setupLink} href={identity.repository}>Installation and workflow guide <span aria-hidden="true">→</span></Link>}
        </div>
        <div className={styles.code}>
          <CodeBlock language="bash" title="Install in your project">{page.quickstart.code}</CodeBlock>
        </div>
      </section>
      {page.reference && <section className={`${styles.section} ${styles.reference}`} aria-labelledby="reference-title">
        <Heading as="h2" id="reference-title">{page.reference.title}</Heading>
        <p className={styles.sectionIntro}>{page.reference.description}</p>
        <nav className={styles.referenceNav} aria-label={page.reference.title}>
          {page.reference.tables.map((table, index) => <Link key={index} to={`#reference-table-${index}`}>{table.title}</Link>)}
        </nav>
        {page.reference.tables.map((table, index) => <div className={styles.referenceGroup} key={index}>
          <Heading as="h3" id={`reference-table-${index}`}>{table.title}</Heading>
          <p className={styles.sectionIntro}>{table.description}</p>
          <div className={styles.tableScroll} role="region" aria-labelledby={`reference-table-${index}`} tabIndex={0}>
            <table className={styles.referenceTable} aria-labelledby={`reference-table-${index}`}>
              <thead><tr>{table.columns.map((column, index) => <th key={index} scope="col">{column}</th>)}</tr></thead>
              <tbody>{table.rows.map((row, index) => <tr key={index}>
                {row.map((cell, index) => <td key={index}>{cell}</td>)}
              </tr>)}</tbody>
            </table>
          </div>
        </div>)}
      </section>}
    </main>
  </Layout>;
}
