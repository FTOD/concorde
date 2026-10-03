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
    },
    {
      "id": "sha256:fe7f03fea285f72139db2c4bcc4e9af5dfb22387460e582a83b5300edafb2d5e",
      "created_at": "2026-10-03T08:49:47.058375+00:00",
      "report": {
        "issue_id": "I-d8b60e4393565e3a9ce516ce1bfcedaf",
        "expected_revision": "sha256:442f81db000958c4ffd9a0af1541ccf36dad05e4c9c6b7c15b892dbef24838ba",
        "report_key": "module.distribution/10-verified",
        "tier": "obvious-fix",
        "severity": "low",
        "title": "req.distribution.installer-fresh-guidance says 'older than its sources' and covers only guidance",
        "description": "specs/concorde/distribution/requirements.md, req.distribution.installer-fresh-guidance: 'refuse to install main-session guidance whose rendered output is missing or older than its sources'. The installer actually refuses any stale build by the build manifest's digests (install.py verify_fresh → `stale_build`), as module.md step 1 and the refusal table say ('the build is stale, or a render or file the install places ... is missing'); no requirement states that general refusal.\n\nFix: restate it as 'The installer SHALL refuse with `stale_build`, before writing anything, a package whose build manifest records a missing or changed source or output, or that lacks a render or file the installed parts place', and retitle it; module.md's links stay valid.",
        "impact": "A reader could implement a timestamp check limited to guidance; the code checks digests for every output, so nothing is wrong today.",
        "basis": "Read the requirement, module.md step 1 and the refusal table, src/concorde/distribution/install.py (verify_fresh, _missing_shipped). Classification: pre-existing — identical requirement on main (git show main:specs/concorde/distribution/requirements.md). Severity lowered from medium; tier obvious-fix since the wording fix is clear.",
        "owner_target_id": "module.distribution",
        "type": "bug",
        "subtype": null,
        "evidence": [
          {
            "path": "specs/concorde/distribution/requirements.md",
            "description": "req.distribution.installer-fresh-guidance"
          },
          {
            "path": "src/concorde/distribution/install.py",
            "description": "verify_fresh refuses any stale build with stale_build"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-4a2d9f95-7106-4335-a676-03c1057ec9a1",
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
  "dispositions": []
}
```
