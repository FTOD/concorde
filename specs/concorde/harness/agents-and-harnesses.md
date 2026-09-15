```concorde-document
{
  "id": "document.harness.agents-and-harnesses",
  "owner": "module.harness",
  "main_visible": true
}
```

# Agents and Harnesses

## Usage & Contract

This document defines the required Agent model for Concorde Framework. The requirements below are
the standard for implementation review; an existing role prompt or launcher is not evidence that
the complete model is implemented. Agent, worker, Harness and Capability are Framework entities, not
new Concorde Spec Protocol target kinds. Their providing Modules retain the explicit registered Spec
structure.

### The Agent and Harness model

**Harness = context + control flow + models + permissions and environment, per worker.**
**Agent = role Spec + worker profile (task contract, workspace, tools, children, timeout).**
**Invocation = Agent + Module/version + admitted artifacts + actual grant + model selection.**

| Entity | Meaning | Relationships |
| --- | --- | --- |
| Agent Spec | The worker's authored role `spec.md`, defining its responsibilities, goals and behavioral contract | Rendered after the common worker rules into the worker's instructions |
| Worker profile | The Python definition of one Agent: its task contract, workspace kind, Pi tools, children and timeout | Is the per-worker part of the Harness; bound with the Agent Spec into an `AgentBinding` |
| Task contract | The one task an Agent fulfils: phase and action, admitted context type and result type, effects, admitted stage artifacts, permitted result fields and outcomes | Admitted by the host before launch and by the executor again before and after the process |
| Worker | One Pi coding agent process run in RPC mode for exactly one invocation | Executes one Agent under its grant and returns one submitted result |
| Child agent | A lightweight pi-subagents Markdown definition a worker may delegate a focused subtask to | Runs inside its worker's process, under the same gate, one level deep |
| Common worker rules | The tier-one rules every worker follows (`prompts/workers/common.md`) | Precede every role Spec in the rendered instructions; the Protocol rule bundle follows |
| Agent invocation | One execution of an Agent for a specific task | Receives its frozen context kinds, effective permissions, model selection and a fresh identity |
| Harness | The organized execution environment supporting a worker | Integrates context assembly, the Flow, the worker profile, the Pi worker runtime, permissions and system environment |
| Capability | Functionality a worker can use, or that can be composed to provide further functionality | Deterministic when it makes no model call; otherwise it launches workers through the Harness |
| Tool | A callable interface a worker uses | Pi built-ins filtered by the profile, plus `submit_result`, `run_checks` and `subagent` |
| Skill | An instruction artifact for the developer's external agent runtime | Distribution owns, renders and installs it; the external runtime uses it to invoke a public Capability through Development |
| Constraints/Permissions | Limits on information, operations, effects and execution | Compiled from the contract's effects and the host grant and enforced outside model discretion |

A **deterministic capability** is Python that makes no model call: context resolution, permission
compilation, validation, delivery and installation are examples. A **model-backed capability**
calls a model at least once through a worker. The distinction names whether a model participates,
not whether output is reproducible: deterministic Python may still observe Git, files or
subprocesses. A Flow node is one or the other, and a model-backed leaf is one worker invocation whose
Pi tool loop stays inside its own process.

A model is a resource used through the Harness. Responsibilities, task information and admitted tool
descriptions may all be presented as model context, while retaining distinct identities and
contracts. Loading an instruction or mentioning a tool does not itself grant authority. Skills are
not worker context: a Skill is the installed projection of a public Capability for the developer's
own agent runtime. The four context kinds an invocation receives are defined in [context](context.md).


### A1. Agent Spec and Python definition

Every named Agent MUST have an identifiable authored role `spec.md` under `agents/<name>/`. It MUST
describe its responsibilities, goals, accepted input and feedback, expected results, completion
conditions, and behavior on missing information, failure or a required human decision, under exactly
those six headings after a `# concorde-<name>` title. Its rendered instructions are the common worker
rules followed by that Spec; they MUST remain traceable to both sources and MUST NOT replace the
Spec as the behavioral authority.

