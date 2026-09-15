```concorde-document
{
  "id": "document.topology.module",
  "owner": "module.topology",
  "main_visible": true
}
```

# Topology

## Usage & Contract

### Purpose

Topology designs, prepares and atomically applies changes to registered Module structure and owned definitions. It serves developers evolving ownership, references, dependencies and file bindings through the existing accepted design and application boundaries.

### Usage

Use the topology actions of `concorde-main` when Module ownership, references, composition,
dependencies or file bindings must change together. Supply intended behavior and constraints to
design-topology. Review the proposed registry before accept-topology prepares owned Specs and
compatibility evidence; review that exact prepared application before apply-topology changes files.
The two acceptances concern different artifacts and neither can be inferred from elapsed time.

Authors receive their own candidate contexts and may replace only candidate-owned documents.
A shared definition is authored once; affected consumers are reviewed independently. Rejected,
stale or conflicting input leaves the pre-application project unchanged rather than partially
changing ownership. New Modules need usable external contracts and internal designs, not merely
new directories. The existing main adapter supplies these actions without adding a new callable
flow entry. See [topology](topology.md) for preparation, application and recovery.

### Requirements

#### req.development.shared-document-agreement — Shared changes require owner authoring and consumer agreement

A referenced document change SHALL be applied only from its sole owner's proposal after compatibility
review in every affected consumer's resolved context.

### Scenarios

#### scenario.development.topology-design — Design a candidate registry

- GIVEN a change to identities, composition, dependencies, document ownership and references or file listings
- WHEN `concorde-main` runs `design-topology`
- THEN it admits exact registry metadata and the Module kind definition, withholds implementation file contents, and returns a digest-bound candidate registry, local Spec tasks, migration constraints and acceptance conditions
- AND no project file changes

#### scenario.development.topology-accept — Accept a design and author local Specs

- GIVEN a developer accepts a topology design
- WHEN `concorde-main` runs `accept-topology`
- THEN it rechecks the complete discovery context, starts a fresh target-local Spec author for each affected Module, and validates their combined output against an in-memory registry and document overlay
- AND the full authored documents are stored only in a before-digest-bound application artifact, and the public response exposes only its ArtifactRef

#### scenario.development.topology-apply — Apply a reviewed artifact

- GIVEN a developer accepts the exact prepared application artifact
- WHEN `concorde-main` runs `apply-topology`
- THEN it atomically applies the reviewed registry and document replacements together
- AND successful application updates the accepted structure and sources in the same transaction

#### scenario.development.topology-stale — Stale or conflicting input is rejected

- GIVEN the registry, Protocol or a candidate's shared document bytes changed since the design was produced, or a non-owner proposes a provider document replacement or affected-consumer compatibility remains unresolved
- WHEN `accept-topology` or `apply-topology` processes that input
- THEN the host rejects the mutation and leaves the pre-existing project files unchanged
- AND no target author ever writes a project file directly

