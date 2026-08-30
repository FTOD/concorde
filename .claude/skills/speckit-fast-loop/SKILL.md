---
name: speckit-fast-loop
description: Directly complete one eligible small change across code, tests, and related
  documentation.
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: preset:concorde-core
user-invocable: true
disable-model-invocation: false
---

# Speckit Fast Loop Skill

# Fast Loop

## User Input

```text
$ARGUMENTS
```

Treat the complete user input as the requested modification. If it is empty, ask for one concrete
small-change description and stop without reading or writing project artifacts.

## Concorde Installed Workspace Gate

Before any hook, setup step, prerequisite check, or artifact access, run `.venv/bin/python .specify/extensions/concorde/scripts/python/workspace.py --phase fast-loop` from the target
project root and parse its canonical JSON. Stop without mutation on any status other than `resolved`
or `selected`.

Require Protocol v8 `workspace.workspace_kind`, `workspace.feature_id`,
`workspace.providing_module`, `workspace.parent_context`, bounded `workspace.siblings`,
`workspace.feature_directory`, `workspace.feature_abstract`, `workspace.feature_design`,
`workspace.feature_implementation`, `workspace.module_summary`, `workspace.module_design`,
`workspace.attempt_dir`, `workspace.attempt_state`, and `workspace.reflections`. Require
`phase_root == workspace.feature_directory`. These returned paths are the sole path authority.

Treat the module `design.md` and sibling paths as navigation references, never implicit inputs. For a
sub-feature, read the parent durable trio only as aggregate context. Never load a sibling body or any
parent/sibling `attempt/` implicitly.

## Pre-Execution Hooks

If `.specify/extensions.yml` is valid, inspect `hooks.before_fast_loop`. Ignore disabled hooks and
hooks with non-empty conditions. Present optional hooks without executing them. Execute every
enabled, unconditional mandatory hook, replacing dots in its command ID with hyphens, and wait for
success before continuing. A failed mandatory hook stops the command without fast-loop mutation.

## Eligibility Preflight

Decide eligibility before changing any file:

| Condition | Eligible when | Redirect |
|---|---|---|
| Selection | Exactly one existing canonical feature root resolves | Specification/selection repair |
| Baseline | `implementation.md` is not the placeholder | Implementation acceptance |
| Attempt | `workspace.attempt_state == "absent"` | Resume implementation or acceptance |
| Feature scope | Result stays inside the selected feature's existing outcome | Specification |
| Architecture and boundary contract | No module responsibility, dependency, maintained diagram, or contract changes | Specification, then the full workflow |
| Compatibility | No compatibility or migration policy changes | Specification, then the full workflow |
| cross-feature behavior | No behavioral authority in another feature must change | Specification for every affected root |
| Worktree | Proposed edits do not overlap changes of uncertain ownership | Stop for maintainer coordination |
| Clarity | Bounded inspection leaves no materially ambiguous result | Clarification or specification |

Always preserve unrelated pre-existing changes; never use destructive reset or checkout to make a
request appear eligible.

1. Read the selected `abstract.md` for orientation, selected `design.md` as behavioral authority,
   and selected `implementation.md` deliberately as the accepted realization. Read the providing
   `module.md` only as bounded context. Cite each durable source used.
2. Reject the no-realization placeholder. Fast-loop never creates the first accepted realization.
3. Require `workspace.attempt_state == "absent"`. Any `attempt/`, including checklist-only state,
   redirects to the active normal lifecycle.
4. Inspect `git status --short`, the relevant diff, and only the code, tests, and user-facing docs
   needed to classify the request. Preserve unrelated pre-existing changes. Stop before writing when
   proposed edits overlap work whose ownership cannot be established safely.
5. Confirm the requested result stays within the selected feature's existing outcome and ownership.
   It must not create or restructure a feature/module, change a module responsibility or dependency
   direction, change a boundary contract or maintained diagram, change compatibility or migration
   policy, require behavioral edits in another feature root, or remain materially ambiguous.

When any condition fails, make zero fast-loop edits. Name the failed condition and recommend the
earliest applicable full-workflow stage: specification for new/changed behavior or ownership,
planning for a non-small delivery approach, tasks for a plan lacking executable work, implementation
for an active attempt, or implementation acceptance for a completed attempt. Expected ineligibility
is a normal response and is not itself a reflection-log problem.

## Direct Change

For an eligible request, directly complete the bounded modification in this command execution:

1. Record the pre-existing worktree paths and selected durable-document hashes.
2. Add or update proportional tests before or with the implementation change; run the focused tests
   and repair failures inside the same bounded loop.
3. Update product code and directly related non-architectural user documentation. Do not edit module
   sources, boundary contracts, maintained diagrams, parent/sibling feature bodies, or unrelated
   feature sources.
4. After executable evidence passes, update selected `design.md` and keep `abstract.md` faithful only
   when required behavior changed. Leave both byte-identical for a realization-only correction.
5. Reconcile selected `implementation.md` with the verified realization delta. This is direct
   maintained-source authoring authorized by the explicit fast-loop request, not acceptance
   compaction.
6. Run every targeted test and deterministic validation required by the changed source and docs.
   Claim completion only when code, tests, and maintained documentation agree.

No attempt is created or used. Do not create `plan.md`, `tasks.md`, a task checklist, or an acceptance
proposal. Do not delegate to the planning, task-generation, implementation, convergence, or
implementation-acceptance procedures as hidden substeps.

If a required check cannot pass, keep unrelated user work intact, do not describe unverified
realization as accepted, and report the exact remaining diff/failure plus the safe next action.

## Reflection Recording

Expected eligibility rejection is not a workflow problem. If the eligible execution instead cannot
follow maintained specification, accepted realization, architecture, installed guidance, or tooling,
append or update the matching entry in the project reflection log at `workspace.reflections` before
the final report. Never place a reflection under `attempt/` and never change a maintainer-set status
or note.

For a new entry, use the next `R-NNN` identifier and the fixed field order: `Phase: fast-loop`,
`Date`, `Feature`, `Kind`, `Concerns`, `Expected`, `Observed`, `Effect`, `Action`, `Improvement`, and
`Status: open`. When the same problem already exists, append one `fast-loop YYYY-MM-DD <feature-id>
— <context>` occurrence instead of duplicating it.

## Mandatory Post-Execution Hooks

Before reporting success, inspect valid `.specify/extensions.yml` for `hooks.after_fast_loop` using
the same enabled/unconditional rules as pre-hooks. Execute mandatory hooks and wait for success;
present optional hooks without execution. A failed mandatory post-hook means the fast loop is not
complete.

## Completion Report

Return a concise report containing:

- selected feature ID and `workspace.feature_directory`;
- eligibility basis;
- all changed files;
- behavioral documents: changed or byte-identical;
- tests and validations run, with results;
- unrelated pre-existing changes preserved;
- `No attempt: yes` and `No acceptance: yes`; and
- `Reflections added: <identifiers or none> · open for this feature: <count>`.

Do not claim success when a required test, validation, or mandatory hook failed.
