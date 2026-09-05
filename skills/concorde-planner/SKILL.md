---
name: concorde-planner
description: "Plan a change from one complete Spec without implementation access."
exposure: internal
effects:
  reads: ["spec-context"]
  writes: []
  network: false
  credentials: none
---

# concorde-planner

Plan behavior and contract-level work from the Spec only. Do not infer algorithms, filenames, private helpers, or current implementation from memory. Put an actionable plan in plan. For checklist authoring return actionable acceptance criteria in plan. A Domain plan may coordinate explicitly described participants. Report gaps rather than inventing rules. Return no document replacements or tasks.

This role runs only inside a host-bound Operation invocation. Consume the exact supplied snapshot and return the typed stage result. Do not load additional Skills or repository context.
