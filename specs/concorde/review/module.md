# Review

## Purpose

Review independently examines whether current specifications or code support the requested task. It returns findings and the scope actually examined, without repairing files. A successful review is evidence about those inputs and that question, not proof that every possible problem is absent.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| Review coverage | The representative questions and cases actually examined by this review. |
| Advisory finding | A concrete problem recorded for consideration that does not block the admitted task. |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Evidence](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Grant](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worktree](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Flow](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Usage

Request `concorde-review` with a task and `review_mode=spec|code`. Optional target/focus hints help
the router select one owner; an existing-change resumption supplies its bound target and change ID.
A standalone review runs in the current worktree without creating a development change. Spec mode
assesses the complete readable contract and design of the admitted contract; code mode additionally compares the
authorized implementation with that contract. Neither reviewer can repair files.

Read the typed [review result](review-result.md), including representative coverage, findings,
gaps and exact revision. No findings is a bounded conclusion, not universal proof; skipped,
not-run and incomplete are distinct from success. Missing necessary contracts pause dependent work,
while independent defects can remain advisory. Explicit standalone review is fresh; a composing
Flow can reuse only current evidence for the same intent. Failure, cancellation and invalid output
cannot masquerade as clean review. See [review](review.md) for selection, scope and outcome rules.

## Design

<a id="entity.review.adapter"></a><a id="entity.review.review-input"></a><a id="entity.review.result"></a>

The host constructs a digest-bound review input from current admitted sources and scoped changes,
then launches a fresh Spec or code reviewer under a read-only grant. Result admission checks
identity, coverage, locations and gap/finding consistency before retaining a typed report. Peer
reviews run separately and aggregate only results, not provider code or private conversation.

These mechanisms support [review scope and freshness](review.md), including exact-intent reuse by
composing flows and fresh standalone review. A report remains evidence about one task and revision;
its wire representation does not authorize a repair or override lifecycle gates.

## Relationships

This view covers selection, review admission and the resulting evidence, not a repair workflow.
[Query and Routing](../query-routing/module.md) selects the owner of an unbound standalone request; [Spec Module](../spec/module.md) supplies current scope
and finding ownership; [Harness Module](../harness/module.md) isolates the reviewer with read-only access. [Development Module](../development/module.md) accepts
and stores the Review result against the frozen Review input. None of these dependency edges gives
the reviewer write authority, and the result does not itself advance delivery or repair files.

```mermaid
flowchart TB
    accTitle: Review entities and dependencies
    accDescr: Review routes unbound tasks, resolves current review scope and finding owners, binds independent read-only reviewers and publishes coverage and findings through the host.
    e0["Review adapter"]
    e1["Development"]
    e2["Harness"]
    e3["Spec"]
    e4["Query and Routing"]
    e0 -->|admits review intent and saves reports through| e1
    e0 -->|binds independent reviewers with read access through| e2
    e0 -->|resolves review scope and finding owners through| e3
    e0 -->|routes standalone review through| e4
    domain_review_input["Review input"]
    e0 -->|freezes the reviewed scope in| domain_review_input
    domain_result["Review result"]
    e0 -->|publishes coverage and findings as| domain_result
```

### Development

<a id="entity.review.development"></a><a id="agreement.document.review.module.1"></a>

Admit review intent and current revision, validate returned review identities and persist reports without changing reviewed project files.

This collaboration applies when standalone or composed review enters and when its report is accepted or refused.

- [Host admission](../development/interfaces.md#capability-execution-boundary); Recheck admitted intent and returned identities before accepting host state; a rejected result cannot advance the dependent step.

### Harness

<a id="entity.review.harness"></a><a id="agreement.document.review.module.2"></a>

Run independent fresh Spec or code reviewers with read-only grants and no author conversation, network or credentials.

This collaboration applies before each selected review mode and target is invoked, including recorded component reviews.

- [Complete context selection](../harness/contracts.md#contract.context.selection); Supply only mode-admitted inputs and require a matching completion; unavailable enforcement stops execution without a wider grant.

### Spec

<a id="entity.review.spec"></a><a id="agreement.document.review.module.3"></a>

Resolve complete review contracts, sole finding owners and the current implementation enumeration permitted in code mode.

This collaboration applies when freezing a review scope, attributing findings or rechecking its Spec and code revision.

- [Owner and context resolution](../spec/contracts.md#registry-stable-id-spec-context-queries); Reconstruct current resolutions after input changes; unresolved ownership, missing required definitions or stale revisions block dependent use.

### Query and Routing

<a id="entity.review.query-routing"></a><a id="agreement.document.review.module.4"></a>

Select one owning Module for a new standalone review while preserving its original task, focus and constraints.

This collaboration applies when a new standalone review has neither a trusted bound target nor a bound current-change resumption.

- [Explicit discovery and routing](../query-routing/query-and-routing.md); Preserve submitted task and constraints; accept only admitted selections and stop on gaps, ambiguity or discovery limits.

## Precise specifications

The Review Module owns the exact obligations and interface details in [requirements](requirements.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
