import React, {useEffect, useId, useRef, useState} from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import type {FlowData, Graph} from './types';
import styles from './style.module.css';

type Step = {title: string; kind: string; agent: string; input: string; output: string;
  detail: string; handoff: React.ReactNode; stops: string; spec: string};
const development = '/specs/concorde/development/';
const steps: Record<string, Step> = {
  specify_loop: {title: 'Specify Loop', kind: 'Composed capability', agent: 'spec-engineer / specify → spec-review',
    input: 'Intended behavior, constraints, authoring/review flags and the complete Module Specs.',
    output: 'An authored or revised Spec with independent review evidence, or an attributed blocker.',
    detail: 'Calls concorde-specify-loop, which can also run independently. Its author proposes only owned document replacements, and the host validates them. Independent reviewers assess the complete contract and affected consumers in fresh contexts without reading implementation code.',
    handoff: <><code>concorde-specify-loop-response@1</code> returns <code>completed</code> and artifact references. Dev Loop then enters planning or resumes current downstream work in the same change. Spec completion alone does not mark implementation ready.</>,
    stops: 'Necessary gaps, blocking findings, incomplete coverage or failed execution stop advancement. specify=false skips authoring; run_reviews=false records a Spec skip only if review was not already required. Accepted authoring and current reviews can be reused. There is no automatic Spec-repair edge.',
    spec: development + 'development'},
  plan: {title: 'Plan', kind: 'Two Agent stages', agent: 'spec-engineer / context-solve → plan',
    input: 'Complete Specs, intended behavior, constraints and declared implementation file names.',
    output: 'A context-sufficiency assessment, then a nonempty implementation plan.',
    detail: 'First assess whether the available contract can answer the task. Then plan the approach, affected components and software acceptance. Both calls use Specs and file listings; neither reads code to fill in missing requirements.',
    handoff: <>The Agent returns a <code>plan</code> string in <code>concorde-agent-stage-result@1.data</code>. The host saves <code>plan.md</code> and passes <code>concorde-plan-artifact@1</code> with <code>{'{plan}'}</code> to Tasks through <code>stage_inputs</code>.</>,
    stops: 'Missing contract meaning returns spec_incomplete; contradictions or unsupported intent stop planning. Missing required Spec review, stale context, an empty plan or an invalid Agent result blocks acceptance.',
    spec: development + 'development#stages-and-outcomes'},
  tasks: {title: 'Tasks', kind: 'Agent stage', agent: 'spec-engineer / tasks',
    input: 'Specs, the accepted plan, reserved task IDs and any admitted repair feedback.',
    output: 'Ordered, initially incomplete tasks with an owner, description and acceptance criteria.',
    detail: 'Break the plan into concrete software work. Each task states what its implementation must achieve within the granted files and runtime. Host validation, independent review and delivery remain later gates; they are not prerequisites for marking implementation work complete.',
    handoff: <>Tasks returns a <code>tasks</code> array in <code>concorde-agent-stage-result@1.data</code>. The host supplies Implement with <code>concorde-implementation-task@1</code>: <code>{'{plan, tasks: [{id, target_id, description, acceptance, complete}]}'}</code>. Reserved IDs arrive separately as <code>concorde-task-identity-constraints@1</code>.</>,
    stops: 'No accepted plan, stale intent, missing contract meaning, empty tasks, duplicate/reserved IDs or tasks already marked complete block acceptance. Tasks may target only the current Module, its declared dependencies or direct children. Repair feedback cannot expand that scope.',
    spec: development + 'development'},
  implement: {title: 'Implement', kind: 'Agent stage', agent: 'programmer / implementation',
    input: 'Specs, the plan and task list, authorized code contents, and any admitted code-review feedback.',
    output: 'Changes to authorized implementation files and the exact accepted tasks marked complete.',
    detail: 'Write code and tests to meet each task’s acceptance criteria. Spec documents and the registry are outside this write grant. A coordinating Module sends component work through each component’s own context; all writers finish before final shared-candidate checks.',
    handoff: <>The host passes <code>concorde-implementation-task@1</code>; the Agent returns completed <code>tasks</code> in <code>concorde-agent-stage-result@1.data</code>. Code changes stay in worktree files. Validate reads those files and the saved completion/revision state, not a code payload in the next request.</>,
    stops: 'Missing or stale tasks, unauthorized writes, necessary Spec gaps, execution errors, changed task identities or unmet acceptance stop advancement. A test requiring inputs outside the grant is recorded as deferred to Host verification, not as a passing test; an actual implementation defect remains incomplete.',
    spec: development + 'development#coordinated-implementation-and-final-consumer-checks'},
  validate: {title: 'Validate', kind: 'Deterministic capability', agent: 'No model call',
    input: 'Current candidate files, Spec declarations and the project’s configured check commands.',
    output: 'Deterministic Spec validation and code-check results bound to the measured revision.',
    detail: 'Check machine-verifiable structure: document ownership, IDs, references, required format, file bindings and shared-contract consistency. Run configured checks such as tests, type checking or builds. Structural success does not prove semantic completeness; Review Spec assesses meaning, and Review Code assesses implementation behavior.',
    handoff: <><code>concorde-validate-response@1</code> has a <code>data.checks</code> array with <code>check_id</code>, <code>target_id</code>, <code>status</code>, <code>exit_code</code>, <code>source_digest</code> and <code>log_digest</code> per record. The host saves evidence; Code Review receives its own Spec/code snapshot and review input. Raw check logs are not fed into Spec-only stages.</>,
    stops: 'Invalid Spec structure, failed check commands or timeouts return failed. Changes during verification produce stale_evidence; unenforceable check permissions block execution. Shared implementation users need current evidence too. This stage has no automatic repair edge.',
    spec: development + 'interfaces'},
  review_code: {title: 'Review Code', kind: 'Independent review', agent: 'programmer / code-review',
    input: 'Complete Specs, authorized implementation files and scoped changes at the reviewed revision.',
    output: 'Behavior findings, review coverage, gaps and revision-bound completion status.',
    detail: 'Compare implementation and tests with the promised scenarios, interface behavior and task acceptance. Look for concrete defects and regressions, including failure paths and affected consumers. The reviewer is read-only; passing tests do not replace this review.',
    handoff: <>The reviewer returns <code>concorde-review-stage-result@1</code>; the host stores and publishes <code>concorde-review-result@1</code>. Local repair sends that exact typed record plus the prior tasks back to Tasks and Implement. Otherwise, Ready checks the saved evidence.</>,
    stops: 'Local blocking code findings without a Spec gap can trigger bounded repair. Spec gaps, incomplete reviews, execution failures or another consumer’s blocking findings stop. Repeated identical feedback waits; exhausting the repair limit stops. Advisory findings do not block readiness.',
    spec: development + 'development#ai-and-human-feedback'},
  ready: {title: 'Ready', kind: 'Host checkpoint', agent: 'No model call',
    input: 'Saved task completion, required reviews, configured check results and current candidate digests.',
    output: 'A candidate recorded as ready for a separate delivery request.',
    detail: 'Verify that required evidence is complete and still matches the current task, Specs and code. Ready is an internal host checkpoint, not a separately callable capability. It does not deliver or merge the change.',
    handoff: <>The host updates <code>.concorde/worktree.json</code> and returns <code>concorde-dev-loop-response@1</code> with <code>outcome: ready</code>, check results and review artifact references. A later Deliver request identifies the change by <code>change_id</code>.</>,
    stops: 'Open contract gaps, unfinished tasks, absent or blocking required reviews, failed/missing checks or stale evidence prevent ready. Changing the candidate during completion verification also stops with stale_evidence.',
    spec: development + 'delivery'},
};

