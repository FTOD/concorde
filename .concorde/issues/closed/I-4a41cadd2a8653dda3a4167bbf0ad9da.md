# I-4a41cadd2a8653dda3a4167bbf0ad9da

```json
{
  "schema_version": 4,
  "id": "I-4a41cadd2a8653dda3a4167bbf0ad9da",
  "status": "closed",
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
    },
    {
      "id": "sha256:a362e49281f841eddf5c4c34ee1ba1e515ee7c5c3a683188987a8a3825f686be",
      "created_at": "2026-10-03T08:51:00.905509+00:00",
      "report": {
        "issue_id": "I-4a41cadd2a8653dda3a4167bbf0ad9da",
        "expected_revision": "sha256:3d2fd88dd9bdee71a7579d345a1ed913fb022b97a06d93f7e82a09be02c308a7",
        "report_key": "module.distribution/16-verified",
        "tier": "obvious-fix",
        "severity": "low",
        "title": "uses-dogfooding omits the coordination-and-issues condition of develop guidance; project-mcp --name is unexplained",
        "description": "specs/concorde/distribution/module.md: (1) uses-dogfooding says the installer, after Dogfooding's source check, 'then adds its rendered guidance to the skill and the CLAUDE.md block', while guidance-composition (and the installer, DEVELOP_GUIDANCE_NEEDS) adds it only in a develop install that installs the coordination and issues parts. (2) The command table lists `project-mcp [--name <name>]` without saying what the name is (main's Main session contract said: the server name, default `concorde`). (3) Installer options (--parts, --develop, --without-d2, --without-pi-runtime, --without-dependencies, --update) are spread over several sections.\n\nFix: in uses-dogfooding write '... then, where the coordination and issues parts are installed, adds its rendered guidance ([guidance composition](#guidance-composition)) ...'; in the command table add 'the server's name, `concorde` by default'; optionally give the full installer synopsis in 'Installing into a project'.",
        "impact": "A reader may expect develop guidance in a partial develop install; the composition paragraph and code are right.",
        "basis": "Read module.md uses-dogfooding, guidance-composition and the command table; src/concorde/distribution/install.py DEVELOP_GUIDANCE_NEEDS. Classification: regression — the coordination-and-issues condition came with 6b24ab1c without updating uses-dogfooding (unchanged from main), and the --name explanation was in main's Main session contracts, dropped with the move. Tier raised to obvious-fix (a real inconsistency, clear fix); severity stays low.",
        "owner_target_id": "module.distribution",
        "type": "bug",
        "subtype": null,
        "evidence": [
          {
            "path": "specs/concorde/distribution/module.md",
            "description": "uses-dogfooding paragraph vs guidance-composition's develop-section condition"
          },
          {
            "path": "src/concorde/distribution/install.py",
            "description": "DEVELOP_GUIDANCE_NEEDS = coordination, issues"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-e04d7b93-364d-4cf3-90c0-9776d1b66d8e",
        "agent": "task-session",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.distribution",
        "context_id": "sha256:dc5a1d8cbf5a69d2834f2ea5f6545ea6067e5caf2e4e3c78dfc4f3342c22cb32",
        "change_id": "parts-review-specs",
        "head": "41bda04db324df4ff913498f023597a72c419955"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task parts-review-specs, merged into the primary branch at 8f6860b42000fa749564007acf84e7faea3d3a2c.",
      "evidence": [
        "merge commit 8f6860b42000fa749564007acf84e7faea3d3a2c",
        "task parts-review-specs"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-03T09:36:13.279357+00:00"
    }
  ]
}
```
