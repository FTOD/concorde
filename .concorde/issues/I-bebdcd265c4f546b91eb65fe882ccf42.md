# I-bebdcd265c4f546b91eb65fe882ccf42

```json
{
  "schema_version": 4,
  "id": "I-bebdcd265c4f546b91eb65fe882ccf42",
  "status": "open",
  "reports": [
    {
      "id": "sha256:060b34ac5dc1672a5a777f3b40e039ab2f6f66b57738b5e65141e0eddcb02ec5",
      "created_at": "2026-10-13T18:09:23.370241+00:00",
      "report": {
        "report_key": "code-review/module.distribution/3",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Duplicate part registrations crash their diagnostic",
        "description": "The duplicate-part diagnostic references an undefined variable, so the error path itself crashes.\n\nSuggested repair: Use registration.path for both references to the new registration, and test two directories declaring the same part name.",
        "impact": "A duplicate part registration produces NameError instead of the intended registration refusal. Installer and command startup paths that catch RegistrationError can terminate without their structured error result.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 (module review) judged src/concorde/distribution/parts.py:295-308 against contract.distribution.part-registration and reported a defect: package_parts detects `registration.part in found`, but its intended RegistrationError interpolates `relative` and passes `relative` as its path argument. No local or module-level variable named relative exists in this function's scope; read() has a separate local of that name.",
        "owner_target_id": "module.distribution",
        "evidence": [
          {
            "path": "src/concorde/distribution/parts.py",
            "description": "lines 295-308, shown by the defect finding"
          },
          {
            "path": "specs/concorde/distribution/contracts.md",
            "description": "defines contract.distribution.part-registration, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.distribution",
        "context_id": "sha256:b3e4b9a1d6a5c7edf7f6b97c306c506e0236cbfd38f99b33935a579437ac47ba",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
