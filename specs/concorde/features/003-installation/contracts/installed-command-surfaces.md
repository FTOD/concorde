# Interface Profile: Installed Concorde Command Surfaces

**Profile ID**: `profile.feature003.installed-command-surfaces`  
**Representation**: Spec Kit 0.16.4 preset command Markdown and extension command definitions,
materialized by the active coding-agent integration

This feature-local profile specializes the canonical Spec Kit platform, workflow-composition,
agent-skills, and Feature Workspace contracts. It does not create a second command protocol or make
Feature 003 authoritative for Feature 001 workflow semantics.

## Purpose

Define what a Concorde release must install, which component owns each command surface, when selected
workspace resolution must occur, and what evidence proves that the installed winner behaves as
specified.

## Authority Boundary

| Fact | Authority |
|---|---|
| Selected feature, durable/temporal paths, command intent, results, and failures | Feature 001 Feature Workspace and agent-command contracts |
| Normal phase responsibility and public composition/materialization behavior | Spec Kit 0.16.4 |
| Template and command contribution strategy | `concorde` preset manifest |
| Five active command surfaces, canonical triage assets, queue/projector support | `concorde` extension manifest and Feature 005 contract |
| Agent-specific command and custom-agent syntax | Active coding-agent integration plus Concorde projection manifest |
| Installed winner, package version, source/materialized digests, and execution evidence | Spec Kit state plus generated Feature 003 acceptance receipts |

Feature 003 may package and render the Feature 001 handoff but must not reinterpret it. Every
Concorde-owned installed surface and validation receipt identifies the exact handoff version and
digest.

## Required Inventory

### Existing normal lifecycle surfaces

| Phase root | Canonical command IDs | Required preset strategy |
|---|---|---|
| Durable feature intent plus temporal review state | `speckit.specify`, `speckit.clarify` | Complete layer using `strategy: replace` for each command |
| Temporal `attempt/` workspace | `speckit.checklist`, `speckit.plan`, `speckit.tasks`, `speckit.implement`, `speckit.analyze`, `speckit.converge`, `speckit.taskstoissues` | Complete layer using `strategy: replace` for each command |

Each modification preserves the corresponding Spec Kit 0.16.4 phase responsibility. Its complete
instruction layer must invoke the installed selected-workspace adapter before any setup, prerequisite check, inherited instruction,
or artifact access that could choose a legacy root-level plan or task path.

`append`, `prepend`, and `wrap` are non-conforming for these nine command entries while the lower
command can independently resolve legacy paths. The three spec/plan/tasks template contributions
remain `append` layers because they add guidance and do not perform phase routing. The Concorde-only
`abstract-template` (the feature abstract that `speckit.specify` authors at a new feature root) and
`implementation-template` (the placeholder feature `design.md`; preset 0.2.0 had called it
`implementation-template`) are `replace` contributions because Spec Kit core does not define those
artifacts; both are reached through `specify preset resolve` and have no composed mirror.

Preset script mutation and installer mutation of managed `.specify/scripts/` are outside the
supported contract. If public command composition cannot satisfy the bootstrap ordering, the release
must reject the host version and require an upstream-supported capability instead of patching it.

### Concorde-specific surfaces

The extension supplies these five canonical intents:

1. `speckit.concorde.init`
2. `speckit.concorde.deliver`
3. `speckit.concorde.context`
4. `speckit.concorde.validate`
5. `speckit.concorde.ask`

Feature creation and selection are not Concorde intents: a root is created through the normal
`speckit.specify` phase with `SPECIFY_FEATURE_DIRECTORY` at its canonical path and selected through
the standard `.specify/feature.json` record, which the extension's workspace adapter resolves and
validates before every normal phase.

Platform-safe spellings may vary in the materialized presentation. Arguments, workspace effects,
failures, and semantics must remain equivalent. The first four intents are runtime-backed operations
with deterministic result envelopes. `ask` is an agent-followed Markdown procedure that requires
installed-source grounding, citations, bounded project context, explicit uncertainty, and
non-mutation without a launcher or runtime verb. Every launcher, adapter, schema, and runtime file
referenced by an operational command must be present in the extension archive and resolved relative
to the installed extension, never the Concorde checkout.

### Reflection-triage agent surfaces

The extension additionally ships canonical support assets, not a sixth command. Installation renders
exactly three native outputs for the selected integration: the `reflections-triage` skill,
`reflection-investigator`, and `reflection-implementer`. Claude uses `.claude/skills` and
`.claude/agents`; Codex uses `.agents/skills` and `.codex/agents` TOML. Both projections expose the
same four actions, route/plan vocabulary, shared `.concorde/reflections/` state, installed queue
helper, read-only investigator, assigned-worktree implementer, and maintainer-owned merge/log status.
They pin no mandatory model and contain no Concorde checkout path.

