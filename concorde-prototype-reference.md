# Concorde: Hierarchical Architecture for AI-Developed Software

**Status:** Prototype reference  
**Product name:** Concorde  
**Audience:** Maintainers, software architects, and developers working with AI coding agents  
**Purpose:** Define a workflow and documentation model that gives developers control and confidence over the structure of software increasingly written by AI.

---

## 1. Executive summary

Spec-driven development tools such as Spec Kit are primarily feature-oriented. They are effective at describing what a feature should do, clarifying its requirements, planning its implementation, and turning the plan into executable tasks. This gives an AI coding agent strong local context for implementing a change.

However, a collection of feature specifications and implementation plans does not give a developer a clear model of the software as a whole. Plans contain implementation detail, but they do not necessarily explain the durable structure that emerges across many features: which modules exist, what each module is responsible for, which features each module provides, and which modules and features collaborate in a given scenario.

This gap becomes more important as AI writes a larger share of the code. Developers may no longer need to author or inspect every implementation detail, but they still need to control the organization of the system and understand the consequences of changing it. Confidence shifts from knowing every line to understanding boundaries, responsibilities, dependencies, and behavior at the right level of abstraction.

Concorde adds that architectural view. It organizes a project as aligned, recursive hierarchies of modules and features:

- A module provides one or more related features.
- A module documents the contracts it provides to and requires from everything outside its boundary. Its features depend on those contracts being respected.
- A feature is specified in text through its intended behavior, requirements, and constraints.
- A module-level feature can be refined by lower-level features owned by its submodules.
- Representative user or system scenarios illustrate the feature with concrete examples, including how the module's immediate submodules may collaborate to provide it.
- Any submodule can be opened as another architectural level, where it provides its own features through its own submodules.

This creates a zoomable model. At one level, the developer sees the current module's I/O contracts and features, its immediate submodules, those submodules' I/O contracts, and their organization. The submodules' internal features and children remain hidden. When the developer descends into a submodule, it becomes the current module and the same view repeats at the next level. The same concepts work from the whole project down to the smallest architecturally meaningful component.

Concorde uses two kinds of maintained source artifacts:

- Markdown documents for module intent, feature specifications, scenarios, constraints, and decisions.
- Archify JSON documents for module structure and scenario interactions at each architectural level.

Both behavioral and architectural intent live under one `specs/` hierarchy. Concorde does not treat architecture as a separate documentation domain; it is part of the specification of the system.

Docusaurus turns those sources into a read-only website whose navigation mirrors the architecture hierarchy. Archify renders the JSON diagrams as interactive HTML within those pages. The result serves both audiences: AI agents receive explicit structure and traceable behavioral intent, while developers receive a browsable, visual explanation of the codebase they are directing.

## 2. The problem

### 2.1 Feature specifications provide a local view

Spec Kit's normal workflow starts from a feature. The developer states what should be built; the agent clarifies the behavior, creates a technical plan, derives tasks, implements them, and checks the result against the working artifacts.

That workflow answers questions such as:

- What should this feature do?
- Which requirements and edge cases matter?
- What implementation work is required?
- Has the planned work been completed?

These are essential questions, but they are centered on a particular feature or change.

### 2.2 Implementation plans do not provide durable structural understanding

A technical plan may name files, technologies, interfaces, and implementation steps. It is useful input to the coding agent, but it is usually scoped to the current feature and written as a path toward implementation. It does not automatically become a coherent description of the system after many changes have accumulated.

To understand a mature project from feature artifacts alone, a developer would have to reconstruct the present architecture from a history of specifications and plans. That reconstruction is difficult for people and unreliable for agents.

### 2.3 AI changes what developers need to control

When AI writes most of the implementation, line-by-line authorship becomes a less useful way to maintain confidence. The implementation still matters and must be tested, but the developer's attention moves toward higher-level questions:

- Is the system divided into sensible modules?
- Does each module have a clear responsibility?
- Are related features grouped together?
- Which submodules participate in an important scenario?
- Are dependencies moving in the intended direction?
- Where should a new feature belong?
- How far must a developer zoom in before the relevant design becomes clear?

Without an explicit architecture model, the AI can produce locally correct code while gradually creating a system that is difficult to understand, change, or trust.

### 2.4 Scale requires abstraction

A large project cannot be reasoned about as one flat graph or one exhaustive specification. A useful model must hide detail deliberately.

At the project level, a developer may care only about a handful of major modules and the product features they provide. Inside one of those modules, the developer may need a second view of its submodules and internal features. The process repeats until reaching code-level components.

Concorde therefore treats hierarchy as a reasoning mechanism, not merely a navigation convenience.

## 3. Product thesis

Concorde's central claim is:

> In AI-developed software, a developer can retain control and confidence by maintaining aligned module and feature hierarchies that expose responsibilities, I/O contracts, and collaboration at one meaningful level of abstraction at a time.

Concorde is inspired by the combination of two closely related ideas:

- **Spec-driven development** treats explicit behavioral specifications as the starting point for planning, implementation, and validation.
- **Architecture as Code** represents architectural structure in version-controlled, machine-readable artifacts that can be validated, reviewed, and rendered reproducibly.

Concorde brings them together. Specifications describe the features expected from each module, while architecture artifacts describe the module hierarchy and the submodule collaboration behind each feature. Both evolve alongside the implementation and are presented as one navigable model.

Spec Kit and Concorde answer complementary questions:

| Tool or view | Primary question |
|---|---|
| Spec Kit specification | What behavior should be delivered? |
| Spec Kit plan and tasks | How will this change be implemented? |
| Concorde module view | Where does this behavior belong in the system? |
| Concorde scenario view | Which submodules collaborate to provide it? |
| Concorde hierarchy | What detail should be visible at the current reasoning level? |
| Code and tests | What is actually implemented, and what evidence supports it? |

Concorde does not replace feature-oriented specification. It adds the durable structural context that feature-oriented development needs when implementation is delegated to AI.

