# I-28f9a76b8d3a5bdaae7aaf2719cd0f04

```json
{
  "schema_version": 4,
  "id": "I-28f9a76b8d3a5bdaae7aaf2719cd0f04",
  "status": "open",
  "reports": [
    {
      "id": "sha256:d1385822b0836f888198e9d6e4eb3ab912ec846562946204264ad500251678bc",
      "created_at": "2026-10-02T19:19:05.613895+00:00",
      "report": {
        "report_key": "module.concorde/9",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Fingerprint digests lack a canonical input encoding",
        "description": "Sorted object keys alone do not define a reproducible fingerprint algorithm: the hashed JSON structures, ordering and byte encoding remain unspecified.\n\nSuggested repair: Specify the exact component and aggregate JSON values, normalized path representation and file ordering, and canonical UTF-8 serialization including separators and escaping. Add a small fixed digest example to establish compatibility.",
        "impact": "Conforming implementations can produce different persistent identities for identical measured inputs, invalidating prior-run comparisons after an otherwise irrelevant serialization or iteration-order change.",
        "basis": "spec_panel run r-20261002T190724-spec_panel-89d5bab4 judged specs/concorde/development.md at req.concorde.test-fingerprints, line 41 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The document says \"Every digest is the SHA-256 of the JSON of what it covers, with sorted keys\", describes input as each file's path with its byte hash, and specifies one digest of the five component digests. It supplies no concrete hashed record shapes, file-record ordering or canonical byte serialization.\n\nThe panel's chair merged r3.3 and verified: Verified the complete fingerprint specification and comparison use. Medium because saved development evidence depends on reproducible identity; preferred-fix because several canonical encodings are possible but explicitly defining one is the clear repair.",
        "owner_target_id": "module.concorde",
        "evidence": [
          {
            "path": "specs/concorde/development.md",
            "description": "req.concorde.test-fingerprints, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261002T190724-spec_panel-89d5bab4",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.concorde",
        "context_id": "sha256:087f2e827d6000598e76aaf26d3174f0c178915ee4edda0e14809314a487964c",
        "change_id": "parts-spec",
        "head": "5c717b606e11e429829ec27129610d7a6d21916a"
      }
    }
  ],
  "dispositions": []
}
```
