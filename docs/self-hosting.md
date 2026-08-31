---
title: Developing Concorde with Concorde
sidebar_position: 8
---

# Developing Concorde with Concorde

Concorde is both a distributed framework and the project in which that framework is developed.
Self-hosting installs this checkout's maintained preset and extension into this same Spec Kit
project. That lets subsequent Concorde work exercise the current local workflow instead of an older
release or a set of manually maintained skills.

The normative behavior is [Feature 004](../specs/concorde/features/004-self-host/design.md).
The feature's <a href="/architecture/concorde-self-hosting-components.html">component view</a>
shows the authority flow: checked-in framework sources feed a review-first bootstrap, Spec Kit owns
component registration and active-integration materialization, and a receipt supports later drift
checks. Feature 003 remains the release-installation path for other projects.

## What is authoritative

The source side consists of:

- `presets/concorde/`, including normal-phase command modifications and template layers;
- `extensions/concorde/`, including Concorde commands, launchers, and runtime;
- `bundles/concorde-bundle/bundle.yml`, which pins the tested composition.

Copies beneath `.specify/presets/`, `.specify/extensions/`, the active integration's skill root, and
the composed `.specify/templates/` files are project materializations. Codex uses `.agents/skills/`;
Claude uses `.claude/skills/`. They are replaceable evidence, not sources to edit. Changes made only
to a materialized file are reported as drift and never flow back into the maintained framework.

## Supported integrations

Self-hosting protocol v1 supports the Codex and Claude skills integrations with Spec Kit 0.16.4.
The active value in `.specify/integration.json` selects the registry keys, owned skill root, surface
inventory, snapshot, rollback, and receipt evidence for one reviewed operation. An inactive
integration's assets remain outside that operation and are preserved.

Spec Kit's `preset remove` and forced `extension add` act on every agent recorded in its
registry, not only the active one. Apply therefore snapshots the inactive integration's Concorde
skill directories — and, for Claude, its extension link cache under
`.specify/extensions/concorde/.specify-dev/agent-commands/claude/` — together with the owned
scope and restores them byte-for-byte after Spec Kit has run, on success and on rollback.
Switching the active integration and applying again leaves the other integration's tree exactly
as it was; that tree stays unregistered, and status does not judge it, until its own reviewed
apply.

Codex materializes Concorde skills as regular files. Claude materializes preset skills as regular
files and may materialize development-mode extension skills as relative links into
`.specify/extensions/concorde/.specify-dev/agent-commands/claude/`. The bootstrap accepts only that
exact link target and Spec Kit's regular-file fallback; absolute, dangling, retargeted, escaping, or
otherwise undeclared links are drift and cannot pass verification.

## Why refresh is explicit

Spec Kit development mode copies local components and renders their active integration surfaces. It
does not create a live link to this checkout. After changing a preset command, extension command,
runtime, launcher, manifest, template, or bundle composition, generate and approve a new proposal.

The bootstrap also cannot prove that the already-running coding agent reloaded changed instructions.
Every successful apply therefore reports `reload_required`; start a new agent interaction or use the
integration's documented reload step before counting the change as active self-application.

## Preview the exact change

From the repository root:

```bash
uv run python scripts/development/self-host-concorde.py \
  --project-root . propose --format json
```

This is not an install. It validates the current component identities, versions, bundle
composition, Spec Kit version, active integration, source boundary, and symlink safety. It writes
only `.specify/self-hosting-proposal.json`, then prints:

- the digest of the complete authoritative source set;
- the local preset, extension, and bundle identities;
- every Concorde-owned path that would be created, updated, or adopted;
- the project content classes excluded from mutation; and
- the activation boundary.

Review the complete file. If any framework source, integration metadata, or planned owned state
changes after review, apply rejects the proposal as stale.

## Apply an approved proposal

Only after explicitly approving that exact proposal, run:

```bash
uv run python scripts/development/self-host-concorde.py \
  --project-root . apply \
  --proposal .specify/self-hosting-proposal.json \
  --format json
```

Apply first initializes an isolated Spec Kit project with the same active supported integration and
installs both components there through public `specify preset add --dev` and
`specify extension add --dev` operations. The real checkout is untouched if preflight fails.

After preflight, the bootstrap snapshots only the declared Concorde component copies, registry
entries/files, composed templates, active-integration Concorde/Spec Kit skill directories,
and prior receipt, plus the inactive integration's Concorde skill directories so they can be
restored unchanged after Spec Kit runs.
It delegates installation to Spec Kit, verifies installed bytes, normalized registrations, and all
declared surfaces, then atomically writes `.specify/self-hosting.json`. A failure restores that
scope; if restoration itself is incomplete, every residual path is named and success is not
recorded.

Both the proposal and receipt are ignored machine-local evidence. Do not commit them as durable
project intent.

## Refresh after improving the framework

Refresh uses the same propose/review/apply sequence. There is no separate unreviewed update path.
When sources are unchanged and all evidence matches, apply returns `unchanged` and does not duplicate
ownership or registrations. When sources changed, the new digest and affected paths appear in the
replacement proposal.

Locally edited materializations are not silently overwritten before review: status reports them as
drift, and the next proposal identifies the owned paths that refresh will replace.

## Check freshness without mutation

```bash
uv run python scripts/development/self-host-concorde.py \
  --project-root . status --format json
```

Status compares five independent dimensions:

| Dimension | Question answered |
|---|---|
| Source | Do maintained preset, extension, and bundle inputs match the accepted receipt? |
| Installed | Do copied preset and extension bytes match maintained sources and the receipt? |
| Registry | Do Spec Kit identities, versions, local provenance, priority, ownership, and command lists match? |
| Surfaces | Are all declared templates and active-integration skills present in their supported representation and unaltered, with no extra Concorde-owned skill? |
| Activation | Is a reload still required, externally evidenced, or unknown? |

The first four deterministic dimensions must match for overall `current`. Activation remains
separate. File equality never becomes a claim about what the running agent has loaded.

For a CI or milestone gate, require current deterministic state:

```bash
uv run python scripts/development/self-host-concorde.py \
  --project-root . status --require-current --format json
```

That command exits nonzero for absent, drifted, invalid, or unknown state. It does not require or
change the selected feature pointer and performs no writes.

## Safe recovery and troubleshooting

- `invalid` means source, host, proposal, path, compatibility, or review state failed before
  authorized mutation. Correct the finding and generate a new proposal.
- `failed` during preflight means the isolated install could not prove compatibility; the checkout
  was not mutated.
- `rolled_back` means a real-checkout failure occurred and the exact prior owned scope was restored.
- `failed` with rollback findings names residual paths that require manual restoration before retry.
- `drift` from status names the authority and dimension that disagrees. Do not edit the receipt to
  hide it; refresh from maintained sources or restore the affected installed state.

Use [Commands and installed surfaces](commands.md) for the installed agent-skill model and the
[Concorde workflow](concorde-workflow.md) for normal feature development after activation.
