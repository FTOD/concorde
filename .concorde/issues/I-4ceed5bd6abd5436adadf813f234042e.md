# I-4ceed5bd6abd5436adadf813f234042e

```json
{
  "schema_version": 4,
  "id": "I-4ceed5bd6abd5436adadf813f234042e",
  "status": "open",
  "reports": [
    {
      "id": "sha256:76dd801b5ce21c60fd5e88a9d3cc75310c26ac429fd068ed2498d6c23a094a38",
      "created_at": "2026-10-13T18:21:31.341027+00:00",
      "report": {
        "report_key": "spec-panel/module.dogfooding/4",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Limit boundary classification to refusals caused by a boundary",
        "description": "The classification and evidence requirements omit the condition that the refusal is caused by a boundary. Their scope exceeds the cases they require the agent to use.\n\nSuggested repair: Put the boundary-refusal condition inside both requirement statements and make the adjacent routing rule explicitly refer to those cases. Align the guidance scenario.",
        "impact": "Ordinary invalid-input and environment tool refusals would require boundary evidence and classification even though none of the four cases applies.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/dogfooding/requirements.md at req.dogfooding.boundary-classified, line 61 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: \"The develop guidance SHALL require the main agent to place every refused read, write or tool in one of the four boundary cases.\" The adjacent evidence requirement also says \"every refused read, write or tool\", whereas the entry introduces the cases with \"When a boundary blocks work\".\n\nThe panel's chair merged r2.2 and verified: Verified the universal requirement statements against the entry's boundary-specific introduction and separate environment handling. Medium because the conflict appears on refusal paths; obvious-fix because restoring the already stated boundary condition preserves the intended promise.",
        "owner_target_id": "module.dogfooding",
        "evidence": [
          {
            "path": "specs/concorde/dogfooding/requirements.md",
            "description": "req.dogfooding.boundary-classified, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.dogfooding",
        "context_id": "sha256:8f5ee9701ec7233fe2257825efd4007f478812f4816657c310d2c1d21c4410f6",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    },
    {
      "id": "sha256:14a05336e8adadb4d6e21a60edbf421bbe9abf94b43c4c82fb355ea78a785d15",
      "created_at": "2026-10-29T07:05:58.421731+00:00",
      "report": {
        "report_key": "spec-panel/module.dogfooding/8",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Limit boundary classification to defects involving boundary refusals",
        "description": "The earlier overbroad refusal requirements remain. The task-session handoff additionally requires placing every escalated defect into a boundary case, even when it is a crash or wrong result unrelated to boundaries.\n\nSuggested repair: Place the boundary-caused-refusal condition inside both classification and evidence requirement statements. Apply that condition to the entry and both guidance scenarios, including the task-session handoff. Use the general project-versus-Concorde distinction for other defects.",
        "impact": "The main agent is instructed to classify non-boundary defects using cases that cannot describe them before it may report them.",
        "basis": "project_review run r-20261029T060905-project_review-fa4731e2 judged specs/concorde/dogfooding/module.md at What the project's main agent does by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: “The main agent places the escalated defect in its boundary case, writes the defect report”. The task-session scenario similarly says “once it has placed the defect in its boundary case”. req.dogfooding.boundary-classified still requires classifying “every refused read, write or tool”.\n\nThe panel's chair merged r2.3 and verified: Verified the existing requirement defect and the additional unconditional task-session passages. This expands the earlier Issue rather than creating a new one. Medium and obvious-fix remain appropriate because the existing boundary-case definition supplies the unique scope restriction.",
        "owner_target_id": "module.dogfooding",
        "evidence": [
          {
            "path": "specs/concorde/dogfooding/module.md",
            "description": "What the project's main agent does, cited by the obligations finding"
          }
        ],
        "issue_id": "I-4ceed5bd6abd5436adadf813f234042e",
        "expected_revision": "sha256:086761bd4b7f99eff1528643368e0859b232fa6a30bc32b70dfd0fefdf14559d"
      },
      "source": {
        "invocation_id": "r-20261029T060905-project_review-fa4731e2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.dogfooding",
        "context_id": "sha256:7e1a1a2056e230c253f1e535e5cd8205860412127141bc48e9d2f5d10c42030c",
        "change_id": null,
        "head": "8a5ed4245ef73b623587ddac67b1b88c13c178b2",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
