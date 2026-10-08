# I-761c1984dea15a7bbdbe841b65dbce2a

```json
{
  "schema_version": 4,
  "id": "I-761c1984dea15a7bbdbe841b65dbce2a",
  "status": "open",
  "reports": [
    {
      "id": "sha256:6a8517d71a82d34fcd85481a15ba5d300dfe46dca1a20db5413de8bb47b90838",
      "created_at": "2026-10-08T03:52:45.060223+00:00",
      "report": {
        "report_key": "code-review/module.spec/1",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Repository queries mix loaded declarations with live filesystem state",
        "description": "Filesystem-derived query inputs are not captured when the repository is constructed. The existing snapshot test primes the external cache before modifying files, so it does not cover changes before the first query or changes to bound-file listings.\n\nSuggested repair: Capture bound-path listings, external material and existence, and installation classification as construction-time snapshot inputs. Test mutations both before the first query and between repeated queries, with fresh() observing the changes.",
        "impact": "One repository can produce different file lists, external digests, context identities, and grant levels without reconstruction, defeating callers' snapshot assumptions.",
        "basis": "project_review run r-20261008T024839-project_review-a7857ff6 (module review) judged src/concorde/spec/content_repository.py:1570-1631, src/concorde/spec/grants.py:264-267, tests/concorde/spec/test_loading.py:114-133 against req.spec.snapshot-reconstruct and reported a violation: bound_files expands entries against self.root on every call. _external reads and caches bytes only on first query, and external_context recomputes existence each time. grant also rereads installed_files(repository.root). The requirement says every query answers from sources as they were at construction.",
        "owner_target_id": "module.spec",
        "evidence": [
          {
            "path": "src/concorde/spec/content_repository.py",
            "description": "lines 1570-1631, shown by the violation finding"
          },
          {
            "path": "src/concorde/spec/grants.py",
            "description": "lines 264-267, shown by the violation finding"
          },
          {
            "path": "tests/concorde/spec/test_loading.py",
            "description": "lines 114-133, shown by the violation finding"
          },
          {
            "path": "specs/concorde/spec-tooling/spec/requirements.md",
            "description": "defines req.spec.snapshot-reconstruct, the finding's basis"
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
