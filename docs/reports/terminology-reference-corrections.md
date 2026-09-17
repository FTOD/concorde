# Spec terminology and navigation corrections

## Scope and decisions

This is a direct-maintenance completion record, not a registered Spec or a second definition source.
The session started on `main` at `2a79fcfc` with a clean worktree; the terminology audit baseline was
`19cc8937`. All 17 registered Modules and all 113 document units were reviewed, including both
source roles (53 module-role and 60 implementation-role units). The canonical Concepts page needed
no edit; the other 112 reading documents received page-specific terminology or navigation corrections.

- Kept all 60 canonical definitions in their original documents, with their definition rows unchanged.
  Issue and Blocker still point directly to `concepts.md#terminology`; the Issues Module entry is
  separate capability navigation, not a forwarding glossary.
- Chose terms from each page's meaning, not a shared Module template or an automatic keyword rule.
  Short requirements pages now keep only their actual concepts; Validation's one-requirement page
  explicitly needs no specialized vocabulary and links the Harness Module as its provider.
- Distinguished the Spec and Harness concepts from the Modules with those names, and the developer's
  Candidate from Views' Publication candidate. Complete Module Spec context is not the narrower
  explanation-first Module Specs reading role.
- Added first-use provider entry navigation while retaining detailed obligation links and avoiding
  repeated links for every occurrence. Moved late interface/viewer terminology before field tables
  and command examples; existing definition and section anchors remain intact.
- Added 66 narrow document references across 15 Modules. Existing Module references were retained;
  no `uses`, parent, document ownership, role, stable ID or implementation binding changed.
  The additions include defining units needed by provider pages already selected in a consumer's
  context. Runtime resolution remains one-level: these choices are written explicitly into the
  selecting Module's references, not inferred from Markdown or provider references at runtime.
- Did not modify software behavior, executable diagrams, runtime permissions, safety limits,
  Protocol/Profile versions, prompts, Skills or generated authoring assets. The Development host's
  capability-dispatch versus conditional worker-execution model remains unchanged.

## Regression and verification evidence

Added `tests/concorde/spec/test_terminology_references.py` with nine repository regressions:
registered-role coverage; actual-table extraction excluding fenced examples and later field tables;
unique canonical definitions and direct imports; defining-unit inclusion for every selected context,
including referenced reading; a negative missing-reference case proving links do not expand context;
explicitly curated key reader dependencies; unrelated-template exclusions; Issue/Blocker versus Module
navigation; and early terminology before interface details. These tests do not claim to decide all
semantic relevance by matching words.

Final verification of the corrected Specs and test source:

- `python3 scripts/concorde.py build --check`: current, no differences.
- `python3 scripts/concorde.py validate`: success, zero errors/warnings.
- `python3 scripts/development/check-spec-v5.py --base 19cc8937`: passed identity, ownership,
  references, source structure and link checks.
- `.venv/bin/python scripts/development/check-flow-specs.py`: zero findings.
- `python3 scripts/development/run-tests.py -j 8`: 853 tests, zero failures/errors, 10 optional
  Studio Server tests skipped.
- `CONCORDE_PYTHON="$PWD/.venv/bin/python" npm --prefix docsite run check`: type checking passed,
  223 tests passed, 113 registered documents validated, production site built with link validation.
- Active LSP diagnostics for the new Python test: clean; Ruff lint/format passed.
- Local Chromium/Playwright navigation: 12 actual clicks passed, covering Issue and Blocker to their
  canonical definitions, Issues Module navigation, and samples from Harness, Planning, Distribution,
  Views, Review, Topology and Implementation. Definition destinations exposed local definition rows,
  not forwarding links. The rendered review-and-gaps page was also visually inspected.

The site was built and served locally only, not deployed. No Concorde flow, delegated agent, push,
delivery or primary merge was started. Deterministic checks and sampled browser navigation are not
proof of universal readability or semantic completeness. Existing unfulfilled runtime guarantees
remain documented and were not repaired as part of this editorial task.

## Review inventory

The following inventory is derived from the registry after the per-page review. It records the
resulting vocabulary choices, not another set of definitions. Paths are relative to `specs/concorde/`.

