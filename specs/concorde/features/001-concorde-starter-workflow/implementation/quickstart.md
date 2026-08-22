# Quickstart and Acceptance Guide: Concorde Core Workflow

**Feature**: `feature.concorde.core-workflow`  
**Audience**: Maintainers validating this implementation attempt  
**Status**: Target-state guide; create/select and complete validation rules are planned

This guide starts after Feature 003 has installed a compatible Concorde preset and extension. It
does not build release archives, register catalogs, or run a local release server.

## 1. Prepare an isolated project

Use a clean temporary Spec Kit project with Concorde already installed and a supported active coding
agent. Record the Spec Kit and Concorde versions plus Feature 003's clean-install receipt and the
Feature 001 Workflow Distribution Handoff digest it claims to implement. Do not point these checks at
valuable user content. If the receipt is missing, stale, or identifies a different handoff digest,
stop: repository-local skills are not a substitute for installed behavior.

Expected installed command set:

```text
speckit.concorde.init
speckit.concorde.feature.create
speckit.concorde.feature.select
speckit.concorde.context
speckit.concorde.validate
```

Agent-specific skill/slash punctuation may differ; the canonical command intent must not.

The active integration must also expose the nine normal Spec Kit lifecycle surfaces composed by
Feature 003. This guide tests the workflow meaning behind them; Feature 003 owns their release archive,
winning-layer materialization, checkout isolation, and restoration after preset removal.

## 2. Establish and navigate the hierarchy

1. Run `speckit.concorde.init --propose --module-id module.example --name Example`.
2. Verify the proposal names every path, responsibility, boundary, explicit contract set, source
   digest, and conflict without writing maintained intent.
3. Save and explicitly approve the exact proposal; run init apply.
4. Add two immediate child modules and one grandchild fixture through reviewed maintained sources.
5. Run `speckit.concorde.context module.example`, then request one child.

Expected:

- root context contains only the root and its immediate children;
- child feature bodies and the grandchild are absent from root context;
- selecting the child repeats the same rule and exposes the grandchild only as that child's immediate
  child;
- repeated context calls are read-only and byte-equivalent.

This proves the deterministic part of US1 and SC-002. SC-001 still requires the participant protocol
below.

## 3. Review placement and create a nested feature

Choose a behavior wholly owned by one child module. Run the canonical feature-create command with an
explicit module ID, feature ID, and short name.

Expected proposal:

- exact nested feature root under the providing module;
- one canonical `<feature-root>/spec.md`;
- module feature-registration change;
- affected contracts and current-level view, or explicit none;
- source digest and any collision;
- no maintained write before explicit approval.

Approve the exact proposal and allow the command to continue through the normal specify phase.
Confirm:

```text
<feature-root>/spec.md                         exists
<feature-root>/diagrams/                       contains any declared feature-owned Archify JSON
<feature-root>/implementation/                 may be absent before planning
<feature-root>/plan.md                         does not exist
<feature-root>/tasks.md                        does not exist
.specify/feature.json                          points to <feature-root>
```

Repeat with a behavior spanning two immediate children. The reviewed providing module must be their
nearest common parent; lower-level features may refine the parent feature later.

## 4. Select an existing feature and verify every phase path

Run `speckit.concorde.feature.select <feature-id>` and inspect the normative workspace result.

Run the normal lifecycle in this order:

1. specify and clarify;
2. checklist generation;
3. plan;
4. tasks;
5. implement;
6. analyze and converge.

For every cross-component scenario, confirm that `spec.md` declares a text-backed source directly
under `<feature-root>/diagrams/`, or records a sufficiency rationale. After documentation publication,
the canonical feature page must embed every declaration without manual page markup.

For every phase, capture the path resolver output. The required matrix is:

| Artifact/operation | Required location |
|---|---|
| specification, feature contracts, requirements checklists | `<feature-root>/` |
| plan, research, data model, quickstart | `<feature-root>/implementation/` |
| tasks, implementation execution, analysis, convergence, validation evidence | `<feature-root>/implementation/` |

