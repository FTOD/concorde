# I-073de3b4c29d5ebeadac7da0c87e5008

```json
{
  "schema_version": 4,
  "id": "I-073de3b4c29d5ebeadac7da0c87e5008",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:ca6af04480db2d3e9d20ffd25c51758af069cef292f4ba5351b837a695aa46b1",
      "created_at": "2026-10-08T04:24:07.894188+00:00",
      "report": {
        "report_key": "code-review/module.views/12",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Malformed UTF-8 errors omit the offending source",
        "description": "Strict UTF-8 decoding failures escape without a source-qualified diagnostic.\n\nSuggested repair: Wrap decoding failures with the project-relative source path while preserving the underlying cause, and assert that path in malformed-reading and malformed-metadata tests.",
        "impact": "A build stops on malformed source bytes without telling the caller which registered document, metadata file or glossary needs repair.",
        "basis": "project_review run r-20261008T024839-project_review-a7857ff6 (module review) judged docsite/plugins/scoped-content/model.ts:133-135, docsite/tests/scoped-registry.test.ts:541-547 against specs/concorde/spec-tooling/views/pipeline.md#loading-and-admission and reported a violation: The pipeline requires loading errors to name their source. safeRead directly returns TextDecoder(..., {fatal: true}).decode(readFileSync(current)); invalid UTF-8 throws a decoder error without the file path. The malformed-UTF-8 regression only checks toThrow(), so it does not verify the promised diagnostic.",
        "owner_target_id": "module.views",
        "evidence": [
          {
            "path": "docsite/plugins/scoped-content/model.ts",
            "description": "lines 133-135, shown by the violation finding"
          },
          {
            "path": "docsite/tests/scoped-registry.test.ts",
            "description": "lines 541-547, shown by the violation finding"
          },
          {
            "path": "specs/concorde/spec-tooling/views/pipeline.md",
            "description": "defines specs/concorde/spec-tooling/views/pipeline.md#loading-and-admission, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T024839-project_review-a7857ff6",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.views",
        "context_id": "sha256:694a75b7b53df6199b1e598851e63c9bf43c9da18f3e23215369fca09ba2fa05",
        "change_id": null,
        "head": "a5d10ce4554159cc1f8ca09d5a84e182608a6036",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-views, merged into the primary branch at ba34be01f66451b967a852948bb0a465c794705c.",
      "evidence": [
        "merge commit ba34be01f66451b967a852948bb0a465c794705c",
        "task fix-views"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-08T07:25:32.666560+00:00"
    }
  ]
}
```
