# I-558aded6b7b35a7a98ae5cdbbdc4a949

```json
{
  "schema_version": 3,
  "id": "I-558aded6b7b35a7a98ae5cdbbdc4a949",
  "status": "open",
  "reports": [
    {
      "id": "sha256:81e140d7cb7cb2a258ef65556227be08a61aed0db350999dcd4c26aaaa0834f4",
      "created_at": "2026-10-01T05:30:49.550771+00:00",
      "report": {
        "report_key": "module.distribution/16",
        "tier": "decision-needed",
        "type": "bug",
        "subtype": null,
        "title": "Initialization has no defined handoff for the glossary import",
        "description": "The promised post-initialization glossary amendment has no defined handoff between Distribution and Spec core. Spec core's initialization transaction cannot perform the CLAUDE.md write, and Distribution's adapter description does not explain an additional step.\n\nSuggested repair: Assign the amendment explicitly, preferably to Distribution's guidance handling after successful Spec core initialization. Specify the result, partial-failure reporting and recovery without repeating an initialization that now refuses already_initialized.\n\nOther Modules concerned: module.spec, module.main-session",
        "impact": "Delegation alone cannot produce the promised import. An extra adapter write could fail after initialization succeeds, leaving callers without a specified result or recovery procedure.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/distribution/module.md at installing-into-a-project, line 276 by the interfaces criterion of the Protocol's Evaluating a Spec; the Specs read: Distribution says the glossary import is one \"which `concorde init --apply` also adds when it creates the first glossary\". Spec core's initialization contract permits writing \"only the configuration, the registry, the members of the documents the proposed registry lists and the glossary it declares\", which excludes the existing CLAUDE.md.\n\nThe panel's chair merged a1.3 and verified: Verified Distribution's promise and scenario against Spec core's five-file initialization transaction and allowed paths. Neither defines the extra handoff and partial-failure behavior. Ownership and failure semantics must be decided.",
        "owner_target_id": "module.distribution",
        "evidence": [
          {
            "path": "specs/concorde/distribution/module.md",
            "description": "installing-into-a-project, cited by the interfaces finding"
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
