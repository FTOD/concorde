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
| Template and command contribution strategy | `concorde-core` preset manifest |
| Seven active command surfaces and four runtime/adapter scripts | `concorde` extension manifest |
| Agent-specific filename and invocation syntax | Active coding-agent integration |
| Installed winner, package version, source/materialized digests, and execution evidence | Spec Kit state plus generated Feature 003 acceptance receipts |

Feature 003 may package and render the Feature 001 handoff but must not reinterpret it. Every
Concorde-owned installed surface and validation receipt identifies the exact handoff version and
digest.

## Required Inventory

### Existing normal lifecycle surfaces

| Phase root | Canonical command IDs | Required preset strategy |
|---|---|---|
| Durable feature intent plus temporal review state | `speckit.specify`, `speckit.clarify` | Complete `replace` layer for each command |
| Temporal `implementation/` workspace | `speckit.checklist`, `speckit.plan`, `speckit.tasks`, `speckit.implement`, `speckit.analyze`, `speckit.converge`, `speckit.taskstoissues` | Complete `replace` layer for each command |

Each replacement preserves the corresponding Spec Kit 0.16.4 phase responsibility. It must invoke
the installed selected-workspace adapter before any setup, prerequisite check, inherited instruction,
or artifact access that could choose a legacy root-level plan or task path.

`append`, `prepend`, and `wrap` are non-conforming for these nine command entries while the lower
command can independently resolve legacy paths. The three spec/plan/tasks template contributions
remain `append` layers because they add guidance and do not perform phase routing. The Concorde-only
`design-template` is a fourth, `replace` contribution because Spec Kit core does not define that artifact.

Preset script replacement and installer mutation of managed `.specify/scripts/` are outside the
supported contract. If public command replacement cannot satisfy the bootstrap ordering, the release
must reject the host version and require an upstream-supported capability instead of patching it.

### Concorde-specific surfaces

The extension supplies these seven canonical intents:

1. `speckit.concorde.init`
2. `speckit.concorde.feature.create`
3. `speckit.concorde.feature.select`
4. `speckit.concorde.feature.harden`
5. `speckit.concorde.context`
6. `speckit.concorde.validate`
7. `speckit.concorde.ask`

Platform-safe spellings may vary in the materialized presentation. Arguments, workspace effects,
failures, and semantics must remain equivalent. The first six intents are runtime-backed operations
with deterministic result envelopes. `ask` is an agent-followed Markdown procedure that requires
installed-source grounding, citations, bounded project context, explicit uncertainty, and
non-mutation without a launcher or runtime verb. Every launcher, adapter, schema, and runtime file
referenced by an operational command must be present in the extension archive and resolved relative
to the installed extension, never the Concorde checkout.

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
| Specify / clarify | Feature-root `spec.md` and `contracts/`; generated review state at `implementation/checklists/requirements.md` | A second spec/contract or a root `checklists/` directory |
| Checklist | Durable feature context plus `implementation/checklists/*.md` output and available attempt context | A root checklist, implementation behavior test, or second active attempt |
| Plan | `implementation/plan.md`, `research.md`, `data-model.md`, `quickstart.md` | Root `plan.md` or root design copies |
| Tasks | `implementation/tasks.md` | Root `tasks.md` |
| Implement / analyze / converge / taskstoissues | Feature-root durable intent plus the same active `implementation/` attempt | Root temporal copies, symlinks, or a second active attempt |
| Init / feature create / select / context / validate | Feature 001 contract paths and result envelopes | Checkout-relative runtime or agent-specific semantic drift |
| Feature harden | Root `design.md`, completed `implementation/tasks.md`, resolved `implementation/checklists/*.md`, returned `proposal_path`, `task_summary`, and `checklist_summary`, digest-bound proposal, exact `implementation/` removal | Agent-derived proposal path, direct design mutation, unchecked tasks, unresolved checklist items, implicit approval, stale apply, or broader deletion |
| Ask | Installed extension/preset guidance plus the smallest relevant bounded maintained project sources | Launcher/runtime invocation, checkout dependency, uncited facts, unrelated deeper context, mutation, or implicit lifecycle work |

## Acceptance Evidence

Acceptance must run from built release artifacts in a target outside the Concorde checkout. For each
of the sixteen surfaces it must:

1. identify the active registered artifact and winning source package;
2. record source, materialized, package, and Feature 001 handoff digests;
3. execute the installed workspace/bootstrap path before phase behavior where that surface has one;
4. exercise the bounded phase outcome or Concorde operation, or inspect and semantically review the
   agent-only question procedure;
5. record selected feature root, implementation root, accessed/output paths, exit status, and
   checkout access;
6. compare behavior across one skills-based and one slash-command-based integration.

For an eligible installed hardening proposal, acceptance also records the runtime-returned
`proposal_path`, `task_summary`, and `checklist_summary`. The proposal path must be exactly
`<workspace.implementation_dir>/harden-proposal.json`; installed agents must consume it without
derivation, and apply must revalidate both summaries before mutation.

Acceptance fails on any checkout read, missing required archive member, wrong winner, late workspace
resolution, root checklist or other compatibility copy/symlink, mismatched handoff digest, or
presentation-specific semantic difference. Generated receipts are evidence, not a new public
interface.

## Registry State, Recomposition, and Removal

With a known lower-priority command layer installed, disabling or reprioritizing `concorde-core`
changes future resolution but leaves already registered commands active, matching Spec Kit 0.16.4's
documented lifecycle. Updating must materialize the accepted updated layer. Removing must recompose
and materialize the next surviving winner for all nine normal commands. No stale Concorde
instructions may remain, and removal must not delete shared components, unrelated registered
commands, project configuration, `.concorde/`, `specs/`, or `docs/` content.

## Compatibility and Change Control

This profile supports Spec Kit 0.16.4 only. A later version is supported only after every replacement
is reviewed against that version's phase inputs, outputs, hooks, prerequisites, failures, and
registration behavior, followed by the full isolated path and recomposition matrices.

A change to the nine/seven inventory, bootstrap order, durable/temporal path split, or stable command
intent is a contract change and requires synchronized Feature 001 handoff, package manifests,
catalogs, diagrams, tests, and evidence.
