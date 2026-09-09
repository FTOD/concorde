```concorde-document
{
  "id": "document.specs.modules.concorde.agent-execution.agents-and-harnesses",
  "targets": [
    "module.agent-execution"
  ],
  "main_visible": true
}
```

# Agents and Harnesses

This document defines the required Agent model for Concorde Framework. The requirements below are
the standard for implementation review; an existing role prompt or launcher is not evidence that
the complete model is implemented. Agent, Harness and Capability are Framework entities, not new
Concorde Spec Protocol target kinds. Their owning Modules, Modules and Modules retain the existing
registered Spec structure.

## Architecture

**Agent = `spec.md` + Harness + Constraints/Permissions.**

| Entity | Meaning | Relationships |
| --- | --- | --- |
| Agent Spec | The Agent's authored `spec.md`, defining its responsibilities, goals and behavioral contract | Is bound by its Python Agent definition and constrains every invocation |
| Agent definition | A Python module defining one named Agent by binding its Spec, Harness and constraints | Can be reused for different invocations without sharing their private state |
| Agent invocation | One execution of an Agent definition for a specific task | Receives admitted context, effective permissions and a fresh execution identity |
| Harness | The organized execution environment supporting an Agent | Integrates Capability references, Tools, Skills, model access, context assembly, control loops, state and system environment |
| Capability | Functionality an Agent can use, or that can be composed to provide further functionality | Has an explicit contract and is made available through a Harness binding |
| Tool | A callable interface that performs an operation | Realizes or accesses a Capability under runtime enforcement |
| Skill | Instructions and methods for carrying out a class of work | Can be admitted into a Harness; may describe how to use Capabilities and Tools |
| Constraints/Permissions | Limits on information, operations, effects and execution | Restrict the Agent's effective Harness and are enforced outside model discretion |

An Agent is a uniform abstraction, including Agents implemented with Python control logic and
Agents using Codex or Claude. A Codex/Claude Agent adapter binds behavior, loop and permissions;
the underlying native client is an execution resource. Neither provider integration is inherently
a leaf. A leaf is an invocation that makes no child calls in a particular execution.

A model is a resource used through the Harness. Responsibilities, task information and admitted
Capability or Skill descriptions may all be presented as model context, while retaining distinct
identities and contracts. Loading an instruction, mentioning a Tool or installing a Skill does not
itself grant authority to execute an operation.

## A1. Agent Spec and Python definition

Every named Agent MUST have an identifiable authored `spec.md`. It MUST describe its responsibilities,
goals, accepted input and feedback, expected results, completion conditions, and behavior on missing
information, failure or a required human decision. A rendered prompt is a derived instruction view;
it MUST remain traceable to the Agent Spec and MUST NOT replace that Spec as the behavioral authority.

One Python module MUST define each named Agent and explicitly bind its Agent Spec, Harness reference
and Constraints/Permissions. The module may reuse shared Framework primitives and provide a script
entry; it need not implement a separate model client, permission engine or scheduler. A Python module
that merely launches a role named in a table does not constitute this complete Agent definition.

The binding MUST identify the sources and versions needed to reproduce execution. Missing Spec,
unknown Harness or unresolved Capability references MUST prevent the invocation from starting.
Changing a binding requires fresh admission and invalidates evidence that depended on its old identity.

An Agent's `spec.md` is its responsibility contract. The project task's Target Spec and Shared Specs
are separate admitted inputs about the work to perform. Neither set implicitly grants access to the
other's neighboring files. This Agent-specific filename convention adds no filename requirement to
ordinary Module or Module Specs.

## A2. Harness composition

A Harness MUST have an explicit identity and inspectable configuration. Its configuration MUST
identify its model integration, available Capability references, Tool interfaces, admitted Skills,
context assembly, control-loop policy, state handling and required system environment. A named
policy or shared implementation may be referenced instead of duplicating its body.

The same Harness definition MAY support several Agents. Each invocation MUST receive an effective
configuration restricted by the Agent definition and host-issued authority. The catalog of installed
resources and the effective resources available to an invocation are distinct. Ambient discovery
MUST NOT silently add Skills, Tools, context, credentials or environment access.

The Harness MUST connect decision, action, observation and feedback through the selected control
loop. It MUST distinguish model reasoning, Tool execution and human decisions in its execution
evidence. A model adapter, virtual environment or bag of Tools alone is not the complete Harness.

## A3. Capability use and composition

