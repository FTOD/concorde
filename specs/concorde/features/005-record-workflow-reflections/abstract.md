# Feature Abstract: Record Workflow Reflections

`feature.concorde.record-workflow-reflections` · specified at `module.concorde` · about five
minutes. This page is enough to understand what the feature does, how it is built, and how it
works; the links at the end only redirect you when you want more.

## Purpose

When a coding agent plans or implements a feature and something does not work as the
specification, the accepted design, an existing implementation, the installed guidance, or the plan
says — a requirement reads two ways, another feature's code disagrees with its design reference, a
tool fails, an instruction cannot be followed, a dependency is missing, a workaround has to be taken
— it writes that problem down, in the phase where it happened, in the project's one reflection log.
The maintainer reads that log to improve the specification, the architecture, the guidance, or the
tooling across all features; hardening cites the attempt's entries in the design reference; and the
log outlives every attempt.

The log is project-wide on purpose: a problem met while implementing one feature is usually about
something that already exists — another feature, a module boundary, a contract, a tool. One file
at the specification root, with each entry saying which feature was being worked on and which
source the problem concerns, keeps the same problem from being scattered across roots or deleted
with an attempt. The feature exists for the maintainer who no longer writes the code but still owns
the project, and for the Concorde project itself, which develops with its own workflow and needs a
cumulative list of what the framework got wrong.

## Functionality

| What | How it shows up |
|---|---|
| Recording | During plan, tasks, implement, analyze, and converge, the agent appends an entry to the project log the moment it meets a problem, then continues if it can. No new command. |
| The log | `reflections.md` directly inside the specification root, beside the root `module.md` (for this project: `specs/concorde/reflections.md`). Created from the installed template by the first phase that records; reached through the path the workspace result returns. |
| An entry | Identifier, phase, date, the feature being worked on (`Feature`), one kind, the source it concerns (`Concerns` — any feature, module, contract, guidance, tool, or file in the project), expected versus observed, the effect on the work (`assumed`, `worked-around`, `deferred`, `blocked`) with what the agent did, a suggested improvement, a status (`open`, `resolved`, `dismissed`) with a note. |
| Kinds | `specification`, `architecture`, `guidance`, `tooling`, `environment`, `implementation` — which authority the problem is about. |
| Surfacing | Every recording phase lists the entries it added and the feature's open count in its completion report; analysis lists the feature's open entries and flags entries whose referenced source has since changed; the root level's bounded context exposes the log and open counts. |
| Review | The maintainer resolves or dismisses entries by editing the log; the real fix goes through the phase that owns the document (specification review, an architecture change, a guidance or runtime change). |
| Hardening | The proposal presents the feature's entries by status; the candidate `implementation.md` cites every open one among its known limitations (and resolved, realization-shaping ones among its decisions); apply refuses while an open entry is uncited and never touches the log. |
| Validation | A present log is checked deterministically for unique identifiers, required fields, permitted values, a resolvable feature, and resolvable references; an absent log is not a breach. |

**Not part of this feature**: any new command, skill, or slash command; the agent fixing a
durable document or another feature's code in response to an entry; per-feature or per-module
reflection files, a database, a dashboard, or a published page; automatic archiving; judging
whether an entry is truthful; sending entries anywhere outside the repository.

## Structure

The core view is <a href="/architecture/workflow-reflection-components.html">workflow reflection
components</a> (maintained source `diagrams/workflow-reflection-components.json`). In one sketch:

```text
Coding agent ──plan · tasks · implement · analyze · converge──▶ phase meets a problem
                                                                    │ append / update entry
                                                                    ▼
Specification root ── reflections.md  (one log for the whole project; maintained; never removed)
        ▲ validate: shape findings          ▲ maintainer: review · resolve · dismiss
        │                                   │
Selected feature root ─┬─ abstract.md + design.md          (read-only: cited, never edited)
                       └─ implementation.md  ◀── feature.harden cites the feature's entries
                                          (open → known limitations; resolved → decisions)
                                          ──▶ module implementation.md amendment (level lessons)
```

- **Phase surfaces** are the five Spec Kit phases after specification; the installed guidance and
  the log template carry the recording obligation, so an installed project needs no Concorde
  checkout for it.
