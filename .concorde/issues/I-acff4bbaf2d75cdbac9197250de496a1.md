# I-acff4bbaf2d75cdbac9197250de496a1

```json
{
  "schema_version": 4,
  "id": "I-acff4bbaf2d75cdbac9197250de496a1",
  "status": "open",
  "reports": [
    {
      "id": "sha256:a870fa8bda5c0c4cc0b7c67572b7f44fd9e00d30580c7059d8a12a2a75aa169f",
      "created_at": "2026-10-08T07:28:38.556624+00:00",
      "report": {
        "report_key": "spec-panel/module.coordination/1",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "bug",
        "subtype": null,
        "title": "The isolation explanation overstates the merge audit's protection",
        "description": "The isolation explanation promises refusal for unaccounted changes anywhere outside the task worktree. Tasks explicitly limits both the locations and evidence it audits, and some observed changes only produce warnings.\n\nSuggested repair: Qualify the guarantee to the audit Tasks specifies: refusal for remaining uncommitted or untracked changes in the primary worktree after applicable recovery and changes in surviving worktrees of ended tasks; warnings for dirty worktrees of other delivered tasks. State that working tasks, unrelated worktrees and commits are outside this audit's judgment, and link to Tasks' canonical audit explanation.\n\nOther Modules concerned: module.tasks, module.task-session",
        "impact": "A reader assessing task isolation could rely on a successful merge as assurance that the unrestricted task-session shell made no unaccounted outside changes, although the specified audit cannot establish that.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/coordination/module.md at why-it-is-built-this-way, line 313 by the design criterion of the Protocol's Evaluating a Spec; the Specs read: Coordination states: \"When anything outside the task worktree changed that nobody accounts for, the merge refuses the task.\" In specs/concorde/coordination/tasks/module.md#nothing-changed-outside-the-task, a changed delivered task's worktree instead causes a warning: \"The merge does not refuse\". That passage also states that a working task's worktree \"is not judged at all\", excludes worktrees belonging to no task, and says: \"The audit judges working trees and not commits.\"\n\nThe panel's chair merged r1.1, r2.2, r3.1 and verified: Verified the parent claim against Tasks' complete audit explanation, including refusal, warning and exclusion cases. Merged all three reports of this same overstatement. High severity reflects a misleading guarantee in the main task-isolation design; the child provides a careful reader a way out. Preferred-fix applies because aligning the parent's explanation with the canonical audit limits repairs the contradiction without changing the audit's promises.",
        "owner_target_id": "module.coordination",
        "evidence": [
          {
            "path": "specs/concorde/coordination/module.md",
            "description": "why-it-is-built-this-way, cited by the design finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.coordination",
        "context_id": "sha256:5b85c72ad95db1b6001eef8dba8031ce8036b33b1d66614c541adb6eaf157e3f",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
