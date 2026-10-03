# I-d8b60e4393565e3a9ce516ce1bfcedaf

```json
{
  "schema_version": 4,
  "id": "I-d8b60e4393565e3a9ce516ce1bfcedaf",
  "status": "open",
  "reports": [
    {
      "id": "sha256:d8d884b834a7424b75faa03fc065d5bf1fa3cc8f92c4e6238a6125e0594a0cef",
      "created_at": "2026-10-03T08:43:39.393944+00:00",
      "report": {
        "report_key": "module.distribution/10",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Installer freshness is specified only for guidance and in ambiguous terms",
        "description": "The precise installer freshness obligation covers only guidance and uses age language inconsistent with the manifest-based design. The general pre-write stale-build refusal remains only in the entry.\n\nSuggested repair: Define one manifest-based installer freshness obligation covering the package outputs it places and refusal before writes. Replace the ambiguous 'older' wording and link guidance and workflow explanations to that obligation.\n\nOther Modules concerned: module.workflows",
        "impact": "A task relying on the requirement can enforce timestamp-based guidance freshness while omitting stale workflow or worker-prompt refusal.",
        "basis": "spec_panel run r-20261003T074406-spec_panel-0a7388d8 judged specs/concorde/distribution/requirements.md at req.distribution.installer-fresh-guidance, line 245 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The requirement refuses guidance “whose rendered output is missing or older than its sources”. The entry says the installer “refuses a stale build” and refuses workflow renders “like any other build output”; the build manifest records source and output digests.\n\nThe panel's chair merged r1.10 and verified: Verified that no-stale-copy covers only the Protocol copy writer and the remaining installer requirement covers guidance alone. Medium severity for stale-output cases; preferred-fix because a general manifest-based installer obligation best matches the existing design.",
        "owner_target_id": "module.distribution",
        "evidence": [
          {
            "path": "specs/concorde/distribution/requirements.md",
            "description": "req.distribution.installer-fresh-guidance, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T074406-spec_panel-0a7388d8",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.distribution",
        "context_id": "sha256:2ff62e1118b212ef9ad5fe6e9d93adf72d0b8ac20908c609971a80ecb027ae5f",
        "change_id": "parts-review-specs",
        "head": "959c856c3a7732af1420829a271f59dd21ba837c"
      }
    }
  ],
  "dispositions": []
}
```
