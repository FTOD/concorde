# I-df9c9c2c0d0e5d25bb2c38af7cce0335

```json
{
  "schema_version": 4,
  "id": "I-df9c9c2c0d0e5d25bb2c38af7cce0335",
  "status": "open",
  "reports": [
    {
      "id": "sha256:9f33670dd47727204161d7929bb450850934a4c4102d06f3f03569d8ab8aa630",
      "created_at": "2026-10-08T03:52:48.987669+00:00",
      "report": {
        "report_key": "code-review/module.spec/17",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Malformed Protocol manifests bypass structured binding refusal",
        "description": "Protocol verification assumes that the installed manifest is an object before checking its shape. A malformed copy therefore bypasses the promised refusal interface.\n\nSuggested repair: Validate the installed manifest's top-level shape and asset records before using them, wrapping malformed-copy errors as protocol_mismatch with their path and causes. Test a JSON array/null manifest as well as modified assets.",
        "impact": "A damaged Protocol copy can crash repository construction and validation instead of producing protocol_mismatch and the structured load-error finding.",
        "basis": "project_review run r-20261008T024839-project_review-a7857ff6 (module review) judged src/concorde/spec/repository.py:153-169, src/concorde/spec/validation.py:1475-1496 against req.spec.protocol-binding and reported a violation: _protocol decodes the installed manifest and immediately calls manifest.get('version'). If the installed file contains valid JSON such as [], this raises AttributeError before a binding mismatch is reported. validate_repository does not catch AttributeError.",
        "owner_target_id": "module.spec",
        "evidence": [
          {
            "path": "src/concorde/spec/repository.py",
            "description": "lines 153-169, shown by the violation finding"
          },
          {
            "path": "src/concorde/spec/validation.py",
            "description": "lines 1475-1496, shown by the violation finding"
          },
          {
            "path": "specs/concorde/spec-tooling/spec/requirements.md",
            "description": "defines req.spec.protocol-binding, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T024839-project_review-a7857ff6",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.spec",
        "context_id": "sha256:b9d71c73a527514a46b9ca3276c669e4c070ce765d7a7c1c3f02e4b4fde5b92b",
        "change_id": null,
        "head": "a5d10ce4554159cc1f8ca09d5a84e182608a6036",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
