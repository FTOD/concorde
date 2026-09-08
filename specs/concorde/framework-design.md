```concorde-document
{
  "id": "document.concorde.framework-design",
  "targets": [
    "domain.concorde"
  ],
  "main_visible": true
}
```

# Concorde Framework design

Concorde Framework includes the Concorde Spec Protocol and the software capabilities that apply it. The
Domain/Service/Module model and `ontology.md` organization are defined in the [Concorde Spec Protocol](spec-protocol.md).
This page explains software mechanisms and points to their owning orchestration and service contracts.

## Rules, installation and reproducible execution

A deterministic build renders Skill definitions and prompts into integration-specific Skill files,
role instructions, rule assets, schemas, Studio graph metadata and documentation inventories. The
installer places the selected Skill files in the project's Codex or Claude integration and deploys
the Framework package, templates and managed runtime. Build produces assets; installation places
and verifies them. A project records its accepted rule version and digest; the context Service injects that
version with the appropriate kind definition. These are implementation mechanisms for consistent
execution. Their contracts belong to the [context Service](services/context-boundary.md) and
[Installation](installation/ontology.md), rather than to the basic meaning of Spec organization.

Concorde Spec Protocol rules and Framework execution rules retain separate authored sections. The runtime
currently distributes them in one rule bundle for complete invocation context. P5–P10 describe
Framework execution, topology changes, reviews, worktrees and handoffs; they do not turn these runtime
records into Concorde Spec Protocol file categories.

## Agent definitions and Harnesses

Each Agent is defined by its authored `spec.md`, a Harness reference and Constraints/Permissions.
One Python module binds those parts. The responsibility Spec defines expected behavior; the Harness
integrates capabilities, tools, Skills, model access, context assembly, control loops, state and
system environment. The host resolves those bindings for a specific invocation and enforces the
effective permissions before allowing effects. A rendered prompt is an instruction view of the
Agent Spec, produced through `resolve_agent`'s reproducible `AgentBinding`; the wire `role` string
remains a compatibility identifier derived from that Agent, not the complete Agent definition.

The [Agent and Harness contract](workflow/agents-and-harnesses.md) is authoritative for this required
model. Agent execution and the permissions module implement its invocation boundary; context
resolution supplies admitted project knowledge. Package assets preserve source identity when rendering
and distributing instructions. Actual code conformance must be assessed against these responsibilities.

## Capabilities, Tools and Skills

A Capability describes usable or composable functionality through its input, result, effect and
usage contract. A Tool is an operation interface. A Skill supplies instructions and methods.
The Harness binds the Capabilities, Tools and Skills available to an invocation; resource installation
and admission are distinct. Referencing a capability in model context must agree with its executable
binding, and composition cannot expand the invoking Agent's authority.

Current `capabilities/` Python modules and their global/lifecycle/stage classification form the host
adapter described by the [orchestration inventory](workflow/ontology.md#graphs-and-supporting-capabilities). Current public
`SKILL.md` entries expose global and lifecycle capabilities through the project integration. These
existing mappings remain explicit compatibility contracts; they do not define the whole Capability
concept. Per-Agent Harness bindings are established separately: each Agent under `agents/` resolves
through `resolve_agent` into an `AgentBinding`, and the executor's preflight verifies that binding
before every launch. Developer views retain their separate publication and viewer interfaces.

## Graphs, Loops and feedback

Agent Graphs declare participating Agent definitions, capability calls, state and control transitions.
An Agent's Harness provides its local loop; a Graph can additionally coordinate feedback loops across
Agents. Each transition distinguishes deterministic conditions, AI assessments and human decisions.
A loop defines when to continue, revise, wait, stop or report exhausted limits.

The [Graph and Loop contract](workflow/agent-graphs-and-loops.md) defines these requirements. The
[query graph](workflow/query-and-routing.md) coordinates routing, readers and synthesis; the
[topology graph](workflow/topology.md) coordinates design, human acceptance and Spec authors; the
[development graph](workflow/development.md) coordinates authoring, planning, implementation and
review. [Review and gaps](workflow/review-and-gaps.md) supplies revision-bound feedback.
[Delivery](workflow/delivery.md) retains a separate deterministic acceptance boundary.

A changed Agent Spec, Harness binding, capability contract, admitted project input or effective
policy invalidates dependent evidence. Resumption re-admits current state and starts fresh
invocations. Raw logs and prior conversations are not automatically transferred as context.

## Developer view and feedback

The [Developer view and feedback Domain](developer-view/ontology.md) combines the docsite, diagrams,
Understand Anything code views and feedback into Agent Graphs and feedback loops.


Publication reads registered Markdown and diagram JSON deterministically. Domain navigation lands
on its registered `ontology.md`, and its System overview is embedded there. Automatic checks verify
main-document declarations and diagram/source consistency; human review checks that the Ontology
and architecture are meaningful. Generated pages and diagrams are human views, never Spec authority.

The [viewer service](services/viewer-boundary.md) opens a supplied raw Understand Anything graph
using the installed official runtime. It does not generate the graph or turn code observations into
Spec authority. Developers can use these views together, clarify a question or correction in the
agent conversation, and direct the resulting request into an admitted Graph or capability.
