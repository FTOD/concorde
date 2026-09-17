import React, { useEffect, useId, useMemo, useRef, useState } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";
import type { FlowData, Graph } from "./types";
import {
  capabilityAnchor,
  filterNavigation,
  flowNavigation,
  selectionFromHash,
} from "./navigation";
import styles from "./style.module.css";

type Step = {
  title: string;
  kind: string;
  agent: string;
  input: string;
  output: string;
  detail: string;
  handoff: React.ReactNode;
  stops: string;
  spec: string;
};
const development = "/specs/concorde/development/";
const specSteps: Record<string, Step> = {
  initialize: {
    title: "Select entry",
    kind: "Host decision",
    agent: "No model call",
    input:
      "The routed Module, task, constraints, flags and saved authoring evidence.",
    output: "Enter Specify or proceed directly to Review Spec.",
    detail:
      "After routing and worktree admission, decide whether this task needs authoring. An accepted authoring result for the same intent is retained; specify=false also selects the existing Spec.",
    handoff: (
      <>
        The host selects the next step using the current change record. Each
        Agent receives a fresh snapshot of the complete Module contract.
      </>
    ),
    stops:
      "Incompatible change identity, invalid saved state or failed admission stops before authoring or review.",
    spec: "/specs/concorde/specify-loop/execution-reference#specify-loop-composition-state-and-recovery",
  },
  specify: {
    title: "Write or revise Spec",
    kind: "Model-backed capability",
    agent: "spec-author",
    input:
      "Intended behavior, constraints and complete owned and referenced Module Specs.",
    output: "Proposed replacements for the Module’s owned Spec documents.",
    detail:
      "Write clear purpose, requirements, scenarios, entities and relationships. Referenced documents remain read-only. The host validates replacements and affected contract contexts before applying changes.",
    handoff: (
      <>
        <code>concorde-agent-stage-result@2</code> carries proposed documents.
        The host applies accepted replacements; Review Spec sees the resulting
        files in a fresh context.
      </>
    ),
    stops:
      "Missing contract meaning, invalid document structure, foreign document writes or incompatible consumer contracts stop advancement. Accepted progress stays in the candidate.",
    spec: "/specs/concorde/spec-authoring/authoring",
  },
  review_spec: {
    title: "Review Spec",
    kind: "Independent review",
    agent: "spec-reviewer",
    input:
      "The complete current Module contract, task and scoped Spec changes.",
    output:
      "Revision-bound review coverage, findings, gaps and completion status.",
    detail:
      "Review structure and meaning independently: testable promises, consistent scenarios and coherent responsibilities. Affected consumers receive separate reviews in their own contexts. Reviewers do not read implementation code.",
    handoff: (
      <>
        The host stores <code>concorde-review-result@2</code> artifacts and
        returns their references. Current valid evidence can be reused; explicit
        skips remain visible.
      </>
    ),
    stops:
      "Necessary gaps, blocking findings, incomplete coverage and execution failures prevent Spec completion. Advisory findings remain in the result. Repair the contract and resume with fresh context.",
    spec: "/specs/concorde/review/review",
  },
  summarize: {
    title: "Return Spec result",
    kind: "Host result",
    agent: "No model call",
    input: "The selected steps’ outcomes, gaps and artifact references.",
    output:
      "Spec completion or an attributed blocker, with inspectable evidence.",
    detail:
      "Return completed only after the selected Spec steps succeed. A blocked outcome keeps its meaning and progress. This result does not assert that implementation is ready.",
    handoff: (
      <>
        <code>concorde-specify-loop-response@2</code> returns to the caller. Run
        independently to stop here, or let Dev Loop continue with planning in
        the same change.
      </>
    ),
    stops:
      "This is the end of the Spec flow. Planning, implementation, code checks and delivery belong to subsequent workflows.",
    spec: "/specs/concorde/specify-loop/scenarios#scenario.development.specify-loop",
  },
};
const steps: Record<string, Step> = {
  specify_loop: {
    title: "Specify Loop",
    kind: "Composed capability",
    agent: "spec-author → spec-reviewer",
    input:
      "Intended behavior, constraints, authoring/review flags and the complete Module Specs.",
    output:
      "An authored or revised Spec with independent review evidence, or an attributed blocker.",
    detail:
      "Calls concorde-specify-loop, which can also run independently. Its author proposes only owned document replacements, and the host validates them. Independent reviewers assess the complete contract and affected consumers in fresh contexts without reading implementation code.",
    handoff: (
      <>
        <code>concorde-specify-loop-response@2</code> returns{" "}
        <code>completed</code> and artifact references. Dev Loop then enters
        planning or resumes current downstream work in the same change. Spec
        completion alone does not mark implementation ready.
      </>
    ),
    stops:
      "Necessary gaps, blocking findings, incomplete coverage or failed execution stop advancement. specify=false skips authoring; run_reviews=false records a Spec skip only if review was not already required. Accepted authoring and current reviews can be reused. There is no automatic Spec-repair edge.",
    spec: "/specs/concorde/specify-loop/specify-loop",
  },
  plan: {
    title: "Plan",
    kind: "Composed capability",
    agent: "context-assessor → planner",
    input:
      "Complete Specs, intended behavior, constraints and declared implementation file names.",
    output:
      "A context-sufficiency assessment, then a nonempty implementation plan.",
    detail:
      "First assess whether the available contract can answer the task. Then plan the approach, affected components and software acceptance. Both calls use Specs and file listings; neither reads code to fill in missing requirements.",
    handoff: (
      <>
        The Agent returns a <code>plan</code> string in{" "}
        <code>concorde-agent-stage-result@2.data</code>. The host saves{" "}
        <code>plan.md</code> and passes <code>concorde-plan-artifact@1</code>{" "}
        with <code>{"{plan}"}</code> to Tasks through <code>stage_inputs</code>.
      </>
    ),
    stops:
      "Missing contract meaning returns spec_incomplete; contradictions or unsupported intent stop planning. Missing required Spec review, stale context, an empty plan or an invalid Agent result blocks acceptance.",
    spec: "/specs/concorde/planning/plan",
  },
  tasks: {
    title: "Tasks",
    kind: "Model-backed capability",
    agent: "task-author",
    input:
      "Specs, the accepted plan, reserved task IDs and any admitted repair feedback.",
    output:
      "Ordered, initially incomplete tasks with an owner, description and acceptance criteria.",
    detail:
      "Break the plan into concrete software work. Each task states what its implementation must achieve within the granted files and runtime. Host validation, independent review and delivery remain later gates; they are not prerequisites for marking implementation work complete.",
    handoff: (
      <>
        Tasks returns a <code>tasks</code> array in{" "}
        <code>concorde-agent-stage-result@2.data</code>. The host supplies
        Implement with <code>concorde-implementation-task@1</code>:{" "}
        <code>
          {
            "{plan, tasks: [{id, target_id, description, acceptance, complete}]}"
          }
        </code>
        . Reserved IDs arrive separately as{" "}
        <code>concorde-task-identity-constraints@1</code>.
      </>
    ),
    stops:
      "No accepted plan, stale intent, missing contract meaning, empty tasks, duplicate/reserved IDs or tasks already marked complete block acceptance. Tasks may target only the current Module, its declared dependencies or direct children. Repair feedback cannot expand that scope.",
    spec: "/specs/concorde/planning/tasks",
  },
  implement: {
    title: "Implement",
    kind: "Model-backed capability",
    agent: "programmer",
    input:
      "Specs, the plan and task list, authorized code contents, and any admitted code-review feedback.",
    output:
      "Changes to authorized implementation files and the exact accepted tasks marked complete.",
    detail:
      "Write code and tests to meet each task’s acceptance criteria. Spec documents and the registry are outside this write grant. A coordinating Module sends component work through each component’s own context; all writers finish before final shared-candidate checks.",
    handoff: (
      <>
        The host passes <code>concorde-implementation-task@1</code>; the Agent
        returns completed <code>tasks</code> in{" "}
        <code>concorde-agent-stage-result@2.data</code>. Code changes stay in
        worktree files. Validate reads those files and the saved
        completion/revision state, not a code payload in the next request.
      </>
    ),
    stops:
      "Missing or stale tasks, unauthorized writes, necessary Spec gaps, execution errors, changed task identities or unmet acceptance stop advancement. A test requiring inputs outside the grant is recorded as deferred to Host verification, not as a passing test; an actual implementation defect remains incomplete.",
    spec: "/specs/concorde/implementation/implementation",
  },
  validate: {
    title: "Validate",
    kind: "Deterministic capability",
    agent: "No model call",
    input:
      "Current candidate files, Spec declarations and the project’s configured check commands.",
    output:
      "Deterministic Spec validation and code-check results bound to the measured revision.",
    detail:
      "Check machine-verifiable structure: document ownership, IDs, references, required format, file bindings and shared-contract consistency. Run configured checks such as tests, type checking or builds. Structural success does not prove semantic completeness; Review Spec assesses meaning, and Review Code assesses implementation behavior.",
    handoff: (
      <>
        <code>concorde-validate-response@2</code> has a <code>data.checks</code>{" "}
        array with <code>check_id</code>, <code>target_id</code>,{" "}
        <code>status</code>, <code>exit_code</code>, <code>source_digest</code>{" "}
        and <code>log_digest</code> per record. The host saves evidence; Code
        Review receives its own Spec/code snapshot and review input. Raw check
        logs are not fed into Spec-only stages.
      </>
    ),
    stops:
      "Invalid Spec structure, failed check commands or timeouts return failed. Changes during verification produce stale_evidence; unenforceable check permissions block execution. Shared implementation users need current evidence too. This stage has no automatic repair edge.",
    spec: "/specs/concorde/validation/validation",
  },
  review_code: {
    title: "Review Code",
    kind: "Independent review",
    agent: "code-reviewer",
    input:
      "Complete Specs, authorized implementation files and scoped changes at the reviewed revision.",
    output:
      "Behavior findings, review coverage, gaps and revision-bound completion status.",
    detail:
      "Compare implementation and tests with the promised scenarios, interface behavior and task acceptance. Look for concrete defects and regressions, including failure paths and affected consumers. The reviewer is read-only; passing tests do not replace this review.",
    handoff: (
      <>
        The reviewer returns <code>concorde-review-stage-result@2</code>; the
        host stores and publishes <code>concorde-review-result@2</code>. Local
        repair sends that exact typed record plus the prior tasks back to Tasks
        and Implement. Otherwise, Ready checks the saved evidence.
      </>
    ),
    stops:
      "Local blocking code findings without a Spec gap can trigger bounded repair. Spec gaps, incomplete reviews, execution failures or another consumer’s blocking findings stop. Repeated identical feedback waits; exhausting the repair limit stops. Advisory findings do not block readiness.",
    spec: "/specs/concorde/review/review",
  },
  ready: {
    title: "Ready",
    kind: "Host readiness decision",
    agent: "No model call",
    input:
      "Saved task completion, required reviews, configured check results and current candidate digests.",
    output: "A candidate recorded as ready for a separate delivery request.",
    detail:
      "Verify that required evidence is complete and still matches the current task, Specs and code. Ready is an internal host readiness decision, not a separately callable capability. It does not deliver or merge the change.",
    handoff: (
      <>
        The host updates <code>.concorde/worktree.json</code> and returns{" "}
        <code>concorde-dev-loop-response@2</code> with{" "}
        <code>outcome: ready</code>, check results and review artifact
        references. A later Deliver request identifies the change by{" "}
        <code>change_id</code>.
      </>
    ),
    stops:
      "Open contract gaps, unfinished tasks, absent or blocking required reviews, failed/missing checks or stale evidence prevent ready. Changing the candidate during completion verification also stops with stale_evidence.",
    spec: "/specs/concorde/dev-loop/scenarios#scenario.development.dev-loop-ready",
  },
};

