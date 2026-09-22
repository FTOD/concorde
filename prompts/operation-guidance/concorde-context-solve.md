---
name: concorde-context-solve
description: "Agent entry: prepare a native context-assessor for the selected Module and task."
operation: context_solve
---

# concorde-context-solve

@prompts/workflow-host/invoke-operation-opener.md ACTION="assess whether the selected Module Spec supports the task"

@prompts/workflow-host/task-request-fields.md

Action `run` prepares one complete Module context and returns `state: prepared`, `accepted: false`
and an exact `call` object. Invoke the native Pi `subagent` tool with that object unchanged. It
selects `concorde-context-assessor`, the Host-owned capsule cwd, fresh context, native output schema
and a plain staging gate. Do not invent a workflow, invoke a Python model worker, change the native
arguments or fall back to another entry after a failure.

The native structured output is only a proposal. The Concorde tool-result hook independently
checks terminal native metadata and current inputs. Read `details.concorde_context`: only
`accepted: true` means the Host accepted the assessment; its typed `result` still distinguishes
sufficiency from a business-blocked assessment. A passing gate alone is not acceptance. Report
cancelled, failed, stale or rejected runs explicitly; prepare a fresh invocation rather than replaying
an old slot. Previously committed observations and evidence are not erased by a later stop.

Known dependency gaps/conflicts stop deterministically with `state: not-run`, without a child.
`describe-policy` returns the intended prompt-level read policy without a capsule/model launch.
The assessor reads only the prepared complete Specs by policy, not by an OS confinement claim.
It authors no Specs, plan, tasks or implementation. Other capability workflows are unchanged.

The Pi host must explicitly select the supported installation with `CONCORDE_NATIVE_SUBAGENTS_ROOT`.
A missing or incompatible runtime fails closed. This is a local process selection, not a global
client setting and not authorization. The prepared file Agent is an execution projection of the
candidate-built role, not another authored Agent source or task-status store.
