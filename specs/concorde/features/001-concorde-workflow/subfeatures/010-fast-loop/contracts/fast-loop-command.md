# Fast-Loop Command Contract

**Feature**: `feature.concorde.workflow.fast-loop`

**Surface**: `speckit.fast-loop` (rendered as the active integration's skill or slash-command form)

**Representation**: agent-followed command Markdown plus Feature Workspace Protocol v8 selection

## Intent

Complete one explicitly requested, small modification inside an existing selected feature by
directly reconciling code, proportional tests, and related maintained documentation. Do not create
or invoke a planning, task, implementation, convergence, or acceptance workflow.

## Input

| Field | Required | Meaning |
|---|---:|---|
| change description | yes | The concrete modification the maintainer authorizes the coding agent to make. |
| selected feature | yes | The existing canonical feature or immediate sub-feature resolved from `.specify/feature.json` or `SPECIFY_FEATURE_DIRECTORY`. |

An empty change description is rejected without reading or writing project artifacts.

## Workspace Resolution

Before hooks, preflight, or artifact access, the installed command invokes the extension-relative
workspace adapter with `--phase fast-loop`. A successful Protocol v8 response returns the selected
feature root as `phase_root` and includes the durable trio, providing module references, bounded
parent/sibling summaries, attempt path/state, and project reflection log. Any other status stops the
command without mutation.

The `fast-loop` phase is root-scoped: it resolves an existing feature and never creates an attempt.

## Eligibility

The command decides eligibility before mutation. All conditions must hold:

1. Exactly one canonical feature root is selected.
2. `implementation.md` is an accepted realization, not the placeholder.
3. `attempt_state` is `absent`.
4. The requested outcome remains inside the selected feature's existing ownership.
5. The change creates no feature/module, architecture-view, boundary-contract, compatibility,
   migration, dependency-direction, or cross-feature behavioral change.
6. Relevant current worktree edits can be distinguished safely from the command's proposed edits.
7. Bounded inspection leaves no material ambiguity about the required result.

Expected ineligibility is a normal result, not a reflection-log problem. The command names the
failed rule and recommends the earliest applicable full-workflow stage without changing any file.

## Eligible Direct Change

The coding agent:

1. records the pre-existing worktree state and the exact selected target;
2. reads the selected `design.md` and `implementation.md`, the feature abstract for orientation, the
   providing `module.md` as bounded context, parent aggregate documents only for a sub-feature, and
   only the relevant code, tests, and user-facing docs;
3. edits the implementation and proportional tests while preserving unrelated work;
4. after executable evidence passes, updates selected `design.md` and `abstract.md` only if required
   behavior changed, updates selected `implementation.md` for the verified realization delta, and
   updates directly related non-architectural user guidance;
5. runs targeted tests plus deterministic source/document validation; and
6. returns the completion report below.

The command does not create or read a sibling attempt, does not write any `attempt/` artifact, and
does not edit parent/sibling feature bodies, module sources, boundary contracts, maintained diagrams,
or unrelated feature sources.

## Completion Report

A successful report includes:

- selected feature ID and root;
- the eligibility basis;
- every changed file;
- whether the behavioral documents changed or remained byte-identical;
- every test and validation command with its result;
- unrelated pre-existing changes preserved;
- reflections appended, if a genuine workflow problem was encountered; and
- explicit confirmation that no attempt, planning, task, implementation, convergence, or acceptance
  operation was used.

## Failures

Unsafe or invalid selection, placeholder realization, active attempt, ineligible scope, overlapping
user edits, unavailable required evidence, and failing checks never produce a success claim. The
command either repairs an eligible failure within the same bounded loop or reports the exact
remaining state and safe next action. It never discards pre-existing user work.

## Presentation Parity

Codex skills mode and supported slash-command integrations preserve the same command name, argument
intent, workspace bootstrap, eligibility rules, path boundaries, direct-edit behavior, completion
report, and failure semantics. No presentation embeds an absolute Concorde checkout path.
