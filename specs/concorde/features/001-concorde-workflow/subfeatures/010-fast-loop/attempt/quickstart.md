# Quickstart: Validate Relaxed Fast-Loop Eligibility

Run from the repository root with the Feature 010 selection active.

## 1. Validate canonical workspace routing

```bash
.venv/bin/python .specify/extensions/concorde/scripts/python/workspace.py --phase fast-loop
```

Expected: Protocol v8 status `resolved` or `selected`; `phase_root` is the selected anchor feature
root. Resolve a second explicit existing feature with `--feature-directory <root>` to prove the same
adapter can validate each affected root without changing the one-pointer selection model.

## 2. Run command-policy contract tests

```bash
.venv/bin/python -m unittest \
  tests.concorde.contract.test_agent_commands \
  tests.concorde.contract.test_installed_command_surfaces \
  tests.concorde.contract.test_manifests \
  tests.concorde.acceptance.test_installed_slash_workflow \
  tests.concorde.acceptance.test_self_hosted_checkout
```

Expected: the canonical command requires an anchor plus complete affected set, permits bounded
cross-feature and contract-format reconciliation, rejects changed module responsibilities,
dependencies, and whole-project user compatibility/migration policy, and requires architecture
review state. Installed Codex/Claude surfaces preserve equivalent intent.

## 3. Validate package and self-host projections

```bash
uv run python scripts/release/build-components.py --output dist
uv run python scripts/release/verify-release.py --dist dist
.venv/bin/python scripts/development/self-host-concorde.py status --require-current
```

Expected: packaged sources contain the revised command; the active installed projection is current.
The build output is generated evidence and is not committed.

## 4. Run deterministic source and documentation gates

```bash
.venv/bin/python .specify/extensions/concorde/scripts/python/concorde.py validate --format json
cd docsite
npm run check
```

Expected: Concorde validation has zero errors; docsite type checks, tests, source validation, and
production build pass.

## 5. Inspect policy-specific source consistency

Confirm that no maintained source still says all cross-feature, contract, diagram, or internal-format
changes are automatically ineligible. Confirm every source still rejects module responsibility,
dependency-direction, whole-project user compatibility/migration policy, unsafe worktree, missing
accepted realization, active attempt, and materially ambiguous changes.

If maintained architecture sources changed during an actual fast-loop validation scenario, confirm
the result remains `review_pending` until the maintainer reviews the exact validated diff.