## 4. Core model

### 4.1 Module

A **module** is an architecturally meaningful unit with a clear responsibility and boundary. A module may be a deployable system, service, package, application layer, component group, or other unit appropriate to the current level.

Every module records:

- a stable ID and name;
- its purpose and responsibility;
- the features it provides;
- its immediate submodules;
- the contracts it provides to external consumers;
- the contracts it requires from external dependencies;
- the dependency rules at its boundary;
- relevant constraints and decisions;
- links to source code, tests, and active changes where useful.

The root project is treated as the top-level module.

Here, **external** means anything outside the module boundary. Depending on the current level, that may include the parent module, a sibling module, an end user, or a separately operated system.

Together, a module document and the feature specifications it owns form that module's specification package. Concorde should reuse Spec Kit to author and evolve the feature specifications inside this package while adding the parent/child structure that connects packages across the project.

### 4.2 Feature

A **feature** is an observable behavior provided by one module. Related features belong to the same module when they share responsibility, state, policy, or internal implementation in a meaningful way.

A feature records:

- a stable ID and concise outcome;
- functional requirements and acceptance criteria;
- representative scenarios when useful;
- the providing module;
- the higher-level features it refines or supports;
- the boundary contracts on which the feature depends;
- relevant constraints and evidence.

The providing module owns the feature at that architectural level. A feature describes behavior at the same abstraction level as its module. If behavior crosses several areas of the system, it should normally be described at their nearest common parent module and refined by lower-level features in the participating submodules.

The feature hierarchy therefore follows the module hierarchy:

- a feature on the current module expresses behavior visible at the current level;
- a lower-level feature is owned by an immediate submodule and refines or supports a feature from the parent level;
- lower-level feature details are hidden in the parent view and become visible when the user zooms into their owning submodule;
- stable refinement links preserve traceability between the levels even when those details are not displayed together.

Feature refinement is hierarchical by abstraction, but realization may still be many-to-many: one parent feature may require features from several submodules, and one lower-level feature may support several parent features.

### 4.3 Scenario

A **scenario** is a concrete example of a feature in use. It illustrates how the intended behavior can be achieved, but it does not define the feature exhaustively. A feature usually has one representative primary scenario, while alternative, failure, and degraded cases may provide additional examples.

At a non-leaf level, the participants in a scenario are normally the providing module's immediate submodules or external actors. This keeps the view bounded and prevents high-level diagrams from leaking low-level details.

Whenever a scenario crosses a module boundary, the interaction must reference the contract governing that crossing. The scenario is an example of the interaction; the contract defines the obligation that every implementation of the feature must respect.

A scenario records:

- its trigger or initiating actor;
- its expected outcome;
- the ordered collaboration among participants;
- relevant data or control flow;
- important alternatives and failures;
- references to deeper scenarios when more detail exists below the current level.

### 4.4 Submodule

A **submodule** is simply a module viewed inside its parent. It follows the same model: it provides features, with scenarios that illustrate how its own children may collaborate in concrete cases.

There is no separate ontology for systems, modules, and submodules. Their role depends on the current point of view.

### 4.5 Contract

A **contract** is a documented agreement at a module boundary. It is the only architectural promise that code outside the module should rely on; internal implementation details remain hidden behind it.

Contracts are directional:

- A **provided contract** states what the module promises to external consumers.
- A **required contract** states what the module expects from an external dependency in order to work correctly.

The contract also records the direction of information or control flow across the boundary: **input**, **output**, or **bidirectional**. Flow direction and provided/required role are separate. For example, an emitted event is an output flow governed by a provided contract, while an outbound request to a dependency uses a required contract.

A contract should document, as applicable:

- a stable ID and owning module;
- its provided or required role;
- its input, output, or bidirectional flow direction;
- its intended consumers or provider;
- operations, messages, events, or data exchanged;
- preconditions, postconditions, and invariants;
- failure behavior and error semantics;
- compatibility and versioning expectations;
- tests or other evidence that the contract is respected.

#### Contract representation

Every contract must use one of two representation types:

1. **Commonly adopted format.** The contract names the recognized format or protocol, its relevant version, and the source artifact. Examples may include an established API, schema, interface-definition, event, or document format. Concorde does not duplicate the format's complete specification; the agent provides a short explanation of the information passed across the boundary and links to the authoritative definition.
2. **Custom serialized format.** The contract uses a programmer-readable serialization language such as JSON, YAML, or TOML. The agent must document the format completely enough that a programmer can inspect a value and understand what it represents without reading the implementation.

A custom format must include:

- a normative schema or grammar stored with the contract;
- the meaning of the complete message or document;
- every field's name, type, required/optional status, and semantic meaning;
- units, allowed values, nullability, and default behavior where relevant;
- compatibility and versioning rules;
- at least one representative serialized example;
- validation evidence showing that examples and implementations conform to the declared format.

Opaque, undocumented payloads are not valid contracts. A binary or generated encoding is acceptable only when its authoritative schema or interface definition is itself version-controlled and readable by programmers.

When an agent creates or changes a custom contract, it must update the schema, semantic documentation, representative examples, and affected feature references together. For a commonly adopted format, the agent only needs to keep the format reference and concise information summary current.

A module's features are functional only when the relevant provided and required contracts hold. Every feature must identify at least one provided contract through which the module makes the feature available, together with any required contracts on which its operation depends. Architectural review must therefore treat a contract change as a potential feature change.

### 4.6 The recursive relationship

At every architectural level:

```text
module
├── declares → provided/required I/O boundary contracts
│   └── connect to → external modules and actors
├── provides → feature
│   ├── depends on → boundary contracts
│   └── illustrated by → scenario
│       └── involves → immediate submodules and externals through contracts
└── contains → submodule
    ├── declares → its I/O boundary contracts
    └── provides → lower-level feature
        ├── refines or supports → parent-level feature
        └── illustrated by → lower-level scenario
```