const workerDetails: Record<string, Step> = {
  "concorde-specify": specSteps.specify,
  "concorde-plan": steps.plan,
  "concorde-tasks": steps.tasks,
  "concorde-implement": steps.implement,
  "concorde-context-solve": {
    title: "Assess context",
    kind: "Model-backed capability",
    agent: "context-assessor",
    input:
      "The complete selected Module contract, task, constraints and participant declarations.",
    output: "A sufficiency decision or an attributed contract gap.",
    detail:
      "Check that the declared participants and contract supply the meaning needed to plan the task. This stage cannot expand its context or read implementation code to fill a gap.",
    handoff: (
      <>
        A sufficient result allows planning to proceed. Missing promises return{" "}
        <code>spec_incomplete</code> with the question and blocked step.
      </>
    ),
    stops:
      "Missing contract meaning, incompatible participant routing or unsupported intent prevents planning.",
    spec: "/specs/concorde/planning/assessment",
  },
};

type CapabilityDetail = {
  title: string;
  detail: string;
  exchange: string;
  stops: string;
};
const capabilityDetails: Record<string, CapabilityDetail> = {
  "concorde-main": {
    title: "Main",
    detail:
      "Answer from admitted Specs, route work to an owning Module, or prepare and apply an explicit topology proposal.",
    exchange:
      "concorde-main-request@1 → concorde-main-response@2. Carries task and routing hints, then answer/routes; topology actions exchange concorde-topology-proposal@1 and an application ArtifactRef.",
    stops:
      "Missing contract meaning, incompatible intent, invalid routes, stale proposal/application references or rejected topology validation stop the selected action.",
  },
  "concorde-specify-loop": {
    title: "Specify Loop",
    detail:
      "Route one change, author or revise its Spec, then independently review the contract. Stop before planning or implementation.",
    exchange:
      "concorde-specify-loop-request@1 → concorde-specify-loop-response@2. Task, constraints and flags enter; Spec completion or blockers and artifact references return. The same change can continue through Dev Loop.",
    stops:
      "Spec gaps, blocking findings, incomplete reviews and invalid proposals preserve partial progress. Completion does not mark ready or require code review; a new primary-worktree change requires a fresh candidate session.",
  },
  "concorde-dev-loop": {
    title: "Dev Loop",
    detail:
      "Call Specify Loop, then coordinate planning through Ready, reusing current evidence and allowing the bounded code-review repair shown above.",
    exchange:
      "concorde-dev-loop-request@1 → concorde-dev-loop-response@2. Task, constraints, flags and optional change_id enter; outcome, gaps, checks and artifact references return. Step handoffs and candidate files are managed by the host.",
    stops:
      "Any non-advancing step outcome stops the loop, except admitted local code-review repair. A new primary-worktree change first returns worktree_handoff_required so a fresh session can continue in the candidate.",
  },
  "concorde-review": {
    title: "Review",
    detail:
      "Route an independent, read-only review. Spec mode assesses structure and contract meaning; code mode also checks authorized implementation against those promises.",
    exchange:
      "concorde-review-request@1 (task, review_mode: spec|code) → concorde-review-response@2, whose reviews array contains concorde-review-result@2 values. The host binds each review to its input revision.",
    stops:
      "Missing definitions, blocking findings, incomplete coverage, invalid review output or a failed reviewer prevent a successful review. Advisory findings remain visible without blocking.",
  },
  "concorde-issues": {
    title: "Issues",
    detail:
      "List, show, report, reopen or solve an explicit branch-local Issue. Reporting does not stop a worker; solving uses ordinary providers without mandatory triage.",
    exchange:
      "concorde-issues-request@1 → concorde-issues-response@1, including retained Issue records and an optional solving decision. Blockers and review judgments reference immutable reports; only intended behavior enters Spec authoring.",
    stops:
      "Stale selections, failed verification and bounded iteration stops preserve progress. Unsettled choices return needs-decision. Success is ready, never automatic delivery.",
  },
  "concorde-init": {
    title: "Init",
    detail:
      "Propose or apply initial project configuration, a pinned Protocol and an honest Module stub.",
    exchange:
      "concorde-init-request@1 → concorde-init-response@1. Propose returns concorde-project-proposal@1; apply consumes the exact proposal and returns applied status and changed paths.",
    stops:
      "Missing proposal inputs, malformed or stale proposals, conflicting existing project state or unsuccessful file application block initialization. Preview uses action: propose; describe-policy returns use_proposal.",
  },
  "concorde-configure": {
    title: "Configure",
    detail: "Apply the initialized project’s Pi worker model selection.",
    exchange:
      "concorde-configure-request@1 carries concorde-capability-configuration@1. concorde-configure-response@1 returns configuration and status: applied, rather than the common stage-response fields.",
    stops:
      "Invalid configuration, unavailable initialized project state or a failed configuration write blocks application. Preview through describe-policy is not supported by this project action.",
  },
  "concorde-validate": {
    title: "Validate",
    detail:
      "Check Spec structure and configured commands. Standalone candidate validation can also check readiness; inside Dev Loop, required code review precedes Ready.",
    exchange:
      "concorde-validate-request@1 (target_id, task, optional run_checks) → concorde-validate-response@2 with outcome and revision-bound checks. Evidence is saved in the candidate state.",
    stops:
      "Invalid Specs, failing or timed-out checks, unenforceable permissions or changed inputs stop validation. Skipping check execution does not satisfy readiness requirements for those checks.",
  },
  "concorde-deliver": {
    title: "Deliver",
    detail:
      "Verify the integration, stage an independent delivered branch and normally remove the source worktree. A primary-branch merge requires its own explicit primary-session request.",
    exchange:
      "concorde-deliver-request@1 identifies change_id and optional keep_worktree/merge_primary. concorde-deliver-response@2 returns outcome and artifacts, including the delivery receipt.",
    stops:
      "Wrong session/worktree, unfinished or stale evidence, integration conflicts, unsafe cleanup or missing authority for a primary merge stops the requested delivery action. Incomplete cleanup is recorded separately.",
  },
};

