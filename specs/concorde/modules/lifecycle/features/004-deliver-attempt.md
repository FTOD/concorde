---
id: feature.lifecycle.deliver-attempt
kind: feature
module: module.concorde.lifecycle
related_features:
  - id: feature.concorde.workflow
    relation: composed_by
  - id: feature.lifecycle.execute-and-reconcile
    relation: depends_on
interfaces:
  provided:
    - interface.concorde.deliver
  required: []
---

# Feature Design: Deliver Attempt

## Outcome and Scope

A maintainer invokes delivery once to verify a complete current feature attempt and atomically remove
only that temporal workspace, leaving architecture, design, code, tests, and reflections unchanged.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.lifecycle.deliver-skill` | Leaf prompt that invokes delivery propose then apply and reports the outcome. |
| `entity.lifecycle.delivery` | Checks eligibility, proposal digest/path safety, and applies cleanup-only removal. |
| `module.concorde.capabilities` | Exposes the deterministic delivery Tool through one portable entry point and structured envelope. |
| `module.concorde.understanding` | Revalidates the project and supplies the safe canonical attempt path before removal. |
| `entity.concorde.specification` | Supplies retained durable architecture and feature authorities. |
| `entity.lifecycle.attempt` | The selected stable-ID attempt that becomes eligible for exact removal. |

## Interfaces

### `interface.concorde.deliver` — Close a completed attempt

- **Consumer**: Maintainer accepting completed implementation work.
- **Direction**: Complete attempt to proposal/result and attempt removal.
- **Entry points**: Leaf Skill `concorde-deliver` and native Runtime Tool
  `deliver --propose/--apply`.
- **Inputs**: Selected feature ID/root, complete tasks/checklists, validation containing one
  top-level `- **T### · <trace>**` or legacy `### T###` evidence boundary per checked task with an
  exact in-block `**Outcome**: passed`, safe attempt path, and current source digest.
- **Outputs**: Proposal 9 eligibility/details, applied cleanup manifest, retained-authority digests,
  warnings/findings, and no-active-attempt state.
- **Obligations**: Parse only top-level task evidence boundaries, associate each block with its exact
  task ID, count only an in-block `**Outcome**: passed`, recheck every digest/path/eligibility
  condition at apply, and remove exactly the returned attempt.
- **Failures**: Incomplete items, missing/malformed/non-passing task evidence, validation findings,
  stale digest, unsafe/symlinked path, or filesystem failure preserve the full attempt and every authority.
- **Compatibility**: Proposal 9 and its envelope use `tool`; it contains no implementation or
  module-amendment content and creates no durable feature file.
- **Implementing entities**: `entity.lifecycle.deliver-skill`, `entity.lifecycle.delivery`,
  `module.concorde.capabilities`, `module.concorde.understanding`.
- **Example**: An eligible proposal names target `feature.example.change`, its current digest, and only `.concorde/attempts/feature.example.change` in `remove`.

## Related Features

- `feature.concorde.workflow` is the root umbrella feature this phase realizes as its closing stage.
- `feature.lifecycle.execute-and-reconcile` supplies the complete, evidenced tasks and checklists that
  make the attempt eligible for delivery.

## Usage Scenarios

1. Propose delivery and inspect complete task/checklist/evidence counts, source/attempt digest,
   remove path, findings, and retained authorities; a checked task without a parseable passing block
   is incomplete for delivery even when prose elsewhere says it passed.
2. Apply the same current proposal; stage rollback, revalidate every invariant, remove exactly the attempt, and report digests/manifest.
3. Reject incomplete, stale, unsafe, symlinked, or invalid state without changing attempt or authorities.

## Requirements

- **FR-001**: Eligibility MUST require a real selected attempt, at least one well-formed task, all tasks/checklists complete, and applicable validation passed.
- **FR-002**: Delivery Proposal 9 MUST bind target, source/attempt digest, and exactly the canonical
  attempt remove path; it MUST contain no authored narrative.
- **FR-003**: Apply MUST revalidate target/path/digest/eligibility and be atomic with rollback on filesystem failure.
- **FR-004**: Success MUST remove only the stable-ID attempt and report retained architecture/design/code/test/reflection digests and no-active-attempt state.
- **FR-005**: Eligibility MUST count task evidence only when `validation.md` contains either a
  top-level `- **T### · <trace>**` compact boundary or legacy `### T###` heading and the bounded block
  contains `**Outcome**: passed`; outcome wording in the boundary or unrelated prose MUST NOT count.

## Edge Cases

- The proposal file itself lives inside the attempt that apply will remove.
- Attempt bytes change after propose but before apply, even when durable design/code do not.
- A task boundary wraps onto another line, is nested, uses the wrong separator, or says "passed" only
  in its title; delivery reports the task's passing evidence as missing and preserves the attempt.