type CapabilityDetail = {title: string; detail: string; exchange: string; stops: string};
const capabilityDetails: Record<string, CapabilityDetail> = {
  'concorde-main': {title: 'Main',
    detail: 'Answer from admitted Specs, route work to an owning Module, or prepare and apply an explicit topology proposal.',
    exchange: 'concorde-main-request@1 → concorde-main-response@1. Carries task and routing hints, then answer/routes; topology actions exchange concorde-topology-proposal@1 and an application ArtifactRef.',
    stops: 'Missing contract meaning, incompatible intent, invalid routes, stale proposal/application references or rejected topology validation stop the selected action.'},
  'concorde-specify-loop': {title: 'Specify Loop',
    detail: 'Route one change, author or revise its Spec, then independently review the contract. Stop before planning or implementation.',
    exchange: 'concorde-specify-loop-request@1 → concorde-specify-loop-response@1. Task, constraints and flags enter; Spec completion or blockers and artifact references return. The same change can continue through Dev Loop.',
    stops: 'Spec gaps, blocking findings, incomplete reviews and invalid proposals preserve partial progress. Completion does not mark ready or require code review; a new primary-worktree change requires a fresh candidate session.'},
  'concorde-dev-loop': {title: 'Dev Loop',
    detail: 'Coordinate Specify through Ready, reusing current evidence and allowing the bounded code-review repair shown above.',
    exchange: 'concorde-dev-loop-request@1 → concorde-dev-loop-response@1. Task, constraints, flags and optional change_id enter; outcome, gaps, checks and artifact references return. Stage handoffs and candidate files are managed by the host.',
    stops: 'Any non-advancing stage outcome stops the loop, except admitted local code-review repair. A new primary-worktree change first returns worktree_handoff_required so a fresh session can continue in the candidate.'},
  'concorde-review': {title: 'Review',
    detail: 'Route an independent, read-only review. Spec mode assesses structure and contract meaning; code mode also checks authorized implementation against those promises.',
    exchange: 'concorde-review-request@1 (task, review_mode: spec|code) → concorde-review-response@1, whose reviews array contains concorde-review-result@1 values. The host binds each review to its input revision.',
    stops: 'Missing definitions, blocking findings, incomplete coverage, invalid review output or a failed reviewer prevent a successful review. Advisory findings remain visible without blocking.'},
  'concorde-reflections-triage': {title: 'Reflections',
    detail: 'Report or capture gaps, investigate recorded reflections, and route approved implementation or disposition through the corresponding action.',
    exchange: 'concorde-reflections-triage-request@1 → concorde-reflections-triage-response@1, including reflections and gap_records. Admitted implementation receives concorde-reflection-selection@1; raw investigation logs do not enter Spec authoring.',
    stops: 'Unknown or stale selected records, insufficient investigation evidence, incompatible disposition or required acceptance that is absent blocks the relevant action. Nested development/delivery failures remain visible.'},
  'concorde-init': {title: 'Init',
    detail: 'Propose or apply initial project configuration, a pinned Protocol and an honest Module stub.',
    exchange: 'concorde-init-request@1 → concorde-init-response@1. Propose returns concorde-project-proposal@1; apply consumes the exact proposal and returns applied status and changed paths.',
    stops: 'Missing proposal inputs, malformed or stale proposals, conflicting existing project state or unsuccessful file application block initialization. Preview uses action: propose; describe-policy returns use_proposal.'},
  'concorde-configure': {title: 'Configure',
    detail: 'Apply the initialized project’s integration and enforcement configuration.',
    exchange: 'concorde-configure-request@1 carries concorde-capability-configuration@1. concorde-configure-response@1 returns configuration and status: applied, rather than the common stage-response fields.',
    stops: 'Invalid configuration, unavailable initialized project state or a failed configuration write blocks application. Preview through describe-policy is not supported by this project action.'},
  'concorde-validate': {title: 'Validate',
    detail: 'Check Spec structure and configured commands. Standalone candidate validation can also check readiness; inside Dev Loop, required code review precedes Ready.',
    exchange: 'concorde-validate-request@1 (target_id, task, optional run_checks) → concorde-validate-response@1 with outcome and revision-bound checks. Evidence is saved in the candidate state.',
    stops: 'Invalid Specs, failing or timed-out checks, unenforceable permissions or changed inputs stop validation. Skipping check execution does not satisfy readiness requirements for those checks.'},
  'concorde-deliver': {title: 'Deliver',
    detail: 'Verify the integration, stage an independent delivered branch and normally remove the source worktree. A primary-branch merge requires its own explicit primary-session request.',
    exchange: 'concorde-deliver-request@1 identifies change_id and optional keep_worktree/merge_primary. concorde-deliver-response@1 returns outcome and artifacts, including the delivery receipt.',
    stops: 'Wrong session/worktree, unfinished or stale evidence, integration conflicts, unsafe cleanup or missing authority for a primary merge stops the requested delivery action. Incomplete cleanup is recorded separately.'},
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
        <p>Follow what each step does, what it passes on, and what makes it stop.
          The diagrams come from current Flow factories, without running Agents.</p>
        <p>This is custom documentation for Concorde’s own site, outside the reusable Framework docsite template.</p>
        <nav aria-label="On this page" className={styles.sectionNav}>
          <a href="#development">Development loop</a><a href="#handoffs">Data handoffs</a><a href="#stages">Stage details</a><a href="#routing">Routing & diagnosis</a>
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
        <div id="handoffs" className={styles.handoffs}>
          <h3>How information moves</h3>
          <p>The host calls each capability with a named JSON request and receives a named JSON response.
            It checks the result, saves accepted artifacts and creates the next stage’s inputs.
            An arrow does not mean one Agent receives another Agent’s conversation.</p>
          <ol className={styles.sequence}>
            <li><strong>Capability call → response</strong><span>Public calls use <code>concorde-capability-invocation@3</code> with
              a typed <code>input</code>. The result is <code>concorde-capability-result@3</code> with a typed <code>output</code> or
              admission errors. Internal calls use the same named request/response contracts. The host reads <code>outcome</code>,
              <code>gaps</code>, <code>checks</code> and <code>artifacts</code> to choose the next step.</span></li>
            <li><strong>Host → Agent → host</strong><span>Ordinary workers receive <code>concorde-agent-stage-context@2</code>
              containing a <code>concorde-context-snapshot@2</code> and return <code>concorde-agent-stage-result@1</code>.
              Reviewers use <code>concorde-review-stage-context@2</code> and <code>concorde-review-stage-result@1</code> instead.
              These are internal Agent exchanges, separate from capability responses.</span></li>
            <li><strong>Accepted output → next stage</strong><span>A typed value has <code>{'{type_id, schema_version, data}'}</code>;
              <code>@1</code> in a type label means <code>schema_version: 1</code>. Plans, tasks and admitted repair feedback travel
              in the next snapshot’s <code>stage_inputs</code>. Specs and code remain files, read through a fresh authorized snapshot.</span></li>
            <li><strong>Artifacts and saved state</strong><span>An <code>ArtifactRef</code> is <code>{'{id, path, digest}'}</code>:
              a project-relative file path and a <code>sha256:</code> digest identifying its exact bytes.
              The host verifies references before reuse. <code>.concorde/worktree.json</code> stores candidate progress and evidence;
              <code>.concorde/work/&lt;target-id&gt;/</code> holds plans and auxiliary files. They are host-managed records,
              not an extra public message type.</span></li>
          </ol>
          <details className={styles.wireExample}>
            <summary>Example: the plan passed from Plan to Tasks</summary>
            <p>This illustrative value is one entry in <code>snapshot.data.stage_inputs</code>.
              The request that calls Tasks separately identifies the task, Module and change.</p>
            <pre><code>{JSON.stringify({type_id: 'concorde-plan-artifact', schema_version: 1,
              data: {plan: 'Show each stage’s responsibility, handoff format and stop conditions.'}}, null, 2)}</code></pre>
            <p>Tasks also receives <code>concorde-task-identity-constraints@1</code> containing reserved IDs.
              The repair path adds the prior tasks and the verified <code>concorde-review-result@1</code>.
              Ordinary Plan → Tasks handoff carries no code or review transcript.</p>
          </details>
          <Link to={development + 'interfaces#wire-contracts'}>Request, response and handoff contracts →</Link>
          <div className={styles.stopLegend}>
            <h4>Stopping is not always execution failure</h4>
            <dl>
              <dt><code>spec_incomplete</code></dt><dd>A necessary promise is missing or ambiguous; report the question and blocked step, then wait for contract clarification.</dd>
              <dt><code>conflicting</code></dt><dd>Contracts, intent or blocking review findings conflict. Only admitted local code-review findings can select the bounded repair path.</dd>
              <dt><code>unsupported</code></dt><dd>The requested behavior is outside a known supported boundary; that is different from an unspecified contract.</dd>
              <dt><code>failed</code></dt><dd>Execution or deterministic checks failed. The worktree is preserved; this outcome does not automatically re-enter implementation.</dd>
            </dl>
            <p>These are capability <code>output.data.outcome</code> values. The outer result has its own <code>status</code> and
              <code>errors</code>; malformed inputs, permission problems and stale artifacts can stop admission before any stage runs.
              Cancellation and execution limits have dedicated error codes.</p>
          </div>
        </div>
        <h3 id="stages" className={styles.anchor}>Stage responsibilities & handoffs</h3>
        <p>Names in the graph match the cards below. Each card separates the work itself from its data handoff and stopping rules.</p>
        <div className={styles.stageGrid}>{Object.entries(steps).map(([id, step]) =>
          <article id={`stage-${id}`} key={id} className={styles.stage}>
            <span className={styles.badge}>{step.kind}</span><h4>{step.title}</h4>
            <p><code>{step.agent}</code></p>
            <p>{step.detail}</p>
            <dl><dt>Receives</dt><dd>{step.input}</dd><dt>Produces</dt><dd>{step.output}</dd>
              <dt>Format & next step</dt><dd>{step.handoff}</dd></dl>
            <div className={styles.stopReason}><h5>When it stops</h5><p>{step.stops}</p></div>
            <Link to={step.spec}>Spec details →</Link>
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
        <p><strong>Handoff:</strong> the coordinator receives <code>concorde-main-stage-context@2</code> and returns
          <code>concorde-main-stage-result@1</code> with routes, gaps or an expansion request. The host admits the selected route’s
          <code>target_id</code>, <code>focus_id</code>, <code>task</code> and <code>constraints</code>, then creates a separate
          <code>concorde-review-stage-context@2</code> for the reviewer. Invalid or contradictory route fields stop admission.</p>
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
            <h3>{capabilityDetails[capability].title}</h3>
            <p>{capabilityDetails[capability].detail}</p>
            <h4>Information & format</h4><p className={styles.exchange}>{capabilityDetails[capability].exchange}</p>
            <div className={styles.stopReason}><h4>When it stops</h4><p>{capabilityDetails[capability].stops}</p></div>
            <Link to="/specs/concorde/harness/module#entity.harness.studio">Studio Spec →</Link></aside></div>
        <div className={styles.callout}><h3>Shared admission checks</h3>
          <p>Unknown capabilities, malformed typed data, incompatible versions, configuration mismatches and invalid workspace
            bindings stop before execution. The typed result reports the specific error code.</p>
          <p>Top-level <strong>Main, Dev Loop, Review and Reflections</strong> reject a stale generated build in both execution
            and policy-preview mode. Deterministic lifecycle capabilities <strong>Init, Configure, Validate and Deliver</strong>
            are exempt from that entry check because they launch no Agents. Loading an Agent independently checks build freshness.
            The exception does not waive Protocol, input, permission or evidence validation.</p>
          <Link to={development + 'interfaces'}>Capability admission and error contracts →</Link>
        </div>
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
