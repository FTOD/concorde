# Specification Graph execution and record contracts

These are the precise implementation agreements and executable Graph specifications owned by the
[Specification Graph Module](module.md). Explanatory topics introduce their purposes; exact identities, limits
and transitions are retained here as the single detailed contract.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Graph](../module.md#terminology) | Defined in Concorde Framework. |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Evidence](../module.md#terminology) | Defined in Concorde Framework. |
| [Candidate](../module.md#terminology) | Defined in Concorde Framework. |
| [Ready](../module.md#terminology) | Defined in Concorde Framework. |
| [Blocker](../module.md#terminology) | Defined in Concorde Framework. |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Worktree](../module.md#terminology) | Defined in Concorde Framework. |
| [Spec context](../harness/context.md#terminology) | Defined in What information a worker receives. |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |

## Specification Graph {#specify-loop-specification-graph}

[Harness admission](../harness/admission.md) owns the entry. Its [common invocation envelope](../harness/admission.md#operation-execution-boundary),
[typed handoffs](../harness/admission.md#stage-handoffs) and
[gap rules](../issues/execution-reference.md#review-and-gaps-attributed-issue-blockers-and-host-history) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
`concorde-specify-loop` routes one owning Module, authors or revises its owned Spec documents
and independently reviews its complete context and affected consumers. It returns the common
stage response with `completed` after successful Spec stages, preserving artifacts, explicit
review skips and blockers. It never plans, writes code, runs code checks, requires code review,
marks ready or delivers. Repeated invocations retain accepted authoring for the same intent and
reuse only current review evidence. Necessary gaps and blocking reviews stop for Spec repair
with fresh context; there is no automatic Spec-repair edge. `specify=false` selects review of the
existing Spec, and `run_reviews=false` records only a Spec review skip where no requirement exists.

#### Composition, state and recovery {#specify-loop-composition-state-and-recovery}

The public request requires task and admits optional target/focus hints, constraints, change_id,
specify and run_reviews. Both booleans default true. New tasks use [Query and Routing](../query-routing/module.md) to select one
owner; a trusted bound caller preserves that owner. Mutating primary requests run in the common
host's isolated committed-base candidate. The recorded task, owner, focus and constraints bind resume;
incompatible intent or worktree identity is rejected before a worker starts.

[Spec Authoring](../spec-authoring/module.md) produces owned replacements; [Review Module](../review/module.md) produces independent current coverage for the
complete contract and affected consumers. No author transcript or artifacts become reviewer input.
The affected-consumer compatibility reviews that admit a candidate before it is applied are
recorded under the consumer's review intent; because the applied bytes equal the reviewed bytes,
the review stage rechecks and reuses that evidence instead of reviewing the same consumer context
twice, and reviews only the owner and any consumer whose evidence is missing or stale.
An already accepted authoring result is reused only for the same intent; unrelated standalone
review never stands for authoring. Changed relevant inputs invalidate review. Spec review requirements
are sticky: run_reviews=false records skipped only when no requirement already exists. Skipped,
failed, incomplete and successful evidence remain distinct. The graph returns completed with the
common response and ArtifactRefs; it never requires code review, runs implementation checks or marks
ready. [Development Graph](../dev-loop/module.md) may consume that completed result without repeating accepted current Spec work.

### Design {#specify-loop-design}

#### Specification Graph (`specify_graph`) {#specify-loop-specification-graph-specify-graph}

**State.** `output` (the last stage's typed response data), `artifacts` (every stage's artifact
references under a merge reducer that keeps the newest reference per artifact id), `result` (a
terminal failure envelope when a guard caught an error). The candidate record carries the accepted
authoring (task, focus, constraints, Spec digest), the review requirements and intents, the owner's
and each consumer's review evidence and the gap history. These records, the task and the complete
Spec context are Host-bound inputs/effects, not Graph channels. All channels except `artifacts`
use replacement updates. `output` holds response data during stages and the typed response wrapper
after `summarize`. In the table, `none` means no Graph-channel read, and `?` means a conditional
update. Every guarded node writes `result=None` on success or the failure envelope on error.
There is no `route` channel: `Command.goto` carries the successor outside the State update.

**Nodes.**

| Node | Executes | in | out |
| --- | --- | --- | --- |
| `initialize` | Deterministic: reads Host-bound task and candidate; authoring is needed unless `specify=false` or the same intent was already accepted without an open gap. | none | result |
| `specify` | Calls Spec Authoring through admission; affected-context candidate reviews admit replacements before application and are recorded for reuse. | none | output, artifacts, result |
| `review_spec` | Reads current Spec/review records; independently reviews missing or stale owner/consumer evidence, or records an explicit skip or current-evidence reuse. | none | output, artifacts, result |
| `summarize` | Wraps response data with every artifact reference unless result is already a failure. | output, artifacts, result | output?, result |

**Edges.** Like the development Graph, every node except `summarize` returns a LangGraph `Command`
naming its successor, within its declared destinations. `initialize` goes to `specify` when
authoring is needed and straight to `review_spec` otherwise. Accepted replacements go on to
`review_spec`; a gap, blocker or failure in `specify` stops at `summarize`. `review_spec` always
hands its outcome, reviewed, retained, skipped or stopped, to `summarize`. A guard-caught error in
any stage ends the Graph directly. The authoring branch is exactly `task.specify` (default true)
and no matching accepted authoring record without an open authoring gap. The success edge out of
`specify` requires `output.outcome == completed`; all other outcomes go to `summarize`.
`review_spec` has no repair edge, even when its review blocks.

```mermaid
flowchart TB
    %% graph: specify_graph
    accTitle: Specification Graph
    accDescr: Initialization selects authoring or goes straight to review; accepted authoring is followed by independent review; every stop routes to summarize and a guard-caught error ends the Graph.
    __start__["start"]
    initialize["initialize<br/>in: none<br/>out: result"]
    specify["specify<br/>in: none<br/>out: output, artifacts, result"]
    review_spec["review_spec<br/>in: none<br/>out: output, artifacts, result"]
    summarize["summarize<br/>in: output, artifacts, result<br/>out: output?, result"]
    __end__["end"]
    __start__ --> initialize
    initialize -->|authoring needed| specify
    initialize -->|specify=false or authoring accepted| review_spec
    initialize -->|error| __end__
    specify -->|output.outcome = completed| review_spec
    specify -->|gap, blocked or failed| summarize
    specify -->|error| __end__
    review_spec -->|reviewed, retained, skipped or stopped| summarize
    review_spec -->|error| __end__
    summarize --> __end__
```

There is no automatic Spec-repair edge. A necessary gap waits for explicit repair and fresh inputs;
blocking reviews, invalid output, failed execution, cancellation and limits preserve inspectable
progress with their distinct outcomes. Repeated unchanged blockers cannot imply completion.
The graph composes only the declared specify and review adapters. Its routing is the common
router service, not an additional callable query operation.

## Realization and reuse limits

This Module and its consumers are siblings under Concorde Framework. Its behavior is realized in
its own package `src/concorde/specify_loop/`, bound by its adapter entity together with its `operations/` declaration; this Spec boundary
creates no public Skill, Agent grant or configurable arbitrary graph. Host admission, phase
artifacts and permissions remain mandatory. A new graph requires declared composition and an
implementation of its sequencing, artifact admission, recovery and completion policies before it
can execute. [Harness admission](../harness/admission.md) realizes the common entry and invocation
host, and [Operations](../operations/execution-reference.md#graphs-dispatch-graphs) the dispatch
that reaches this provider.
