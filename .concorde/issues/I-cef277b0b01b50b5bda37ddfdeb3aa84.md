# I-cef277b0b01b50b5bda37ddfdeb3aa84

```json
{
  "schema_version": 4,
  "id": "I-cef277b0b01b50b5bda37ddfdeb3aa84",
  "status": "open",
  "reports": [
    {
      "id": "sha256:3029c217a71e39cd455a7f182ca1fe1ee4902d8605cba3c5cfd5df1b5d483d80",
      "created_at": "2026-10-13T18:24:04.076518+00:00",
      "report": {
        "report_key": "code-review/module.e2e/4",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Owners verdicts include wakes beyond the promised observation deadline",
        "description": "The owners observation deadline is measured from detection of the result rather than its write time, and polling can extend it further. The verdict includes events through the delayed wall-clock end instead of the promised cutoff.\n\nSuggested repair: Derive an absolute observation deadline from the result's write time, cap polling sleeps and grace at that deadline, and pass the bounded cutoff to judge even if execution resumes later. Add a deterministic test with a delayed result read and notifications just after the allowed cutoff.",
        "impact": "A wake arriving after the specified window can count toward the verdict: a late owner wake can turn a required failure into a pass, or a late non-owner wake can create an unwarranted failure.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 (module review) judged scripts/e2e/owners.py:203-211, scripts/e2e/owners.py:367-405 against req.e2e.owners-deadline and reported a violation: phase polls until it reads result.json, then starts a fresh wake interval with observe(..., wake), sleeps the full grace interval and uses time.time() as the judged end. observe checks the condition before its deadline and sleeps in fixed 0.5-second increments. The requirement bounds the phase by wake plus grace seconds after the run wrote its result.",
        "owner_target_id": "module.e2e",
        "evidence": [
          {
            "path": "scripts/e2e/owners.py",
            "description": "lines 203-211, shown by the violation finding"
          },
          {
            "path": "scripts/e2e/owners.py",
            "description": "lines 367-405, shown by the violation finding"
          },
          {
            "path": "specs/concorde/e2e/requirements.md",
            "description": "defines req.e2e.owners-deadline, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.e2e",
        "context_id": "sha256:982f7551fa9f6d20906174bc1a98eeaa5c0c1ff11a4ab7be751f9a985dff0432",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
