# Self-hosting Concorde

Self-hosting materializes this checkout's canonical package sources into the same checkout for Spec
Kit, Codex, and Claude acceptance. It is review-first, scoped, atomic, and reversible on failure.

## Source and projection boundary

Authoritative distribution sources:

- `presets/concorde/`
- `extensions/concorde/`
- `bundles/concorde-bundle/`

Installed projections:

- `.specify/presets/concorde/`
- `.specify/extensions/concorde/`
- composed `.specify/templates/`
- `.agents/skills/` or `.claude/skills/`
- integration-specific reflection-triage roles

Always edit canonical sources first. Self-hosting uses Spec Kit's public component lifecycle to
materialize projections and then verifies them. It does not treat installed copies as an edit
baseline.

## Propose, apply, verify

```bash
uv run python scripts/development/self-host-concorde.py --project-root . propose --format json
uv run python scripts/development/self-host-concorde.py --project-root . \
  apply --proposal .specify/self-hosting-proposal.json --format json
uv run python scripts/development/self-host-concorde.py --project-root . \
  status --require-current --format json
```

Proposal mode inventories canonical preset/extension/bundle content, versions, active integration,
registered command ownership, exact projected paths, preserved classes, and source digest. It writes
only the proposal.

Apply rejects a changed or ineligible proposal, preflights installation in an isolated project,
snapshots the exact owned surface plus inactive-integration surfaces, refreshes through Spec Kit,
reconciles agent assets, restores inactive projections, verifies the result, and writes a receipt.
Any failure rolls the exact scope back; residual rollback failures are reported by path.

## Freshness dimensions

Status compares:

| Dimension | Evidence |
|---|---|
| Source | Canonical preset/extension/bundle inventory digest. |
| Installed | Installed component bytes equal canonical bytes and receipt. |
| Registry | Normalized component ownership/version/priority/commands equal expected composition. |
| Surfaces | Composed templates, all command skills, extension commands, and agent assets equal receipt. |
| Protocol | Every installed phase advertises Protocol 12, delivery advertises Proposal 8, and reflection agent assets advertise reflection-triage/v3. |
| Removal | Obsolete feature-document templates are absent from canonical and installed surfaces. |
| Activation | On-disk current; agent reload still required after changes. |

Source-only improvements must be preserved when canonical and installed guidance already differ:
reconcile canonical content deliberately, then regenerate. Never copy an older installed command over
newer canonical diagram output-boundary, uniqueness, or freshness checks.

## Preserved state

Self-hosting preserves project-authored `.concorde/config.json`, stable-ID attempts,
`.concorde/reflections/log.md`, reflection-triage configuration/scratch state, module architectures,
direct feature files/interfaces, code, tests, docs, generated evidence, unrelated integrations/agent
assets, and inactive integration projections. Receipt-managed agent assets are updated or removed
only while their observed digest matches ownership evidence.

## Common failures

- unsupported Spec Kit/integration: use the pinned supported versions or add isolated compatibility
  evidence before expanding support;
- command collision: resolve component ownership before proposing;
- installed/source drift: generate and review a fresh proposal;
- stale workspace/reflection protocol marker or obsolete template: recompose through the public lifecycle;
- modified receipt-owned agent file: reconcile the ownership conflict explicitly; and
- activation pending: restart/reload the coding agent after a successful apply.
