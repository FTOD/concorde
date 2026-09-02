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
Concorde 2.1.0 packages 17 leaves and three Operation pairs, but installs exactly 18 public agent
skills: 15 public leaves plus the three Operations. Both internal planner leaves stay in the framework.

## 2. Initialize project architecture

Inside the target, invoke `$concorde-init` (Claude may present `/concorde-init`). The
leaf Skill invokes Concorde's native Profile 7 initializer Tool. Initialization Proposal 3 creates:

- `.concorde/config.json`
- `.concorde/reflections/log.md`
- `specs/<project>/architecture.md`
- `specs/<project>/diagrams/system-overview.json`

It creates no feature or attempt.

## 3. Create/select a feature

Choose a direct `features/<NNN-name>.md` beneath its providing module and invoke
`$concorde-specify <description>`. The first Protocol 13 response for a new file intentionally has no
stable feature/attempt ID. After the Skill writes valid front matter, it resolves again and persists
only `.concorde/feature.json` plus the returned requirements checklist path.

Use `$concorde-clarify` for material ambiguity and `$concorde-checklist` for reviewer-focused quality.

## 4. Plan and implement

```text
$concorde-plan          # public context → author Operation
$concorde-tasks
$concorde-analyze
$concorde-implement
$concorde-converge      # only when verified work remains
```

Planning/task/evidence artifacts live at `.concorde/attempts/<stable-feature-id>/`. Implementation
tasks explicitly reconcile every affected architecture, feature, source, test, documentation, and
projection authority. A task is complete only after passing evidence is recorded.

The planner reads provider feature bodies only for exact required-interface ownership and denies
provider internals. Each internal leaf gets a distinct default-deny Codex/Claude policy before
launch. Inspect without starting a model:

```bash
python3 .concorde/framework/operations/concorde-plan/operation.py \
  "Plan the selected change" --integration codex --describe-policy
```

Use `--execute` only with a supported native permission profile/strict sandbox or a verified
equivalent outer boundary. Tests inject process recorders; installation itself remains offline.

## 5. Explore alignment (optional)

The native explorer works without Understand Anything and returns bounded specification subjects with
unknown implementation status:

```bash
python3 .concorde/framework/scripts/concorde.py \
  --project-root . \
  explore feature.example.change
```

If the project has a UA graph, create/review an explicit schema-1 alignment sidecar, then bind it to
the expected implementation revision:

```bash
python3 .concorde/framework/scripts/concorde.py \
  --project-root . \
  explore feature.example.change \
  --graph .ua/knowledge-graph.json \
  --alignment evidence/alignment.json \
  --revision "$(git rev-parse HEAD)" \
  --status verified
```

This Tool is read-only and deterministic. It never infers verification from matching names or
paths; missing/stale/invalid evidence becomes unknown. See [Skill reference](skills.md#native-read-only-tool)
and [Ontology](ontology.md#alignment-exploration).

## 6. Validate and deliver

Run the installed native validator directly when useful:

```bash
python3 .concorde/framework/scripts/concorde.py --project-root . validate --format json
```

After tasks/checklists/evidence pass, invoke `$concorde-deliver`. It proposes and applies
Delivery Proposal 9, removing exactly the selected attempt while leaving durable sources/reflections
unchanged.

## 7. Update Concorde

Preview the new checkout/version against the existing target. Unchanged receipt-owned outputs can
update; unowned or user-modified collisions stop. Apply after review. A second identical apply is
`unchanged`.

For framework-development projections, see [Agent-surface maintenance](agent-surfaces.md).
