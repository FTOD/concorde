# I-29d63aa9d81558cfaafc2deaa3154be0

```json
{
  "schema_version": 3,
  "id": "I-29d63aa9d81558cfaafc2deaa3154be0",
  "status": "open",
  "reports": [
    {
      "id": "sha256:d45c1924917ebcc369b8c36815f4164ca9c96c0ea49d1f02b9dc6cf2a323fc04",
      "created_at": "2026-10-01T05:30:49.070665+00:00",
      "report": {
        "report_key": "module.distribution/7",
        "tier": "decision-needed",
        "type": "bug",
        "subtype": null,
        "title": "Protocol-manifest flag modes lack a complete behavior contract",
        "description": "The public protocol-manifest command leaves its individual flag modes undefined. Its manifest data is defined in selected context, but that definition does not establish the command's effects for every advertised mode.\n\nSuggested repair: Link to Spec core's existing manifest definition and specify the valid flag combinations, each mode's writes, binding and copy-refresh effects, result, and refusals in implementation reading.\n\nOther Modules concerned: module.spec",
        "impact": "A caller or implementer cannot determine which state each advertised flag combination changes or when it should be refused.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/distribution/module.md at the-command-line, line 196 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The table advertises `protocol-manifest [--write] [--bind-project]` as \"reconciles the Protocol manifest\". The build section explains `--write --bind-project`, and scenarios cover that combination and no flags, but no passage defines `--write` alone or the validity of `--bind-project` alone.\n\nThe panel's chair merged r1.8 and verified: Spec core's selected contracts.md#protocol-manifest already defines the tracked manifest's path, assets, version and binding digest, so the broad terminology claim does not hold. The independently reported command-mode gap remains; resolving the unspecified combinations requires choosing public behavior.",
        "owner_target_id": "module.distribution",
        "evidence": [
          {
            "path": "specs/concorde/distribution/module.md",
            "description": "the-command-line, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261001T051011-spec_panel-91e80034",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.distribution",
        "context_id": "sha256:763ec486bd954028051a1133a2036e5bb74e9c151d89fed6d611b973b9a9f4a8",
        "change_id": null,
        "head": "eb6687427361c480d7a7eb0d9a022b0c2c9f5dbb"
      }
    }
  ],
  "dispositions": []
}
```
