# I-4a41cadd2a8653dda3a4167bbf0ad9da

```json
{
  "schema_version": 4,
  "id": "I-4a41cadd2a8653dda3a4167bbf0ad9da",
  "status": "open",
  "reports": [
    {
      "id": "sha256:3fb6117b76ae29ebbdaa89d564fa0a2e0790f091c1e7bfb7d1809e4ba97a38d6",
      "created_at": "2026-10-03T08:43:40.858124+00:00",
      "report": {
        "report_key": "module.distribution/16",
        "tier": "suggestion",
        "severity": "low",
        "type": "bug",
        "subtype": null,
        "title": "Installer options and develop-guidance conditions are hard to find",
        "description": "Installer options are scattered, project-mcp --name is not explained, and the Dogfooding collaboration paragraph omits the guidance condition stated later.\n\nSuggested repair: Provide a complete installer synopsis with concise option effects, explain project-mcp --name, and make the Dogfooding paragraph refer to the coordination-and-issues condition in guidance composition.\n\nOther Modules concerned: module.dogfooding",
        "impact": "A developer must assemble the available options from several sections and may initially expect develop guidance in a partial install that omits it.",
        "basis": "spec_panel run r-20261003T074406-spec_panel-0a7388d8 judged specs/concorde/distribution/module.md at uses-dogfooding, line 811 by the readability criterion of the Protocol's Evaluating a Spec; the Specs read: The installer synopsis shows only `<project> [--parts <part>[,<part>…]]`; other options appear across installation, runtime and update sections. The Dogfooding paragraph says the installer “then adds its rendered guidance”, whereas guidance-composition restricts that addition to installs with coordination and issues.\n\nThe panel's chair merged r1.17 and verified: Verified each cited option and the explicit condition in guidance-composition. Retained as a low-severity advisory organization/summary correction because the operational explanation supplies the condition and the option effects elsewhere.",
        "owner_target_id": "module.distribution",
        "evidence": [
          {
            "path": "specs/concorde/distribution/module.md",
            "description": "uses-dogfooding, cited by the readability finding"
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
