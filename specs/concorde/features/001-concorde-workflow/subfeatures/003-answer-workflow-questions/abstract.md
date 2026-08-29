# Feature Abstract: Answer Workflow Questions

`feature.concorde.workflow.answer-workflow-questions` · sub-feature of `feature.concorde.workflow`,
specified at `module.concorde` · about three minutes. This page is enough to understand this
workflow step; the links at the end only redirect you when you want more.

## Purpose

Give a maintainer a concise, source-grounded answer about Concorde — what a concept means, when to
use a command, where an artifact belongs, how the workflow applies to the selected project context,
what a feature does, or why a level is built the way it is — without any workspace mutation and
without the answer silently reading more of the project than the question needs. It fits anywhere
in the workflow and never becomes a new authority.

## Functionality

The owned command surface is `speckit.concorde.ask`, an agent-followed procedure with no runtime.
Installed Concorde guidance is the primary workflow authority; project-specific answers start from
the smallest relevant maintained context and open deeper documents only when the question requires
them.

| Question needs… | Sources considered |
|---|---|
| A concept, command, or artifact placement | Installed guidance |
| The selected project or a child feature | The child's abstract, the parent's abstract, the level's `module.md`, concise sibling summary fields |
| A requirement's exact wording | That feature's `design.md`, cited |
| Why or how a level is built, beyond `module.md` | That level's `implementation.md`, cited, with the answer saying it was opened |
| How a feature is realized, beyond `abstract.md` | That feature's `implementation.md`, cited, with the answer saying it was opened |

Every answer identifies its source basis and separates fact from inference; it labels uncertainty
or conflict, including a abstract that disagrees with its specification. When no safe answer exists,
it states the limitation or asks one focused clarification. It keeps module summary, feature abstract,
required behavior, module and feature design references, temporal attempt, generated evidence,
containment, and refinement distinct, and never passes one off as another.

**Not part of this step**: invoking a runtime operation because it might help (context and
validation are their own steps), mutating any source or control state, and defining what the
workflow is — the parent owns that; this step only explains it.

## Structure

This step uses the parent's core view, <a href="/architecture/concorde-workflow-components.html">workflow components</a>;
it declares no diagram of its own. It is the Concorde surface the coding agent follows directly
inside the coding-agent integration: no launcher and no runtime operation are involved.

```text
Maintainer ──question──▶ speckit.concorde.ask (agent-followed, read-only)
                            ├─ first:   installed guidance · module.md · feature abstract.md · sibling summary fields
                            ├─ only when needed, and cited:  design.md (exact wording) · implementation.md (detail, rationale, realization)
                            └─ never:   runtime operations · writes · implicit attempts or deeper levels
```

## Logic

1. Interpret the question and decide whether installed guidance alone answers it.
2. If project context is needed, read only the smallest relevant set: module summaries and feature
   abstracts, with siblings as summary fields.
3. Open a `design.md` only for a requirement's exact wording; open a module or feature `implementation.md`
   only for implementation detail, rationale, or accepted realization — and cite each document
   opened.
4. Answer concisely, naming the source basis and labeling inference, uncertainty, or conflict.
5. If the question is unsupported or materially ambiguous, state the limitation or ask one focused
   clarification instead of guessing.

**Rules the implementation must keep**

- Installed Concorde guidance is the primary workflow authority (FR-001).
- Project-specific answers use only the smallest relevant maintained context, starting from module
  summaries and feature abstracts (FR-002).
- Answers identify their source basis and label inference, uncertainty, or conflict, including a
  abstract that disagrees with its specification (FR-003).
- The surface distinguishes module summary, feature abstract, required behavior, design references,
  temporal attempt, generated evidence, containment, and refinement (FR-004).
- It never invokes another operation or mutates any source or control state (FR-005).
- Unsupported or materially ambiguous questions receive an honest limitation or a focused
  clarification (FR-006).
- A `design.md` is opened only for exact wording, a `implementation.md` only for implementation detail,
  rationale, or accepted realization, and every opened document is cited (FR-007).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): FR-001 to FR-007 and
  SC-001 to SC-004.
- **How the accepted implementation realizes this step** — [implementation.md](implementation.md) (states that no
  realization has been accepted yet).
- **The parent feature** — its [abstract](../../abstract.md) and [design.md](../../design.md), whose "Where a
  fact lives" table is what this step navigates.
- **Contracts** — `../../contracts/agent-commands.md` for the surface and
  `../../contracts/architecture-sources.md` for the sources it may cite.
- **The level** — [module.md](../../../../module.md).
- **Previous and next steps** — [retrieve bounded context](../002-retrieve-bounded-context/design.md)
  and [manage feature workspaces](../004-manage-feature-workspaces/design.md).
