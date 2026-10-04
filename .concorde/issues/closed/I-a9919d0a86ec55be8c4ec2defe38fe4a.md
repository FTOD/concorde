# I-a9919d0a86ec55be8c4ec2defe38fe4a

```json
{
  "schema_version": 4,
  "id": "I-a9919d0a86ec55be8c4ec2defe38fe4a",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:b0e812ee93469b9f964fba72074d3f1c50e92b8901c0977e45840acbe19e3e10",
      "created_at": "2026-10-03T04:00:59.886587+00:00",
      "report": {
        "report_key": "spec-review-grant-terms-aliasing",
        "tier": "suggestion",
        "severity": "low",
        "type": "bug",
        "subtype": null,
        "title": "Grant and context records share mutable glossary entries with the repository",
        "description": "grant() puts the repository's own glossary_entries dictionaries into Grant.value['terms'], and term_records() returns the same dictionaries in spec context records. A caller that mutates a returned record changes the repository's entries and so every later context and context identity of that repository. No current caller mutates them.\n\nSuggested repair: return deep copies (or read-only views) of the glossary entries.",
        "impact": "None today; a future caller that edits a returned grant or context record would silently change the repository it came from.",
        "basis": "From the module.spec reviewer of code_review run r-20261003T032159-code_review-6dd40e26 (its finding 3), which the host could not record; verified against the code and Spec by the task session of task parts-review. req.spec.snapshot-reconstruct (a repository answers from its sources as constructed). grant() in src/concorde/spec/grants.py and term_records() in src/concorde/spec/content_repository.py return repository.glossary_entries[...] directly. Lowered from obvious-fix/medium to suggestion/low because no caller mutates the records.",
        "owner_target_id": "module.spec",
        "evidence": [
          {
            "path": "src/concorde/spec/grants.py",
            "description": "grant() builds terms from repository.glossary_entries without copying"
          },
          {
            "path": "src/concorde/spec/content_repository.py",
            "description": "term_records() returns the repository's entry dictionaries"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-2c5c7750-456b-4b01-a161-da69509a8626",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.spec",
        "context_id": "sha256:1d5cfc2a2a7ba74b163c0a7da2044601cb98d3bb39fa931e4f515946b2ee70f4",
        "change_id": "parts-review",
        "head": "43871f64ab7162b4b32fd566e2f81ec15aba06d2"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-open-spec, merged into the primary branch at 5bae23eab3684e46256cd75d2eec28c986ef6751.",
      "evidence": [
        "merge commit 5bae23eab3684e46256cd75d2eec28c986ef6751",
        "task fix-open-spec"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-04T02:45:48.207573+00:00"
    }
  ]
}
```
