```concorde-document
{
  "id": "document.specify-loop.specify-loop",
  "owner": "module.specify-loop",
  "main_visible": true
}
```

# Specification Flow

The [common invocation envelope](../development/interfaces.md#capability-execution-boundary),
[typed handoffs](../development/interfaces.md#stage-handoffs) and
[gap rules](../development/review-and-gaps.md) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
`concorde-specify-loop` routes one owning Module, authors or revises its owned Spec documents
and independently reviews its complete context and affected consumers. It returns the common
stage response with `completed` after successful Spec stages, preserving artifacts, explicit
review skips and blockers. It never plans, writes code, runs code checks, requires code review,
marks ready or delivers. Repeated invocations retain accepted authoring for the same intent and
reuse only current review evidence. Necessary gaps and blocking reviews stop for Spec repair
with fresh context; there is no automatic Spec-repair edge. `specify=false` selects review of the
existing Spec, and `run_reviews=false` records only a Spec review skip where no requirement exists.


## Composition, state and recovery

The public request requires task and admits optional target/focus hints, constraints, change_id,
specify and run_reviews. Both booleans default true. New tasks use Query and Routing to select one
owner; a trusted bound caller preserves that owner. Mutating primary requests first use the common
host's isolated committed-base handoff. The recorded task, owner, focus and constraints bind resume;
incompatible intent or worktree identity is rejected before a worker starts.

Spec Authoring produces owned replacements; Review produces independent current coverage for the
complete contract and affected consumers. No author transcript or artifacts become reviewer input.
The affected-consumer compatibility reviews that admit a candidate before it is applied are
recorded under the consumer's review intent; because the applied bytes equal the reviewed bytes,
the review stage rechecks and reuses that evidence instead of reviewing the same consumer context
twice, and reviews only the owner and any consumer whose evidence is missing or stale.
An already accepted authoring result is reused only for the same intent; unrelated standalone
review never stands for authoring. Changed relevant inputs invalidate review. Spec review requirements
are sticky: run_reviews=false records skipped only when no requirement already exists. Skipped,
failed, incomplete and successful evidence remain distinct. The flow returns completed with the
common response and ArtifactRefs; it never requires code review, runs implementation checks or marks
ready. Dev-loop may consume that completed result without repeating accepted current Spec work.

```mermaid
flowchart TB
    accTitle: Independent specification preparation
    accDescr: Routing binds one owner. Accepted authoring or an explicit skip selects independent review or an admissible recorded skip. Every blocker stops with preserved progress; completion ends before planning.
    route["Bind owner and intent"]
    author["Spec Authoring"]
    decision["Select required review or admissible skip"]
    review["Independent Spec Review"]
    skip["Record admissible Spec review skip"]
    complete["Completed Spec preparation"]
    stop["Stop with preserved progress"]
    route -->|authoring needed| author
    route -->|authoring accepted or explicitly skipped| decision
    author -->|accepted replacements| decision
    decision -->|review enabled or already required| review
    decision -->|review disabled and not required| skip
    skip -->|skip recorded| complete
    review -->|current successful coverage| complete
    route -->|admission fails| stop
    author -->|gap or invalid output| stop
    review -->|gap, blocking finding, incomplete or failed| stop
```

There is no automatic Spec-repair edge. A necessary gap waits for explicit repair and fresh inputs;
blocking reviews, invalid output, failed execution, cancellation and limits preserve inspectable
progress with their distinct outcomes. Repeated unchanged blockers cannot imply completion.
The flow composes only the declared specify and review adapters. Its routing is the common
coordinator service, not an additional callable query capability.