function label(id: string) {
  id = id.split(":").at(-1) ?? id;
  return id === "__start__"
    ? "Start"
    : id === "__end__"
      ? "End"
      : (steps[id]?.title ?? id.replace(/_/g, " "));
}

function Diagram({
  graph,
  name,
  studio = false,
  details = steps,
  anchorPrefix = "stage",
}: {
  graph: Graph;
  name: string;
  studio?: boolean;
  details?: Record<string, Step>;
  anchorPrefix?: string;
}) {
  const marker = useId().replace(/:/g, "");
  const [readingSize, setReadingSize] = useState(false);
  const canvas = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (canvas.current)
      canvas.current.scrollLeft =
        (canvas.current.scrollWidth - canvas.current.clientWidth) / 2;
  }, [graph, readingSize]);
  const order = studio
    ? [
        "__start__",
        ...graph.nodes.filter((id) => id !== "__start__" && id !== "__end__"),
        "__end__",
      ]
    : [
        "__start__",
        ...Object.keys(details).filter((n) => graph.nodes.includes(n)),
        "__end__",
      ];
  const position = (id: string) => 55 + order.indexOf(id) * 136;
  const height = order.length * 136;
  return (
    <>
      <div className={styles.diagramTools}>
        <span>Solid: unconditional · Dashed: conditional</span>
        <button
          type="button"
          aria-pressed={readingSize}
          onClick={() => setReadingSize(!readingSize)}
        >
          {readingSize ? "Fit width" : "Reading size"}
        </button>
      </div>
      <div
        ref={canvas}
        className={styles.canvas}
        role="region"
        aria-label={`${name} diagram; scroll to explore`}
        tabIndex={0}
      >
        <svg
          className={readingSize ? styles.readingSize : styles.fit}
          viewBox={`0 0 720 ${height}`}
          role="img"
          aria-labelledby={`${marker}-title ${marker}-desc`}
        >
          <title id={`${marker}-title`}>{name}</title>
          <desc id={`${marker}-desc`}>
            Compiled LangGraph nodes and edges. Select a step for its
            responsibilities. The transition list below provides the same
            topology as text.
          </desc>
          <defs>
            <marker
              id={marker}
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="7"
              markerHeight="7"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
            </marker>
          </defs>
          {graph.edges.map((edge) => {
            const from = position(edge.source),
              to = position(edge.target);
            const adjacent =
              order.indexOf(edge.target) === order.indexOf(edge.source) + 1;
            const repair =
              edge.source === "review_code" && edge.target === "tasks";
            const stop =
              (edge.target === "__end__" && !adjacent) ||
              (edge.source === "specify" && edge.target === "summarize");
            const d = adjacent
              ? `M 360 ${from + 37} V ${to - 37}`
              : stop
                ? `M 515 ${from} H 645 V ${to} H 515`
                : `M 205 ${from} H ${repair ? 65 : 125} V ${to} H 205`;
            return (
              <g
                key={`${edge.source}-${edge.target}`}
                className={repair ? styles.repair : styles.edge}
              >
                <path
                  d={d}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={repair ? 2.5 : 1.5}
                  strokeDasharray={edge.conditional ? "6 5" : undefined}
                  markerEnd={`url(#${marker})`}
                />
                {edge.conditional && (
                  <text
                    x={adjacent ? 373 : stop ? 548 : repair ? 72 : 130}
                    y={adjacent ? (from + to) / 2 + 4 : from - 10}
                    className={styles.edgeLabel}
                  >
                    {repair
                      ? "repair"
                      : stop
                        ? "stop"
                        : adjacent
                          ? studio
                            ? "branch"
                            : "advance"
                          : studio
                            ? "branch"
                            : "resume"}
                  </text>
                )}
              </g>
            );
          })}
          {order.map((id) => {
            const boundary = id.startsWith("__");
            const y = position(id);
            const title = details[id]?.title ?? label(id);
            const node = (
              <g
                className={
                  details[id]?.agent !== "No model call" && details[id]
                    ? styles.agentNode
                    : styles.hostNode
                }
              >
                <title>{id}</title>
                <rect
                  x="205"
                  y={y - 37}
                  width="310"
                  height="74"
                  rx={boundary ? 37 : 12}
                />
                <text
                  x="360"
                  y={y}
                  textAnchor="middle"
                  dominantBaseline="central"
                  className={styles.nodeLabel}
                >
                  {title}
                </text>
              </g>
            );
            return details[id] && !studio ? (
              <a
                key={id}
                href={
                  id === "specify_loop" ? "#specify" : `#${anchorPrefix}-${id}`
                }
                aria-label={`${title}: responsibilities and Spec`}
              >
                {node}
              </a>
            ) : (
              <g key={id}>{node}</g>
            );
          })}
        </svg>
      </div>
      <details className={styles.transitions}>
        <summary>All transitions ({graph.edges.length})</summary>
        <ul>
          {graph.edges.map((edge) => (
            <li key={`${edge.source}-${edge.target}`}>
              <code>{edge.source}</code> → <code>{edge.target}</code> —{" "}
              {edge.conditional ? "conditional" : "unconditional"}
            </li>
          ))}
        </ul>
      </details>
    </>
  );
}

