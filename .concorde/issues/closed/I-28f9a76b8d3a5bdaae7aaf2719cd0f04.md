# I-28f9a76b8d3a5bdaae7aaf2719cd0f04

```json
{
  "schema_version": 4,
  "id": "I-28f9a76b8d3a5bdaae7aaf2719cd0f04",
  "status": "closed",
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
    },
    {
      "id": "sha256:a9c254b56cb0e9917f07066b907d668d23ef59955bff4746eaa8d2a2c9512ed1",
      "created_at": "2026-10-03T03:20:49.845753+00:00",
      "report": {
        "report_key": "module.concorde/8",
        "tier": "obvious-fix",
        "severity": "low",
        "type": "bug",
        "subtype": null,
        "title": "Part dependencies combines import and installation obligations",
        "description": "One requirement combines a restriction on code imports with a restriction on mandatory installation dependencies.\n\nSuggested repair: Keep the import restriction under the existing identity and define a separate installation-dependency requirement, both referring to the parts table. Preserve the outstanding canonical-fingerprint-encoding repair in the earlier Issue.",
        "impact": "Import restrictions and mandatory-installation restrictions cannot be tracked independently as stable obligations even though either can be violated alone.",
        "basis": "spec_panel run r-20261003T031022-spec_panel-14df7875 judged specs/concorde/requirements.md at req.concorde.part-dependencies, line 11 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: \"Every [part](glossary.json#concept.part) SHALL import code of, and require the installation of, only the parts it depends on\".\n\nThe panel's chair merged r3.2 and verified: Verified two independently decidable restrictions. Low severity for obligation organization and obvious-fix because splitting preserves both promises. The source's earlier identity is retained as instructed, but its original fingerprint-encoding defect remains independently present and must not be treated as repaired by this split.",
        "owner_target_id": "module.concorde",
        "evidence": [
          {
            "path": "specs/concorde/requirements.md",
            "description": "req.concorde.part-dependencies, cited by the obligations finding"
          }
        ],
        "issue_id": "I-28f9a76b8d3a5bdaae7aaf2719cd0f04",
        "expected_revision": "sha256:6f6c2421c6f94ab191f9706acf5e72067813b561c12adc7a2ae83df79c4628a4"
      },
      "source": {
        "invocation_id": "r-20261003T031022-spec_panel-14df7875",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.concorde",
        "context_id": "sha256:3c577f5386c868abefc662fbbed61d8e280a4f6c3265e8687132615872deb336",
        "change_id": null,
        "head": "43871f64ab7162b4b32fd566e2f81ec15aba06d2"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-spec-root, merged into the primary branch at 337934dadfdbcc4ac0efc87a90d76679bb4e6591.",
      "evidence": [
        "merge commit 337934dadfdbcc4ac0efc87a90d76679bb4e6591",
        "task fix-spec-root"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-03T06:31:43.152032+00:00"
    }
  ]
}
```
