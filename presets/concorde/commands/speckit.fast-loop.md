---
description: "Directly complete one eligible small change across code, tests, and related documentation."
scripts:
  py: .specify/extensions/concorde/scripts/python/workspace.py --phase fast-loop
---

# Fast Loop

## User Input

```text
$ARGUMENTS
```

Treat the complete user input as the requested modification. If it is empty, ask for one concrete
small-change description and stop without reading or writing project artifacts.

## Concorde Installed Workspace Gate

Before any hook, setup step, prerequisite check, or artifact access, run `{SCRIPT}` from the target
project root and parse its canonical JSON. Stop without mutation on any status other than `resolved`
or `selected`. Treat this first resolved root as the **anchor feature**: it starts bounded impact
discovery but does not assert that exactly one feature owns the change.

Require Protocol v8 `workspace.workspace_kind`, `workspace.feature_id`,
`workspace.providing_module`, `workspace.parent_context`, bounded `workspace.siblings`,
`workspace.feature_directory`, `workspace.feature_abstract`, `workspace.feature_design`,
`workspace.feature_implementation`, `workspace.module_summary`, `workspace.module_design`,
`workspace.attempt_dir`, `workspace.attempt_state`, and `workspace.reflections`. Require
`phase_root == workspace.feature_directory`. These returned paths are the sole path authority for
the anchor.

Treat the module `design.md` and sibling paths as navigation references, never implicit inputs. For a
sub-feature, read the parent durable trio only as aggregate context. Never load a sibling body or any
parent/sibling `attempt/` implicitly. A related feature body becomes an input only after bounded
evidence identifies it as affected; resolve that root by rerunning the same adapter with
`--feature-directory <affected-root> --phase fast-loop`. Require a successful canonical receipt for
every affected root and use only that receipt's paths. Do not persist or invent a multi-feature
selection record.

## Pre-Execution Hooks

If `.specify/extensions.yml` is valid, inspect `hooks.before_fast_loop`. Ignore disabled hooks and
hooks with non-empty conditions. Present optional hooks without executing them. Execute every
enabled, unconditional mandatory hook, replacing dots in its command ID with hyphens, and wait for
success before continuing. A failed mandatory hook stops the command without fast-loop mutation.

## Eligibility Preflight

Decide eligibility before changing any file:

| Condition | Eligible when | Redirect |
|---|---|---|
| Anchor | At least one existing canonical anchor feature resolves | Specification/selection repair |
| Affected feature set | Every feature whose behavior or accepted realization can change is identified and resolves canonically | Clarification or specification |
| Baseline | Every affected feature's `implementation.md` is not the placeholder | Implementation acceptance for that root |
| Attempt | Every affected feature has `workspace.attempt_state == "absent"` | Resume implementation or acceptance for that root |
| Module boundary | The change creates/restructures no feature or module and changes no module responsibility or dependency direction | Specification, then the full workflow |
| Related authority | Every affected feature, inter-module contract, maintained diagram, module reference, and user guide can be reconciled in this bounded loop | Planning or specification |
| Project compatibility | No project-level compatibility or migration policy promised to users of the whole project changes; an explicit pure naming migration may replace names while following the existing policy | Specification, then the full workflow |
| Pure rename (when claimed) | The request supplies an explicit old-to-new mapping; only identifiers, labels, paths, and their references change; behavior, data semantics, permissions, failure handling, responsibilities, and dependencies remain unchanged | Specification, then the full workflow |
| Worktree | Proposed edits do not overlap changes of uncertain ownership | Stop for maintainer coordination |
| Clarity | Bounded inspection leaves no materially ambiguous result | Clarification or specification |

Always preserve unrelated pre-existing changes; never use destructive reset or checkout to make a
request appear eligible.

1. Read the anchor `abstract.md` for orientation, `design.md` as behavioral authority, and
   `implementation.md` deliberately as the accepted realization. Read its providing `module.md` only
   as bounded context. Cite each durable source used.
2. Build the affected feature set by inspecting only the relevant module summaries, contracts, code,
   tests, accepted implementation references, and maintained/user documentation. Do not equate
   sibling or same-module proximity with impact.
