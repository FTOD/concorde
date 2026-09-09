```concorde-document
{
  "id": "document.specs.implementations.file-transactions",
  "targets": [
    "implementation.file-transactions"
  ],
  "main_visible": false
}
```

# File Transactions implementation

`implementation.file-transactions` follows Spec Protocol 2.0.0 and binds the exact files below. It is reused by `module.file-transactions`.

## Responsibility

Realize exact replacement proposals as staged filesystem operations with original-byte recovery.

## Bound files

- `src/concorde/specification/changes.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/specification/changes.py` | Captures before-digests, stages exact replacements, rechecks inputs and restores prior bytes on failure. |

## Implementation interfaces, dependencies and constraints

file_change captures path/content and the current digest or missing-file precondition; apply_files consumes those records and a caller-owned allowed set. Its dependencies are filesystem operations, digest calculation and an optional trusted verification callback. It retains original bytes separately from staged replacements, rejects duplicate/unsafe destinations, and rechecks originals before replacement. Only a completed verification yields the applied-path list. A failed write or verifier initiates recovery; a recovery I/O error must not be hidden as success. No process-crash durability or general concurrent-writer isolation is implied.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Exercise absent/existing files, duplicate and out-of-grant paths, stale before-digests, failure after an earlier replacement and a failing verifier. Recovery cases must compare the actual previous bytes and absence states; include recovery I/O failure as an explicit failed outcome. Use the specification transaction/initialization cases that exercise this shared helper.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
