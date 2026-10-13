# I-1e6fe92f4b0a56a3bebb2cfcc0d01ed6

```json
{
  "schema_version": 4,
  "id": "I-1e6fe92f4b0a56a3bebb2cfcc0d01ed6",
  "status": "open",
  "reports": [
    {
      "id": "sha256:0a0575c8d95fa64ae07cfd42dc1d178cfbdfb43a574b283dd37278ea69e34cd3",
      "created_at": "2026-10-13T18:40:42.258819+00:00",
      "report": {
        "report_key": "code-review/module.harness/1",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Preserve symbolic-link spellings of admitted runtime paths",
        "description": "Runtime-path compilation discards the caller's symbolic-link spelling and preserves only its resolved target. When that spelling lies in otherwise protected material and is not independently granted, it remains denied even though the caller explicitly admitted it.\n\nSuggested repair: Preserve both the supplied absolute spelling and its resolved target when compiling runtime read access and deny-rule exclusions, retaining the existing overlap protections and read-only treatment. Add cases for a symlinked runtime directory inside the worktree and a symlinked runtime file inside the user's home, checking reads through the supplied paths on both backends.",
        "impact": "A worker can be refused when reading an explicitly admitted environment or log path through its symbolic link. The caller must discover and use the target spelling as a workaround; tools using the original path do not receive the promised access.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 (module review) judged src/concorde/worker_harness/settings.py:385-393, src/concorde/worker_harness/settings.py:463-466, src/concorde/worker_harness/pi_policy.ts:209-214, src/concorde/worker_harness/pi_backend.py:160-162 against specs/concorde/worker-harness/harness/module.md#a-workers-harness and reported a violation: The Spec says runtime paths are passed 'exactly as the caller lists them' and 'Every tool of the worker, Bash and the file tools alike, may read them.' settings.py:390 replaces each supplied runtime path with its realpath before generating exclusions, and lines 463-466 retain only realpaths in allowRead. The pi policy producer likewise retains only realpaths at pi_backend.py:160-162, while pi_policy.ts:209-214 rejects a denied lexical path before checking its real path. Thus an ungranted worktree path such as .venv that is a symlink to an admitted external environment is not recognized as runtime material under its supplied spelling.",
        "owner_target_id": "module.harness",
        "evidence": [
          {
            "path": "src/concorde/worker_harness/settings.py",
            "description": "lines 385-393, shown by the violation finding"
          },
          {
            "path": "src/concorde/worker_harness/settings.py",
            "description": "lines 463-466, shown by the violation finding"
          },
          {
            "path": "src/concorde/worker_harness/pi_policy.ts",
            "description": "lines 209-214, shown by the violation finding"
          },
          {
            "path": "src/concorde/worker_harness/pi_backend.py",
            "description": "lines 160-162, shown by the violation finding"
          },
          {
            "path": "specs/concorde/worker-harness/harness/module.md",
            "description": "defines specs/concorde/worker-harness/harness/module.md#a-workers-harness, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.harness",
        "context_id": "sha256:0402f6a704021b21698ee07a657da47a5f7fe070e3d121c901aa77ebf6370462",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
