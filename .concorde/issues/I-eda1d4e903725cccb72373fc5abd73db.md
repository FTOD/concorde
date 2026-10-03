# I-eda1d4e903725cccb72373fc5abd73db

```json
{
  "schema_version": 4,
  "id": "I-eda1d4e903725cccb72373fc5abd73db",
  "status": "open",
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
    }
  ],
  "dispositions": []
}
```