See [owner authoring and consumer agreement](#req.development.shared-document-agreement).


The detailed contract is [Accepted atomic topology](topology.md).

## Architecture & Realization

### Design

Preparation orders candidate authors so providers precede consumers, validates the complete
overlay and obtains independent affected-context reviews before persisting an exact application.
Application then rechecks the accepted artifact, registry/Protocol identity and every before-digest
before one transaction. [Topology Flows](topology.md#architecture--realization) expose those distinct
boundaries and stop conditions.

Each candidate definition has one author/owner. Comparing old and candidate contexts captures
consumers affected by reference or ownership changes even when the path set is unchanged. Keeping
prepared bytes separate from accepted effects supports the external two-acceptance and no-partial-
application promises; it does not add arbitrary flow configuration or provider write grants.

### Entities

```concorde-entities
[
  {
    "id": "entity.topology.adapter",
    "title": "Topology adapter",
    "kind": "shared program",
    "responsibility": "Topology designs, prepares and atomically applies changes to registered Module structure and owned definitions. It serves developers evolving ownership, references, dependencies and file bindings through the existing accepted design and application boundaries.",
    "files": [
      "capabilities/main.py",
      "tests/concorde/harness/test_scoped_protocol.py"
    ]
  },
  {
    "id": "entity.topology.development",
    "title": "Development",
    "kind": "used module",
    "target_id": "module.development",
    "responsibility": "Admit topology actions and exact acceptance artifacts, store before-digest-bound applications and apply accepted replacements atomically."
  },
  {
    "id": "entity.topology.harness",
    "title": "Harness",
    "kind": "used module",
    "target_id": "module.harness",
    "responsibility": "Run an isolated topology designer and separate candidate-local Spec authors and compatibility reviewers under their own contexts."
  },
  {
    "id": "entity.topology.spec",
    "title": "Spec",
    "kind": "used module",
    "target_id": "module.spec",
    "responsibility": "Resolve registry ownership and old/candidate contexts and validate the combined registry and document overlay."
  },
  {
    "id": "entity.topology.query-routing",
    "title": "Query and Routing",
    "kind": "used module",
    "target_id": "module.query-routing",
    "responsibility": "Supply explicit complete-context discovery for topology design without reading implementation to infer missing contracts."
  },
  {
    "id": "entity.topology.application",
    "title": "Prepared application",
    "kind": "record",
    "responsibility": "Digest-bound registry and sole-owner document replacements for exact accepted application."
  }
]
```

### Relationships

This diagram separates preparing a topology change from applying the Prepared application. Query
and Routing supplies explicit discovery, Spec resolves old and candidate ownership and references,
and Harness isolates designers, owner-local authors and independent reviewers. Development retains
the exact proposal and applies only the accepted transaction. These provider collaborations do not
transfer document ownership to Topology or turn a designer's proposed paths into write authority.

```mermaid
flowchart TB
    accTitle: Topology entities and dependencies
    accDescr: Topology selects complete design contexts, binds separate designers authors and reviewers, validates the registry and document overlay and applies the exact accepted transaction through the host.
    e0["Topology adapter"]
    e1["Development"]
    e2["Harness"]
    e3["Spec"]
    e4["Query and Routing"]
    e0 -->|prepares and applies accepted transactions through| e1
    e0 -->|binds isolated designers authors and reviewers through| e2
    e0 -->|resolves and validates candidate topology through| e3
    e0 -->|selects topology design contexts through| e4
    domain_application["Prepared application"]
    e0 -->|prepares exact accepted replacements in| domain_application
```


### Dependencies and composition

```concorde-dependencies
[
  {
    "target_id": "module.development",
    "responsibility": "Admit topology actions and exact acceptance artifacts, store before-digest-bound applications and apply accepted replacements atomically.",
    "selection_condition": "When design-topology, accept-topology or apply-topology crosses its existing host boundary.",
    "relied_upon_promises": [
      "[Host admission](../development/interfaces.md#capability-execution-boundary); Recheck admitted intent and returned identities before accepting host state; a rejected result cannot advance the dependent step."
    ]
  },
  {
    "target_id": "module.harness",
    "responsibility": "Run an isolated topology designer and separate candidate-local Spec authors and compatibility reviewers under their own contexts.",
    "selection_condition": "During design and accepted preparation, before each fresh topology designer, author or consumer-review invocation.",
    "relied_upon_promises": [
      "[Explicit complete-context discovery](../harness/context.md#global-spec-context-assembly); Supply only mode-admitted inputs and require a matching completion; unavailable enforcement stops execution without a wider grant."
    ]
  },
  {
    "target_id": "module.spec",
    "responsibility": "Resolve registry ownership and old/candidate contexts and validate the combined registry and document overlay.",
    "selection_condition": "When forming a candidate topology, finding affected consumers or validating the exact prepared application.",
    "relied_upon_promises": [
      "[Owner and context resolution](../spec/registry.md#stable-id-spec-context-queries); Reconstruct current resolutions after input changes; unresolved ownership, missing required definitions or stale revisions block dependent use.",
      "[Structural validation](../spec/structure.md#scenario.spec.validate-success); require consistent registered state without claiming semantic completeness."
    ]
  },
  {
    "target_id": "module.query-routing",
    "responsibility": "Supply explicit complete-context discovery for topology design without reading implementation to infer missing contracts.",
    "selection_condition": "When design-topology selects or expands the complete Module contexts needed to propose a registry.",
    "relied_upon_promises": [
      "[Explicit discovery and routing](../query-routing/query-and-routing.md); Preserve submitted task and constraints; accept only admitted selections and stop on gaps, ambiguity or discovery limits."
    ]
  }
]
```


### Realization and reuse limits

This Module and its consumers are siblings under Concorde Framework. Declared files explicitly
share the existing adapter realization with Development; no new runtime package, public Skill,
Agent grant or configurable arbitrary flow is created by this Spec boundary. Host admission,
phase artifacts and permissions remain mandatory. A new flow requires declared composition and
an implementation of its sequencing, artifact admission, recovery and completion policies before
it can execute. The existing host package still realizes common dispatch and provider internals.
