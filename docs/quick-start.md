# Quick start

## Prerequisites

- Python 3.11+
- Git
- Codex or Claude project integration

Concorde needs no host specification framework and no network access when installing from a checkout.

## 1. Preview installation

From the Concorde checkout:

```bash
python3 scripts/install-concorde.py \
  --target ../my-project \
  --integration codex
```

Preview is the default and writes nothing. Review every create/adopt/update/remove/conflict action,
role, and digest. Apply only a conflict-free accepted plan:

```bash
python3 scripts/install-concorde.py \
  --target ../my-project \
  --integration codex \
  --apply
```

Use `--integration claude` for Claude. Installed framework bytes live at `.concorde/framework/`;
ownership lives at `.concorde/install.json`.

## 2. Initialize project architecture

Inside the target, invoke `$speckit-concorde-init` (Claude may present `/speckit-concorde-init`). The
compatibility name now runs Concorde's native Profile 7 initializer. Initialization Proposal 2 creates:

- `.concorde/config.json`
- `.concorde/reflections/log.md`
- `specs/<project>/architecture.md`

It creates no feature or attempt.

## 3. Create/select a feature

Choose a direct `features/<NNN-name>.md` beneath its providing module and invoke
`$speckit-specify <description>`. The first Protocol 12 response for a new file intentionally has no
stable feature/attempt ID. After the command writes valid front matter, it resolves again and persists
only `.concorde/feature.json` plus the returned requirements checklist path.

Use `$speckit-clarify` for material ambiguity and `$speckit-checklist` for reviewer-focused quality.

## 4. Plan and implement

```text
$speckit-plan
$speckit-tasks
$speckit-analyze
$speckit-implement
$speckit-converge      # only when verified work remains
```

Planning/task/evidence artifacts live at `.concorde/attempts/<stable-feature-id>/`. Implementation
tasks explicitly reconcile every affected architecture, feature, source, test, documentation, and
projection authority. A task is complete only after passing evidence is recorded.

## 5. Validate and deliver

Run the installed native validator directly when useful:

```bash
python3 .concorde/framework/scripts/concorde.py --project-root . validate --format json
```

After tasks/checklists/evidence pass, invoke `$speckit-concorde-deliver`. It proposes and applies
Delivery Proposal 8, removing exactly the selected attempt while leaving durable sources/reflections
unchanged.

## 6. Update Concorde

Preview the new checkout/version against the existing target. Unchanged receipt-owned outputs can
update; unowned or user-modified collisions stop. Apply after review. A second identical apply is
`unchanged`.

For framework-development projections, see [Agent-surface maintenance](agent-surfaces.md).
