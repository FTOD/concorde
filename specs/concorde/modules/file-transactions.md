# File transactions

## api.files.apply

file_change(root,relative,content) captures the exact original digest or null for a new path. apply_files(root,changes,allowed,verify=None) rejects duplicate/unsafe/out-of-grant paths and stale before-digests, stages replacements, rechecks each original immediately before replacing and invokes target-state verification. Failure restores prior bytes and removes newly created files. Return the applied project-relative paths. No arbitrary directory deletion or symlink traversal is allowed. The caller owns the authorization set; proposed content cannot enlarge it.

## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of changes:

```text
file_change(root: Path, path: str, content: str) -> dict
apply_files(root: Path, changes: list[dict], allowed: set[str], *, verify=None) -> list[str]
```

Failures return structured findings or the declared exception; callers must stop the affected transition. Repeating an unchanged read is side-effect free. Mutations require current preconditions and explicit caller-owned paths. Local contract facts above remain authoritative without reading the parent or collaborating Specs.
