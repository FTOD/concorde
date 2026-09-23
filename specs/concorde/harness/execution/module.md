# Agent execution

## Purpose

Agent execution runs Concorde's model work and decides when a model's answer counts as a result.
It runs one Agent call, or one pi workflow of several calls and Host steps, through Pi's
pi-subagents extension, with a generic native driver that providers extend through Agent hooks and
workflow hooks. It owns the result gate, launch preflight, the Host-step protocol, the pinned native
runtime, model selection, and Concorde's LangGraph mechanism with its Graph Spec check. Providers
under Operations rely on it to run their Agents; the Pi session relies on it to launch prepared
calls. It never imports a provider, does not choose Agents, context or the next capability, and does
not confine what a running Agent reads, writes or sends: those limits are not enforced.

## Terminology

| Term | Definition |
| --- | --- |
| Agent call | One launch of one Agent by pi-subagents, in a fresh context, from an Agent definition file the Host prepared for exactly this call. |
| Workflow | An authored pi-subagents script that orders the Agent calls and Host steps of one capability, such as reviewing every Module of a scope. |
| Graph | A LangGraph `StateGraph` whose State, nodes and edges are declared before it is compiled. |
| Proposal | The one structured result an Agent call submits, which stays untrusted data until the Host accepts it. |
| Host step | One finite, deterministic Host command run for an Agent call or a Workflow, such as staging a proposal; it never starts or waits for a model. |
| Result gate | The Host service of one Agent call that stores its proposal, stages it after the run and accepts it only after independent checks of the run's outcome and the current inputs. |
| Agent hook | The provider code, named by an entry point in an Agent definition, that prepares the stage of one call of that Agent, validates its proposal and applies an accepted one. |
| Workflow hook | The provider code, named by an entry point in a capability declaration, that prepares a Workflow's first Agent calls and answers each of its Host steps. |
| Model selection | The model, thinking level and time limit resolved for one Agent from the project configuration. |
| Terminal Agent Operation | The Graph with one node that validates an Agent's typed input, calls a trusted Agent service supplied by its embedding and validates the typed result. |
| Graph Spec | The section of an implementation document that states one compiled Graph's State, Nodes and Edges and draws it in a flowchart bound to that Graph. |
| [Agent](../../agents/module.md#concept.agents.agent) | |
| [Agent definition](../../agents/module.md#concept.agents.definition) | |
| [Host](../../vocabulary.md#concept.concorde.host) | |
| [Capability declaration](../admission/module.md#concept.admission.capability-declaration) | |
| [Causal feedback](../admission/module.md#concept.admission.causal-feedback) | |

## Usage

Users are the providers that run Agents, the Pi session and maintainers adding a provider or Graph.
[In depth](design.md) walks through a call and a Workflow step by step.

<a id="concept.execution.agent-call"></a><a id="concept.execution.proposal"></a><a id="concept.execution.result-gate"></a><a id="concept.execution.host-step"></a>

**One Agent call** (`concorde-context-solve`, `concorde-tasks`, `concorde-implement`):

1. The Pi session runs the launcher's native `prepare`; the driver re-enters Request admission and
   the provider's route asks the Host's native service to run its Agent.
2. The driver asks the Agent hook named by the definition for a stage plan (which may stop with a
   response, launching nothing). Task context freezes the snapshot and assembles the capsule; the
   driver writes the Agent definition file and a descriptor binding every input digest and returns
   the exact `call`.
3. The user session passes the call unchanged to `subagent`; the native call extension refuses any
   other call and runs the **Host step** `check` and launch preflight.
4. The Agent submits once through `structured_output`; the **result gate** validates it with the
   hook and stores the **proposal**; the gate command `stage` prints a staged, unaccepted document.
5. On return, `accept` reads pi-subagents' own records, requires success, a passed gate bound to the
   proposal and unchanged inputs, reserves the terminal record, has the hook accept, and archives
   the evidence in the primary worktree.

Host steps are finite and never wait for a model. `report_issue` and `run_checks` results never
count as the call's result. `describe-policy` returns the intended policy without launching.

<a id="concept.execution.workflow"></a>

**Workflows** (`concorde-plan`, both reviews, `concorde-issues` `solve`): the capability declaration
names a workflow hook, which issues call slots and a workflow plan; the registrar registers the
script and the user session launches it. Host steps preflight each slot, and the final step has the
driver reconcile pi-subagents' status with the issued slots before admitting any. `concorde` action
`result` reports acceptance. Providers explain their Workflow in a step table; the messages are the
[Host-step protocol](interfaces.md#contract.execution.host-step).

<a id="concept.execution.agent-hook"></a><a id="concept.execution.workflow-hook"></a>

**Writing a provider.** An **Agent hook** gives the stage plan, extra rechecks, proposal validation
and acceptance; a **workflow hook** gives the plan, each step's answer and the failure record. See
[Hooks](agent-calls.md#hooks).

**Stopping outcomes.** A missing, duplicate or refused proposal is an invalid completion (schema
rejections are correctable in the run). A passing gate never rescues a failed run; changed inputs
make a call stale; cancellation revokes acceptance but keeps a programmer's edits; `accept` records
at most once; nothing is retried; causes stay in the
[causal feedback](../admission/module.md#concept.admission.causal-feedback) record.

<a id="concept.execution.model-selection"></a>

**Model selection.** Project configuration defaults for `model`, `thinking` and `timeout_seconds`,
overridden per Agent under `workers`; invalid entries are rejected
([details](agent-calls.md#model-selection)).

<a id="concept.execution.graph"></a><a id="concept.execution.graph-spec"></a><a id="concept.execution.terminal-agent-operation"></a>

**Control flow.** Simple flows use a Workflow. A **Graph** (LangGraph Graph API only) is used when
state and branching must be inspectable, and has exactly one **Graph Spec** that the Graph Spec
check compares with it ([Control flow](control-flow.md)). The **Terminal Agent Operation** receives
its trusted Agent service in Runtime context, never State; see its
[Graph Spec](control-flow.md#terminal-agent-operation).

## Design

A model's output is a proposal; the Host decides what counts. Launch shape (preflight) and
acceptance (result gate, native records, input rechecks) are enforced. Not enforced: reads outside
the capsule, the programmer's writes and shell outside its `ImplementationScope`, network and
credentials, and an Agent with `bash` running the launcher. Agents never delegate by
[req.agents.terminal](../../agents/definitions.md#req.agents.terminal). [In depth](design.md) gives
the reasons.

<a id="realization.execution.native-driver"></a>

The **native driver** holds only the shared path and reaches providers through hook entry points;
staging never accepts and the exclusive terminal record makes acceptance happen once.

<a id="realization.execution.native-plumbing"></a>

The **native Pi plumbing** (Host-step transport, proposal capture, preflight, native call extension,
workflow registrar) reads tools, scripts and commands from prepared files, with no provider
knowledge.

<a id="realization.execution.invocation-host"></a>

The **invocation host** carries a request's roots, mode, identities, observer and native service
outside any data a model writes, and resolves model selection.

<a id="realization.execution.operation-graph"></a><a id="realization.execution.graph-spec-check"></a>

The **operation graph** builds the Terminal Agent Operation and its Runtime context; the
**Graph Spec check** compares each catalog Graph with its Graph Spec and refuses the Functional API.

<a id="realization.execution.tests"></a>

The **execution tests** use scripted pi-subagents runs; they show the plumbing holds, not model
judgement.

## Relationships

```mermaid
flowchart LR
    accTitle: How a model result is produced and accepted
    accDescr: The native driver prepares and accepts Agent calls through hooks; a Workflow orders calls and Host steps; the result gate stages and accepts each proposal.
    driver[Native driver] -->|prepares and accepts| call[Agent call]
    driver -->|calls| hook[Agent hook]
    driver -->|calls| whook[Workflow hook]
    plumbing[Native Pi plumbing] -->|registers| workflow[Workflow]
    workflow -->|orders| call
    workflow -->|runs| step[Host step]
    call -->|runs one| agent[Agents / Agent]
    hook -->|is named by| definition[Agents / Agent definition]
    call -->|submits| proposal[Proposal]
    step -->|drives| gate[Result gate]
    gate -->|stages and accepts| proposal
```

Providers under Operations implement the hooks and participate in the
[Host-step protocol](interfaces.md#contract.execution.host-step); the Pi session loads the native
call extension.

<a id="uses-agents"></a>

**Agents** defines each [Agent](../../agents/module.md#concept.agents.agent). The driver relies on
its [definition](../../agents/module.md#concept.agents.definition) for tools, instructions, time
limit, result type and hook, and on [req.agents.terminal](../../agents/definitions.md#req.agents.terminal).
An unknown Agent or unresolved hook stops preparation.

<a id="uses-context"></a>

**Task context** freezes the [snapshot](../context/module.md#concept.context.snapshot) for the
[phase](../context/module.md#concept.context.phase) and [stage inputs](../context/module.md#concept.context.stage-input),
assembles the [capsule](../context/module.md#concept.context.capsule) and yields the
[Agent binding](../context/module.md#concept.context.agent-binding). The driver rechecks the
snapshot before staging and acceptance and rejects a changed one as stale.

<a id="uses-admission"></a>

**Request admission** is re-entered by every Host step with the stored
[invocation](../admission/contracts.md#contract.admission.invocation), answering with
[result envelopes](../admission/contracts.md#contract.admission.result) and
[feedback](../admission/contracts.md#contract.admission.feedback). A
[relayed](../admission/module.md#concept.admission.relay) request prepares in the candidate. The
[capability declaration](../admission/contracts.md#contract.admission.capability-declaration) names
any workflow hook; one without a native entry refuses preparation.

<a id="uses-worktrees"></a>

**Candidate worktrees** supplies the [change status](../worktrees/module.md#concept.worktrees.change-status),
whose digest each descriptor binds, and the primary [run record](../worktrees/module.md#concept.worktrees.run-record)
directory for archives. A failed archive write fails the acceptance.

<a id="uses-checks"></a>

**Check execution** runs [configured checks](../checks/module.md#concept.checks.configured-check)
for `run_checks` in its [read-only check boundary](../checks/module.md#concept.checks.read-only-boundary)
and returns [check results](../checks/module.md#concept.checks.check-result). Only Agents listing
the tool get it; an unavailable boundary fails the call.

<a id="uses-spec"></a>

**Spec tooling** supplies [typed values](../../spec/module.md#concept.spec.typed-value), and the
[registry](../../spec/module.md#concept.spec.registry) and [documents](../../spec/module.md#concept.spec.document)
the Graph Spec check reads. A Spec error stops the step.

<a id="uses-issues"></a>

**Issues** takes each [report](../../issues/interface.md#contract.issues.report) bound to the call
and returns a [receipt](../../issues/interface.md#contract.issues.receipt). An accepted
[Issue report](../../issues/module.md#concept.issues.report) survives a failed call; a rejected one
fails the tool call; a proposal may cite only this call's receipts.

<a id="uses-observation"></a>

**Observation** records a [diagnostic span](../observation/module.md#concept.observation.diagnostic-span)
per Host step through the invocation host's observer, never changing the outcome.
