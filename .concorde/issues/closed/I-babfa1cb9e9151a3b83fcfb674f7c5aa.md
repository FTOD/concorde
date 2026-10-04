# I-babfa1cb9e9151a3b83fcfb674f7c5aa

```json
{
  "schema_version": 4,
  "id": "I-babfa1cb9e9151a3b83fcfb674f7c5aa",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:015fb0e5f0fc47ea4cf7954873c4fa5e60143c1de2295fcd3883451d21e1960b",
      "created_at": "2026-10-04T03:30:28.871985+00:00",
      "report": {
        "title": "pi's Bash sandbox reads a names path listed apart below a readable directory",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "owner_target_id": "module.harness",
        "tier": "obvious-fix",
        "severity": "low",
        "report_key": "fix-open-trace-producers/pi-bash-reads-names-below-readable-dir",
        "description": "sandbox_filesystem (src/concorde/worker_harness/settings.py) puts the task worktree in denyRead and every ro and rw grant path in allowRead, which wins over the wider denyRead. A file or directory the grant lists apart at names below an ro or rw directory entry is therefore readable to Bash: on Claude Code the Read deny rule worktree_rules emits for it is merged into the sandbox's denyRead, but pi's permission extension receives only these sandbox lists, so on pi a `cat` of such a file returns its contents although its file tools refuse to read it. Fix: add every names entry listed strictly below an ro or rw directory entry to denyRead, which sandbox-runtime keeps denied inside a wider allowRead, as the ro/names entries below rw directories were added to denyWrite in fix-open-trace-producers.",
        "impact": "A pi worker can read through Bash the contents of a file whose grant level is names only, such as another Module's file listed apart below a directory it may read; nothing is written, and the read is not audited.",
        "basis": "Probed in task fix-open-trace-producers with the installed @anthropic-ai/sandbox-runtime 0.0.77 and bwrap on Linux: with denyRead [base] and allowRead [base/dir], `cat base/dir/names.txt` printed the file; adding base/dir/names.txt to denyRead made it fail with Permission denied. sandbox-runtime's README (references/sandbox-runtime/README.md) states that a denyRead entry more specific than the allowRead region it falls inside stays denied.",
        "evidence": [
          {
            "path": "src/concorde/worker_harness/settings.py",
            "description": "sandbox_filesystem: denyRead lists only the worktree and boundaries, allowRead every ro and rw path"
          },
          {
            "path": "src/concorde/worker_harness/pi_permission.ts",
            "description": "the pi extension passes these lists to sandbox-runtime for every command"
          },
          {
            "path": "references/sandbox-runtime/README.md",
            "description": "a more specific denyRead stays denied inside a wider allowRead"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-579c0eec-6b15-4654-9c8a-08f650901c43",
        "agent": "task-session",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.harness",
        "context_id": "sha256:6f38070545b3d2a852c73beb9aa15f865ddaf138dfcdd06c23d0ea55c4a7bc01",
        "change_id": "fix-open-trace-producers",
        "head": "1da89bd4139ba93f50c1328748f0347f1800e497"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-open-last, merged into the primary branch at 57343c40a3e079f12918da8687c3610aaac0d4e7.",
      "evidence": [
        "merge commit 57343c40a3e079f12918da8687c3610aaac0d4e7",
        "task fix-open-last"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-04T04:09:49.775525+00:00"
    }
  ]
}
```
