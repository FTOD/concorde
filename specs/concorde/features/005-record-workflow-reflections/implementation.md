# Feature Implementation: Record Workflow Reflections

**Realization status**: First milestone accepted for hardening on 2026-08-28 (attempt of the same
day; project-wide log model).

**Selected level**: Top-level feature of `module.concorde`; it has no parent feature.

## Realization Overview

The feature is realized without a new command surface. Three existing parts carry it:

| Part | Owner | What it now does |
|---|---|---|
| Phase guidance and templates | Spec Kit Integration (`presets/concorde-core`) | A byte-identical **Reflection Recording** block in the five phase instructions after specification (`speckit.plan`, `tasks`, `implement`, `analyze`, `converge`) tells the agent when, where, and how to record; `reflections-template` seeds the log; the plan and tasks append layers name the log as the one maintained file a phase may append to; each completion report ends with `Reflections added: … · open for this feature: N`. |
| Runtime | Architecture Core (`extensions/concorde/runtime/concorde`) | `reflections.py` is the single parser of the log; `validation/reflections.py` emits `CONCORDE-REFLECT-001..004`; `repository.py` loads `<specification_root>/reflections.md` into `package.auxiliary` (and the digest); `feature_workspace.py` adds `reflections` and `reflections_open` to every workspace result; `context.py` adds `reflections` (path + open count per feature) and `reflections_open` on feature summaries; `feature_hardening.py` adds `reflection_summary`, blocks on a malformed log (`CONCORDE-HARDEN-011`), refuses an uncited open entry (`CONCORDE-HARDEN-012`), and never writes the log. |
| Protocol and documentation | Feature 001 contracts, guides, root view | Reflection fields remain additive in Feature Workspace Protocol v6; the root view shows the feature node with two governed crossings; guides and READMEs describe the review loop. |

The log itself, `specs/concorde/reflections.md` for this project, is a maintained source beside the
root `module.md`: created from the template by the first phase that records, appended to by every
phase, never removed, not published (the docsite excludes it as a non-canonical artifact).

## Module and Feature Collaboration

- **Spec Kit Integration** composes the preset: `reflections-template` (`strategy: replace`, six
  templates in total) resolves through `specify preset resolve`; the nine normal command
  replacements keep `workspace.py --phase` as the path authority, so `workspace.reflections` is the
  only way a phase locates the log (FR-003, FR-013). The recording block lives in the five phase
  files at the point where each already says what it may write; `analyze` names the log as its
  single permitted write (see R-006).
- **Architecture Core** owns every deterministic behavior: parsing, the four shape rules, the
  per-feature open count used by context and the adapter, and the hardening summary and gate.
  All of them read the log through `package.auxiliary`, so a symlinked log is a source error and
  the log is part of `source_digest` and of the hardening digest (a log edited after a proposal is
  `CONCORDE-HARDEN-004`).
- **Feature 001 (Concorde Workflow)** carries the protocol: the additions are optional in the
  schemas and always emitted by the runtime, examples updated, `hardeningProposal` untouched.
- **Documentation** needs no change: `registry.ts` already excludes non-canonical Markdown under
  `specs/`; the abstract therefore names the contract, example, and log as code spans (R-007).
- **Distribution** packages the changed preset and extension unchanged in shape; the release
  builder's catalog count moved from five to six templates; versions stay `0.3.0` (unpublished).
- **Feature 004 (Self-Host Concorde)** refreshes this checkout's mirrors only for the Codex
  integration; under the active `claude` integration the refresh is `specify preset remove` +
  `preset add --dev` and `extension add --dev --force` with byte equality proven by
  `test_installed_command_surfaces` (R-001).

Contracts crossed: `contract.concorde.workflow` (phases and operations into maintained sources),
`contract.concorde.spec-kit-platform` (host phases), and internally
`contract.integration.feature-workspace` (Protocol v6 fields) and
`contract.core.architecture-services` (validation findings, context results).

## Scenario Realization

- **Record while planning and implementing** (US1, US2; core view
  `record-during-planning-and-implementation`): the phase instruction's block triggers on FR-002
  conditions; the agent appends `### R-NNN · title` with `Feature = workspace.feature_id` and a
  free `Concerns`; `implement` records `Effect: blocked` before any halt; re-encounters append
  `Occurrences`. Unit evidence: `test_reflection_parser.py` (grammar, selection by feature,
  occurrences), composition acceptance (block present byte-identical on all five surfaces).
