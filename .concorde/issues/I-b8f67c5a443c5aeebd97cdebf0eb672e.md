# I-b8f67c5a443c5aeebd97cdebf0eb672e

```json
{
  "schema_version": 4,
  "id": "I-b8f67c5a443c5aeebd97cdebf0eb672e",
  "status": "open",
  "reports": [
    {
      "id": "sha256:e119fbbdea1c3be8946c9bc7c1d7e56620ffb9c04fc055cd07f093ad1433b0eb",
      "created_at": "2026-10-13T18:55:41.088139+00:00",
      "report": {
        "report_key": "spec-panel/module.issues/7",
        "tier": "preferred-fix",
        "severity": "low",
        "type": "bug",
        "subtype": null,
        "title": "Issue report has inconsistent scope around provenance",
        "description": "Issue report denotes an observation including its reporter in the glossary but excludes reporter provenance in the canonical payload contract.\n\nSuggested repair: Define the Issue report as the observation stored with its caller's provenance, and consistently call the enclosing {id, created_at, report, source} object a report entry. Preserve the payload's exclusion of provenance.",
        "impact": "Readers must distinguish two scopes of the same term when constructing reports and interpreting stored reports and receipt identities.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/issues/interface.md at contract.issues.report, line 17 by the terminology criterion of the Protocol's Evaluating a Spec; the Specs read: The supplied Issue report definition includes “who reported it”. The report contract states “Provenance is never part of a report.” The record representation says “Each entry of `reports` is `{id, created_at, report, source}`” and identifies source as provenance.\n\nThe panel's chair merged r1.5 and verified: Verified the glossary definition supplied in the brief against the report and record contracts. The concrete representation remains clear, limiting severity to low, but the inconsistent term is blocking under the terminology criterion. Separating the payload from its stored entry is the preferred repair.",
        "owner_target_id": "module.issues",
        "evidence": [
          {
            "path": "specs/concorde/issues/interface.md",
            "description": "contract.issues.report, cited by the terminology finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.issues",
        "context_id": "sha256:598659ceff07f40883b41c88a8cd343d72e19fab28d7edeedb3affe1b09649bc",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
