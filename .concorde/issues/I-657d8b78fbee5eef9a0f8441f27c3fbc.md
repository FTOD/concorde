# I-657d8b78fbee5eef9a0f8441f27c3fbc

```json
{
  "schema_version": 4,
  "id": "I-657d8b78fbee5eef9a0f8441f27c3fbc",
  "status": "open",
  "reports": [
    {
      "id": "sha256:5c869323d6154a3a49e9408ea005fe8eb69ba2fb17edad2393c8fda6db49ea6d",
      "created_at": "2026-10-03T04:12:11.091236+00:00",
      "report": {
        "report_key": "module.workers/1",
        "tier": "preferred-fix",
        "severity": "critical",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Proposed deletions can escape the grant through directory symlinks",
        "description": "Proposed deletions are authorized using lexical paths, but unlink follows symlinks in their parent directories. An existing directory symlink beneath a writable directory therefore allows the host to delete outside the writable boundary.\n\nSuggested repair: Resolve parent-directory symlinks before checking worktree containment and rw authorization, preserving the final entry's name for unlink semantics. Add tests for parent symlinks pointing outside the worktree and into a read-only subtree.",
        "impact": "A proposal such as src/link/victim, with src/ writable and link pointing outside the worktree or into a read-only directory, can delete the actual ungranted victim with the host's permissions after a clean audit.",
        "basis": "code_review run r-20261003T035159-code_review-dc0efdcc (module review) judged src/concorde/worker_harness/workers.py:1111-1134 against req.workers.host-deletes and reported a violation: _finalize constructs `absolute = Path(os.path.normpath(os.path.join(worktree, proposed)))`, checks its lexical `relative_to(worktree)` and `rw_allows`, then calls `absolute.unlink()`. It never resolves symlinks in parent directories. launch.md#proposed-deletions requires paths outside the worktree or rw list to be refused.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "src/concorde/worker_harness/workers.py",
            "description": "lines 1111-1134, shown by the violation finding"
          },
          {
            "path": "specs/concorde/worker-harness/workers/launch.md",
            "description": "defines req.workers.host-deletes, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T035159-code_review-dc0efdcc",
        "agent": "operation",
        "operation": "code_review",
        "phase": "report",
        "target_id": "module.workers",
        "context_id": "sha256:d1680f8965bc4bd9a8d84ee00426acbf1fdc230cad735073abffd34139c83164",
        "change_id": "parts-review",
        "head": "43871f64ab7162b4b32fd566e2f81ec15aba06d2"
      }
    }
  ],
  "dispositions": []
}
```
