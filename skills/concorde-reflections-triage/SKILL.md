---
name: concorde-reflections-triage
description: "Global reflection queue: report status, capture recorded gaps, and investigate, implement, merge or close owned reflections."
capability: reflections_triage
---

# concorde-reflections-triage

@include prompts/workflow-host/invoke-capability-opener.md ACTION="reflections triage"

@include prompts/workflow-host/stdin-invocation-open.md NAME=concorde-reflections-triage
@include prompts/workflow-host/stdin-invocation-config-input.md NAME=concorde-reflections-triage
@include prompts/workflow-host/task-request-fields.md
@include prompts/workflow-host/init-request-and-no-flags.md

@include prompts/workflow-host/target-identity-opener.md
@include prompts/workflow-host/worktree-handoff.md

Use action=record-gaps with explicit gap_ids selected from the status response
`gap_records[].id` and an empty
reflection_ids array to preserve durable missing-contract reports in the existing queue. Each gap
keeps its host-bound target owner; a Module may capture gaps of its participating components.
Repeated capture reuses the linked Reflection ID. Capture does not resolve gaps, investigate, approve
or implement a fix. For existing records, target_id names the owning target and focus_id may name its
Feature/API; a Feature/API ID is not itself a target and concerns is not ownership.
