---
id: feature.concorde.workflow.accept-milestone
kind: feature
module: module.concorde
related_features:
  - feature.concorde.workflow
  - feature.concorde.workflow.execute-and-reconcile
interfaces:
  provided:
    - interface.concorde.deliver
  required:
    - contract.concorde.workflow
evidence_status: partial
---

# Feature Design: Deliver Milestone

## Outcome and Scope

A maintainer invokes delivery once to verify a complete current feature attempt and atomically remove
only that temporal workspace, leaving architecture, design, code, tests, and reflections unchanged.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.concorde.cli` | Exposes delivery propose/apply through one structured operation family. |
| `entity.concorde.runtime` | Checks eligibility, proposal digest/path safety, project validation, rollback, and cleanup. |
| `entity.concorde.specification` | Supplies retained durable architecture and feature authorities. |
| `entity.concorde.control-state` | Supplies the selected stable-ID attempt and retained reflection log. |

## Interfaces

### `interface.concorde.deliver` — Close a completed attempt

- **Consumer**: Maintainer accepting completed implementation work.
- **Direction**: Complete attempt to proposal/result and attempt removal.
- **Entry points**: Compatibility command `speckit.concorde.deliver` and native runtime `deliver --propose/--apply`.
- **Inputs**: Selected feature ID/root, complete tasks/checklists/validation, safe attempt path, and current source digest.
- **Outputs**: Proposal 8 eligibility/details, applied cleanup manifest, retained-authority digests, warnings/findings, and no-active-attempt state.
- **Obligations**: Recheck every digest/path/eligibility condition at apply and remove exactly the returned attempt.
- **Failures**: Incomplete items, validation findings, stale digest, unsafe/symlinked path, or filesystem failure preserve the full attempt and every authority.
- **Compatibility**: Proposal 8 contains no implementation or module-amendment content and creates no durable feature file.
- **Implementing entities**: `entity.concorde.cli`, `entity.concorde.runtime`.
- **Example**: An eligible proposal names target `feature.example.change`, its current digest, and only `.concorde/attempts/feature.example.change` in `remove`.

## Usage Scenarios

1. Propose delivery and inspect complete task/checklist counts, source/attempt digest, remove path, findings, and retained authorities.
2. Apply the same current proposal; stage rollback, revalidate every invariant, remove exactly the attempt, and report digests/manifest.
3. Reject incomplete, stale, unsafe, symlinked, or invalid state without changing attempt or authorities.

## Requirements

- **FR-001**: Eligibility MUST require a real selected attempt, at least one well-formed task, all tasks/checklists complete, and applicable validation passed.
- **FR-002**: Proposal 8 MUST bind target, source/attempt digest, and exactly the canonical attempt remove path; it MUST contain no authored narrative.
- **FR-003**: Apply MUST revalidate target/path/digest/eligibility and be atomic with rollback on filesystem failure.
- **FR-004**: Success MUST remove only the stable-ID attempt and report retained architecture/design/code/test/reflection digests and no-active-attempt state.

## Edge Cases

- The proposal file itself lives inside the attempt that apply will remove.
- Attempt bytes change after propose but before apply, even when durable design/code do not.
