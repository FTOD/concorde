---
name: concorde-configure
description: "Host service: apply the Pi worker model selection (model, thinking level, timeout and per-worker overrides); with accept_protocol, rebind the project to the installed Protocol copy."
operation: configure
---

# concorde-configure

@prompts/workflow-host/invoke-operation-opener.md ACTION=configure
@prompts/workflow-host/lifecycle-no-cognition.md

@prompts/workflow-host/task-request-fields.md
@prompts/workflow-host/init-request-and-no-flags.md

@prompts/workflow-host/target-identity-opener.md
@prompts/workflow-host/candidate-worktree.md

From the primary worktree this request is relayed into a new candidate, and the new configuration
takes effect only when that candidate is delivered. Before calling it from the primary, ask the
developer which they want: to change or test this command (run in a candidate, effective after
delivery), or simply to configure this project now. Only for the second answer set
`run_in_primary: true`, which applies the request in the primary worktree directly. Never set it
without that answer.
