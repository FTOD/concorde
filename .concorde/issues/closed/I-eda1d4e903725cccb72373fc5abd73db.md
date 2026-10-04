# I-eda1d4e903725cccb72373fc5abd73db

```json
{
  "schema_version": 4,
  "id": "I-eda1d4e903725cccb72373fc5abd73db",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:5e72e185763198857adc37a6674f37c514350405e0679e3da4fb82af7583d90e",
      "created_at": "2026-10-03T04:36:52.613587+00:00",
      "report": {
        "report_key": "module.workflows/8",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Malformed workflow records escape structured refusal handling",
        "description": "Valid JSON with an invalid workflow-record shape bypasses record_unreadable handling. For example, content.data=null raises AttributeError, and content.data={} raises KeyError.\n\nSuggested repair: Validate the loaded workflow content and translate structural decoding failures into WorkflowError('record_unreadable', ...), covering the entire load operation. Test null content, missing workflow, and malformed step entries.",
        "impact": "A structurally unreadable record can crash the step command rather than producing step_rejected over record_unreadable; the report returns generic report_failed instead of the specified record refusal.",
        "basis": "code_review run r-20261003T043108-code_review-b638d3d3 (module review) judged src/concorde/workflows/store.py:195-232, src/concorde/workflows/step.py:518-523 against specs/concorde/workflows/contracts.md#errors and reported a defect: store.load catches errors only while decoding JSON and selecting node['content']['data']; data.get, step expansion, report path access, and data['workflow'] are outside that try block.",
        "owner_target_id": "module.workflows",
        "evidence": [
          {
            "path": "src/concorde/workflows/store.py",
            "description": "lines 195-232, shown by the defect finding"
          },
          {
            "path": "src/concorde/workflows/step.py",
            "description": "lines 518-523, shown by the defect finding"
          },
          {
            "path": "specs/concorde/workflows/contracts.md",
            "description": "defines specs/concorde/workflows/contracts.md#errors, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T043108-code_review-b638d3d3",
        "agent": "operation",
        "operation": "code_review",
        "phase": "report",
        "target_id": "module.workflows",
        "context_id": "sha256:8c074fe64a30f2a8a45df5e481233bf52e46dd1b7524c2170687e30be0264870",
        "change_id": "parts-review",
        "head": "43871f64ab7162b4b32fd566e2f81ec15aba06d2"
      }
    },
    {
      "id": "sha256:e6f7da6a90a8d37972fc65eb8f0147cbc2401a1e65383f6a918816956884aadb",
      "created_at": "2026-10-03T05:03:16.374127+00:00",
      "report": {
        "issue_id": "I-eda1d4e903725cccb72373fc5abd73db",
        "report_key": "verify/workflows/8",
        "tier": "obvious-fix",
        "severity": "low",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "A wrongly shaped workflow record escapes record_unreadable",
        "description": "store.load (store.py:195-231) maps only JSON decoding and node['content']['data'] lookup to record_unreadable; a record whose data is null or lacks workflow, steps entries or report paths raises AttributeError/KeyError outside that try. The step command then ends in a traceback (run_step catches only Workflows errors) and the report answers report_failed instead of record_unreadable.",
        "impact": "Only a trace.json that is valid JSON with a wrong shape triggers it; Concorde alone writes that file, so this needs outside corruption. The error is still visible, just not the specified one.",
        "basis": "specs/concorde/workflows/contracts.md error table: record_unreadable when the workflow record cannot be read. Same code on main (pre-existing).",
        "owner_target_id": "module.workflows",
        "evidence": [
          {
            "path": "src/concorde/workflows/store.py",
            "description": "load()"
          },
          {
            "path": "specs/concorde/workflows/contracts.md",
            "description": "errors section"
          }
        ],
        "expected_revision": "sha256:ba042be770422dbefdd9180490cdef9f341966940ae4df0250fe5984748fe239"
      },
      "source": {
        "invocation_id": "cli-18dd387e-01cb-48ce-aaa0-1175f2d517fd",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.workflows",
        "context_id": "sha256:1d5cfc2a2a7ba74b163c0a7da2044601cb98d3bb39fa931e4f515946b2ee70f4",
        "change_id": "parts-review",
        "head": "43871f64ab7162b4b32fd566e2f81ec15aba06d2"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-open-workflows, merged into the primary branch at 3e0e6838daca08100a8fe4cc072945ee01bce7be.",
      "evidence": [
        "merge commit 3e0e6838daca08100a8fe4cc072945ee01bce7be",
        "task fix-open-workflows"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-04T02:44:00.331915+00:00"
    }
  ]
}
```
