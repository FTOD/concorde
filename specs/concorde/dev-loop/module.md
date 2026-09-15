```concorde-document
{
  "id": "document.dev-loop.module",
  "owner": "module.dev-loop",
  "main_visible": true
}
```

# Development Flow

## Purpose

Development Flow composes sibling providers to carry one intended change through Spec preparation, planning, tasks, implementation, validation and independent code review to a ready candidate. It owns that sequence, candidate lifecycle, bounded repair and stop policy, while each provider owns its own reusable contract.

## Requirements

### req.development.specify-loop-composition — Spec preparation has one reusable entry

The development Flow SHALL compose concorde-specify-loop for its Spec authoring and review stages.

### req.development.explicit-skip-sticky — Review skips cannot cancel required reviews

A `run_reviews=false` retry SHALL NOT cancel a Spec or code review already required for this change
by an earlier enabled invocation.

### req.development.repair-edge-only — Code-review repair is the only automatic edge

`review_code -> tasks` SHALL be the development Flow's only automatic revision edge.

### req.development.non-repair-stops-graph — Other outcomes stop the graph for a decision

Every other non-successful outcome SHALL stop the graph for a human decision or an explicit Spec or
code change.

## Scenarios

### scenario.development.resume-unbound — Resume a handoff before target selection

- GIVEN the host created a candidate and returned a session handoff before routing or binding an owner
- WHEN a fresh host in that worktree resumes the development loop with the recorded change identity and original task
- THEN it validates the worktree identity and preserved intent, restores omitted constraints and focus hints, and performs real router discovery and single-target selection before binding the owner
- AND a supplied target hint never substitutes for routing authority
- AND both specify modes and both review modes use this same admission, with one successful route selection before the first development stage

### scenario.development.resume-bound — Restore a bound candidate without rerouting

- GIVEN a candidate has a persisted owner, task, constraints and focus
- WHEN a fresh host resumes that change
- THEN it restores omitted target, constraints and focus from the recorded owner and resolves the current complete Module contract without rerouting
- AND explicit conflicting target, task, constraints or focus returns incompatible_handoff with the conflicting field before any Agent runs, preserving the candidate state
- AND a missing change returns missing_change, an inconsistent owner returns invalid_worktree_state, and a mismatched change or worktree identity is refused before routing or execution
- AND trusted internal routes may select separately admitted components without replacing the top-level owner, while a child target differing from its host route is rejected
- AND existing stage admission, review requirements, file permissions and current-candidate freshness checks still apply


### scenario.development.dev-loop-ready — A change reaches a ready candidate

- GIVEN a developer supplies one intended change with its task and constraints
- WHEN `concorde-dev-loop` calls `concorde-specify-loop` for Spec authoring (unless `specify=false`) and Spec review, then runs planning, tasks, implementation, deterministic checks and code review in order
- THEN every stage completes successfully and the candidate reaches status `ready` with current evidence for every affected Module
- AND the loop stops there and never itself invokes delivery

### scenario.development.dev-loop-spec-gap — Development waits for a necessary Spec repair

- GIVEN a stage discovers a necessary missing or ambiguous contract
- WHEN that stage reports a Spec gap
- THEN the loop stops with status `waiting` and preserves the candidate worktree
- AND unrelated independent work may continue, and resuming after an explicit Spec repair does not repeat already-accepted authoring for the same task, focus and constraints

### scenario.development.task-scope-repair — Recover an implementation phase boundary error

- GIVEN an existing incomplete task list whose acceptance requires later Host actions
- WHEN a normal dev-loop request binds that list's canonical digest with repair_task_scope
- THEN a fresh task author receives the admitted plan, prior tasks and typed semantic boundary feedback
- AND no implementation contents or raw test logs enter that author's context
- AND accepted replacement tasks start incomplete, preserve software acceptance and use new IDs
- AND the original list remains in history and implementation precedes validation and required code review
- AND only current successful evidence reaches ready, while a replay resumes without reauthoring
- AND stale digests, unresolved gaps and invalid replacements cannot bypass the existing gates

### scenario.development.dev-loop-repair — Bounded automatic repair after blocking code review

- GIVEN a code-owning target's code review returns blocking findings
- WHEN the loop selects its automatic revision edge from code review back to task authoring
- THEN task authoring receives the current completed tasks and the blocking `concorde-review-result@1` as `stage_inputs`, and the resulting repair tasks and their implementation are checked and code-reviewed again like any other change
- AND this repair is bounded by the target's declared `max_repair_iterations` policy

