# Feature Abstract: Validate Architecture

`feature.concorde.workflow.validate-architecture` · sub-feature of `feature.concorde.workflow`,
specified at `module.concorde` · about four minutes. This page is enough to understand this
workflow step; the links at the end only redirect you when you want more.

## Purpose

Give a maintainer a repeatable, complete, actionable account of structural validity, document-model
compliance, and known evidence agreement for the whole project or one supported target — without
validation ever rewriting the sources it evaluates. It can run after any maintained structural
change, not only at its place in the workflow order.

## Functionality

The owned command surface is `speckit.concorde.validate`. Its input is the whole project or one
supported target; its output is a stable status (`success`, `invalid`, `conflict`, or `failed`), a
source digest, a summary, and complete sorted findings, each with a stable rule ID, severity,
location, explanation, and actionable remediation.

| Area | What is checked |
|---|---|
| Hierarchy and identity | Identities, paths, module hierarchy, contracts, scenarios, views, refinements, feature containment, diagrams, selection safety |
| Feature roots | Illegal third-level, alternate-depth, dangling, duplicate, cyclic, symlinked, or mismatched roots; containment and refinement as distinct acyclic relationships |
| Module documents | `module.md` summary shape and reading budget; module `design.md` present and reachable |
| Feature documents | `abstract.md` present with exactly the five sections in order, a structure section linking a maintained diagram or holding a text sketch, `Logic` rules citing requirement IDs present in the adjacent `design.md`, and the reading budget; the durable trio present |
| Legacy names | Former `tldr.md`/`spec.md` files and `implementation/`; missing `implementation.md` or `abstract.md` |
| Evidence | Evidence references; unknown or conflicting evidence reported as unknown or disagreement, never promoted to agreement |

Reading-budget findings use the deterministic proxies the parent records and are warnings that leave
the status unchanged; later findings are never hidden by earlier ones.

**Not part of this step**: judging prose quality or whether a abstract is a faithful summary (a
requirements-review judgment in the specify step), analyzing an attempt's artifacts (the execute
step), and deciding whether an application behaves correctly.

## Structure

This step uses the parent's core view, <a href="/architecture/concorde-workflow-components.html">workflow components</a>;
it declares no diagram of its own. The maintainer invokes the Concorde surface through the
coding-agent integration; the launcher runs the runtime, which indexes the maintained architecture
sources and evaluates every rule.

```text
Maintainer ──project or target──▶ speckit.concorde.validate ──▶ launcher + runtime
                                                                  ├─ discovers: module.md · design.md · views · contracts · feature roots (abstract · design · implementation) · selection
                                                                  ├─ evaluates: structural rules · document-model rules · evidence freshness
                                                                  └─ returns:   status · digest · summary · sorted findings (rule · severity · location · remediation)
```

## Logic

1. Resolve the scope: the whole project or one supported target; an unknown or ambiguous target is
   a finding.
2. Discover and index every maintained source; malformed metadata becomes a finding rather than a
   crash.
3. Evaluate the structural rules, the document-model rules for every `module.md`, module
   `design.md`, and feature root, and the evidence rules.
4. Sort the findings completely and compute the status; budget overruns are warnings and do not
   change it.
5. Return status, digest, summary, and findings with nothing on disk changed; a repeat on unchanged
   sources yields equivalent output.

**Rules the implementation must keep**

- Validation is read-only, deterministic, and repeatable for unchanged inputs (FR-001).
- Every finding carries a stable rule ID, severity, location, explanation, and actionable
  remediation (FR-002).
- Coverage spans identities, paths, hierarchy, contracts, scenarios, views, refinements,
  containment, diagrams, selection safety, evidence references, both document models, the durable
  trio, and legacy names (FR-003).
- Containment and refinement are validated as distinct acyclic relationships (FR-004).
- Illegal third-level, alternate-depth, dangling, duplicate, cyclic, symlinked, or mismatched roots
  are actionable findings (FR-005).
- Findings are complete and sorted; statuses are the stable success, invalid, conflict, and failed
  set (FR-006).
- Unknown evidence is never promoted to agreement (FR-007).
- Every `module.md` is checked for summary shape and budget, and every module for a `design.md`
  reachable from its summary (FR-008).
- Every feature root is checked for a five-section `abstract.md` with a structure link, requirement
  citations present in `design.md`, and the reading budget (FR-009).
- Legacy names and missing `implementation.md`/`abstract.md` are reported with specific remediation (FR-010).
- Reading-budget findings use the parent's deterministic proxies, are warnings that leave the status
  unchanged, and never judge prose quality or faithfulness (FR-011).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): FR-001 to FR-011 and
  SC-001 to SC-005.
- **How the accepted implementation realizes this step** — [implementation.md](implementation.md) (states that no
  realization has been accepted yet).
- **The parent feature** — its [abstract](../../abstract.md) and [design.md](../../design.md), which define the
  document model and the reading-budget proxies.
- **Contracts** — `../../contracts/architecture-sources.md` for the source
  profile validated and `../../contracts/agent-commands.md` for the surface.
- **The level** — [module.md](../../../../module.md).
- **Previous and next steps** — [execute and reconcile](../007-execute-and-reconcile/design.md) and
  [accept design](../009-accept-milestone/design.md).
