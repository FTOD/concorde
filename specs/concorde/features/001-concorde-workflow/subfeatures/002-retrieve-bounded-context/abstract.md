# Feature Abstract: Retrieve Bounded Context

`feature.concorde.workflow.retrieve-bounded-context` · sub-feature of `feature.concorde.workflow`,
specified at `module.concorde` · about three minutes. This page is enough to understand this
workflow step; the links at the end only redirect you when you want more.

## Purpose

Let a maintainer or coding agent get enough maintained context to reason about exactly one target —
a module, a parent feature, or an immediate sub-feature — without the result silently pulling in
deeper or unrelated specification, design-reference, or implementation detail. It is how a reader
finds the level a feature belongs to, and how an agent bounds what it loads before working.

## Functionality

The owned command surface is `speckit.concorde.context`. Its input is one stable module or feature
target; its output is one level built from module summaries, level views, contracts, and feature
summary fields.

| Target | Expanded in the result | Present only as a stable reference |
|---|---|---|
| Module | That module's summary, immediate children, current-level features and contracts, permitted externals, and scenarios | The module `design.md`; each feature's `abstract.md`, `design.md`, and `implementation.md` paths |
| Parent feature | Its immediate children, summarized in authored order | The same document paths |
| Child feature | Its parent and siblings as concise summary fields — ID, title, outcome, evidence status, canonical root, abstract path | The same document paths; no bodies, no attempt paths |

The result distinguishes containment from adjacent-module refinement. An invalid or ambiguous
target, duplicate IDs, cycles, unreadable sources, or malformed containment metadata return
findings. A module without `design.md`, a feature root without a durable companion, or a feature root
with a legacy name is reported as a finding rather than
silently substituted. The operation never writes anything.

**Not part of this step**: deterministic validation (the validate step), explanatory questions (the
ask step), and opening a design reference — a navigation reference is not an authorization to
expand it; deliberately opening one is the caller's act.

## Structure

This step uses the parent's core view, <a href="/architecture/concorde-workflow-components.html">workflow components</a>;
it declares no diagram of its own. The maintainer or agent invokes the Concorde surface through the
coding-agent integration; the launcher runs the runtime, which resolves the target against the
architecture sources and assembles one level.

```text
Maintainer / agent ──target──▶ speckit.concorde.context ──▶ launcher + runtime
                                                               ├─ reads: module.md · level view · contracts · feature summary fields
                                                               ├─ never expands: any implementation.md · design.md · abstract.md body · attempt/
                                                               └─ returns: one level + navigation references + findings
```

Feature roots contribute only their summary fields and the paths of their durable trio; attempts are
invisible to this step.

## Logic

1. Resolve the target to exactly one stable module or feature; on ambiguity or invalid sources,
   return findings and stop.
2. Build the level: for a module, its summary plus immediate children, current-level features,
   contracts, externals, and scenarios; for a parent feature, its children in authored order; for a
   child, its parent and siblings as summary fields.
3. Attach stable navigation references — the module `design.md` and each feature's `abstract.md`,
   `design.md`, and `implementation.md` paths — without their content.
4. Label containment and refinement relationships distinctly.
5. Report any missing module reference, missing feature companion, or legacy name as a finding
   and return the result with the sources unchanged.

**Rules the implementation must keep**

- Exactly one stable module or feature target is resolved per request (FR-001).
- A module result expands only the current module and its immediate children (FR-002).
- A parent feature result summarizes its immediate children in authored order (FR-003).
- A child result summarizes its parent and siblings without their bodies or attempts (FR-004).
- Containment and adjacent-module refinement are distinguished in the result (FR-005).
- Retrieval is read-only and returns actionable findings for invalid sources (FR-006).
- The result is built from module summaries, level views, contracts, and feature summary fields, and
  includes the module `design.md` only as a stable navigation reference (FR-007).
- Feature `abstract.md`, `design.md`, and `implementation.md` appear as paths, never as bodies beyond the summary
  fields the parent defines (FR-008).
- A missing module reference, missing feature companion, or legacy feature name
  surfaces as a finding, never as silent substitution (FR-009).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): FR-001 to FR-009 and
  SC-001 to SC-004.
- **How the accepted implementation realizes this step** — [implementation.md](implementation.md) (states that no
  realization has been hardened yet).
- **The parent feature** — its [abstract](../../abstract.md) and [design.md](../../design.md), which define
  bounded context, the summary fields, and the read/consult split.
- **Contracts** — `../../contracts/agent-commands.md` for the surface and
  `../../contracts/architecture-sources.md` for what a level is built from.
- **The level** — [module.md](../../../../module.md).
- **Previous and next steps** — [initialize](../001-initialize-architecture/design.md) and
  [answer workflow questions](../003-answer-workflow-questions/design.md).
