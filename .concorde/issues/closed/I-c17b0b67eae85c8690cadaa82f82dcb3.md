# I-c17b0b67eae85c8690cadaa82f82dcb3

```json
{
  "schema_version": 4,
  "id": "I-c17b0b67eae85c8690cadaa82f82dcb3",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:c5ef44967a1e59a552d17b239365371863e9a5dedca690cbe8e303d8f941c9b4",
      "created_at": "2026-10-13T18:21:30.124551+00:00",
      "report": {
        "report_key": "spec-panel/module.dogfooding/1",
        "tier": "decision-needed",
        "severity": "high",
        "type": "bug",
        "subtype": null,
        "title": "Define how task-session observations reach Dogfooding's reporting flow",
        "description": "Dogfooding assigns all observation and reporting to the main agent without explaining how that responsibility works when task sessions start and observe the runs. It does not define the task-session-to-main-agent handoff for suspected Concorde defects.\n\nSuggested repair: Decide and specify which develop instructions task sessions receive, what they preserve and escalate, and what the main agent then classifies and reports. Include a scenario for a defect first observed by a task session.\n\nOther Modules concerned: module.main-session, module.tasks",
        "impact": "The session that actually observes task runs has no stated Dogfooding duty to recognize and forward defects or avoid project workarounds. The reporting flow can miss defects encountered during ordinary task work.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/dogfooding/module.md at What the project's main agent does, line 215 by the design criterion of the Protocol's Evaluating a Spec; the Specs read: Dogfooding says, \"Besides its work on the project, the project's main agent watches Concorde\" and requires observation of every run. Main session says, \"A run a task session starts in its worktree | that task session, no main session\" and explains that the main session hears through task-session reports.\n\nThe panel's chair merged r1.1 and verified: Verified against Dogfooding's guidance requirements and Main session's ownership table and delegation flow. High because this affects ordinary task execution; decision-needed because assigning observation and reporting duties changes the actors' promises.",
        "owner_target_id": "module.dogfooding",
        "evidence": [
          {
            "path": "specs/concorde/dogfooding/module.md",
            "description": "What the project's main agent does, cited by the design finding"
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
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task r4-e2e-dist, merged into the primary branch at ad2f6af4d5d883cae87062430b9963cbcfc099b5.",
      "evidence": [
        "merge commit ad2f6af4d5d883cae87062430b9963cbcfc099b5",
        "task r4-e2e-dist"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-23T09:03:05.172151+00:00"
    }
  ]
}
```