See [code-review repair is the only automatic edge](#req.development.repair-edge-only) and
[other outcomes stop the graph for a decision](#req.development.non-repair-stops-graph).

### scenario.development.dev-loop-repair-exhausted — Repeated feedback or an exhausted limit stops the loop

- GIVEN a repair attempt reproduces the same blocking-feedback fingerprint as the previous attempt, or the declared repair limit is exhausted
- WHEN the loop would otherwise select another automatic repair
- THEN it stops instead of retrying: unchanged feedback records status `waiting` and an exhausted limit records status `limit_exhausted`, and both keep the wire `outcome` `conflicting`
- AND a human directly changing the Spec or the implementation between invocations resets the recorded repair count instead of continuing a stale attempt

### scenario.development.dev-loop-coordinated — A Module coordinates its own and dependency tasks

- GIVEN a Module task has both local code tasks and separately bound submodule or used-Module tasks
- WHEN implementation runs
- THEN each component is specified, planned and implemented from its own complete Module contract and the files its own entries bind, and the coordinator waits for every writer, including its own coordination code, before checking the final candidate
- AND a repair that changes a file listed by several Modules invalidates the already-recorded evidence of every listing Module, and finalization repeats until every participant is stable


The detailed contract is [Ready-only bounded development](development.md).

## Ontology

### Entities

```concorde-entities
[
  {
    "id": "entity.dev-loop.adapter",
    "title": "Development Flow adapter",
    "kind": "shared program",
    "responsibility": "Development Flow composes sibling providers to carry one intended change through Spec preparation, planning, tasks, implementation, validation and independent code review to a ready candidate. It owns that sequence, candidate lifecycle, bounded repair and stop policy, while each provider owns its own reusable contract.",
    "files": [
      "capabilities/dev_loop.py",
      "tests/concorde/development/test_review.py",
      "tests/concorde/development/test_specify_loop.py",
      "tests/concorde/harness/test_scoped_protocol.py",
      "tests/concorde/harness/test_worktree_lifecycle.py"
    ]
  },
  {
    "id": "entity.dev-loop.development",
    "title": "Development",
    "kind": "used module",
    "target_id": "module.development",
    "responsibility": "Admit or resume the change intent, maintain candidate and component progress and record bounded repair transitions and evidence."
  },
  {
    "id": "entity.dev-loop.harness",
    "title": "Harness",
    "kind": "used module",
    "target_id": "module.harness",
    "responsibility": "Bind each routed or composed Agent invocation to a fresh complete context and its phase-specific authority."
  },
  {
    "id": "entity.dev-loop.spec",
    "title": "Spec",
    "kind": "used module",
    "target_id": "module.spec",
    "responsibility": "Resolve the owner, declared components and all old/candidate Spec consumers and shared implementation users."
  },
  {
    "id": "entity.dev-loop.query-routing",
    "title": "Query and Routing",
    "kind": "used module",
    "target_id": "module.query-routing",
    "responsibility": "Select one root owner for a new or still-unbound change while preserving recorded intent and constraints."
  },
  {
    "id": "entity.dev-loop.specify-loop",
    "title": "Specification Flow",
    "kind": "used module",
    "target_id": "module.specify-loop",
    "responsibility": "Prepare or review the selected Spec and return current accepted Spec-stage evidence before development continues."
  },
  {
    "id": "entity.dev-loop.planning",
    "title": "Planning",
    "kind": "used module",
    "target_id": "module.planning",
    "responsibility": "Assess current sufficiency, produce the accepted plan and derive new implementation tasks or admitted repair tasks."
  },
  {
    "id": "entity.dev-loop.implementation",
    "title": "Implementation",
    "kind": "used module",
    "target_id": "module.implementation",
    "responsibility": "Fulfill accepted local tasks or coordinate separately admitted participants within their own implementation grants."
  },
  {
    "id": "entity.dev-loop.validation",
    "title": "Validation",
    "kind": "used module",
    "target_id": "module.validation",
    "responsibility": "Collect deterministic Spec and configured code evidence for the affected candidate and evaluate existing readiness gates."
  },
  {
    "id": "entity.dev-loop.review",
    "title": "Review",
    "kind": "used module",
    "target_id": "module.review",
    "responsibility": "Independently review current code and return coverage, findings and gaps for the flow's bounded repair or stop decision."
  },
  {
    "id": "entity.dev-loop.candidate",
    "title": "Development candidate",
    "kind": "record",
    "responsibility": "One worktree holding intent, component progress, gaps and current evidence."
  },
  {
    "id": "entity.dev-loop.repair",
    "title": "Repair policy",
    "kind": "record",
    "responsibility": "The bounded review_code to tasks edge with feedback fingerprints and explicit stops."
  }
]
```

### Relationships

```mermaid
flowchart TB
    accTitle: Development Flow entities and dependencies
    accDescr: Development Flow records one candidate and bounded repair policy while sibling providers route intent, prepare Specs, plan tasks, implement code, validate the candidate and independently review code.
    e0["Development Flow adapter"]
    e1["Development"]
    e2["Harness"]
    e3["Spec"]
    e4["Query and Routing"]
    e5["Specification Flow"]
    e6["Planning"]
    e7["Implementation"]
    e8["Validation"]
    e9["Review"]
    e0 -->|maintains candidate progress through| e1
    e0 -->|binds fresh stage invocations through| e2
    e0 -->|resolves participants and affected consumers through| e3
    e0 -->|selects the change owner through| e4
    e0 -->|prepares and reviews Specs through| e5
    e0 -->|obtains plans and acceptance tasks from| e6
    e0 -->|implements accepted tasks through| e7
    e0 -->|validates the current candidate through| e8
    e0 -->|reviews code and receives repair feedback from| e9
    domain_candidate["Development candidate"]
    e0 -->|advances and preserves| domain_candidate
    domain_repair["Repair policy"]
    e0 -->|selects bounded transitions under| domain_repair
```

## Dependencies and composition

```concorde-dependencies
[
  {
    "target_id": "module.development",
    "responsibility": "Admit or resume the change intent, maintain candidate and component progress and record bounded repair transitions and evidence.",
    "selection_condition": "At flow entry, each accepted stage result, a stopping outcome and a current-state resume.",
    "relied_upon_promises": [
      "[Host admission](../development/interfaces.md#capability-execution-boundary); Recheck admitted intent and returned identities before accepting host state; a rejected result cannot advance the dependent step."
    ]
  },
  {
    "target_id": "module.harness",
    "responsibility": "Bind each routed or composed Agent invocation to a fresh complete context and its phase-specific authority.",
    "selection_condition": "When discovery or a composed stage launches an Agent; stage grants remain separate across repairs and reviews.",
    "relied_upon_promises": [
      "[Complete context selection](../harness/context.md#contract.context.selection); Supply only mode-admitted inputs and require a matching completion; unavailable enforcement stops execution without a wider grant."
    ]
  },
  {
    "target_id": "module.spec",
    "responsibility": "Resolve the owner, declared components and all old/candidate Spec consumers and shared implementation users.",
    "selection_condition": "When binding the root or a component and when invalidating evidence or finalizing the candidate.",
    "relied_upon_promises": [
      "[Owner and context resolution](../spec/registry.md#stable-id-spec-context-queries); Reconstruct current resolutions after input changes; unresolved ownership, missing required definitions or stale revisions block dependent use."
    ]
  },
  {
    "target_id": "module.query-routing",
    "responsibility": "Select one root owner for a new or still-unbound change while preserving recorded intent and constraints.",
    "selection_condition": "When the candidate has no persisted owner; a bound resume does not reroute.",
    "relied_upon_promises": [
      "[Explicit discovery and routing](../query-routing/query-and-routing.md); Preserve submitted task and constraints; accept only admitted selections and stop on gaps, ambiguity or discovery limits."
    ]
  },
  {
    "target_id": "module.specify-loop",
    "responsibility": "Prepare or review the selected Spec and return current accepted Spec-stage evidence before development continues.",
    "selection_condition": "At the Spec preparation entry with the admitted specify and run_reviews flags, reusing only current accepted work.",
    "relied_upon_promises": [
      "[Spec-stage completion](../specify-loop/specify-loop.md); Continue only after current successful Spec preparation; retain explicit skips and stop on blockers."
    ]
  },
  {
    "target_id": "module.planning",
    "responsibility": "Assess current sufficiency, produce the accepted plan and derive new implementation tasks or admitted repair tasks.",
    "selection_condition": "After successful Spec preparation when a current plan or tasks are missing, or when a permitted repair returns to tasks.",
    "relied_upon_promises": [
      "[Current plan admission](../planning/plan.md); Pass current intent and accepted artifacts; a gap, stale plan or rejected task list prevents implementation.",
      "[Task admission and identity history](../planning/tasks.md); provide the plan and reserved IDs, and admit feedback only for a permitted repair."
    ]
  },
  {
    "target_id": "module.implementation",
    "responsibility": "Fulfill accepted local tasks or coordinate separately admitted participants within their own implementation grants.",
    "selection_condition": "When current incomplete tasks require code work and component contract reconciliation permits it.",
    "relied_upon_promises": [
      "[Exact task fulfillment](../implementation/implementation.md); Supply exact current tasks and their grant; incomplete tasks or failed execution cannot satisfy finalization."
    ]
  },
  {
    "target_id": "module.validation",
    "responsibility": "Collect deterministic Spec and configured code evidence for the affected candidate and evaluate existing readiness gates.",
    "selection_condition": "After the relevant writers finish and during finalization before the ready decision.",
    "relied_upon_promises": [
      "[Candidate checks and readiness gates](../validation/validation.md); Require current evidence for every affected participant; failures or stale required evidence prevent ready."
    ]
  },
  {
    "target_id": "module.review",
    "responsibility": "Independently review current code and return coverage, findings and gaps for the flow's bounded repair or stop decision.",
    "selection_condition": "After implementation checks when code review is enabled or already required, including final component review.",
    "relied_upon_promises": [
      "[Independent review](../review/review.md); Supply the exact review intent and current scope; incomplete coverage, gaps or blocking findings cannot satisfy the required gate."
    ]
  }
]
```

## Realization and reuse limits

This Module and its consumers are siblings under Concorde Framework. Declared files explicitly
share the existing adapter realization with Development; no new runtime package, public Skill,
Agent grant or configurable arbitrary flow is created by this Spec boundary. Host admission,
phase artifacts and permissions remain mandatory. A new flow requires declared composition and
an implementation of its sequencing, artifact admission, recovery and completion policies before
it can execute. The existing host package still realizes common dispatch and provider internals.
