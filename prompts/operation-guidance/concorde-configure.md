---
name: concorde-configure
description: "Host service: propose a change of the stored Agent models, thinking levels and time limits, then apply exactly the reviewed proposal; with accept_protocol, also rebind the project to the installed Protocol copy."
---

# concorde-configure

@prompts/workflow-host/invoke-operation-opener.md ACTION=configure
@prompts/workflow-host/lifecycle-no-cognition.md

Configuration changes in two steps; use the published request schema. First call `action:
"propose"` with the new `configuration` (a `concorde-operation-configuration` value) and, only when
the developer agreed to adopt the Protocol copy the installer placed under `.concorde/protocol/`,
`accept_protocol: true`. Propose changes nothing: it returns `status: "proposed"` with the
`proposal` and its `proposal_digest`, or `status: "unchanged"`. Show the developer the proposed
value. Then call `action: "apply"` with that exact `proposal` and `proposal_digest`. Apply refuses an
altered proposal with `invalid_proposal` and a configuration file changed since the proposal with
`stale_proposal`; propose again in both cases. Configuration is never a context grant.

From the primary worktree an `apply` request is relayed into a new candidate, and the new
configuration takes effect only when that candidate is delivered. Before calling `apply` from the
primary, ask the developer which they want: to change or test this command (run in a candidate,
effective after delivery), or simply to configure this project now. Only for the second answer set
`run_in_primary: true`, which applies the request in the primary worktree directly. Never set it
without that answer.