The complete model is recursive, but a rendered view reveals only one level at a time. Concorde models only architecturally meaningful levels; it should not create a module document for every class or function.

## 5. Hierarchical architecture views

### 5.1 The visibility rule at one level

Each module page establishes one current architectural level. At that level, the view shows exactly:

- the current module as the context boundary;
- the current module's input and output contracts;
- the features owned by the current module;
- relevant external actors or systems;
- the current module's immediate submodules;
- each immediate submodule's input and output contracts;
- the organization and allowed connections among those submodules and externals;
- the contract governing every connection;
- scenario traces that illustrate the current module's features using only entities visible at this level.

The view does **not** show the submodules' internal features, their own submodules, or any deeper implementation details. Those become visible only after the user zooms into the relevant submodule.

This rule makes each level both a black-box and white-box view:

- The current module is a **black box** from the outside: its I/O contracts and features describe what it offers and requires.
- The current module is opened as a **white box** one level deep: its immediate submodules, their I/O contracts, and their organization show how the current level is structured.
- Each submodule remains a **black box** until selected as the next current module.

A leaf module has no required child-module diagram. Its scenarios remain behavioral specifications linked to implementation and test evidence; a lower-level view is added only if the module is later decomposed.

### 5.2 Feature visibility and refinement

Features follow the same zoom boundary as modules. The default view shows only features owned by the current module. Lower-level features are not expanded alongside them, even though refinement links connect the levels.

When the user zooms into a submodule:

1. The selected submodule becomes the current module.
2. Its I/O contracts remain visible, now as the boundary of the new view.
3. Its own features become visible.
4. Its immediate children, their I/O contracts, and their organization become visible.
5. Features and modules below that next level remain hidden.

This keeps feature abstraction aligned with structural abstraction. A high-level feature says what the parent module provides; lower-level features explain more specific responsibilities only where the user asks for that detail.

### 5.3 Zooming through the system

For example:

```text
Project: Concorde
├── Documentation module
│   ├── Docusaurus generator
│   └── Archify renderer adapter
└── Architecture authoring module
    ├── Module registry
    ├── Feature specification adapter
    └── Architecture validator
```

At the project level, the view shows the Concorde project's I/O contracts and features, the Architecture Authoring and Documentation modules, each child module's I/O contracts, and the connections between them. A scenario for **Publish architecture documentation** uses only those visible elements.

Opening the Documentation module makes it the new current module. Its features—such as **Render a module page**—and its Docusaurus Generator and Archify Adapter submodules now become visible. The internal features of those two submodules remain hidden until the user zooms in again.

### 5.4 Cross-cutting behavior

Not every relationship is a tree. A module can support several features, and a feature scenario can involve several submodules. External systems and shared contracts may also be referenced from multiple places. The hierarchy determines containment, while contracts make interactions across containment boundaries explicit.

Module containment and feature abstraction are hierarchical, while feature realization may be graph-shaped within and between adjacent levels. Concorde preserves both:

- the module hierarchy determines structural scope and navigation;
- the feature hierarchy preserves behavioral refinement across levels;
- stable references express cross-cutting relationships;
- scenario views show collaboration without flattening the whole project.

## 6. Why this helps AI and humans

### 6.1 Context for AI coding agents

Before implementing a feature, an agent should be able to load a bounded architecture context containing:

- the module that owns the feature;
- the module's responsibility and constraints;
- the relevant feature specification and scenarios;
- the immediate submodules available to realize the behavior;
- the provided and required contracts governing those submodules' interactions;
- deeper module documents only where the task requires them.

This context guides placement and decomposition without flooding the agent with the entire codebase.

### 6.2 Confidence for developers

The same information should let a developer:

- understand the project without reading all generated code;
- review whether the AI chose the right boundaries and dependencies;
- follow a feature from outcome to module collaboration;
- descend into detail selectively;
- detect when implementation changes have altered the intended structure;
- explain the system to another developer using shared, durable artifacts.

The goal is not blind trust in either code or documentation. It is a reviewable agreement between declared behavior, intended structure, and implementation evidence.

## 7. Artifact model

Concorde deliberately starts with two primary specification source formats. Contract documents may additionally reference standard interface definitions or custom JSON, YAML, TOML, or similar schema and example files when those files define the actual boundary representation.

### 7.1 Markdown

Markdown is used for information best read and reviewed as prose:

- module purpose and responsibility;
- feature specifications;
- requirements and acceptance criteria;
- scenario triggers, outcomes, and exceptional behavior;
- provided and required contracts, constraints, and architectural decisions;
- references to code, tests, and related modules.

Stable IDs and relationships can be stored in front matter so tools can validate and join documents without making the prose unpleasant to edit.

Example:

```markdown
---
id: feature.docs.publish
kind: feature
module: module.docs
refines:
  - feature.concorde.publish-architecture
scenarios:
  - scenario.docs.publish-success
---

# Publish architecture documentation

Generate a browsable site from the maintained Markdown and Archify JSON sources.
```

### 7.2 Archify JSON

Archify JSON is the maintained structural and visual source for a module-level view. It represents:

- the current module boundary;
- references to the current module's features and I/O contracts;
- immediate submodules and external actors;
- each immediate submodule's I/O contracts;
- connections and organization among the visible participants;
- the participants and ordered interactions in scenario traces;
- stable references back to Markdown specifications;
- layout or presentation information needed for a useful diagram.

Archify HTML is generated from this JSON. The generated HTML is not edited directly.

The two source formats divide responsibility instead of repeating the same content. Markdown owns what a feature and scenario mean; Archify JSON owns how the participating modules interact. A shared scenario ID joins the behavioral narrative to its structural trace, and Docusaurus presents them together.

### 7.3 Code and tests

Code and tests remain implementation and evidence. They are not replaced by the documentation model. Concorde may link module and feature IDs to source directories and test cases, but the first prototype should not attempt to reconstruct the complete architecture automatically.

### 7.4 Docusaurus output

