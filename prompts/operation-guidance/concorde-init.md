---
name: concorde-init
description: "Host service: propose and apply explicit project initialization with a pinned Protocol and an honest registry stub."
operation: init
---

# concorde-init

@prompts/workflow-host/invoke-operation-opener.md ACTION=init
@prompts/workflow-host/lifecycle-no-cognition.md

@prompts/workflow-host/task-request-fields.md
@prompts/workflow-host/init-request-and-no-flags.md

@prompts/workflow-host/target-identity-opener.md
@prompts/workflow-host/candidate-worktree.md

From the primary worktree an `apply` request is relayed into a new candidate, and the new Spec
takes effect only when that candidate is delivered. Before calling `apply` from the primary, ask the
developer which they want: to change or test this command (run in a candidate, effective after
delivery), or simply to initialize this project now. Only for the second answer set
`run_in_primary: true`, which applies the request in the primary worktree directly. Never set it
without that answer.
