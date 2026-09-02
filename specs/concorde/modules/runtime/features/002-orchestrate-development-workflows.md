---
id: feature.runtime.orchestrate-development-workflows
kind: feature
module: module.concorde.runtime
related_features:
  - feature.commands.project-workflow
interfaces:
  provided:
    - contract.runtime.workflow-graph
  required:
    - contract.commands.workflow-guidance
evidence_status: verified
---

# Feature Design: Orchestrate Development Workflows

**Input**: Use LangGraph to organize Concorde prompts as composable workflow stages and provide a
tested standard development loop with specify, plan, tasks, and deliver stages.

## Outcome and Scope

**Outcome**: A workflow author can compile and invoke a LangGraph development loop whose stages load
the canonical Concorde command prompts and execute in the order specify → plan → tasks → deliver.

**In scope**:

- A reusable prompt-stage representation whose ordered prompt bundle is backed by canonical
  `commands/concorde.*.md` sources.
- A LangGraph `StateGraph` example for the standard four-stage development loop.
- An injectable stage runner so tests and consumers do not require an LLM or network service.
- Ordered stage results that expose which canonical prompt and prior outputs each stage received.

**Out of scope**:

- Choosing a model, agent platform, checkpointer, deployment service, or LangSmith integration.
- Automatically approving destructive actions or bypassing each command prompt's existing gates.
- Defining every possible Concorde workflow graph in this first example.

## Usage

A workflow author supplies a callable stage runner and builds the standard graph from a Concorde
package root. Invoking the compiled graph with one development request calls the runner four times in
order. Each call receives the stage's ordered canonical prompt bundle plus the results already
produced by preceding stages. The tasks stage combines task generation with implementation; the
deliver stage combines validation with cleanup-only delivery.

### Edge and failure cases

- A missing or unsafe command root fails before the graph is returned.
- A missing LangGraph installation reports the optional workflow dependency clearly.
- A stage-runner exception propagates and prevents every downstream stage from running.
- Empty user input remains explicit state and is handled by the stage prompt rather than silently
  replaced by example prose.

## User Scenarios & Testing

### User Story 1 — Run the Standard Development Loop (Priority: P1)

A maintainer composes the standard Concorde prompts into an executable LangGraph without copying
their contents into Python.

**Why this priority**: It proves the central idea that commands are reusable stage prompts and that
LangGraph owns their execution topology.

**Independent Test**: Invoke the compiled graph with a recording runner and assert the exact stage
order, ordered command bundles, prompt source bytes, accumulated prior results, and terminal state.

**Acceptance Scenarios**:

1. **Given** a valid Concorde package root, **When** the standard graph is invoked, **Then** specify,
   plan, tasks, and deliver each run exactly once in that order.
2. **Given** one deterministic result per stage, **When** a later stage runs, **Then** it receives all
   earlier results in order and the final state contains all four results.

### User Story 2 — Stop Safely on a Failed Stage (Priority: P2)

A workflow author can trust graph failure semantics without an LLM or external service.

**Why this priority**: A development workflow must not continue into planning, task generation, or
delivery after an earlier stage fails.

**Independent Test**: Configure the recording runner to raise at plan and assert that tasks and
deliver are never called.

**Acceptance Scenario**:

1. **Given** a runner that fails during plan, **When** the graph is invoked, **Then** the exception is
   observable and only specify and plan appear in the call trace.

## Interfaces

### `contract.runtime.workflow-graph` — Prompt-stage workflow graph

- **Consumer**: Concorde workflow authors, examples, and tests.
- **Direction**: Graph configuration and user request into an executable workflow and ordered result state.
- **Entry points**: `entity.runtime.workflow-orchestrator` and `build_standard_dev_loop`.
- **Inputs**: A safe Concorde package root, an injectable stage runner, and one explicit user request.
- **Outputs**: A compiled LangGraph plus terminal state containing ordered stage result records.
- **Obligations**: Load prompt text from canonical command files; preserve stage, bundle, and prompt
  order; pass prior results without mutation; leave command gates and authorization semantics intact.
- **Failures**: Invalid package roots, missing command prompts, unavailable LangGraph dependency, or
  runner exceptions fail visibly and do not fabricate later-stage results.
- **Compatibility**: The example targets `langgraph>=1.2,<2` and its
  `StateGraph`/`START`/`END` Graph API; base Concorde imports and offline installation do not require
  the optional package.
- **Example**: Build the standard graph with a runner, then invoke it with
  `{"request": "Add audit logging", "stage_results": []}`.
