---
name: concorde-plan
description: Run permission-bounded context resolution and temporal plan authorship in order.
exposure: public
operation: operation.py
capabilities:
  - concorde-plan-context
  - concorde-plan-author
---

# Concorde Plan Operation

Treat `$ARGUMENTS` as one complete planning request. Use the paired graph at `{OPERATION}` as the
execution authority for exactly `context -> author`. The public Operation retains the stable
`concorde-plan` identity; its two implementation leaves are internal and must never be invoked or
projected as alternative user capabilities. The trusted host resolves Workspace Protocol 13 before
the first leaf and binds its concrete paths into both native launch policies.

To inspect concrete policies without starting a model, run:

```bash
{OPERATION} "$ARGUMENTS" --framework-prefix {FRAMEWORK} --integration codex --describe-policy
```

Claude uses `--integration claude`. Real execution uses `--execute` and requires a supported native
permission profile/sandbox or a verified equivalently narrow outer sandbox.

The context leaf is read-only and returns the exact selected/module/provider-interface receipt. The
author leaf receives that prior result and may write only the selected attempt plus an authorized
authorized per-file reflection state. A context, policy, enforcement, or executor failure stops authorship;
the Operation never falls back to ambient repository access.