### Concorde Framework

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `module.md` | module | Module, Spec, Capability, Skill, Worker, Host, Flow, Candidate, Worktree, Ready, Delivery, Issue, Evidence |
| `concepts.md` | module | Module, Spec, Module Specs, Implementation Specs, Entity, Requirement, Scenario, Registry, Context, Grant, Snapshot, Evidence, Capability, Skill, Worker, Host, Harness, Flow, Candidate, Worktree, Ready, Delivery, Issue, Blocker, Contract |
| `requirements.md` | implementation | Module, Spec, Capability, Candidate, Context, Grant, Worker, Host, Issue, Initialization, Delivery, Ready |
| `scenarios.md` | implementation | Module, Spec, Candidate, Ready, Delivery, Evidence, Worker, Worktree, Issue, Disposition, Protocol binding, Spec context, Initialization |
| `contracts.md` | implementation | Skill, Capability, Candidate, Ready, Grant, Worker |
| `collaborations.md` | implementation | Module, Spec, Capability, Worker, Host, Flow, Candidate, Evidence, Protocol binding, Registry, Spec context, Implementation context, Skill, Issue, Blocker, Disposition, Delivery, Ready |
| `ownership-migration.md` | implementation | Module, Spec, Capability, Contract, Requirement, Scenario, Entity, Ownership, Reference, Implementation binding, Evidence |

### Spec

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `spec/module.md` | module | Module, Spec, Registry, Context, Snapshot, Protocol binding, Document unit, Entity, Reference, Implementation binding, Structural validation, Semantic completeness |
| `spec/registry.md` | module | Ownership, Composition, Use, Reference, Implementation binding, Module, Spec, Registry, Context, Snapshot, Document unit, Document role, Entity, Scenario, Spec context, Evidence |
| `spec/values.md` | module | Document unit, Document role, Source-member role, Protocol binding, Module, Spec, Snapshot, Evidence, Requirement, Scenario, Host, Registry |
| `spec/structure.md` | module | Structural validation, Semantic completeness, Module, Registry, Reference, Document role, Document unit, Entity, Context, Evidence |
| `spec/initialize.md` | module | Initialization, Initial proposal, Module, Spec, Registry, Protocol binding, Document role, Worker, Installation |
| `spec/requirements.md` | implementation | Module, Spec, Registry, Snapshot, Entity, Implementation binding, Structural validation, Semantic completeness, Host, Initialization, Initial proposal, Worktree |
| `spec/scenarios.md` | implementation | Module, Spec, Registry, Context, Snapshot, Protocol binding, Ownership, Composition, Use, Reference, Implementation binding, Document unit, Document role, Entity, Requirement, Scenario, Structural validation, Semantic completeness, Initialization, Initial proposal, Issue, Spec context |
| `spec/contracts.md` | implementation | Module, Spec, Registry, Snapshot, Host, Ownership, Composition, Use, Reference, Implementation binding, Document unit, Document role, Source-member role, Protocol binding, Entity, Requirement, Scenario, Spec context, Structural validation, Semantic completeness, Initialization, Initial proposal, Worker, Grant, Issue |

### Harness

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `harness/module.md` | module | Worker profile, Tool gate, Capsule, Worker, Harness, Context, Grant, Snapshot, Capability, Host, Flow, Candidate, Worktree, Spec context, Implementation context, Capability context, Task context, Protocol binding |
| `harness/agents-and-harnesses.md` | module | Capability, Worker, Harness, Worker profile, Host, Grant, Flow |
| `harness/graphs-and-loops.md` | module | Flow, Worker, Ready, Delivery |
| `harness/context.md` | module | Spec context, Implementation context, Capability context, Task context, Context, Worker, Module, Spec, Scenario, Host, Grant, Snapshot, Reference, Document role, Implementation Specs |
| `harness/permissions.md` | module | Tool gate, Worker profile, Worker, Grant, Host, Module, Reference, Worktree |
| `harness/execution.md` | module | Tool gate, Capsule, Worker, Host, Grant, Snapshot, Spec, Candidate, Issue |
| `harness/host.md` | module | Host, Worker, Spec, Grant, Flow, Skill |
| `harness/runtime-values.md` | implementation | Capability, Host, Worker, Worker profile, Grant, Snapshot, Capsule, Spec context, Implementation context, Issue, Entity, Module, Reference |
| `harness/typed-values.md` | module | Host, Contract, Grant, Review coverage, Structural validation, Semantic completeness |
| `harness/requirements.md` | implementation | Worker, Worker profile, Context, Grant, Snapshot, Host, Spec context, Task context, Capsule, Tool gate, Module, Entity, Scenario, Spec, Registry |
| `harness/scenarios.md` | implementation | Worker, Worker profile, Context, Grant, Snapshot, Host, Flow, Capability, Spec context, Task context, Capsule, Tool gate, Candidate, Worktree, Protocol binding, Entity, Reference |
| `harness/contracts.md` | implementation | Worker, Host, Context, Grant, Snapshot, Capsule, Spec context, Implementation context, Capability context, Task context, Document unit, Source-member role, Protocol binding, Reference, Issue, Blocker, Candidate, Worktree, Skill, Capability, Evidence |
| `harness/execution-reference.md` | implementation | Capability, Worker, Worker profile, Harness, Host, Flow, Skill, Context, Grant, Snapshot, Capsule, Tool gate, Spec context, Implementation context, Task context, Issue, Evidence, Candidate, Worktree, Structural validation, Semantic completeness |