No run may create root `plan.md`, root `tasks.md`, a symlink, or a flat duplicate feature. Re-selecting
the same root is idempotent. Selecting another valid root changes only the standard selection record.
An existing non-empty implementation attempt requires explicit resume; silence is not consent.

This is the automated SC-004 and SC-009 acceptance path.

Record the Feature 001 semantic result separately from Feature 003's installation receipt. A passing
self-hosted path run cannot repair or replace a failed clean-install result.

## 5. Exercise the architecture-readiness gate

Create a cross-boundary scenario that omits its governing contract and expected evidence. Attempt to
complete the plan.

Expected incomplete review:

- providing module and abstraction level are shown;
- the missing adjacent refinement, participant boundary, contract crossing, dependency direction,
  affected view, or evidence expectation is named precisely;
- the plan is not reported as architecture-ready.

Add a durable contract with role, flow, counterparties, representation, obligations, failures,
compatibility, and evidence. For a custom format, add its schema/grammar and conforming example. Add
the ordered scenario interaction and contract reference to the current-level view, then validate
again. The gate may pass only after the reviewed sources and expected evidence are complete.

## 6. Request active-feature implementation context

Run `speckit.concorde.context <feature-id>` after planning.

Expected context includes:

- root `spec.md`, durable feature contracts/checklists, and current implementation artifacts;
- providing-module responsibility, boundary, features, and current-level view;
- relevant parent/child refinements and governing contracts;
- explicit evidence references and statuses;
- stable IDs for deliberate adjacent navigation.

It excludes unrelated features, unrelated implementation attempts, child feature bodies,
grandchildren, generated page bodies, and implementation details outside the selected feature.

## 7. Seed deterministic reconciliation failures

In isolated copies, introduce one defect at a time:

- root-level `plan.md` or `tasks.md`;
- broken or non-adjacent feature refinement;
- cross-boundary interaction without a contract;
- custom example that fails its supported schema/grammar adapter;
- missing evidence reference;
- evidence marked verified whose target is missing or digest disagrees;
- stale Archify or documentation projection.

Run `speckit.concorde.validate` three times for each unchanged fixture. Expected:

- every seeded defect has a stable rule, source, severity, and remediation;
- unsupported conformance formats are reported, never assumed valid;
- missing implementation evidence remains `unknown` and disagreement stays explicit;
- delegated Archify/docsite freshness findings retain their owning tool provenance;
- all three JSON outputs and exit codes are byte-equivalent;
- source hashes before and after validation are identical.

## 8. Self-application and full repository gates

Select Feature 001 itself and verify its durable/temporal split. Then run:

```bash
uv run python -m unittest discover -s tests/concorde -t .
uv run python extensions/concorde/scripts/python/concorde.py --project-root . validate
cd docsite && npm run check
```

Also run the Archify validation/freshness command used by the repository for each changed maintained
view. Generated outputs may be refreshed only from validated sources and must retain provenance.

Record results in `implementation/validation.md`. Do not reuse installation evidence from Feature
003 or claim pending human outcomes from automated commands.

## 9. Human approval and outcome evidence

For every AI-authored architecture change in the acceptance sample, record the reviewer, reviewed
source digest, decision, and separate behavioral, structural, implementation/test, and generated
evidence. This is required for SC-008.

### SC-001 placement pilot

- Recruit first-time maintainers and give each only this workflow guide and the same fixture.
- Start the timer when the behavior description is revealed.
- Success requires selecting the correct providing module and creating/selecting the canonical
  workspace within 10 minutes without intervention.
- Report participant count, completion times, intervention count, and the percentage succeeding.
- Pass threshold: at least 90%.

### SC-007 mental-model pilot

- Give first-time maintainers at most five minutes to review the specification/architecture guide.
- Ask four questions: what defines feature behavior; what scenarios mean; what module/contract prose
  owns; and what the one-level view owns.
- Success requires all four answers to preserve those authority boundaries.
- Report participant count and exact scoring; pass threshold is at least 90%.

Automated source, diagram, or documentation checks cannot substitute for either participant result.