Docusaurus is the generated human-facing presentation. It combines Markdown content, navigation metadata, traceability tables, and rendered Archify views. The site is a read model, not a third maintained source of truth.

### 7.5 Artifact authority

| Artifact | Authority |
|---|---|
| Feature `spec.md` | Intended behavior of the feature |
| Module Markdown | Intended responsibility, boundary, and constraints |
| Contract Markdown | Intended obligations across a module boundary |
| Standard or custom contract definition | Normative serialized representation exchanged across the boundary |
| Archify JSON | Intended module structure and scenario interactions at that level |
| Code | Actual implementation |
| Tests | Executable evidence about behavior and constraints |
| Generated Archify HTML | Visual projection of Archify JSON |
| Generated Docusaurus site | Published projection of the maintained sources |

When these disagree, Concorde should expose the disagreement rather than silently choose one representation as universally correct.

## 8. Unified specification repository

In vanilla Spec Kit, `specs/` is the default home of feature workspaces. Concorde broadens its meaning: `specs/` is the home of all maintained system intent, including module architecture, boundary contracts, and feature specifications. Architecture is therefore part of the specification tree rather than a separate top-level `architecture/` tree.

The specification tree mirrors the module hierarchy. A possible prototype layout is:

```text
specs/
└── concorde/
    ├── module.md
    ├── architecture.json
    ├── contracts/
    │   └── published-site/
    │       ├── contract.md
    │       ├── schema.json        # when custom
    │       └── example.json       # when custom
    ├── features/
    │   ├── 001-model-hierarchy/
    │   │   ├── spec.md
    │   │   ├── plan.md
    │   │   ├── tasks.md
    │   │   └── checklists/
    │   └── 002-publish-documentation/
    │       ├── spec.md
    │       ├── plan.md
    │       └── tasks.md
    └── modules/
        ├── authoring/
        │   ├── module.md
        │   ├── architecture.json
        │   ├── contracts/
        │   ├── features/
        │   │   └── 001-validate-architecture/
        │   │       ├── spec.md
        │   │       ├── plan.md
        │   │       └── tasks.md
        │   └── modules/
        └── documentation/
            ├── module.md
            ├── architecture.json
            ├── contracts/
            ├── features/
            └── modules/

.concorde/
├── config.yaml
└── schemas/
    ├── document.schema.json
    └── architecture.schema.json

docs-site/
├── docs/generated/
├── static/archify/
└── src/components/ArchifyEmbed.tsx

generated/
├── architecture-index.json
├── traceability.json
└── validation-report.json
```

Each module directory is a self-similar architecture specification package. It contains the module document, its level-specific Archify JSON, boundary contract documents and format definitions, Spec Kit feature workspaces owned by that module, and optional child module packages.

Within a feature workspace, `spec.md`, `plan.md`, `tasks.md`, checklists, and other design artifacts retain their normal Spec Kit meanings. The architecture files surrounding that workspace provide its durable module context.

Spec Kit defaults to creating a feature directly under `specs/`, but it also supports explicitly selecting a feature workspace through `SPECIFY_FEATURE_DIRECTORY` or `.specify/feature.json`. Concorde should use that mechanism to select a nested workspace such as `specs/concorde/modules/authoring/features/001-validate-architecture`. Downstream Spec Kit commands can then continue to resolve `spec.md`, `plan.md`, and `tasks.md` from the active workspace.

Concorde therefore needs a small feature-path selector in its extension or workflow, not a second canonical feature store. The same feature specification must never be copied into both a flat Spec Kit directory and the hierarchical Concorde tree.

## 9. Spec Kit integration

Spec Kit remains the feature-specification engine. Concorde adds architectural context before planning and preserves architectural understanding after implementation.

Spec Kit commands operate on one active feature workspace at a time. Concorde owns the surrounding module specification package and sets the active nested feature path before invoking those commands. This preserves the standard feature artifacts without implying that features are the only kind of specification in the project.

### 9.1 Division of responsibility

| Concern | Spec Kit | Concorde |
|---|---:|---:|
| Define feature behavior and requirements | Primary | Adds module context |
| Clarify user scenarios and edge cases | Primary | Adds structural questions |
| Choose implementation approach | Plan | Constrains placement and boundaries |
| Generate implementation tasks | Primary | Adds documentation and validation tasks |
| Implement the feature | Primary | Supplies bounded architecture context |
| Describe module and feature hierarchies | — | Primary |
| Enforce one-level visibility and zooming | — | Primary |
| Show submodule collaboration by scenario | — | Primary |
| Publish hierarchical architecture documentation | — | Primary |

### 9.2 Architecture-aware feature workflow

```text
Choose providing module
  → create or select its nested feature workspace under specs/
  → set SPECIFY_FEATURE_DIRECTORY for Spec Kit
  → link the feature to its parent-level feature when applicable
  → specify or revise feature behavior with Spec Kit
  → clarify scenarios
  → identify participating immediate submodules and their I/O contracts
  → update the module's one-level Archify JSON view
  → create the implementation plan and tasks
  → implement and test
  → validate feature, architecture, and evidence references
  → publish the updated hierarchy
```

Architecture work should happen before the implementation plan is treated as complete. Otherwise the plan may encode a structural decision that the developer never reviewed explicitly.

### 9.3 Concorde additions to a feature specification

Concorde should require the following metadata or sections:

- providing module ID;
- parent-level feature IDs that this feature refines or supports;
- stable feature and scenario IDs;
- participating submodule IDs for each scenario;
- provided and required contract IDs used by the feature and its scenarios;
- deeper feature or scenario references where behavior is delegated;
- expected source and test evidence.

### 9.4 Packaging direction

The likely distribution is a Spec Kit bundle containing:

- a preset that adds architecture metadata and scenario structure to feature artifacts;
- an extension that selects nested feature workspaces and adds Concorde validation, rendering, and publishing commands;
- a workflow that places architecture review into the normal feature lifecycle.