### Development

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `development/module.md` | module | Public capability, Internal capability, Capability, Host, Flow, Skill, Worker, Candidate, Worktree, Ready, Evidence, Issue |
| `development/interfaces.md` | implementation | Capability, Public capability, Internal capability, Host, Flow, Skill, Worker, Worker profile, Grant, Snapshot, Capsule, Candidate, Worktree, Ready, Delivery, Evidence, Issue, Blocker, Disposition, Spec context, Implementation context, Protocol binding |
| `development/capabilities.md` | module | Public capability, Internal capability, Capability, Host, Flow, Skill, Worker, Module, Grant |
| `development/review-and-gaps.md` | module | Issue, Blocker, Spec, Worker, Evidence, Disposition |
| `development/flows.md` | module | Capability, Host, Flow, Candidate, Evidence, Module, Worker |
| `development/requirements.md` | implementation | Capability, Internal capability, Host, Flow, Skill, Context, Spec, Module, Worktree |
| `development/scenarios.md` | implementation | Capability, Public capability, Internal capability, Host, Flow, Skill, Worker, Harness, Grant, Context, Candidate, Worktree, Spec, Issue |
| `development/execution-reference.md` | implementation | Capability, Public capability, Internal capability, Host, Flow, Worker, Worker profile, Skill, Context, Grant, Snapshot, Spec context, Task context, Candidate, Worktree, Ready, Evidence, Issue, Blocker, Disposition, Review coverage |
| `development/collaborations.md` | implementation | Module, Capability, Host, Flow, Worker, Skill, Spec, Protocol binding, Registry, Implementation binding, Candidate, Evidence, Blocker, Delivery, Ready |

### Issues

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `issues/module.md` | module | Issue, Blocker, Candidate, Ready, Evidence, Disposition, Worker, Host, Spec, Flow |
| `issues/interfaces.md` | implementation | Issue, Blocker, Candidate, Evidence, Disposition, Worker, Host, Grant |
| `issues/lifecycle.md` | module | Disposition, Issue, Candidate, Ready, Evidence, Host, Spec, Flow |
| `issues/issues.md` | module | Issue, Blocker, Candidate, Evidence, Worker, Disposition, Module |
| `issues/requirements.md` | implementation | Issue, Worker, Grant, Disposition, Ready, Delivery, Flow |
| `issues/scenarios.md` | implementation | Issue, Blocker, Candidate, Evidence, Disposition, Ready, Delivery, Worker, Host, Grant, Spec, Worktree |
| `issues/execution-reference.md` | implementation | Issue, Blocker, Candidate, Evidence, Disposition, Worker, Host, Grant, Spec context, Spec, Ready, Delivery, Worktree, Flow |

### Distribution

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `distribution/module.md` | module | Skill, Worker, Capability, Worktree, Installation, Update, Installation receipt, Initialization, Protocol binding, Registry, Spec |
| `distribution/installation.md` | module | Installation, Update, Installation receipt, Skill, Initialization, Protocol binding, Spec, Registry |
| `distribution/build.md` | module | Skill, Worker, Capability, Public capability, Internal capability, Host, Worktree, Protocol binding, Document role, Worker profile |
| `distribution/runtime.md` | module | Worker, Installation, Evidence |
| `distribution/requirements.md` | implementation | Skill, Installation, Update, Installation receipt, Protocol binding, Worktree |
| `distribution/scenarios.md` | implementation | Skill, Worker, Worker profile, Capability, Public capability, Internal capability, Host, Worktree, Candidate, Installation, Update, Installation receipt, Initialization, Protocol binding, Spec |
| `distribution/contracts.md` | implementation | Skill, Worker, Worker profile, Capability, Host, Grant, Installation, Installation receipt |