A Capability MUST declare its identity, purpose, inputs, results, effects, constraints and relevant
failure or retry behavior. Its meaning is the functionality it provides, not the Python file that
implements it. A deterministic operation, a composed operation or an Agent Graph may provide a
Capability when its complete contract is explicit.

An Agent's Harness MUST reference its available Capabilities explicitly. Descriptions supplied to
the model and bindings accepted by the executor MUST resolve to the same admitted contracts.
An unavailable or unauthorized reference MUST fail before its effects occur.

Composition MUST preserve required input/output contracts and propagate failure and effect limits.
An outer Capability cannot grant an inner operation more authority than the invoking Agent has.
The composition MUST identify required capabilities without exposing unrelated definitions or
private invocation context. Runtime host composition and Agent-available capabilities MUST be
distinguishable; a host's ability to compose an operation does not make it callable by every Agent.

Existing `capabilities/` modules and global/lifecycle/stage classes describe Concorde's current host
adapter. The exact inventory remains documented in the capability registry. Those adapter classes
do not exhaust the meaning of Capability or turn every capability into an Agent.

## A4. Constraints, context and invocation

Constraints/Permissions MUST cover applicable context access, Tool and Capability calls, file and
process effects, network and credential use, and execution limits. The trusted runtime MUST enforce
the effective boundary; instructions alone are insufficient. Effective permissions MUST be a subset
of both the Agent's declared constraints and the host authority for this invocation.

Every invocation MUST bind its task, admitted context, Agent Spec, Harness configuration, capability
references, effective policy and execution identity. State and evidence MUST remain attributable to
that invocation. A repeated call is a fresh invocation, and resumption admits only the state and
artifacts authorized by the selected loop or graph. Raw predecessor conversations are not an
implicit context channel.

Completion MUST distinguish a successful result, a missing-information gap, a required human
decision, cancellation, an execution failure and exhaustion of the configured execution limits.
Failure MUST NOT cause an automatic retry with broader permissions. Feedback that requests a new
goal, different context or additional authority MUST pass admission again before dependent work.

## A5. Recursive delegation

Any Agent MAY request another admitted Agent, including itself, through a host-controlled
sub-agent/delegation interface. Python control logic and model decisions use the same admission
boundary. A child may run its own loop and request further children. No provider or implementation
language implies leaf status or gives an implicit delegation grant.

The host MUST resolve the child definition, validate its typed input, check an explicit parent-to-child
edge and the invocation's delegation grant, and independently bind its complete target context and
permissions before execution. Self-calls require an explicit edge too. The installed Agent catalog,
parent context, caller-supplied paths and native sub-agent names do not grant child authority.
Cross-target delegation uses host-selected contexts within the enclosing task's explicit grant;
it never copies another target's private snapshot through the parent.

The child returns only its declared typed result, invocation identity and outcome. Context bodies,
raw transcripts, exception messages and native logs are not child results. A continuation admits
only the original task/context and declared typed feedback; each native model decision starts a
fresh process. The host records parent/child identities and the source of each control decision.

The invocation tree MUST share finite call and decision budgets, a depth limit and cancellation.
A child cannot reset them. Host limits override local continuation requests. Cancellation and limit
exhaustion stop dependent ancestors; execution/admission failures are typed feedback and a parent
may recover only under its declared bounded loop. A missing-information or human-decision outcome
remains distinct from execution failure. There is no implicit retry or permission widening.

A native integration without a verified callback transport MAY yield a typed delegation request to
the host and continue in a fresh decision invocation after receiving typed child feedback. This is
a supported model-driven loop, not a claim that arbitrary provider-native sub-agent tools are safe.
Unmediated native delegation MUST remain disabled. The current read-only adapter supports this
yield/delegate/continue path; it grants only a private context capsule, not project file effects.

## Responsibilities and implementation boundaries

The orchestration host resolves Agent definitions and schedules invocations. Agent execution
operates the bound Harness through model integrations and validates completion. The permissions
module compiles and checks effective boundaries. Context resolution supplies admitted project
knowledge. Package assets render and distribute instruction views with source identity.

Existing wire fields such as `role`, `agent`, `protocol` and `LaunchSpecification` remain their
documented compatibility contracts. The explicit mapping is `agent_binding_json`: a `LaunchSpecification`
carries the launched Agent's complete resolved `AgentBinding` in this field, and the executor
verifies it against the actual prompt, Harness, admitted context/result types and policy before
executing anything. A launch with no binding, or one the executor cannot verify, is refused rather
than executed.
