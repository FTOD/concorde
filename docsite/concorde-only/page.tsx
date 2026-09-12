import React, {useEffect, useId, useRef, useState} from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import type {FlowData, Graph} from './types';
import styles from './style.module.css';

type Step = {title: string; kind: string; agent: string; input: string; output: string; detail: string; spec: string};
const development = '/specs/concorde/development/';
const steps: Record<string, Step> = {
  specify: {title: 'Author owned Specs', kind: 'Capability → Agent', agent: 'spec-engineer / specify',
    input: 'Task, complete Module Spec context', output: 'Owned-document proposals',
    detail: 'The host reviews affected owner and consumer contexts before applying proposals. Referenced documents stay read-only.',
    spec: development + 'development#stages-and-outcomes'},
  review_spec: {title: 'Review the contract', kind: 'Capability → Agent', agent: 'spec-engineer / spec-review',
    input: 'Current complete Spec context', output: 'Revision-bound review or explicit skip',
    detail: 'A current review may be reused. Disabled reviews record a skip. Gaps or blocking Spec findings stop for a human; there is no automatic Spec repair edge.',
    spec: development + 'review-and-gaps'},
  plan: {title: 'Assess and plan', kind: 'Capability → Agents', agent: 'spec-engineer / context-solve → plan',
    input: 'Complete Specs, task and file listings', output: 'Context assessment and accepted plan',
    detail: 'The planner receives declared file names, not implementation contents. Missing meaning blocks the dependent work.',
    spec: development + 'development#stages-and-outcomes'},
  tasks: {title: 'Define acceptance tasks', kind: 'Capability → Agent', agent: 'spec-engineer / tasks',
    input: 'Accepted plan, task identities, admitted repair feedback', output: 'Ordered tasks with scope and acceptance',
    detail: 'The repair edge re-enters here with a typed code review. Task-scope repair is a separately bound request; feedback cannot widen file authority.',
    spec: development + 'development'},
  implement: {title: 'Implement scoped tasks', kind: 'Capability → Agent', agent: 'programmer / implementation',
    input: 'One task, Specs and authorized implementation contents', output: 'Code changes and completion evidence',
    detail: 'Only listed implementation files may be written. Coordinated child components are separately admitted. Deferred component verification can end this graph after the draft.',
    spec: development + 'development#coordinated-implementation-and-final-consumer-checks'},
  validate: {title: 'Validate the candidate', kind: 'Deterministic capability', agent: 'No model call',
    input: 'Current candidate and configured checks', output: 'Spec validation and code-check evidence',
    detail: 'Failed or stale evidence stops advancement. Shared implementation consumers require their own scoped evidence.',
    spec: development + 'interfaces'},
  review_code: {title: 'Review code independently', kind: 'Capability → Agent', agent: 'programmer / code-review',
    input: 'Specs, authorized code and current revision', output: 'Findings, coverage and feedback identity',
    detail: 'Only local blocking findings without a Spec gap can select repair. Foreign-consumer findings stop for separately routed work. Unchanged feedback waits; the persisted repair limit stops further retries.',
    spec: development + 'development#ai-and-human-feedback'},
  ready: {title: 'Record readiness', kind: 'Deterministic host', agent: 'No model call',
    input: 'Current required reviews and validation evidence', output: 'Ready candidate',
    detail: 'Readiness does not deliver or merge. Delivery is a separately authorized capability.',
    spec: development + 'delivery'},
};

function label(id: string) {
  id = id.split(':').at(-1) ?? id;
  return id === '__start__' ? 'Start' : id === '__end__' ? 'End' : steps[id]?.title ??
    id.replace(/_/g, ' ');
}

