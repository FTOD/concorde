# I-01d4e7db35ad5c1981b9f05d8bdebffe

```json
{
  "schema_version": 4,
  "id": "I-01d4e7db35ad5c1981b9f05d8bdebffe",
  "status": "open",
  "reports": [
    {
      "id": "sha256:8d7dbfcd3c224568f331546e98115563806e2a84238c990d8af4ae626da35cda",
      "created_at": "2026-10-08T03:45:18.299988+00:00",
      "report": {
        "report_key": "code-review/module.spec-mcp/3",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Validation of unloadable Specs lacks MCP test coverage",
        "description": "The MCP tests do not exercise validation of Specs that cannot be loaded, despite its explicitly different error behavior.\n\nSuggested repair: Call validate on the Protocol-mismatch fixture and compare its complete decoded result with Spec core's validation envelope. Assert isError is false, status is invalid, exactly one error finding describes the mismatch, and result.load_error preserves the core error record.",
        "impact": "A regression that turns validate's Protocol mismatch into an MCP tool error, drops result.load_error, or returns a partial validation result would escape the Module's tests.",
        "basis": "project_review run r-20261008T024839-project_review-a7857ff6 (module review) judged tests/concorde/spec_mcp/test_server.py:305-319, tests/concorde/spec_mcp/test_server.py:368-384 against req.spec-mcp.no-partial-answer and reported a missing-test: The requirement explicitly makes validate return an invalid validation result for unloadable Specs. test_specs_that_cannot_be_loaded_answer_nothing creates a Protocol mismatch but calls only modules, module, context, boundary and impact. test_validate_returns_the_command_envelope covers a loadable project with a structural error, so neither test exercises validate's distinct load-failure response.",
        "owner_target_id": "module.spec-mcp",
        "evidence": [
          {
            "path": "tests/concorde/spec_mcp/test_server.py",
            "description": "lines 305-319, shown by the missing-test finding"
          },
          {
            "path": "tests/concorde/spec_mcp/test_server.py",
            "description": "lines 368-384, shown by the missing-test finding"
          },
          {
            "path": "specs/concorde/spec-tooling/spec-mcp/requirements.md",
            "description": "defines req.spec-mcp.no-partial-answer, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T024839-project_review-a7857ff6",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.spec-mcp",
        "context_id": "sha256:af82eaf7bfd3aac2fcb03f3bdb58251bc378347bc7f2b624c34d591d59b1dcbd",
        "change_id": null,
        "head": "a5d10ce4554159cc1f8ca09d5a84e182608a6036",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