function StepCards({
  details,
  anchorPrefix = "stage",
}: {
  details: Record<string, Step>;
  anchorPrefix?: string;
}) {
  return (
    <div className={styles.stepGrid}>
      {Object.entries(details).map(([id, step]) => (
        <article id={`${anchorPrefix}-${id}`} key={id} className={styles.step}>
          <span className={styles.badge}>{step.kind}</span>
          <h4>{step.title}</h4>
          <p>
            <code>{step.agent}</code>
          </p>
          <p>{step.detail}</p>
          <dl>
            <dt>Receives</dt>
            <dd>{step.input}</dd>
            <dt>Produces</dt>
            <dd>{step.output}</dd>
            <dt>Format & next step</dt>
            <dd>{step.handoff}</dd>
          </dl>
          <div className={styles.stopReason}>
            <h5>When it stops</h5>
            <p>{step.stops}</p>
          </div>
          <Link to={step.spec}>Spec details →</Link>
        </article>
      ))}
    </div>
  );
}

function CapabilityRelations({ name, data }: { name: string; data: FlowData }) {
  const info = data.capability_info[name];
  const callers = Object.keys(data.capability_info).filter((key) =>
    data.capability_info[key].uses.includes(name),
  );
  const links = (names: string[]) =>
    names.map((key, index) => (
      <React.Fragment key={key}>
        {index > 0 && ", "}
        <a href={`#${capabilityAnchor(key)}`}>
          {key.replace(/^concorde-/, "")}
        </a>
      </React.Fragment>
    ));
  return (
    <div className={styles.capabilityRelations}>
      <p>
        {info.public ? "Public Skill" : "Called through composition"} · Context:{" "}
        {info.context_selection} ·{" "}
        {info.deterministic ? "No model calls" : "May call a model"}
      </p>
      <p>
        <strong>Input State:</strong> <code>{info.state.input.join(", ")}</code>
        <br />
        <strong>Output update:</strong>{" "}
        <code>{info.state.output.join(", ")}</code>
      </p>
      {info.uses.length > 0 && (
        <p>
          <strong>Calls:</strong> {links(info.uses)}
        </p>
      )}
      {callers.length > 0 && (
        <p>
          <strong>Called by:</strong> {links(callers)}
        </p>
      )}
    </div>
  );
}