- **Review and improve** (US3, US5; `review-and-improve`): `speckit.concorde.context module.<root>`
  returns `reflections.path` and `reflections.open` per feature; `speckit.concorde.validate` reports
  `CONCORDE-REFLECT-001..004` read-only and byte-equivalently; the maintainer edits `Status`/`Note`
  in place. Evidence: `test_context.py`, `test_reflection_rules.py`, `test_validation.py` (malformed
  fixture overlay: one finding per rule, fixture unchanged).
- **Carry lessons through hardening** (US4; `carry-lessons-through-hardening`): `propose` returns
  `reflection_summary` for the target's entries; `apply` computes the target's open identifiers from
  the log and refuses with `CONCORDE-HARDEN-012` naming those absent from `design.content`; the
  log is retained and byte-identical. Evidence: six `ReflectionHardeningTests` cases.

## Durable Implementation Decisions

- **One project-wide log at the specification root** (R-004, resolved): problems concern existing
  implementations, often other features'; per-attempt files scatter and delete them. `Feature`
  attributes, `Concerns` targets anything.
- **Markdown grammar with bold-labelled fields**, identifiers `R-` + three or more digits, an
  optional `## Archive` section, continuation lines indented by two spaces; the parser never raises
  and reports `shape`, `duplicate`, and `vocabulary` problems that map to `REFLECT-001/002/003`;
  reference resolution (`Feature`, `Concerns`) is `REFLECT-004` and accepts stable IDs, level-view
  scenario IDs, and existing project-relative paths with an ignored `#fragment` or `:line` suffix.
- **Seeding by the first phase that records**, not by `init`: no runtime write path was added; the
  adapter stays read-only.
- **Citation gate instead of dispositions**: because the log persists, hardening only has to prove
  that the design reference is honest about open problems — the entry identifier in
  `implementation.content` is that proof; proposal v4 gained no reflection field.
- **Additive protocol fields**, never a version bump: `reflections`/`reflections_open` optional in
  the schema and always emitted.
- **Analysis may append to the log and nothing else** (R-006, open) — the one exception to its
  read-only contract, stated in the instruction.
- **Root view shows two crossings** (R-005, open): agent → feature and feature → Architecture Core;
  the Spec Kit Integration crossing is not drawable without corridor conflicts; the feature's core
  diagram shows every part.
- **Alignment prose describes the end state** (R-003, resolved): the specification says the root
  view shows the feature; pending work is recorded in the log, not in durable prose.

## Traceability and Evidence

- Tests (223 pass, 2026-08-28): `tests/concorde/unit/test_reflection_parser.py`,
  `unit/test_reflection_rules.py`, `unit/test_feature_workspace.py` (path and per-root count),
  `contract/test_feature_workspace_contract.py` (schema additive, examples validate),
  `integration/test_context.py` (path and counts), `integration/test_feature_hardening.py`
  (`ReflectionHardeningTests`), `integration/test_implementation_workspace.py` (adapter),
  `integration/test_validation.py` (malformed fixture; this repository `success`),
  `acceptance/test_workspace_composition.py` (block byte-identical on five surfaces;
  `reflections-template` resolves in a fresh project), `contract/test_installed_command_surfaces.py`
  (mirrors equal sources).
- Fixtures: `tests/concorde/fixtures/invalid-projects/reflections-malformed/` (one breach per
  rule); `tests/concorde/support/feature_workspace.py::write_reflection_log` / `reflection_entry`.
- Deterministic checks on this repository: `speckit.concorde.validate` → `success`, 0 findings
  with `specs/concorde/reflections.md` present; root view and feature core view pass all 9 Archify
  showcase checks and are delivered; docsite `Validated 99 pages (33 excluded sources); 0 errors`,
  production build promoted.
- Success criteria: SC-002, SC-004, SC-006, SC-007 met by automated evidence; SC-001, SC-003,
  SC-005, SC-008, SC-009 are met in guidance text and unit fixtures, with the manual phase-run
  acceptance (quickstart §8) pending a new agent session.
- The contract of the log: `contracts/reflection-log.md` with `contracts/examples/reflections.md`;
  the live log: `specs/concorde/reflections.md`.

## Known Limitations

- **R-001** (open, tooling): the self-hosting tool has no evidence for the `claude` integration this
  checkout uses; mirrors are refreshed through Spec Kit's development-mode commands instead, and a
  new agent session is required before refreshed skills are active.
- **R-002** (open, guidance): the plan and tasks append layers disagree on whether an attempt may
  edit `module.md`; this attempt presented its `module.md` reconciliation as a maintainer-approved
  diff rather than applying it.
