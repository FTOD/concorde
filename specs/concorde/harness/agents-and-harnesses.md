# Capabilities and Harnesses

This document defines model execution configuration for the single Capability model. Capability
is the executable entity: deterministic code, a model invocation and a compiled LangGraph subgraph
all expose State-based node contracts. A worker profile is optional execution configuration on a
Capability, not a separately registered Agent or an additional composition relation. The historical
document identity and requirement/scenario anchors remain stable for existing links.

### The execution model

**Harness = context + control flow + models + permissions and environment.**
**Capability = input State + output State updates + execution implementation and constraints.**
**Invocation = Capability + Module/version + admitted artifacts + actual grant + runtime settings.**

| Term | Meaning |
| --- | --- |
| Capability | The one executable identity, usable as a LangGraph node or composed subgraph |
| State contract | Declared input channels and output updates; wire shapes are checked at runtime |
| Model execution profile | Instructions, task/effect contract, workspace, tools, children and timeout on a Capability |
| Worker | One fresh Pi RPC process executing a model-backed Capability invocation |
| Child helper | A bounded pi-subagents session internal to a worker; not an independently callable Framework node |
| Harness | Context resolution, worker runtime, model selection, permissions and environment |
| Skill | Instructions for an external developer runtime to invoke one public Capability |
| Tool | An interface admitted by the worker's actual tool grant, not by graph composition alone |

A deterministic Capability makes no model call on any supported path, including its transitive
composition. It may still read Git, files or subprocess results; determinism here does not mean
purity. Model-backed nodes use the same Capability inventory and USES relation as other nodes.
Sharing a graph State or knowing a Capability name grants neither context nor execution authority.

### A1. Capability instructions and execution profile

Each model-backed Capability MUST own instructions in `capabilities/<name>/spec.md` and a Python
`PROFILE` declaration in that same package. Its instructions define responsibilities, goals,
accepted input and feedback, expected results, completion conditions, and behavior on missing
information, failure or required human decisions. These remain six sections after its
`# concorde-<name>` title. Common worker rules precede them in the build; Protocol rules follow
in the actual system prompt. Instructions are not project Spec context or permission grants.

`PROFILE` MUST have the same identity as its Capability and bind its task contract, workspace,
tools, children and timeout. There is no independent Agent inventory or `AGENTS` call relation.
A `WorkerBinding` records exact instruction, profile, child-definition and build digests for one
model Capability. Stale or inconsistent bindings MUST prevent execution. The serialized `agent`
field, `concorde-agent-stage-*` types and `generated/agents/` paths are retained compatibility
spellings, not a second executable model.

### A2. Profile and Harness

A model profile selects a `capsule` workspace for Spec-only work or a `project` workspace for
implementation access. It declares Pi tools and maximum effects. The host adds `submit_result`,
and adds `subagent` only when the profile declares helpers. `edit` and `write` require a write
effect; implementation reads require the project workspace. The host compiles each concrete grant
as a subset of both those effects and its invocation authority.

Project configuration selects model, thinking and timeout, with per-worker/helper overrides.
These settings are not authority. Pi starts with ambient sessions, context files, Skills, prompt
templates, themes and discovered extensions disabled. Only the host-issued configuration and
explicitly admitted tools are loaded. The shared [execution runtime](execution.md) independently
validates the model profile, input, instruction bytes and permissions before launching a process.

### A3. State and composition

Every Capability MUST expose a State contract and `run(state, runtime)`. LangGraph nodes read
only their admitted channels and return State updates. `CapabilityNode` supplies the common
compiled-node adapter; a compiled graph may be embedded as another node. Different parent/child
schemas require explicit channel mapping. Concurrent writers require explicit reducers on the
owning graph; no automatic merge or broad parent-State grant is inferred.

The host supplies launchers, configuration and authority through trusted `Runtime.context`, never
through caller-writable State. Model nodes validate their context and output against the task
contract as well as its wire schema. Existing public host adapters preserve the complete versioned
result envelope in a `result` output channel, including errors and blocked outcomes.

