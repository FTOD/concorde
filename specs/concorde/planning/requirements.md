# Planning requirements

These precise specifications belong directly to the [Planning Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Planning

### req.planning.admitted-contract — Assess sufficiency before saving a plan

Planning SHALL persist a plan only after sufficient assessment of the selected current Module contract.

## Context assessment

### req.planning.assessment-context — Assess only the selected contract

Planning SHALL assess task sufficiency only from the selected Module's complete admitted Spec context.

### req.planning.assessment-gap — Attribute necessary contract gaps

Planning SHALL report a necessary missing contract with its question, blocked step, needed contract and host-bound target/context provenance.

## Planning capability

### req.planning.plan-rejection-preserves — Rejected plans preserve accepted state

Planning SHALL leave the previously accepted plan unchanged when a returned plan is empty, invalid or bound to stale inputs.

## Task authoring capability

### req.planning.tasks-require-plan — Tasks require an accepted current plan

Planning SHALL reject task authoring without an accepted current plan.

### req.planning.tasks-admission — Accept only valid new task lists

Planning SHALL accept only nonempty, internally unique, initially incomplete task lists whose IDs are disjoint from the admitted reserved IDs.

### req.planning.task-collision-preserves — Identity collisions preserve task history

Planning SHALL preserve the prior task list and retained history when it rejects colliding task IDs.
