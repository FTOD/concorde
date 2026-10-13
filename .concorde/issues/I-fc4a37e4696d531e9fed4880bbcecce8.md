# I-fc4a37e4696d531e9fed4880bbcecce8

```json
{
  "schema_version": 4,
  "id": "I-fc4a37e4696d531e9fed4880bbcecce8",
  "status": "open",
  "reports": [
    {
      "id": "sha256:6ea6747a897211b35ed3789f0e2820e9a73220c30d8f34a300f750f04f36146e",
      "created_at": "2026-10-13T17:38:11.812961+00:00",
      "report": {
        "report_key": "spec-panel/module.checks/4",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Trace-write evidence can disappear despite the reporting guarantee",
        "description": "Running checks explicitly permits losing trace_failures when an exception rejects attributes, but the requirement and error contract promise all refused writes reach the caller.\n\nSuggested repair: Choose and specify a reporting mechanism for exceptions that cannot carry attributes, or explicitly revise the competing guarantees. Align the procedure, requirement, error contract and scenarios.",
        "impact": "A caller can receive an error with no evidence of refused trace writes despite the unconditional reporting contract.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/execution/checks/service.md at req.checks.trace-write-reported, line 240 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: “An exception that takes no attribute loses them.” The requirement instead says the service “SHALL report every write” refused by the operating system in the result or the call's error.\n\nThe panel's chair merged r2.3 and verified: Verified the loss exception against the requirement and Errors section. Medium because it concerns an exceptional failure path; decision-needed because the reporting guarantee and unchanged-exception guarantee need a compatible policy.",
        "owner_target_id": "module.checks",
        "evidence": [
          {
            "path": "specs/concorde/execution/checks/service.md",
            "description": "req.checks.trace-write-reported, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.checks",
        "context_id": "sha256:2ebc2edac0a9beb4426e5f87435f55444d15833ccfb9a9e96526f8611f0a0075",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
