```concorde-document
{
  "id": "document.module.file-transactions",
  "targets": [
    "module.file-transactions"
  ],
  "main_visible": true
}
```

# File transactions

## api.files.apply

file_change(root,relative,content) captures the exact original digest or null for a new path. apply_files(root,changes,allowed,verify=None) rejects duplicate/unsafe/out-of-grant paths and stale before-digests, stages replacements, rechecks each original immediately before replacing and invokes target-state verification. Failure attempts to restore prior bytes and remove newly created files; an I/O failure during recovery propagates and cannot be reported as applied. Return the applied project-relative paths. No arbitrary directory deletion or symlink traversal is allowed. The caller owns the authorization set; proposed content cannot enlarge it.

## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of changes:

```text
file_change(root: Path, path: str, content: str) -> dict
apply_files(root: Path, changes: list[dict], allowed: set[str], *, verify=None) -> list[str]
```

## Values, errors and compatibility

`file_change` returns exactly `{path: str, before_digest: str|null, content: str}`. `path` is a
canonical project-relative POSIX file path; `before_digest` is `sha256:` plus 64 lowercase hex digits
for existing bytes, or null for required absence. `content` is UTF-8 replacement text, including
empty text; this API has no deletion record. `root` is a trusted caller-selected project directory.
The call reads existing bytes and does not write files.

`apply_files` requires a nonempty list of distinct complete change records and a separate allowed
set of exact paths. It returns applied paths in input order only after all replacements and, when
provided, `verify()` complete without raising. The callback takes no arguments; its return value
is ignored. A false return value is not rejection: the callback must raise on invalid final state.
The transaction can create missing parent directories; successful file rollback may leave empty
parents. It does not promise to preserve file modes or recover after process termination.

Empty/duplicate changes or non-string content raise `SpecError/invalid_proposal`. A complete record
outside the allowed set, or one with unexpected fields, raises `SpecError/permission_denied`.
Changed original bytes raise `SpecError/stale_proposal`. Unsafe paths propagate `TypedDataError`;
filesystem and verification exceptions propagate after attempted recovery. Callers supply shaped
records; this low-level helper is not an arbitrary untyped JSON admission interface.

The caller must prevent concurrent writes to transaction-owned paths through application and
recovery. A successful proposal cannot be replayed with its old before-digests; obtain current
records for a later mutation. After failure, inspect current state and resolve any recovery error
before retrying. The applied-path list is completion evidence for this call, not a durable receipt.

```python
proposal = file_change(root, "specs/project/module.md", replacement_markdown)
# The trusted verifier raises if the final repository is invalid.
applied = apply_files(root, [proposal], {"specs/project/module.md"}, verify=verify_repository)
```

The local Module dependency declarations supply the safe-path, exact-file read and digest promises
needed by this API. Those helpers convey no additional write authority.
