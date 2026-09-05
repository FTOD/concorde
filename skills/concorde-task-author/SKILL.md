---
name: concorde-task-author
description: "Turn an admitted plan into tasks with observable acceptance conditions."
exposure: internal
effects:
  reads: ["spec-context"]
  writes: []
  network: false
  credentials: none
---

# concorde-task-author

Use the supplied plan and complete Spec. Return nonempty tasks, each with a unique stable id, target_id, description, acceptance, and complete:false. Component tasks target the current component. Domain tasks may target its explicitly described participating components. Define observable acceptance rather than guessed implementation details. Return no document replacements or new plan.

This role runs only inside a host-bound Operation invocation. Consume the exact supplied snapshot and return the typed stage result. Do not load additional Skills or repository context.
