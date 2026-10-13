# I-bd3b56fe95cb5c48aca94dbcb6ccb68d

```json
{
  "schema_version": 4,
  "id": "I-bd3b56fe95cb5c48aca94dbcb6ccb68d",
  "status": "open",
  "reports": [
    {
      "id": "sha256:9c721ceea29f3b1961b5180481f161fd4b0889e76ce00d81c88b349f934a1d27",
      "created_at": "2026-10-13T17:37:59.918037+00:00",
      "report": {
        "report_key": "code-review/module.checks/2",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Measure current check definitions before each run",
        "description": "Before-run measurements reuse the configuration snapshot from the start of the whole call, whereas after-run measurements read current configuration. A definition change between checks is therefore incorrectly classified as a change during the later check.\n\nSuggested repair: Refresh and validate the relevant configuration before each check and ensure its executed command and both measurements use the appropriate current definition. Add a regression that changes a definition, rather than only implementation bytes, between checks.",
        "impact": "A stable second check can cause stale_evidence and discard all results merely because a definition changed before its run began.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 (module review) judged src/concorde/execution/checks/checks.py:759-762, src/concorde/execution/checks/checks.py:818, src/concorde/execution/checks/checks.py:867-875 against specs/concorde/execution/checks/module.md#one-call-of-the-check-service and reported a violation: The Spec says 'A change between two checks is no change during either of them' and each result measures its own run. run_checks captures the initial checks list in def measure(check=check, checks=checks); _run_one uses measure() before execution but measure(checks=None) afterwards, which rereads the file.",
        "owner_target_id": "module.checks",
        "evidence": [
          {
            "path": "src/concorde/execution/checks/checks.py",
            "description": "lines 759-762, shown by the violation finding"
          },
          {
            "path": "src/concorde/execution/checks/checks.py",
            "description": "line 818, shown by the violation finding"
          },
          {
            "path": "src/concorde/execution/checks/checks.py",
            "description": "lines 867-875, shown by the violation finding"
          },
          {
            "path": "specs/concorde/execution/checks/module.md",
            "description": "defines specs/concorde/execution/checks/module.md#one-call-of-the-check-service, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.checks",
        "context_id": "sha256:2ebc2edac0a9beb4426e5f87435f55444d15833ccfb9a9e96526f8611f0a0075",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