function Diagram({graph, name, studio = false}: {graph: Graph; name: string; studio?: boolean}) {
  const marker = useId().replace(/:/g, '');
  const [readingSize, setReadingSize] = useState(false);
  const canvas = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (canvas.current) canvas.current.scrollLeft = (canvas.current.scrollWidth - canvas.current.clientWidth) / 2;
  }, [graph, readingSize]);
  const order = studio ? ['__start__', ...graph.nodes.filter(id => id !== '__start__' && id !== '__end__'), '__end__'] : ['__start__', ...Object.keys(steps).filter(n => graph.nodes.includes(n)), '__end__'];
  const position = (id: string) => 55 + order.indexOf(id) * 136;
  const height = order.length * 136;
  return <>
    <div className={styles.diagramTools}>
      <span>Solid: unconditional · Dashed: conditional</span>
      <button type="button" aria-pressed={readingSize} onClick={() => setReadingSize(!readingSize)}>
        {readingSize ? 'Fit width' : 'Reading size'}</button>
    </div>
    <div ref={canvas} className={styles.canvas} role="region" aria-label={`${name} diagram; scroll to explore`} tabIndex={0}>
      <svg className={readingSize ? styles.readingSize : styles.fit} viewBox={`0 0 720 ${height}`}
        role="img" aria-labelledby={`${marker}-title ${marker}-desc`}>
        <title id={`${marker}-title`}>{name}</title>
        <desc id={`${marker}-desc`}>Compiled LangGraph nodes and edges. Select a stage for its responsibilities.
          The transition list below provides the same topology as text.</desc>
        <defs><marker id={marker} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" /></marker></defs>
        {graph.edges.map(edge => {
          const from = position(edge.source), to = position(edge.target);
          const adjacent = order.indexOf(edge.target) === order.indexOf(edge.source) + 1;
          const repair = edge.source === 'review_code' && edge.target === 'tasks';
          const stop = edge.target === '__end__' && !adjacent;
          const d = adjacent ? `M 360 ${from + 37} V ${to - 37}`
            : stop ? `M 515 ${from} H 645 V ${to} H 515`
            : `M 205 ${from} H ${repair ? 65 : 125} V ${to} H 205`;
          return <g key={`${edge.source}-${edge.target}`} className={repair ? styles.repair : styles.edge}>
            <path d={d} fill="none" stroke="currentColor" strokeWidth={repair ? 2.5 : 1.5}
              strokeDasharray={edge.conditional ? '6 5' : undefined} markerEnd={`url(#${marker})`} />
            {edge.conditional && <text x={adjacent ? 373 : stop ? 548 : repair ? 72 : 130}
              y={adjacent ? (from + to) / 2 + 4 : from - 10} className={styles.edgeLabel}>
              {repair ? 'repair' : stop ? 'stop' : adjacent ? (studio ? 'branch' : 'advance') : (studio ? 'branch' : 'resume')}</text>}
          </g>;
        })}
        {order.map(id => {
          const boundary = id.startsWith('__');
          const y = position(id);
          const node = <g className={steps[id]?.agent !== 'No model call' && steps[id] ? styles.agentNode : styles.hostNode}>
            <rect x="205" y={y - 37} width="310" height="74" rx={boundary ? 37 : 12} />
            <text x="360" y={y - 3} textAnchor="middle" className={styles.nodeLabel}>{label(id)}</text>
            <text x="360" y={y + 19} textAnchor="middle" className={styles.nodeId}><title>{id}</title>{id.length > 36 ? '…' + id.slice(-35) : id}</text>
          </g>;
          return steps[id] && !studio ? <a key={id} href={`#stage-${id}`} aria-label={`${label(id)}: responsibilities and Spec`}>{node}</a>
            : <g key={id}>{node}</g>;
        })}
      </svg>
    </div>
    <details className={styles.transitions}><summary>All transitions ({graph.edges.length})</summary>
      <ul>{graph.edges.map(edge => <li key={`${edge.source}-${edge.target}`}>
        <code>{edge.source}</code> → <code>{edge.target}</code> — {edge.conditional ? 'conditional' : 'unconditional'}
      </li>)}</ul>
    </details>
  </>;
}

