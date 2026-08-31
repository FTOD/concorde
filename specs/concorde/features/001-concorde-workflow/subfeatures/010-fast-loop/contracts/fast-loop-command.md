# Fast-Loop Command Contract

**Feature**: `feature.concorde.workflow.fast-loop`

**Surface**: `speckit.fast-loop` (rendered as the active integration's skill or slash-command form)

**Representation**: agent-followed command Markdown plus Feature Workspace Protocol v8 selection

## Intent

Complete one explicitly requested, small modification beginning from an existing selected anchor
feature by directly reconciling code, proportional tests, every affected existing feature, and
related maintained documentation. Do not create or invoke a planning, task, implementation,
convergence, or acceptance workflow.

## Input

| Field | Required | Meaning |
|---|---:|---|
| change description | yes | The concrete modification the maintainer authorizes the coding agent to make. |
| anchor feature | yes | The existing canonical feature or immediate sub-feature resolved from `.specify/feature.json` or `SPECIFY_FEATURE_DIRECTORY`; it starts impact discovery but is not necessarily the only affected feature. |

An empty change description is rejected without reading or writing project artifacts.

## Workspace Resolution

Before hooks, preflight, or artifact access, the installed command invokes the extension-relative
workspace adapter with `--phase fast-loop`. A successful Protocol v8 response returns the selected
anchor root as `phase_root` and includes the durable trio, providing module references, bounded
parent/sibling summaries, attempt path/state, and project reflection log. After bounded impact
discovery, the command reruns the same adapter with `--feature-directory <affected-root> --phase
fast-loop` for every affected feature and uses each returned receipt as that root's path authority.
Any non-success status stops the command without mutation.

The `fast-loop` phase is root-scoped: each call resolves one existing feature and never creates an
attempt. Repeated explicit resolution does not persist a multi-feature selection record.

## Eligibility

The command decides eligibility before mutation. All conditions must hold:

1. At least one existing canonical feature root resolves as the anchor.
2. Bounded inspection identifies every existing feature whose behavior or accepted realization is
   affected.
3. Every affected `implementation.md` is an accepted realization, not the placeholder, and every
   affected `attempt_state` is `absent`.
4. The change creates or restructures no feature or module and changes no module responsibility or
   dependency direction.
5. The change does not alter project-level compatibility or migration policy promised to users of
   the whole project. Internal inter-module contracts and data formats are not independently
   disqualifying. An explicitly requested pure naming migration may replace names while following
   the existing policy.
6. Every affected feature, contract, architecture detail, and user document can be reconciled in the
   same bounded loop.
7. Relevant current worktree edits can be distinguished safely from the command's proposed edits.
8. Bounded inspection leaves no material ambiguity about the required result.
9. When the request claims a pure rename, it supplies a complete old-to-new mapping; changes only
   identifiers, labels, paths, and references; preserves implementation logic and non-name semantics;
   and defines a deterministic stale-name/alias/duplicate inventory plus any explicitly authorized
   historical or immutable exclusions.

Expected ineligibility is a normal result, not a reflection-log problem. The command names the
failed rule and recommends the earliest applicable full-workflow stage without changing any file.

## Eligible Direct Change

The coding agent:

1. records the pre-existing worktree state, selected anchor, and durable-document hashes for every
   affected feature;
2. reads the anchor's durable trio and providing `module.md`, discovers the affected set from bounded
   module, contract, implementation, test, and documentation evidence, then deliberately reads each
   affected feature's durable trio without reading any attempt;
3. edits the implementation and proportional tests while preserving unrelated work;
4. after executable evidence passes, reconciles each affected feature's `design.md`, `abstract.md`,
   and `implementation.md` according to its behavior and realization delta, plus every directly
   related inter-module contract, maintained diagram or module reference, and user guide needed to
   keep the repository truthful without changing module responsibilities or dependencies;
5. for a pure rename, classifies mapped durable changes as referential-only and deterministically
   rejects stale old names, partial replacements, unauthorized aliases, and duplicate identities;
6. runs targeted tests plus deterministic source/document validation; and
7. when maintained architecture sources changed, reports their exact validated diff and source
   hashes with evidence state `validated`, without requiring separate post-edit human review under
   constitution A.V; and
8. returns the completion report below.

The command does not create or read any affected feature's attempt and does not write any `attempt/`
artifact. It edits a parent, sibling, module, contract, or maintained diagram source only when that
source is directly related to the bounded eligible change, and never changes module responsibility
or dependency direction through that edit.

## Completion Report

A successful report includes:

- anchor feature ID/root and every affected feature ID/root;
- the eligibility basis;
- every changed file;
- whether each affected feature's behavioral documents changed or remained byte-identical;
- every test and validation command with its result;
- unrelated pre-existing changes preserved;
- reflections appended, if a genuine workflow problem was encountered; and
- architecture evidence state (`not_applicable` or `validated`) with the affected source paths and
  hashes;
- for a pure rename, the mapping, referential-only authorities, stale-name inventory result, and
  authorized historical/immutable exclusions; and
- explicit confirmation that no attempt, planning, task, implementation, convergence, or acceptance
  operation was used.

An otherwise eligible architecture-source change may complete after its exact diff, hashes, and
applicable deterministic evidence validate. It requires no separate post-edit human review and
creates no attempt or implementation-acceptance artifact.

## Failures

Unsafe or invalid anchor resolution, a placeholder realization or active attempt in any affected
feature, ineligible module-boundary or project-policy scope, overlapping user edits, unavailable
required evidence, and failing checks never produce a success claim. The command either repairs an
eligible failure within the same bounded loop or reports the exact remaining state and safe next
action. It never discards pre-existing user work.

## Presentation Parity

Codex skills mode and supported slash-command integrations preserve the same command name, argument
intent, workspace bootstrap, eligibility rules, path boundaries, direct-edit behavior, completion
report, and failure semantics. No presentation embeds an absolute Concorde checkout path.
