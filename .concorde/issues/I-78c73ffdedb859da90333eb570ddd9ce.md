# I-78c73ffdedb859da90333eb570ddd9ce

```json
{
  "schema_version": 4,
  "id": "I-78c73ffdedb859da90333eb570ddd9ce",
  "status": "open",
  "reports": [
    {
      "id": "sha256:e7862ada7b167f46cdf9a2f1a8557902293659a335bfda931ca90e7340284896",
      "created_at": "2026-10-08T03:52:48.481206+00:00",
      "report": {
        "report_key": "code-review/module.spec/15",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Commented TypeScript calls can falsely establish scenario coverage",
        "description": "The TypeScript scanner recognizes apparent test calls in comments and string literals as actual calls. Its search does not distinguish source code from inert text.\n\nSuggested repair: Use a lightweight lexical scan that skips comments and strings when locating test-call tokens, while still reading titles from actual calls. Add commented-call, block-comment, and string-literal counterexamples without compiling or executing TypeScript.",
        "impact": "Commented-out tests can count as scenario coverage, suppressing an uncovered-scenario warning and the malformed-declaration error.",
        "basis": "project_review run r-20261008T024839-project_review-a7857ff6 (module review) judged src/concorde/spec/verification.py:138-166, src/concorde/spec/verification.py:194-199 against specs/concorde/spec-tooling/spec/contracts.md#verification-declarations and reported a violation: _typescript_title applies TYPESCRIPT_CALL.search to each raw line, including comments and strings. A declaration followed only by '// it(\"disabled\", () => {});' receives the title 'disabled' and is accepted instead of the required 'verifies: comment declares no test' error.",
        "owner_target_id": "module.spec",
        "evidence": [
          {
            "path": "src/concorde/spec/verification.py",
            "description": "lines 138-166, shown by the violation finding"
          },
          {
            "path": "src/concorde/spec/verification.py",
            "description": "lines 194-199, shown by the violation finding"
          },
          {
            "path": "specs/concorde/spec-tooling/spec/contracts.md",
            "description": "defines specs/concorde/spec-tooling/spec/contracts.md#verification-declarations, the finding's basis"
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