export default function CapabilityFlows({ data }: { data: FlowData }) {
  const [variant, setVariant] = useState(0);
  const groups = useMemo(() => flowNavigation(data), [data]);
  const [selected, setSelected] = useState("development");
  const [query, setQuery] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigation = useRef<HTMLElement>(null);
  const visibleGroups = filterNavigation(groups, query);
  const entries = groups.flatMap((group) => group.entries);
  useEffect(() => {
    const sync = () =>
      setSelected(selectionFromHash(window.location.hash, groups));
    sync();
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, [groups]);
  useEffect(() => {
    if (!window.location.hash) return;
    const frame = requestAnimationFrame(() => {
      const current = navigation.current?.querySelector<HTMLElement>(
        '[aria-current="page"]',
      );
      if (current?.offsetParent) current.scrollIntoView({ block: "nearest" });
      let anchor = selected;
      try {
        anchor = decodeURIComponent(window.location.hash.slice(1));
      } catch {
        /* Use the selected flow. */
      }
      (
        document.getElementById(anchor) ?? document.getElementById(selected)
      )?.scrollIntoView({ block: "start" });
    });
    return () => cancelAnimationFrame(frame);
  }, [selected]);
  const sourceBase = "https://github.com/FTOD/concorde/blob/main/";
  const spec = useBaseUrl("/specs/concorde/query-routing/query-and-routing");
  return (
    <Layout
      title="Capability Flows"
      description="Concorde's State-based Capability execution, branches and bounded feedback loops."
    >
      <main className={styles.page}>
        <aside className={styles.sidebar} aria-label="Flow navigation">
          <div className={styles.sidebarHeading}>
            <strong>Capability Flows</strong>
            <button
              type="button"
              className={styles.sidebarToggle}
              aria-expanded={sidebarOpen}
              aria-controls="flow-navigation"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              {sidebarOpen ? "Close flows" : "Browse flows"}
            </button>
          </div>
          <nav
            ref={navigation}
            id="flow-navigation"
            className={styles.flowNavigation}
            data-open={sidebarOpen}
            aria-label="All flows"
          >
            <label className={styles.searchLabel} htmlFor="flow-search">
              Find a flow
            </label>
            <input
              id="flow-search"
              type="search"
              value={query}
              placeholder="Search flows…"
              onChange={(event) => setQuery(event.target.value)}
            />
            {visibleGroups.map((group) => (
              <div className={styles.navGroup} key={group.title}>
                <h2>{group.title}</h2>
                <ul>
                  {group.entries.map((entry) => (
                    <li key={entry.id}>
                      <a
                        href={`#${entry.id}`}
                        aria-current={
                          selected === entry.id ? "page" : undefined
                        }
                        onClick={() => setSidebarOpen(false)}
                      >
                        {entry.title}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
            {visibleGroups.length === 0 && (
              <p role="status">No flows match “{query}”.</p>
            )}
          </nav>
        </aside>
        <div className={styles.content}>
          <header className={styles.header}>
            <p className={styles.eyebrow}>CONCORDE INTERNALS</p>
            <h1>Inside the Capability Flows.</h1>
            <p>
              Follow what each step does, what it passes on, and what makes it
              stop. The diagrams come from current Flow factories, without
              running Agents.
            </p>
            <p>Choose a Capability or a shared Flow in the sidebar.</p>
          </header>

          <section
            id="specify"
            className={styles.section}
            hidden={selected !== "specify"}
          >
            <div className={styles.sectionHeading}>
              <span className={styles.badge}>INDEPENDENT SPEC FLOW</span>
              <h2>The specify loop</h2>
              <CapabilityRelations name="concorde-specify-loop" data={data} />
              <p>
                Write or revise a Spec, then review it independently. Run this
                flow on its own, or call it as the first step of the development
                loop.
              </p>
            </div>
            <div className={styles.columns}>
              <div>
                <Diagram
                  graph={data.flows["Spec authoring and review"]}
                  name="Specify Loop"
                  details={specSteps}
                  anchorPrefix="spec-stage"
                />
              </div>
              <aside
                className={styles.notes}
                aria-label="Specify loop decisions"
              >
                <h3>One contract, fresh contexts</h3>
                <p>
                  The coordinator first selects the owning Module. After
                  admission, the author and independent reviewers each receive a
                  fresh, complete Spec context. Implementation code is outside
                  their input.
                </p>
                <h3>Choose where to enter</h3>
                <p>
                  <code>specify=false</code> skips authoring. Accepted authoring
                  for the same task can also be retained. Both paths enter
                  Review Spec, which reuses valid evidence or runs the required
                  review.
                </p>
                <h3>Review controls</h3>
                <p>
                  <code>run_reviews=false</code> records a Spec review skip only
                  when no earlier requirement exists. It does not change
                  code-review requirements.
                </p>
                <h3>Repair and resume</h3>
                <p>
                  Gaps, blocking findings or incomplete reviews stop with saved
                  progress. An interrupted reviewer produces an incomplete
                  review report and a failed Review domain outcome; the
                  enclosing flow preserves cancelled or limit_exhausted as the
                  execution and candidate lifecycle classification. No
                  interruption completes Spec preparation or selects an
                  automatic retry. Resume through admission with current inputs;
                  a contract gap needs explicit repair. There is no automatic
                  Spec-repair edge.
                </p>
                <div className={styles.callout}>
                  <h3>Completed Spec → continue development</h3>
                  <p>
                    Successful Spec steps return <code>completed</code>.
                    Standalone execution ends here.
                  </p>
                  <p>
                    Dev Loop calls this same capability, then proceeds to
                    planning or resumes current downstream work in the same
                    change. Implementation reaches <code>ready</code> after its
                    own checks and review.
                  </p>
                  <a href="#development">Follow the development loop →</a>
                </div>
              </aside>
            </div>
            <h3>Spec step responsibilities & handoffs</h3>
            <StepCards details={specSteps} anchorPrefix="spec-stage" />
            <details className={styles.transitions} id="specify-studio">
              <summary>Full Specify Loop invocation</summary>
              <Diagram
                graph={data.capabilities["concorde-specify-loop"]}
                name="Specify Loop invocation"
                studio
              />
            </details>
          </section>

          <section
            id="development"
            className={styles.section}
            hidden={selected !== "development"}
          >
            <div className={styles.sectionHeading}>
              <span className={styles.badge}>EXECUTABLE FLOW</span>
              <h2>The development loop</h2>
              <CapabilityRelations name="concorde-dev-loop" data={data} />
              <p>
                Start with <a href="#specify">Specify Loop</a>, then plan,
                implement and verify the change. Select its node to explore the
                Spec steps.
              </p>
            </div>
            <div className={styles.controls}>
              <label htmlFor="flow-variant">Entry & scope</label>
              <select
                id="flow-variant"
                value={variant}
                onChange={(e) => setVariant(Number(e.target.value))}
              >
                {data.loops.map((loop, index) => (
                  <option key={loop.label} value={index}>
                    {loop.label}
                  </option>
                ))}
              </select>
            </div>
            <div className={styles.columns}>
              <div>
                <Diagram
                  graph={data.loops[variant]}
                  name={data.loops[variant].label}
                />
              </div>
              <aside
                className={styles.notes}
                aria-label="Development decisions"
              >
                <h3>What moves execution forward?</h3>
                <p>
                  <code>completed</code> or <code>ready</code> selects the
                  successor. Other outcomes stop, except the admitted
                  code-review repair below.
                </p>
                <div className={styles.callout}>
                  <h3>Feedback → revised tasks</h3>
                  <p>
                    Local blocking code findings return to <code>tasks</code>,
                    then implementation, validation and independent review.
                  </p>
                  <p>
                    Default: at most{" "}
                    <strong>
                      {data.policy.max_repair_iterations} repair iterations
                    </strong>
                    . The candidate keeps its persisted policy. Repeated
                    feedback waits; an exhausted limit stops.
                  </p>
                </div>
                <h3>Resume is re-admission</h3>
                <p>
                  Current plan, task and code evidence determine the entry.
                  Nodes skipped by a resume remain declared so a later repair
                  can re-enter tasks. Internal Flows are stateless: resume
                  re-enters the public admission boundary using host-saved
                  candidate evidence, not an internal LangGraph checkpoint.
                </p>
                <h3>Review controls</h3>
                <p>
                  <code>run_reviews=false</code> records explicit skips inside
                  review nodes. Current valid reviews can be reused. A Module
                  without implementation bindings omits the code-review node.
                </p>
                <h3>Stops remain visible</h3>
                <p>
                  Spec gaps wait for clarification. Failed checks, execution
                  failures and incompatible feedback stop. Interrupted reviewers
                  retain incomplete review reports and failed Review domain
                  outcomes, while cancellation and limits propagate with
                  distinct execution errors and candidate lifecycle
                  classifications. They never select code-review repair or
                  permit dependent work to advance; they are not extra graph
                  nodes.
                </p>
                <p>
                  Deferred component checks may stop after implementation, or
                  after Spec review on a validation-only resume.
                </p>
                <Link
                  to={
                    "/specs/concorde/dev-loop/execution-reference#development-ai-and-human-feedback"
                  }
                >
                  Read the feedback and recovery contract →
                </Link>
              </aside>
            </div>
            <div id="handoffs" className={styles.handoffs}>
              <h3>How information moves</h3>
              <p>
                Every Capability consumes its declared State and returns a State
                update. The host checks the result, saves accepted artifacts and
                prepares the next node’s input channels. Hosts, model launchers
                and permissions stay outside State in trusted runtime context.
                An arrow never transfers a worker’s private conversation.
              </p>
              <ol className={styles.sequence}>
                <li>
                  <strong>Capability call → response</strong>
                  <span>
                    Public calls use{" "}
                    <code>concorde-capability-invocation@3</code> with a typed{" "}
                    <code>input</code>. The result is{" "}
                    <code>concorde-capability-result@3</code> with a typed{" "}
                    <code>output</code> or admission errors. These wire adapters
                    preserve existing callers while nodes use State contracts.
                    Host-backed graphs retain the envelope in a result channel.
                    The host reads <code>outcome</code>,<code>gaps</code>,{" "}
                    <code>checks</code> and <code>artifacts</code> to choose the
                    next step.
                  </span>
                </li>
                <li>
                  <strong>Model-backed Capability → worker result</strong>
                  <span>
                    Ordinary workers receive{" "}
                    <code>concorde-agent-stage-context@4</code>
                    containing a <code>concorde-context-snapshot@6</code> and
                    return <code>concorde-agent-stage-result@2</code>. Reviewers
                    use <code>concorde-review-stage-context@4</code> and{" "}
                    <code>concorde-review-stage-result@2</code> instead. These
                    remain compatible process envelopes for the model node’s
                    State fields, not a separate Agent identity or registry.
                  </span>
                </li>
                <li>
                  <strong>Accepted output → next stage</strong>
                  <span>
                    A typed value has{" "}
                    <code>{"{type_id, schema_version, data}"}</code>;
                    <code>@1</code> in a type label means{" "}
                    <code>schema_version: 1</code>. Plans, tasks and admitted
                    repair feedback travel in the next snapshot’s{" "}
                    <code>stage_inputs</code>. Specs and code remain files, read
                    through a fresh authorized snapshot.
                  </span>
                </li>
                <li>
                  <strong>Artifacts and saved state</strong>
                  <span>
                    An <code>ArtifactRef</code> is{" "}
                    <code>{"{id, path, digest}"}</code>: a project-relative file
                    path and a <code>sha256:</code> digest identifying its exact
                    bytes. The host verifies references before reuse.{" "}
                    <code>.concorde/worktree.json</code> stores candidate
                    progress and evidence;
                    <code>.concorde/work/&lt;target-id&gt;/</code> holds plans
                    and auxiliary files. They are host-managed records, not an
                    extra public message type.
                  </span>
                </li>
              </ol>
              <details className={styles.wireExample}>
                <summary>Example: the plan passed from Plan to Tasks</summary>
                <p>
                  This illustrative value is one entry in{" "}
                  <code>snapshot.data.stage_inputs</code>. The request that
                  calls Tasks separately identifies the task, Module and change.
                </p>
                <pre>
                  <code>
                    {JSON.stringify(
                      {
                        type_id: "concorde-plan-artifact",
                        schema_version: 1,
                        data: {
                          plan: "Show each step’s responsibility, handoff format and stop conditions.",
                        },
                      },
                      null,
                      2,
                    )}
                  </code>
                </pre>
                <p>
                  Tasks also receives{" "}
                  <code>concorde-task-identity-constraints@1</code> containing
                  reserved IDs. The repair path adds the prior tasks and the
                  verified <code>concorde-review-result@2</code>. Ordinary Plan
                  → Tasks handoff carries no code or review transcript.
                </p>
              </details>
              <Link to={development + "interfaces#wire-contracts"}>
                Request, response and handoff contracts →
              </Link>
              <div className={styles.stopLegend}>
                <h4>Stopping is not always execution failure</h4>
                <dl>
                  <dt>
                    <code>spec_incomplete</code>
                  </dt>
                  <dd>
                    A necessary promise is missing or ambiguous; report the
                    question and blocked step, then wait for contract
                    clarification.
                  </dd>
                  <dt>
                    <code>conflicting</code>
                  </dt>
                  <dd>
                    Contracts, intent or blocking review findings conflict. Only
                    admitted local code-review findings can select the bounded
                    repair path.
                  </dd>
                  <dt>
                    <code>unsupported</code>
                  </dt>
                  <dd>
                    The requested behavior is outside a known supported
                    boundary; that is different from an unspecified contract.
                  </dd>
                  <dt>
                    <code>failed</code>
                  </dt>
                  <dd>
                    Execution or deterministic checks failed. The worktree is
                    preserved; this outcome does not automatically re-enter
                    implementation.
                  </dd>
                </dl>
                <p>
                  These are capability <code>output.data.outcome</code> values.
                  The outer result has its own <code>status</code> and
                  <code>errors</code>; malformed inputs, permission problems and
                  stale artifacts can stop admission before any step runs.
                  Cancellation and execution limits have dedicated error codes.
                </p>
              </div>
            </div>
            <h3 id="stages" className={styles.anchor}>
              Step responsibilities & handoffs
            </h3>
            <p>
              Names in the graph match the cards below. Each card separates the
              work itself from its data handoff and stopping rules.
            </p>
            <StepCards details={steps} />
            <details className={styles.transitions} id="studio">
              <summary>Full Dev Loop invocation</summary>
              <Diagram
                graph={data.capabilities["concorde-dev-loop"]}
                name="Dev Loop invocation"
                studio
              />
            </details>
          </section>

          <section
            id="routing"
            className={styles.section}
            hidden={selected !== "routing"}
          >
            <span className={styles.badge}>EXECUTABLE DISCOVERY FLOW</span>
            <h2>Routing a read-only diagnosis</h2>
            <p>
              <code>Discovery Flow → owner admission → review Flow</code>. The
              coordinator selects responsibility; it has no implementation
              contents.
            </p>
            <ol className={styles.sequence}>
              <li>
                <strong>Freeze entry context</strong>
                <span>
                  Original task, ordered constraints, routing hints and the
                  entry Module's complete owned/reference context.
                </span>
              </li>
              <li>
                <strong>Coordinator / route</strong>
                <span>
                  Select target and focus, request explicit context expansion,
                  or return a blocked outcome. Each expansion starts a fresh
                  invocation; the loop is bounded by the Module count.
                </span>
              </li>
              <li>
                <strong>Host admission</strong>
                <span>
                  Validate context identity, admitted target and focus; require
                  one route. Bind the original task and constraints. Explicit
                  conflicting echoes fail before review.
                </span>
              </li>
              <li>
                <strong>Independent reviewer</strong>
                <span>
                  Code diagnosis uses the code-reviewer Capability with the
                  selected Module's authorized code. Spec review uses
                  spec-reviewer. Both model Capabilities are read-only.
                </span>
              </li>
              <li>
                <strong>Return scoped evidence</strong>
                <span>
                  Findings, coverage, input revision and completion status. A
                  standalone diagnosis needs no change ID and creates no
                  candidate worktree.
                </span>
              </li>
            </ol>
            <p className={styles.callout}>
              Expansion feeds back to a new frozen context and coordinator
              invocation. A missing contract stops the dependent step; it does
              not authorize source access or automatic repair.
            </p>
            <p>
              <strong>Handoff:</strong> the coordinator receives{" "}
              <code>concorde-main-stage-context@4</code> and returns
              <code>concorde-main-stage-result@2</code> with routes, gaps or an
              expansion request. The host admits the selected route’s
              <code>target_id</code>, <code>focus_id</code>, <code>task</code>{" "}
              and <code>constraints</code>, then creates a separate
              <code>concorde-review-stage-context@4</code> for the reviewer.
              Invalid or contradictory route fields stop admission.
            </p>
            <a href={spec}>Routing contract →</a>
            {" · "}
            <Link
              to={
                "/specs/concorde/review/scenarios#scenario.development.standalone-review"
              }
            >
              Standalone review scenario →
            </Link>
          </section>

          {entries
            .filter(
              (entry) =>
                entry.kind === "capability" &&
                data.capability_info[entry.key].public &&
                !["development", "specify"].includes(entry.id),
            )
            .map((entry) => (
              <section
                id={entry.id}
                key={entry.id}
                className={styles.section}
                hidden={selected !== entry.id}
              >
                {selected === entry.id && (
                  <>
                    <span className={styles.badge}>CAPABILITY</span>
                    <h2>{capabilityDetails[entry.key].title}</h2>
                    <CapabilityRelations name={entry.key} data={data} />
                    <p>{capabilityDetails[entry.key].detail}</p>
                    <div className={styles.columns}>
                      <div>
                        <Diagram
                          graph={data.capabilities[entry.key]}
                          name={`${entry.title} invocation`}
                          studio
                        />
                      </div>
                      <aside className={styles.notes}>
                        <h3>Input → result</h3>
                        <p>{capabilityDetails[entry.key].exchange}</p>
                        <h3>When it stops</h3>
                        <p>{capabilityDetails[entry.key].stops}</p>
                        <h3>Admission and execution</h3>
                        <p>
                          The host validates the typed request, binds the
                          workspace and admits context before executing the
                          selected flow. The result preserves permission
                          policies and stage events.
                        </p>
                        <Link to={development + "interfaces"}>
                          Capability contracts →
                        </Link>
                      </aside>
                    </div>
                  </>
                )}
              </section>
            ))}

          {entries
            .filter(
              (entry) =>
                entry.kind === "capability" &&
                !data.capability_info[entry.key].public,
            )
            .map((entry) => (
              <section
                id={entry.id}
                key={entry.id}
                className={styles.section}
                hidden={selected !== entry.id}
              >
                {selected === entry.id && (
                  <>
                    <span className={styles.badge}>CAPABILITY</span>
                    <h2>{entry.title}</h2>
                    <CapabilityRelations name={entry.key} data={data} />
                    <p>
                      {workerDetails[entry.key]?.detail ??
                        "This State-based model Capability runs with its own instructions, tools and permission profile. It shares the same inventory and composition relation as deterministic and composed nodes."}
                    </p>
                    <p>
                      This Capability receives its Module from its caller and is
                      available through declared composition. It has no public
                      Skill.
                    </p>
                    <Diagram
                      graph={data.capabilities[entry.key]}
                      name={`${entry.title} capability`}
                      studio
                    />
                    {workerDetails[entry.key] && (
                      <StepCards
                        details={{ [entry.key]: workerDetails[entry.key] }}
                        anchorPrefix="internal-stage"
                      />
                    )}
                    {entry.key === "concorde-specify" ? (
                      <p>
                        Called by <a href="#specify">specify-loop</a>, which
                        also performs independent Spec review.
                      </p>
                    ) : (
                      <p>
                        Explore the enclosing{" "}
                        <a href="#development">development loop</a>.
                      </p>
                    )}
                  </>
                )}
              </section>
            ))}

          {entries
            .filter((entry) => entry.kind === "flow")
            .map((entry) => (
              <section
                id={entry.id}
                key={entry.id}
                className={styles.section}
                hidden={selected !== entry.id}
              >
                {selected === entry.id && (
                  <>
                    <span className={styles.badge}>SHARED FLOW</span>
                    <h2>{entry.title}</h2>
                    <p>
                      Inspect the current executable flow. Conditional
                      transitions choose admitted outcomes; repeated work
                      follows the flow’s declared limits.
                    </p>
                    <Diagram
                      graph={data.flows[entry.key]}
                      name={entry.title}
                      studio
                    />
                    <Link to="/specs/concorde/harness/graphs-and-loops">
                      Flow and Loop contracts →
                    </Link>
                  </>
                )}
              </section>
            ))}

          <section
            id="coverage"
            className={styles.section}
            hidden={selected !== "coverage"}
          >
            <h2>What is implemented?</h2>
            <p>
              Public entries execute LangGraph Flows for admission and
              capability dispatch. Query, topology, Spec authoring and review,
              planning, development and Issue-solving Flows are composed into
              those entries. Component coordination, batch work and recursive
              Agent decisions also use executable Flow factories shown in the
              catalog.
            </p>
            <p>
              The{" "}
              <Link to="/specs/concorde/harness/graphs-and-loops">
                Flow and Loop contracts
              </Link>{" "}
              define the terminology and boundaries. Runtime context selects
              concrete component and Agent instances. The catalog shows their
              scheduling structure; it does not claim an admitted delegation
              tree. Atomic delivery remains a deterministic transaction node.
            </p>
            <p>
              These views describe possible compiled transitions, not a live
              trace or proof that a candidate passed review. Source links track
              main; the byte digests below identify the inputs used for this
              page.
            </p>
            <details>
              <summary>Source factories & build fingerprints</summary>
              <ul className={styles.sources}>
                {data.sources.map((source) => (
                  <li key={source.path}>
                    <a href={sourceBase + source.path}>{source.path}</a>
                    <code>sha256:{source.digest}</code>
                  </li>
                ))}
              </ul>
            </details>
          </section>
        </div>
      </main>
    </Layout>
  );
}
