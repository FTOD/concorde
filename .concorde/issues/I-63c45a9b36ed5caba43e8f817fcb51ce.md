# I-63c45a9b36ed5caba43e8f817fcb51ce

```json
{
  "schema_version": 4,
  "id": "I-63c45a9b36ed5caba43e8f817fcb51ce",
  "status": "open",
  "reports": [
    {
      "id": "sha256:bbd1416e2f2b9a24c5205b987c55bcfef5b61cba5bda350297f952fcd03527fc",
      "created_at": "2026-10-23T09:32:32.945982+00:00",
      "report": {
        "report_key": "shared-json-tmp-writes",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Progress and run-state files are written through one shared .json.tmp path",
        "description": "Task r4-kernel-tracing fixed I-986b963e (Kernel binding writes sharing one temporary file, which can break atomic publication when two writers overlap) by giving each write its own mkstemp file, fsynced then renamed. It reports the same shared `<file>.json.tmp` pattern in src/concorde/worker_harness/progress.py (around line 74) and src/concorde/execution/runner.py (around line 990), outside its Modules. Apply the same fix there.",
        "impact": "Two overlapping writers of a worker progress file or a run's status file can publish a torn or wrong file, or fail a rename.",
        "basis": "Task r4-kernel-tracing report 3 (2026-10-23) and the fix of I-986b963e.",
        "owner_target_id": "module.execution",
        "evidence": [
          {
            "path": "src/concorde/execution/runner.py",
            "description": "shared .json.tmp write"
          },
          {
            "path": "src/concorde/worker_harness/progress.py",
            "description": "shared .json.tmp write"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-e4e2e0a7-b129-494c-a73e-2c2961a48fa6",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.execution",
        "context_id": "sha256:3d0d125f3ea826ecf9f02f9ff73e11fa4a98782eeb462e9b63bffff8c59ced7c",
        "change_id": null,
        "head": "05e182592fe70b78053b6c1440af97ae51af601f"
      }
    }
  ],
  "dispositions": []
}
```
