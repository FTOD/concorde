# I-1bfef91eff8f5393ac01ad1ec0b435e4

```json
{
  "schema_version": 4,
  "id": "I-1bfef91eff8f5393ac01ad1ec0b435e4",
  "status": "open",
  "reports": [
    {
      "id": "sha256:7ea62fc8c438457e4a48ad6c63c77252655f71b05f9657f1cc73fb1f90ebb932",
      "created_at": "2026-10-13T17:32:25.616257+00:00",
      "report": {
        "report_key": "spec-panel/module.adoption/4",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "missing-contract",
        "title": "Select the Scaffold promises used to validate proposals",
        "description": "Adoption relies on Scaffold's folder-construction and no-overwrite promises without selecting their defining documents. A link and Adoption's restatement do not supply the provider's canonical context.\n\nSuggested repair: Declare a narrowly scoped uses relation to module.scaffold, selecting its entry and req.scaffold.no-overwrite, and explain why survey validation relies on those promises. Ensure the folder-construction definition is included in the selected documents.\n\nOther Modules concerned: module.scaffold",
        "impact": "A task maintaining proposal validation cannot consult the canonical folder and no-overwrite promises that the text expressly relies upon.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/method/adoption/requirements.md at req.adoption.proposal-checked, line 249 by the context criterion of the Protocol's Evaluating a Spec; the Specs read: “A child's folder is the surveyed Module's entry folder plus the last segment of the child's identity, as Scaffold writes it.” The next sentence relies on req.scaffold.no-overwrite. Adoption's module metadata selects Method, Execution, Operations, Workers, Checks, Spec core and Workflows, but neither Scaffold nor its documents.\n\nThe panel's chair merged r1.8, r2.4, r3.1 and verified: Verified both the reliance in requirements.md and the selections in module.md.json. The defining Scaffold documents are outside the supplied context. Medium severity because maintenance requires unavailable defining context; preferred-fix because a narrow provider selection repairs this without changing behaviour. The optional brownfield walkthrough link is not independently established as necessary.",
        "owner_target_id": "module.adoption",
        "evidence": [
          {
            "path": "specs/concorde/method/adoption/requirements.md",
            "description": "req.adoption.proposal-checked, cited by the context finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.adoption",
        "context_id": "sha256:9f91a9083aa5a25dd5b8613c94f830f11513195394a5776d0abf8187e3c2ae1b",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
