# I-da204eb8694b5995bdc8a8fecccf0c86

```json
{
  "schema_version": 4,
  "id": "I-da204eb8694b5995bdc8a8fecccf0c86",
  "status": "open",
  "reports": [
    {
      "id": "sha256:9ccc2ab0725606fca3b9d7c4653412ee30a2e53cb7cd5e156c1d53fe688a3ac0",
      "created_at": "2026-10-13T19:35:00.327151+00:00",
      "report": {
        "report_key": "code-review/module.spec-review/2",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Earlier-Issue checks skip reviewer and architect references",
        "description": "Nonblank earlier references are checked only in the final chair report. References supplied by reviewers or architects that the chair does not carry into that report are never checked against the offered Issues.\n\nSuggested repair: Validate nonblank earlier references for each worker against that worker's offered Issues, retain the original claims separately as required, and carry invalid-reference diagnostics into the result. Continue settling duplicate matches and resolutions at the final chair-report stage. Test an unknown reference that the chair rejects or omits.",
        "impact": "An unoffered Issue name in a reviewer finding can reach the chair unchecked and disappear without an ignored entry when the chair rejects that finding or removes the name. The result therefore omits the promised account of invalid earlier-Issue references.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 (module review) judged src/concorde/method/spec_review/review.py:438-457, src/concorde/method/spec_review/review.py:513-526, src/concorde/method/spec_review/panel.py:401-414 against req.spec-review.earlier-checked and reported a violation: The requirement says the Operation checks 'every earlier of a worker’s finding' that is nonblank against the Issues offered. _normalize only invokes without_blank_earlier and copies the remaining value. The settlement at review.py:522 checks review.findings, which contains the chair's merged report, not every reviewer's and architect's findings.",
        "owner_target_id": "module.spec-review",
        "evidence": [
          {
            "path": "src/concorde/method/spec_review/review.py",
            "description": "lines 438-457, shown by the violation finding"
          },
          {
            "path": "src/concorde/method/spec_review/review.py",
            "description": "lines 513-526, shown by the violation finding"
          },
          {
            "path": "src/concorde/method/spec_review/panel.py",
            "description": "lines 401-414, shown by the violation finding"
          },
          {
            "path": "specs/concorde/method/spec-review/requirements.md",
            "description": "defines req.spec-review.earlier-checked, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.spec-review",
        "context_id": "sha256:619f54ad2b28f562af88d1174357bde9888c2490aaed32f2a5eb79a677d96bf7",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
