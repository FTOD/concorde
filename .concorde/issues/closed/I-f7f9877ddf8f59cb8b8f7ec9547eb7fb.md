# I-f7f9877ddf8f59cb8b8f7ec9547eb7fb

```json
{
  "schema_version": 4,
  "id": "I-f7f9877ddf8f59cb8b8f7ec9547eb7fb",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:9ebfe7ffff607cdb9624eb9a0e5602d9e00fe4a2ffaa6e8f2c73f978bf3a017f",
      "created_at": "2026-10-03T04:25:54.839468+00:00",
      "report": {
        "report_key": "module.commands/2",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Command catalog omits the providing Module",
        "description": "The command catalog records the registering part but not the providing Module promised by its Spec. Neither its registration API nor its stored Provider carries that identity.\n\nSuggested repair: Add a providing-Module identity to command definitions or catalog registration metadata and expose it alongside the registering part, writes flag and output contract.",
        "impact": "Catalog consumers cannot identify the providing Module; Method's Validation, Delivery and Scaffold providers are all represented only as the method part.",
        "basis": "code_review run r-20261003T041234-code_review-72e86ad6 (module review) judged src/concorde/execution/commands/catalog.py:10-12, src/concorde/execution/operations/catalog.py:28-30, src/concorde/execution/context.py:41-65 against specs/concorde/execution/commands/module.md#the-command-catalog and reported a violation: The Spec says the catalog lists each execution command 'with its providing Module, what it writes and its output'. Catalog stores only definitions and parts; Provider declares writes and output_schema but no providing Module, and Catalog.part returns the registering part.",
        "owner_target_id": "module.commands",
        "evidence": [
          {
            "path": "src/concorde/execution/commands/catalog.py",
            "description": "lines 10-12, shown by the violation finding"
          },
          {
            "path": "src/concorde/execution/operations/catalog.py",
            "description": "lines 28-30, shown by the violation finding"
          },
          {
            "path": "src/concorde/execution/context.py",
            "description": "lines 41-65, shown by the violation finding"
          },
          {
            "path": "specs/concorde/execution/commands/module.md",
            "description": "defines specs/concorde/execution/commands/module.md#the-command-catalog, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T041234-code_review-72e86ad6",
        "agent": "operation",
        "operation": "code_review",
        "phase": "report",
        "target_id": "module.commands",
        "context_id": "sha256:a3eff19b3049502d74d9e0c37403f839f547d610eab6cb8461f7ef5e0e7b0545",
        "change_id": "parts-review",
        "head": "43871f64ab7162b4b32fd566e2f81ec15aba06d2"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "duplicate",
      "note": "Same problem as I-3f709b3041765ee5989f5e26235f4356: the command catalog is an instance of the same Catalog class (src/concorde/execution/commands/catalog.py:10-12 builds Catalog('command') from src/concorde/execution/operations/catalog.py), which keeps the registering part and no providing Module; one decision and one fix cover both catalogs, and I-3f70's corrected report names the commands Spec too.",
      "evidence": [
        "src/concorde/execution/commands/catalog.py",
        "src/concorde/execution/operations/catalog.py",
        "specs/concorde/execution/commands/module.md"
      ],
      "duplicate_of": "I-3f709b3041765ee5989f5e26235f4356",
      "actor": "main-agent",
      "created_at": "2026-10-03T04:36:46.989408+00:00"
    }
  ]
}
```
