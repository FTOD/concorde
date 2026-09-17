# Issues

## Purpose

Issues keeps a durable record of observed problems and supports their explicit investigation, repair and verification. Recording a problem does not itself stop work or authorize code changes. Developers use it when a concern must remain visible beyond the current conversation.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Issue](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Blocker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Ready](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Evidence](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Disposition](lifecycle.md#terminology) | Defined in Solving a recorded problem. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Graph](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Usage

Workers use `report_issue` during any admitted invocation, including a Spec-only query or review.
The host returns an immutable receipt and the current record revision before the worker continues.
A final stage blocker or review judgment references that receipt instead of repeating the problem.
A reviewer can collect all independently assessable findings before finishing; an implementer can
repair or work around a problem only within the current task and its existing authority.

Use `concorde-issues` with `action=list|show|report|reopen|solve`. Listing and showing records are
read-only. Reporting is bookkeeping without a managed change requirement. Solve selects one Issue,
uses ordinary development and optional verification or Spec repair, and ends at a verified ready
candidate, a bounded stop or a precise need for a developer decision. It never delivers or merges.
See [the public interface](interfaces.md), [records and reporting](issues.md) and
[the solving lifecycle](lifecycle.md) for fields, effects and error behavior.

Records under `.concorde/issues/` travel through Git with the branch. Closing an Issue in a candidate
is not a claim about primary. Closed records remain available. Old Reflections are archived
historical material, not active Issues; no old report is silently classified or approved.

## Design

<a id="entity.issues.runtime"></a>

The Issue runtime validates report references, coordinates the solving graph and separates durable
problem content from task-local blocker relations. Its file transactions are host-only and use
exact-byte checks. Individual reports are immutable; a later observation can refine classification
without erasing the report that a review actually considered. Report IDs are never joined by
free-text equality. Candidate blocker records identify a change, Module, phase and Issue, not a
mutable task description. Reassessment can release a dependency without closing the Issue.

<a id="entity.issues.solver"></a>

The Issue solver is a fresh Spec-only decision worker, invoked only when solve is requested. It
selects intended development, bounded Spec repair, Issue-specific review or a reasoned disposition.
It does not perform intake classification or implementation. Only its intended behavior becomes
an input to ordinary development; code evidence, old logs and previous conversations are excluded
from Spec authoring. Decisions bind the selected record revision and current input identities.

<a id="entity.issues.langgraph"></a>

LangGraph compiles the declared `issue_graph` nodes and routes before execution. The host retains
attempt counts before model calls, current intended behavior and evidence in candidate bookkeeping.
No autonomous nested repair escapes the selected goal or the declared iteration limit.

## Relationships

This view shows the selected Issue's collaborators, not the inventory of the repaired Module. Each
provider runs under its own contract and context. Using a provider does not acquire its files or
allow the Issue solver to edit a Spec or implementation directly.

```mermaid
flowchart TB
    accTitle: Issue reporting and solving
    accDescr: The runtime stores classified observations, binds a solver decision and uses ordinary development, Spec repair, review and validation without automatic delivery.
    runtime["Issue runtime"]
    store["Issue store"]
    solver["Issue solver"]
    development["Development"]
    spec["Spec"]
    loop["Development Graph"]
    author["Spec Authoring"]
    review["Review"]
    validation["Validation"]
    langgraph["LangGraph"]
    runtime -->|persists observations through| store
    runtime -->|requests bounded decisions from| solver
    runtime -->|admits workers through| development
    runtime -->|resolves attribution with| spec
    runtime -->|implements intended behavior through| loop
    runtime -->|repairs necessary contracts through| author
    runtime -->|checks the selected problem through| review
    runtime -->|verifies final candidate bytes through| validation
    runtime -->|executes declared transitions with| langgraph
```

## Collaborations

<a id="entity.issues.development"></a>

[Development Module](../development/module.md) owns typed admission, phase results and candidate progress. Issue operations use its
[execution boundary](../development/interfaces.md#operation-execution-boundary), preserving its
configuration, context, permission and failure distinctions. Reporting is a separate limited host
effect, never worker filesystem write authority or permission to advance a failed stage.

<a id="entity.issues.spec"></a>

[Spec Module](../spec/module.md) resolves Module/scenario ownership and validates paired contracts. Issue attribution uses the
[current registered context](../spec/contracts.md#registry-stable-id-spec-context-queries), not a path guess.
Included definitions retain their owner; unknown ownership remains null. Historical report owners
need not remain in a later registry. Invalid current target selections stop solving.

<a id="entity.issues.dev-loop"></a>

[Development Graph](../dev-loop/module.md) supplies [ordinary development](../dev-loop/module.md#usage) for the selected goal.
The Issue runtime preserves the goal, constraints, file boundaries, required checks and independent
reviews. A blocked child yields a new bounded decision rather than automatic delivery or wider access.

<a id="entity.issues.spec-authoring"></a>

[Spec Authoring](../spec-authoring/module.md) supplies [owner-only contract changes](../spec-authoring/module.md#usage) when an
admitted decision can settle a required contract. The author receives intended behavior, not code
investigation. Missing product choices remain explicit; shared changes retain consumer checks.

<a id="entity.issues.review"></a>

[Review Module](../review/module.md) supplies [fresh read-only assessments](../review/module.md#usage). Issue-specific verification
checks the selected problem, not just unrelated passing tests. Failed, incomplete or stale reviews
cannot justify resolved disposition. Canonical report references retain their exact observations.

<a id="entity.issues.validation"></a>

[Validation Module](../validation/module.md) supplies [candidate checks](../validation/module.md#usage). The disposition is written
before final validation so ready evidence includes those bytes. A failed final validation restores
only the runtime's own unchanged disposition write, preserves other work and leaves the Issue open.
If concurrent edits prevent restoration, the host reports the conflict rather than overwriting them.

## Precise specifications

The Issues Module owns the exact obligations and interface details in [requirements](requirements.md).
These companions are part of the same complete Module specification, not separate topic owners.
