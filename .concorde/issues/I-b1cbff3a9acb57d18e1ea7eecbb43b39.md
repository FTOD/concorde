# I-b1cbff3a9acb57d18e1ea7eecbb43b39

```json
{
  "schema_version": 4,
  "id": "I-b1cbff3a9acb57d18e1ea7eecbb43b39",
  "status": "open",
  "reports": [
    {
      "id": "sha256:d2d01eba676f1be5972ad6ce86ef0931cba7afa7ead8deae770f8f544dc7d7d5",
      "created_at": "2026-10-03T09:37:20.868422+00:00",
      "report": {
        "report_key": "main-agent/registration-uses-distribution-check",
        "tier": "suggestion",
        "severity": "low",
        "type": "limitation",
        "subtype": null,
        "title": "Nothing checks that a part's Module declares its use of Distribution's registration contract",
        "description": "req.concorde.part-dependencies says every part meets Distribution's host promises, the part registration among them, through a declared `uses`. After the parts refactor seven top Modules that bind a registration.json declared no such `uses` until task parts-review-specs added them by hand. No structural check keeps it, so a new part, or a registration moved to another Module, can lose the declaration again unnoticed. Suggested repair: extend the part-dependency test (tests/concorde/development/test_part_dependencies.py), or a Concorde structural check, so that every Module whose realization binds a part's registration.json must declare a `uses` of module.distribution relying on the part registration.",
        "impact": "The Spec context of a part's workers can silently miss the registration contract its own registration must meet, and the root's rule goes unenforced.",
        "basis": "Systemic finding 1 of task parts-review-specs (decision log, report 1), which found and fixed the gap in spec-tooling, Spec core, kernel, worker-harness, execution, issues and method.",
        "owner_target_id": "module.concorde",
        "evidence": [
          {
            "path": "specs/concorde/requirements.md",
            "description": "req.concorde.part-dependencies: format and host reliances are declared as uses"
          },
          {
            "path": "tests/concorde/development/test_part_dependencies.py",
            "description": "checks imports and registration entries, not the Modules' uses of Distribution"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-6ca57cc2-e55a-40fa-93aa-217535fdf50d",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.concorde",
        "context_id": "sha256:b9332e652847410af34a543178b859ed2ac0280c6596f34933dd884bff972a1a",
        "change_id": null,
        "head": "2aa8025c4c07f9516f635b1556ad377caeafeb3c"
      }
    }
  ],
  "dispositions": []
}
```