- **Implementing entities**: `entity.runtime.workflow-orchestrator`, `entity.runtime.agent-projector`,
  `entity.runtime.langgraph`, `entity.runtime.tests`.

### `contract.commands.workflow-guidance` — Canonical stage prompts

- **Provider**: `module.concorde.commands`.
- **Consumer**: The Runtime workflow graph and its injected stage runner.
- **Direction**: Canonical command sources into immutable prompt-stage definitions.
- **Entry points**: `commands/concorde.specify.md`, `commands/concorde.plan.md`,
  `commands/concorde.tasks.md`, `commands/concorde.implement.md`,
  `commands/concorde.validate.md`, and `commands/concorde.deliver.md`.
- **Inputs**: Package-relative command identity and source path.
- **Outputs**: Exact command prompt text and stable stage metadata.
- **Obligations**: Remain the sole prompt authority; graph code references command identities and
  never embeds replacement prompt copies.
- **Failures**: A missing, unreadable, unsafe, or mismatched command source prevents graph construction.
- **Compatibility**: Canonical `concorde.*` IDs remain stable across source and installed layouts.
- **Example**: The tasks node loads `concorde.tasks` followed by `concorde.implement`; the deliver
  node loads `concorde.validate` followed by `concorde.deliver`.
- **Implementing entities**: `entity.runtime.agent-projector`, `module.concorde.commands`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `entity.runtime.agent-projector` | Resolves canonical command identities and prompt sources. | Supplies immutable prompt-stage definitions to the graph. |
| `entity.runtime.workflow-orchestrator` | Owns stage bundles, typed state, and graph topology. | Compiles and invokes the four nodes through an injected executor. |
| `entity.runtime.langgraph` | Supplies the optional public Graph API. | Schedules ordered Runtime nodes without owning prompt semantics. |
| `entity.runtime.tests` | Provides executable graph evidence. | Invokes the compiled graph with recording and failing runners. |
| `module.concorde.commands` | Owns the stage prompt text. | Remains authoritative while Runtime owns graph topology. |

## Related Features

- `feature.commands.project-workflow` provides the canonical command prompts that this feature
  composes; it does not own or execute the LangGraph topology.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST represent each graph stage by an ordered bundle of canonical command
  IDs, source paths, and prompt text loaded from the selected Concorde package root.
- **FR-002**: The standard development loop MUST compile with LangGraph and connect `START` to
  specify, then plan, tasks, deliver, and `END` in exactly that order.
- **FR-003**: The standard prompt bundles MUST be specify = `concorde.specify`, plan =
  `concorde.plan`, tasks = `concorde.tasks` then `concorde.implement`, and deliver =
  `concorde.validate` then `concorde.deliver`.
- **FR-004**: Every node MUST invoke the injected runner exactly once with the user request, its stage
  definition, ordered prompts, and an immutable view of prior ordered results.
- **FR-005**: Each successful node MUST append exactly one stage result without replacing prior results.
- **FR-006**: Graph construction MUST reject an unsafe package root or any missing canonical stage prompt.
- **FR-007**: A runner failure MUST remain observable and MUST prevent all downstream nodes from running.
- **FR-008**: The example and tests MUST run without model credentials, network calls, or LangSmith.

### Non-Functional Requirements

- **NFR-001**: LangGraph compatibility MUST be constrained to the supported 1.x Graph API and tested
  against the repository's locked development dependency.

### Assumptions

- The four-stage example intentionally follows the user-specified specify → plan → tasks → deliver
  path; `implement` is part of the tasks stage because `deliver` itself is cleanup-only.
- Persistence, interrupts, retries, and conditional routing are deferred until a workflow requires them.

## Success Criteria

- **SC-001**: An automated test observes exactly four calls in the order specify, plan, tasks, deliver.
- **SC-002**: Flattening observed bundles yields specify, plan, tasks, implement, validate, deliver;
  every prompt equals its canonical command file and no prompt body is duplicated in the workflow implementation.
- **SC-003**: A plan-stage failure yields zero tasks or deliver calls in automated evidence.
- **SC-004**: The standard example, complete Python suite, Concorde validation, and package/release
  checks pass with no external credentials.

## Edge Cases

- The package root exists but one stage path is a symlink, directory, or non-UTF-8 file.
- A runner returns an empty output; the stage still records that explicit result and continues.
- The same compiled graph is invoked more than once; each invocation begins with an independent
  ordered result list.
- A caller supplies pre-populated stage results; graph input validation rejects the ambiguous resume
  unless a later persistence contract explicitly defines it.
