# Feature Abstract: Initialize Architecture

`feature.concorde.workflow.initialize-architecture` · sub-feature of `feature.concorde.workflow`,
specified at `module.concorde` · about three minutes. This page is enough to understand this
workflow step; the links at the end only redirect you when you want more.

## Purpose

Give a maintainer a root module package they have actually reviewed — the root `module.md` summary,
its `implementation.md` design reference, the level view, the configuration, and the initial contracts —
before any later workflow step depends on architectural ownership. The maintainer sees exactly what
would be created, where, and what it conflicts with, and nothing exists until they explicitly say
yes.

It is the first writer of a module summary and its reference, and it seeds them in the shape the
parent's document model requires, so the root can be read in minutes from the day it exists.

## Functionality

The owned command surface is `speckit.concorde.init`, in two modes:

| Mode | Reads | Produces |
|---|---|---|
| Proposal (read-only) | Existing project metadata | Root responsibility, boundary, contracts, child summaries, every proposed path (summary, design reference, level view, configuration, initial contracts), the source digest, and any conflicts |
| Apply (after explicit approval of that exact proposal) | The reviewed, project-contained proposal | `.concorde/config.json`, root `module.md`, root `implementation.md`, the root view, and the approved initial contracts, as one failure-safe change |

Repeating the operation against the same accepted hierarchy reports unchanged and rewrites nothing.
Conflicting existing content, unsafe paths, malformed proposals, and stale state produce findings and
leave maintained sources untouched; a target that already has a summary without a reference, or a
reference without a summary, is a conflict with a remediation, never a silent completion.

**Not part of this step**: installing Concorde (`feature.concorde.install-with-spec-kit`), adding a
`implementation.md` to a module that predates it (migration work owned by the parent), and creating or
selecting a feature root (the workspaces and specify steps).

## Structure

This step uses the parent's core view, <a href="/architecture/concorde-workflow-components.html">workflow components</a>;
it declares no diagram of its own. The maintainer invokes the surface through the coding-agent
integration; the launcher runs the Python runtime; the runtime reads project metadata and, only on
approval, writes control state and architecture sources.

```text
Maintainer ──invoke · review · approve──▶ speckit.concorde.init (Concorde surface, via the integration)
                                              └─▶ launcher + runtime
                                                    ├─ proposal: read project metadata → proposal + digest + conflicts
                                                    └─ apply:    .concorde/config.json · module.md · implementation.md · level view · contracts
```

No feature root, selected-workspace adapter, or attempt participates: the step ends where the root
package begins.

## Logic

1. The maintainer runs proposal mode; the runtime returns the full proposal with its source digest
   and conflicts, and changes nothing.
2. The maintainer reviews the responsibility, boundary, contracts, paths, and conflicts.
3. The maintainer explicitly approves that exact proposal; silence is not approval.
4. Apply creates the configuration, summary, reference, view, and contracts together as one
   failure-safe change, or fails leaving existing sources untouched.
5. The resulting root validates: the summary has the required shape within its reading budget and
   the reference is reachable from it.
6. Running initialization again reports unchanged.

**Rules the implementation must keep**

- A reviewable proposal comes first and lists responsibility, boundary, contracts, child summaries,
  every proposed path, the source digest, and conflicts (FR-001).
- Proposal mode is read-only, and silence never counts as approval (FR-002).
- Apply accepts only the explicitly reviewed, project-contained proposal (FR-003).
- Configuration, root `module.md`, root `implementation.md`, root view, and approved initial contracts are
  created as one failure-safe change (FR-004).
- Conflicts, unsafe paths, malformed proposals, and stale state leave existing sources unchanged and
  yield actionable findings (FR-005).
- Re-running against the same accepted hierarchy is idempotent (FR-006).
- The seeded summary meets the parent's shape and reading budget on creation; the seeded reference is
  reachable from it and may say only that nothing has been recorded yet (FR-007).
- A summary without a reference, or a reference without a summary, is reported as a conflict with a
  remediation (FR-008).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): FR-001 to FR-008 and
  SC-001 to SC-004.
- **How the accepted implementation realizes this step** — [implementation.md](implementation.md) (states that no
  realization has been hardened yet).
- **The parent feature** — its [abstract](../../abstract.md) and [design.md](../../design.md), which own the
  document model this step seeds.
- **Contracts** — `../../contracts/agent-commands.md` for the surface and
  `../../contracts/architecture-sources.md` for the source profile of the
  package it creates.
- **The level** — [module.md](../../../../module.md).
- **Next step** — [retrieve bounded context](../002-retrieve-bounded-context/design.md).
