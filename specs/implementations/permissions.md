```concorde-document
{
  "id": "document.implementation.permissions",
  "targets": [
    "implementation.permissions"
  ],
  "main_visible": false
}
```
# Permissions implementation

`implementation.permissions` follows Spec Protocol 2.1.0 and binds the exact files below. It is reused by `module.harness`.

## Responsibility

Realize immutable policy records, authority intersection and integration-specific launch configuration.

## Bound files

- `src/concorde/host/permissions.py`
- `tests/concorde/host/unit/test_permissions.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/host/permissions.py` | Intersects effects with exact host-provided paths and renders reproducible native enforcement. Implementation Spec documents are writable only in a code-writing grant; Module Specs are excluded. |

## Implementation interfaces, dependencies and constraints

compile_policy maps effect-role names to explicit caller-bound paths and creates a canonical policy digest. Native renderers produce the requested Codex/Claude enforcement shape; finalization binds an attested executable bootstrap without enlarging task authority. Dependencies are typed safe-path/serialization contracts and trusted host admission of role paths and any outer sandbox. The compiler does not resolve contexts or schedule Agents. Returned configuration objects must describe the effective boundary, including disabled native delegation, rather than just the requested boundary.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Permission tests must reject widened reads/writes/network/credentials, unknown roles, unsafe paths and missing outer enforcement. Compare effective native boundaries, verify bootstrap digest changes and assert empty write authority for Spec and code reviewers.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