### Views

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `views/module.md` | module | Module Specs, Implementation Specs, Registry, Publication candidate, Promotion, Document role, Document unit, Spec context, Reference, Entity, Flow, Semantic completeness |
| `views/requirements.md` | implementation | Module Specs, Implementation Specs, Registry, Publication candidate, Promotion, Spec context, Snapshot, Entity, Scenario, Flow |
| `views/publication.md` | module | Module Specs, Implementation Specs, Registry, Document role, Document unit, Spec context, Publication candidate, Promotion, Reference |
| `views/pipeline.md` | module | Publication candidate, Promotion, Module Specs, Implementation Specs, Registry, Document role, Document unit, Scenario, Spec context |
| `views/viewer.md` | module | Capability, Skill, Module, Installation |
| `views/ua-graph.md` | module | Registry, Module, Entity, Composition, Use, Reference, Implementation binding, Implementation context, Capability, Skill, Worktree |
| `views/scenarios.md` | implementation | Module Specs, Implementation Specs, Registry, Document role, Document unit, Publication candidate, Promotion, Spec context, Reference, Ownership, Composition, Use, Implementation binding, Entity, Requirement, Scenario, Flow, Capability, Snapshot |
| `views/contracts.md` | implementation | Module Specs, Implementation Specs, Registry, Document role, Document unit, Publication candidate, Promotion, Spec context, Reference, Ownership, Composition, Implementation binding, Entity, Installation |
| `views/execution-reference.md` | implementation | Module Specs, Implementation Specs, Registry, Document role, Document unit, Publication candidate, Promotion, Spec context, Reference, Entity, Requirement, Scenario, Flow, Capability, Skill, Semantic completeness |

### Planning

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `planning/module.md` | module | Spec, Worker, Candidate, Ready, Host, Skill, Flow, Task sufficiency, Acceptance task, Reserved task ID, Spec context, Grant |
| `planning/assessment.md` | module | Task sufficiency, Spec, Module, Host, Blocker, Internal capability, Skill |
| `planning/plan.md` | module | Spec, Module, Candidate, Ready, Host, Flow, Task sufficiency |
| `planning/tasks.md` | module | Acceptance task, Reserved task ID, Spec, Module, Host, Grant, Evidence, Delivery |
| `planning/requirements.md` | implementation | Spec, Module, Spec context, Task sufficiency, Acceptance task, Reserved task ID, Host |
| `planning/scenarios.md` | implementation | Spec, Module, Host, Task sufficiency, Acceptance task, Reserved task ID, Ready, Semantic completeness |
| `planning/execution-reference.md` | implementation | Spec, Module, Worker, Host, Candidate, Ready, Grant, Spec context, Internal capability, Skill, Flow, Task sufficiency, Acceptance task, Reserved task ID, Evidence, Delivery |

### Implementation

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `implementation/module.md` | module | Spec, Module, Worker, Host, Grant, Candidate, Ready, Delivery, Acceptance task, Internal capability, Skill, Flow, Entity |
| `implementation/implementation.md` | module | Spec, Module, Worker, Host, Grant, Candidate, Ready, Acceptance task, Internal capability, Evidence |
| `implementation/requirements.md` | implementation | Acceptance task |
| `implementation/scenarios.md` | implementation | Spec, Module, Worker, Host, Grant, Candidate, Ready, Acceptance task |
| `implementation/execution-reference.md` | implementation | Spec, Module, Worker, Host, Grant, Candidate, Ready, Acceptance task, Spec context, Internal capability, Skill, Flow, Entity, Evidence |

### Spec Authoring

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `spec-authoring/module.md` | module | Spec, Module, Worker, Host, Grant, Blocker, Reference, Ownership, Flow, Internal capability, Skill |
| `spec-authoring/authoring.md` | module | Spec, Module, Host, Grant, Module Specs, Implementation Specs, Ownership, Reference |
| `spec-authoring/requirements.md` | implementation | Spec, Module, Ownership |
| `spec-authoring/scenarios.md` | implementation | Spec, Module, Host, Blocker, Context, Ownership, Reference |
| `spec-authoring/execution-reference.md` | implementation | Spec, Module, Worker, Host, Grant, Blocker, Candidate, Ready, Spec context, Reference, Ownership, Flow, Internal capability, Skill |

### Review

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `review/module.md` | module | Review coverage, Advisory finding, Spec, Evidence, Worker, Host, Grant, Worktree, Flow |
| `review/review.md` | module | Review coverage, Advisory finding, Spec, Evidence, Host, Candidate, Module |
| `review/review-result.md` | implementation | Spec, Evidence, Worker, Host, Issue, Blocker, Disposition, Review coverage, Advisory finding, Reference |
| `review/requirements.md` | implementation | Evidence, Review coverage |
| `review/scenarios.md` | implementation | Spec, Issue, Host, Worker, Skill, Module, Review coverage |
| `review/execution-reference.md` | implementation | Spec, Evidence, Worker, Host, Grant, Harness, Issue, Blocker, Review coverage, Advisory finding, Candidate, Worktree, Capsule, Snapshot, Flow, Capability, Public capability, Skill |

