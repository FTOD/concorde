```concorde-document
{
  "id": "document.implementation.file-transactions",
  "targets": [
    "implementation.file-transactions"
  ],
  "main_visible": false
}
```

# File transactions implementation

`implementation.file-transactions` follows Spec Protocol 2.1.0 and binds the exact files below. It is reused by `module.spec`, `module.development`, `module.reflections`, `module.views`.

## Responsibility

Realize exact replacement proposals as staged filesystem operations with before-digest checks and original-byte recovery, for every Module that applies an accepted proposal.

## Bound files

- `src/concorde/specification/changes.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/specification/changes.py` | Captures before-digests, stages exact replacements, rechecks inputs and restores prior bytes on failure. |

## Interface

```text
file_change(root: Path, path: str, content: str) -> dict
apply_files(root: Path, changes: list[dict], allowed: set[str], *, verify=None) -> list[str]
```

`file_change` returns exactly `{path: str, before_digest: str|null, content: str}`. `path` is a canonical project-relative POSIX file path; `before_digest` is `sha256:` plus 64 lowercase hex digits for existing bytes, or null for required absence. `content` is UTF-8 replacement text, including empty text; this API has no deletion record. `root` is a trusted caller-selected project directory. The call reads existing bytes and does not write files.

`apply_files` requires a nonempty list of distinct complete change records and a separate allowed set of exact paths. It rejects duplicate, unsafe or out-of-grant paths and stale before-digests, stages replacements, rechecks each original immediately before replacing it and invokes the optional `verify()` callback. It returns applied paths in input order only after all replacements and verification complete without raising. The callback takes no arguments and its return value is ignored; it must raise to reject the final state. Failure attempts to restore prior bytes and remove newly created files; an I/O failure during recovery propagates and cannot be reported as applied. The transaction may create missing parent directories, and a successful rollback may leave empty parents. It promises neither file-mode preservation, crash durability nor isolation from arbitrary concurrent writers; the caller owns exclusive access to the affected paths during application and recovery.

Empty or duplicate changes and non-string content raise `SpecError/invalid_proposal`. A record outside the allowed set, or one with unexpected fields, raises `SpecError/permission_denied`. Changed original bytes raise `SpecError/stale_proposal`. Unsafe paths propagate `TypedDataError`; filesystem and verification exceptions propagate after attempted recovery. A successful proposal cannot be replayed with its old before-digests; obtain current records for a later mutation. The applied-path list is completion evidence for this call, not a durable receipt.

```python
proposal = file_change(root, "specs/project/module.md", replacement_markdown)
# The trusted verifier raises if the final repository is invalid.
applied = apply_files(root, [proposal], {"specs/project/module.md"}, verify=verify_repository)
```

## Implementation interfaces, dependencies and constraints

Dependencies are the typed-value safe-path helper, exact regular-file reads, digest calculation and an optional trusted verification callback. The helper retains original bytes separately from staged replacements. Proposed content cannot enlarge the caller's allowed set, and no path helper conveys write authority.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Exercise absent and existing files, duplicate and out-of-grant paths, stale before-digests, failure after an earlier replacement and a failing verifier. Recovery cases must compare the actual previous bytes and absence states and include recovery I/O failure as an explicit failed outcome.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