The projector records path/digest ownership in `.specify/concorde-agent-assets.json`. Update/removal
may alter a projected path only while its digest matches that receipt. Shared config, plans,
worktrees, logs, inactive integration surfaces, unrelated files, modified projections, and user
permission settings are preserved.

## Resolution and Materialization

For every target project, Spec Kit must:

1. resolve the accepted preset and extension versions;
2. compose template and command layers according to their manifests and active priority;
3. identify the winning source for each affected command;
4. materialize the winner through the target's active coding-agent integration;
5. record enough ownership/provenance to verify, update, disable, reprioritize, and remove it safely.

The integration owns presentation syntax only. Matching text in a non-winning source file or an
unregistered package member is not an installed command surface.

## Observable Path Matrix

| Command | Required selected paths | Prohibited result |
|---|---|---|
| Specify / clarify | Feature-root `abstract.md` and `design.md` (authored), seeded placeholder `implementation.md`, and `contracts/`; generated review state at `attempt/checklists/requirements.md` | A second design/contract or root `checklists/` directory |
| Checklist | Durable feature context plus `attempt/checklists/*.md` output and available attempt context | A root checklist, implementation behavior test, or second active attempt |
| Plan | `attempt/plan.md`, `research.md`, `data-model.md`, `quickstart.md` (reading root `design.md`/`implementation.md` and module summary as baseline) | Root `plan.md`, root temporal copies, or writes to durable files |
| Tasks | `attempt/tasks.md` | Root `tasks.md` |
| Implement / analyze / converge / taskstoissues | Feature-root durable intent plus the same active `attempt/` attempt | Root temporal copies, symlinks, or a second active attempt |
| Init / context / validate | Feature 001 contract paths and result envelopes | Checkout-relative runtime or agent-specific semantic drift |
| Deliver | Root trio, module summary/design, completed tasks/checklists, returned proposal metadata, digest-bound proposal v7 (candidate feature `implementation.md`, optional module `design.md` amendment), exact `attempt/` removal | Derived paths, wrong targets, unchecked work, an absent user invocation, stale apply, or broader deletion |
| Ask | Installed extension/preset guidance plus the smallest relevant bounded maintained project sources | Launcher/runtime invocation, checkout dependency, uncited facts, unrelated deeper context, mutation, or implicit lifecycle work |
| Reflection triage | Installed canonical agent bodies/wrappers, shared config/queue/plans, and explicit implementer worktrees | Checkout dependency, duplicate platform queue, model pin, permission overwrite, main-checkout parallel writes, or automatic log status changes |

## Acceptance Evidence

Acceptance must run from built release artifacts in a target outside the Concorde checkout. For each
of the fifteen command surfaces and the selected integration's three triage outputs it must:

1. identify the active registered artifact and winning source package;
2. record source, materialized, package, and Feature 001 handoff digests;
3. execute the installed workspace/bootstrap path before phase behavior where that surface has one;
4. exercise the bounded phase outcome or Concorde operation, or inspect and semantically review the
   agent-only question procedure;
5. record selected feature root, implementation root, accessed/output paths, exit status, and
   checkout access;
6. compare command behavior and triage semantics across Claude and Codex;
7. parse native agent metadata and verify receipt/source/materialized digests.

For an eligible installed delivery proposal, delivery also records the runtime-returned
`proposal_path`, `task_summary`, and `checklist_summary`. The proposal path must be exactly
`<workspace.attempt_dir>/deliver-proposal.json`; installed agents must consume it without
derivation, and apply must revalidate both summaries before mutation.

Acceptance fails on any checkout read, missing required archive member, wrong winner, late workspace
resolution, root checklist or other compatibility copy/symlink, mismatched handoff digest, or
presentation-specific semantic difference. Generated receipts are evidence, not a new public
interface.

## Registry State, Recomposition, and Removal

With a known lower-priority command layer installed, disabling or reprioritizing the `concorde` preset
changes future resolution but leaves already registered commands active, matching Spec Kit 0.16.4's
documented lifecycle. Updating must materialize the accepted updated layer. Removing must recompose
and materialize the next surviving winner for all nine normal commands. No stale Concorde
instructions may remain, and removal must not delete shared components, unrelated registered
commands, project configuration, shared triage state, inactive/customized agent files, `.concorde/`,
`specs/`, or `docs/` content.

## Compatibility and Change Control

This profile supports Spec Kit 0.16.4 only. A later version is supported only after every complete command layer
is reviewed against that version's phase inputs, outputs, hooks, prerequisites, failures, and
registration behavior, followed by the full isolated path and recomposition matrices.

A change to the nine-plus-fast-loop/five-command/three-triage inventory, bootstrap order,
durable/temporal path split, projection ownership, or stable intent is a contract change and requires
synchronized Feature 001/005 handoff, manifests, catalogs, diagrams, tests, and evidence.
