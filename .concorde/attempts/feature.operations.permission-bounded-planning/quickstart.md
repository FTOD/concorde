# Quickstart: Inspect and Execute a Bounded Plan Operation

## Validate the package and selected context

```bash
uv run python scripts/concorde.py validate feature.operations.permission-bounded-planning --format json
uv run python scripts/workspace.py --phase plan
```

## Describe the real nested graph and native policies without credentials

```bash
uv run python operations/concorde-plan/operation.py \
  "Plan the selected change" \
  --framework-prefix . \
  --integration codex \
  --describe-policy

uv run python operations/concorde-plan/operation.py \
  "Plan the selected change" \
  --framework-prefix . \
  --integration claude \
  --describe-policy
```

Expected: both results contain `context -> author`, the same normalized path-policy digest/effective
sets, integration-native configuration, no network, and no model process launch.

## Execute through the host boundary

```bash
uv run python operations/concorde-plan/operation.py \
  "Plan the selected change" \
  --framework-prefix . \
  --integration codex \
  --execute
```

Claude uses `--integration claude`. Execution requires the corresponding authenticated CLI and a
supported native sandbox or an explicitly configured outer sandbox. Missing enforcement fails before
the first agent starts.

## Focused evidence

```bash
uv run python -m unittest \
  tests.concorde.unit.test_operation_permissions \
  tests.concorde.unit.test_skill_assets \
  tests.concorde.unit.test_capability_validation \
  tests.concorde.unit.test_feature_workspace \
  tests.concorde.integration.test_plan_operation \
  tests.concorde.integration.test_standard_dev_loop_operation \
  tests.concorde.integration.test_reflections_triage_operation
```

No acceptance test invokes a paid/live model. Process-launch tests inject a recorder and verify exact
argv/settings/policy/receipt behavior.