export default function AgentFlows({data}: {data: FlowData}) {
  const [variant, setVariant] = useState(0);
  const [flowName, setFlowName] = useState('Discovery');
  const [capability, setCapability] = useState('concorde-dev-loop');
  const sourceBase = 'https://github.com/FTOD/concorde/blob/main/';
  const spec = useBaseUrl(development + 'query-and-routing');
  return <Layout title="Agent Flows" description="Concorde's actual Agent and LangGraph execution, branches and bounded feedback loops.">
    <main className={styles.page}>
      <header className={styles.header}>
        <p className={styles.eyebrow}>CONCORDE INTERNALS</p>
        <h1>Inside the Agent Flows.</h1>
        <p>Inspect Concorde's executable Flows, Agent calls and bounded feedback.
          Compiled from current Flow factories, without running Agents.</p>
        <nav aria-label="On this page" className={styles.sectionNav}>
          <a href="#development">Development loop</a><a href="#routing">Routing & diagnosis</a>
          <a href="#studio">Studio Flows</a><a href="#coverage">Implementation coverage</a><a href="#flow-catalog">Flow catalog</a>
        </nav>
      </header>

      <section id="development" className={styles.section}>
        <div className={styles.sectionHeading}><span className={styles.badge}>EXECUTABLE FLOW</span>
          <h2>The development loop</h2>
          <p><code>Invocation.loop → build_loop_flow</code>. Nodes call scoped capabilities; their internal Agent calls are described alongside the graph.</p>
        </div>
        <div className={styles.controls}><label htmlFor="flow-variant">Entry & scope</label>
          <select id="flow-variant" value={variant} onChange={e => setVariant(Number(e.target.value))}>
            {data.loops.map((loop, index) => <option key={loop.label} value={index}>{loop.label}</option>)}
          </select>
        </div>
        <div className={styles.columns}>
          <div><Diagram graph={data.loops[variant]} name={data.loops[variant].label} /></div>
          <aside className={styles.notes} aria-label="Development decisions">
            <h3>What moves execution forward?</h3>
            <p><code>completed</code> or <code>ready</code> selects the successor. Other outcomes stop, except the admitted code-review repair below.</p>
            <div className={styles.callout}><h3>Feedback → revised tasks</h3>
              <p>Local blocking code findings return to <code>tasks</code>, then implementation, validation and independent review.</p>
              <p>Default: at most <strong>{data.policy.max_repair_iterations} repair iterations</strong>. The candidate keeps its persisted policy. Repeated feedback waits; an exhausted limit stops.</p>
            </div>
            <h3>Resume is re-admission</h3>
            <p>Current plan, task and code evidence determine the entry. Nodes skipped by a resume remain declared so a later repair can re-enter tasks.</p>
            <h3>Review controls</h3>
            <p><code>run_reviews=false</code> records explicit skips inside review nodes. Current valid reviews can be reused. A Module without implementation bindings omits the code-review node.</p>
            <h3>Stops remain visible</h3>
            <p>Spec gaps wait for clarification. Failed checks, execution failures and incompatible feedback stop. Cancellation and limits propagate as errors; they are not extra graph nodes.</p>
            <p>Deferred component checks may stop after implementation, or after Spec review on a validation-only resume.</p>
            <Link to={development + 'development#ai-and-human-feedback'}>Read the feedback and recovery contract →</Link>
          </aside>
        </div>
        <h3>Stage responsibilities & handoffs</h3>
        <div className={styles.stageGrid}>{Object.entries(steps).map(([id, step]) =>
          <article id={`stage-${id}`} key={id} className={styles.stage}>
            <span className={styles.badge}>{step.kind}</span><h4>{step.title}</h4>
            <p><code>{step.agent}</code></p>
            <dl><dt>Input</dt><dd>{step.input}</dd><dt>Output</dt><dd>{step.output}</dd></dl>
            <p>{step.detail}</p><Link to={step.spec}>Spec details →</Link>
          </article>)}</div>
      </section>

      <section id="routing" className={styles.section}>
        <span className={styles.badge}>EXECUTABLE DISCOVERY FLOW</span>
        <h2>Routing a read-only diagnosis</h2>
        <p><code>Discovery Flow → owner admission → review Flow</code>. The coordinator selects responsibility; it has no implementation contents.</p>
        <ol className={styles.sequence}>
          <li><strong>Freeze entry context</strong><span>Original task, ordered constraints, routing hints and the entry Module's complete owned/reference context.</span></li>
          <li><strong>Coordinator / route</strong><span>Select target and focus, request explicit context expansion, or return a blocked outcome. Each expansion starts a fresh invocation; the loop is bounded by the Module count.</span></li>
          <li><strong>Host admission</strong><span>Validate context identity, admitted target and focus; require one route. Bind the original task and constraints. Explicit conflicting echoes fail before review.</span></li>
          <li><strong>Independent reviewer</strong><span>Code diagnosis uses programmer / code-review with the selected Module's authorized code. Spec review uses spec-engineer / spec-review. Both are read-only.</span></li>
          <li><strong>Return scoped evidence</strong><span>Findings, coverage, input revision and completion status. A standalone diagnosis needs no change ID and creates no candidate worktree.</span></li>
        </ol>
        <p className={styles.callout}>Expansion feeds back to a new frozen context and coordinator invocation. A missing contract stops the dependent step; it does not authorize source access or automatic repair.</p>
        <a href={spec}>Routing contract →</a>{' · '}<Link to={development + 'module#scenario.development.standalone-review'}>Standalone review scenario →</Link>
      </section>

      <section id="studio" className={styles.section}>
        <span className={styles.badge}>COMPOSED EXECUTION FLOW</span><h2>The Studio entry Flow</h2>
        <p><code>build_studio_flow</code> exposes the same admission, dispatch and composed Flows used by local calls. Expand the transitions to inspect the selected capability.</p>
        <div className={styles.controls}><label htmlFor="flow-capability">Public capability</label>
          <select id="flow-capability" value={capability} onChange={e => setCapability(e.target.value)}>
            {Object.keys(data.studio).map(name => <option key={name}>{name}</option>)}
          </select></div>
        <div className={styles.columns}><div><Diagram graph={data.studio[capability]} name={`${capability} Studio Flow`} studio /></div>
          <aside className={styles.notes}><h3>Input → result</h3>
            <p>A typed invocation and optional expected workspace enter validation. Invalid input goes directly to End with a failure result.</p>
            <p>The Flow rechecks admission and the workspace on replay. The final state contains the typed result, permission policies and streamed stage / Agent events.</p>
            <p>Internal Flow nodes are inspectable, but do not become public capability entries. Host objects stay outside checkpoints. Atomic lifecycle operations remain deterministic nodes.</p>
            <Link to="/specs/concorde/harness/module#entity.harness.studio">Studio Spec →</Link></aside></div>
      </section>

      <section id="flow-catalog" className={styles.section}>
        <span className={styles.badge}>EXECUTABLE FLOW FACTORIES</span><h2>Inspect every Flow family</h2>
        <p>These are compiled runtime definitions. Branches select admitted outcomes; repeated work remains bounded by each Flow's domain limits.</p>
        <div className={styles.controls}><label htmlFor="flow-family">Flow family</label>
          <select id="flow-family" value={flowName} onChange={e => setFlowName(e.target.value)}>
            {Object.keys(data.flows).map(name => <option key={name}>{name}</option>)}
          </select></div>
        <Diagram graph={data.flows[flowName]} name={flowName} studio />
      </section>

      <section id="coverage" className={styles.section}>
        <h2>What is implemented?</h2>
        <p>Public entries execute LangGraph Flows for admission and capability dispatch. Query, topology, planning,
          development and reflection Flows are composed into those entries. Component coordination, batch work and
          recursive Agent decisions also use executable Flow factories shown in the catalog.</p>
        <p>The <Link to="/specs/concorde/harness/graphs-and-loops">Flow and Loop contracts</Link> define the terminology and boundaries.
          Runtime context selects concrete component and Agent instances. The catalog shows their scheduling structure;
          it does not claim an admitted delegation tree. Atomic delivery remains a deterministic transaction node.</p>
        <p>These views describe possible compiled transitions, not a live trace or proof that a candidate passed review.
          Source links track main; the byte digests below identify the inputs used for this page.</p>
        <details><summary>Source factories & build fingerprints</summary>
          <ul className={styles.sources}>{data.sources.map(source => <li key={source.path}>
            <a href={sourceBase + source.path}>{source.path}</a><code>sha256:{source.digest}</code>
          </li>)}</ul></details>
      </section>
    </main>
  </Layout>;
}
