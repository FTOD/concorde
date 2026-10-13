# I-a95e1ef8eec257b8a1fddb3fbafcd4ff

```json
{
  "schema_version": 4,
  "id": "I-a95e1ef8eec257b8a1fddb3fbafcd4ff",
  "status": "open",
  "reports": [
    {
      "id": "sha256:490a96fb755003c6b92bad09bd69f899604bf7e70663c11530d5a926b778bde4",
      "created_at": "2026-10-13T18:08:45.628124+00:00",
      "report": {
        "report_key": "spec-panel/module.distribution/15",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "The installer target prerequisite is ambiguous",
        "description": "The preflight prose suggests an existing directory can fail a project qualification, but the refusal table specifies only directory existence. The Specs do not reconcile those predicates.\n\nSuggested repair: Decide and state the installation target predicate explicitly, including whether a non-Git directory qualifies. Align the preflight and refusal table and add a corresponding acceptance or refusal scenario; clarify linked-worktree treatment if it differs.",
        "impact": "A task cannot confidently decide whether an existing non-Git directory is an accepted installation target or should be refused before writes.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/distribution/module.md at Installing into a project, line 635 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: Step 1 refuses \"A directory is not a project (`invalid_project`).\" The refusal table defines invalid_project as \"the project is not a directory\". The installation scenario starts with a Git project, while the MCP session contract separately describes behavior outside a Git repository.\n\nThe panel's chair merged r2.4 and verified: Verified the preflight statement, refusal table and Git-specific example. The MCP no-project behavior does not itself establish an installer prerequisite. Medium severity for target-selection edge cases. Decision-needed because choosing the accepted target predicate changes installer promises.",
        "owner_target_id": "module.distribution",
        "evidence": [
          {
            "path": "specs/concorde/distribution/module.md",
            "description": "Installing into a project, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.distribution",
        "context_id": "sha256:b3e4b9a1d6a5c7edf7f6b97c306c506e0236cbfd38f99b33935a579437ac47ba",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