3. For every affected root, run the installed adapter explicitly with `--feature-directory` and
   `--phase fast-loop`; require canonical paths, read its durable trio deliberately, reject the
   no-realization placeholder, and require `workspace.attempt_state == "absent"`. Any affected
   `attempt/`, including checklist-only state, redirects to that root's active normal lifecycle.
4. Inspect `git status --short`, the relevant diff, and only the code, tests, contracts, architecture
   detail, and user-facing docs needed to classify the request. Preserve unrelated pre-existing
   changes. Stop before writing when proposed edits overlap work whose ownership cannot be
   established safely.
5. Reject a new or restructured feature/module, a changed module responsibility, or a changed
   dependency direction. Cross-feature behavior, an inter-module contract/data-format change, a
   maintained diagram update, or a related module-reference edit is not independently disqualifying
   when bounded and all affected authorities can be reconciled.
6. Evaluate compatibility and migration only against durable project-level promises to users of the
   whole project. Internal coordination is not independently disqualifying, but an internal contract
   that is also the project's public user interface remains project-level. Feature or module sources
   must not invent their own compatibility or migration policy. An explicitly requested pure naming
   migration is eligible when it follows that existing policy: record the complete old-to-new
   mapping, prove that implementation logic and behavioral semantics are unchanged, identify every
   affected authority, and define the deterministic stale-name inventory that must reach zero (apart
   from explicitly authorized historical/immutable exclusions).

When any condition fails, make zero fast-loop edits. Name the failed condition and recommend the
earliest applicable full-workflow stage: specification for new/changed behavior or ownership,
planning for a non-small delivery approach, tasks for a plan lacking executable work, implementation
for an active attempt, or implementation acceptance for a completed attempt. Expected ineligibility
is a normal response and is not itself a reflection-log problem.

## Direct Change

For an eligible request, directly complete the bounded modification in this command execution:

1. Record the pre-existing worktree paths plus the anchor and every affected feature ID, root,
   durable-document hash, and attempt state.
2. Add or update proportional tests before or with the implementation change; run the focused tests
   and repair failures inside the same bounded loop.
3. Update product code and every directly related affected feature source, inter-module contract,
   maintained diagram, module reference, and user guide required to keep the repository truthful.
   Never use such edits to change a module responsibility or dependency direction, and never edit an
   unrelated feature or architecture source.
4. For a pure naming migration, apply only the recorded mapping across the bounded affected set;
   classify each durable-document change as referential-only, preserve all implementation logic and
   behavioral semantics, honor source-specific mutation rules, and run a deterministic inventory for
   stale old names, partial new names, aliases, and duplicate identities.
5. After executable evidence passes, update each affected `design.md` and keep its `abstract.md`
   faithful only when that feature's required behavior changed. Leave both byte-identical for an
   unaffected, realization-only, or referential-only feature except for the required mapped names.
6. Reconcile every affected `implementation.md` with its verified realization delta. This is direct
   maintained-source authoring authorized by the explicit fast-loop request, not acceptance
   compaction.
7. Run every targeted test and deterministic validation required by the changed code, feature,
   contract, architecture, and user documentation. Claim completion only when all agree.
8. If an inter-module contract, maintained architecture diagram, or other architecture authority
   changed, report its exact validated diff, source hashes, and architecture evidence state
   `validated`. Under constitution A.V an otherwise eligible fast loop needs no separate post-edit
   human review. If no architecture authority changed, report `not_applicable`.

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

- anchor feature ID/root and every affected feature ID/root;
- eligibility basis;
- all changed files;
- per-feature behavioral and realization documents: changed or byte-identical;
- tests and validations run, with results;
- architecture evidence state (`not_applicable` or `validated`) and affected source paths/hashes;
- for a pure rename, the old-to-new mapping, referential-only authorities, inventory command/result,
  and any explicitly authorized historical/immutable exclusions;
- unrelated pre-existing changes preserved;
- `No attempt: yes` and `No acceptance: yes`; and
- `Reflections added: <identifiers or none> · open for this feature: <count>`.

Do not claim success when a required test, validation, inventory, or mandatory hook failed.
