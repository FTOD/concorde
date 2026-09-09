```concorde-document
{
  "id": "document.specs.modules.concorde.file-transactions.architecture",
  "targets": [
    "module.file-transactions"
  ],
  "main_visible": true
}
```

# Architecture

file_change captures a current before-digest. apply_files accepts exact allowed paths, stages changes, rechecks originals and invokes verification. A stale, invalid or failed application restores prior bytes and removes newly created files. Proposed content cannot expand the allowed set.

## Internal domain

Apply exact multi-file changes with before-digest checks and rollback. Inputs, results, state/effects and failure behavior are defined in this collection's feature and interface contracts. Private implementation files are described separately by their authoritative Implementation Specs.

## Dependencies

No internal Module dependency is required by this boundary. External inputs and interfaces are specified locally.