### Validation

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `validation/module.md` | module | Candidate, Evidence, Ready, Spec, Host, Structural validation, Semantic completeness, Scenario, Capability |
| `validation/validation.md` | module | Candidate, Evidence, Ready, Spec, Host, Module, Structural validation |
| `validation/requirements.md` | implementation | No specialized terminology |
| `validation/scenarios.md` | implementation | Candidate, Evidence, Ready, Spec, Host, Module, Semantic completeness |
| `validation/execution-reference.md` | implementation | Candidate, Evidence, Ready, Spec, Host, Module, Grant, Structural validation, Semantic completeness, Delivery, Flow, Skill |

### Delivery

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `delivery/module.md` | module | Delivered branch, Delivery receipt, Candidate, Ready, Delivery, Worktree, Evidence, Host |
| `delivery/delivery.md` | module | Delivery receipt, Delivered branch, Candidate, Ready, Delivery, Worktree, Evidence, Host |
| `delivery/requirements.md` | implementation | Worktree, Host |
| `delivery/scenarios.md` | implementation | Candidate, Ready, Delivery, Worktree, Evidence, Host, Delivery receipt, Delivered branch |
| `delivery/execution-reference.md` | implementation | Candidate, Ready, Delivery, Worktree, Evidence, Host, Delivery receipt, Delivered branch, Reference, Grant, Flow, Skill |

### Query and Routing

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `query-routing/module.md` | module | Module, Spec, Context, Spec context, Host, Worker, Flow, Candidate, Reference |
| `query-routing/query-and-routing.md` | module | Module, Spec, Context, Spec context, Host, Worker, Grant, Candidate, Flow, Reference |
| `query-routing/requirements.md` | implementation | Module, Capability, Worker, Spec context, Context |
| `query-routing/scenarios.md` | implementation | Module, Spec, Spec context, Context, Host, Worker |
| `query-routing/execution-reference.md` | implementation | Module, Spec, Spec context, Context, Host, Worker, Capability, Grant, Flow, Reference, Skill |

### Topology

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `topology/module.md` | module | Module, Registry, Spec, Ownership, Composition, Reference, Implementation binding, Protocol binding, Evidence, Flow, Grant |
| `topology/topology.md` | module | Module, Registry, Ownership, Reference, Implementation binding, Host, Flow |
| `topology/requirements.md` | implementation | Ownership, Reference, Context |
| `topology/scenarios.md` | implementation | Module, Registry, Spec, Ownership, Composition, Reference, Implementation binding, Host, Context |
| `topology/execution-reference.md` | implementation | Module, Registry, Spec, Ownership, Reference, Flow, Capability, Harness, Host, Grant, Evidence, Protocol binding, Skill |

### Development Flow

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `dev-loop/module.md` | module | Flow, Spec, Candidate, Ready, Evidence, Blocker, Worktree, Delivery, Module |
| `dev-loop/development.md` | module | Flow, Spec, Candidate, Ready, Evidence, Worker, Module, Delivery |
| `dev-loop/requirements.md` | implementation | Flow, Spec |
| `dev-loop/scenarios.md` | implementation | Flow, Spec, Candidate, Ready, Evidence, Worktree, Host, Module, Acceptance task |
| `dev-loop/execution-reference.md` | implementation | Flow, Spec, Candidate, Ready, Evidence, Blocker, Worktree, Host, Worker, Module, Grant, Snapshot, Spec context, Task context, Protocol binding, Acceptance task, Reserved task ID, Review coverage, Capability, Harness, Delivery, Skill |

### Specification Flow

| Document | Role | Selected vocabulary |
| --- | --- | --- |
| `specify-loop/module.md` | module | Flow, Spec, Evidence, Candidate, Ready, Blocker, Module, Delivery |
| `specify-loop/specify-loop.md` | module | Flow, Spec, Evidence, Candidate, Ready, Host, Module |
| `specify-loop/requirements.md` | implementation | Spec, Ready |
| `specify-loop/scenarios.md` | implementation | Spec, Module, Evidence, Review coverage, Ready |
| `specify-loop/execution-reference.md` | implementation | Flow, Spec, Evidence, Candidate, Ready, Blocker, Module, Host, Worker, Worktree, Spec context, Skill |
