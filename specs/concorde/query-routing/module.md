# Query and Routing

## Purpose

Query and Routing answers questions from selected specifications and identifies the Module responsible for an intended task. It preserves the developer’s request rather than rewriting the goal to fit available code. Missing knowledge leads to explicit selection or a reported gap, not unrestricted searching.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Context](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec context](../harness/context.md#terminology) | Defined in What information a worker receives. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Graph](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Reference](../spec/registry.md#terminology) | Defined in Registry. |

## Usage

Use `concorde-main` to ask a Spec-grounded question; composing discovery callers can request one
owning Module route for an unchanged task and constraints. Target/focus hints guide selection but
supply no additional reading authority. Discovery begins with the entry Module's complete context
including both document roles and metadata, and explicitly selects additional complete contexts
only when needed. It does not inspect code to invent missing behavior.
[Topology Module](../topology/module.md) actions sharing the main entry have their own provider contract.

An answer includes limitations; a route retains the caller's task rather than rewriting it.
Missing necessary promises produce attributed gaps, contradictions and prohibitions remain
distinct, and exhausted discovery returns an explicit limit outcome. Queries author no files and
create no candidate. Human clarification requires fresh admitted input, not unbounded expansion.
A saved candidate with a bound owner resumes that identity rather than silently rerouting to
another Module. A route selects responsibility; it is not implementation completion or permission
to change a provider's files.

For example, a checkout question may require Inventory's reservation contract. The selection must
include that knowledge explicitly. Inventory's own unrelated references do not recursively enter
the reader's context merely because Inventory was selected.

## Design

<a id="entity.query-routing.adapter"></a><a id="entity.query-routing.selection"></a>

The [discovery Graph](execution-reference.md#query-and-routing-discovery-graph-discovery-graph) alternates a fresh
discovery decision with deterministic admission of explicitly selected complete contexts. A router
returns identities; the host binds the original task and constraints rather than trusting rewritten
intent. An answerer can complete directly from the indexed/granted originals without reader-worker
summaries or a synthesis stage.

The [query Graph](execution-reference.md#query-and-routing-query-graph-query-graph) returns the last admitted decision.
Expansion limits and stop edges bound missing-context reasoning. Provider references expand once;
links and implementation files never become implicit discovery routes.

## Relationships

The diagram shows how an Admitted selection reaches a discovery worker. [Spec Module](../spec/module.md) resolves complete
Module contexts and their provenance, [Harness Module](../harness/module.md) binds the fresh worker to that selection, and
[Development Module](../development/module.md) admits expansion and returns its typed outcome. Dependency arrows describe provider
use, not extra context: links, hints and provider implementation files are not implicit expansion
routes. The selected originals remain the source of the answer rather than generated summaries.

```mermaid
flowchart TB
    accTitle: Query and Routing entities and dependencies
    accDescr: Query and Routing resolves explicit complete Module contexts through Spec, binds fresh discovery workers through Harness and returns admitted answers routes or stopping outcomes through the host.
    e0["Query and Routing adapter"]
    e1["Development"]
    e2["Harness"]
    e3["Spec"]
    e0 -->|admits discovery and returns typed outcomes through| e1
    e0 -->|binds isolated discovery workers through| e2
    e0 -->|resolves complete discovery contexts through| e3
    domain_selection["Admitted selection"]
    e0 -->|expands only explicitly admitted| domain_selection
```

### Development

<a id="entity.query-routing.development"></a><a id="agreement.document.query-routing.module.1"></a>

Admit question and routing requests, bound discovery expansion and return answers, routes or attributed stopping outcomes.

This collaboration applies when main answers a question or a discovery consumer requests owner selection.

- [Host admission](../development/interfaces.md#operation-execution-boundary); Recheck admitted intent and returned identities before accepting host state; a rejected result cannot advance the dependent step.

### Harness

<a id="entity.query-routing.harness"></a><a id="agreement.document.query-routing.module.2"></a>

Freeze explicitly selected complete contexts and run fresh isolated discovery-worker (answerer, router or topology-designer) invocations without code contents.

This collaboration applies at the initial discovery-worker call and each admitted discovery expansion.

- [Explicit complete-context discovery](../harness/contracts.md#context-global-spec-context-assembly); Supply only mode-admitted inputs and require a matching completion; unavailable enforcement stops execution without a wider grant.

### Spec

<a id="entity.query-routing.spec"></a><a id="agreement.document.query-routing.module.3"></a>

Resolve entry and explicitly selected Module contexts with unique document ownership, inclusion provenance and byte digests.

This collaboration applies when selecting discovery inputs, validating target/focus hints or resolving an additional admitted context.

- [Owner and context resolution](../spec/contracts.md#registry-stable-id-spec-context-queries); Reconstruct current resolutions after input changes; unresolved ownership, missing required definitions or stale revisions block dependent use.

## Precise specifications

The Query and Routing Module owns the exact obligations and interface details in [requirements](requirements.md), [scenarios](scenarios.md) and the
[execution and record contracts](execution-reference.md#query-and-routing-query-and-routing-agent-graph).
These companions are part of the same complete Module specification, not separate topic owners.