Capabilities MUST declare direct composition through `USES`, including model nodes. The host
rejects undeclared calls. A worker's granted tools are separate from the host's composition graph:
being present in `USES` does not install a Capability as a Pi tool. Dependencies must not widen
context, effects or write authority. Graph nodes, edges and stopping rules are the executable
control-flow definition; metadata does not repeat their order or branching.

### A4. Invocation constraints and evidence

Each invocation MUST bind its task, frozen context, Capability profile and instruction digests,
effective permissions, model settings and fresh identity. Reuse of a Capability never implies
reuse of its predecessor's conversation. Only explicitly admitted artifacts cross stages.

Completion MUST distinguish successful output, missing information, required human decisions,
cancellation, execution failure and exhausted limits. Failures MUST NOT retry with broader
permissions. A changed goal, context or authority requires new host admission. LangGraph State
schemas do not replace any of these checks.

### A5. One-level helper delegation

A model Capability MAY delegate inside its worker only to the helpers its profile declares under
`capabilities/<name>/children/`. They use replaced, context-free prompts and read/check tools,
with no model selection embedded in their definitions. They execute in foreground fresh sessions
under the same grant and tool gate, cannot delegate again and cannot submit the worker's final
result. Only the verified worker result leaves the process. Helper answers are evidence, not a
second Framework node result. [Execution](execution.md) defines the capability ceiling and gate.

### Common worker rules and inventory

The build combines `prompts/workers/common.md` with the Capability's own instructions and binds
its child definitions as sources. Distribution still publishes `generated/agents/<name>.md` to
preserve the installed instruction layout. The host appends the granted Protocol rule bundle.

The single inventory is defined by [Capability registry](../development/capabilities.md).
Its metadata includes each model Capability's optional workspace, tools and children alongside
its State and USES declarations. There is no separate `concorde.agents` metadata collection.

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
| issue-solver | stage; issue-solve | required concorde-issue-selection | Bounded next action or disposition; Spec-only, no project writes |

The host selects the worker before freezing its context and compiling its permissions, and the
executor checks that selection again before any process starts. A context of the wrong type or
phase, a wrong discovery action, unadmitted or missing required artifacts, implementation contents
admitted to a worker without implementation reads, and a policy wider than the contract are
rejected. After the process, a result whose type, outcome or populated fields the contract does not
permit is rejected: disallowed authored fields as `permission_denied`, other contract violations as
`invalid_completion`. Reviews additionally bind the matching `review_mode`. Spec-only workers never
receive source contents or project writes; the programmer receives only the bound Module's
authorized code; read-only code review grants enumerate the frozen implementation
files, so a listed directory cannot widen them to hidden, excluded or later-created files.

The programmer executes useful tests its grant supports. A listed test does not grant transitive
imports or repository fixtures; an unavailable input is recorded as deferred host verification,
never as a passing result, and actual defects and unfulfilled obligations still prevent completion.
The Issue solver uses its own issue-solve phase and a selected problem, not an implementation grant.
Ordinary development stages may receive the host-bound concorde-issue-intent. Tasks/implementation
repair receives selected concorde-issue-context observations alongside the admitted review result.

Every phase, target, repair and review has a fresh invocation identity and frozen context. Sharing a
role never shares a conversation, private reasoning, stage inputs or write grant between workers.
Only explicitly admitted structured artifacts cross stages.

## Design

### Responsibilities and implementation boundaries

The common Development host dispatches the declared provider and Flow contracts and schedules
invocations. Planning owns plan/task semantics, Implementation owns task fulfillment, and each
composing Flow owns its ordering and stopping policy. This Module's worker executor verifies and
launches workers through the Pi worker runtime and admits their results; its permissions service
compiles effective boundaries; its context service supplies the admitted context kinds; its model-profile
service resolves definitions and bindings. The Distribution build renders and distributes instruction
views with source identity.
