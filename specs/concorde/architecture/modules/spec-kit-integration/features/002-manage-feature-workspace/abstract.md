# Feature Abstract: Manage a Nested Feature Workspace

`feature.integration.manage-feature-workspace` · specified at `module.concorde.spec-kit-integration`
· refines `feature.concorde.workflow` · about three minutes. This page is enough to understand how a
feature root is created, selected, routed, and accepted, and what must hold; the links at the end
only redirect you when you want more.

## Purpose

A maintainer can review a feature's placement, create its one nested canonical workspace through the
standard Spec Kit specify phase or select an existing one through the standard Spec Kit pointer, run
every normal Spec Kit phase with durable intent and accepted design at the feature root and temporal
delivery artifacts under `attempt/`, then explicitly accept a completed attempt into that
permanent design. It exists so that one selected root, and never a competing root-level artifact,
is the place every phase reads and writes.

## Functionality

| Concern | How it works |
|---|---|
| Creation | `speckit.specify` with `SPECIFY_FEATURE_DIRECTORY` at the canonical root; the preset's addendum seeds `design.md` and the adjacent design reference and persists the root to `.specify/feature.json`. The author records ownership in the front matter and feature lists; `speckit.concorde.validate` enforces it. |
| Selection | Spec Kit's project-scoped feature pointer; no Concorde copy and no Concorde selection command. |
| Routing | Before every normal phase, the selected-workspace adapter validates the root and returns durable and temporal paths, the workspace kind, parent context and sibling summaries for a sub-feature, and `attempt_state`. |
| Durable paths | Specify and contracts resolve from the feature root; the permanent accepted realization resolves from the root design reference and is never changed by a normal phase. |
| Temporal paths | Plan, tasks, implement, analyze, and converge resolve from `attempt/`; every checklist lives under `attempt/checklists/` while reading the durable specification. |
| Acceptance | Requires complete tasks, a reviewed digest-bound design proposal, and explicit approval; removes only the selected feature's `attempt/`. |

**Not part of this feature**: Spec Kit's core phases, choosing or changing architectural ownership
silently, a second registry or root-level temporal aliases, and more than one active implementation
attempt per feature.

## Structure

The parent feature's core view
<a href="/architecture/concorde-workflow-components.html">workflow components</a> (maintained source
`specs/concorde/features/001-concorde-workflow/diagrams/concorde-workflow-components.json`) shows
the coding agent reaching this workspace service through the adapter every normal phase invokes and
through `impl.accept`, sharing the selected workspace with Spec Kit and Architecture Core.

```text
speckit.specify (SPECIFY_FEATURE_DIRECTORY) ──▶ .specify/feature.json ◀── standard Spec Kit selection
normal phase override ──▶ selected-workspace adapter ──feature-workspace──▶ validated root
                                                            ├─ durable: design.md · design reference · contracts
                                                            └─ temporal: attempt/ (plan · tasks · checklists) + attempt_state
impl.accept ──▶ digest-bound proposal ──▶ explicit approval ──▶ root design updated · attempt/ removed
architecture context / validation ──architecture-services──▶ Architecture Core (read-only relay)
```

The module provides `contract.integration.feature-workspace`,
`contract.integration.workflow-composition`, and `contract.integration.agent-skills`, and requires
`contract.integration.spec-kit-platform` and `contract.integration.architecture-services`.

## Logic

**One feature, start to acceptance**

1. The maintainer reviews placement and runs the standard specify phase at the canonical root,
   which writes the durable pair and the selection.
2. Each later phase resolves the selection through the adapter; unsafe, stale, unregistered,
   unknown, or ambiguous targets return findings and change nothing.
3. Durable work stays at the root; planning, tasks, checklists, and execution stay under
   `attempt/`, and an existing non-empty attempt is reported as active.
4. When tasks are complete, acceptance proposes the design, the maintainer approves the exact
   proposal, and the attempt is promoted and removed.

**Rules the implementation must keep**

- Creation is the standard specify phase at the canonical root, seeding the durable pair and the
  selection, and never silently chooses or changes ownership (Requirements, item 1).
- Selection uses Spec Kit's supported project-scoped feature pointer only (Requirements, item 2).
- The adapter validates the selected root before every normal phase and returns kind, context,
  paths, and `attempt_state` (Requirements, item 3).
- Specify and contracts resolve from the root; every checklist resolves from
  `attempt/checklists/` (Requirements, item 4).
- The permanent accepted realization is never changed by normal phases; plan, tasks, implement,
  analyze, and converge resolve from `attempt/` (Requirements, items 5 and 6).
- A non-empty attempt is reported as active and never replaced or removed silently (Requirements,
  item 7).
- Acceptance needs complete tasks, a digest-bound reviewed proposal, and explicit approval, and
  removes only the selected feature's temporal workspace (Requirements, item 8).
- Installed behavior ships through supported preset and extension mechanisms with clean-project
  compatibility tests (Requirements, item 9).

## Read Next

- **Exact outcome, scenario, requirements, and evidence** — [design.md](design.md).
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md).
- **The contracts** — [feature-workspace](../../architecture/contracts/feature-workspace/contract.md) (the
  protocol), [workflow-composition](../../architecture/contracts/workflow-composition/contract.md),
  [agent-skills](../../architecture/contracts/agent-skills/contract.md),
  [spec-kit-platform](../../architecture/contracts/spec-kit-platform/contract.md), and
  [architecture-services](../../architecture/contracts/architecture-services/contract.md).
- **The level this feature belongs to** — [module.md](../../module.md) (the Spec Kit Integration
  summary) and its [design reference](../../design.md); the sibling feature is
  [compose-concorde-workflow](../001-compose-concorde-workflow/design.md); the root summary is
  [module.md](../../../../../module.md).
- **The parent feature** — [Concorde Workflow](../../../../../features/001-concorde-workflow/abstract.md)
  and the steps this feature serves:
  [workspaces](../../../../../features/001-concorde-workflow/subfeatures/004-manage-feature-workspaces/design.md)
  and [accept](../../../../../features/001-concorde-workflow/subfeatures/009-accept-milestone/design.md).
- **Framework guides** — [docs/project-structure.md](../../../../../../../docs/project-structure.md)
  (nested feature selection) and [docs/concorde-workflow.md](../../../../../../../docs/concorde-workflow.md).
