# Spec Authoring

## Purpose

Spec Authoring proposes changes to a Module’s intended behavior and design. It works from the allowed specifications and explicit intent, not from source code used to guess missing requirements. The host checks and applies owned proposals; independent review belongs to the calling workflow.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Grant](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Blocker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Reference](../spec/registry.md#terminology) | Defined in Registry. |
| [Ownership](../spec/registry.md#terminology) | Defined in Registry. |
| [Flow](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Internal capability](../development/module.md#terminology) | Defined in Development capability host. |
| [Skill](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Usage

Use `specify` from a declared composing capability to author or revise the selected Module's owned
Spec documents. Supply the task, constraints and current complete owned/direct-reference context;
this private bound provider has no direct Skill/CLI entry and does not select a different owner.
Its author returns full Markdown replacements for host acceptance, never direct project writes.
Write consumer usage and guarantees first, then the design and internal constraints that fulfill
them, keeping each definition canonical and preserving stable identities.

Unknown meaning returns attributed gaps without replacements. Foreign, malformed or stale output
is rejected with prior document bytes and blockers preserved. Referencing a provider permits
reading, not replacing its Spec. Ordinary authoring retains metadata and membership; ownership or
reference changes require topology reconciliation. Shared changes require separate affected-consumer
compatibility checks. Independent review, accepted-authoring reuse and completion belong to the
calling Flow, not to this author. See [authoring](authoring.md) for the precise input/output and
failure contract.

## Design

<a id="entity.spec-authoring.adapter"></a><a id="entity.spec-authoring.replacements"></a>

A fresh author sees the full contract and task but no implementation contents or write grant.
It returns complete owned Markdown replacements; the host checks metadata, current bytes and
allowed paths before applying them as one accepted change. Independent candidate reviews assess
affected consumers in their own contexts, preserving provider ownership and preventing copied
shared definitions from becoming competing authorities.

This proposal/acceptance split realizes the [authoring boundary](authoring.md) without trusting
model-authored paths as permission. Ordinary authoring preserves registered metadata; topology
reconciliation remains the separate mechanism for structural changes. Accepted-output reuse and
independent review ordering belong to the consuming Flow.

## Relationships

The diagram distinguishes proposing Owned replacements from applying them. [Spec Module](../spec/module.md) supplies document
ownership and affected-consumer scope; the [Harness Module](../harness/module.md) gives the fresh author read-only contract access;
[Development Module](../development/module.md) checks and applies accepted proposals. The author itself never gains a project write
grant. These are dependencies on sibling responsibilities, not structural ownership of providers,
and a provider reference does not permit a replacement of that provider's documents.

```mermaid
flowchart TB
    accTitle: Spec Authoring entities and dependencies
    accDescr: Spec Authoring resolves owned documents and consumers through Spec, runs an isolated author through Harness and applies accepted replacements only through the host.
    e0["Spec Authoring adapter"]
    e1["Development"]
    e2["Harness"]
    e3["Spec"]
    e0 -->|applies accepted owned replacements through| e1
    e0 -->|binds an isolated Spec author through| e2
    e0 -->|resolves owned documents and consumers through| e3
    domain_replacements["Owned replacements"]
    e0 -->|proposes and applies accepted| domain_replacements
```

### Development

<a id="entity.spec-authoring.development"></a><a id="agreement.document.spec-authoring.module.1"></a>

Admit the bound authoring request, check returned replacement identity and apply only accepted owned document replacements.

This collaboration applies when ordinary specify enters, accepts replacement output or preserves blockers after rejection.

- [Host admission](../development/interfaces.md#capability-execution-boundary); Recheck admitted intent and returned identities before accepting host state; a rejected result cannot advance the dependent step.

### Harness

<a id="entity.spec-authoring.harness"></a><a id="agreement.document.spec-authoring.module.2"></a>

The Harness Module runs a fresh isolated Spec author with complete Spec inputs, no inherited artifacts, no implementation contents and no project write grant.

This collaboration applies before launching spec-engineer specify mode and when validating its completion.

- [Complete context selection](../harness/contracts.md#contract.context.selection); Supply only mode-admitted inputs and require a matching completion; unavailable enforcement stops execution without a wider grant.

### Spec

<a id="entity.spec-authoring.spec"></a><a id="agreement.document.spec-authoring.module.3"></a>

Resolve sole document ownership, complete references and affected consumers, and validate replacement structure.

This collaboration applies when determining allowed replacement documents and checking their current contract and consumer set.

- [Owner and context resolution](../spec/contracts.md#registry-stable-id-spec-context-queries); Reconstruct current resolutions after input changes; unresolved ownership, missing required definitions or stale revisions block dependent use.

## Precise specifications

The Spec Authoring Module owns the exact obligations and interface details in [requirements](requirements.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