- **R-005** (open, architecture): the root view draws two of the three planned crossings for this
  feature; the Spec Kit Integration crossing cannot be routed at showcase quality in the current
  column order.
- **R-006** (open, specification): `feature.concorde.workflow.execute-and-reconcile` FR-004/SC-002
  still describe analysis as strictly read-only; this feature makes the log its one permitted write.
- **R-007** (open, tooling): the docsite rejects abstract links to non-canonical artifacts; the
  `abstract.md` names the contract, example, and log as code spans, and no specify-guidance rule about
  link targets is delivered yet.
- Visual (browser) review of both diagrams is pending: Chrome/Chromium is unavailable in the
  validation environment; structural showcase checks are not perceptual evidence.
- The sub-feature specifications 002/006/007/008/009 of Feature 001 are not yet reconciled with
  FR-003, FR-009, FR-011, FR-012 of this feature (a specification action on those roots).
- Manual acceptance of the live phases (quickstart §8) has not been run; the guidance is proven by
  composition tests, not by an observed phase run.

## Implementation Detail

### Grammar and parser

`extensions/concorde/runtime/concorde/reflections.py`: `parse_reflection_log(text) -> ParsedLog`
walks lines, ignores fenced blocks, opens an entry at `### R-\d{3,} · title` (any other `###`
heading is a `shape` problem), collects `- **Label**: value` fields with two-space continuation
lines, and `- **Occurrences**:` followed by `  - …` items. On entry end it checks required fields
(`Phase`, `Date`, `Feature`, `Kind`, `Concerns`, `Expected`, `Observed`, `Effect`, `Action`,
`Improvement`, `Status`), the `YYYY-MM-DD` date, the vocabularies (`PHASES`, `KINDS`, `EFFECTS`,
`STATUSES`), a `Note` on non-open status, and duplicate identifiers. `ParsedLog.entries_for`,
`open_count`, and `summary` select by `Feature`. `log_path(specification_root)` and
`strip_reference_suffix` are shared helpers.

### Validation rule

`validation/reflections.py::validate_reflections(package)` returns nothing when
`package.auxiliary` has no log; maps parser problems to `REFLECT-001/002/003` with line numbers and
`subject_id`; resolves `Feature` (must be one `feature` document) and `Concerns` (any `by_id` entry,
any level-view scenario ID, or an existing safe project-relative path) for `REFLECT-004`. Wired
after `validate_tldrs` in `validate.FOCUSED_VALIDATORS`.

### Workspace, context, hardening

- `WorkspacePaths.reflections`/`reflections_open` (defaults keep positional construction stable);
  `resolve_phase_paths` uses `reflections_open_count(package, feature_id)`; `_planned_paths`
  receives `specification_root` so a planned root reports the same path with `0`.
- `_summary(feature, package)` adds `reflections_open` only when the log exists, so sibling and
  parent summaries stay schema-valid without a log.
- `context.bounded_context` adds `context["reflections"] = {"path", "open": {feature_id: n}}`
  (features with at least one entry) and the path to `artifacts`.
- `propose_hardening` adds `reflection_summary`, includes the log in `_hardening_digest`, and emits
  `CONCORDE-HARDEN-011` on parser problems; `apply_hardening` calls `_uncited_open_reflections`
  after `_validate_design` and returns `invalid` with `CONCORDE-HARDEN-012` before any staging;
  the hardened result carries `reflection_summary` and lists the log among `retained_artifacts`;
  `diagnostics.operation_envelope` forwards `reflection_summary`.

### Guidance placement

The shared block is authored once (`speckit.plan.md`) and copied verbatim into the other four
files immediately before their hooks section (`## Mandatory Post-Execution Hooks` or
`### 9. Check for extension hooks`), so the composition test can assert byte identity. Phase
specifics: plan lists unresolved problems in its architecture gate; implement records before
failing or halting a task; analyze reads the log as an artifact, reports a "Reflections" table with
stale flags (`git log -1 --format=%cs -- <path>` later than `Date`, or an unresolvable ID), and
never repairs it; converge makes candidate work only from genuine `deferred` entries of the
feature. `speckit.concorde.feature.harden.md` states the citation rule; `context.md` and `ask.md`
present the log; `validate.md` lists the rule IDs.

### Refresh procedure used by this attempt

`uv run specify preset remove concorde-core && uv run specify preset add --dev presets/concorde-core --priority 10`,
then `uv run specify extension add extensions/concorde --dev --priority 10 --force`; verify with
`diff -r` against `.specify/` and `test_installed_command_surfaces`; start a new agent session.