One Python module MUST define each named Agent as its worker profile and explicitly bind its Spec,
task contract, workspace kind, tools, children and timeout. The binding MUST identify the sources and
versions needed to reproduce execution: the Spec digest, the rendered instructions digest, the
profile digest (which covers each child definition's bytes), the build manifest digest and the
timeout. A missing Spec, an inconsistent profile or a stale build MUST prevent the invocation from
starting. Changing a binding requires fresh admission and invalidates evidence that depended on its
old identity.

An Agent's `spec.md` is its responsibility contract. The project task's Spec context and
implementation context are separate admitted inputs about the work to perform. Neither set
implicitly grants access to the other's neighboring files. This filename convention adds no filename
requirement to ordinary Module Specs.


### A2. Worker profile and Harness

A Harness MUST have an explicit identity and inspectable configuration. The per-worker part is the
worker profile: its workspace kind (`capsule` for Spec-only work, `project` for work that reads or
writes implementation files), its Pi tools, its children, its timeout and its contract's effects.
The shared part is the host environment allowlist, the Pi worker runtime and the LangGraph Flows. A
profile grants tools from Pi's built-ins (`read`, `grep`, `find`, `ls`, `edit`, `write`, `bash`) and
`run_checks`; the host adds `submit_result` to every worker and `subagent` to every worker with
children. `edit` and `write` require a write effect, and implementation reads require a project
workspace.

Each invocation MUST receive an effective configuration restricted by the profile and host-issued
authority. The model, thinking level and timeout are project configuration, resolved per worker and
per child as defined in [execution](execution.md); they are not authority and cannot widen a grant.
Ambient discovery MUST NOT silently add tools, context, credentials or environment access: a worker's
Pi process starts with sessions, context files, skills, prompt templates, themes and discovered
extensions disabled, and its own configuration directory holds only what the host placed there.

The Harness MUST connect decision, action, observation and feedback through a LangGraph Flow as
required by [Agent Flows, Agent Loops and feedback](graphs-and-loops.md). Execution evidence MUST
distinguish model reasoning, tool execution and human decisions. A model adapter, virtual
environment or bag of tools alone is not the complete Harness.


### A3. Capability use and composition

A Capability MUST declare its identity, purpose, inputs, results, effects, constraints and relevant
failure or retry behavior. Its meaning is the functionality it provides, not the Python file that
implements it. A deterministic operation, a composed operation or an Agent Flow may provide a
Capability when its complete contract is explicit.

A worker's available tools form part of its capability context together with the Module's declared
external references. Descriptions supplied to the model and the tools the runtime admits MUST
resolve to the same contracts. An unavailable or unauthorized tool MUST fail before its effects
occur.

Composition MUST preserve required input/output contracts and propagate failure and effect limits.
An outer Capability cannot grant an inner operation more authority than the invoking worker has.
Runtime host composition and worker-available tools MUST be distinguishable; a host's ability to
compose an operation does not make it callable by every worker. Existing `capabilities/` modules
and their exposure and context-selection properties describe Concorde's current host adapter; the
Development Module registers that inventory.


### A4. Constraints, context and invocation

Constraints/Permissions MUST cover applicable context access, tool calls, file and process effects,
network and credential use, and execution limits. The trusted runtime MUST enforce the effective
boundary; instructions alone are insufficient. Effective permissions MUST be a subset of both the
Agent's contract effects and the host authority for this invocation. How the boundary is enforced
is defined in [permissions](permissions.md) and [execution](execution.md).

Every invocation MUST bind its task, admitted context kinds, Agent binding, contract, effective
policy, model selection and execution identity. State and evidence MUST remain attributable to that
invocation. A repeated call is a fresh invocation, and resumption admits only the state and artifacts
authorized by the selected Flow. Raw predecessor conversations are not an implicit context channel.

Completion MUST distinguish a successful result, a missing-information gap, a required human
decision, cancellation, an execution failure and exhaustion of the configured execution limits.
Failure MUST NOT cause an automatic retry with broader permissions. Feedback that requests a new
goal, different context or additional authority MUST pass admission again before dependent work.


### A5. One-level delegation

A worker MAY delegate a focused subtask only to a child its own profile declares, and only through
its `subagent` tool. A child is a lightweight pi-subagents Markdown definition under
`agents/<worker>/children/<child>.md`: its frontmatter names it, describes it, lists its tools from
`read`, `grep`, `find`, `ls`, `bash` and `run_checks`, replaces Pi's base prompt and inherits no
project context, global context or skills; it names no model or thinking level, which project
configuration supplies. A child runs as a foreground session inside its worker's process, under the
same grant and gate, with exactly its declared tools. A child cannot delegate further and cannot
submit the worker's result.

What a child does is not a Concorde contract. Its answer is evidence the worker verifies against the
granted files, and only the worker's single submitted result leaves the process. Delegation between
workers does not exist: Flows compose workers, and one worker never starts another. The capability
ceiling that bounds delegation, and its enforcement, are defined in [execution](execution.md).


### Common worker rules

Worker instructions have two tiers. The first tier is common to every worker: the rules in
`prompts/workers/common.md` (how to read the input and the granted files, what the tool gate
refuses, how to submit exactly one result, how to report gaps and how to use children) and the
Protocol rule bundle, which the host appends to every system prompt. The second tier is the worker's
own profile and role Spec, managed with the Flow that launches it; its static model selection is
exposed in project configuration.


### Registered workers

The twelve workers are each one Python module under the top-level `agents/` package, declared in
`agents/__init__.py`. Exact Agent source files have the single authoritative owner
`entity.harness.agent-definitions`; a capability that launches a worker does not own its definition.
Each rendered `generated/agents/<hyphenated>.md` holds the common worker rules followed by that
worker's role Spec, and the child definitions are build sources of that output.

```concorde-agents
[
  {
    "id": "answerer",
    "workspace": "capsule",
    "capabilities": ["main"],
    "tools": ["find", "grep", "ls", "read"],
    "children": []
  },
  {
    "id": "code-reviewer",
    "workspace": "project",
    "capabilities": ["review"],
    "tools": ["find", "grep", "ls", "read"],
    "children": ["scout", "verifier"]
  },
  {
    "id": "context-assessor",
    "workspace": "capsule",
    "capabilities": ["context-solve", "plan"],
    "tools": ["find", "grep", "ls", "read"],
    "children": []
  },
  {
    "id": "investigator",
    "workspace": "project",
    "capabilities": ["reflections-triage"],
    "tools": ["bash", "find", "grep", "ls", "read"],
    "children": ["scout"]
  },
  {
    "id": "planner",
    "workspace": "capsule",
    "capabilities": ["plan"],
    "tools": ["find", "grep", "ls", "read"],
    "children": ["scout"]
  },
  {
    "id": "programmer",
    "workspace": "project",
    "capabilities": ["implement"],
    "tools": ["bash", "edit", "find", "grep", "ls", "read", "run_checks", "write"],
    "children": ["planner", "scout", "verifier"]
  },
  {
    "id": "router",
    "workspace": "capsule",
    "capabilities": ["dev-loop", "main", "review", "specify-loop"],
    "tools": ["find", "grep", "ls", "read"],
    "children": []
  },
  {
    "id": "spec-author",
    "workspace": "capsule",
    "capabilities": ["specify"],
    "tools": ["find", "grep", "ls", "read"],
    "children": []
  },
  {
    "id": "spec-reviewer",
    "workspace": "capsule",
    "capabilities": ["review"],
    "tools": ["find", "grep", "ls", "read"],
    "children": ["consistency", "fact-check"]
  },
  {
    "id": "task-author",
    "workspace": "capsule",
    "capabilities": ["tasks"],
    "tools": ["find", "grep", "ls", "read"],
    "children": []
  },
  {
    "id": "topology-author",
    "workspace": "capsule",
    "capabilities": ["main"],
    "tools": ["find", "grep", "ls", "read"],
    "children": []
  },
  {
    "id": "topology-designer",
    "workspace": "capsule",
    "capabilities": ["main"],
    "tools": ["find", "grep", "ls", "read"],
    "children": []
  }
]
```

Deterministic validation requires this block to equal the Agent inventory declared in code: the
same identifiers, workspace kinds, sorted profile tools, sorted child names and the sorted hyphenated
names of every capability module whose `AGENTS` includes that worker. The block is intentional
redundancy so that this Spec explains the catalog without reading Python; it never adds a worker
that code does not implement. `capabilities` records which Development capabilities launch the
worker; it is not the worker's capability context.


### Task contracts

Each worker fulfils exactly one task contract. The table uses these typed pairs: **stage** =
`concorde-agent-stage-context` / `concorde-agent-stage-result`, **review** =
`concorde-review-stage-context` / `concorde-review-stage-result`, **discovery** =
`concorde-main-stage-context` / `concorde-main-stage-result`, and **topology** =
`concorde-topology-author-context` / `concorde-topology-author-result`.

| Worker | Pair and phase/action | Admitted stage artifacts | Result and authority |
| --- | --- | --- | --- |
| answerer | discovery; route/ask | none | Direct answer, expansion or gaps; no routes, topology design or writes |
| router | discovery; route/route | none | One owning Module route, expansion or gaps; no implementation or writes |
| topology-designer | discovery; route/design-topology | none | Candidate topology from selected complete Specs and the explicit inventory; no document bodies or writes |
| spec-author | stage; specify | none | Structured document replacements, applied by the host |
| topology-author | topology; topology-author | none | Only candidate-owned documents for host application |
| spec-reviewer | review; spec-review | none | Independent Spec findings; no author artifacts or writes |
| context-assessor | stage; context-solve | none | Sufficient, incomplete, unsupported or conflicting assessment; no authored artifacts |
| planner | stage; plan | optional concorde-plan-artifact | Plan only; external references readable; no source contents or writes |
| task-author | stage; tasks | required concorde-plan-artifact and concorde-task-identity-constraints; optional concorde-implementation-task, concorde-review-result and concorde-task-scope-feedback | Implementation acceptance tasks with new IDs outside the reserved set; no source contents or writes |
| programmer | stage; implementation | required concorde-implementation-task; optional concorde-review-result | Fulfilled tasks only; may write the selected Module's listed implementation paths |
| code-reviewer | review; code-review | none | Independent code findings; authorized code read-only |
| investigator | stage; implementation | required concorde-reflection-selection | Reflection findings only; authorized code read-only |

The host selects the worker before freezing its context and compiling its permissions, and the
executor checks that selection again before any process starts. A context of the wrong type or
phase, a wrong discovery action, unadmitted or missing required artifacts, implementation contents
admitted to a worker without implementation reads, and a policy wider than the contract are
rejected. After the process, a result whose type, outcome or populated fields the contract does not
permit is rejected: disallowed authored fields as `permission_denied`, other contract violations as
`invalid_completion`. Reviews additionally bind the matching `review_mode`. Spec-only workers never
receive source contents or project writes; the programmer receives only the bound Module's
authorized code; read-only code review and investigation grants enumerate the frozen implementation
files, so a listed directory cannot widen them to hidden, excluded or later-created files.

The programmer executes useful tests its grant supports. A listed test does not grant transitive
imports or repository fixtures; an unavailable input is recorded as deferred host verification,
never as a passing result, and actual defects and unfulfilled obligations still prevent completion.
The investigator retains the implementation phase on the stage wire while its own contract admits
only the reflection selection; reusing a wire pair does not merge artifact or result permissions.

Every phase, target, repair and review has a fresh invocation identity and frozen context. Sharing a
role never shares a conversation, private reasoning, stage inputs or write grant between workers.
Only explicitly admitted structured artifacts cross stages.

## Architecture & Realization

### Responsibilities and implementation boundaries

The common Development host dispatches the declared provider and Flow contracts and schedules
invocations. Planning owns plan/task semantics, Implementation owns task fulfillment, and each
composing Flow owns its ordering and stopping policy. This Module's worker executor verifies and
launches workers through the Pi worker runtime and admits their results; its permissions service
compiles effective boundaries; its context service supplies the admitted context kinds; its Agent
model resolves definitions and bindings. The Distribution build renders and distributes instruction
views with source identity.