This should be validated in the prototype before deciding that a fork or a separate orchestration layer is necessary.

## 10. Authoring and review workflow

### 10.1 Bootstrap a project

1. Treat the project as the root module.
2. State its responsibility, I/O contracts, and top-level features.
3. Identify only its immediate child modules and their I/O contracts.
4. Describe the organization of those child modules and a representative scenario for each top-level feature.
5. Create the root's one-level Archify JSON view.
6. Descend only into child modules that need additional explanation.
7. At each selected child, define its features and link them to the parent-level features they refine or support.

This top-down process prevents early modeling from collapsing into a catalog of files and classes.

### 10.2 Add or change a feature

1. Locate the module that should own the behavior.
2. If ownership or abstraction level is unclear, resolve it before planning code.
3. Link a lower-level feature to the parent-level features it refines or supports.
4. Write or revise the feature specification and its primary scenario.
5. Identify the immediate submodules involved and the contracts governing every boundary crossing.
6. Define or revise those contracts and their standard or custom serialized representations before treating the architecture as agreed.
7. Update only the corresponding one-level Archify JSON and review the rendered scenario.
8. Zoom into affected submodules only where their internal design must change.
9. Run the Spec Kit planning, task, implementation, and convergence steps.
10. Update contract, code, and test evidence and rebuild the documentation.

### 10.3 Review a change

A reviewer should be able to see:

- the feature behavior being added or changed;
- the module and abstraction level that own it;
- the parent and lower-level feature refinement links affected;
- the scenarios affected;
- the module views changed at each level;
- new or changed dependencies and provided or required contracts;
- new or changed contract formats, schemas, field semantics, and compatibility expectations;
- links to implementation and test evidence;
- any unresolved disagreement between documentation and code.

Before/change/after diagrams may be useful for structural changes, but they are a review aid rather than a mandatory representation for every feature.

## 11. Docusaurus experience

The generated website should preserve the same hierarchy as the architecture sources.

### 11.1 Module page

Every module page should contain:

1. Module name, ID, purpose, and responsibility.
2. Its position in the hierarchy, with parent and child navigation.
3. Its own input and output contracts.
4. The features it owns at the current level.
5. Its immediate submodules and each submodule's input and output contracts.
6. A module-level Archify diagram, when it has submodules, showing the organization and connections among those visible elements.
7. Scenario selectors or links for highlighting the collaboration behind each current-level feature.
8. Links to source, tests, and active changes where available.

The page should not expand the features or children of its submodules. Selecting a submodule opens a new page that applies the same layout with that submodule as the current context.

### 11.2 Feature page

Every feature page should contain:

1. Feature outcome and providing module.
2. Its parent-level features and lower-level refinements.
3. Requirements and acceptance criteria.
4. Primary and alternative scenarios.
5. A bounded view of participating immediate submodules.
6. The contracts that must hold for the feature to function.
7. Links that zoom into lower-level features without expanding them in place.
8. Implementation and test evidence.

### 11.3 Contract page

Every contract page should contain:

1. Owning module, role, I/O flow direction, and external counterparties.
2. The features that expose or depend on the contract.
3. Whether the representation is a commonly adopted or custom format.
4. For a commonly adopted format: its name and version, a link to the authoritative definition, and a short explanation of the information passed.
5. For a custom format: the serialization language, normative schema or grammar, full field semantics, compatibility rules, and representative serialized examples.
6. Failure behavior and validation or test evidence.

The generated page should render custom schemas and examples directly so a programmer can inspect the boundary data without opening implementation code.

### 11.4 Navigation

The main navigation should be architecture-first:

```text
Project
└── Module
    ├── I/O contracts
    ├── Current-level features
    │   └── Feature → scenarios and refinement links
    └── Submodules
        └── Module boundary → zoom to next level
```

Search and cross-links should also allow users to navigate among features, scenarios, contracts, their format definitions, and every referenced module.

### 11.5 Generated views

For the prototype, each `architecture.json` file is validated and rendered into self-contained Archify HTML under `docs-site/static/archify/`. Docusaurus embeds that output through a sandboxed component and renders a textual summary outside the iframe for accessibility, search, and stable linking.

All generated pages and diagrams should record their source files and generator version. CI should be able to detect stale outputs reproducibly without an LLM call.

## 12. Deterministic tooling

Agent skills guide authoring and architectural reasoning. Deterministic tooling validates and builds the artifacts.

A prototype CLI could provide:

```text
concorde init
concorde feature create <module-id> <feature-name>
concorde feature select <feature-id>
concorde validate [path-or-id]
concorde context <module-or-feature-id>
concorde render [module-id]
concorde docs build
concorde status [module-or-feature-id]
```

| Command | Prototype behavior |
|---|---|
| `init` | Create the recursive source layout, schemas, and starter documents |
| `feature create` | Create a Spec Kit workspace under the owning module's `features/` directory and make it active |
| `feature select` | Resolve a feature ID and persist its nested workspace path for subsequent Spec Kit commands |
| `validate` | Check structure, IDs, references, hierarchy, scenario participants, contract representations and examples, and generated freshness |
| `context` | Return one bounded level: current module I/O and features, immediate submodules and their I/O summaries, organization, scenarios, and refinement links |
| `render` | Validate Archify JSON and produce the corresponding HTML view |
| `docs build` | Generate indexes, pages, traceability data, and embedded diagram assets |
| `status` | Report missing specifications, diagrams, evidence, or stale generated artifacts |

There should be no LLM call in validation or publication. AI-authored artifacts become inputs to reproducible tools.

## 13. Validation rules

The first prototype should validate rules that directly protect comprehension and structural control:

1. Every module, feature, and scenario has a unique stable ID.
2. Every maintained module architecture specification and feature workspace lives under the unified `specs/` hierarchy.
3. Every feature workspace is nested under its owning module's `features/` directory and contains one canonical `spec.md`.
4. No feature ID or specification is duplicated in a second flat or hierarchical location.
5. Every feature names exactly one providing module at its current level.
6. Every lower-level feature links to at least one feature owned by its parent module, unless explicitly marked internal.
7. Feature refinement links connect adjacent module levels and contain no cycles.
8. Every module explicitly declares its provided and required contracts, their I/O flow directions, and an explicit empty set when it has none.
9. Every feature references at least one provided contract through which it is made available and every required contract on which it depends.
10. Every non-leaf module declares its immediate submodules.
11. Every feature normally has at least one representative scenario; a feature without one explicitly records why an example would not add useful understanding.
12. Every scenario participant resolves to an immediate submodule or permitted external actor.
13. Every interaction crossing a module boundary references a declared contract.
14. Every contract reference resolves, has a role and flow direction, and identifies its owning module and external counterparty or audience.
15. Every contract declares its representation as either a commonly adopted format or a custom serialized format.
16. A commonly adopted format names the format and relevant version, links to its authoritative definition, and summarizes the information passed.
17. A custom format uses a programmer-readable serialization definition and supplies a normative schema or grammar, complete field semantics, compatibility rules, and representative examples.
18. Every custom example validates against its declared schema or grammar, and contract evidence checks implementation conformance where practical.
19. References to parent, child, deeper scenario, source, and test evidence resolve.
20. The module hierarchy contains no cycles.
21. A module-level view contains only the current module's I/O and features, immediate submodules and their I/O, relevant externals, and connections among them.
22. A module-level view does not expand child features, grandchildren, or deeper implementation details.
23. Every `architecture.json` file passes Archify validation.
24. Each documented scenario can be found in the corresponding module-level architecture view, unless explicitly marked prose-only.
25. Generated Archify HTML and Docusaurus pages match the maintained sources.
26. Unknown or missing implementation evidence is reported as unknown, not agreement.

The validator should not require every class, function, or call edge to appear in the architecture. Concorde protects intentional structure, not a second copy of the codebase.

## 14. Prototype components

| Component | Responsibility |
|---|---|
| Spec Kit bundle | Architecture-aware templates, commands, and workflow integration |
| Concorde CLI | Identity, reference, hierarchy, scenario, contract representation, and freshness validation |
| Markdown sources | Module, feature, contract, scenario, constraint, and decision intent |
| Archify JSON sources | Module-level structure and scenario interactions |
| Archify renderer integration | Validation and generation of interactive HTML diagrams |
| Docusaurus generator | Hierarchical navigation, pages, indexes, cross-links, and embedded views |

TypeScript is a pragmatic implementation language for the CLI and generator because types and validation logic can be shared with Docusaurus. The prototype should still keep the Markdown front matter and JSON schemas portable.

## 15. First prototype scope

### 15.1 Included

- Model one real project area as a root module with two or three levels.
- Store architectural and behavioral specifications together under one recursive `specs/` hierarchy.
- Select nested Spec Kit feature workspaces through the active feature-directory mechanism.
- Define aligned module containment and feature refinement hierarchies.
- Enforce the one-level visibility rule for modules, features, I/O contracts, and organization.
- Maintain module and feature documentation in Markdown.
- Maintain provided and required module contracts in Markdown.
- Represent each contract with either a referenced commonly adopted format or a fully documented custom serialized format.
- Validate custom schemas and representative payload examples.
- Maintain one Archify JSON view per modeled non-leaf module.
- Provide stable IDs and validated cross-references.
- Add Concorde metadata and architecture review to a Spec Kit feature workflow.
- Generate a Docusaurus site whose navigation mirrors the module hierarchy.
- Render and embed Archify HTML for each modeled level.
- Provide bounded context retrieval for an AI coding agent.
- Detect stale generated outputs and broken references in CI.

### 15.2 Deferred

- Automatic reconstruction of the complete module hierarchy from code.
- Modeling every class, function, or call edge.
- Automatic architectural correctness or risk scoring.
- Runtime topology ingestion.
- Organization-wide or cross-repository architecture catalogs.
- A universal semantic model separate from Markdown and Archify JSON.
- Automatic acceptance of AI-proposed structural changes.
- Mandatory before/change/after diagrams for ordinary feature work.

## 16. Prototype milestones

### Milestone 1: Prove the hierarchy

- Move all maintained architecture and feature intent into the unified `specs/` tree.
- Select one subsystem with at least two meaningful levels.
- Write the root and child module documents.
- Define features, refinement links, I/O contracts, contract representations, and primary scenarios at each level.
- Test whether a developer can navigate the hierarchy without reading the code.

### Milestone 2: Prove the visual model

- Create one Archify JSON view per modeled non-leaf module.
- Render the current module's features and I/O, its immediate submodules and their I/O, and their organization.
- Render scenario-specific interactions among only those visible elements.
- Validate that views reveal neither child features nor grandchildren.

### Milestone 3: Integrate feature development

- Adapt a Spec Kit feature artifact with providing-module and scenario metadata.
- Reference the provided and required contracts that make the feature functional.
- Validate standard-format references and custom schemas, field semantics, and examples.
- Load bounded module context before planning.
- Exercise one feature change that affects more than one architectural level.
- Validate all IDs and scenario participants.

### Milestone 4: Publish the documentation

- Generate hierarchical Docusaurus navigation and module, feature, and contract pages.
- Embed the rendered Archify HTML.
- Add search-friendly textual relationships and provenance.
- Build the site reproducibly in CI.

### Milestone 5: Evaluate confidence and maintenance cost

- Ask an unfamiliar developer to explain the modeled subsystem.
- Ask a maintainer to place and review a new feature using the hierarchy.
- Measure how many source artifacts must change for a typical feature.
- Remove or simplify any field that does not improve agent guidance or human understanding.

## 17. Acceptance criteria for version 0.1

The prototype succeeds if a developer unfamiliar with the chosen subsystem can:

1. Start at the project page and identify its main modules and features.
2. Distinguish the current module's features and I/O from the visible submodules' I/O.
3. Explain the organization and contract-governed connections among the immediate submodules.
4. Confirm that submodule features and grandchildren are hidden at the current level.
5. Open one participating submodule and see the same view repeated with its own features, I/O, children, and organization.
6. Follow a feature-refinement link from a parent-level feature to a lower-level feature.
7. Identify the contracts governing each interaction that crosses a module boundary.
8. Explain which contracts must hold for a selected feature to function.
9. Identify whether a contract uses a commonly adopted or custom format and summarize the information it passes.
10. Inspect a custom serialized example and understand every field from its schema and semantic documentation.
11. Locate a module architecture specification and all of its feature workspaces within the same `specs/` subtree.
12. Select a nested feature workspace and run normal Spec Kit planning and task commands against it.
13. Locate the specification, architecture view, source evidence, and tests through stable links.
14. Decide at which module and feature level a proposed behavior belongs before implementation planning begins.
15. Detect a deliberately broken module, feature, refinement, scenario, contract, schema, example, or participant reference.
16. Detect stale generated documentation in CI.
17. Rebuild the same Archify HTML and Docusaurus site without an LLM.

The prototype fails if the hierarchy merely reproduces the source tree, if diagrams require the whole project to be understood at once, or if developers must duplicate the same intent across several maintained formats.

## 18. Risks and mitigations

| Risk | Mitigation |
|---|---|
| The architecture becomes a duplicate of the code | Model responsibilities, boundaries, and scenarios—not implementation inventory |
| Every feature appears to span the whole project | Place it at the nearest common owning module and decompose lower-level behavior |
| High-level diagrams leak excessive detail | Restrict default views to the current module and its immediate children |
| Module and feature hierarchies drift apart | Require lower-level features to refine parent-level features across adjacent module levels |
| A parent view exposes child internals | Validate the one-level visibility rule and link to deeper pages instead of expanding them |
| Markdown and Archify JSON drift apart | Use stable IDs and deterministic cross-artifact validation |
| Module interactions bypass documented contracts | Require every boundary-crossing scenario interaction to reference a provided or required contract |
| A custom contract hides meaning in implementation code | Require a readable schema, complete field semantics, and validated representative examples |
| Documentation copies an entire standard unnecessarily | Reference its authoritative definition and maintain only a concise information summary |
| Hierarchy hides important cross-cutting dependencies | Preserve typed references and scenario links across the tree |
| AI-authored diagrams appear authoritative | Treat them as proposed intent until reviewed and validated |
| Documentation becomes burdensome | Require only information that improves placement, review, navigation, or confidence |
| Physical nesting bypasses Spec Kit's default feature location | Explicitly select the nested workspace through `SPECIFY_FEATURE_DIRECTORY` or `.specify/feature.json` |
| Docusaurus output becomes another editable source | Generate it reproducibly and mark it read-only |
| Developers infer implementation correctness from architecture | Present tests and source links as separate evidence, including unknowns |

## 19. Open design questions

- How should feature names and numbering be assigned within each module's nested `features/` directory?
- How much of a scenario belongs in Markdown versus Archify JSON without duplicating intent?
- Which Archify JSON fields are stable enough to be treated as maintained architecture source rather than generated rendering input?
- Can a scenario reference a deeper scenario directly, or should the relationship always pass through a lower-level feature?
- When should a lower-level feature refine one parent feature versus support several parent features?
- Which lower-level behaviors are legitimately internal and therefore need no parent-feature refinement link?
- How should a shared submodule that serves multiple parents be represented without breaking the primary containment hierarchy?
- Which contract fields are essential for operations, data, failures, compatibility, and versioning without creating excessive documentation?
- What qualifies as a commonly adopted format, and who approves that classification for the project?
- How should leaf modules link to code without forcing directory structure to equal architecture?
- Which changes require explicit architecture review, and which can update documentation during normal convergence?
- Should Concorde persist the active nested feature only through `.specify/feature.json`, or also expose a higher-level feature-selection index?

## 20. Recommended first implementation decision

Build the smallest end-to-end example that demonstrates recursive reasoning:

1. Model Concorde itself as the root module.
2. Give it two top-level features and two or three child modules.
3. Choose one child module and model one additional level beneath it.
4. Define parent and lower-level features with explicit refinement links.
5. Document the I/O contracts of the root, the child modules, and the selected grandchild modules.
6. Represent one contract with a commonly adopted format and another with a custom JSON, YAML, or TOML format.
7. For the custom contract, provide a schema, complete field semantics, and a validated representative example.
8. Write one primary scenario at each of those two levels.
9. Store the feature workspaces, module documents, contracts, and both structural views in one hierarchical `specs/` tree.
10. Generate linked Docusaurus pages that preserve the one-level visibility rule while allowing explicit zooming.
11. Use the resulting context to guide an AI agent through one small implementation change.
12. Evaluate whether the developer can review the placement and collaboration of the change without inspecting every line of code.

This vertical slice tests Concorde's essential promise: feature specifications explain what the software should do, while a hierarchical architecture explains where that behavior belongs and how progressively smaller modules collaborate to provide it.

## 21. Reference documentation

