# Reflection Log Contract

## Purpose

Define the one machine-checkable shape and sole persisted authority of the project reflection log —
`reflections.md` directly inside the specification root — in which coding agents record every
difficulty or problem met during the plan, tasks, implement, analyze, and converge phases of any
attempt, so that a maintainer can read it in minutes, deterministic validation can check it, phase
reports and bounded context can count it, delivery can present it transiently, and explicit
project renames or documentation corrections can
reconcile it like the other maintained docs/specs without changing stable entry identities.

## Representation

Custom format: **Concorde Reflection Log v1**, a Markdown grammar (this document is its normative
definition). One conforming example is maintained at [examples/reflections.md](examples/reflections.md);
the project's actual log is `specs/concorde/reflections.md`. The log is carried by
`contract.concorde.workflow` through the Feature Workspace Protocol v9 path `workspace.reflections`
(project-level, identical for every selected root) and the optional `reflections_open` count in
workspace results and bounded-context feature summaries (both defined in Feature 001's contracts).

## Grammar

```text
log        := H1 preamble? (entry | archive)*
H1         := "# Reflections: " project-title NEWLINE
preamble   := any Markdown without an H2 or H3 heading
archive    := "## Archive" NEWLINE entry*            (optional; same entry grammar)
entry      := "### " ID " · " title NEWLINE field+ occurrences?
ID         := "R-" DIGIT{3,}                          (unique; allocated monotonically; gaps allowed; never reused)
field      := "- **" LABEL "**: " value NEWLINE (continuation lines indented by two spaces)
LABEL      := Phase | Date | Feature | Kind | Concerns | Expected | Observed | Effect | Action | Improvement | Status | Note
occurrences:= "- **Occurrences**:" NEWLINE ("  - " phase " " date " " feature-id " — " text NEWLINE)+
```

Required fields, in this order: `Phase`, `Date`, `Feature`, `Kind`, `Concerns`, `Expected`,
`Observed`, `Effect`, `Action`, `Improvement`, `Status`. `Note` is required when `Status` is not
`open`. `Occurrences` is optional.

## Field semantics

| Field | Value | Meaning |
|---|---|---|
| `Phase` | `plan`, `tasks`, `implement`, `analyze`, `converge` | Phase that first recorded the entry |
| `Date` | `YYYY-MM-DD` | Day first recorded |
| `Feature` | stable feature or sub-feature ID | The root selected when the entry was recorded; the key for "the feature's entries" |
| `Kind` | `specification`, `architecture`, `guidance`, `tooling`, `environment`, `implementation` | Which authority the problem is about (Feature 005 FR-005) |
| `Concerns` | a stable ID (`module.*`, `feature.*`, `contract.*`, a scenario ID from a level view) or a project-relative path, optionally followed by `#fragment` or `:line` | The source the problem is about — anywhere in the project; must resolve |
| `Expected` | text | What the concerned source says should hold |
| `Observed` | text | What actually happened |
| `Effect` | `assumed`, `worked-around`, `deferred`, `blocked` | What the problem did to the work |
| `Action` | text | What the agent did: the assumption taken, the workaround, the deferral, or the stop reason |
| `Improvement` | text | The change to the concerned authority that would remove the problem |
| `Status` | `open`, `resolved`, `dismissed` | Maintainer-owned once set by a maintainer |
| `Note` | text | Why resolved/dismissed and a reference to the resolving change |
| `Occurrences` | list | Later encounters of the same problem (any phase, any feature); never a second entry |

## Obligations

- Ordinary phase recording appends entries and `Occurrences`; it never deletes an entry, changes or
  reuses an `R-NNN` identifier, or reverses a maintainer's `Status` or `Note`.
- An explicitly requested rename or documentation correction MAY rewrite existing titles, prose,
  `Feature`, `Concerns`, `Note`, and occurrence text. It MUST preserve each exact `R-NNN` identifier,
  identifier uniqueness, required field structure, phase/date/kind/effect, maintainer-owned status
  decision, occurrence identity, and problem meaning; renamed IDs and paths MUST resolve and the
  complete rewritten log MUST validate without reflection findings.
- Explicit maintainer cleanup MAY remove resolved or dismissed entries. Surviving entries keep their
  identifiers, removed identifiers are never reused, and no entry is renumbered to close a gap.
- Entries cite evidence paths rather than embedding secrets, credentials, or bulk output, and keep
  `Expected`/`Observed`/`Action` under about 150 words together.
- Phases that record list the added identifiers and the open count for `Feature` = the selected
  root in their completion report.
- The log is the only file that persists entry identifiers, fields, statuses, notes, occurrences,
  and prose. Feature/module documents, attempt artifacts, contracts, diagrams, code, and tests MUST
  NOT copy or cite that reflection identity or entry content; they MAY retain independently verified
  facts without reflection identity. Triage plans and completion reports MAY refer to identifiers
  only for transient coordination.
- Acceptance presents every entry whose `Feature` is the selected root by status as a transient
  log-sourced view; candidate feature `implementation.md` and module `design.md` content containing
  an `R-NNN` identifier is refused, and delivery never modifies the log.
- Validation reads the log read-only and reports `CONCORDE-REFLECT-001` to `-004` findings; it
  reports nothing for an absent log.
- No workflow operation removes the log; it is a maintained, version-controlled source and is not
  published as a specification, design reference, or contract.

## Failure Semantics

A malformed log is a validation finding and blocks delivery eligibility (`CONCORDE-DELIVER-011`);
it never causes a phase to stop, and validation never rewrites the log to repair it. A `Concerns` or
`Feature` reference that stops resolving after a source change is reported by analysis as stale and
by validation as `CONCORDE-REFLECT-004`. A candidate feature `implementation.md` or module
`design.md` that persists an `R-NNN` identifier is `CONCORDE-DELIVER-012` at apply time.

## Compatibility

v1 permits additive optional fields (new labels after `Status`/`Note`) and controlled maintained-text
rewrites that preserve the grammar and stable `R-NNN` identities. Removing or renaming a required
label, changing the log's location, changing the identifier grammar, or changing a vocabulary
value's meaning requires v2 and migration guidance in the feature specification.

## Evidence

`tests/concorde/unit/test_reflection_parser.py` covers grammar, duplicate IDs, stable-ID-preserving
rewrites, archive handling, and summaries. `tests/concorde/unit/test_reflection_rules.py` covers all
four validation rules plus controlled rename reference validity. Acceptance centralization gates are in
`tests/concorde/integration/test_delivery.py`; installed phase parity is covered by
`tests/concorde/acceptance/test_workspace_composition.py`.
