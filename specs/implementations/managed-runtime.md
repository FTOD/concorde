```concorde-document
{
  "id": "document.implementation.managed-runtime",
  "targets": [
    "implementation.managed-runtime"
  ],
  "main_visible": false
}
```
# Managed Runtime implementation

`implementation.managed-runtime` follows Spec Protocol 2.1.0 and binds the exact files below. It is reused by `module.distribution`.

## Responsibility

Realize locked Python and official viewer provisioning with staged artifacts and identity receipts.

## Bound files

- `src/concorde/distribution/managed_runtime.py`
- `tests/concorde/support/managed_runtime.py`
- `viewer/README.md`
- `viewer/package-lock.json`
- `viewer/package.json`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/distribution/managed_runtime.py` | Plans, stages and verifies the locked Python and viewer runtimes with recoverable receipts. |
| `viewer/` | Pins the official viewer package input independently of graph content. |

## Implementation interfaces, dependencies and constraints

load_runtime_spec admits pinned inputs; plan_runtime compares the existing receipt; provision_runtime stages the selected action and returns accepted runtime metadata. Dependencies are the locked package inputs, bootstrap Python, package acquisition tools and filesystem operations. The viewer package lock and manifest remain independent from project graph bytes. A verified existing runtime can be reused; incomplete or mismatched artifacts cannot be accepted. The support fixture supplies controlled artifacts for installation tests and must not turn a mocked acquisition into real provisioning evidence.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Exercise exact lock/version/hash agreement, verified reuse, missing Python, invalid viewer identity, interrupted acquisition and restoration of a previous runtime through distribution tests. A fresh-environment acceptance case must distinguish missing prerequisites from a successful provision.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