- **The reflection log** is the only maintained document an agent may extend in response to a
  problem with a durable document or an existing implementation; every entry names the feature
  being worked on and the source it concerns.
- **Hardening and validation** are the existing Concorde operations; they gain the citation rule
  and the shape check respectively.

## Logic

**How one problem moves through the workflow**

1. A phase meets a problem: it cannot follow the specification, the design baseline, an existing
   implementation, the guidance, the architecture, or the plan, or must assume, work around, defer,
   or stop.
2. The agent records an entry in the project log in that same phase — creating the log from the
   template if the project has none — attributed to the selected feature and naming the concerned
   source, and continues when it can; if blocked, it records the stop reason and then halts under
   the phase's existing rules.
3. Meeting the same problem again, from any feature, updates the existing entry; agents never
   delete or renumber entries or reverse a maintainer's note.
4. The phase's completion report lists what it added and how many of the feature's entries are
   open; analysis repeats the open list and flags entries whose sources changed.
5. The maintainer resolves or dismisses entries in the log and makes the improvement through the
   owning path; in the Concorde project a guidance or tooling fix counts as used only once the
   self-hosted installation is refreshed.
6. At hardening the proposal presents the feature's entries by status; the accepted `implementation.md`
   cites the open ones as known limitations; the log stays byte-identical.

**Rules the implementation must keep**

- Recording happens through the existing phases only: no new command, no new approval, no
  checkout dependency, and the installed guidance and template carry the obligation (FR-001,
  FR-015).
- A problem is recorded in the phase in which it is met, before that phase reports completion,
  and recording never halts a phase that can continue (FR-002, FR-006).
- One project-wide log at `reflections.md` inside the specification root; the first recording phase
  creates it; it is maintained, never removed, and not published by this feature (FR-003, FR-016).
- Every entry has the full field set including the attributed feature and the concerned source,
  exactly one of the six kinds, one of the four effects, and one of the three statuses (FR-004,
  FR-005).
- Recording never edits `abstract.md`, `design.md`, any `implementation.md`, any `module.md`, a contract, a
  view, a diagram, or another feature's code, and never reads another root's attempt (FR-007,
  FR-013).
- Repeats update the existing entry; agents never delete, renumber, or reverse maintainer decisions
  (FR-008).
- Phases report what they added and what is open for the feature; analysis flags stale
  references; convergence makes work only from genuine deferred entries (FR-009).
- Maintainers resolve or dismiss directly in the log with a note and a reference (FR-010, FR-017).
- Hardening presents the feature's entries, the design reference cites every open one, apply
  refuses otherwise, and the log is left byte-identical (FR-011).
- Validation checks a present log read-only and reports nothing for an absent one (FR-012).
- Entries cite evidence instead of pasting secrets or bulk output and stay short (FR-014).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): the Reflection
  Boundary, five user stories, FR-001 to FR-017, and SC-001 to SC-009.
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md) (a
  placeholder until the first milestone is hardened).
- **The log's grammar** — `contracts/reflection-log.md` and the conforming example
  `contracts/examples/reflections.md` (repository files, not published pages); the boundary promise is
  [contract.concorde.workflow](../../architecture/contracts/concorde-workflow/contract.md); the host lifecycle
  is [contract.concorde.spec-kit-platform](../../architecture/contracts/spec-kit-platform/contract.md).
- **The project's actual log** — `specs/concorde/reflections.md` (a maintained repository file,
  not a published page).
- **The level this feature belongs to** — [module.md](../../module.md) and its
  [design reference](../../design.md).
- **The workflow this feature extends** — [Concorde Workflow](../001-concorde-workflow/abstract.md),
  especially its sub-features [context](../001-concorde-workflow/subfeatures/002-retrieve-bounded-context/design.md),
  [plan](../001-concorde-workflow/subfeatures/006-plan-delivery/design.md),
  [execute](../001-concorde-workflow/subfeatures/007-execute-and-reconcile/design.md),
  [validate](../001-concorde-workflow/subfeatures/008-validate-architecture/design.md), and
  [harden](../001-concorde-workflow/subfeatures/009-harden-design/design.md); framework fixes reach
  this checkout through [Self-Host Concorde](../004-self-host-concorde/abstract.md).