- [Spec Kit repository and workflow overview](https://github.com/github/spec-kit)
- [Spec Kit quickstart](https://github.com/github/spec-kit/blob/main/docs/quickstart.md)
- [Spec Kit core path and active-feature reference](https://github.com/github/spec-kit/blob/main/docs/reference/core.md)
- [Spec Kit extensions](https://github.com/github/spec-kit/blob/main/docs/reference/extensions.md)
- [Spec Kit presets](https://github.com/github/spec-kit/blob/main/docs/reference/presets.md)
- [Spec Kit bundles](https://github.com/github/spec-kit/blob/main/docs/reference/bundles.md)
- [Spec Kit: spec of specs](https://github.com/github/spec-kit/blob/main/docs/concepts/spec-of-specs.md)
- [Archify repository](https://github.com/tt-a1i/archify)
- [Archify schema documentation](https://github.com/tt-a1i/archify/blob/main/archify/schemas/README.md)
- [Docusaurus MDX and React integration](https://docusaurus.io/docs/markdown-features/react)

---

## Appendix A: Prototype authoring rules

1. The project is the root module.
2. All maintained behavioral and architectural intent lives under one hierarchical `specs/` tree.
3. Every module has one clear responsibility.
4. Every module documents the contracts it provides to and requires from externals.
5. Every contract records both its provided/required role and its I/O flow direction.
6. Every contract uses either a commonly adopted format or a programmer-readable custom serialized format.
7. A commonly adopted format has an authoritative reference and a concise explanation of the information passed.
8. A custom format has a normative schema or grammar, complete semantic documentation, compatibility rules, and validated representative examples.
9. Every feature has one providing module at its current architectural level.
10. Every feature has one canonical Spec Kit workspace nested under its owning module.
11. Every lower-level feature refines or supports a parent-level feature unless explicitly internal.
12. Every feature references the contracts that must hold for it to function.
13. Every feature normally has a representative primary scenario; exceptions are explicit.
14. A scenario uses immediate submodules by default; deeper details belong in lower-level views.
15. Every scenario interaction crossing a module boundary names its governing contract.
16. A view shows the current module's I/O and features, its immediate children and their I/O, and their organization—nothing deeper.
17. Every module may be opened as a new level with the same visibility rule.
18. Stable IDs connect Markdown, Archify JSON, code evidence, tests, and generated pages.
19. Markdown and Archify JSON are maintained sources; Archify HTML and Docusaurus pages are generated.
20. Architecture describes intended structure; code and tests provide distinct implementation evidence.
21. AI-generated architecture changes require review and deterministic validation.
22. The model records architecturally meaningful facts, not every implementation detail.
23. No intent should need to be maintained canonically in more than one place.

## Appendix B: Minimal module document

```markdown
---
id: module.docs
kind: module
parent: module.concorde
view: specs/concorde/modules/documentation/architecture.json
children:
  - module.docs.site-generator
  - module.docs.archify-adapter
features:
  - feature.docs.publish
contracts:
  provided:
    - contract.docs.published-site
  required:
    - contract.docs.archify-renderer
source:
  - packages/docs/
---

# Documentation

## Responsibility

Publish the maintained architecture and feature sources as a hierarchical,
browsable developer website.

## Boundary

This module owns documentation generation and presentation. It does not own
feature specification or architecture authoring.
```

## Appendix C: Minimal feature and scenario document

```markdown
---
id: feature.docs.publish
kind: feature
module: module.docs
refines:
  - feature.concorde.publish-architecture
scenarios:
  - scenario.docs.publish-success
contracts:
  - contract.docs.published-site
  - contract.docs.archify-renderer
evidence:
  tests:
    - tests/docs/publish.test.ts
---

# Publish architecture documentation

## Outcome

A developer can browse the current module hierarchy, feature specifications,
and architecture views in one generated site.

## Primary scenario: successful publication

**ID:** `scenario.docs.publish-success`

**Trigger:** A maintainer requests a documentation build from validated sources.

**Outcome:** The maintainer receives a browsable site containing the current
module hierarchy, feature specifications, and architecture views.

The ordered collaboration and its participants are maintained under
`scenario.docs.publish-success` in the providing module's `architecture.json`.
```

## Appendix D: Minimal contract document

```markdown
---
id: contract.docs.published-site
kind: contract
module: module.docs
role: provided
flow: output
representation:
  kind: standard
  format: HTML
  version: living-standard
  authoritative_definition: https://html.spec.whatwg.org/
  information_passed: Generated module, feature, contract, and architecture documentation.
consumers:
  - external.maintainer
features:
  - feature.docs.publish
version: 1
evidence:
  tests:
    - tests/docs/published-site-contract.test.ts
---

# Published architecture site contract

## Purpose

Provide maintainers with a browsable representation of every validated module,
feature, scenario, and architecture view.

## Representation

The contract uses standard HTML. It passes generated documentation pages,
navigation links, textual architecture information, and embedded Archify views
to a maintainer's web browser.

## Preconditions

- All maintained Markdown and Archify JSON sources pass validation.

## Guarantees

- Every accepted module and feature has a stable URL.
- Every non-leaf module page includes its validated architecture view.
- Every displayed feature links to the contracts on which it depends.

## Failure behavior

- Publication fails without replacing the last successful output when source
  validation or the Docusaurus build fails.

## Compatibility

- Stable module and feature URLs remain valid within a major documentation
  version.
```

## Appendix E: Minimal custom contract representation

````markdown
---
id: contract.docs.build-request
kind: contract
module: module.docs
role: provided
flow: input
representation:
  kind: custom
  serialization: json
  version: 1
  schema: build-request.schema.json
  examples:
    - examples/build-request.json
---

# Documentation build request contract

## Information passed

This message asks the Documentation module to build architecture pages for a
specific revision and selected modules.

## Fields

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `format_version` | integer | yes | Major version of this custom message format; currently `1` |
| `request_id` | string | yes | Correlation ID for this build request and its result |
| `source_revision` | string | yes | Version-control revision containing the source artifacts to build |
| `module_ids` | array of strings | yes | Stable IDs of modules to publish; an empty array means all modules |
| `fail_on_warning` | boolean | no | Whether validation warnings fail the build; defaults to `false` |

## Representative JSON

```json
{
  "format_version": 1,
  "request_id": "build-2026-08-19-001",
  "source_revision": "abc123",
  "module_ids": ["module.docs"],
  "fail_on_warning": true
}
```

## Compatibility

- Version 1 producers may add optional fields.
- Version 1 consumers ignore unknown optional fields.
- Removing a field or changing its meaning requires a new major format version.

The adjacent `build-request.schema.json` file is normative. CI validates every
checked-in example and the implementation's emitted or accepted messages
against it.
````
