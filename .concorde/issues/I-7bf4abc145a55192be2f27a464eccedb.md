# I-7bf4abc145a55192be2f27a464eccedb

```json
{
  "schema_version": 4,
  "id": "I-7bf4abc145a55192be2f27a464eccedb",
  "status": "open",
  "reports": [
    {
      "id": "sha256:0789996336199e4191982973b0477b08f5c0e58edf21c34456b4de182f403e21",
      "created_at": "2026-10-13T19:54:14.890623+00:00",
      "report": {
        "report_key": "spec-panel/module.swe-bench-cases/5",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "XPASS is attributed to a SWE-bench parser that does not report it",
        "description": "The Spec attributes XPASS to SWE-bench's parser even though the selected parser does not report it. The verdict contract includes XPASS without explaining this departure from the reference the Module says it copies.\n\nSuggested repair: Decide whether XPASS is an intentional extension. If retained, explicitly describe it as such and define its participation in truncated matching and its effect on equivalence to SWE-bench. Otherwise align the status inventory and verdict contract with the selected reference.",
        "impact": "A reader cannot reconcile the claimed SWE-bench equivalence with the additional status. Including XPASS identities can affect truncated-identity matching as well as diagnostics.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/e2e/cases/module.md at Grading a case, line 186 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: “The statuses are the ones SWE-bench's pytest parser reads: `PASSED`, `FAILED`, `ERROR`, `SKIPPED`, `XFAIL` and `XPASS`.” The selected external harness's constants/__init__.py defines TestStatus with FAILED, PASSED, SKIPPED, ERROR and XFAIL only; log_parsers/python.py's parse_log_pytest accepts lines beginning with those values.\n\nThe panel's chair merged r1.3 and verified: Verified the quotation and the selected external harness, which the Spec explicitly makes authoritative for statuses and grading. Medium severity for XPASS cases; decision-needed because choosing whether to retain an extension or conform to the reference changes the stated grading promise.",
        "owner_target_id": "module.swe-bench-cases",
        "evidence": [
          {
            "path": "specs/concorde/e2e/cases/module.md",
            "description": "Grading a case, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.swe-bench-cases",
        "context_id": "sha256:1e7f1d3e59fd595ed3c0d5c2c566f35aa5a411701b7ea73f65dd07e93f2ff3da",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
