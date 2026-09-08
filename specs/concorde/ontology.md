```concorde-document
{
  "id": "document.concorde.system",
  "targets": [
    "domain.concorde"
  ],
  "main_visible": true
}
```

# Concorde Framework

Concorde Framework includes the **Concorde Spec Protocol**, installable Skills, automatic checks,
constrained Agent orchestration, developer views and feedback. The Protocol is the Framework's specification
standard; its software components implement and apply that standard. A developer uses the Framework
to turn specified intent into an inspectable, verified change. Concorde's own Specs follow the same
Protocol as consumer projects.

The [Concorde Spec Protocol](spec-protocol.md) defines how Specs are organized and expressed.
[Framework design](framework-design.md) explains the software's execution and integration mechanisms.
[Main routing](main-routing.md) identifies where a task about this project belongs.

## Architecture overview

The embedded **Concorde Framework** System overview separates Framework rules and software from
project-side inputs and integration entry points. The Concorde Spec Protocol directly governs the
organization of Project Specs, including both consumer projects and Concorde's own project. Build and
installation distribute the rule assets and produce installed Skill entries; those entries invoke
Framework Capabilities from a project's Codex or Claude integration. Agent Graphs coordinate
invocations and feedback loops; each Agent binds its `spec.md`, Harness and Constraints/Permissions.
The context Service resolves registered Specs for execution, and developer views present project
knowledge for inspection and feedback.

The boundary describes the Framework's supplied rules and software, not a process or deployment
location. Installed Skill entries are shown at their project-side use location; their definitions
and generated instruction assets still belong to the Framework. The Framework runtime can also be
installed in a consumer project. Concorde's own source checkout uses its local build directly.

## Ontology

An **Ontology** describes the entities relevant to a domain, their types and meanings, and the
relationships between them. Here it describes Concorde Framework: the Protocol it contains,
the software capabilities it provides, and the people and projects that use them.

### Software and rules

| Entity | Meaning in the Framework | Relationship |
| --- | --- | --- |
| [Concorde Spec Protocol](spec-protocol.md) | The Framework’s specification standard | Belongs to the Framework and governs Spec organization in consumer projects and Concorde’s own project |
| Agent | An execution subject defined by its `spec.md`, Harness and Constraints/Permissions | Has a Python definition and creates separately bound invocations |
| Agent Spec | The Agent’s authored `spec.md` responsibility contract | Defines its goals, behavior, accepted feedback, results and completion conditions |
| Harness | The organized environment supporting Agent execution | Integrates Capability references, Tools, Skills, model access, context, control loops, state and system environment |
| Constraints/Permissions | Limits on information, operations, effects and execution | Restrict the effective Harness and are enforced by the trusted runtime |
| Skill definition | Instructions and methods for a class of work | Can be admitted through a Harness; current public Skill entries expose selected host Capabilities |
| Installed Skill entry | A rendered Skill made available in a project’s Codex or Claude integration | Invokes the corresponding Framework Capability; its installation location does not change its origin |
| Capability | Functionality available to empower an Agent or compose into another capability | Has an explicit input, result, effect and usage contract; is referenced through the Harness |
| Tool | A callable operation interface | Executes or accesses a Capability within effective permissions |
| Agent Graph | The structure coordinating Agents, capabilities and control decisions | Defines state, handoffs, branches and AI or human feedback paths |
| Agent Loop | Feedback-driven decision, action, observation and revision | Runs through a Harness or across a Graph with explicit completion and stop conditions |
| Validation | Checks of Specs and candidate changes | Tests conformance and configured acceptance conditions, supplying evidence for further work or delivery |
| [Developer view and feedback](developer-view/ontology.md) | Ways to understand project knowledge and provide input | Combines docsite, diagrams and Understand Anything views with feedback into Agent Graphs and Loops |

### People, projects and results

| Entity | Meaning in the Framework | Relationship |
| --- | --- | --- |
| Developer | A person using the Framework to understand, specify, implement or review a project | Inspects views, supplies tasks and feedback, and makes the required acceptance decisions |
| Project Specs | A project’s explicitly registered specification documents and diagram sources | Follow the Concorde Spec Protocol in both consumer projects and Concorde itself |
| Consumer project | A project adopting Concorde Framework | Owns its Specs, code and configuration and receives Framework assets through installation |
| Model client | An integration such as Codex or Claude | Executes the agent work prepared by the Framework |
| Candidate change | An inspectable in-progress project revision | Retains work and evidence until it is ready for a separate delivery decision |

## How the Framework works together

A developer submits a task through an installed Skill entry. The orchestration host selects the
Agent Graph and binds each Agent invocation to its responsibility Spec, Harness, task context and
effective permissions. The Harness supplies the available capabilities, Tools, Skills and model
integration. Graph transitions coordinate separate Agents; local control loops and cross-agent
feedback loops determine whether work continues, is revised, waits for a human decision or stops.

AI assessment and review provide revision-bound findings. Human clarification and acceptance can
select a new task or authorize a specific transition. Feedback never silently expands context or
permissions. Checks and review evidence support readiness; delivery remains a separately authorized
capability. Developer views expose the relevant Specs, results and code knowledge for further input.

The [Agents Domain](workflow/ontology.md) defines [Agents and Harnesses](workflow/agents-and-harnesses.md)
and [Agent Graphs, Loops and feedback](workflow/agent-graphs-and-loops.md). [Framework design](framework-design.md)
connects those requirements to supporting component responsibilities and existing compatibility
bindings. Detailed project-Spec organization is defined by the [Concorde Spec Protocol](spec-protocol.md).

## Domain responsibilities

| Domain | Responsibility and relationships |
| --- | --- |
| [Agents](workflow/ontology.md) | Defines Agents and Harnesses, composes capabilities, and controls Graphs and Loops through AI and human feedback |
| [Installation](installation/ontology.md) | Distributes and configures the Framework, Skills, runtime and Concorde Spec Protocol for a consumer project |
| [Developer view and feedback](developer-view/ontology.md) | Helps developers inspect Specs, diagrams and code graphs, then clarify feedback and direct further work |

Context resolution is used by both project initialization and Agent invocation. Built assets
connect installation to execution. Developer views combine Spec publication with code exploration,
and the orchestration host turns clarified feedback into bounded requests. These collaborations are part of the Framework's design; the linked Domain
Specs explain their behavior and participating components in more detail.

## Design principles

Implement the Concorde Spec Protocol consistently across installation, execution and developer-facing views. Give
bounded agent work reproducible context and permissions. Keep automatic structural evidence distinct
from judgments about semantic completeness, and preserve inspectable progress when work is blocked.
Use the main page to establish overall understanding, with useful detail in the related Domain,
Service, Module and topic Specs; include internal collaborations here when they help explain the whole.

## Project authoring conventions

Concorde's own Spec prose, diagram labels and diagram viewer interface use English. This language
choice belongs to the Concorde project; it is not a Concorde Spec Protocol requirement for other projects.
